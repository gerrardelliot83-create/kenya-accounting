# Sprint 4 Quick Test Guide

## Quick Start (3 Steps)

### Step 1: Run Database Migration

```bash
cd /mnt/c/Users/Dell/Desktop/Kenya-Accounting/backend

# Copy the database URL from .env
source .env

# Run migration using psql
psql $DATABASE_URL -f migrations/sprint4_create_tables.sql
```

### Step 2: Start Backend Server

```bash
# In a new terminal
cd /mnt/c/Users/Dell/Desktop/Kenya-Accounting/backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

### Step 3: Run Tests

```bash
# In another terminal
cd /mnt/c/Users/Dell/Desktop/Kenya-Accounting/backend
source venv/bin/activate
python -m pytest tests/test_sprint4_api.py -v
```

## Expected Results

### Successful Test Run

```
============================= test session starts ==============================
collected 26 items

tests/test_sprint4_api.py::TestAuthentication::test_001_bank_import_requires_auth PASSED [  3%]
tests/test_sprint4_api.py::TestAuthentication::test_002_bank_import_requires_business_id PASSED [  7%]
tests/test_sprint4_api.py::TestBankImportCRUD::test_003_create_bank_import_csv PASSED [ 11%]
tests/test_sprint4_api.py::TestBankImportCRUD::test_004_create_bank_import_pdf SKIPPED [ 15%]
tests/test_sprint4_api.py::TestBankImportCRUD::test_005_create_bank_import_invalid_file_type PASSED [ 19%]
...
==================== 20 passed, 6 skipped in 45.23s ==========================
```

### What Gets Tested

✅ **Authentication** - All endpoints require valid auth token
✅ **CSV Upload** - Bank statements can be uploaded
✅ **Column Mapping** - CSV columns mapped to transaction fields
✅ **Import Processing** - Transactions created from statements
✅ **Reconciliation** - Transactions matched to expenses/invoices
✅ **Statistics** - Progress tracking and metrics
✅ **Error Handling** - Invalid data rejected properly

## Common Commands

### Run All Tests
```bash
pytest tests/test_sprint4_api.py -v
```

### Run Specific Category
```bash
# Authentication only
pytest tests/test_sprint4_api.py::TestAuthentication -v

# Import CRUD only
pytest tests/test_sprint4_api.py::TestBankImportCRUD -v

# Reconciliation only
pytest tests/test_sprint4_api.py::TestReconciliation -v
```

### Run Single Test
```bash
pytest tests/test_sprint4_api.py::TestBankImportCRUD::test_003_create_bank_import_csv -v
```

### Run with Detailed Output
```bash
pytest tests/test_sprint4_api.py -v -s
```

### Run with Coverage
```bash
pytest tests/test_sprint4_api.py --cov=app.api.v1.endpoints.bank_imports --cov=app.services.bank_import_service --cov-report=term
```

## Troubleshooting

### Error: "relation 'bank_imports' does not exist"
**Fix:** Run the Sprint 4 migration (Step 1 above)

### Error: Connection refused
**Fix:** Start the backend server (Step 2 above)

### Error: Login failed
**Fix:** Create test user:
```bash
python create_test_user.py
```

### Error: Tests fail with 500 errors
**Fix:** Check backend logs:
```bash
# In backend terminal, check output
# Or check database connectivity
psql $DATABASE_URL -c "SELECT * FROM bank_imports LIMIT 1;"
```

## Test Statistics

- **Total Tests:** 26
- **Test Categories:** 6
- **Expected Pass:** 20
- **Expected Skip:** 6 (PDF tests if LlamaParse unavailable)
- **Expected Fail:** 0
- **Typical Duration:** 30-60 seconds

## What Each Test Category Does

### Authentication (2 tests)
- Ensures endpoints require authentication
- Validates business-level data isolation

### Import CRUD (12 tests)
- Upload CSV/PDF files
- List, get, update, delete imports
- Configure column mappings
- Process imports to create transactions

### Transactions (4 tests)
- List transactions from imports
- Filter by reconciliation status
- Get individual transactions
- Get AI-powered match suggestions

### Reconciliation (5 tests)
- Match transactions to expenses
- Match transactions to invoices
- Unmatch incorrect matches
- Ignore irrelevant transactions
- Prevent invalid operations

### Statistics (1 test)
- Get reconciliation progress metrics
- Calculate matched percentages
- Sum matched amounts

### Edge Cases (2 tests)
- Handle empty CSV files
- Handle malformed CSV files

## Test Data

The tests use these sample transactions:

```csv
Date,Description,Debit,Credit,Balance
01/12/2024,MPESA Payment to ABC Corp,5000.00,,95000.00
02/12/2024,Salary Deposit,,150000.00,245000.00
03/12/2024,Office Supplies,2500.00,,242500.00
04/12/2024,Rent Payment,50000.00,,192500.00
05/12/2024,Customer Payment - INV001,,25000.00,217500.00
```

## API Endpoints Tested

### Bank Imports
- ✅ POST `/api/v1/bank-imports/` - Upload file
- ✅ GET `/api/v1/bank-imports/` - List imports
- ✅ GET `/api/v1/bank-imports/{id}` - Get import
- ✅ PATCH `/api/v1/bank-imports/{id}/mapping` - Update mapping
- ✅ POST `/api/v1/bank-imports/{id}/process` - Process import
- ✅ DELETE `/api/v1/bank-imports/{id}` - Delete import
- ✅ GET `/api/v1/bank-imports/{id}/transactions` - List transactions
- ✅ GET `/api/v1/bank-imports/{id}/reconciliation-stats` - Get stats

### Bank Transactions
- ✅ GET `/api/v1/bank-transactions/{id}` - Get transaction
- ✅ GET `/api/v1/bank-transactions/{id}/suggestions` - Get suggestions
- ✅ POST `/api/v1/bank-transactions/{id}/match` - Match
- ✅ DELETE `/api/v1/bank-transactions/{id}/match` - Unmatch
- ✅ POST `/api/v1/bank-transactions/{id}/ignore` - Ignore

## Next Steps

1. **After Tests Pass:** Review test coverage report
2. **If Tests Fail:** Check troubleshooting section above
3. **For API Changes:** Update tests in `/backend/tests/test_sprint4_api.py`
4. **For Documentation:** See `/backend/tests/SPRINT4_TEST_DOCUMENTATION.md`

## Need More Help?

See the full documentation:
- **Full Test Docs:** `/backend/tests/SPRINT4_TEST_DOCUMENTATION.md`
- **Migration SQL:** `/backend/migrations/sprint4_create_tables.sql`
- **API Implementation:** `/backend/app/api/v1/endpoints/bank_imports.py`
- **Service Logic:** `/backend/app/services/bank_import_service.py`

---

**Pro Tip:** Run tests frequently during development to catch issues early!
