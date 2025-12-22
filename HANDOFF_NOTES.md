# Kenya SMB Accounting - Agent Handoff Document

**Date:** December 22, 2025
**Status:** Deployed to Railway (Staging) - Pre-Production Fixes Required

---

## CRITICAL: First Steps for New Agent

Before making any changes, read these documents in order:

1. **Architecture Overview:** `Kenya_SMB_Accounting_MVP_System_Architecture.md` (root directory)
2. **Deployment Status:** `DEPLOYMENT_STATUS.md` (root directory)
3. **This Document:** Continue reading for known issues and fix strategies

---

## Project Overview

### What is This?
A cloud-based accounting application for small and medium businesses in Kenya, featuring:
- Invoice management with PDF generation
- Expense tracking
- Bank statement import and reconciliation
- Tax compliance (VAT 16%, TOT 1%)
- Multi-portal architecture (Business, Onboarding, Support, Admin)

### Live Deployment URLs

| Service | URL | Status |
|---------|-----|--------|
| Backend API | https://kenya-accounting-production.up.railway.app | Online |
| Frontend App | https://loyal-serenity-production.up.railway.app | Online |
| Health Check | https://kenya-accounting-production.up.railway.app/api/v1/health | Online |

### Test Accounts

| Email | Password | Role | Access |
|-------|----------|------|--------|
| admin@example.com | AdminPass123 | system_admin | All portals |
| business@example.com | BusinessPass123 | business_admin | Business Portal |
| bookkeeper@example.com | BookkeeperPass123 | bookkeeper | Business Portal |
| onboarding@example.com | OnboardPass123 | onboarding_agent | Onboarding Portal |
| support@example.com | SupportPass123 | support_agent | Support Portal |

---

## Technology Stack

### Backend (`/backend`)
- **Framework:** FastAPI (Python 3.11)
- **Database:** PostgreSQL via Supabase
- **ORM:** SQLAlchemy 2.0 (async)
- **Authentication:** JWT tokens (python-jose)
- **Password Hashing:** bcrypt via passlib
- **PDF Generation:** WeasyPrint
- **Email:** aiosmtplib via Brevo SMTP
- **Hosting:** Railway (Docker)

### Frontend (`/frontend`)
- **Framework:** React 18 + TypeScript
- **Build Tool:** Vite 7
- **UI Library:** Shadcn/UI + Tailwind CSS
- **State Management:** Zustand (auth) + React Query (server state)
- **Routing:** React Router v6
- **Hosting:** Railway (Nixpacks)

### Key Configuration Files
- `backend/app/config.py` - All backend settings (loaded from environment)
- `backend/Dockerfile` - Production Docker build
- `frontend/src/lib/api.ts` - API client with auth token handling
- `frontend/src/stores/authStore.ts` - Auth state management
- `frontend/src/routes/index.tsx` - All route definitions with role guards

---

## Codebase Structure

