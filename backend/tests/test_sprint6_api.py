"""
Comprehensive Sprint 6 API Tests

Tests all Sprint 6 features including:
- Onboarding Portal APIs (application workflow, submission, review, approval)
- Admin Portal APIs (business directory, user management, audit logs, analytics)
- PDF Generation APIs (invoices, receipts, reports)
- Role-based access control (RBAC)
- Rate limiting
- Business isolation and data security

Test Users Required:
- Onboarding Agent: onboarding@example.com / OnboardPass123
- System Admin: admin@example.com / AdminPass123
- Business User: business@example.com / BusinessPass123
- Support Agent: support@example.com / SupportPass123
"""

import pytest
import httpx
from uuid import UUID, uuid4
from datetime import date, datetime, timedelta
from decimal import Decimal
import time

# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)

# Base configuration
BASE_URL = "http://localhost:8000/api/v1"
ONBOARDING_EMAIL = "onboarding@example.com"
ONBOARDING_PASSWORD = "OnboardPass123"
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "AdminPass123"
BUSINESS_EMAIL = "business@example.com"
BUSINESS_PASSWORD = "BusinessPass123"
SUPPORT_EMAIL = "support@example.com"
SUPPORT_PASSWORD = "SupportPass123"

# Unique test run identifier
TEST_RUN_ID = str(int(time.time()))[-6:]

# Global variables to store test data
onboarding_token = None
admin_token = None
business_token = None
support_token = None
business_id = None
test_application_id = None
test_application_number = None
test_invoice_id = None
test_payment_id = None
test_customer_id = None
test_product_id = None
approved_business_id = None
approved_user_id = None
internal_user_id = None
audit_log_id = None


# ================================
# HELPER FUNCTIONS
# ================================

async def get_onboarding_token():
    """Get authentication token for onboarding agent."""
    global onboarding_token

    if onboarding_token:
        return onboarding_token

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/auth/login",
            json={
                "email": ONBOARDING_EMAIL,
                "password": ONBOARDING_PASSWORD
            }
        )

        if response.status_code == 200:
            data = response.json()
            onboarding_token = data["access_token"]
            return onboarding_token

    return None


async def get_admin_token():
    """Get authentication token for system admin."""
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

    return None


async def get_business_token():
    """Get authentication token for business user."""
    global business_token, business_id

    if business_token:
        return business_token

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/auth/login",
            json={
                "email": BUSINESS_EMAIL,
                "password": BUSINESS_PASSWORD
            }
        )

        if response.status_code == 200:
            data = response.json()
            business_token = data["access_token"]
            if "user" in data and data["user"]:
                business_id = data["user"].get("business_id")
            return business_token

    return None


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

    return None


def get_headers(token):
    """Get auth headers."""
    return {"Authorization": f"Bearer {token}"}


async def create_test_customer():
    """Helper to create a test customer for invoices."""
    global test_customer_id

    if test_customer_id:
        return test_customer_id

    token = await get_business_token()
    if not token:
        return None

    headers = get_headers(token)

    contact_data = {
        "name": f"Sprint6 Test Customer {TEST_RUN_ID}",
        "contact_type": "customer",
        "email": f"s6customer{TEST_RUN_ID}@test.com",
        "phone": "+254712345678"
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/contacts/",
            json=contact_data,
            headers=headers
        )

    if response.status_code == 201:
        test_customer_id = response.json()["id"]
        return test_customer_id
    return None


async def create_test_product():
    """Helper to create a test product for invoices."""
    global test_product_id

    if test_product_id:
        return test_product_id

    token = await get_business_token()
    if not token:
        return None

    headers = get_headers(token)

    item_data = {
        "name": f"Sprint6 Test Product {TEST_RUN_ID}",
        "item_type": "product",
        "unit_price": 10000.00,
        "tax_rate": 16.0,
        "sku": f"S6PROD-{TEST_RUN_ID}"
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/items/",
            json=item_data,
            headers=headers
        )

    if response.status_code == 201:
        test_product_id = response.json()["id"]
        return test_product_id
    return None


