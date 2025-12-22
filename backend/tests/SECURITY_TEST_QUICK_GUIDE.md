# Security Test Suite - Quick Reference Guide

## Quick Start

### 1. Start the Server
```bash
cd /mnt/c/Users/Dell/Desktop/Kenya-Accounting/backend
source venv/bin/activate
uvicorn app.main:app --reload
```

### 2. Run Security Tests (in another terminal)
```bash
cd /mnt/c/Users/Dell/Desktop/Kenya-Accounting/backend
source venv/bin/activate
python -m pytest tests/test_security.py -v --tb=short
```

---

## Test Summary

**Total Tests:** 27
**Estimated Duration:** 30-90 seconds

| Category | Tests | Key Features Tested |
|----------|-------|-------------------|
| Access Control | 7 | IDOR, Horizontal/Vertical Escalation, RBAC |
| Cryptographic Failures | 4 | Data Masking, Password Exposure, Token Leakage |
| Injection | 4 | SQL, NoSQL, Command Injection |
| Insecure Design | 2 | Rate Limiting, Account Enumeration |
| Security Misconfiguration | 3 | Headers, Debug Endpoints, Error Messages |
| Authentication | 4 | JWT Validation, Token Expiry, Brute Force |
| Security Logging | 2 | Audit Logs, Login Tracking |
| XSS Prevention | 1 | Script Injection, Input Sanitization |

---

## Common Commands

```bash
# Run all security tests
pytest tests/test_security.py -v

# Run specific category
pytest tests/test_security.py::TestBrokenAccessControl -v
pytest tests/test_security.py::TestInjection -v

# Run single test
pytest tests/test_security.py::TestBrokenAccessControl::test_horizontal_privilege_escalation_invoice -v

# Run with coverage
pytest tests/test_security.py --cov=app --cov-report=html

# Show test list without running
pytest tests/test_security.py --collect-only

# Run with detailed output
pytest tests/test_security.py -v -s --tb=long
```

---

## Test User Requirements

Ensure these users exist in your database:

| Email | Password | Role | Required For |
|-------|----------|------|-------------|
| business@example.com | BusinessPass123 | Business User | Most tests |
| support@example.com | SupportPass123 | Support Agent | Limited access tests |
| admin@example.com | AdminPass123 | Admin | Admin endpoint tests |

**Create test users:**
```bash
python create_test_user.py
```

---

## Quick Troubleshooting

### Issue: Connection Timeout
```
httpx.ReadTimeout
```
**Fix:** Start the backend server
```bash
uvicorn app.main:app --reload
```

### Issue: Tests Skipped
```
SKIPPED [1] Authentication not available
```
**Fix:** Verify test users exist in database

### Issue: Rate Limit Tests Fail
**Fix:** Ensure SlowAPI middleware is enabled in `app/main.py`

### Issue: All Tests Fail
**Fix:** Check server is running on `http://localhost:8000`

---

## Expected Pass Rate

- **100% Pass:** All security features working correctly
- **90%+ Pass:** Good security posture, review failures
- **<90% Pass:** Security concerns, investigate immediately

---

## Test Categories Explained

### 🔴 CRITICAL (6 tests)
- Password exposure prevention
- SQL injection prevention
- Command injection prevention
- JWT authentication
- Privilege escalation

### 🟠 HIGH (16 tests)
- Access control violations
- Data breach prevention
- Rate limiting
- Brute force protection
- Audit logging

### 🟡 MEDIUM (5 tests)
- Data masking
- Security headers
- Account enumeration
- Error message disclosure

---

## Security Test Results Interpretation

### All Tests Pass ✓
System has strong security posture. Continue monitoring and updating tests.

### Access Control Tests Fail ✗
**Risk:** Data breach, unauthorized access
**Action:** Review RBAC implementation immediately

### Injection Tests Fail ✗
**Risk:** Database compromise, server takeover
**Action:** Critical - patch input validation immediately

### Authentication Tests Fail ✗
**Risk:** Unauthorized access, session hijacking
**Action:** Review JWT implementation and token validation

### Rate Limiting Tests Fail ✗
**Risk:** Brute force attacks, DoS
**Action:** Enable and configure SlowAPI middleware

---

## Integration Testing

### Test in Staging Before Production
```bash
# Update BASE_URL in test_security.py
BASE_URL = "https://staging.example.com/api/v1"

# Run tests
pytest tests/test_security.py -v
```

### Continuous Integration
Add to your CI/CD pipeline:
```yaml
- name: Security Tests
  run: pytest tests/test_security.py --junit-xml=security-results.xml
```

---

## Performance Notes

### Tests with Delays
- `test_rate_limiting_exists`: ~10s (rate limit testing)
- `test_brute_force_protection`: ~15s (multiple attempts with delays)
- `test_account_enumeration_prevention`: ~2s (delay between requests)

### Parallel Execution
Security tests should run **sequentially** (not in parallel) because:
- Rate limiting affects multiple tests
- Tests may create/cleanup shared data
- Authentication tokens are cached globally

---

## Next Steps After Testing

1. **Review Failures:** Investigate any failed tests immediately
2. **Check Coverage:** Ensure all critical paths are tested
3. **Update Documentation:** Document any security exceptions
4. **Schedule Pen Test:** Plan manual penetration testing
5. **Monitor Logs:** Review audit logs for suspicious activity

---

## Additional Security Checks

Beyond automated tests, perform:

1. **Manual Code Review:** Review security-critical code
2. **Dependency Scanning:** `pip-audit` or `safety check`
3. **Static Analysis:** Run `bandit` for Python security issues
4. **Dynamic Scanning:** Use OWASP ZAP or Burp Suite
5. **Penetration Testing:** Quarterly professional assessment

---

## Files Created

- `tests/test_security.py` - Main test suite (27 tests)
- `tests/SECURITY_TEST_DOCUMENTATION.md` - Detailed documentation
- `tests/SECURITY_TEST_QUICK_GUIDE.md` - This quick reference

---

## Support

For questions or issues:
1. Check detailed documentation: `SECURITY_TEST_DOCUMENTATION.md`
2. Review security hardening: `/SECURITY_HARDENING_SUMMARY.md`
3. Contact security team for vulnerabilities
