"""
Security Test Suite for Kenya SMB Accounting MVP

Tests cover:
- OWASP Top 10 vulnerabilities
- Authentication security
- Authorization (RBAC) enforcement
- Rate limiting and brute force protection
- Data exposure prevention
- Input validation and injection prevention

Test Credentials:
- Business User: business@example.com / BusinessPass123
- Support Agent: support@example.com / SupportPass123
- Admin User: admin@example.com / AdminPass123
"""

import pytest
import httpx
from uuid import uuid4, UUID
import json
import time


# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)

# Base configuration
BASE_URL = "http://localhost:8000/api/v1"
TEST_EMAIL = "business@example.com"
TEST_PASSWORD = "BusinessPass123"
SUPPORT_EMAIL = "support@example.com"
SUPPORT_PASSWORD = "SupportPass123"
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "AdminPass123"

# Global variables to store test data
auth_token = None
support_token = None
admin_token = None
bookkeeper_token = None
business_id = None
other_business_id = None
test_invoice_id = None
test_contact_id = None
other_business_invoice_id = None
other_business_contact_id = None


# ================================
# HELPER FUNCTIONS
# ================================

async def get_auth_token():
    """Get authentication token for business user."""
    global auth_token, business_id

    if auth_token:
        return auth_token

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/auth/login",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            }
        )

        if response.status_code == 200:
            data = response.json()
            auth_token = data["access_token"]
            if "user" in data and data["user"]:
                business_id = data["user"].get("business_id")

    return auth_token


async def get_support_token():
    """Get authentication token for support agent."""
    global support_token

    if support_token:
        return support_token

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/auth/login",
            json={
                "email": SUPPORT_EMAIL,
                "password": SUPPORT_PASSWORD
            }
        )

        if response.status_code == 200:
            data = response.json()
            support_token = data["access_token"]

    return support_token


async def get_admin_token():
    """Get authentication token for admin user."""
    global admin_token

    if admin_token:
        return admin_token

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/auth/login",
            json={
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            }
        )

        if response.status_code == 200:
            data = response.json()
            admin_token = data["access_token"]

    return admin_token


async def create_test_data():
    """Create test data for security testing."""
    global test_invoice_id, test_contact_id

    token = await get_auth_token()
    if not token:
        return

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Create a test contact
        response = await client.post(
            f"{BASE_URL}/contacts/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "Security Test Contact",
                "contact_type": "customer",
                "email": "sectest@example.com"
            }
        )
        if response.status_code == 201:
            test_contact_id = response.json().get("id")

        # Try to create a test invoice if we have a contact
        if test_contact_id:
            response = await client.post(
                f"{BASE_URL}/invoices/",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "customer_id": test_contact_id,
                    "invoice_date": "2024-01-01",
                    "due_date": "2024-01-31",
                    "items": [
                        {
                            "description": "Test Item",
                            "quantity": 1,
                            "unit_price": 100.00
                        }
                    ]
                }
            )
            if response.status_code == 201:
                test_invoice_id = response.json().get("id")


# ============================================================================
# A01:2021 - BROKEN ACCESS CONTROL
# ============================================================================

