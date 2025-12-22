# Sprint 4 API Tests Documentation

## Overview

This document provides comprehensive documentation for the Sprint 4: Bank Import API test suite. The test file `/backend/tests/test_sprint4_api.py` contains 26 comprehensive tests covering all Sprint 4 functionality.

## Test Coverage Summary

### Test Categories

1. **Authentication Tests (2 tests)**
   - Endpoint authentication validation
   - Business ID requirement verification

2. **Import CRUD Tests (12 tests)**
   - CSV file upload and import creation
   - PDF file upload (skipped if LlamaParse unavailable)
   - Invalid file type rejection
   - List imports with pagination
   - Filter imports by status
   - Get import by ID
   - Handle non-existent imports (404)
   - Update column mapping
   - Invalid column mapping rejection
   - Process import to create transactions
   - Delete import
   - Prevent deletion of imports with matched transactions

3. **Transaction Tests (4 tests)**
   - List transactions for an import
   - Filter transactions by reconciliation status
   - Get single transaction by ID
   - Get reconciliation suggestions for a transaction

4. **Reconciliation Tests (5 tests)**
   - Match transaction to expense
   - Match transaction to invoice
   - Unmatch transaction
   - Ignore transaction
   - Prevent ignoring matched transactions

5. **Statistics Tests (1 test)**
   - Get reconciliation statistics for an import

6. **Edge Case Tests (2 tests)**
   - Handle empty CSV files
   - Handle CSV with missing required columns

## Prerequisites

### 1. Database Migration

**IMPORTANT:** Before running Sprint 4 tests, you must run the Sprint 4 database migration to create the required tables.

```bash
cd /mnt/c/Users/Dell/Desktop/Kenya-Accounting/backend

# Connect to database and run migration
psql $DATABASE_URL -f migrations/sprint4_create_tables.sql
```

Or using Python:

```bash
cd /mnt/c/Users/Dell/Desktop/Kenya-Accounting/backend
source venv/bin/activate

python3 << 'EOF'
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from app.config import settings

async def run_migration():
    engine = create_async_engine(settings.DATABASE_URL)

    with open('migrations/sprint4_create_tables.sql', 'r') as f:
        sql = f.read()

    async with engine.begin() as conn:
        # Split by semicolons and execute each statement
        statements = sql.split(';')
        for statement in statements:
            statement = statement.strip()
            if statement and not statement.startswith('--'):
                await conn.execute(statement)

    print("Sprint 4 migration completed successfully!")
    await engine.dispose()

asyncio.run(run_migration())
EOF
```

### 2. Backend Server

The backend server must be running:

```bash
cd /mnt/c/Users/Dell/Desktop/Kenya-Accounting/backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

### 3. Test User

The test suite uses these credentials (should already exist):
- Email: `business@example.com`
- Password: `BusinessPass123`

If the user doesn't exist, create it:

```bash
cd /mnt/c/Users/Dell/Desktop/Kenya-Accounting/backend
source venv/bin/activate
python create_test_user.py
```

## Running the Tests

### Run All Sprint 4 Tests

```bash
cd /mnt/c/Users/Dell/Desktop/Kenya-Accounting/backend
source venv/bin/activate
python -m pytest tests/test_sprint4_api.py -v
```

### Run Specific Test Categories

```bash
# Authentication tests only
python -m pytest tests/test_sprint4_api.py::TestAuthentication -v

# Import CRUD tests only
python -m pytest tests/test_sprint4_api.py::TestBankImportCRUD -v

# Transaction tests only
python -m pytest tests/test_sprint4_api.py::TestBankTransactions -v

# Reconciliation tests only
python -m pytest tests/test_sprint4_api.py::TestReconciliation -v

# Statistics tests only
python -m pytest tests/test_sprint4_api.py::TestReconciliationStats -v

# Edge case tests only
python -m pytest tests/test_sprint4_api.py::TestEdgeCases -v
```

### Run Individual Tests

```bash
# Run a specific test by name
python -m pytest tests/test_sprint4_api.py::TestBankImportCRUD::test_003_create_bank_import_csv -v

