# Kenya SMB Accounting - Railway Deployment Guide

## Overview

This guide will deploy the application to **accounting.pakta.app** using Railway.

**Architecture:**
- **Backend API**: `api.accounting.pakta.app` (FastAPI)
- **Frontend**: `accounting.pakta.app` (React/Vite)
- **Database**: Supabase PostgreSQL (existing)
- **Main Website**: `pakta.app` (Webflow - separate)

---

## Prerequisites

1. **GitHub Account** - Push your code to GitHub
2. **Railway Account** - Sign up at https://railway.app
3. **Domain Access** - DNS access for pakta.app

---

## Step 1: Prepare Repository

### 1.1 Initialize Git Repository

```bash
cd /mnt/c/Users/Dell/Desktop/Kenya-Accounting

# Initialize git
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: Kenya SMB Accounting MVP"
```

### 1.2 Create GitHub Repository

1. Go to https://github.com/new
2. Create a new repository named `kenya-accounting` (private recommended)
3. Push your code:

```bash
git remote add origin https://github.com/YOUR_USERNAME/kenya-accounting.git
git branch -M main
git push -u origin main
```

---

## Step 2: Deploy Backend on Railway

### 2.1 Create Backend Service

1. Log in to https://railway.app
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose your `kenya-accounting` repository
5. Railway will detect multiple services - select **"backend"** folder

### 2.2 Configure Backend Environment Variables

In Railway dashboard, go to **Variables** tab and add:

| Variable | Value |
|----------|-------|
| `ENVIRONMENT` | `production` |
| `DEBUG` | `False` |
| `APP_NAME` | `Kenya SMB Accounting MVP` |
| `APP_VERSION` | `1.0.0` |
| `SUPABASE_URL` | `https://hmegnaodyosjpgcbgdes.supabase.co` |
| `SUPABASE_ANON_KEY` | (copy from your .env) |
| `SUPABASE_SERVICE_ROLE_KEY` | (copy from your .env) |
| `DATABASE_URL` | `postgresql+asyncpg://postgres.hmegnaodyosjpgcbgdes:BhCrT50yYWjNCUcC@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres` |
| `DATABASE_POOL_SIZE` | `20` |
| `DATABASE_MAX_OVERFLOW` | `10` |
| `JWT_SECRET_KEY` | (copy from your .env) |
| `JWT_ALGORITHM` | `HS256` |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `30` |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | `7` |
| `ENCRYPTION_KEY` | (copy from your .env) |
| `UPLOADTHING_TOKEN` | (copy from your .env) |
| `LLAMA_CLOUD_API_KEY` | (copy from your .env) |
| `CORS_ORIGINS` | `["https://accounting.pakta.app"]` |
| `CORS_ALLOW_CREDENTIALS` | `True` |
| `EMAIL_ENABLED` | `True` |
| `SMTP_HOST` | `smtp-relay.brevo.com` |
| `SMTP_PORT` | `587` |
| `SMTP_USER` | (copy from your .env) |
| `SMTP_PASSWORD` | (copy from your .env) |
| `SMTP_FROM_EMAIL` | `aenesh@pakta.app` |
| `SMTP_FROM_NAME` | `Kenya SMB Accounting` |
| `SMTP_USE_TLS` | `True` |
| `LOG_LEVEL` | `INFO` |
| `LOG_FORMAT` | `json` |

### 2.3 Configure Backend Settings

1. Go to **Settings** tab
2. Set **Root Directory**: `backend`
3. Railway will auto-detect Python and use nixpacks.toml

### 2.4 Generate Backend Domain

1. Go to **Settings** > **Networking**
2. Click **"Generate Domain"** - you'll get something like `backend-xxx.up.railway.app`
3. **Or** add custom domain: `api.accounting.pakta.app`

---

## Step 3: Deploy Frontend on Railway

### 3.1 Create Frontend Service

