# E2E Testing Quick Start Guide

## Prerequisites

1. **Install Dependencies**
   ```bash
   cd /mnt/c/Users/Dell/Desktop/Kenya-Accounting/frontend
   npm install
   ```

2. **Start Backend**
   ```bash
   # In a separate terminal
   cd /mnt/c/Users/Dell/Desktop/Kenya-Accounting/backend
   uvicorn app.main:app --reload
   ```
   Backend should be running at `http://localhost:8000`

3. **Ensure Test Users Exist**

   The following test accounts must exist in your database:

   - `business@example.com` / `BusinessPass123` (Business Owner)
   - `admin@example.com` / `AdminPass123` (System Admin)
   - `onboarding@example.com` / `OnboardPass123` (Onboarding Agent)
   - `support@example.com` / `SupportPass123` (Support Agent)

## Running Tests

### Option 1: UI Mode (Recommended for Development)
```bash
npm run test:e2e:ui
```
**Benefits:**
- Interactive test runner
- Time-travel debugging
- Watch mode for test development
- Visual test execution

### Option 2: Headless Mode (CI/Production)
```bash
npm run test:e2e
```
**Output:** HTML report generated in `playwright-report/`

### Option 3: Headed Mode (See Browser)
```bash
npm run test:e2e:headed
```
**Use case:** Debug visual issues or see actual browser interactions

### Option 4: Debug Mode
```bash
npm run test:e2e:debug
```
**Features:**
- Playwright Inspector opens
- Step through tests line by line
- Set breakpoints
- Inspect elements

## Run Specific Tests

### By Test File
```bash
# Authentication tests only
npx playwright test e2e/auth.spec.ts

# Invoice tests only
npx playwright test e2e/invoices.spec.ts

# Admin portal tests only
npx playwright test e2e/admin.spec.ts
```

### By Test Name
```bash
# Run tests matching "login"
npx playwright test --grep "login"

# Run tests matching "invoice"
npx playwright test --grep "invoice"
```

### Single Test
```bash
# Run one specific test
npx playwright test e2e/auth.spec.ts:13
```

## View Test Results

### HTML Report
```bash
npm run test:e2e:report
```
Opens interactive HTML report with:
- Test results
- Screenshots (on failure)
- Videos (on failure)
- Traces (on retry)

### Console Output
```bash
# Verbose output
npx playwright test --reporter=list

# Detailed output
npx playwright test --reporter=verbose
```

## Test Structure

```
frontend/
├── e2e/
│   ├── fixtures/
│   │   └── auth.ts              # Auth fixtures (authenticatedPage, adminPage, etc.)
│   ├── pages/
│   │   ├── login.page.ts        # Login page object
│   │   ├── dashboard.page.ts    # Dashboard page object
│   │   ├── invoices.page.ts     # Invoices page object
│   │   ├── expenses.page.ts     # Expenses page object
│   │   ├── onboarding.page.ts   # Onboarding portal page object
│   │   └── admin.page.ts        # Admin portal page object
│   ├── auth.spec.ts             # 7 authentication tests
│   ├── invoices.spec.ts         # 8 invoice tests
│   ├── expenses.spec.ts         # 7 expense tests
│   ├── onboarding.spec.ts       # 8 onboarding portal tests
│   └── admin.spec.ts            # 12 admin portal tests
└── playwright.config.ts         # Playwright configuration
```

## Common Commands

```bash
# Install Playwright browsers (if not already installed)
npx playwright install

# Update Playwright
npm install -D @playwright/test@latest
npx playwright install

# Generate code (record tests)
npx playwright codegen http://localhost:5173

# Show trace viewer for failed test
npx playwright show-trace trace.zip
```

## Troubleshooting

### Tests Timeout
```bash
# Increase timeout
npx playwright test --timeout=60000
```

### Backend Not Running
```bash
# Check backend status
curl http://localhost:8000/health

# Start backend if needed
cd /mnt/c/Users/Dell/Desktop/Kenya-Accounting/backend
uvicorn app.main:app --reload
```

### Frontend Not Starting
```bash
# Check if port 5173 is in use
lsof -i :5173

# Manually start frontend (usually Playwright does this)
npm run dev
```

### Authentication Failures
- Verify test users exist in database
- Check credentials in `e2e/fixtures/auth.ts`
- Ensure backend authentication endpoints work

### Flaky Tests
```bash
# Run with retries
npx playwright test --retries=3

# Run tests serially (not parallel)
npx playwright test --workers=1
```

## Test Coverage

| Feature | Tests | Status |
|---------|-------|--------|
| Authentication | 7 | ✅ |
| Invoices | 8 | ✅ |
| Expenses | 7 | ✅ |
| Onboarding Portal | 8 | ✅ |
| Admin Portal | 12 | ✅ |
| **TOTAL** | **42** | ✅ |

## Writing New Tests

1. **Create/Update Page Object**
   ```typescript
   // e2e/pages/myfeature.page.ts
   export class MyFeaturePage {
     constructor(public page: Page) {}

     async goto() {
       await this.page.goto('/my-feature');
     }
   }
   ```

2. **Write Test**
   ```typescript
   // e2e/myfeature.spec.ts
   import { test, expect } from './fixtures/auth';
   import { MyFeaturePage } from './pages/myfeature.page';

   test('should do something', async ({ authenticatedPage }) => {
     const myFeaturePage = new MyFeaturePage(authenticatedPage);
     await myFeaturePage.goto();
     // ... test logic
   });
   ```

3. **Run Test**
   ```bash
   npx playwright test e2e/myfeature.spec.ts
   ```

## CI/CD Integration

```bash
# Run in CI mode
CI=true npm run test:e2e

# Generate JUnit report for CI
npx playwright test --reporter=junit

# Generate JSON report
npx playwright test --reporter=json
```

## Documentation

- **Detailed Guide**: `e2e/README.md`
- **Implementation Summary**: `E2E_TESTING_SUMMARY.md`
- **This Quick Start**: `E2E_QUICK_START.md`
- **Playwright Docs**: https://playwright.dev

## Quick Test Commands Summary

```bash
# Development
npm run test:e2e:ui           # Interactive UI mode
npm run test:e2e:headed       # See browser
npm run test:e2e:debug        # Debug mode

# CI/Production
npm run test:e2e              # Headless mode
npm run test:e2e:report       # View HTML report

# Specific tests
npx playwright test e2e/auth.spec.ts           # Auth tests
npx playwright test e2e/invoices.spec.ts       # Invoice tests
npx playwright test e2e/admin.spec.ts          # Admin tests
npx playwright test --grep "login"             # Filter by name
```

## Support

For issues or questions:
1. Check `e2e/README.md` for detailed documentation
2. Review test output and screenshots in `playwright-report/`
3. Use debug mode: `npm run test:e2e:debug`
4. Check Playwright documentation: https://playwright.dev

---

**Ready to run?**
```bash
npm run test:e2e:ui
```
