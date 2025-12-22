# Deployment Handoff - December 22, 2025

## CURRENT STATUS: Railway Deployment In Progress

### What's Done
- GitHub repo: https://github.com/gerrardelliot83-create/kenya-accounting
- Backend has Dockerfile configured
- Requirements.txt fixed for dependency conflicts
- Root directory set to `backend` in Railway

### Pending Push
User needs to **push via GitHub Desktop** then **redeploy on Railway**.

The last commit fixed dependency conflicts in requirements.txt.

### Railway Configuration Needed

**Backend Service:**
- Root Directory: `backend` (already set)
- After successful build, add these environment variables in Railway dashboard:

```
ENVIRONMENT=production
DEBUG=False
SUPABASE_URL=https://hmegnaodyosjpgcbgdes.supabase.co
SUPABASE_ANON_KEY=(from backend/.env)
SUPABASE_SERVICE_ROLE_KEY=(from backend/.env)
DATABASE_URL=postgresql+asyncpg://postgres.hmegnaodyosjpgcbgdes:BhCrT50yYWjNCUcC@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres
JWT_SECRET_KEY=(from backend/.env)
ENCRYPTION_KEY=(from backend/.env)
UPLOADTHING_TOKEN=(from backend/.env)
CORS_ORIGINS=["https://accounting.pakta.app"]
EMAIL_ENABLED=True
SMTP_HOST=smtp-relay.brevo.com
SMTP_PORT=587
SMTP_USER=(from backend/.env)
SMTP_PASSWORD=(from backend/.env)
SMTP_FROM_EMAIL=aenesh@pakta.app
SMTP_FROM_NAME=Kenya SMB Accounting
SMTP_USE_TLS=True
```

**Frontend Service:**
- Create new service in same Railway project
- Root Directory: `frontend`
- Environment variables:
```
VITE_SUPABASE_URL=https://hmegnaodyosjpgcbgdes.supabase.co
VITE_SUPABASE_ANON_KEY=(from frontend/.env)
VITE_API_URL=https://<backend-railway-url>/api/v1
```

### Custom Domain
Target: `accounting.pakta.app`
- Add CNAME record pointing to Railway-generated domain

### Files Modified for Deployment
- `backend/Dockerfile` - WeasyPrint dependencies
- `backend/railway.json` - Deploy config
- `backend/requirements.txt` - Fixed dependency conflicts
- `frontend/railway.json` - Deploy config

### LlamaParse Note
`llama-cloud-services` was commented out in requirements.txt due to slow dependency resolution. Add back later if needed for bank statement parsing.

### Test Credentials
- business@example.com / BusinessPass123
- admin@example.com / AdminPass123