```
Kenya-Accounting/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/    # All API routes
│   │   ├── core/                # Security, rate limiting, encryption
│   │   ├── db/                  # Database session management
│   │   ├── models/              # SQLAlchemy models
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── services/            # Business logic layer
│   │   ├── config.py            # Settings from environment
│   │   └── main.py              # FastAPI app initialization
│   ├── alembic/                 # Database migrations
│   ├── templates/               # Email and PDF templates
│   ├── tests/                   # Pytest test suites
│   ├── Dockerfile               # Production Docker config
│   ├── requirements.txt         # Python dependencies
│   └── railway.json             # Railway deploy config
│
├── frontend/
│   ├── src/
│   │   ├── components/          # Reusable UI components
│   │   │   ├── common/          # Shared components
│   │   │   ├── layout/          # Layout components (MainLayout, AdminLayout, etc.)
│   │   │   ├── ui/              # Shadcn/UI components
│   │   │   └── support-portal/  # Support-specific components
│   │   ├── hooks/               # Custom React hooks
│   │   ├── lib/                 # Utilities (api.ts, formatters, etc.)
│   │   ├── pages/               # Page components by feature
│   │   │   ├── admin/           # Admin portal pages
│   │   │   ├── auth/            # Login, change password
│   │   │   ├── bank-imports/    # Bank reconciliation
│   │   │   ├── contacts/        # Contact management
│   │   │   ├── dashboard/       # Main dashboard
│   │   │   ├── expenses/        # Expense tracking
│   │   │   ├── help/            # Help center & tickets
│   │   │   ├── invoices/        # Invoice CRUD
│   │   │   ├── items/           # Items/services catalog
│   │   │   ├── onboarding/      # Onboarding portal pages
│   │   │   ├── reports/         # Financial reports
│   │   │   ├── support-portal/  # Support agent pages
│   │   │   └── tax/             # Tax dashboard
│   │   ├── routes/              # Route definitions
│   │   ├── services/            # Mock services (onboardingService)
│   │   ├── stores/              # Zustand stores
│   │   └── types/               # TypeScript type definitions
│   ├── railway.json             # Railway deploy config
│   └── package.json             # Node dependencies
│
├── Issues/                      # Local issue tracking (gitignored)
├── DEPLOYMENT_STATUS.md         # Current deployment info
├── HANDOFF_NOTES.md             # This document
└── Kenya_SMB_Accounting_MVP_System_Architecture.md  # Full architecture doc
```

---

## Portal Access & Routing

### Business Portal (Main App)
- **Base Path:** `/dashboard`
- **Roles:** business_admin, business_user, bookkeeper
- **Layout:** `MainLayout.tsx`
- **Routes:** See `/frontend/src/routes/index.tsx` lines 52-106

### Onboarding Portal
- **Base Path:** `/onboarding`
- **Roles:** onboarding_agent, system_admin
- **Layout:** `OnboardingLayout.tsx`
- **Routes:** Lines 118-132

### Support Portal
- **Base Path:** `/support-portal`
- **Roles:** support_agent, system_admin
- **Layout:** `SupportPortalLayout.tsx`
- **Routes:** Lines 134-148

### Admin Portal
- **Base Path:** `/admin`
- **Roles:** system_admin only
- **Layout:** `AdminLayout.tsx`
- **Routes:** Lines 150-165

---

## KNOWN ISSUES (Pre-Production Fixes Required)

### Issue 1-2, 4-7: HTTPS/Mixed Content Error (CRITICAL - 6 ISSUES)

**Symptoms:**
- Contacts not being created
- Items not being created
- Bank statement upload fails
- Clicking Expenses logs user out
- Clicking Tax logs user out
- Clicking any Report logs user out

**Root Cause:**
The `VITE_API_URL` environment variable in Railway frontend service is set with `http://` instead of `https://`. Browser blocks mixed content requests.

**Evidence from console:**
```
Mixed Content: The page at 'https://loyal-serenity-production.up.railway.app/dashboard'
was loaded over HTTPS, but requested an insecure XMLHttpRequest endpoint
'http://kenya-accounting-production.up.railway.app/api/v1/contacts/?limit=1'.
This request has been blocked.
```

**Fix Strategy:**
1. Go to Railway Dashboard → Frontend Service → Variables
2. Change `VITE_API_URL` from:
   ```
   http://kenya-accounting-production.up.railway.app/api/v1
   ```
   to:
   ```
   https://kenya-accounting-production.up.railway.app/api/v1
   ```
3. Railway will auto-redeploy

**Files Involved:** None - this is a configuration fix only.

---

### Issue 3: Invoice Creation - Select.Item Empty Value Error

**Symptom:**
When clicking "New Invoice", the page crashes with:
```
Error: A <Select.Item /> must have a value prop that is not an empty string.
```

**Root Cause:**
The invoice form renders Contact/Item dropdowns using data from API. If any contact or item has an empty/undefined ID, the Select component crashes.