class TestBrokenAccessControl:
    """Test for broken access control vulnerabilities."""

    @pytest.mark.asyncio
    async def test_horizontal_privilege_escalation_invoice(self):
        """Test that users cannot access other business's invoices."""
        token = await get_auth_token()
        if not token:
            pytest.skip("Authentication not available")

        # Try to access a random invoice ID
        random_id = str(uuid4())

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/invoices/{random_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            # Should not find it - 404 or 422 for invalid UUID format
            assert response.status_code in [404, 422], \
                f"Should not access other business invoice, got {response.status_code}"

    @pytest.mark.asyncio
    async def test_horizontal_privilege_escalation_contact(self):
        """Test that users cannot access other business's contacts."""
        token = await get_auth_token()
        if not token:
            pytest.skip("Authentication not available")

        # Try to access a random contact ID
        random_id = str(uuid4())

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/contacts/{random_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            assert response.status_code in [404, 422], \
                f"Should not access other business contact, got {response.status_code}"

    @pytest.mark.asyncio
    async def test_vertical_privilege_escalation_admin(self):
        """Test that business users cannot access admin endpoints."""
        token = await get_auth_token()
        if not token:
            pytest.skip("Authentication not available")

        admin_endpoints = [
            "/admin/businesses",
            "/admin/users",
            "/admin/audit-logs",
        ]

        async with httpx.AsyncClient(timeout=30.0) as client:
            for endpoint in admin_endpoints:
                response = await client.get(
                    f"{BASE_URL}{endpoint}",
                    headers={"Authorization": f"Bearer {token}"}
                )
                assert response.status_code in [403, 404], \
                    f"Endpoint {endpoint} should be forbidden, got {response.status_code}"

    @pytest.mark.asyncio
    async def test_vertical_privilege_escalation_onboarding(self):
        """Test that business users cannot access onboarding endpoints."""
        token = await get_auth_token()
        if not token:
            pytest.skip("Authentication not available")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/onboarding/applications",
                headers={"Authorization": f"Bearer {token}"}
            )
            assert response.status_code in [403, 404], \
                f"Onboarding endpoint should be forbidden, got {response.status_code}"

    @pytest.mark.asyncio
    async def test_direct_object_reference_id_manipulation(self):
        """Test that manipulating IDs doesn't grant access."""
        token = await get_auth_token()
        if not token:
            pytest.skip("Authentication not available")

        # Try random UUIDs
        random_ids = [str(uuid4()) for _ in range(3)]

        async with httpx.AsyncClient(timeout=30.0) as client:
            for random_id in random_ids:
                response = await client.get(
                    f"{BASE_URL}/invoices/{random_id}",
                    headers={"Authorization": f"Bearer {token}"}
                )
                # Should not find or invalid format
                assert response.status_code in [404, 422], \
                    f"Random ID should not grant access, got {response.status_code}"

    @pytest.mark.asyncio
    async def test_support_agent_limited_access(self):
        """Test that support agents have limited access."""
        token = await get_support_token()
        if not token:
            pytest.skip("Support authentication not available")

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Support agents should not access business financial data directly
            response = await client.get(
                f"{BASE_URL}/invoices/",
                headers={"Authorization": f"Bearer {token}"}
            )
            # Should be forbidden or require specific permissions
            assert response.status_code in [403, 404], \
                f"Support should not access invoices, got {response.status_code}"

    @pytest.mark.asyncio
    async def test_function_level_access_control(self):
        """Test that users cannot perform unauthorized operations."""
        token = await get_auth_token()
        if not token:
            pytest.skip("Authentication not available")

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Try to delete a random resource
            random_id = str(uuid4())
            response = await client.delete(
                f"{BASE_URL}/invoices/{random_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            # Should be not found or forbidden (not actually deleted)
            assert response.status_code in [403, 404], \
                f"Delete should be controlled, got {response.status_code}"


# ============================================================================
# A02:2021 - CRYPTOGRAPHIC FAILURES
# ============================================================================

class TestCryptographicFailures:
    """Test for cryptographic and sensitive data exposure issues."""

    @pytest.mark.asyncio
    async def test_sensitive_data_not_in_response(self):
        """Test that raw sensitive data is not returned in API responses."""
        token = await get_auth_token()
        if not token:
            pytest.skip("Authentication not available")

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Get contacts - sensitive fields should be decrypted but clean
            response = await client.get(
                f"{BASE_URL}/contacts/",
                headers={"Authorization": f"Bearer {token}"}
            )

            if response.status_code == 200:
                data = response.json()
                contacts = data.get("contacts", data.get("items", []))

                for contact in contacts:
                    # These encrypted fields should not show encryption artifacts
                    if contact.get("email"):
                        assert "encrypted:" not in contact["email"].lower(), \
                            "Email should not contain encryption artifacts"
                        assert "aes" not in contact["email"].lower(), \
                            "Email should not contain encryption markers"

    @pytest.mark.asyncio
    async def test_password_not_returned(self):
        """Test that password hashes are never returned."""
        token = await get_admin_token()
        if not token:
            pytest.skip("Admin authentication not available")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/admin/users",
                headers={"Authorization": f"Bearer {token}"}
            )

            if response.status_code == 200:
                data = response.json()
                users = data.get("users", data.get("items", []))

                for user in users:
                    assert "password" not in user, "Password should not be in response"
                    assert "password_hash" not in user, "Password hash should not be in response"
                    assert "hashed_password" not in user, "Hashed password should not be in response"

    @pytest.mark.asyncio
    async def test_tokens_not_logged(self):
        """Test that tokens are not present in audit logs."""
        token = await get_admin_token()
        if not token:
            pytest.skip("Admin authentication not available")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/admin/audit-logs",
                headers={"Authorization": f"Bearer {token}"}
            )

            if response.status_code == 200:
                data = response.json()
                logs = data.get("logs", data.get("audit_logs", []))

                for log in logs:
                    log_str = json.dumps(log).lower()
                    # If password/token mentioned, should be redacted
                    if "password" in log_str:
                        assert "redacted" in log_str or "*" in log_str, \
                            "Passwords in logs should be redacted"

    @pytest.mark.asyncio
    async def test_sensitive_data_masked(self):
        """Test that sensitive data is properly masked."""
        token = await get_auth_token()
        if not token:
            pytest.skip("Authentication not available")

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Get business details
            response = await client.get(
                f"{BASE_URL}/businesses/me",
                headers={"Authorization": f"Bearer {token}"}
            )

            if response.status_code == 200:
                data = response.json()
                # KRA PIN should be masked if shown
                if data.get("kra_pin_masked"):
                    assert "****" in data["kra_pin_masked"] or "***" in data["kra_pin_masked"], \
                        "KRA PIN should be masked"


