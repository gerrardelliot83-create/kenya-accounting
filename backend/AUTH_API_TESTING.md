# Authentication API Testing Guide

This guide provides curl commands and testing procedures for all authentication endpoints.

## Prerequisites

1. **Database Migration**: Run the migration to add password_hash field:
   ```bash
   alembic upgrade head
   ```

2. **Create Test User**: First, you need to create a test user in the database. You can use the following SQL (run in Supabase SQL editor):

   ```sql
   -- Create a test user with encrypted email and hashed password
   -- Password: TestPass123
   -- Password hash below is bcrypt hash of "TestPass123"

   INSERT INTO users (
       id,
       email_encrypted,
       password_hash,
       first_name,
       last_name,
       role,
       is_active,
       must_change_password
   ) VALUES (
       uuid_generate_v4(),
       'ENCRYPTED_EMAIL_HERE',  -- You'll need to encrypt this using the encryption service
       '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqJQrKQW9u',  -- Hash of "TestPass123"
       'Test',
       'User',
       'business_admin',
       true,
       false
   );
   ```

3. **Start the Server**:
   ```bash
   uvicorn app.main:app --reload
   ```

   Server will be running at: http://localhost:8000

## API Endpoints

Base URL: `http://localhost:8000/api/v1`

### 1. Login (POST /auth/login)

Authenticate user and receive access and refresh tokens.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123"
  }'
```

**Success Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User",
    "phone": null,
    "role": "business_admin",
    "business_id": null,
    "is_active": true,
    "must_change_password": false,
    "last_login_at": "2025-12-06T12:00:00",
    "created_at": "2025-12-06T00:00:00",
    "updated_at": "2025-12-06T12:00:00"
  }
}
```

**Error Responses:**
- 401: Invalid credentials
- 429: Too many login attempts (rate limit: 5 attempts per 5 minutes)

**Security Features:**
- Rate limited to 5 attempts per 5 minutes per email
- All login attempts logged to audit_logs
- Generic error messages to prevent user enumeration

---

### 2. Get Current User (GET /auth/me)

Get information about the currently authenticated user.

**Request:**
```bash
# Replace YOUR_ACCESS_TOKEN with the token from login
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Success Response (200):**
```json
{
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User",
    "phone": null,
    "role": "business_admin",
    "business_id": null,
    "is_active": true,
    "must_change_password": false,
    "last_login_at": "2025-12-06T12:00:00",
    "created_at": "2025-12-06T00:00:00",
    "updated_at": "2025-12-06T12:00:00"
  }
}
```

**Error Responses:**
- 401: Not authenticated or invalid token

---

### 3. Refresh Access Token (POST /auth/refresh)

Get a new access token using a valid refresh token.

**Request:**
```bash
# Replace YOUR_REFRESH_TOKEN with the refresh token from login
curl -X POST "http://localhost:8000/api/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "YOUR_REFRESH_TOKEN"
  }'
```

**Success Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error Responses:**
- 401: Invalid or expired refresh token

---

### 4. Change Password (POST /auth/change-password)

Change the current user's password.

**Request:**
```bash
# Replace YOUR_ACCESS_TOKEN with the token from login
curl -X POST "http://localhost:8000/api/v1/auth/change-password" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "TestPass123",
    "new_password": "NewSecurePass456"
  }'
```

**Password Requirements:**
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number

**Success Response (200):**
```json
{
  "message": "Password changed successfully"
}
```

**Error Responses:**
- 400: Current password incorrect or password requirements not met
- 401: Not authenticated

**Security Features:**
- Requires current password verification
- Password complexity validation
- Clears must_change_password flag
- Invalidates user cache
- Logs password change to audit_logs

---

### 5. Logout (POST /auth/logout)

Logout the current user and invalidate the session.

**Request:**
```bash
# Replace YOUR_ACCESS_TOKEN with the token from login
curl -X POST "http://localhost:8000/api/v1/auth/logout" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Success Response (200):**
```json
{
  "message": "Successfully logged out"
}
```

**Error Responses:**
- 401: Not authenticated

**Note:** For stateless JWT tokens, the token remains valid until expiration. This endpoint clears server-side cache and logs the logout event.

---

## Complete Test Flow

