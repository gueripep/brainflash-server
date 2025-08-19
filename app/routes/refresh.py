"""
Refresh token endpoints: /auth/refresh and /auth/logout
"""
from fastapi import APIRouter, Depends, HTTPException, Cookie, Response
from sqlalchemy import select, update
from datetime import datetime, timedelta
import hashlib, secrets

from app.database import RefreshToken, AsyncSessionLocal, User
from app.auth import SECRET, ACCESS_TOKEN_LIFETIME, REFRESH_TOKEN_LIFETIME_DAYS, auth_backend

router = APIRouter()


async def _find_refresh(session, raw_token: str):
    th = hashlib.sha256(raw_token.encode()).hexdigest()
    q = await session.execute(select(RefreshToken).where(RefreshToken.token_hash == th, RefreshToken.revoked == False))
    return q.scalar_one_or_none()


@router.post("/auth/refresh")
async def refresh(response: Response, refresh_token: str | None = Cookie(None), strategy=Depends(auth_backend.get_strategy)):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Missing refresh token")

    async with AsyncSessionLocal() as session:
        rt = await _find_refresh(session, refresh_token)
        if not rt:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        if rt.expires_at < datetime.now():
            raise HTTPException(status_code=401, detail="Expired refresh token")

        # Get user and ask backend to create the canonical access token
        user = await session.get(User, rt.user_id)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        resp = await auth_backend.login(strategy, user)
        import json
        try:
            body = json.loads(resp.body.decode() if isinstance(resp.body, (bytes, bytearray)) else resp.body)
            access_token = body.get("access_token")
        except Exception:
            access_token = None

        if not access_token:
            raise HTTPException(status_code=500, detail="Unable to obtain access token from auth backend")

        # Rotate refresh token: revoke old, create new
        await session.execute(update(RefreshToken).where(RefreshToken.id == rt.id).values(revoked=True))
        new_raw = secrets.token_urlsafe(64)
        new_hash = hashlib.sha256(new_raw.encode()).hexdigest()
        expires_at = datetime.now() + timedelta(days=REFRESH_TOKEN_LIFETIME_DAYS)
        new_rt = RefreshToken(user_id=rt.user_id, token_hash=new_hash, issued_at=datetime.now(), expires_at=expires_at, revoked=False)
        session.add(new_rt)
        await session.commit()

        # Set cookie with new refresh token
        response.set_cookie(
            key="refresh_token",
            value=new_raw,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=REFRESH_TOKEN_LIFETIME_DAYS * 24 * 3600,
        )

        return {"access_token": access_token, "token_type": "bearer"}


@router.post("/auth/logout")
async def logout(response: Response, refresh_token: str | None = Cookie(None)):
    if not refresh_token:
        # Nothing to revoke
        response.delete_cookie("refresh_token")
        return {"detail": "logged out"}

    async with AsyncSessionLocal() as session:
        rt = await _find_refresh(session, refresh_token)
        if rt:
            await session.execute(update(RefreshToken).where(RefreshToken.id == rt.id).values(revoked=True))
            await session.commit()

    response.delete_cookie("refresh_token")
    return {"detail": "logged out"}
