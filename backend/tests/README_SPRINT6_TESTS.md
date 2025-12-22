# Sprint 6 API Test Documentation

## Overview

Comprehensive API testing suite for Sprint 6 features of the Kenya SMB Accounting MVP. This test suite validates all onboarding portal, admin portal, and PDF generation functionality with a focus on security, data isolation, and role-based access control.

## Test Architecture

### Test Structure
```
tests/
├── test_sprint6_api.py          # Main test file (38 tests)
├── SPRINT6_TEST_SUMMARY.md      # Detailed test summary
├── SPRINT6_QUICK_TEST_GUIDE.md  # Quick start guide
└── README_SPRINT6_TESTS.md      # This file
```

### Test Organization

The test suite is organized into 7 test classes:

1. **TestOnboardingApplications** (12 tests)
   - Application CRUD operations
   - Workflow state transitions
   - Approval/rejection flows
   - Dashboard statistics

2. **TestAdminBusinessDirectory** (5 tests)
   - Business listing and search
   - Business details with data masking
   - User listing per business
   - RBAC enforcement

3. **TestAdminUserManagement** (5 tests)
   - Internal user CRUD
   - Role-based filtering
   - User lifecycle management

4. **TestAdminAuditLogs** (3 tests)
   - Audit log querying
   - Filtering and search
   - Detailed log retrieval

5. **TestAdminDashboard** (2 tests)
   - Dashboard statistics
   - System health metrics

6. **TestPDFGeneration** (8 tests)
   - Document PDF generation
   - Report PDF generation
   - Security and validation

7. **TestAuthorizationAndSecurity** (3 tests)
   - RBAC enforcement
   - Authentication validation
   - Unauthorized access prevention

## Feature Coverage

### 1. Onboarding Portal API

#### Endpoints Tested
- `POST /api/v1/onboarding/applications` - Create application
- `GET /api/v1/onboarding/applications` - List applications
- `GET /api/v1/onboarding/applications/{id}` - Get application details
- `PUT /api/v1/onboarding/applications/{id}` - Update application
- `POST /api/v1/onboarding/applications/{id}/submit` - Submit for review
- `POST /api/v1/onboarding/applications/{id}/approve` - Approve application
- `POST /api/v1/onboarding/applications/{id}/reject` - Reject application
- `POST /api/v1/onboarding/applications/{id}/request-info` - Request info
- `GET /api/v1/onboarding/stats` - Dashboard stats

#### Test Scenarios

**Application Creation**
```python
async def test_001_create_application(self):
    """Test creating a new business application."""
    # Creates application with all required fields
    # Validates encrypted fields are decrypted for agents
    # Checks default status is 'draft'
```

**Application Workflow**
```
Draft → Submit → Under Review → Approve/Reject/Request Info
                                     ↓
                               (if info requested)
                                     ↓
                              Info Requested → Resubmit
```

**Approval Process**
- Validates business creation
- Validates user creation with temporary password
- Checks password complexity (≥12 characters)
- Verifies must_change_password flag

**Rejection Process**
- Requires rejection reason (≥10 characters)
- Updates application status
- Records reason in application

### 2. Admin Portal API

#### Business Directory

**Endpoints:**
- `GET /admin/businesses` - List all businesses
- `GET /admin/businesses/{id}` - Get business details
- `GET /admin/businesses/{id}/users` - List business users
- `POST /admin/businesses/{id}/deactivate` - Deactivate business

**Data Masking:**
```python
# Sensitive fields are masked in responses
kra_pin_masked: "P05****567A"
phone_masked: "+2547****5678"
email_masked: "te**@business.co.ke"
bank_account_masked: "****5678"
```

**Business Metrics:**
- user_count
- invoice_count
- total_revenue
- subscription_status

#### Internal User Management

**Endpoints:**
- `GET /admin/users` - List internal users
- `POST /admin/users` - Create internal user
- `GET /admin/users/{id}` - Get user details
- `PUT /admin/users/{id}` - Update user
- `POST /admin/users/{id}/deactivate` - Deactivate user

**User Roles:**
- onboarding_agent
- support_agent
- system_admin

**Features Tested:**
- Role-based filtering
- Pagination
- Email masking
- Phone masking
- Active status filtering
- User creation with temp password
- Update validation

#### Audit Logs

**Endpoints:**
- `GET /admin/audit-logs` - Query audit logs
- `GET /admin/audit-logs/{id}` - Get log entry

**Filtering Options:**
- user_id
- action
- resource_type
- status
- start_date / end_date
- ip_address

