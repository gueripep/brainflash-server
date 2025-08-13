# BrainFlash Server Authentication System

## Overview

BrainFlash Server now includes a comprehensive authentication system using `fastapi-users` with JWT tokens and PostgreSQL storage. This system provides secure user registration, login, and access control for all API endpoints.

## Features

✅ **User Registration & Login**: Secure user authentication with email and password  
✅ **JWT Token Authentication**: Stateless authentication using JSON Web Tokens  
✅ **PostgreSQL Storage**: User data stored in PostgreSQL database  
✅ **Password Security**: Argon2 password hashing for maximum security  
✅ **Protected Endpoints**: Role-based access control for sensitive operations  
✅ **User Management**: Profile management and user administration  
✅ **Password Reset**: Secure password reset functionality (tokens generated)  
✅ **Email Verification**: Email verification system (tokens generated)  

## API Endpoints

### Authentication Endpoints

| Method | Endpoint | Description | Authentication |
|--------|----------|-------------|----------------|
| POST | `/auth/register` | Register a new user | None |
| POST | `/auth/jwt/login` | Login and get JWT token | None |
| POST | `/auth/jwt/logout` | Logout (invalidate token) | Bearer Token |
| POST | `/auth/forgot-password` | Request password reset | None |
| POST | `/auth/reset-password` | Reset password with token | None |
| POST | `/auth/request-verify-token` | Request email verification | Bearer Token |
| POST | `/auth/verify` | Verify email with token | None |

### User Management Endpoints

| Method | Endpoint | Description | Authentication |
|--------|----------|-------------|----------------|
| GET | `/users/me` | Get current user profile | Bearer Token |
| PATCH | `/users/me` | Update current user profile | Bearer Token |
| GET | `/users/{id}` | Get user by ID (superuser only) | Bearer Token |
| PATCH | `/users/{id}` | Update user by ID (superuser only) | Bearer Token |
| DELETE | `/users/{id}` | Delete user by ID (superuser only) | Bearer Token |

### Protected TTS Endpoints

| Method | Endpoint | Description | Authentication |
|--------|----------|-------------|----------------|
| GET | `/tts/protected/user-stats` | Get user TTS statistics | Bearer Token |
| POST | `/tts/synthesize` | Convert text to speech | API Key |

## Authentication Flow

### 1. User Registration

```python
import requests

# Register a new user
response = requests.post("http://localhost:8000/auth/register", json={
    "email": "user@example.com",
    "password": "SecurePassword123!",
    "first_name": "John",
    "last_name": "Doe"
})
```

### 2. User Login

```python
# Login and get JWT token
response = requests.post("http://localhost:8000/auth/jwt/login", data={
    "username": "user@example.com",  # Note: uses 'username' field for email
    "password": "SecurePassword123!"
})

token_data = response.json()
access_token = token_data["access_token"]
```

### 3. Accessing Protected Endpoints

```python
# Use the JWT token in Authorization header
headers = {"Authorization": f"Bearer {access_token}"}

# Access protected endpoint
response = requests.get("http://localhost:8000/users/me", headers=headers)
user_profile = response.json()
```

## Environment Variables

Add these variables to your `.env` file:

```bash
# Authentication Configuration
SECRET_KEY=your-super-secret-jwt-key-change-this-in-production-must-be-long-and-random

# Database Configuration
DATABASE_URL=postgresql+asyncpg://brainflash:brainflash_password@db:5432/brainflash

# API Security (for legacy endpoints)
API_KEY=your_api_key_here
```

## User Model

The user model includes the following fields:

```python
{
    "id": "uuid",
    "email": "string",
    "first_name": "string (optional)",
    "last_name": "string (optional)",
    "is_active": "boolean",
    "is_superuser": "boolean",
    "is_verified": "boolean",
    "created_at": "datetime"
}
```

## Security Features

### Password Security
- **Argon2 Hashing**: Industry-standard password hashing algorithm
- **Salt Generation**: Automatic salt generation for each password
- **Secure Verification**: Constant-time password verification

### JWT Token Security
- **Secure Secret**: Configurable JWT signing secret
- **Token Expiration**: 1-hour token lifetime (configurable)
- **Bearer Token Transport**: Secure token transmission

### Access Control
- **Authentication Required**: Protected endpoints require valid JWT tokens
- **Role-Based Access**: Superuser roles for administrative functions
- **API Key Fallback**: Legacy API key support for specific endpoints

## Testing the Authentication System

Run the included test script to verify the authentication system:

```bash
python test_auth.py
```

This will test:
- ✅ Unauthorized access rejection
- ✅ User registration
- ✅ User login
- ✅ Protected endpoint access
- ✅ User profile retrieval
- ✅ User logout

## Migration from API Key

The system maintains backward compatibility with API key authentication for specific endpoints:

- **New Authentication**: Use JWT tokens for user-specific operations
- **Legacy Support**: API key still works for `/tts/synthesize` endpoint
- **Dual Mode**: Both authentication methods can coexist

## Common Use Cases

### Frontend Integration
```javascript
// Login and store token
const loginResponse = await fetch('/auth/jwt/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: 'username=user@example.com&password=SecurePassword123!'
});
const { access_token } = await loginResponse.json();
localStorage.setItem('token', access_token);

// Use token for authenticated requests
const response = await fetch('/users/me', {
    headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
});
```

### Mobile App Integration
```swift
// Swift example for iOS
let token = UserDefaults.standard.string(forKey: "jwt_token")
var request = URLRequest(url: URL(string: "http://localhost:8000/users/me")!)
request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
```

## Troubleshooting

### Common Issues

1. **"Invalid JWT token"**: Token may be expired or malformed
   - Solution: Re-authenticate to get a new token

2. **"User already exists"**: Email already registered
   - Solution: Use a different email or login instead

3. **"Authentication required"**: Missing or invalid token
   - Solution: Include valid Bearer token in Authorization header

4. **"Permission denied"**: Insufficient user privileges
   - Solution: Contact admin for appropriate permissions

### Debug Mode

In development, enable SQL logging by setting `ENV=dev` to see database queries and debug authentication issues.

## Production Deployment

### Security Checklist

- [ ] Generate a strong, random `SECRET_KEY`
- [ ] Use HTTPS for all authentication endpoints
- [ ] Set secure database credentials
- [ ] Disable debug mode (`ENV=prod`)
- [ ] Configure rate limiting for auth endpoints
- [ ] Set up proper CORS policies
- [ ] Enable database backups
- [ ] Monitor authentication logs

### Performance Considerations

- JWT tokens are stateless (no database lookup required)
- User sessions scale horizontally
- Database connection pooling configured
- Async/await for non-blocking operations

---

## 🎉 Authentication System Successfully Implemented!

Your BrainFlash server now has enterprise-grade authentication with:
- Secure user management
- JWT token authentication  
- PostgreSQL storage
- Role-based access control
- Production-ready security features
