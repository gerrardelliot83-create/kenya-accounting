# Security Tests - Quick Start

## Files in this Directory

### Test Suite
- **test_security.py** - 27 comprehensive security tests (33 KB)

### Documentation
- **SECURITY_TEST_DOCUMENTATION.md** - Detailed test descriptions (16 KB)
- **SECURITY_TEST_QUICK_GUIDE.md** - Quick reference guide (5.8 KB)
- **README_SECURITY_TESTS.md** - This file

### Parent Directory Files
- **../SPRINT6_SECURITY_TEST_SUMMARY.md** - Implementation summary (14 KB)
- **../run_security_tests.sh** - Test runner script (4.4 KB, executable)

---

## Quick Start (3 Steps)

### 1. Start Server (Terminal 1)
```bash
cd /mnt/c/Users/Dell/Desktop/Kenya-Accounting/backend
source venv/bin/activate
uvicorn app.main:app --reload
```

### 2. Run Tests (Terminal 2)
```bash
cd /mnt/c/Users/Dell/Desktop/Kenya-Accounting/backend
source venv/bin/activate
python -m pytest tests/test_security.py -v
```

### 3. Check Results
- All 27 tests should pass ✓
- Duration: ~30-90 seconds

---

## Alternative: Use Test Runner Script

```bash
cd /mnt/c/Users/Dell/Desktop/Kenya-Accounting/backend
./run_security_tests.sh --all
```

**Options:**
- `--all` - Run all tests (default)
- `--access` - Run access control tests only
- `--injection` - Run injection tests only
- `--auth` - Run authentication tests only
- `--quick` - Validate test structure only
- `--coverage` - Generate coverage report
- `--verbose` - Detailed output

---

## What's Tested? (27 Tests)

### OWASP Top 10 Coverage
- ✓ A01: Broken Access Control (7 tests)
- ✓ A02: Cryptographic Failures (4 tests)
- ✓ A03: Injection (4 tests)
- ✓ A04: Insecure Design (2 tests)
- ✓ A05: Security Misconfiguration (3 tests)
- ✓ A07: Authentication Failures (4 tests)
- ✓ A09: Security Logging (2 tests)
- ✓ XSS Prevention (1 test)

### Critical Security Tests
- SQL Injection Prevention
- Authentication Bypass Prevention
- Access Control Enforcement
- Password Security
- Rate Limiting
- Brute Force Protection

---

## Test Requirements

### Server
- Backend running on `http://localhost:8000`

### Test Users
| Email | Password | Role |
|-------|----------|------|
| business@example.com | BusinessPass123 | Business |
| support@example.com | SupportPass123 | Support |
| admin@example.com | AdminPass123 | Admin |

Create users with:
```bash
python create_test_user.py
```

---

## Common Commands

```bash
# Run all security tests
pytest tests/test_security.py -v

# Run specific category
pytest tests/test_security.py::TestBrokenAccessControl -v
pytest tests/test_security.py::TestInjection -v

# Run with coverage
pytest tests/test_security.py --cov=app --cov-report=html

# Just validate (don't run)
pytest tests/test_security.py --collect-only
```

---

## Troubleshooting

### Problem: Connection Timeout
```
httpx.ReadTimeout
```
**Fix:** Start the server
```bash
uvicorn app.main:app --reload
```

### Problem: Tests Skipped
```
SKIPPED [1] Authentication not available
```
**Fix:** Create test users
```bash
python create_test_user.py
```

### Problem: Rate Limit Tests Fail
**Fix:** Ensure SlowAPI middleware is enabled in `app/main.py`

---

## Documentation

- **Quick Start:** This file
- **Detailed Docs:** `SECURITY_TEST_DOCUMENTATION.md`
- **Quick Reference:** `SECURITY_TEST_QUICK_GUIDE.md`
- **Implementation:** `../SPRINT6_SECURITY_TEST_SUMMARY.md`

---

## Test Results Meaning

| Result | Meaning | Action |
|--------|---------|--------|
| 27/27 PASS | ✓ Excellent security | Monitor and maintain |
| 24-26 PASS | ⚠ Good, review failures | Fix non-critical issues |
| <24 PASS | ❌ Security concerns | Fix immediately |

---

## Next Steps

1. ✓ Run tests: `pytest tests/test_security.py -v`
2. ✓ Review results
3. ✓ Fix any failures
4. ✓ Add to CI/CD pipeline
5. ✓ Run before each deployment

---

**For detailed information, see:** `SECURITY_TEST_DOCUMENTATION.md`