# Run with detailed output
python -m pytest tests/test_sprint4_api.py::TestAuthentication::test_001_bank_import_requires_auth -v -s
```

### Run with Coverage

```bash
# Run with code coverage report
python -m pytest tests/test_sprint4_api.py --cov=app --cov-report=html --cov-report=term

# View coverage report
open htmlcov/index.html  # On macOS
xdg-open htmlcov/index.html  # On Linux
```

## Test Details

### Authentication Tests

#### test_001_bank_import_requires_auth
- **Purpose:** Verify that bank import endpoints require authentication
- **Method:** Attempt to access `/api/v1/bank-imports/` without auth token
- **Expected:** 401 or 403 status code
- **Security:** Ensures unauthenticated users cannot access bank data

#### test_002_bank_import_requires_business_id
- **Purpose:** Verify that business_id is properly extracted from token
- **Method:** Access bank imports with valid auth token
- **Expected:** 200 status code with business isolation enforced
- **Security:** Validates business-level data isolation

### Import CRUD Tests

#### test_003_create_bank_import_csv
- **Purpose:** Test CSV file upload and import creation
- **Method:** Upload a CSV file with sample bank transactions
- **Expected:** 201 status with import record containing file metadata
- **Data:** Creates sample CSV with 5 transactions

#### test_004_create_bank_import_pdf (Skipped)
- **Purpose:** Test PDF file upload
- **Method:** Upload a PDF file (mocked)
- **Expected:** 201 status
- **Note:** Skipped if LlamaParse not available in test environment

#### test_005_create_bank_import_invalid_file_type
- **Purpose:** Verify invalid file type rejection
- **Method:** Attempt to upload .txt file
- **Expected:** 400 or 422 status
- **Security:** Prevents arbitrary file uploads

#### test_006_list_bank_imports
- **Purpose:** Test pagination of bank imports
- **Method:** GET `/api/v1/bank-imports/` with pagination params
- **Expected:** Paginated response with imports array
- **Validates:** Pagination structure, total count, page info

#### test_007_list_bank_imports_filter_by_status
- **Purpose:** Test status filtering
- **Method:** GET `/api/v1/bank-imports/?status=pending`
- **Expected:** All returned imports have pending status
- **Use Case:** Filter by processing stage

#### test_008_get_bank_import_by_id
- **Purpose:** Test retrieving single import
- **Method:** GET `/api/v1/bank-imports/{id}`
- **Expected:** 200 with complete import details
- **Validates:** All required fields present

#### test_009_get_bank_import_not_found
- **Purpose:** Test 404 handling
- **Method:** GET with non-existent UUID
- **Expected:** 404 status
- **Error Handling:** Graceful handling of invalid IDs

#### test_010_update_column_mapping
- **Purpose:** Test column mapping configuration
- **Method:** PATCH `/api/v1/bank-imports/{id}/mapping`
- **Expected:** 200 with updated mapping in response
- **Business Logic:** Maps CSV columns to transaction fields

#### test_011_update_column_mapping_invalid
- **Purpose:** Test invalid mapping rejection
- **Method:** PATCH with incomplete mapping (missing required fields)
- **Expected:** 400 or 422 status
- **Validation:** Ensures required fields are mapped

#### test_012_process_import
- **Purpose:** Test import processing to create transactions
- **Method:** POST `/api/v1/bank-imports/{id}/process`
- **Expected:** 200 with status "importing" or "completed"
- **Business Logic:** Creates bank_transactions from parsed data

#### test_013_delete_bank_import
- **Purpose:** Test import deletion
- **Method:** DELETE `/api/v1/bank-imports/{id}`
- **Expected:** 204 No Content
- **Cleanup:** Soft delete or cascade delete

#### test_014_delete_bank_import_with_matched_transactions_fails
- **Purpose:** Prevent deletion of imports with matched transactions
- **Method:** Attempt delete on import with matched transactions
- **Expected:** 400 status with error message
- **Data Integrity:** Protects reconciliation data

### Transaction Tests

#### test_015_list_transactions_for_import
- **Purpose:** List all transactions from an import
- **Method:** GET `/api/v1/bank-imports/{id}/transactions`
- **Expected:** Paginated list of transactions
- **Use Case:** Review imported transactions

#### test_016_list_transactions_filter_by_status
- **Purpose:** Filter transactions by reconciliation status
- **Method:** GET with `?status=unmatched` query param
- **Expected:** Only unmatched transactions returned
- **Use Case:** Focus on unreconciled items

#### test_017_get_transaction_by_id
- **Purpose:** Retrieve single transaction
- **Method:** GET `/api/v1/bank-transactions/{id}`
- **Expected:** 200 with complete transaction details
- **Validates:** Date, amounts, status, matched records

#### test_018_get_reconciliation_suggestions
- **Purpose:** Get AI-powered match suggestions
- **Method:** GET `/api/v1/bank-transactions/{id}/suggestions`
- **Expected:** List of suggested matches with confidence scores
- **Business Logic:** Matches by amount, date, description

### Reconciliation Tests

#### test_019_match_transaction_to_expense
- **Purpose:** Match debit transaction to expense
- **Method:** POST `/api/v1/bank-transactions/{id}/match`
- **Expected:** 200 with status "matched" and matched_expense_id set
- **Business Logic:** Links bank debit to recorded expense

#### test_020_match_transaction_to_invoice
- **Purpose:** Match credit transaction to invoice
- **Method:** POST `/api/v1/bank-transactions/{id}/match` with invoice
- **Expected:** 200 with status "matched" and matched_invoice_id set
- **Business Logic:** Links bank credit to invoice payment

#### test_021_unmatch_transaction
- **Purpose:** Remove an incorrect match
- **Method:** DELETE `/api/v1/bank-transactions/{id}/match`
- **Expected:** 200 with status reset to "unmatched"
- **Use Case:** Correct matching errors

#### test_022_ignore_transaction
- **Purpose:** Mark transaction as not requiring reconciliation
- **Method:** POST `/api/v1/bank-transactions/{id}/ignore`
- **Expected:** 200 with status "ignored"
- **Use Case:** Internal transfers, fees, etc.

#### test_023_cannot_ignore_matched_transaction
- **Purpose:** Prevent ignoring already matched transactions
- **Method:** Attempt to ignore a matched transaction
- **Expected:** 400 status with error
- **Data Integrity:** Protects existing reconciliations

### Statistics Tests

#### test_024_get_reconciliation_stats
- **Purpose:** Get reconciliation progress statistics
- **Method:** GET `/api/v1/bank-imports/{id}/reconciliation-stats`
- **Expected:** Stats including counts, percentages, amounts
- **Validates:** total_transactions, matched_count, matched_percentage
- **Use Case:** Dashboard metrics, reconciliation progress

### Edge Case Tests

#### test_025_empty_csv_file
- **Purpose:** Handle empty CSV gracefully
- **Method:** Upload CSV with headers but no data rows
- **Expected:** 201 with total_rows=0 OR 400/422 rejection
- **Error Handling:** Prevents processing empty files

#### test_026_csv_with_missing_required_columns
- **Purpose:** Reject CSV without required columns
- **Method:** Upload CSV with only Date and Details columns
- **Expected:** 400/422 when mapping non-existent columns
- **Validation:** Ensures data quality

## Test Data

### Sample CSV Format

The tests use this CSV structure:

```csv
Date,Description,Debit,Credit,Balance
01/12/2024,MPESA Payment to ABC Corp,5000.00,,95000.00
02/12/2024,Salary Deposit,,150000.00,245000.00
03/12/2024,Office Supplies,2500.00,,242500.00
04/12/2024,Rent Payment,50000.00,,192500.00
05/12/2024,Customer Payment - INV001,,25000.00,217500.00
```

### Test Credentials

- **Email:** business@example.com
- **Password:** BusinessPass123
- **Business ID:** Extracted from login response

## Expected API Endpoints

The tests validate these Sprint 4 endpoints:

### Bank Imports
- `POST /api/v1/bank-imports/` - Upload file (multipart)
- `GET /api/v1/bank-imports/` - List imports
- `GET /api/v1/bank-imports/{id}` - Get import details
- `PATCH /api/v1/bank-imports/{id}/mapping` - Update column mapping
- `POST /api/v1/bank-imports/{id}/process` - Process import
- `DELETE /api/v1/bank-imports/{id}` - Delete import
- `GET /api/v1/bank-imports/{id}/transactions` - List transactions
- `GET /api/v1/bank-imports/{id}/reconciliation-stats` - Get stats

### Bank Transactions
- `GET /api/v1/bank-transactions/{id}` - Get single transaction
- `GET /api/v1/bank-transactions/{id}/suggestions` - Get match suggestions
- `POST /api/v1/bank-transactions/{id}/match` - Match transaction
- `DELETE /api/v1/bank-transactions/{id}/match` - Unmatch transaction
- `POST /api/v1/bank-transactions/{id}/ignore` - Ignore transaction

## Common Issues and Solutions

### Issue: "relation 'bank_imports' does not exist"

**Solution:** Run the Sprint 4 migration first:
```bash
psql $DATABASE_URL -f migrations/sprint4_create_tables.sql
```

### Issue: Tests fail with 401 Unauthorized

**Solution:** Ensure the test user exists:
```bash
python create_test_user.py
```

### Issue: Tests fail with 500 errors

**Solution:** Check backend logs for detailed error messages:
```bash
# In backend terminal
tail -f logs/app.log