**Fix Strategy:**
1. Open `frontend/src/pages/invoices/InvoiceFormPage.tsx`
2. Find where contacts and items are mapped to `<SelectItem>` components
3. Filter out any items with empty/null/undefined IDs before rendering
4. Example fix:
   ```tsx
   {contacts?.filter(c => c.id).map((contact) => (
     <SelectItem key={contact.id} value={contact.id}>
       {contact.name}
     </SelectItem>
   ))}
   ```

**Files to Modify:**
- `frontend/src/pages/invoices/InvoiceFormPage.tsx`

---

### Issue 8: Payments & Settings Show "Coming Soon"

**Symptom:**
The Payments and Settings navigation items show placeholder text.

**Context:**
These were intentionally left as placeholders in the MVP scope. Core payment functionality exists through invoices (marking as paid/cancelled).

**Decision Required:**
Ask user if they want these implemented before production:
- **Payments Page:** Would show payment history, allow recording payments against invoices
- **Settings Page:** Would show user profile, business settings, notification preferences

**Files to Create (if implementing):**
- `frontend/src/pages/payments/PaymentsPage.tsx`
- `frontend/src/pages/settings/SettingsPage.tsx`
- Backend endpoints may already exist or need creation

---

### Issue 9: Help Centre - "r?.map is not a function" Error

**Symptom:**
Help Centre page loads but crashes with:
```
TypeError: r?.map is not a function
```

**Root Cause:**
The Help Centre page expects the FAQ API to return an array, but it's receiving a different data structure (likely an object with nested array, or an error response).

**Fix Strategy:**
1. Check the API endpoint response format:
   - `GET /api/v1/support/faq/categories`
   - `GET /api/v1/support/faq`
2. Update the frontend to handle the actual response format
3. Add defensive coding for error cases

**Files to Check:**
- `frontend/src/pages/help/HelpCentrePage.tsx`
- `frontend/src/hooks/useHelp.ts` (if exists)
- `backend/app/api/v1/endpoints/support.py` - FAQ endpoints

---

## Priority Fix Order

| Priority | Issue | Fix Type | Effort |
|----------|-------|----------|--------|
| 1 | HTTPS/Mixed Content (Issues 1,2,4,5,6,7) | Config change in Railway | 2 min |
| 2 | Invoice Select.Item (Issue 3) | Code fix | 15 min |
| 3 | Help Centre map error (Issue 9) | Code fix | 30 min |
| 4 | Payments/Settings (Issue 8) | New feature | TBD |

---

## Environment Variables Reference

### Backend (Railway)
```
ENVIRONMENT=production
DEBUG=False
SUPABASE_URL=https://hmegnaodyosjpgcbgdes.supabase.co
SUPABASE_ANON_KEY=<configured>
SUPABASE_SERVICE_ROLE_KEY=<configured>
DATABASE_URL=postgresql+asyncpg://postgres.hmegnaodyosjpgcbgdes:BhCrT50yYWjNCUcC@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres
JWT_SECRET_KEY=<configured>
ENCRYPTION_KEY=<configured>
UPLOADTHING_TOKEN=<configured>
LLAMA_CLOUD_API_KEY=llx-placeholder
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

### Frontend (Railway) - IMPORTANT
```
VITE_SUPABASE_URL=https://hmegnaodyosjpgcbgdes.supabase.co
VITE_SUPABASE_ANON_KEY=<configured>
VITE_API_URL=https://kenya-accounting-production.up.railway.app/api/v1  # MUST be HTTPS!
```

**NOTE:** The `VITE_API_URL` MUST use `https://` not `http://`. This is the root cause of Issues 1,2,4,5,6,7.

---

## Authentication Flow

1. User submits login credentials
2. Backend validates and returns `accessToken` + `refreshToken`
3. Frontend stores tokens in `localStorage` (see `frontend/src/lib/api.ts`)
4. All API requests include `Authorization: Bearer <accessToken>` header
5. On 401 response, tokens are cleared and user redirected to `/login`

