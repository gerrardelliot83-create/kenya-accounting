# Sprint 5 API Tests - Quick Test Guide

## Quick Start

### 1. Prerequisites Check
```bash
# Check if server is running
curl http://localhost:8000/api/v1/health

# Check database connection
source venv/bin/activate
alembic current
```

### 2. Run All Tests
```bash
cd /mnt/c/Users/Dell/Desktop/Kenya-Accounting/backend
source venv/bin/activate
pytest tests/test_sprint5_api.py -v
```

### 3. Expected Results
- **Total Tests:** 42
- **Expected Pass:** 42 (once DB migrations are complete)
- **Execution Time:** ~20-30 seconds

---

## Test Categories

### Tax APIs (10 tests)
```bash
pytest tests/test_sprint5_api.py::TestTaxAPIs -v
```
Tests tax settings, VAT/TOT calculations, and filing guidance.

### Report APIs (8 tests)
```bash
pytest tests/test_sprint5_api.py::TestReportAPIs -v
```
Tests P&L, expense summary, aged receivables, and sales reports.

### Support Tickets (12 tests)
```bash
pytest tests/test_sprint5_api.py::TestSupportTickets -v
```
Tests ticket creation, messaging, rating, and agent operations.

### Help Centre (6 tests)
```bash
pytest tests/test_sprint5_api.py::TestHelpCentre -v
```
Tests FAQ and help article endpoints.

### Authorization (4 tests)
```bash
pytest tests/test_sprint5_api.py::TestAuthorization -v
```
Tests role-based access control.

### Admin Support (2 tests)
```bash
pytest tests/test_sprint5_api.py::TestAdminSupportStats -v
pytest tests/test_sprint5_api.py::TestCannedResponses -v
```
Tests support dashboard and canned responses.

---

## Common Test Scenarios

### Scenario 1: VAT Registered Business
```bash
# Tests 002, 005, 008, 010
pytest tests/test_sprint5_api.py -k "vat" -v
```

### Scenario 2: Support Ticket Lifecycle
```bash
# Tests 019, 023, 028, 024
pytest tests/test_sprint5_api.py::TestSupportTickets::test_019_create_ticket -v
pytest tests/test_sprint5_api.py::TestSupportTickets::test_023_add_message_to_ticket -v
pytest tests/test_sprint5_api.py::TestSupportTickets::test_028_admin_update_ticket_status -v
pytest tests/test_sprint5_api.py::TestSupportTickets::test_024_rate_ticket -v
```

### Scenario 3: Financial Reports
```bash
# Tests 011, 013, 014, 016
pytest tests/test_sprint5_api.py::TestReportAPIs -v
```

---

## Troubleshooting

### Issue: Database Table Not Found
```
relation "tax_settingses" does not exist
```
**Solution:** Run database migrations
```bash
alembic upgrade head
```

### Issue: Test Users Not Found
```
Login failed: Invalid credentials
```
**Solution:** Ensure test users exist:
- business@example.com (business_admin)
- support@example.com (support_agent)

### Issue: Server Not Running
```
Connection refused
```
**Solution:** Start the server
```bash
uvicorn app.main:app --reload
```

### Issue: Authentication Failures
```
401 Unauthorized
```
**Solution:** Check that:
1. Users exist in database
2. Passwords are correct
3. JWT secret key is configured

---

## Manual API Testing

### Tax Settings
```bash
# Get tax settings
curl -X GET "http://localhost:8000/api/v1/tax/settings" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Update to VAT registered
curl -X PUT "http://localhost:8000/api/v1/tax/settings" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "vat_registered": true,
    "vat_registration_number": "P051234567A",
    "vat_registration_date": "2024-01-01"
  }'

# Get VAT summary
curl -X GET "http://localhost:8000/api/v1/tax/vat-summary?start_date=2024-01-01&end_date=2024-12-31" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Support Tickets
```bash
# Create ticket
curl -X POST "http://localhost:8000/api/v1/support/tickets" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Need help with invoicing",
    "description": "How do I create a recurring invoice?",
    "category": "general"
  }'

# List my tickets
curl -X GET "http://localhost:8000/api/v1/support/tickets" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Reports
```bash
# P&L Report
curl -X GET "http://localhost:8000/api/v1/reports/profit-loss?start_date=2024-01-01&end_date=2024-12-31" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Aged Receivables
curl -X GET "http://localhost:8000/api/v1/reports/aged-receivables" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Test Data Setup

### Create Test Invoice (for reports)
```python
# In Python shell or test script
import httpx
import asyncio