# Or check stdout from uvicorn
```

### Issue: Connection refused

**Solution:** Ensure backend server is running:
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

### Issue: PDF tests fail

**Solution:** PDF tests are skipped by default if LlamaParse is not configured. This is expected behavior.

## Test Results Interpretation

### Success Indicators

- **26 passed** - All tests pass (ideal)
- **20+ passed, 6 skipped** - All tests except PDF tests pass (acceptable)
- **15+ passed** - Core functionality works, some edge cases may need attention

### Failure Indicators

- **Multiple 500 errors** - Database migration not run or backend issues
- **Multiple 401/403 errors** - Authentication problems
- **Multiple 422 errors** - Schema validation issues

## Best Practices

### Before Running Tests

1. ✅ Run database migration
2. ✅ Start backend server
3. ✅ Verify test user exists
4. ✅ Check database connectivity

### During Development

1. Run specific test classes during feature development
2. Use `-v -s` flags for detailed output
3. Review error messages carefully
4. Check backend logs for server-side errors

### After Changes

1. Run full test suite
2. Check for regressions
3. Update tests if API changes
4. Document new edge cases

## CI/CD Integration

These tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
test-sprint4:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.12'
    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt
    - name: Run migrations
      run: |
        cd backend
        psql $DATABASE_URL -f migrations/sprint4_create_tables.sql
    - name: Run Sprint 4 tests
      run: |
        cd backend
        pytest tests/test_sprint4_api.py -v --junitxml=test-results.xml
    - name: Upload test results
      uses: actions/upload-artifact@v2
      with:
        name: test-results
        path: backend/test-results.xml
```

