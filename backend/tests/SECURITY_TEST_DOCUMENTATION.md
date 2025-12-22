# Security Test Suite Documentation

## Overview

This document describes the comprehensive security test suite for the Kenya SMB Accounting MVP backend application. The test suite covers OWASP Top 10 vulnerabilities and application-specific security concerns.

**Test File:** `tests/test_security.py`
**Total Tests:** 27 tests
**Framework:** pytest with async support (httpx)

---

## Test Coverage Summary

### OWASP Top 10 Coverage

| OWASP Category | Test Count | Status |
|---------------|------------|--------|
| A01:2021 - Broken Access Control | 7 tests | ✓ |
| A02:2021 - Cryptographic Failures | 4 tests | ✓ |
| A03:2021 - Injection | 4 tests | ✓ |
| A04:2021 - Insecure Design | 2 tests | ✓ |
| A05:2021 - Security Misconfiguration | 3 tests | ✓ |
| A07:2021 - Authentication Failures | 4 tests | ✓ |
| A09:2021 - Security Logging Failures | 2 tests | ✓ |
| XSS Prevention (Additional) | 1 test | ✓ |

---

## Detailed Test Descriptions

### A01:2021 - Broken Access Control (7 tests)

#### 1. `test_horizontal_privilege_escalation_invoice`
**Purpose:** Prevent users from accessing other businesses' invoices
**Method:** Attempts to access random invoice IDs
**Expected:** HTTP 404 or 422 (Not Found or Invalid UUID)
**Security Impact:** HIGH - Prevents data breach between tenants

#### 2. `test_horizontal_privilege_escalation_contact`
**Purpose:** Prevent users from accessing other businesses' contacts
**Method:** Attempts to access random contact IDs
**Expected:** HTTP 404 or 422
**Security Impact:** HIGH - Prevents customer data leakage

#### 3. `test_vertical_privilege_escalation_admin`
**Purpose:** Prevent business users from accessing admin endpoints
**Method:** Tests access to `/admin/businesses`, `/admin/users`, `/admin/audit-logs`
**Expected:** HTTP 403 or 404 (Forbidden)
**Security Impact:** CRITICAL - Prevents privilege escalation

#### 4. `test_vertical_privilege_escalation_onboarding`
**Purpose:** Prevent business users from accessing onboarding portal
**Method:** Tests access to `/onboarding/applications`
**Expected:** HTTP 403 or 404
**Security Impact:** HIGH - Prevents unauthorized application review

#### 5. `test_direct_object_reference_id_manipulation`
**Purpose:** Prevent access through random UUID guessing
**Method:** Attempts 3 random UUIDs for invoice access
**Expected:** HTTP 404 or 422
**Security Impact:** HIGH - Prevents IDOR vulnerabilities

#### 6. `test_support_agent_limited_access`
**Purpose:** Ensure support agents cannot access financial data directly
**Method:** Support token attempts to access `/invoices/`
**Expected:** HTTP 403 or 404
**Security Impact:** HIGH - Prevents support staff data breach

#### 7. `test_function_level_access_control`
**Purpose:** Ensure users cannot perform unauthorized operations
**Method:** Attempts to delete resources
**Expected:** HTTP 403 or 404
**Security Impact:** HIGH - Prevents unauthorized data modification

---

### A02:2021 - Cryptographic Failures (4 tests)

#### 8. `test_sensitive_data_not_in_response`
**Purpose:** Ensure encrypted data doesn't expose encryption artifacts
**Method:** Checks contact responses for "encrypted:", "aes" markers
**Expected:** Clean data without encryption markers
**Security Impact:** MEDIUM - Prevents information leakage

#### 9. `test_password_not_returned`
**Purpose:** Ensure password hashes never appear in API responses
**Method:** Checks admin user listing for password fields
**Expected:** No password/password_hash/hashed_password fields
**Security Impact:** CRITICAL - Prevents credential exposure

#### 10. `test_tokens_not_logged`
**Purpose:** Ensure tokens and passwords are redacted in audit logs
**Method:** Checks audit logs for redaction of sensitive data
**Expected:** Passwords/tokens should be redacted or masked
**Security Impact:** HIGH - Prevents credential leakage through logs

#### 11. `test_sensitive_data_masked`
**Purpose:** Ensure sensitive business data is masked appropriately
**Method:** Checks KRA PIN masking in business details
**Expected:** Should contain "****" or "***" for masked data
**Security Impact:** MEDIUM - Prevents sensitive data exposure

---

### A03:2021 - Injection (4 tests)

#### 12. `test_sql_injection_search`
**Purpose:** Prevent SQL injection through search parameters
**Method:** Tests payloads like `'; DROP TABLE users; --`, `1 OR 1=1`, `' UNION SELECT *`
**Expected:** HTTP 200/400/422, no database errors or data dump
**Security Impact:** CRITICAL - Prevents database compromise

#### 13. `test_sql_injection_filter`
**Purpose:** Prevent SQL injection through filter parameters
**Method:** Tests `status=issued' OR '1'='1`
**Expected:** HTTP 200/400/422, filtered results only
**Security Impact:** CRITICAL - Prevents data breach

