# Kenya SMB Accounting - Deployment Status

**Last Updated:** December 22, 2025

## Deployment Summary

The Kenya SMB Accounting MVP has been successfully deployed to Railway.

### Live URLs

| Service | URL | Status |
|---------|-----|--------|
| Backend API | https://kenya-accounting-production.up.railway.app | Online |
| Frontend App | https://loyal-serenity-production.up.railway.app | Online |
| Target Domain | https://accounting.pakta.app | Pending DNS setup |

### Backend Health Check
```
https://kenya-accounting-production.up.railway.app/api/v1/health
```

---

## Test User Accounts

| Email | Password | Role | Portal Access |
|-------|----------|------|---------------|
| admin@example.com | AdminPass123 | system_admin | All portals |
| business@example.com | BusinessPass123 | business_admin | Business Portal only |
| bookkeeper@example.com | BookkeeperPass123 | bookkeeper | Business Portal only |
| onboarding@example.com | OnboardPass123 | onboarding_agent | Onboarding Portal |
| support@example.com | SupportPass123 | support_agent | Support Portal |

---

## Portal Access Guide

### 1. Business Portal (Main App)
- **URL:** `/dashboard`
- **Roles:** business_admin, business_user, bookkeeper
- **Features:**
  - Dashboard with financial overview
  - Contacts management
  - Items/Services catalog
  - Invoice creation and management (with PDF export)
  - Expense tracking
  - Bank statement imports and reconciliation
  - Tax dashboard (VAT/TOT summaries)
  - Financial reports
  - Help center and support tickets

### 2. Onboarding Portal
- **URL:** `/onboarding`
- **Roles:** onboarding_agent, system_admin
- **Login:** Use `onboarding@example.com` / `OnboardPass123` or `admin@example.com` / `AdminPass123`
- **Features:**
  - Onboarding dashboard with statistics
  - Create new business applications
  - Application queue management
  - Review and approve/reject applications
  - Application detail view

### 3. Support Portal
- **URL:** `/support-portal`
- **Roles:** support_agent, system_admin
- **Login:** Use `support@example.com` / `SupportPass123` or `admin@example.com` / `AdminPass123`
- **Features:**
  - Support dashboard with ticket statistics
  - Ticket list with filtering
  - Ticket detail view with conversation
  - Agent assignment
  - Internal notes
  - Canned responses

### 4. Admin Portal
- **URL:** `/admin`
- **Roles:** system_admin only
- **Login:** Use `admin@example.com` / `AdminPass123`
- **Features:**
  - Admin dashboard with system statistics
  - Business directory
  - Internal user management
  - Audit log viewer
  - System health monitoring

---

## Technology Stack

### Backend
- **Framework:** FastAPI (Python 3.11)
- **Database:** PostgreSQL (Supabase)
- **Authentication:** JWT tokens
- **PDF Generation:** WeasyPrint
- **Email:** Brevo SMTP (aiosmtplib)
- **Hosting:** Railway (Docker)

### Frontend
- **Framework:** React 18 + TypeScript
- **Build Tool:** Vite 7
- **UI Components:** Shadcn/UI + Tailwind CSS
- **State Management:** Zustand + React Query
- **Routing:** React Router v6
- **Hosting:** Railway (Nixpacks)

---

## Environment Variables

### Backend (Railway)
```
ENVIRONMENT=production
DEBUG=False
SUPABASE_URL=https://hmegnaodyosjpgcbgdes.supabase.co
SUPABASE_ANON_KEY=<configured>
SUPABASE_SERVICE_ROLE_KEY=<configured>
DATABASE_URL=postgresql+asyncpg://...
JWT_SECRET_KEY=<configured>
ENCRYPTION_KEY=<configured>
UPLOADTHING_TOKEN=<configured>
CORS_ORIGINS=["https://accounting.pakta.app","https://loyal-serenity-production.up.railway.app","http://localhost:5173"]
EMAIL_ENABLED=True
SMTP_HOST=smtp-relay.brevo.com
SMTP_PORT=587
SMTP_USER=<configured>
SMTP_PASSWORD=<configured>
SMTP_FROM_EMAIL=aenesh@pakta.app
SMTP_FROM_NAME=Kenya SMB Accounting
SMTP_USE_TLS=True
```

### Frontend (Railway)
```
VITE_SUPABASE_URL=https://hmegnaodyosjpgcbgdes.supabase.co
VITE_SUPABASE_ANON_KEY=<configured>
VITE_API_URL=https://kenya-accounting-production.up.railway.app/api/v1
```

---

## Current Application Status

### Completed Features (Phase 1 + Phase 2)

**Core Accounting:**
- Contact management with encryption
- Items/Services catalog
- Invoice CRUD with line items
- Invoice PDF generation
- Invoice status workflow (draft -> issued -> paid/cancelled)
- Expense tracking with categories
- Receipt upload support

**Bank Reconciliation:**
- CSV bank statement import
- Column mapping wizard
- Fuzzy matching for transaction reconciliation
- Manual match/unmatch/ignore

**Tax Module:**
- VAT summary reports (16% rate)
- TOT summary reports (1% rate)
- Tax settings configuration
- Filing guidance

**Reports:**
- Profit & Loss report
- Expense summary by category
- Aged receivables
- Sales summary

**Help & Support (Customer-facing):**
- FAQ categories and articles
- Support ticket submission
- Ticket conversation view
- Ticket rating

**Internal Portals:**
- Onboarding Portal for new business setup
- Support Portal for ticket management
- Admin Portal for system administration

**Security:**
- JWT authentication with refresh tokens
- Rate limiting (SlowAPI)
- IP blocking after failed attempts
- Field-level encryption (PII fields)
- Audit logging
- Security headers

**Email:**
- Welcome emails for new users
- Password reset emails
- Invoice notification emails (via Brevo SMTP)

---

## Known Issues / Pre-Production Fixes Needed

*To be documented based on user testing...*

---

## Custom Domain Setup (Pending)

To configure `accounting.pakta.app`:

1. Go to frontend service in Railway → Settings → Networking
2. Click "+ Custom Domain"
3. Enter: `accounting.pakta.app`
4. Add CNAME record in DNS:
   - Name: `accounting`
   - Value: `loyal-serenity-production.up.railway.app`
5. Update backend `CORS_ORIGINS` to include the new domain

---

## Files Modified for Deployment

- `backend/Dockerfile` - Python 3.11 with WeasyPrint and bcrypt dependencies
- `backend/railway.json` - Health check configuration
- `backend/requirements.txt` - Production dependencies
- `frontend/railway.json` - Nixpacks build configuration
- `frontend/src/lib/api.ts` - JWT token storage in localStorage