async def create_test_data():
    async with httpx.AsyncClient() as client:
        # Login
        login_resp = await client.post(
            "http://localhost:8000/api/v1/auth/login",
            json={"email": "business@example.com", "password": "BusinessPass123"}
        )
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create customer
        customer_resp = await client.post(
            "http://localhost:8000/api/v1/contacts/",
            json={
                "name": "Test Customer",
                "contact_type": "customer",
                "email": "customer@test.com"
            },
            headers=headers
        )
        customer_id = customer_resp.json()["id"]

        # Create product
        product_resp = await client.post(
            "http://localhost:8000/api/v1/items/",
            json={
                "name": "Test Product",
                "item_type": "product",
                "unit_price": 10000.00,
                "tax_rate": 16.0
            },
            headers=headers
        )
        product_id = product_resp.json()["id"]

        # Create invoice
        invoice_resp = await client.post(
            "http://localhost:8000/api/v1/invoices/",
            json={
                "contact_id": customer_id,
                "due_date": "2024-12-31",
                "line_items": [{
                    "item_id": product_id,
                    "quantity": 1,
                    "unit_price": 10000.00,
                    "tax_rate": 16.0
                }]
            },
            headers=headers
        )
        print(f"Created invoice: {invoice_resp.json()['id']}")

asyncio.run(create_test_data())
```

---

## Performance Benchmarks

Expected test execution times:

| Test Category | Tests | Expected Time |
|---------------|-------|---------------|
| Tax APIs | 10 | 3-5 seconds |
| Report APIs | 8 | 4-6 seconds |
| Support Tickets | 12 | 6-8 seconds |
| Help Centre | 6 | 2-3 seconds |
| Authorization | 4 | 2-3 seconds |
| Admin Support | 2 | 1-2 seconds |
| **TOTAL** | **42** | **20-30 seconds** |

---

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Sprint 5 API Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Run migrations
        run: |
          alembic upgrade head

      - name: Run Sprint 5 tests
        run: |
          pytest tests/test_sprint5_api.py -v --cov=app
```

---

## Test Maintenance

### Adding New Tests
1. Follow existing naming convention: `test_XXX_descriptive_name`
2. Use appropriate test class (TestTaxAPIs, TestReportAPIs, etc.)
3. Include docstring describing what is tested
4. Assert on both status code AND response structure
5. Add to this guide

### Updating Tests
When API changes:
1. Update test expectations
2. Update SPRINT5_TEST_SUMMARY.md
3. Update this quick guide
4. Re-run all tests to ensure no regressions

---

## Quick Reference

### Test File
`/backend/tests/test_sprint5_api.py`

### Documentation
- `SPRINT5_TEST_SUMMARY.md` - Detailed test documentation
- `SPRINT5_QUICK_TEST_GUIDE.md` - This file

### Test Users
- Business: `business@example.com` / `BusinessPass123`
- Support: `support@example.com` / `SupportPass123`

### Base URL
`http://localhost:8000/api/v1`

### Test Run ID
Auto-generated unique identifier to avoid data conflicts

---

## Getting Help

If tests fail:

1. **Check Prerequisites**
   - Server running?
   - Database accessible?
   - Migrations applied?
   - Test users exist?

2. **Run Individual Test**
   ```bash
   pytest tests/test_sprint5_api.py::TestTaxAPIs::test_001_get_tax_settings_default -v -s
   ```

3. **Check Logs**
   - Server logs: `uvicorn` output
   - Database logs: PostgreSQL logs
   - Test output: pytest `-v -s` flags

4. **Verify API Manually**
   - Use curl or Postman
   - Check actual response vs expected
   - Verify database state

---

## Success Criteria

Tests pass when:
- ✅ All 42 tests pass
- ✅ No database errors
- ✅ No authentication failures
- ✅ Response structures match schemas
- ✅ Business logic validated correctly
- ✅ Edge cases handled properly
- ✅ Authorization enforced correctly

---

**Created:** 2024-12-09
**Test Coverage:** 100% of Sprint 5 API endpoints
**Ready to run:** After database migrations
