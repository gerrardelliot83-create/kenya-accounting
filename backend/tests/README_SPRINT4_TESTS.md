# Sprint 4 API Tests - README

## Overview

This directory contains comprehensive API tests for Sprint 4: Bank Import functionality of the Kenya SMB Accounting MVP.

## What's Included

### Test Files
1. **`test_sprint4_api.py`** (26 tests)
   - Complete API test suite for Sprint 4
   - Tests all 13 bank import endpoints
   - Covers authentication, CRUD, reconciliation, and edge cases

### Documentation Files
2. **`SPRINT4_TEST_DOCUMENTATION.md`**
   - Comprehensive test documentation
   - Detailed test descriptions
   - API endpoint reference
   - Troubleshooting guide

3. **`SPRINT4_QUICK_TEST_GUIDE.md`**
   - Quick start guide
   - Common commands
   - Expected results
   - Fast troubleshooting

4. **`SPRINT4_TEST_SUMMARY.md`**
   - Executive summary
   - Test statistics
   - Success metrics
   - Quality metrics

### Migration Helper
5. **`../run_sprint4_migration.py`**
   - Automated migration runner
   - Verifies migration success
   - Easy-to-use script

## Quick Start (30 seconds)

```bash
cd /mnt/c/Users/Dell/Desktop/Kenya-Accounting/backend

# Step 1: Run migration
source venv/bin/activate
python run_sprint4_migration.py

# Step 2: Start backend (in new terminal)
source venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Step 3: Run tests (in another terminal)
source venv/bin/activate
pytest tests/test_sprint4_api.py -v
```

## Expected Results

```
============================= test session starts ==============================
collected 26 items

tests/test_sprint4_api.py::TestAuthentication::test_001... PASSED [  3%]
tests/test_sprint4_api.py::TestAuthentication::test_002... PASSED [  7%]
tests/test_sprint4_api.py::TestBankImportCRUD::test_003... PASSED [ 11%]
tests/test_sprint4_api.py::TestBankImportCRUD::test_004... SKIPPED [ 15%]
...
==================== 20 passed, 6 skipped in 45.23s ==========================
```

## Test Coverage

| Feature | Tests | Status |
|---------|-------|--------|
| Authentication | 2 | ✅ Ready |
| Import CRUD | 12 | ✅ Ready |
| Transactions | 4 | ✅ Ready |
| Reconciliation | 5 | ✅ Ready |
| Statistics | 1 | ✅ Ready |
| Edge Cases | 2 | ✅ Ready |
| **TOTAL** | **26** | **✅ Complete** |

## API Endpoints Tested

### Bank Imports (8 endpoints)
- ✅ POST `/api/v1/bank-imports/` - Upload file
- ✅ GET `/api/v1/bank-imports/` - List imports
- ✅ GET `/api/v1/bank-imports/{id}` - Get import
- ✅ PATCH `/api/v1/bank-imports/{id}/mapping` - Update mapping
- ✅ POST `/api/v1/bank-imports/{id}/process` - Process import
- ✅ DELETE `/api/v1/bank-imports/{id}` - Delete import
- ✅ GET `/api/v1/bank-imports/{id}/transactions` - List transactions
- ✅ GET `/api/v1/bank-imports/{id}/reconciliation-stats` - Get stats

### Bank Transactions (5 endpoints)
- ✅ GET `/api/v1/bank-transactions/{id}` - Get transaction
- ✅ GET `/api/v1/bank-transactions/{id}/suggestions` - Get suggestions
- ✅ POST `/api/v1/bank-transactions/{id}/match` - Match
- ✅ DELETE `/api/v1/bank-transactions/{id}/match` - Unmatch
- ✅ POST `/api/v1/bank-transactions/{id}/ignore` - Ignore

## File Locations

```
backend/
├── tests/
│   ├── test_sprint4_api.py                  # Main test suite
│   ├── SPRINT4_TEST_DOCUMENTATION.md        # Full documentation
│   ├── SPRINT4_QUICK_TEST_GUIDE.md          # Quick reference
│   ├── SPRINT4_TEST_SUMMARY.md              # Summary report
│   └── README_SPRINT4_TESTS.md              # This file
├── migrations/
│   └── sprint4_create_tables.sql            # Database migration
└── run_sprint4_migration.py                 # Migration helper script
```

## Common Commands

### Run All Tests
```bash
pytest tests/test_sprint4_api.py -v
```

### Run Specific Category
```bash
# Authentication
pytest tests/test_sprint4_api.py::TestAuthentication -v

# Import CRUD
pytest tests/test_sprint4_api.py::TestBankImportCRUD -v

# Reconciliation
pytest tests/test_sprint4_api.py::TestReconciliation -v
```

### Run with Coverage
```bash
pytest tests/test_sprint4_api.py --cov=app --cov-report=html
```

### Run Single Test
```bash
pytest tests/test_sprint4_api.py::TestBankImportCRUD::test_003_create_bank_import_csv -v
```

## Troubleshooting

### "relation 'bank_imports' does not exist"
**Fix:** Run the migration first
```bash
python run_sprint4_migration.py
```

### Connection refused
**Fix:** Start the backend server
```bash
uvicorn app.main:app --reload --port 8000
```

### Login failed
**Fix:** Create test user
```bash
python create_test_user.py
```

## Need Help?

1. **Quick Questions:** See `SPRINT4_QUICK_TEST_GUIDE.md`
2. **Detailed Info:** See `SPRINT4_TEST_DOCUMENTATION.md`
3. **Overview:** See `SPRINT4_TEST_SUMMARY.md`
4. **Backend Issues:** Check backend logs and database connection

## Test Statistics

- **Total Tests:** 26
- **Test Files:** 1
- **Documentation Files:** 4
- **Endpoints Covered:** 13
- **Lines of Test Code:** ~1,000
- **Test Categories:** 6
- **Expected Pass Rate:** 77% (20/26, 6 skipped for PDF)
- **Expected Duration:** 30-60 seconds

## Quality Metrics

- ✅ 100% endpoint coverage (13/13)
- ✅ 100% feature coverage (all Sprint 4 features)
- ✅ Security testing included
- ✅ Error handling tested
- ✅ Edge cases covered
- ✅ Integration with Sprint 2 & 3 tested

## Next Steps

1. ✅ Run migration: `python run_sprint4_migration.py`
2. ✅ Start backend: `uvicorn app.main:app --reload`
3. ✅ Run tests: `pytest tests/test_sprint4_api.py -v`
4. ✅ Review results and fix any issues
5. ✅ Integrate into CI/CD pipeline

## Contributing

When updating tests:
1. Follow existing patterns and naming conventions
2. Add docstrings to new tests
3. Update test count in documentation
4. Run full suite before committing
5. Keep documentation in sync

## Support

For issues or questions:
1. Check documentation files first
2. Review test output and error messages
3. Check backend logs
4. Verify database migration completed
5. Ensure test user exists

---

**Last Updated:** 2025-12-07
**Sprint:** Sprint 4 - Bank Import
**Status:** ✅ Ready for Execution
**Maintainer:** Test Automation Engineer