#### 14. `test_nosql_injection`
**Purpose:** Prevent NoSQL injection patterns
**Method:** Tests `{"$gt": ""}`, `{"$ne": null}`
**Expected:** HTTP 200/400/422, no unauthorized data access
**Security Impact:** HIGH - Prevents NoSQL database compromise

#### 15. `test_command_injection`
**Purpose:** Prevent OS command injection
**Method:** Tests `; rm -rf /`, `| cat /etc/passwd`, `$(whoami)`, `` `id` ``
**Expected:** HTTP 201/400/422, commands not executed
**Security Impact:** CRITICAL - Prevents server compromise

---

### A04:2021 - Insecure Design (2 tests)

#### 16. `test_rate_limiting_exists`
**Purpose:** Verify rate limiting is active
**Method:** Makes 8 rapid login requests
**Expected:** HTTP 429 (Too Many Requests) appears
**Security Impact:** HIGH - Prevents brute force and DoS

#### 17. `test_account_enumeration_prevention`
**Purpose:** Prevent email enumeration through login
**Method:** Compares responses for non-existent emails
**Expected:** Same status code (401), generic error message
**Security Impact:** MEDIUM - Prevents user enumeration

---

### A05:2021 - Security Misconfiguration (3 tests)

#### 18. `test_security_headers_present`
**Purpose:** Verify security headers are configured
**Method:** Checks for X-Content-Type-Options, X-Frame-Options, HSTS (on HTTPS)
**Expected:** All headers present
**Security Impact:** MEDIUM - Defense in depth

#### 19. `test_no_sensitive_error_details`
**Purpose:** Prevent information disclosure through error messages
**Method:** Triggers errors and checks for stack traces, file paths
**Expected:** No "traceback", "/home/", internal exception details
**Security Impact:** MEDIUM - Prevents reconnaissance

#### 20. `test_no_debug_endpoints_exposed`
**Purpose:** Ensure debug endpoints are disabled
**Method:** Tests `/__debug__/`, `/debug/`, `/phpinfo.php`, `/server-status`
**Expected:** All return HTTP 404
**Security Impact:** HIGH - Prevents information leakage

---

### A07:2021 - Authentication Failures (4 tests)

#### 21. `test_jwt_token_required`
**Purpose:** Verify all protected endpoints require authentication
**Method:** Attempts to access `/invoices/`, `/contacts/`, `/expenses/` without token
**Expected:** HTTP 401 or 403
**Security Impact:** CRITICAL - Prevents unauthorized access

#### 22. `test_invalid_jwt_rejected`
**Purpose:** Ensure invalid JWTs are rejected
**Method:** Tests "invalid_token", malformed JWT, empty string, "null"
**Expected:** HTTP 401/403/422
**Security Impact:** CRITICAL - Prevents token forgery

#### 23. `test_expired_token_rejected`
**Purpose:** Ensure expired tokens don't grant access
**Method:** Uses JWT with past expiration (`exp: 1000000000`)
**Expected:** HTTP 401/403
**Security Impact:** HIGH - Prevents session persistence

#### 24. `test_brute_force_protection`
**Purpose:** Verify brute force protection is active
**Method:** Makes 6 failed login attempts
**Expected:** HTTP 429 or 403 with "blocked"/"too many"/"rate" message
**Security Impact:** HIGH - Prevents credential guessing

---

### A09:2021 - Security Logging (2 tests)

#### 25. `test_login_attempts_logged`
**Purpose:** Verify login attempts are audited
**Method:** Makes login attempt, checks audit logs
**Expected:** Audit logs endpoint accessible (HTTP 200 or 404 if not implemented)
**Security Impact:** HIGH - Enables security monitoring

#### 26. `test_sensitive_actions_logged`
**Purpose:** Verify audit logging system exists
**Method:** Accesses `/admin/audit-logs`
**Expected:** Structured audit log response
**Security Impact:** HIGH - Enables incident response

---

### XSS Prevention (1 test)

#### 27. `test_xss_in_input_fields`
**Purpose:** Prevent XSS attacks through user input
**Method:** Tests `<script>alert('xss')</script>`, `javascript:alert('xss')`, `<img src=x onerror=alert('xss')>`, `';alert('xss');//`
**Expected:** HTTP 201/400/422, script tags escaped if stored
**Security Impact:** HIGH - Prevents client-side attacks

---

## Running the Tests

### Prerequisites

1. **Server Running:** Backend must be running on `http://localhost:8000`
2. **Test Users:** Following users must exist in database:
   - Business User: `business@example.com` / `BusinessPass123`
   - Support Agent: `support@example.com` / `SupportPass123`
   - Admin User: `admin@example.com` / `AdminPass123` (optional for some tests)

### Commands