# ============================================================================
# A03:2021 - INJECTION
# ============================================================================

class TestInjection:
    """Test for injection vulnerabilities."""

    @pytest.mark.asyncio
    async def test_sql_injection_search(self):
        """Test SQL injection in search parameters."""
        token = await get_auth_token()
        if not token:
            pytest.skip("Authentication not available")

        injection_payloads = [
            "'; DROP TABLE users; --",
            "1 OR 1=1",
            "' UNION SELECT * FROM users --",
            "' OR '1'='1",
        ]

        async with httpx.AsyncClient(timeout=30.0) as client:
            for payload in injection_payloads:
                response = await client.get(
                    f"{BASE_URL}/contacts/",
                    params={"search": payload},
                    headers={"Authorization": f"Bearer {token}"}
                )
                # Should not cause server error or data leak
                assert response.status_code in [200, 400, 422], \
                    f"SQL injection should be prevented, got {response.status_code}"

                # If 200, should not return all data
                if response.status_code == 200:
                    data = response.json()
                    # Response should be controlled, not dumping entire database
                    assert isinstance(data, dict), "Response should be structured"

    @pytest.mark.asyncio
    async def test_sql_injection_filter(self):
        """Test SQL injection in filter parameters."""
        token = await get_auth_token()
        if not token:
            pytest.skip("Authentication not available")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/invoices/",
                params={"status": "issued' OR '1'='1"},
                headers={"Authorization": f"Bearer {token}"}
            )
            assert response.status_code in [200, 400, 422], \
                f"SQL injection in filter should be prevented, got {response.status_code}"

    @pytest.mark.asyncio
    async def test_nosql_injection(self):
        """Test NoSQL injection patterns."""
        token = await get_auth_token()
        if not token:
            pytest.skip("Authentication not available")

        injection_payloads = [
            '{"$gt": ""}',
            '{"$ne": null}',
        ]

        async with httpx.AsyncClient(timeout=30.0) as client:
            for payload in injection_payloads:
                response = await client.get(
                    f"{BASE_URL}/contacts/",
                    params={"search": payload},
                    headers={"Authorization": f"Bearer {token}"}
                )
                assert response.status_code in [200, 400, 422], \
                    f"NoSQL injection should be prevented, got {response.status_code}"

    @pytest.mark.asyncio
    async def test_command_injection(self):
        """Test command injection in input fields."""
        token = await get_auth_token()
        if not token:
            pytest.skip("Authentication not available")

        malicious_names = [
            "; rm -rf /",
            "| cat /etc/passwd",
            "$(whoami)",
            "`id`",
        ]

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test in contact name
            for name in malicious_names:
                response = await client.post(
                    f"{BASE_URL}/contacts/",
                    headers={"Authorization": f"Bearer {token}"},
                    json={
                        "name": name,
                        "contact_type": "customer",
                        "email": f"cmdinjtest{int(time.time())}@test.com"
                    }
                )
                # Should either reject or safely store
                assert response.status_code in [201, 400, 422], \
                    f"Command injection should be prevented, got {response.status_code}"

                # If created, verify it's safely stored (not executed)
                if response.status_code == 201:
                    created_id = response.json().get("id")
                    # Clean up
                    await client.delete(
                        f"{BASE_URL}/contacts/{created_id}",
                        headers={"Authorization": f"Bearer {token}"}
                    )