Here's a complete test flow to verify all endpoints:

```bash
# 1. Login
LOGIN_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123"
  }')

echo "Login Response:"
echo $LOGIN_RESPONSE | jq .

# Extract tokens
ACCESS_TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')
REFRESH_TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.refresh_token')

# 2. Get current user info
echo -e "\n\nGet Current User:"
curl -s -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq .

# 3. Refresh access token
echo -e "\n\nRefresh Token:"
NEW_TOKEN_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\": \"$REFRESH_TOKEN\"}")

echo $NEW_TOKEN_RESPONSE | jq .

NEW_ACCESS_TOKEN=$(echo $NEW_TOKEN_RESPONSE | jq -r '.access_token')

# 4. Change password
echo -e "\n\nChange Password:"
curl -s -X POST "http://localhost:8000/api/v1/auth/change-password" \
  -H "Authorization: Bearer $NEW_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "TestPass123",
    "new_password": "NewSecurePass456"
  }' | jq .

# 5. Login with new password
echo -e "\n\nLogin with New Password:"
curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "NewSecurePass456"
  }' | jq .

# 6. Logout
echo -e "\n\nLogout:"
curl -s -X POST "http://localhost:8000/api/v1/auth/logout" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq .
```

## API Documentation

Once the server is running, you can access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Security Testing

### Test Rate Limiting

Try logging in with wrong credentials 6 times rapidly:

```bash
for i in {1..6}; do
  echo "Attempt $i:"
  curl -X POST "http://localhost:8000/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d '{
      "email": "test@example.com",
      "password": "WrongPassword"
    }'
  echo -e "\n"
done
```

The 6th attempt should return a 429 error.

### Test Invalid Token

```bash
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer invalid_token_here"
```

Should return 401 Unauthorized.

### Test Expired Token

Wait for the access token to expire (default: 30 minutes) and try to access /auth/me.

## Audit Logging

All authentication events are logged to the `audit_logs` table. Check the logs:

```sql
SELECT
    action,
    status,
    ip_address,
    created_at,
    error_message
FROM audit_logs
WHERE action IN ('login', 'login_failed', 'logout', 'password_change')
ORDER BY created_at DESC
LIMIT 20;
```

## Troubleshooting

### Issue: "User not found or inactive"

- Verify the user exists in the database
- Check that `is_active` is true
- Ensure the email is properly encrypted

### Issue: "Could not validate credentials"

- Check that JWT_SECRET_KEY is properly set in .env
- Verify token hasn't expired
- Ensure token is properly formatted in Authorization header

### Issue: "Current password is incorrect"

- Verify the password hash in the database
- Check that bcrypt is properly installed
- Ensure password was set correctly during user creation

### Issue: Rate limit exceeded

- Wait 5 minutes before trying again
- Or clear the cache (for development only)

## Creating Additional Test Users

To create more test users for testing different roles:

```python
# Run this in a Python shell or script
from app.services.user_service import UserService
from app.db.session import get_db_context
from app.models.user import UserRole
import asyncio

async def create_test_user():
    async with get_db_context() as db:
        user_service = UserService(db)

        user = await user_service.create_user(
            email="admin@example.com",
            password="AdminPass123",
            role=UserRole.SYSTEM_ADMIN,
            first_name="System",
            last_name="Admin",
            must_change_password=False
        )

        print(f"Created user: {user.id}")

asyncio.run(create_test_user())
```

## Token Information

### Access Token
- **Lifetime**: 30 minutes (configurable in .env: JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
- **Contents**: user_id, role, business_id, email (as subject)
- **Use**: For authenticating API requests

### Refresh Token
- **Lifetime**: 7 days (configurable in .env: JWT_REFRESH_TOKEN_EXPIRE_DAYS)
- **Contents**: user_id, email (as subject)
- **Use**: For obtaining new access tokens without re-authentication

## Next Steps

After testing the authentication endpoints, you can:

1. **Implement User Management Endpoints** (CRUD operations for users)
2. **Implement Business Management Endpoints**
3. **Add Role-Based Access Control** to endpoints
4. **Implement Password Reset Flow** (email-based)
5. **Add Two-Factor Authentication** (optional)
6. **Implement Token Blacklisting** (for logout)