1. In your Railway project, click **"+ New"**
2. Select **"GitHub Repo"** again
3. Choose same repository, but set **Root Directory** to `frontend`

### 3.2 Configure Frontend Environment Variables

| Variable | Value |
|----------|-------|
| `VITE_SUPABASE_URL` | `https://hmegnaodyosjpgcbgdes.supabase.co` |
| `VITE_SUPABASE_ANON_KEY` | (copy from your .env) |
| `VITE_API_URL` | `https://api.accounting.pakta.app/api/v1` |
| `NODE_ENV` | `production` |

### 3.3 Configure Frontend Settings

1. Go to **Settings** tab
2. Set **Root Directory**: `frontend`
3. Build command should auto-detect from nixpacks.toml

### 3.4 Generate Frontend Domain

1. Go to **Settings** > **Networking**
2. Add custom domain: `accounting.pakta.app`

---

## Step 4: Configure DNS (Cloudflare/DNS Provider)

### 4.1 Add DNS Records

Add these DNS records for `pakta.app`:

| Type | Name | Value | Proxy |
|------|------|-------|-------|
| CNAME | `accounting` | `your-frontend.up.railway.app` | Proxied |
| CNAME | `api.accounting` | `your-backend.up.railway.app` | Proxied |

**Note:** Replace `your-frontend.up.railway.app` and `your-backend.up.railway.app` with actual Railway domains.

### 4.2 SSL Configuration

Railway automatically provisions SSL certificates for custom domains.

---

## Step 5: Verify Deployment

### 5.1 Test Backend Health

```bash
curl https://api.accounting.pakta.app/api/v1/health
```

Expected response:
```json
{"status": "healthy", "version": "1.0.0"}
```

### 5.2 Test Frontend

Open https://accounting.pakta.app in your browser.

### 5.3 Test Login

Use test credentials:
- Email: `business@example.com`
- Password: `BusinessPass123`

---

## Step 6: Update CORS (If Needed)

If you encounter CORS errors, update the backend's `CORS_ORIGINS` variable:

```
["https://accounting.pakta.app", "https://www.accounting.pakta.app"]
```

---

## Troubleshooting

### Backend Not Starting

1. Check **Deployments** tab for build logs
2. Verify all environment variables are set
3. Check WeasyPrint dependencies in nixpacks.toml

### Database Connection Errors

1. Verify `DATABASE_URL` is correct
2. Check Supabase dashboard for connection limits
3. Ensure IP is whitelisted (Railway IPs may need whitelisting)

### CORS Errors

1. Update `CORS_ORIGINS` to include your frontend domain
2. Redeploy backend after changing variables

### PDF Generation Fails

WeasyPrint requires system libraries. The `nixpacks.toml` includes:
- pango, cairo, gdk-pixbuf, fontconfig, freetype, harfbuzz

If PDFs fail, check Railway build logs for missing dependencies.

---

## Cost Estimate

| Service | Railway Plan | Cost |
|---------|--------------|------|
| Backend | Starter | ~$5/month |
| Frontend | Starter | ~$5/month |
| Database | Supabase Free | $0 |
| **Total** | | **~$10/month** |

Railway offers $5 free credits monthly, so initial costs may be lower.

---

## Post-Deployment Checklist

- [ ] Backend health endpoint responds
- [ ] Frontend loads correctly
- [ ] Login works with test credentials
- [ ] Invoice PDF generation works
- [ ] Email sending works
- [ ] All API endpoints accessible
- [ ] HTTPS working on both domains
- [ ] CORS configured correctly

---

## Security Reminders

1. **Never commit .env files** - Use Railway Variables dashboard
2. **Rotate secrets periodically** - JWT_SECRET_KEY, ENCRYPTION_KEY
3. **Monitor logs** - Railway provides logging dashboard
4. **Enable 2FA** - On GitHub, Railway, and Supabase

---

*Last Updated: December 22, 2025*