## Coverage Goals

### Current Coverage

- **Authentication:** 100% (2/2 tests)
- **Import CRUD:** 92% (11/12 tests, 1 placeholder)
- **Transactions:** 100% (4/4 tests)
- **Reconciliation:** 100% (5/5 tests)
- **Statistics:** 100% (1/1 test)
- **Edge Cases:** 100% (2/2 tests)

### Target Coverage

- **Code Coverage:** 80%+ of Sprint 4 code
- **Endpoint Coverage:** 100% of Sprint 4 endpoints
- **Error Handling:** All major error paths tested
- **Security:** All authentication and authorization paths tested

## Maintenance

### Updating Tests

When API changes:
1. Update expected response structures
2. Update validation rules
3. Add new edge case tests
4. Update this documentation

### Adding Tests

When adding new features:
1. Follow existing test patterns
2. Include authentication tests
3. Test happy path and error cases
4. Update test count in this document

## Related Documentation

- `/backend/migrations/sprint4_create_tables.sql` - Database schema
- `/backend/app/api/v1/endpoints/bank_imports.py` - API implementation
- `/backend/app/services/bank_import_service.py` - Business logic
- `/backend/app/schemas/bank_import.py` - Request/response schemas

## Contact

For questions or issues with tests:
1. Check this documentation first
2. Review test output and error messages
3. Check backend logs
4. Consult API implementation
5. Review database schema

---

**Last Updated:** 2025-12-07
**Test Suite Version:** 1.0
**Total Tests:** 26
**Sprint:** Sprint 4 - Bank Import