**Audit Log Structure:**
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "user_name": "string",
  "action": "string",
  "resource_type": "string",
  "resource_id": "uuid",
  "status": "success|failure",
  "details": {},
  "error_message": "string",
  "ip_address": "string",
  "user_agent": "string",
  "old_values": {},
  "new_values": {},
  "created_at": "datetime"
}
```

#### Analytics & Dashboard

**Endpoints:**
- `GET /admin/dashboard` - Dashboard statistics
- `GET /admin/system-health` - System health metrics

**Dashboard Metrics:**
- total_businesses
- active_businesses
- total_users
- active_users
- new_registrations (today/week/month)
- invoice_metrics
- revenue_metrics

**Health Metrics:**
- database_status
- audit_log_count
- active_sessions
- security_events

### 3. PDF Generation API

#### Document PDFs

**Invoices:**
```python
GET /api/v1/invoices/{id}/pdf
Content-Type: application/pdf
Content-Disposition: attachment; filename="invoice_INV-XXXXX.pdf"
```

**Payment Receipts:**
```python
GET /api/v1/payments/{id}/receipt/pdf
Content-Type: application/pdf
Content-Disposition: attachment; filename="receipt_RCP-XXXXX.pdf"
```

#### Report PDFs

**Profit & Loss:**
```python
GET /api/v1/reports/profit-loss/pdf?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD
```

**Expense Summary:**
```python
GET /api/v1/reports/expense-summary/pdf?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD
```

**Aged Receivables:**
```python
GET /api/v1/reports/aged-receivables/pdf
```

#### PDF Validation Tests

**Content Validation:**
- Content-Type is "application/pdf"
- Content-Disposition includes "attachment"
- PDF content length > 0
- Proper filename in header

**Security Validation:**
- Requires authentication (401 if not authenticated)
- Business data isolation (404 for other business data)
- Date range validation (400 for invalid dates)

**Test Example:**
```python
async def test_028_generate_invoice_pdf(self):
    """Test generating invoice PDF."""
    response = await client.get(
        f"{BASE_URL}/invoices/{invoice_id}/pdf",
        headers=headers
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment" in response.headers["content-disposition"]
    assert len(response.content) > 0
```

## Security Testing

### Role-Based Access Control (RBAC)

**Tested Scenarios:**

1. **Onboarding Endpoints** (onboarding_agent or system_admin only)
   ```python
   # Business users CANNOT access
   GET /onboarding/applications → 403 Forbidden
   ```

2. **Admin Endpoints** (system_admin only)
   ```python
   # Support agents CANNOT access
   GET /admin/businesses → 403 Forbidden

   # Business users CANNOT access
   GET /admin/users → 403 Forbidden
   ```

3. **PDF Endpoints** (authenticated business users)
   ```python
   # Unauthenticated CANNOT access
   GET /invoices/{id}/pdf → 401 Unauthorized

   # Other business CANNOT access
   GET /invoices/{other_business_invoice}/pdf → 404 Not Found
   ```

### Data Isolation

**Business Data:**
- Users can only access their own business data
- PDFs scoped to user's business
- Invoices, payments filtered by business_id

**Admin Data:**
- System admins can see all businesses
- Sensitive data is masked
- Full data only for authorized operations

### Encryption & Masking

**Encrypted Fields:**
- KRA PIN
- Phone numbers
- Email addresses
- National ID
- Bank account numbers

**Masking Functions:**
```python
def mask_kra_pin(pin: str) -> str:
    # "P051234567A" → "P05****567A"

def mask_phone(phone: str) -> str:
    # "+254712345678" → "+2547****5678"

def mask_email(email: str) -> str:
    # "test@business.com" → "te**@business.com"

def mask_bank_account(account: str) -> str:
    # "1234567890" → "****7890"
```

## Test Data Management

### Test User Accounts

All tests require pre-created user accounts:

```python
ONBOARDING_EMAIL = "onboarding@example.com"
ONBOARDING_PASSWORD = "OnboardPass123"

ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "AdminPass123"

BUSINESS_EMAIL = "business@example.com"
BUSINESS_PASSWORD = "BusinessPass123"

SUPPORT_EMAIL = "support@example.com"
SUPPORT_PASSWORD = "SupportPass123"
```

### Test Data Creation

**Unique Identifiers:**
```python
TEST_RUN_ID = str(int(time.time()))[-6:]  # Last 6 digits of timestamp
```

**Helper Functions:**
```python
create_test_customer()     # Creates customer contact
create_test_product()      # Creates product item
create_test_invoice()      # Creates and issues invoice
create_test_payment()      # Creates payment record
```

### Data Dependencies

Some tests depend on data from previous tests:

```
test_001_create_application
  ↓ (creates test_application_id)
test_004_get_application_details
  ↓
test_005_update_application
  ↓
test_006_submit_application
  ↓
test_009_approve_application
  ↓ (creates approved_business_id, approved_user_id)
```

## Running Tests

### Full Test Suite
```bash
python -m pytest tests/test_sprint6_api.py -v
```

### With Coverage
```bash
python -m pytest tests/test_sprint6_api.py --cov=app.api.v1.endpoints --cov-report=html
```

### Specific Test Class
```bash
python -m pytest tests/test_sprint6_api.py::TestOnboardingApplications -v
```

### Specific Test
```bash
python -m pytest tests/test_sprint6_api.py::TestOnboardingApplications::test_001_create_application -v
```

### Stop on First Failure
```bash
python -m pytest tests/test_sprint6_api.py -x
```

### Show Print Statements
```bash
python -m pytest tests/test_sprint6_api.py -v -s
```

## Test Output

### Success Output
```
tests/test_sprint6_api.py::TestOnboardingApplications::test_001_create_application PASSED [ 2%]
tests/test_sprint6_api.py::TestOnboardingApplications::test_002_list_applications_with_pagination PASSED [ 5%]
tests/test_sprint6_api.py::TestOnboardingApplications::test_003_list_applications_filter_by_status PASSED [ 7%]
...
============================== 38 passed in 120.45s ==============================
```

### Failure Output
```
FAILED tests/test_sprint6_api.py::TestOnboardingApplications::test_001_create_application
AssertionError: assert 403 == 201
E   +  where 403 = <Response [403 Forbidden]>.status_code

Short test summary info:
FAILED tests/test_sprint6_api.py::TestOnboardingApplications::test_001_create_application - AssertionError: assert 403 == 201
```

## Troubleshooting

### Common Issues

**1. ReadTimeout / Connection Refused**
```
Problem: Server not running or not responding
Solution:
  - Check server: ps aux | grep uvicorn
  - Start server: uvicorn app.main:app --reload
  - Check port: lsof -i :8000
```

**2. 401 Unauthorized**
```
Problem: Invalid credentials or token expired
Solution:
  - Verify user exists in database
  - Check password is correct
  - Verify email_encrypted format
  - Check JWT token generation
```

**3. 403 Forbidden**
```
Problem: User doesn't have required role
Solution:
  - Check user role in database
  - Verify role assignment
  - Check endpoint permissions
```

**4. 404 Not Found**
```
Problem: Resource doesn't exist or wrong business
Solution:
  - Verify resource ID is correct
  - Check business_id matches
  - Ensure test data was created successfully
```

**5. 400 Bad Request**
```
Problem: Invalid request data or date range
Solution:
  - Check request payload format
  - Verify date formats (ISO 8601)
  - Validate required fields present
```

### Debug Mode

Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Check request/response:
```python
print(f"Request: {response.request.method} {response.request.url}")
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")
```

## Best Practices

### Test Writing

1. **Clear Test Names**
   ```python
   def test_001_create_application(self):  # Good
   def test_app_create(self):              # Bad
   ```

2. **Descriptive Docstrings**
   ```python
   """Test creating a new business application."""  # Good
   """Test create."""                               # Bad
   ```

3. **Proper Assertions**
   ```python
   assert response.status_code == 201, f"Failed: {response.text}"  # Good
   assert response.status_code == 201                               # OK
   ```

4. **Test Isolation**
   - Each test should be independent
   - Use global variables for shared data only when necessary
   - Clean up after tests if needed

5. **Error Messages**
   - Include actual vs expected values
   - Add context about what was being tested
   - Include response body for API failures

### Test Maintenance

1. **Update tests when API changes**
2. **Keep test data realistic**
3. **Document test dependencies**
4. **Review failed tests immediately**
5. **Refactor duplicated test code**

## Continuous Integration

### GitHub Actions Example
```yaml
name: Sprint 6 API Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Start server
        run: |
          uvicorn app.main:app --host 0.0.0.0 --port 8000 &
          sleep 5

      - name: Run Sprint 6 tests
        run: |
          pytest tests/test_sprint6_api.py -v --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## Performance Considerations

### Test Duration

Expected durations per test class:
- Onboarding: 30-45s (database-intensive)
- Admin Business: 15-20s (multiple queries)
- Admin Users: 15-20s (CRUD operations)
- Admin Audit: 10-15s (log queries)
- Admin Dashboard: 5-10s (aggregations)
- PDF Generation: 25-35s (PDF rendering)
- Security: 10-15s (quick validation)

**Total: ~105-155 seconds for full suite**

### Optimization Tips

1. **Parallel Execution** (use pytest-xdist)
   ```bash
   pytest tests/test_sprint6_api.py -n auto
   ```

2. **Selective Running**
   ```bash
   # Only run failed tests
   pytest tests/test_sprint6_api.py --lf
   ```

3. **Skip Slow Tests** (in development)
   ```python
   @pytest.mark.slow
   def test_generate_large_pdf(self):
       pass
   ```

## Related Documentation

- [Sprint 6 Test Summary](./SPRINT6_TEST_SUMMARY.md)
- [Quick Test Guide](./SPRINT6_QUICK_TEST_GUIDE.md)
- [Sprint 5 Tests](./test_sprint5_api.py)
- [API Documentation](../app/api/v1/endpoints/)

## Support & Contact

For issues or questions:
1. Check troubleshooting section
2. Review test output carefully
3. Check server logs
4. Verify database state
5. Contact development team

---

**Version:** 1.0
**Created:** 2025-12-09
**Sprint:** Sprint 6
**Test Count:** 38
**Coverage:** Onboarding, Admin Portal, PDF Generation, Security
