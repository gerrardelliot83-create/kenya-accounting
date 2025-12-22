# E2E Testing with Playwright

This directory contains end-to-end tests for the Kenya SMB Accounting MVP using Playwright.

## Overview

The E2E test suite covers critical user journeys across the application:

- **Authentication**: Login, logout, role-based access control
- **Invoice Management**: Create, view, filter, download invoices
- **Expense Management**: Create, view, filter expenses
- **Onboarding Portal**: Business application workflows (onboarding agents only)
- **Admin Portal**: System administration features (system admins only)

## Directory Structure

```
e2e/
├── fixtures/
│   └── auth.ts              # Authentication fixtures for different user roles
├── pages/
│   ├── login.page.ts        # Login page object model
│   ├── dashboard.page.ts    # Dashboard page object model
│   ├── invoices.page.ts     # Invoices page object model
│   ├── contacts.page.ts     # Contacts page object model
│   ├── expenses.page.ts     # Expenses page object model
│   ├── onboarding.page.ts   # Onboarding portal page object model
│   └── admin.page.ts        # Admin portal page object model
├── auth.spec.ts             # Authentication tests (7 tests)
├── invoices.spec.ts         # Invoice workflow tests (8 tests)
├── expenses.spec.ts         # Expense workflow tests (7 tests)
├── onboarding.spec.ts       # Onboarding portal tests (8 tests)
└── admin.spec.ts            # Admin portal tests (12 tests)
```

## Prerequisites

1. **Backend Running**: Ensure FastAPI backend is running at `http://localhost:8000`
2. **Frontend Running**: Vite dev server at `http://localhost:5173` (auto-started by Playwright)
3. **Test Data**: Seed database with test users:
   - `business@example.com` / `BusinessPass123` (Business User)
   - `admin@example.com` / `AdminPass123` (System Admin)
   - `onboarding@example.com` / `OnboardPass123` (Onboarding Agent)
   - `support@example.com` / `SupportPass123` (Support Agent)

## Running Tests

### Run all tests
```bash
npm run test:e2e
```

### Run with UI mode (interactive)
```bash
npm run test:e2e:ui
```

### Run in headed mode (see browser)
```bash
npm run test:e2e:headed
```

### Run in debug mode
```bash
npm run test:e2e:debug
```

### Run specific test file
```bash
npx playwright test e2e/auth.spec.ts
```

### Run tests with specific tag/grep
```bash
npx playwright test --grep "should login"
```

### View HTML report
```bash
npm run test:e2e:report
```

## Test Coverage

### Authentication (7 tests)
- Login with valid credentials
- Login with invalid credentials
- Email validation
- Redirect to login when not authenticated
- Logout functionality
- Authentication persistence across navigation
- Role-based access control

### Invoices (8 tests)
- Display invoice list
- Navigate to create invoice
- Create draft invoice
- Filter by status
- View invoice details
- Download invoice PDF
- Search invoices
- Empty state display

### Expenses (7 tests)
- Display expenses list
- Open create expense modal
- Create new expense
- Filter by category
- Validate expense form
- Display expenses table
- View expense details

### Onboarding Portal (8 tests)
- Display onboarding dashboard (authorized users)
- Navigate to create application
- Create business application
- Display applications queue
- View application details
- Validate application form
- Deny access to unauthorized users
- Allow system admin access

### Admin Portal (12 tests)
- Display admin dashboard
- Display system statistics
- List all businesses
- View business details
- Show masked sensitive data
- View audit logs
- Filter audit logs
- Display internal users
- View system health
- Deny access to non-admin users
- Navigate between admin sections
- Search businesses

## Page Object Model Pattern

All tests use Page Object Models (POM) for better maintainability:

```typescript
// Example usage
import { InvoicesPage } from './pages/invoices.page';

test('should create invoice', async ({ authenticatedPage }) => {
  const invoicesPage = new InvoicesPage(authenticatedPage);
  await invoicesPage.goto();
  await invoicesPage.createInvoice({
    items: [
      { description: 'Consulting', quantity: 1, price: 50000 }
    ]
  });
});
```

## Authentication Fixtures

Tests use custom fixtures for different user roles:

```typescript
// Business user (authenticated)
test('my test', async ({ authenticatedPage }) => {
  // Already logged in as business user
});

// System admin
test('my test', async ({ adminPage }) => {
  // Already logged in as system admin
});

// Onboarding agent
test('my test', async ({ onboardingPage }) => {
  // Already logged in as onboarding agent
});
```

## Best Practices

1. **Use Page Objects**: Always use page object models for better maintainability
2. **Wait for Elements**: Use proper waits (`waitForSelector`, `waitForURL`) instead of arbitrary timeouts
3. **Descriptive Tests**: Write clear, descriptive test names
4. **Independent Tests**: Each test should be independent and not rely on others
5. **Clean Data**: Tests should not depend on specific database state
6. **Role-Based Testing**: Use appropriate fixtures for role-specific features

## Configuration

See `playwright.config.ts` for:
- Base URL configuration
- Retry settings
- Screenshot and video settings
- Browser configurations
- Web server auto-start

## Debugging Tests

### UI Mode (Recommended)
```bash
npm run test:e2e:ui
```
- Interactive test execution
- Time travel debugging
- Watch mode

### Debug Mode
```bash
npm run test:e2e:debug
```
- Opens Playwright Inspector
- Step through tests
- Set breakpoints

### Screenshots and Videos
- Screenshots: Captured on failure only
- Videos: Retained on failure only
- Traces: Captured on first retry

## CI/CD Integration

For CI environments:
```bash
CI=true npm run test:e2e
```

This will:
- Run tests in headless mode
- Retry failed tests 2 times
- Use single worker (no parallelization)
- Generate HTML report

## Troubleshooting

### Tests failing due to timeout
- Increase timeout in test: `test.setTimeout(60000)`
- Check backend is running
- Check frontend dev server is accessible

### Authentication issues
- Verify test users exist in database
- Check credentials in `e2e/fixtures/auth.ts`
- Ensure backend authentication endpoints are working

### Flaky tests
- Add proper waits instead of `waitForTimeout`
- Use `waitForLoadState('networkidle')` for dynamic content
- Increase retry count in `playwright.config.ts`

## Writing New Tests

1. Create/update page object in `e2e/pages/`
2. Write test in appropriate spec file
3. Use fixtures for authentication
4. Follow naming convention: `should [action] [expected result]`
5. Run test locally before committing

## Total Test Count

- Authentication: 7 tests
- Invoices: 8 tests
- Expenses: 7 tests
- Onboarding: 8 tests
- Admin: 12 tests

**Total: 42 E2E tests**