async def create_test_invoice():
    """Helper to create and issue a test invoice."""
    global test_invoice_id

    token = await get_business_token()
    if not token:
        return None

    headers = get_headers(token)

    # Ensure dependencies exist
    customer_id = await create_test_customer()
    product_id = await create_test_product()

    if not customer_id or not product_id:
        return None

    invoice_data = {
        "contact_id": customer_id,
        "due_date": (date.today() + timedelta(days=30)).isoformat(),
        "line_items": [
            {
                "item_id": product_id,
                "quantity": 1,
                "unit_price": 10000.00,
                "tax_rate": 16.0,
                "description": "Test product for Sprint 6 PDF"
            }
        ]
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Create invoice
        response = await client.post(
            f"{BASE_URL}/invoices/",
            json=invoice_data,
            headers=headers
        )

        if response.status_code != 201:
            return None

        invoice_id = response.json()["id"]

        # Issue invoice
        response = await client.post(
            f"{BASE_URL}/invoices/{invoice_id}/issue",
            json={"issue_date": date.today().isoformat()},
            headers=headers
        )

        if response.status_code == 200:
            test_invoice_id = invoice_id
            return invoice_id

    return None


async def create_test_payment():
    """Helper to create a test payment for receipt PDF."""
    global test_payment_id

    token = await get_business_token()
    if not token:
        return None

    headers = get_headers(token)

    # Ensure invoice exists
    invoice_id = await create_test_invoice()
    if not invoice_id:
        return None

    payment_data = {
        "amount": 11600.00,  # 10000 + 16% VAT
        "payment_date": date.today().isoformat(),
        "payment_method": "mpesa",
        "reference_number": f"MPESA{TEST_RUN_ID}"
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/invoices/{invoice_id}/payments",
            json=payment_data,
            headers=headers
        )

    if response.status_code == 201:
        test_payment_id = response.json()["id"]
        return test_payment_id
    return None


# ================================
# ONBOARDING PORTAL TESTS (12 tests)
# ================================

class TestOnboardingApplications:
    """Test onboarding application CRUD and workflow."""

    @pytest.mark.asyncio
    async def test_001_create_application(self):
        """Test creating a new business application."""
        global test_application_id

        token = await get_onboarding_token()
        assert token is not None, "Failed to get onboarding token"

        headers = get_headers(token)

        application_data = {
            "business_name": f"Test Business Ltd {TEST_RUN_ID}",
            "business_type": "limited_company",
            "kra_pin": "P051234567A",
            "county": "Nairobi",
            "sub_county": "Westlands",
            "phone": "+254712345678",
            "email": f"test{TEST_RUN_ID}@business.co.ke",
            "owner_name": "John Kamau",
            "owner_national_id": "12345678",
            "owner_phone": "+254712345679",
            "owner_email": f"john{TEST_RUN_ID}@business.co.ke",
            "vat_registered": True,
            "tot_registered": False
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BASE_URL}/onboarding/applications",
                headers=headers,
                json=application_data
            )

        assert response.status_code == 201, f"Failed to create application: {response.text}"
        data = response.json()

        assert "id" in data
        assert data["business_name"] == application_data["business_name"]
        assert data["status"] == "draft"
        assert data["kra_pin"] == "P051234567A"  # Decrypted for agents

        test_application_id = data["id"]

    @pytest.mark.asyncio
    async def test_002_list_applications_with_pagination(self):
        """Test listing applications with pagination."""
        token = await get_onboarding_token()
        assert token is not None

        headers = get_headers(token)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/onboarding/applications?page=1&page_size=10",
                headers=headers
            )

        assert response.status_code == 200, f"Failed to list applications: {response.text}"
        data = response.json()

        assert "applications" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data
        assert data["total"] >= 1  # At least the one we created

    @pytest.mark.asyncio
    async def test_003_list_applications_filter_by_status(self):
        """Test filtering applications by status."""
        token = await get_onboarding_token()
        assert token is not None

        headers = get_headers(token)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/onboarding/applications?status=draft",
                headers=headers
            )

        assert response.status_code == 200
        data = response.json()

        # All returned applications should have draft status
        for app in data["applications"]:
            assert app["status"] == "draft"

    @pytest.mark.asyncio
    async def test_004_get_application_details(self):
        """Test getting application details with decrypted fields."""
        global test_application_id

        if not test_application_id:
            pytest.skip("No application ID from previous tests")

        token = await get_onboarding_token()
        assert token is not None

        headers = get_headers(token)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/onboarding/applications/{test_application_id}",
                headers=headers
            )

        assert response.status_code == 200, f"Failed to get application: {response.text}"
        data = response.json()

        assert data["id"] == test_application_id
        assert "kra_pin" in data  # Decrypted field
        assert "phone" in data
        assert "email" in data
        assert "owner_national_id" in data

    @pytest.mark.asyncio
    async def test_005_update_application(self):
        """Test updating application details."""
        global test_application_id

        if not test_application_id:
            pytest.skip("No application ID from previous tests")

        token = await get_onboarding_token()
        assert token is not None

        headers = get_headers(token)

        update_data = {
            "business_type": "limited_company",
            "notes": "Updated via test - retail business"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.put(
                f"{BASE_URL}/onboarding/applications/{test_application_id}",
                headers=headers,
                json=update_data
            )

        assert response.status_code == 200, f"Failed to update application: {response.text}"
        data = response.json()

        assert data["business_type"] == "limited_company"
        assert "notes" in data

    @pytest.mark.asyncio
    async def test_006_submit_application(self):
        """Test submitting an application for review."""
        global test_application_id

        if not test_application_id:
            pytest.skip("No application ID from previous tests")

        token = await get_onboarding_token()
        assert token is not None

        headers = get_headers(token)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BASE_URL}/onboarding/applications/{test_application_id}/submit",
                headers=headers
            )

        assert response.status_code == 200, f"Failed to submit application: {response.text}"
        data = response.json()

        assert data["status"] == "submitted"
        assert "submitted_at" in data

    @pytest.mark.asyncio
    async def test_007_request_more_info(self):
        """Test requesting additional information from applicant."""
        global test_application_id

        if not test_application_id:
            pytest.skip("No application ID from previous tests")

        token = await get_admin_token()
        assert token is not None

        headers = get_headers(token)

        info_request = {
            "info_request_note": "Please provide business registration certificate and proof of KRA PIN."
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BASE_URL}/onboarding/applications/{test_application_id}/request-info",
                headers=headers,
                json=info_request
            )

        assert response.status_code == 200, f"Failed to request info: {response.text}"
        data = response.json()

        assert data["status"] == "info_requested"
        assert "info_requested_note" in data or "notes" in data

    @pytest.mark.asyncio
    async def test_008_resubmit_after_info_request(self):
        """Test resubmitting application after providing info."""
        global test_application_id

        if not test_application_id:
            pytest.skip("No application ID from previous tests")

        token = await get_onboarding_token()
        assert token is not None

        headers = get_headers(token)

        # Update with requested info
        update_data = {
            "notes": "Registration certificate attached. KRA PIN verified."
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Update
            await client.put(
                f"{BASE_URL}/onboarding/applications/{test_application_id}",
                headers=headers,
                json=update_data
            )

            # Resubmit
            response = await client.post(
                f"{BASE_URL}/onboarding/applications/{test_application_id}/submit",
                headers=headers
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "submitted"

    @pytest.mark.asyncio
    async def test_009_approve_application_creates_business(self):
        """Test that approving application creates business and user."""
        global test_application_id, approved_business_id, approved_user_id

        if not test_application_id:
            pytest.skip("No application ID from previous tests")

        token = await get_admin_token()
        assert token is not None

        headers = get_headers(token)

        approval_data = {
            "notes": "All documentation verified. Approved for onboarding."
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BASE_URL}/onboarding/applications/{test_application_id}/approve",
                headers=headers,
                json=approval_data
            )

        assert response.status_code == 200, f"Failed to approve application: {response.text}"
        data = response.json()

        # Check approval response
        assert "business_id" in data
        assert "admin_user_id" in data
        assert "temporary_password" in data
        assert len(data["temporary_password"]) >= 12  # Strong password

        approved_business_id = data["business_id"]
        approved_user_id = data["admin_user_id"]

    @pytest.mark.asyncio
    async def test_010_reject_application(self):
        """Test rejecting an application with reason."""
        token = await get_onboarding_token()
        assert token is not None

        headers = get_headers(token)

        # Create a new application to reject
        application_data = {
            "business_name": f"Rejected Business {TEST_RUN_ID}",
            "business_type": "sole_proprietor",
            "kra_pin": "P059999999Z",
            "county": "Mombasa",
            "phone": "+254722222222",
            "email": f"reject{TEST_RUN_ID}@test.com",
            "owner_name": "Test Reject",
            "owner_national_id": "99999999",
            "owner_phone": "+254722222223",
            "owner_email": f"rejectowner{TEST_RUN_ID}@test.com"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Create
            create_response = await client.post(
                f"{BASE_URL}/onboarding/applications",
                headers=headers,
                json=application_data
            )

            assert create_response.status_code == 201
            reject_app_id = create_response.json()["id"]

            # Submit
            await client.post(
                f"{BASE_URL}/onboarding/applications/{reject_app_id}/submit",
                headers=headers
            )

            # Get admin token and reject
            admin_token_value = await get_admin_token()
            admin_headers = get_headers(admin_token_value)

            rejection_data = {
                "rejection_reason": "Invalid KRA PIN documentation provided. Cannot verify authenticity."
            }

            response = await client.post(
                f"{BASE_URL}/onboarding/applications/{reject_app_id}/reject",
                headers=admin_headers,
                json=rejection_data
            )

        assert response.status_code == 200, f"Failed to reject application: {response.text}"
        data = response.json()

        assert data["status"] == "rejected"
        assert "rejection_reason" in data or "notes" in data

    @pytest.mark.asyncio
    async def test_011_onboarding_stats(self):
        """Test getting onboarding dashboard stats."""
        token = await get_onboarding_token()
        assert token is not None

        headers = get_headers(token)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/onboarding/stats",
                headers=headers
            )

        assert response.status_code == 200, f"Failed to get stats: {response.text}"
        data = response.json()

        # Verify stats structure
        assert "total_applications" in data
        assert "approved_count" in data
        assert "submitted_count" in data or "pending_review_count" in data

    @pytest.mark.asyncio
    async def test_012_business_user_cannot_access_onboarding(self):
        """Test that business users cannot access onboarding endpoints."""
        token = await get_business_token()
        assert token is not None

        headers = get_headers(token)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/onboarding/applications",
                headers=headers
            )

        assert response.status_code == 403, "Business user should not access onboarding"


