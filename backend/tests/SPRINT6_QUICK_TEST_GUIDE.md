# Sprint 6 Quick Test Guide

## Quick Start

### 1. Prerequisites
```bash
# Ensure server is running
ps aux | grep uvicorn

# If not running, start it
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
```

### 2. Create Test Users (if not exists)
The tests require these user accounts. Run the database seed script or create manually:

```sql
-- Onboarding Agent
INSERT INTO users (email_encrypted, role, full_name, is_active, must_change_password)
VALUES ('onboarding@example.com', 'onboarding_agent', 'Onboarding Agent', true, false);

-- System Admin
INSERT INTO users (email_encrypted, role, full_name, is_active, must_change_password)
VALUES ('admin@example.com', 'system_admin', 'System Admin', true, false);

-- Business User (must belong to a business)
INSERT INTO users (email_encrypted, role, full_name, is_active, business_id, must_change_password)
VALUES ('business@example.com', 'business_admin', 'Business User', true, '<business_id>', false);

-- Support Agent
INSERT INTO users (email_encrypted, role, full_name, is_active, must_change_password)
VALUES ('support@example.com', 'support_agent', 'Support Agent', true, false);
```

**Note:** Update passwords using the auth system to hash them properly.

### 3. Run All Tests
```bash
cd /mnt/c/Users/Dell/Desktop/Kenya-Accounting/backend
source venv/bin/activate
python -m pytest tests/test_sprint6_api.py -v
```

## Test Breakdown

### Onboarding Portal (12 tests)
```bash
python -m pytest tests/test_sprint6_api.py::TestOnboardingApplications -v
```

**Tests:**
1. Create application
2. List applications with pagination
3. Filter applications by status
4. Get application details
5. Update application
6. Submit application
7. Request more info
8. Resubmit after info request
9. Approve application (creates business & user)
10. Reject application
11. Onboarding stats
12. RBAC enforcement

**Expected Duration:** ~30-45 seconds

### Admin Portal (15 tests)
```bash
# All admin tests
python -m pytest tests/test_sprint6_api.py::TestAdminBusinessDirectory -v
python -m pytest tests/test_sprint6_api.py::TestAdminUserManagement -v
python -m pytest tests/test_sprint6_api.py::TestAdminAuditLogs -v
python -m pytest tests/test_sprint6_api.py::TestAdminDashboard -v
```

**Test Groups:**
- Business Directory (5 tests): List, get details, search, users, RBAC
- User Management (5 tests): List, create, get, update, filter
- Audit Logs (3 tests): Query, filter, get details
- Dashboard (2 tests): Stats, system health

**Expected Duration:** ~40-60 seconds

### PDF Generation (8 tests)
```bash
python -m pytest tests/test_sprint6_api.py::TestPDFGeneration -v
```

**Tests:**
1. Invoice PDF
2. Payment receipt PDF
3. Profit & Loss PDF
4. Expense summary PDF
5. Aged receivables PDF
6. Auth requirement
7. Business isolation
8. Date validation

**Expected Duration:** ~25-35 seconds

### Security & Authorization (3 tests)
```bash
python -m pytest tests/test_sprint6_api.py::TestAuthorizationAndSecurity -v
```

**Tests:**
1. Onboarding requires agent role
2. Admin requires system_admin role
3. Unauthenticated requests rejected

**Expected Duration:** ~10-15 seconds

## Running Individual Tests

```bash
# Test onboarding application creation
python -m pytest tests/test_sprint6_api.py::TestOnboardingApplications::test_001_create_application -v

# Test admin business listing
python -m pytest tests/test_sprint6_api.py::TestAdminBusinessDirectory::test_013_list_all_businesses -v

# Test invoice PDF generation
python -m pytest tests/test_sprint6_api.py::TestPDFGeneration::test_028_generate_invoice_pdf -v
```

## Common Issues

### Issue: "ReadTimeout" on login
**Cause:** Test user doesn't exist or server not responding
**Fix:**
```bash
# Check server is running
curl http://localhost:8000/api/v1/health

# Verify user exists
psql -d kenya_accounting -c "SELECT email_encrypted, role FROM users WHERE email_encrypted LIKE '%example.com%';"
```

