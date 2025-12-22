# Kenya SMB Accounting MVP - Backend

FastAPI backend with PostgreSQL (Supabase), AES-256-GCM encryption, and comprehensive security features.

## Prerequisites

- Python 3.11 or higher
- PostgreSQL (via Supabase)
- Supabase account with project created
- Virtual environment tool (venv or virtualenv)

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Application configuration
│   ├── dependencies.py      # Dependency injection
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py    # Main API router
│   │       └── endpoints/   # API endpoints
│   ├── core/
│   │   ├── __init__.py
│   │   ├── security.py      # JWT, password hashing, RBAC
│   │   ├── encryption.py    # AES-256-GCM encryption
│   │   └── cache.py         # In-memory caching
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── business.py
│   │   └── audit_log.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── business.py
│   │   └── common.py
│   ├── services/
│   │   └── __init__.py
│   └── db/
│       ├── __init__.py
│       ├── base.py          # Base model
│       └── session.py       # Database session
├── alembic/
│   ├── versions/            # Migration files
│   ├── env.py              # Alembic environment
│   └── script.py.mako      # Migration template
├── tests/
├── .env                     # Environment variables (DO NOT COMMIT)
├── .env.example            # Environment template
├── .gitignore
├── alembic.ini             # Alembic configuration
├── requirements.txt        # Python dependencies
└── README.md
```

## Setup Instructions

### 1. Create Virtual Environment

```bash
cd backend
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Unix or MacOS:
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Update `.env` with your actual credentials:
   - Get Supabase credentials from your project settings
   - Get database password from Supabase > Project Settings > Database
   - Generate secure keys for JWT and encryption (see below)

### 4. Generate Secure Keys

```bash
# Generate encryption key
python -c "import secrets; print('ENCRYPTION_KEY=' + secrets.token_urlsafe(32))"

# Generate JWT secret key
python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(64))"
```

### 5. Get Supabase Database Connection String

1. Go to Supabase Dashboard > Project Settings > Database
2. Look for "Connection string" under "Connection pooling"
3. Select "Transaction" mode
4. Copy the connection string and replace placeholders:
   ```
   postgresql+asyncpg://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
   ```

### 6. Supabase Setup

In your Supabase project, you need to:

1. **Enable UUID Extension** (if not already enabled):
   - Go to SQL Editor
   - Run: `CREATE EXTENSION IF NOT EXISTS "uuid-ossp";`

2. **Configure Authentication**:
   - Go to Authentication > Settings
   - Disable "Enable email confirmations" (for MVP testing)
   - Configure email templates as needed

3. **Set up Service Role** (for bypassing RLS in backend):
   - The service role key is already in your project settings
   - Add it to your `.env` file

### 7. Run Database Migrations

```bash
# Create initial migration (already created)
# alembic revision --autogenerate -m "Initial schema"

# Apply migrations
alembic upgrade head
```

### 8. Run the Application

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or using the main.py directly
python -m app.main
```

The API will be available at:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Database Migrations

### Create a new migration

```bash
alembic revision --autogenerate -m "Description of changes"
```

### Apply migrations

```bash
alembic upgrade head
```

### Rollback migration

```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade <revision_id>

# Rollback all migrations
alembic downgrade base
```

### View migration history

```bash
alembic history
alembic current
```

## Security Features

### Encrypted Fields

The following fields are encrypted at rest using AES-256-GCM:
- User: email, phone, national_id
- Business: kra_pin, bank_account_number, tax_certificate_number

### Row Level Security (RLS)

All tables have RLS policies enabled:
- **businesses**: Business admins see only their business, system admins see all
- **users**: Users see their own data, admins see users in their scope
- **audit_logs**: Only system admins and support agents can read

### Audit Logging

All security events are logged to the `audit_logs` table:
- Authentication attempts (success/failure)
- Authorization failures
- Data modifications
- Admin actions

## API Documentation

### Health Check

```bash
curl http://localhost:8000/api/v1/health
```

Response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected",
  "timestamp": "2025-12-06T00:00:00"
}
```

### Authentication

Authentication endpoints will be available at `/api/v1/auth`:
- POST `/api/v1/auth/login` - User login
- POST `/api/v1/auth/refresh` - Refresh access token
- POST `/api/v1/auth/logout` - User logout

## User Roles

- **system_admin**: Full system access
- **business_admin**: Manage their own business
- **bookkeeper**: Accounting operations within business
- **onboarding_agent**: Onboard new businesses
- **support_agent**: Customer support access

## Development

### Code Quality

```bash
# Format code with black
black app/

# Lint with ruff
ruff check app/

# Type checking with mypy
mypy app/
```

### Testing

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=app tests/
```

## Troubleshooting

### Database Connection Issues

1. Verify database URL is correct in `.env`
2. Check Supabase project is active
3. Ensure connection pooling is enabled in Supabase
4. Verify network connectivity to Supabase

### Migration Issues

1. Check database connection
2. Verify Alembic can access models: `alembic current`
3. Check migration files in `alembic/versions/`
4. Review Alembic logs for specific errors

### Encryption Issues

1. Verify ENCRYPTION_KEY is at least 32 characters
2. Never change ENCRYPTION_KEY after encrypting data (data will be unrecoverable)
3. Use different keys for different environments

## Production Deployment

1. Set `ENVIRONMENT=production` in `.env`
2. Set `DEBUG=False`
3. Use strong, unique encryption and JWT keys
4. Enable HTTPS/SSL
5. Configure proper CORS origins
6. Set up proper logging and monitoring
7. Use environment-specific database credentials
8. Implement proper backup strategy

## Support

For issues or questions, contact the development team.

## License

Proprietary - Kenya SMB Accounting MVP