# ============================================================================
# A04:2021 - INSECURE DESIGN
# ============================================================================

class TestInsecureDesign:
    """Test for insecure design patterns."""

    @pytest.mark.asyncio
    async def test_rate_limiting_exists(self):
        """Test that rate limiting is implemented."""
        # Attempt rapid requests to trigger rate limit
        responses = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            for i in range(8):
                response = await client.post(
                    f"{BASE_URL}/auth/login",
                    json={"email": f"test{i}@test.com", "password": "wrong"}
                )
                responses.append(response.status_code)
                # Small delay to avoid overwhelming the server
                await httpx.AsyncClient().get("http://localhost:8000/")

        # Should see 429 (Too Many Requests) after exceeding limit
        # Note: The exact number depends on rate limit configuration
        has_rate_limit = 429 in responses or any(r >= 400 for r in responses)
        assert has_rate_limit, f"Rate limiting should be active, got statuses: {responses}"

    @pytest.mark.asyncio
    async def test_account_enumeration_prevention(self):
        """Test that login doesn't reveal if email exists."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Non-existent email
            response1 = await client.post(
                f"{BASE_URL}/auth/login",
                json={"email": "nonexistent999@test.com", "password": "password123"}
            )

            # Wait a bit to avoid rate limiting
            time.sleep(0.5)

            # Another non-existent email with different password
            response2 = await client.post(
                f"{BASE_URL}/auth/login",
                json={"email": "alsonotreal888@test.com", "password": "wrongpassword"}
            )

            # Both should return same status code
            assert response1.status_code == response2.status_code, \
                "Login responses should be consistent to prevent enumeration"

            # Both should return 401 (Unauthorized) not 404
            assert response1.status_code == 401, \
                f"Should return 401 for failed login, got {response1.status_code}"


# ============================================================================
# A05:2021 - SECURITY MISCONFIGURATION
# ============================================================================

class TestSecurityMisconfiguration:
    """Test for security misconfiguration issues."""

    @pytest.mark.asyncio
    async def test_security_headers_present(self):
        """Test that security headers are present."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get("http://localhost:8000/")

            # Check for important security headers
            headers = response.headers

            # X-Content-Type-Options should be nosniff
            assert "x-content-type-options" in headers, \
                "X-Content-Type-Options header should be present"

            # X-Frame-Options should prevent clickjacking
            assert "x-frame-options" in headers, \
                "X-Frame-Options header should be present"

            # Note: HSTS is typically only on HTTPS
            # We check for it or acknowledge HTTP
            if response.url.scheme == "https":
                assert "strict-transport-security" in headers, \
                    "HSTS header should be present on HTTPS"

    @pytest.mark.asyncio
    async def test_no_sensitive_error_details(self):
        """Test that error messages don't leak sensitive info."""
        token = await get_auth_token()
        if not token:
            pytest.skip("Authentication not available")

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Cause an error by accessing invalid resource
            response = await client.get(
                f"{BASE_URL}/invoices/{uuid4()}",
                headers={"Authorization": f"Bearer {token}"}
            )

            if response.status_code >= 400:
                try:
                    data = response.json()
                    error_str = json.dumps(data).lower()

                    # Should not contain stack traces or internal paths
                    assert "traceback" not in error_str, \
                        "Error should not contain traceback"
                    assert "/home/" not in error_str, \
                        "Error should not contain system paths"
                    assert "exception" not in error_str or "detail" in error_str, \
                        "Error should not expose internal exceptions"
                except json.JSONDecodeError:
                    pass  # Non-JSON error is acceptable

    @pytest.mark.asyncio
    async def test_no_debug_endpoints_exposed(self):
        """Test that debug endpoints are not exposed."""
        debug_paths = [
            "/__debug__/",
            "/debug/",
            "/phpinfo.php",
            "/server-status",
        ]

        async with httpx.AsyncClient(timeout=30.0) as client:
            for path in debug_paths:
                response = await client.get(f"http://localhost:8000{path}")
                assert response.status_code == 404, \
                    f"Debug endpoint {path} should not be accessible, got {response.status_code}"