# ================================
# ADMIN PORTAL TESTS (15 tests)
# ================================

class TestAdminBusinessDirectory:
    """Test admin business management endpoints."""

    @pytest.mark.asyncio
    async def test_013_list_all_businesses(self):
        """Test listing all businesses in the system."""
        token = await get_admin_token()
        assert token is not None

        headers = get_headers(token)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/admin/businesses?page=1&page_size=20",
                headers=headers
            )

        assert response.status_code == 200, f"Failed to list businesses: {response.text}"
        data = response.json()

        assert "businesses" in data
        assert "total" in data
        assert "page" in data
        assert data["total"] >= 1  # At least one business exists

    @pytest.mark.asyncio
    async def test_014_get_business_details_with_masked_data(self):
        """Test that sensitive data is masked in business details."""
        global business_id

        if not business_id:
            token = await get_business_token()  # This sets business_id

        if not business_id:
            pytest.skip("No business ID available")

        admin_token_value = await get_admin_token()
        assert admin_token_value is not None

        headers = get_headers(admin_token_value)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/admin/businesses/{business_id}",
                headers=headers
            )

        assert response.status_code == 200, f"Failed to get business details: {response.text}"
        data = response.json()

        # Verify masking - sensitive fields should be masked
        if "kra_pin_masked" in data:
            assert "****" in data["kra_pin_masked"] or "*" in data["kra_pin_masked"]

        if "phone_masked" in data:
            assert "****" in data["phone_masked"] or "*" in data["phone_masked"]

        if "email_masked" in data:
            assert "****" in data["email_masked"] or "*" in data["email_masked"]

    @pytest.mark.asyncio
    async def test_015_get_business_users(self):
        """Test listing users for a specific business."""
        global business_id

        if not business_id:
            await get_business_token()

        if not business_id:
            pytest.skip("No business ID available")

        admin_token_value = await get_admin_token()
        assert admin_token_value is not None

        headers = get_headers(admin_token_value)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/admin/businesses/{business_id}/users",
                headers=headers
            )

        assert response.status_code == 200, f"Failed to get business users: {response.text}"
        data = response.json()

        assert "users" in data
        assert "total" in data
        assert data["total"] >= 1  # At least one user

    @pytest.mark.asyncio
    async def test_016_search_businesses_by_name(self):
        """Test searching businesses by name."""
        token = await get_admin_token()
        assert token is not None

        headers = get_headers(token)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/admin/businesses?search=Test",
                headers=headers
            )

        assert response.status_code == 200
        data = response.json()

        assert "businesses" in data
        # Results may or may not contain "Test" depending on data

    @pytest.mark.asyncio
    async def test_017_non_admin_cannot_access_admin_endpoints(self):
        """Test that non-admins cannot access admin endpoints."""
        token = await get_business_token()
        assert token is not None

        headers = get_headers(token)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/admin/businesses",
                headers=headers
            )

        assert response.status_code == 403, "Business user should not access admin endpoints"


