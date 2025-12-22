# Kenya SMB Accounting MVP - Quick Start Guide

## Prerequisites Installed

- Python 3.11+
- Git (optional)
- Code editor (VS Code recommended)

## 5-Minute Setup

### Step 1: Navigate to Backend

```bash
cd /mnt/c/Users/Dell/Desktop/Kenya-Accounting/backend
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (WSL/Linux - if you're using WSL)
source venv/bin/activate
```

Your terminal should now show `(venv)` at the beginning.

### Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This will take 2-3 minutes. You should see packages being installed.

### Step 4: Get Supabase Database Password

1. Open your browser
2. Go to: https://supabase.com/dashboard
3. Select your project: `hmegnaodyosjpgcbgdes`
4. Click: Settings (gear icon) > Database
5. Find "Database password" section
6. Copy your password OR reset it if you don't remember

### Step 5: Update Database Connection

Open `/backend/.env` file and find this line:

```
DATABASE_URL=postgresql+asyncpg://postgres.hmegnaodyosjpgcbgdes:[YOUR_DB_PASSWORD]@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres
```

Replace `[YOUR_DB_PASSWORD]` with your actual password from Step 4.

Example:
```
DATABASE_URL=postgresql+asyncpg://postgres.hmegnaodyosjpgcbgdes:MySecurePassword123@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres
```

Save the file.

### Step 6: Verify Setup (Optional)

```bash
python verify_setup.py
```

This script checks if everything is configured correctly. Fix any errors before proceeding.

### Step 7: Setup Database

```bash
# Run migrations to create tables
alembic upgrade head
```

Expected output:
```
INFO  [alembic.runtime.migration] Running upgrade  -> 001_initial, Initial schema
```

### Step 8: Start the Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Step 9: Test the API

Open your browser and visit:

1. **API Documentation**: http://localhost:8000/docs
   - You should see interactive API documentation

2. **Health Check**: http://localhost:8000/api/v1/health
   - You should see:
   ```json
   {
     "status": "healthy",
     "version": "1.0.0",
     "database": "connected",
     "timestamp": "2025-12-06T..."
   }
   ```

3. **Root Endpoint**: http://localhost:8000
   - You should see basic API information

## Success! Your backend is running.

Press `CTRL+C` in the terminal to stop the server.

## Common Issues

### Issue: "ModuleNotFoundError"

**Solution**:
```bash
pip install -r requirements.txt
```

### Issue: Database connection fails

**Solution**:
1. Check your database password in `.env` is correct
2. Verify your Supabase project is active
3. Check internet connection

### Issue: "could not connect to server"

**Solution**:
Run in Supabase SQL Editor:
```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

### Issue: Port 8000 already in use

**Solution**:
Use a different port:
```bash
uvicorn app.main:app --reload --port 8001
```

## Next Steps

Now that your backend is running:

1. **Create your first user** (coming in next sprint)
2. **Test authentication endpoints** (coming in next sprint)
3. **Connect frontend** (coming in next sprint)

## Daily Development Workflow

1. **Start backend**:
   ```bash
   cd /mnt/c/Users/Dell/Desktop/Kenya-Accounting/backend
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   uvicorn app.main:app --reload
   ```

2. **Make changes** to code - server auto-reloads

3. **Test changes** at http://localhost:8000/docs

4. **Stop server**: Press CTRL+C

## Project Structure

```
backend/
├── app/
│   ├── main.py           # Start here
│   ├── config.py         # Configuration
│   ├── core/             # Security, encryption, caching
│   ├── models/           # Database models
│   ├── schemas/          # API request/response schemas
│   ├── api/v1/           # API endpoints
│   └── db/               # Database configuration
├── alembic/              # Database migrations
├── .env                  # Environment variables (SECRET)
└── requirements.txt      # Dependencies
```

## Helpful Commands

```bash
# Install new package
pip install package-name
pip freeze > requirements.txt

# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# View current migration
alembic current

# Run tests (when available)
pytest

# Format code
black app/

# Check code quality
ruff check app/
```

## Getting Help

1. Check `README.md` in `/backend/` folder
2. Check `BACKEND_SETUP_COMPLETE.md` for detailed setup
3. Visit FastAPI docs: https://fastapi.tiangolo.com/
4. Visit Supabase docs: https://supabase.com/docs

## What's Already Built

- FastAPI application with CORS
- PostgreSQL database with Supabase
- User authentication (JWT ready)
- AES-256-GCM encryption for sensitive data
- Row Level Security (RLS) policies
- Audit logging
- Health check endpoint
- Database migrations with Alembic
- Type-safe request/response validation

## What's Next (Sprint 1)

- Authentication endpoints (login, logout, register)
- User management endpoints
- Business management endpoints
- Onboarding workflow
- Frontend integration

---

**Remember**: Never commit the `.env` file to version control. It's already in `.gitignore`.

Happy coding!