### Issue: "403 Forbidden"
**Cause:** User doesn't have correct role
**Fix:**
```bash
# Check user role
psql -d kenya_accounting -c "SELECT email_encrypted, role FROM users WHERE email_encrypted = 'onboarding@example.com';"

# Update role if needed
psql -d kenya_accounting -c "UPDATE users SET role = 'onboarding_agent' WHERE email_encrypted = 'onboarding@example.com';"
```

### Issue: "404 Not Found" on PDF
**Cause:** Invoice/payment doesn't exist
**Fix:**
- Ensure test data helpers run successfully
- Check invoice belongs to the test business

### Issue: Tests hang or timeout
**Cause:** Database connection issues or slow queries
**Fix:**
```bash
# Restart server
pkill -f uvicorn
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &

# Check database connections
psql -d kenya_accounting -c "SELECT count(*) FROM pg_stat_activity;"
```

## Expected Output

### Success
```
tests/test_sprint6_api.py::TestOnboardingApplications::test_001_create_application PASSED [ 2%]
tests/test_sprint6_api.py::TestOnboardingApplications::test_002_list_applications_with_pagination PASSED [ 5%]
...
tests/test_sprint6_api.py::TestAuthorizationAndSecurity::test_038_unauthenticated_requests_rejected PASSED [100%]

============================== 38 passed in 120.45s ==============================
```

### Failure Example
```
FAILED tests/test_sprint6_api.py::TestOnboardingApplications::test_001_create_application
AssertionError: Failed to get onboarding token
```

## Test Data Created

During test execution, the following data is created:

**Applications:**
- 1-2 business applications (draft, submitted, approved, rejected states)

**Businesses:**
- 1 business created from approved application

**Users:**
- 1 business admin created from approved application
- 1 internal user (support_agent)

**Invoices:**
- 1-2 test invoices for PDF generation

**Payments:**
- 1 test payment for receipt PDF

**Audit Logs:**
- Multiple audit entries from test actions

## Cleanup

Test data is prefixed with unique TEST_RUN_ID and can be cleaned up:

```sql
-- Clean up test applications
DELETE FROM business_applications WHERE business_name LIKE '%Test Business%';

-- Clean up test users created
DELETE FROM users WHERE email_encrypted LIKE '%agent______@kenyaaccounting.com%';

-- Clean up test invoices
DELETE FROM invoices WHERE contact_id IN (
    SELECT id FROM contacts WHERE name LIKE '%Sprint6 Test%'
);

-- Clean up test contacts
DELETE FROM contacts WHERE name LIKE '%Sprint6 Test%';
```

**Note:** Be careful running cleanup in production environments!

## Performance Benchmarks

| Test Suite | Expected Duration | Test Count |
|------------|------------------|------------|
| Onboarding | 30-45s | 12 |
| Admin Portal | 40-60s | 15 |
| PDF Generation | 25-35s | 8 |
| Security | 10-15s | 3 |
| **Total** | **105-155s** | **38** |

## Test Coverage

### Endpoints Tested: 30+
- `/api/v1/onboarding/*` (8 endpoints)
- `/api/v1/admin/*` (12 endpoints)
- `/api/v1/invoices/*/pdf` (1 endpoint)
- `/api/v1/payments/*/receipt/pdf` (1 endpoint)
- `/api/v1/reports/*/pdf` (3 endpoints)

### HTTP Methods:
- GET: 20 tests
- POST: 14 tests
- PUT: 4 tests

### Status Codes Validated:
- 200 OK
- 201 Created
- 400 Bad Request
- 401 Unauthorized
- 403 Forbidden
- 404 Not Found

## Next Steps

After tests pass:
1. Review test coverage report
2. Check for any skipped tests
3. Verify PDF file contents manually
4. Test with real business data
5. Run performance tests
6. Update API documentation

## Support

For issues:
1. Check server logs: `tail -f /tmp/uvicorn_sprint5.log`
2. Check database: `psql -d kenya_accounting`
3. Review test output: `pytest -v --tb=long`
4. Check this guide: SPRINT6_TEST_SUMMARY.md

---

**Quick Reference:**
- Test File: `tests/test_sprint6_api.py`
- Total Tests: 38
- Required Users: 4 (onboarding@example.com, admin@example.com, business@example.com, support@example.com)
- Server: http://localhost:8000
- Database: kenya_accounting