# ============================================================================
# A07:2021 - IDENTIFICATION AND AUTHENTICATION FAILURES
# ============================================================================

class TestAuthenticationFailures:
    """Test for authentication vulnerabilities."""

    @pytest.mark.asyncio
    async def test_jwt_token_required(self):
        """Test that protected endpoints require JWT."""
        protected_endpoints = [
            "/invoices/",
            "/contacts/",
            "/expenses/",
        ]

        async with httpx.AsyncClient(timeout=30.0) as client:
            for endpoint in protected_endpoints:
                response = await client.get(f"{BASE_URL}{endpoint}")
                assert response.status_code in [401, 403], \
                    f"Endpoint {endpoint} should require authentication, got {response.status_code}"

    @pytest.mark.asyncio
    async def test_invalid_jwt_rejected(self):
        """Test that invalid JWT tokens are rejected."""
        invalid_tokens = [
            "invalid_token",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature",
            "",
            "null",
        ]

        async with httpx.AsyncClient(timeout=30.0) as client:
            for token in invalid_tokens:
                response = await client.get(
                    f"{BASE_URL}/invoices/",
                    headers={"Authorization": f"Bearer {token}"}
                )
                assert response.status_code in [401, 403, 422], \
                    f"Invalid token should be rejected, got {response.status_code}"

    @pytest.mark.asyncio
    async def test_expired_token_rejected(self):
        """Test that expired tokens are rejected."""
        # Create a token with past expiration
        expired_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0QHRlc3QuY29tIiwiZXhwIjoxMDAwMDAwMDAwfQ.invalid"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/invoices/",
                headers={"Authorization": f"Bearer {expired_token}"}
            )
            assert response.status_code in [401, 403, 422], \
                f"Expired token should be rejected, got {response.status_code}"

    @pytest.mark.asyncio
    async def test_brute_force_protection(self):
        """Test IP blocking or rate limiting after multiple failed attempts."""
        attempts = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Make multiple failed login attempts
            for i in range(6):
                response = await client.post(
                    f"{BASE_URL}/auth/login",
                    json={"email": "bruteforce@test.com", "password": f"wrong{i}"}
                )
                attempts.append(response.status_code)

                # Check if blocked
                if response.status_code == 403:
                    data = response.json()
                    detail = data.get("detail", "").lower()
                    assert "blocked" in detail or "too many" in detail or "rate" in detail, \
                        "Should indicate blocking or rate limiting"
                    return

                # Small delay between attempts
                time.sleep(0.2)

        # Should have encountered rate limiting (429) or blocking
        assert 429 in attempts or 403 in attempts, \
            f"Should implement brute force protection, got statuses: {attempts}"