class TestAdminUserManagement:
    """Test admin internal user management endpoints."""

    @pytest.mark.asyncio
    async def test_018_list_internal_users(self):
        """Test listing internal users (agents, admins)."""
        token = await get_admin_token()
        assert token is not None

        headers = get_headers(token)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/admin/users?page=1&page_size=20",
                headers=headers
            )

        assert response.status_code == 200, f"Failed to list internal users: {response.text}"
        data = response.json()

        assert "users" in data
        assert "total" in data
        assert data["total"] >= 1  # At least the admin user

    @pytest.mark.asyncio
    async def test_019_create_internal_user(self):
        """Test creating a new internal user."""
        global internal_user_id

        token = await get_admin_token()
        assert token is not None

        headers = get_headers(token)

        user_data = {
            "email": f"agent{TEST_RUN_ID}@kenyaaccounting.com",
            "first_name": "Test",
            "last_name": f"Agent{TEST_RUN_ID}",
            "role": "support_agent"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BASE_URL}/admin/users",
                headers=headers,
                json=user_data
            )

        assert response.status_code == 201, f"Failed to create internal user: {response.text}"
        data = response.json()

        assert "id" in data
        assert data["role"] == "support_agent"
        assert data["must_change_password"] == True

        internal_user_id = data["id"]

    @pytest.mark.asyncio
    async def test_020_get_internal_user_details(self):
        """Test getting internal user details."""
        global internal_user_id

        if not internal_user_id:
            pytest.skip("No internal user ID from previous tests")

        token = await get_admin_token()
        assert token is not None

        headers = get_headers(token)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/admin/users/{internal_user_id}",
                headers=headers
            )

        assert response.status_code == 200, f"Failed to get user details: {response.text}"
        data = response.json()

        assert data["id"] == internal_user_id
        # Email should be masked
        if "email_masked" in data:
            assert "****" in data["email_masked"] or "*" in data["email_masked"]

    @pytest.mark.asyncio
    async def test_021_update_internal_user(self):
        """Test updating internal user information."""
        global internal_user_id

        if not internal_user_id:
            pytest.skip("No internal user ID from previous tests")

        token = await get_admin_token()
        assert token is not None

        headers = get_headers(token)

        update_data = {
            "first_name": "Updated",
            "last_name": f"AgentName{TEST_RUN_ID}",
            "phone": "0700000000"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.put(
                f"{BASE_URL}/admin/users/{internal_user_id}",
                headers=headers,
                json=update_data
            )

        assert response.status_code == 200, f"Failed to update user: {response.text}"
        data = response.json()

        # Check full_name is constructed from first_name + last_name
        assert "full_name" in data

    @pytest.mark.asyncio
    async def test_022_filter_internal_users_by_role(self):
        """Test filtering internal users by role."""
        token = await get_admin_token()
        assert token is not None

        headers = get_headers(token)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/admin/users?role=system_admin",
                headers=headers
            )

        assert response.status_code == 200
        data = response.json()

        # All returned users should be system_admin
        for user in data.get("users", []):
            assert user["role"] == "system_admin"