**Key Files:**
- `frontend/src/lib/api.ts` - Token storage and request interceptor
- `frontend/src/stores/authStore.ts` - Auth state management
- `backend/app/api/v1/endpoints/auth.py` - Login/logout/refresh endpoints
- `backend/app/services/auth_service.py` - Auth business logic

---

## Database Schema

The database uses Supabase (PostgreSQL). Key tables:

- `users` - User accounts with encrypted PII fields
- `businesses` - Business entities
- `contacts` - Customer/vendor contacts (encrypted fields)
- `items` - Products/services catalog
- `invoices` - Invoice headers
- `invoice_line_items` - Invoice line items
- `expenses` - Expense records
- `expense_categories` - Expense categories
- `bank_imports` - Bank statement imports
- `bank_transactions` - Parsed bank transactions
- `support_tickets` - Help desk tickets
- `ticket_messages` - Ticket conversation messages
- `audit_logs` - Security audit trail

**Migrations:** Located in `backend/alembic/versions/`

---

## Security Features

1. **Field-Level Encryption:** PII fields (email, phone, national_id, bank_account, kra_pin) are encrypted at rest
2. **JWT Authentication:** Access tokens (30 min) + Refresh tokens (7 days)
3. **Rate Limiting:** SlowAPI middleware with per-endpoint limits
4. **IP Blocking:** Auto-block after 10 failed login attempts
5. **Audit Logging:** All sensitive operations logged to `audit_logs` table
6. **Security Headers:** CSP, HSTS, X-Frame-Options via middleware

---

## Testing

### Backend Tests
```bash
cd backend
source venv/bin/activate
TESTING=true python -m pytest tests/ -v
```

**Test Results:** 165/167 passing (2 skipped need LlamaParse API)

### Frontend Build Test
```bash
cd frontend
npm run build
```

### E2E Tests (Playwright)
```bash
cd frontend
npx playwright test
```

---

## Deployment Process

### To Deploy Changes:
1. Make code changes locally
2. Test with `npm run build` (frontend) or `pytest` (backend)
3. Commit changes to git
4. Push to GitHub via GitHub Desktop
5. Railway auto-deploys on push to main branch

### Railway Dashboard:
- Project contains 2 services: backend and frontend
- Each service has its own Variables, Logs, and Settings

---

## Project Statistics

| Metric | Value |
|--------|-------|
| Total API Endpoints | 104+ |
| Total Database Tables | 20 |
| Backend Tests | 167 (165 passing) |
| Sprints Completed | 6 of 6 |
| Frontend Pages | 45+ |

---

## Notes for Next Agent

1. **Always test locally before deploying**
2. The user prefers using GitHub Desktop for git operations
3. Do not include Claude Code references in commit messages
4. The Issues folder is gitignored - it contains user-reported bugs
5. Check `DEPLOYMENT_STATUS.md` for current deployment state
6. JWT tokens are stored in localStorage (not httpOnly cookies)
7. When committing, create clean commit messages without AI tool references

---

## Quick Start Commands

```bash
# Start backend locally
cd /mnt/c/Users/Dell/Desktop/Kenya-Accounting/backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Run backend tests
TESTING=true python -m pytest tests/ -v

# Check server health
curl http://localhost:8000/api/v1/health

# Start frontend locally
cd /mnt/c/Users/Dell/Desktop/Kenya-Accounting/frontend
npm run dev

# Build frontend
npm run build
```

---

## Contact & Resources

- **GitHub Repo:** https://github.com/gerrardelliot83-create/kenya-accounting
- **Railway Dashboard:** User has access
- **Supabase Dashboard:** https://supabase.com/dashboard (user has access)

---

*Last Updated: December 22, 2025*
*Next Agent: Fix HTTPS config in Railway, then fix Invoice Select and Help Centre issues*