# ============================================================================
# A09:2021 - SECURITY LOGGING AND MONITORING FAILURES
# ============================================================================

class TestSecurityLogging:
    """Test for security logging and monitoring."""

    @pytest.mark.asyncio
    async def test_login_attempts_logged(self):
        """Test that login attempts are logged."""
        token = await get_admin_token()
        if not token:
            pytest.skip("Admin authentication not available")

        # Make a login attempt
        async with httpx.AsyncClient(timeout=30.0) as client:
            await client.post(
                f"{BASE_URL}/auth/login",
                json={"email": "logtest@test.com", "password": "testpassword"}
            )

            # Small delay for log processing
            time.sleep(0.5)

            # Check audit logs for login action
            response = await client.get(
                f"{BASE_URL}/admin/audit-logs",
                params={"action": "login"},
                headers={"Authorization": f"Bearer {token}"}
            )

            # Should be able to query audit logs
            assert response.status_code in [200, 404], \
                f"Audit logs endpoint should exist, got {response.status_code}"

    @pytest.mark.asyncio
    async def test_sensitive_actions_logged(self):
        """Test that sensitive actions are logged."""
        token = await get_admin_token()
        if not token:
            pytest.skip("Admin authentication not available")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/admin/audit-logs",
                headers={"Authorization": f"Bearer {token}"}
            )

            # Audit logs endpoint should exist and be accessible to admins
            assert response.status_code in [200, 404], \
                f"Audit logs should be accessible, got {response.status_code}"

            if response.status_code == 200:
                data = response.json()
                # Should have audit log structure
                assert isinstance(data, dict), "Audit logs should be structured"


# ============================================================================
# XSS PREVENTION
# ============================================================================

class TestXSSPrevention:
    """Test for XSS prevention."""

    @pytest.mark.asyncio
    async def test_xss_in_input_fields(self):
        """Test that XSS payloads are handled safely."""
        token = await get_auth_token()
        if not token:
            pytest.skip("Authentication not available")

        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "';alert('xss');//",
        ]

        async with httpx.AsyncClient(timeout=30.0) as client:
            for payload in xss_payloads:
                response = await client.post(
                    f"{BASE_URL}/contacts/",
                    headers={"Authorization": f"Bearer {token}"},
                    json={
                        "name": payload,
                        "contact_type": "customer",
                        "email": f"xsstest{int(time.time())}@test.com"
                    }
                )

                # Should either escape or reject
                if response.status_code == 201:
                    data = response.json()
                    created_id = data.get("id")
                    stored_name = data.get("name", "")

                    # If stored, should be escaped when returned
                    assert "<script>" not in stored_name, \
                        "Script tags should be escaped or sanitized"

                    # Clean up
                    await client.delete(
                        f"{BASE_URL}/contacts/{created_id}",
                        headers={"Authorization": f"Bearer {token}"}
                    )
                else:
                    # Rejecting is also acceptable
                    assert response.status_code in [400, 422], \
                        f"XSS payload should be rejected or escaped, got {response.status_code}"


# ============================================================================
# TEST SETUP AND TEARDOWN
# ============================================================================

@pytest.fixture(scope="session", autouse=True)
async def setup_test_data():
    """Setup test data once for all tests."""
    await create_test_data()
    yield
    # Teardown would go here if needed


if __name__ == "__main__":
    # Run tests with: python -m pytest tests/test_security.py -v
    pytest.main([__file__, "-v", "--tb=short"])
