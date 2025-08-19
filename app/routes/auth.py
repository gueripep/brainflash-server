"""
Authentication routes
"""
from fastapi import APIRouter, Request, Depends, Response, Cookie, HTTPException, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select, update
from datetime import datetime, timedelta
import hashlib, secrets
import logging


# Simple helper to mask tokens in logs
def _mask_token(token: str | None, keep: int = 8) -> str | None:
    if not token:
        return None
    try:
        return f"{token[:keep]}...({len(token)} chars)"
    except Exception:
        return "(unreadable)"


logger = logging.getLogger(__name__)

from app.auth import auth_backend, fastapi_users, get_user_manager, SECRET, ACCESS_TOKEN_LIFETIME, REFRESH_TOKEN_LIFETIME_DAYS
from app.schemas import UserRead, UserCreate, UserUpdate
from app.database import RefreshToken, AsyncSessionLocal

router = APIRouter()


# Custom login route that returns both access and refresh token
@router.post("/auth/jwt/login", tags=["auth"])
async def login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_manager=Depends(get_user_manager),
    strategy=Depends(auth_backend.get_strategy),
):
    # Authenticate user
    user = await user_manager.authenticate(form_data)
    if user is None or not user.is_active:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    logger.debug("login attempt: user_id=%s email=%s", getattr(user, "id", None), getattr(user, "email", None))

    # Create access token via backend (use the backend's token so verification matches)
    resp = await auth_backend.login(strategy, user)
    # Extract access token from backend response body
    import json
    try:
        body_text = resp.body.decode() if isinstance(resp.body, (bytes, bytearray)) else resp.body
    except Exception:
        body_text = None

    logger.debug("backend.login response status=%s body_preview=%s", getattr(resp, "status_code", None), (body_text[:200] if body_text else None))

    try:
        body = json.loads(body_text) if body_text else {}
        backend_access_token = body.get("access_token")
    except Exception as e:
        logger.exception("failed parsing backend login response: %s", e)
        backend_access_token = None

    logger.debug("backend_access_token present=%s masked=%s", bool(backend_access_token), _mask_token(backend_access_token))

    # Create refresh token and store
    raw = secrets.token_urlsafe(64)
    token_hash = hashlib.sha256(raw.encode()).hexdigest()
    now = datetime.now()
    expires_at = now + timedelta(days=REFRESH_TOKEN_LIFETIME_DAYS)
    async with AsyncSessionLocal() as session:
        rt = RefreshToken(user_id=user.id, token_hash=token_hash, issued_at=now, expires_at=expires_at, revoked=False)
        session.add(rt)
        await session.commit()

    logger.debug("created refresh token: user_id=%s refresh_token_hash_prefix=%s expires_at=%s", user.id, token_hash[:8], expires_at)

    # Set cookie and return combined payload (access from backend + refresh)
    resp.set_cookie("refresh_token", raw, httponly=True, secure=True, samesite="lax", max_age=REFRESH_TOKEN_LIFETIME_DAYS * 24 * 3600)

    # Prefer the backend token; if not present, return None so caller sees failure
    access_token = backend_access_token

    logger.debug("returning login payload: user_id=%s access_token_mask=%s refresh_token_set_cookie=yes", user.id, _mask_token(access_token))

    return {"access_token": access_token, "token_type": "bearer", "refresh_token": raw}


# Refresh endpoint (also in auth file per request)
@router.post("/auth/refresh", tags=["auth"])
async def refresh(
    response: Response,
    refresh_token: str = Body(..., embed=True),
    strategy=Depends(auth_backend.get_strategy),
):
    if not refresh_token:
        print("refresh called without cookie refresh_token")
        raise HTTPException(status_code=401, detail="Missing refresh token")

    print("refresh attempt: refresh_token_mask=%s", _mask_token(refresh_token))

    async with AsyncSessionLocal() as session:
        th = hashlib.sha256(refresh_token.encode()).hexdigest()
        q = await session.execute(select(RefreshToken).where(RefreshToken.token_hash == th, RefreshToken.revoked == False))
        rt = q.scalar_one_or_none()
        if not rt:
            print("refresh token not found in DB: token_hash=%s", hashlib.sha256(refresh_token.encode()).hexdigest()[:8])
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        if rt.expires_at < datetime.now():
            print("refresh token expired: id=%s user_id=%s expires_at=%s", getattr(rt, "id", None), getattr(rt, "user_id", None), getattr(rt, "expires_at", None))
            raise HTTPException(status_code=401, detail="Expired refresh token")

        print("found refresh token: id=%s user_id=%s revoked=%s expires_at=%s", rt.id, rt.user_id, rt.revoked, rt.expires_at)

        # Get user and ask backend to create the canonical access token
        from app.database import User
        user = await session.get(User, rt.user_id)
        if not user:
            print("user referenced by refresh token not found: user_id=%s", rt.user_id)
            raise HTTPException(status_code=401, detail="User not found")

        print("refresh token belongs to user: user_id=%s email=%s", user.id, getattr(user, "email", None))

        resp = await auth_backend.login(strategy, user)
        import json
        try:
            body_text = resp.body.decode() if isinstance(resp.body, (bytes, bytearray)) else resp.body
        except Exception:
            body_text = None

        print("backend.login response status=%s body_preview=%s", getattr(resp, "status_code", None), (body_text[:200] if body_text else None))

        try:
            body = json.loads(body_text) if body_text else {}
            access_token = body.get("access_token")
        except Exception as e:
            logger.exception("failed parsing backend login response during refresh: %s", e)
            access_token = None

        if not access_token:
            logger.error("auth backend did not return an access token during refresh; body_preview=%s", (body_text[:400] if body_text else None))
            raise HTTPException(status_code=500, detail="Unable to obtain access token from auth backend")

        # Rotate refresh token: revoke old, create new
        await session.execute(update(RefreshToken).where(RefreshToken.id == rt.id).values(revoked=True))
        new_raw = secrets.token_urlsafe(64)
        new_hash = hashlib.sha256(new_raw.encode()).hexdigest()
        expires_at = datetime.now() + timedelta(days=REFRESH_TOKEN_LIFETIME_DAYS)
        new_rt = RefreshToken(user_id=rt.user_id, token_hash=new_hash, issued_at=datetime.now(), expires_at=expires_at, revoked=False)
        session.add(new_rt)
        await session.commit()

        print("rotated refresh token: old_id=%s new_hash_prefix=%s new_expires_at=%s", rt.id, new_hash[:8], expires_at)

    # Return new refresh token in response body (no cookie)
    print("returning refreshed access token for user_id=%s access_token_mask=%s new_refresh_token_mask=%s", rt.user_id, _mask_token(access_token), _mask_token(new_raw))
    return {"access_token": access_token, "token_type": "bearer", "refresh_token": new_raw}


@router.post("/auth/logout", tags=["auth"])
async def logout(response: Response, refresh_token: str | None = Cookie(None)):
    if not refresh_token:
        response.delete_cookie("refresh_token")
        return {"detail": "logged out"}

    async with AsyncSessionLocal() as session:
        th = hashlib.sha256(refresh_token.encode()).hexdigest()
        q = await session.execute(select(RefreshToken).where(RefreshToken.token_hash == th, RefreshToken.revoked == False))
        rt = q.scalar_one_or_none()
        if rt:
            await session.execute(update(RefreshToken).where(RefreshToken.id == rt.id).values(revoked=True))
            await session.commit()

    response.delete_cookie("refresh_token")
    return {"detail": "logged out"}


# Keep registration, users, reset and verify routers from fastapi-users
router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)

router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)

router.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)

router.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["auth"],
)