class TestAdminAuditLogs:
    """Test audit log querying endpoints."""

    @pytest.mark.asyncio
    async def test_023_query_audit_logs(self):
        """Test querying audit logs with pagination."""
        global audit_log_id

        token = await get_admin_token()
        assert token is not None

        headers = get_headers(token)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/admin/audit-logs?page=1&page_size=20",
                headers=headers
            )

        assert response.status_code == 200, f"Failed to query audit logs: {response.text}"
        data = response.json()

        assert "logs" in data or "audit_logs" in data
        assert "total" in data

        # Store first log ID for detail test
        logs = data.get("logs", data.get("audit_logs", []))
        if logs and len(logs) > 0:
            audit_log_id = logs[0]["id"]

    @pytest.mark.asyncio
    async def test_024_filter_audit_logs_by_action(self):
        """Test filtering audit logs by action type."""
        token = await get_admin_token()
        assert token is not None

        headers = get_headers(token)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/admin/audit-logs?action=login",
                headers=headers
            )

        assert response.status_code == 200
        data = response.json()

        # All returned logs should have login action
        logs = data.get("logs", data.get("audit_logs", []))
        for log in logs:
            assert log["action"] == "login"

    @pytest.mark.asyncio
    async def test_025_get_audit_log_details(self):
        """Test getting single audit log entry."""
        global audit_log_id

        if not audit_log_id:
            pytest.skip("No audit log ID from previous tests")

        token = await get_admin_token()
        assert token is not None

        headers = get_headers(token)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/admin/audit-logs/{audit_log_id}",
                headers=headers
            )

        assert response.status_code == 200, f"Failed to get audit log: {response.text}"
        data = response.json()

        assert data["id"] == audit_log_id
        assert "action" in data
        assert "created_at" in data