```bash
# Activate virtual environment
cd /mnt/c/Users/Dell/Desktop/Kenya-Accounting/backend
source venv/bin/activate

# Run all security tests
python -m pytest tests/test_security.py -v --tb=short

# Run specific test category
python -m pytest tests/test_security.py::TestBrokenAccessControl -v
python -m pytest tests/test_security.py::TestInjection -v
python -m pytest tests/test_security.py::TestAuthenticationFailures -v

# Run with detailed output
python -m pytest tests/test_security.py -v --tb=long -s

# Run and generate coverage report
python -m pytest tests/test_security.py --cov=app --cov-report=html

# Collect tests without running
python -m pytest tests/test_security.py --collect-only
```

---

## Expected Results

### Success Criteria

All 27 tests should **PASS** when:
- Server is running and accessible
- Test users are properly configured
- Security features are correctly implemented
- Rate limiting is active
- Security headers middleware is enabled
- Input validation is working
- RBAC is properly enforced

### Common Failures and Solutions

#### Test Failure: Connection Timeout
**Symptom:** `httpx.ReadTimeout` or connection errors
**Solution:** Start the backend server:
```bash
uvicorn app.main:app --reload
```

#### Test Failure: Authentication Not Available
**Symptom:** Tests skipped with "Authentication not available"
**Solution:** Create test users using:
```bash
python create_test_user.py
```

#### Test Failure: Rate Limiting Tests
**Symptom:** `test_rate_limiting_exists` or `test_brute_force_protection` fail
**Solution:**
- Ensure SlowAPI middleware is enabled in `app/main.py`
- Check rate limiter configuration in `app/core/rate_limiter.py`
- Clear rate limit cache between test runs

#### Test Failure: Security Headers
**Symptom:** `test_security_headers_present` fails
**Solution:**
- Verify security headers middleware in `app/main.py`
- Check `app/core/security_headers.py` is properly configured

#### Test Failure: Admin Endpoints
**Symptom:** Admin tests return 404 instead of 403
**Solution:** This is acceptable - endpoint may not exist yet

---

## Security Test Metrics

### Test Distribution by Severity

| Severity | Test Count | Percentage |
|----------|------------|------------|
| CRITICAL | 6 tests | 22% |
| HIGH | 16 tests | 59% |
| MEDIUM | 5 tests | 19% |

### Test Distribution by OWASP Category

```
Broken Access Control     ████████████████ 26% (7 tests)
Cryptographic Failures    ████████ 15% (4 tests)
Injection                 ████████ 15% (4 tests)
Authentication            ████████ 15% (4 tests)
Security Misconfiguration ██████ 11% (3 tests)
Insecure Design          ████ 7% (2 tests)
Security Logging         ████ 7% (2 tests)
XSS Prevention           ██ 4% (1 test)
```

---

## Test Execution Time

**Expected Duration:** 30-90 seconds (depends on rate limiting delays)

**Breakdown:**
- Access Control Tests: ~10s
- Injection Tests: ~15s (includes cleanup)
- Authentication Tests: ~20s (includes rate limiting waits)
- Other Tests: ~15s

---

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Security Tests

on: [push, pull_request]

jobs:
  security-tests:
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

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Run migrations
        run: |
          alembic upgrade head

      - name: Create test users
        run: |
          python create_test_user.py

      - name: Start server in background
        run: |
          uvicorn app.main:app --host 0.0.0.0 --port 8000 &
          sleep 10

      - name: Run security tests
        run: |
          pytest tests/test_security.py -v --tb=short --junit-xml=security-results.xml

      - name: Upload test results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: security-test-results
          path: security-results.xml
```

---

## Maintenance Notes

### When to Update Tests

1. **New Endpoints Added:** Add access control tests
2. **New User Roles Added:** Update RBAC tests
3. **New Sensitive Data Fields:** Add encryption/masking tests
4. **Security Features Changed:** Update corresponding tests
5. **OWASP Top 10 Updated:** Review and add new vulnerability tests

### Test Data Cleanup

Some tests create data (contacts, invoices) and clean up automatically. If tests fail mid-execution, you may need to manually clean test data:

```sql
DELETE FROM contacts WHERE email LIKE '%test@test.com' OR email LIKE '%xsstest%' OR email LIKE '%cmdinjtest%';
```

---

## Security Testing Best Practices

1. **Run Regularly:** Execute security tests before each deployment
2. **Monitor Trends:** Track test execution time and failure patterns
3. **Update Payloads:** Regularly update injection payloads with new attack vectors
4. **Combine with SAST:** Use alongside static analysis tools (bandit, semgrep)
5. **Penetration Testing:** Complement with manual penetration testing quarterly
6. **Security Scanning:** Use OWASP ZAP or Burp Suite for dynamic testing
7. **Dependency Scanning:** Run `pip-audit` or `safety check` regularly

---

## Related Documentation

- **Security Hardening Summary:** `/SECURITY_HARDENING_SUMMARY.md`
- **Rate Limiter Implementation:** `/app/core/rate_limiter.py`
- **Security Headers Implementation:** `/app/core/security_headers.py`
- **IP Blocker Implementation:** `/app/core/ip_blocker.py`
- **RBAC Implementation:** `/app/core/security.py`

---

## Contact

For security vulnerabilities or test failures, contact:
- Security Team: security@example.com
- Development Team: dev@example.com

**Note:** Never commit real credentials or tokens to version control. Use environment variables and secure secret management.