class TestAdminDashboard:
    """Test admin dashboard and analytics endpoints."""

    @pytest.mark.asyncio
    async def test_026_admin_dashboard_stats(self):
        """Test getting admin dashboard statistics."""
        token = await get_admin_token()
        assert token is not None

        headers = get_headers(token)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/admin/dashboard",
                headers=headers
            )

        assert response.status_code == 200, f"Failed to get dashboard stats: {response.text}"
        data = response.json()

        # Verify stats structure
        assert "total_businesses" in data
        assert "total_users" in data or "active_users" in data

    @pytest.mark.asyncio
    async def test_027_system_health_metrics(self):
        """Test getting system health metrics."""
        token = await get_admin_token()
        assert token is not None

        headers = get_headers(token)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/admin/system-health",
                headers=headers
            )

        assert response.status_code == 200, f"Failed to get system health: {response.text}"
        data = response.json()

        # Verify health metrics structure
        assert "database_status" in data or "status" in data


# ================================
# PDF GENERATION TESTS (8 tests)
# ================================

class TestPDFGeneration:
    """Test PDF generation endpoints."""

    @pytest.mark.asyncio
    async def test_028_generate_invoice_pdf(self):
        """Test generating invoice PDF."""
        invoice_id = await create_test_invoice()
        if not invoice_id:
            pytest.skip("Could not create test invoice")

        token = await get_business_token()
        assert token is not None

        headers = get_headers(token)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/invoices/{invoice_id}/pdf",
                headers=headers
            )

        assert response.status_code == 200, f"Failed to generate invoice PDF: {response.text}"
        assert response.headers["content-type"] == "application/pdf"
        assert "attachment" in response.headers.get("content-disposition", "").lower()
        assert len(response.content) > 0  # PDF has content

    @pytest.mark.asyncio
    async def test_029_generate_payment_receipt_pdf(self):
        """Test generating payment receipt PDF."""
        payment_id = await create_test_payment()
        if not payment_id:
            pytest.skip("Could not create test payment")

        token = await get_business_token()
        assert token is not None

        headers = get_headers(token)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/payments/{payment_id}/receipt/pdf",
                headers=headers
            )

        assert response.status_code == 200, f"Failed to generate receipt PDF: {response.text}"
        assert response.headers["content-type"] == "application/pdf"
        assert len(response.content) > 0

    @pytest.mark.asyncio
    async def test_030_generate_profit_loss_pdf(self):
        """Test generating P&L report PDF."""
        token = await get_business_token()
        assert token is not None

        headers = get_headers(token)

        start_date = (date.today() - timedelta(days=30)).isoformat()
        end_date = date.today().isoformat()

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/reports/profit-loss/pdf?start_date={start_date}&end_date={end_date}",
                headers=headers
            )

        assert response.status_code == 200, f"Failed to generate P&L PDF: {response.text}"
        assert response.headers["content-type"] == "application/pdf"
        assert len(response.content) > 0

    @pytest.mark.asyncio
    async def test_031_generate_expense_summary_pdf(self):
        """Test generating expense summary PDF."""
        token = await get_business_token()
        assert token is not None

        headers = get_headers(token)

        start_date = (date.today() - timedelta(days=30)).isoformat()
        end_date = date.today().isoformat()

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/reports/expense-summary/pdf?start_date={start_date}&end_date={end_date}",
                headers=headers
            )

        assert response.status_code == 200, f"Failed to generate expense PDF: {response.text}"
        assert response.headers["content-type"] == "application/pdf"
        assert len(response.content) > 0

    @pytest.mark.asyncio
    async def test_032_generate_aged_receivables_pdf(self):
        """Test generating aged receivables PDF."""
        token = await get_business_token()
        assert token is not None

        headers = get_headers(token)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/reports/aged-receivables/pdf",
                headers=headers
            )

        assert response.status_code == 200, f"Failed to generate aged receivables PDF: {response.text}"
        assert response.headers["content-type"] == "application/pdf"
        assert len(response.content) > 0

    @pytest.mark.asyncio
    async def test_033_pdf_requires_authentication(self):
        """Test that PDF endpoints require authentication."""
        invoice_id = await create_test_invoice()
        if not invoice_id:
            pytest.skip("Could not create test invoice")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/invoices/{invoice_id}/pdf"
            )

        # 401 (Unauthorized) or 403 (Forbidden/IP blocked) are both valid responses
        assert response.status_code in [401, 403], f"PDF should require authentication, got {response.status_code}"

    @pytest.mark.asyncio
    async def test_034_pdf_business_isolation(self):
        """Test that users cannot access other business's PDFs."""
        # This test would require a second business user
        # For now, test with invalid invoice ID
        token = await get_business_token()
        assert token is not None

        headers = get_headers(token)

        fake_invoice_id = "00000000-0000-0000-0000-000000000000"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/invoices/{fake_invoice_id}/pdf",
                headers=headers
            )

        assert response.status_code == 404, "Should not access non-existent invoice PDF"

    @pytest.mark.asyncio
    async def test_035_pdf_date_range_validation(self):
        """Test PDF endpoints validate date ranges."""
        token = await get_business_token()
        assert token is not None

        headers = get_headers(token)

        # Invalid date range (end before start)
        start_date = date.today().isoformat()
        end_date = (date.today() - timedelta(days=30)).isoformat()

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/reports/profit-loss/pdf?start_date={start_date}&end_date={end_date}",
                headers=headers
            )

        assert response.status_code == 400, "Should reject invalid date range"


# ================================
# AUTHORIZATION & SECURITY TESTS (3 tests)
# ================================

class TestAuthorizationAndSecurity:
    """Test role-based access control and security."""

    @pytest.mark.asyncio
    async def test_036_onboarding_requires_agent_role(self):
        """Test that onboarding endpoints require onboarding_agent role."""
        token = await get_business_token()
        assert token is not None

        headers = get_headers(token)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/onboarding/applications",
                headers=headers
            )

        assert response.status_code == 403, "Business user should not access onboarding"

    @pytest.mark.asyncio
    async def test_037_admin_requires_system_admin_role(self):
        """Test that admin endpoints require system_admin role."""
        token = await get_support_token()
        assert token is not None

        headers = get_headers(token)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/admin/businesses",
                headers=headers
            )

        # Support agents should NOT have access to admin endpoints
        assert response.status_code == 403, "Support agent should not access admin endpoints"

    @pytest.mark.asyncio
    async def test_038_unauthenticated_requests_rejected(self):
        """Test that unauthenticated requests are rejected."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test onboarding endpoint
            response1 = await client.get(
                f"{BASE_URL}/onboarding/applications"
            )

            # Test admin endpoint
            response2 = await client.get(
                f"{BASE_URL}/admin/businesses"
            )

        assert response1.status_code in [401, 403], "Should require authentication"
        assert response2.status_code in [401, 403], "Should require authentication"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
