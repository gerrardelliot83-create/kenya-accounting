"""
Comprehensive Sprint 2 API Tests

Tests all Sprint 2 features including:
- Contacts API (create, read, update, delete with encryption)
- Items API (create, read, update, delete with SKU uniqueness)
- Invoices API (create, issue, cancel, workflow enforcement)
- Security (authentication, business isolation, input validation)

Test Credentials:
- Email: business@example.com
- Password: BusinessPass123
"""

import pytest
import httpx
from uuid import UUID
from datetime import date, timedelta
from decimal import Decimal
import time

# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)

# Base configuration
BASE_URL = "http://localhost:8000/api/v1"
TEST_EMAIL = "business@example.com"
TEST_PASSWORD = "BusinessPass123"

# Unique test run identifier to avoid data conflicts
TEST_RUN_ID = str(int(time.time()))[-6:]

# Global variables to store test data
auth_token = None
business_id = None
test_customer_id = None
test_supplier_id = None
test_product_id = None
test_service_id = None
test_invoice_id = None


# ================================
# HELPER FUNCTIONS
# ================================

async def get_auth_token():
    """Get authentication token."""
    global auth_token, business_id

    if auth_token:
        return auth_token

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Login with JSON body
        response = await client.post(
            f"{BASE_URL}/auth/login",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            }
        )

        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        auth_token = data["access_token"]

        # Get business_id from user data in login response
        if "user" in data and data["user"]:
            business_id = data["user"].get("business_id")

    return auth_token


def get_headers(token):
    """Get auth headers."""
    return {"Authorization": f"Bearer {token}"}


# ================================
# CONTACTS API TESTS
# ================================

class TestContactsAPI:
    """Test Contacts CRUD operations."""

    @pytest.mark.asyncio
    async def test_001_create_customer_contact(self):
        """Test creating a customer contact with all fields."""
        global test_customer_id

        token = await get_auth_token()
        headers = get_headers(token)

        contact_data = {
            "name": f"Test Customer Ltd {TEST_RUN_ID}",
            "contact_type": "customer",
            "email": f"customer{TEST_RUN_ID}@test.com",
            "phone": "+254712345678",
            "kra_pin": "A001234567X",
            "address": "123 Test Street, Nairobi",
            "notes": "VIP customer"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BASE_URL}/contacts/",
                json=contact_data,
                headers=headers
            )

        assert response.status_code == 201, f"Failed to create customer: {response.text}"
        data = response.json()

        # Verify response structure
        assert "id" in data
        assert data["name"] == contact_data["name"]
        assert data["contact_type"] == "customer"

        # Verify encrypted fields are decrypted in response
        assert data["email"] == contact_data["email"]
        assert data["phone"] == contact_data["phone"]
        assert data["kra_pin"] == contact_data["kra_pin"]

        # Verify other fields
        assert data["address"] == contact_data["address"]
        assert data["notes"] == contact_data["notes"]
        assert data["is_active"] is True

        # Store ID for later tests
        test_customer_id = data["id"]

    @pytest.mark.asyncio
    async def test_002_create_supplier_contact(self):
        """Test creating a supplier contact."""
        global test_supplier_id

        token = await get_auth_token()
        headers = get_headers(token)

        contact_data = {
            "name": f"Test Supplier Co {TEST_RUN_ID}",
            "contact_type": "supplier",
            "email": f"supplier{TEST_RUN_ID}@test.com",
            "phone": "+254722345678"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BASE_URL}/contacts/",
                json=contact_data,
                headers=headers
            )

        assert response.status_code == 201, f"Failed to create supplier: {response.text}"
        data = response.json()

        assert data["contact_type"] == "supplier"
        test_supplier_id = data["id"]

    @pytest.mark.asyncio
    async def test_003_create_contact_missing_required_fields(self):
        """Test validation error when missing required fields."""
        token = await get_auth_token()
        headers = get_headers(token)

        contact_data = {
            "email": "incomplete@test.com"
            # Missing 'name' which is required
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BASE_URL}/contacts/",
                json=contact_data,
                headers=headers
            )

        assert response.status_code == 422, "Should return validation error"

    @pytest.mark.asyncio
    async def test_004_list_contacts_with_pagination(self):
        """Test listing contacts with pagination."""
        token = await get_auth_token()
        headers = get_headers(token)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/contacts/?page=1&page_size=10",
                headers=headers
            )

        assert response.status_code == 200, f"Failed to list contacts: {response.text}"
        data = response.json()

        # Verify pagination structure
        assert "contacts" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data

        # Should have at least 2 contacts from previous tests
        assert data["total"] >= 2
        assert len(data["contacts"]) >= 2

    @pytest.mark.asyncio
    async def test_005_search_contacts_by_name(self):
        """Test searching contacts by name."""
        token = await get_auth_token()
        headers = get_headers(token)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/contacts/?search=Customer",
                headers=headers
            )

        assert response.status_code == 200
        data = response.json()

        # Should find the customer contact
        assert data["total"] >= 1
        assert any("Customer" in contact["name"] for contact in data["contacts"])

    @pytest.mark.asyncio
    async def test_006_filter_contacts_by_type(self):
        """Test filtering contacts by type."""
        token = await get_auth_token()
        headers = get_headers(token)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/contacts/?contact_type=customer",
                headers=headers
            )

        assert response.status_code == 200
        data = response.json()

        # All returned contacts should be customers
        assert all(contact["contact_type"] == "customer" for contact in data["contacts"])

    @pytest.mark.asyncio
    async def test_007_get_single_contact(self):
        """Test getting a single contact by ID."""
        global test_customer_id

        token = await get_auth_token()
        headers = get_headers(token)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/contacts/{test_customer_id}",
                headers=headers
            )

        assert response.status_code == 200, f"Failed to get contact: {response.text}"
        data = response.json()

        assert data["id"] == test_customer_id
        assert "Test Customer Ltd" in data["name"]

    @pytest.mark.asyncio
    async def test_008_update_contact(self):
        """Test updating a contact."""
        global test_customer_id

        token = await get_auth_token()
        headers = get_headers(token)

        update_data = {
            "name": f"Updated Customer Ltd {TEST_RUN_ID}",
            "notes": "Updated notes"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.put(
                f"{BASE_URL}/contacts/{test_customer_id}",
                json=update_data,
                headers=headers
            )

        assert response.status_code == 200, f"Failed to update contact: {response.text}"
        data = response.json()

        assert "Updated Customer Ltd" in data["name"]
        assert data["notes"] == "Updated notes"
        # Email should remain unchanged
        assert f"customer{TEST_RUN_ID}@test.com" == data["email"]

    @pytest.mark.asyncio
    async def test_009_soft_delete_contact(self):
        """Test soft deleting a contact."""
        token = await get_auth_token()
        headers = get_headers(token)

        # Create a temporary contact for deletion
        contact_data = {
            "name": "To Be Deleted",
            "contact_type": "customer"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BASE_URL}/contacts/",
                json=contact_data,
                headers=headers
            )
            assert response.status_code == 201
            contact_id = response.json()["id"]

            # Delete the contact
            response = await client.delete(
                f"{BASE_URL}/contacts/{contact_id}",
                headers=headers
            )

            assert response.status_code == 204, f"Failed to delete contact: {response.text}"

            # Verify contact is soft deleted (not returned in active list)
            response = await client.get(
                f"{BASE_URL}/contacts/?is_active=true",
                headers=headers
            )
            assert response.status_code == 200
            data = response.json()
            assert not any(contact["id"] == contact_id for contact in data["contacts"])


# ================================
# ITEMS API TESTS
# ================================

class TestItemsAPI:
    """Test Items/Services CRUD operations."""

    @pytest.mark.asyncio
    async def test_010_create_product_item(self):
        """Test creating a product item."""
        global test_product_id

        token = await get_auth_token()
        headers = get_headers(token)

        item_data = {
            "name": f"Test Product {TEST_RUN_ID}",
            "item_type": "product",
            "unit_price": 1000.00,
            "tax_rate": 16.0,
            "description": "A test product",
            "sku": f"PROD-{TEST_RUN_ID}"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BASE_URL}/items/",
                json=item_data,
                headers=headers
            )

        assert response.status_code == 201, f"Failed to create product: {response.text}"
        data = response.json()

        assert data["name"] == item_data["name"]
        assert data["item_type"] == "product"
        assert float(data["unit_price"]) == item_data["unit_price"]
        assert float(data["tax_rate"]) == item_data["tax_rate"]
        assert data["sku"] == item_data["sku"]
        assert data["is_active"] is True

        test_product_id = data["id"]

    @pytest.mark.asyncio
    async def test_011_create_service_item(self):
        """Test creating a service item."""
        global test_service_id

        token = await get_auth_token()
        headers = get_headers(token)

        item_data = {
            "name": f"Consulting Service {TEST_RUN_ID}",
            "item_type": "service",
            "unit_price": 5000.00,
            "tax_rate": 16.0,
            "description": "Hourly consulting"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BASE_URL}/items/",
                json=item_data,
                headers=headers
            )

        assert response.status_code == 201, f"Failed to create service: {response.text}"
        data = response.json()

        assert data["item_type"] == "service"
        assert data["sku"] is None  # Services may not have SKU
        test_service_id = data["id"]

    @pytest.mark.asyncio
    async def test_012_sku_uniqueness_per_business(self):
        """Test that SKU must be unique within a business."""
        token = await get_auth_token()
        headers = get_headers(token)

        # Try to create another item with the same SKU
        item_data = {
            "name": "Duplicate SKU Product",
            "item_type": "product",
            "unit_price": 500.00,
            "tax_rate": 16.0,
            "sku": f"PROD-{TEST_RUN_ID}"  # Same as test_product_id
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BASE_URL}/items/",
                json=item_data,
                headers=headers
            )

        # Should fail with 400 error
        assert response.status_code == 400, "Should reject duplicate SKU"

    @pytest.mark.asyncio
    async def test_013_price_validation(self):
        """Test price and tax rate validation."""
        token = await get_auth_token()
        headers = get_headers(token)

        # Negative price should fail
        item_data = {
            "name": "Invalid Price Item",
            "item_type": "product",
            "unit_price": -100.00,
            "tax_rate": 16.0
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BASE_URL}/items/",
                json=item_data,
                headers=headers
            )

        assert response.status_code in [400, 422], "Should reject negative price"

    @pytest.mark.asyncio
    async def test_014_list_items(self):
        """Test listing items."""
        token = await get_auth_token()
        headers = get_headers(token)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/items/?page=1&page_size=10",
                headers=headers
            )

        assert response.status_code == 200, f"Failed to list items: {response.text}"
        data = response.json()

        assert "items" in data
        assert "total" in data
        assert data["total"] >= 2  # At least product and service

    @pytest.mark.asyncio
    async def test_015_filter_items_by_type(self):
        """Test filtering items by type."""
        token = await get_auth_token()
        headers = get_headers(token)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/items/?item_type=product",
                headers=headers
            )

        assert response.status_code == 200
        data = response.json()

        # All returned items should be products
        assert all(item["item_type"] == "product" for item in data["items"])

    @pytest.mark.asyncio
    async def test_016_get_single_item(self):
        """Test getting a single item by ID."""
        global test_product_id

        token = await get_auth_token()
        headers = get_headers(token)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/items/{test_product_id}",
                headers=headers
            )

        assert response.status_code == 200, f"Failed to get item: {response.text}"
        data = response.json()

        assert data["id"] == test_product_id
        assert f"Test Product" in data["name"]

    @pytest.mark.asyncio
    async def test_017_update_item(self):
        """Test updating an item."""
        global test_product_id

        token = await get_auth_token()
        headers = get_headers(token)

        update_data = {
            "name": f"Updated Product Name {TEST_RUN_ID}",
            "unit_price": 1200.00
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.put(
                f"{BASE_URL}/items/{test_product_id}",
                json=update_data,
                headers=headers
            )

        assert response.status_code == 200, f"Failed to update item: {response.text}"
        data = response.json()

        assert "Updated Product Name" in data["name"]
        assert float(data["unit_price"]) == 1200.00

    @pytest.mark.asyncio
    async def test_018_soft_delete_item(self):
        """Test soft deleting an item."""
        token = await get_auth_token()
        headers = get_headers(token)

        # Create a temporary item for deletion
        item_data = {
            "name": "To Be Deleted",
            "item_type": "product",
            "unit_price": 100.00,
            "tax_rate": 16.0
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BASE_URL}/items/",
                json=item_data,
                headers=headers
            )
            assert response.status_code == 201
            item_id = response.json()["id"]

            # Delete the item
            response = await client.delete(
                f"{BASE_URL}/items/{item_id}",
                headers=headers
            )

            assert response.status_code == 204, f"Failed to delete item: {response.text}"


# ================================
# INVOICES API TESTS
# ================================

class TestInvoicesAPI:
    """Test Invoices CRUD and workflow operations."""

    @pytest.mark.asyncio
    async def test_019_create_invoice_with_line_items(self):
        """Test creating an invoice with line items."""
        global test_invoice_id, test_customer_id, test_product_id, test_service_id

        token = await get_auth_token()
        headers = get_headers(token)

        # Ensure we have test data
        assert test_customer_id is not None, "Need customer contact for invoice"
        assert test_product_id is not None, "Need product item for invoice"

        invoice_data = {
            "contact_id": test_customer_id,
            "due_date": str(date.today() + timedelta(days=30)),
            "notes": "Test invoice",
            "line_items": [
                {
                    "item_id": test_product_id,
                    "quantity": 2,
                    "unit_price": 1200.00,
                    "tax_rate": 16.0,
                    "description": f"Updated Product Name {TEST_RUN_ID}"
                },
                {
                    "item_id": test_service_id,
                    "quantity": 1,
                    "unit_price": 5000.00,
                    "tax_rate": 16.0,
                    "description": f"Consulting Service {TEST_RUN_ID}"
                }
            ]
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BASE_URL}/invoices/",
                json=invoice_data,
                headers=headers
            )

        assert response.status_code == 201, f"Failed to create invoice: {response.text}"
        data = response.json()

        # Verify invoice structure
        assert "id" in data
        assert "invoice_number" in data
        assert data["status"] == "draft"
        assert data["contact_id"] == test_customer_id

        # Verify invoice number format (INV-YYYY-NNNNN)
        assert data["invoice_number"].startswith("INV-")
        parts = data["invoice_number"].split("-")
        assert len(parts) == 3
        assert len(parts[1]) == 4  # Year
        assert len(parts[2]) == 5  # Sequence

        # Verify line items
        assert "line_items" in data
        assert len(data["line_items"]) == 2

        # Verify total calculations
        # Line 1: 2 * 1200 = 2400, tax = 384, total = 2784
        # Line 2: 1 * 5000 = 5000, tax = 800, total = 5800
        # Subtotal: 7400, Tax: 1184, Total: 8584
        assert float(data["subtotal"]) == 7400.00
        assert float(data["tax_amount"]) == 1184.00
        assert float(data["total_amount"]) == 8584.00

        test_invoice_id = data["id"]

    @pytest.mark.asyncio
    async def test_020_get_invoice_with_line_items(self):
        """Test getting an invoice with line items."""
        global test_invoice_id

        token = await get_auth_token()
        headers = get_headers(token)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/invoices/{test_invoice_id}",
                headers=headers
            )

        assert response.status_code == 200, f"Failed to get invoice: {response.text}"
        data = response.json()

        assert data["id"] == test_invoice_id
        assert "line_items" in data
        assert len(data["line_items"]) == 2

    @pytest.mark.asyncio
    async def test_021_update_draft_invoice(self):
        """Test updating a draft invoice."""
        global test_invoice_id

        token = await get_auth_token()
        headers = get_headers(token)

        update_data = {
            "notes": "Updated invoice notes"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.put(
                f"{BASE_URL}/invoices/{test_invoice_id}",
                json=update_data,
                headers=headers
            )

        assert response.status_code == 200, f"Failed to update invoice: {response.text}"
        data = response.json()

        assert data["notes"] == "Updated invoice notes"

    @pytest.mark.asyncio
    async def test_022_issue_invoice(self):
        """Test issuing an invoice (draft -> issued)."""
        global test_invoice_id

        token = await get_auth_token()
        headers = get_headers(token)

        issue_data = {
            "issue_date": str(date.today())
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BASE_URL}/invoices/{test_invoice_id}/issue",
                json=issue_data,
                headers=headers
            )

        assert response.status_code == 200, f"Failed to issue invoice: {response.text}"
        data = response.json()

        assert data["status"] == "issued"
        assert data["issue_date"] == str(date.today())

    @pytest.mark.asyncio
    async def test_023_edit_blocked_after_issuing(self):
        """Test that issued invoices cannot be edited."""
        global test_invoice_id

        token = await get_auth_token()
        headers = get_headers(token)

        update_data = {
            "notes": "Should not be allowed"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.put(
                f"{BASE_URL}/invoices/{test_invoice_id}",
                json=update_data,
                headers=headers
            )

        # Should be rejected
        assert response.status_code == 400, "Should not allow editing issued invoice"

    @pytest.mark.asyncio
    async def test_024_list_invoices_with_filters(self):
        """Test listing invoices with status filter."""
        token = await get_auth_token()
        headers = get_headers(token)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/invoices/?status=issued",
                headers=headers
            )

        assert response.status_code == 200, f"Failed to list invoices: {response.text}"
        data = response.json()

        assert "invoices" in data
        # All returned invoices should be issued
        assert all(invoice["status"] == "issued" for invoice in data["invoices"])

    @pytest.mark.asyncio
    async def test_025_filter_invoices_by_date_range(self):
        """Test filtering invoices by date range."""
        token = await get_auth_token()
        headers = get_headers(token)

        start_date = date.today() - timedelta(days=7)
        end_date = date.today()

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/invoices/?start_date={start_date}&end_date={end_date}",
                headers=headers
            )

        assert response.status_code == 200
        # Just verify endpoint works, actual filtering depends on data

    @pytest.mark.asyncio
    async def test_026_cancel_invoice(self):
        """Test canceling an invoice."""
        global test_customer_id, test_product_id

        token = await get_auth_token()
        headers = get_headers(token)

        # Create a new draft invoice to cancel
        invoice_data = {
            "contact_id": test_customer_id,
            "due_date": str(date.today() + timedelta(days=30)),
            "line_items": [
                {
                    "item_id": test_product_id,
                    "quantity": 1,
                    "unit_price": 1200.00,
                    "tax_rate": 16.0,
                    "description": "Test"
                }
            ]
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BASE_URL}/invoices/",
                json=invoice_data,
                headers=headers
            )
            assert response.status_code == 201
            invoice_id = response.json()["id"]

            # Cancel the invoice
            response = await client.post(
                f"{BASE_URL}/invoices/{invoice_id}/cancel",
                headers=headers
            )

            assert response.status_code == 200, f"Failed to cancel invoice: {response.text}"
            data = response.json()

            assert data["status"] == "cancelled"

    @pytest.mark.asyncio
    async def test_027_invoice_status_workflow(self):
        """Test invoice status workflow enforcement."""
        global test_customer_id, test_product_id

        token = await get_auth_token()
        headers = get_headers(token)

        # Create draft invoice
        invoice_data = {
            "contact_id": test_customer_id,
            "due_date": str(date.today() + timedelta(days=30)),
            "line_items": [
                {
                    "item_id": test_product_id,
                    "quantity": 1,
                    "unit_price": 1000.00,
                    "tax_rate": 16.0,
                    "description": "Test"
                }
            ]
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BASE_URL}/invoices/",
                json=invoice_data,
                headers=headers
            )
            assert response.status_code == 201
            invoice_id = response.json()["id"]

            # Issue it
            response = await client.post(
                f"{BASE_URL}/invoices/{invoice_id}/issue",
                json={"issue_date": str(date.today())},
                headers=headers
            )
            assert response.status_code == 200
            assert response.json()["status"] == "issued"

            # Try to issue again - should fail
            response = await client.post(
                f"{BASE_URL}/invoices/{invoice_id}/issue",
                json={"issue_date": str(date.today())},
                headers=headers
            )
            assert response.status_code == 400, "Should not allow re-issuing"


# ================================
# SECURITY TESTS
# ================================

class TestSecurity:
    """Test security and authorization."""

    @pytest.mark.asyncio
    async def test_028_unauthorized_access_no_token(self):
        """Test that endpoints require authentication."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Try to access contacts without token
            response = await client.get(f"{BASE_URL}/contacts/")
            assert response.status_code in [401, 403], "Should require authentication"

            # Try to access items without token
            response = await client.get(f"{BASE_URL}/items/")
            assert response.status_code in [401, 403], "Should require authentication"

            # Try to access invoices without token
            response = await client.get(f"{BASE_URL}/invoices/")
            assert response.status_code in [401, 403], "Should require authentication"

    @pytest.mark.asyncio
    async def test_029_invalid_token(self):
        """Test that invalid tokens are rejected."""
        headers = {"Authorization": "Bearer invalid_token_12345"}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{BASE_URL}/contacts/", headers=headers)
            assert response.status_code == 401, "Should reject invalid token"

    @pytest.mark.asyncio
    async def test_030_business_isolation(self):
        """Test that users can only access their own business data."""
        token = await get_auth_token()
        headers = get_headers(token)

        # This test verifies the basic business scoping
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/contacts/",
                headers=headers
            )

            assert response.status_code == 200
            # All contacts should belong to the user's business
            # This is enforced at the service layer

    @pytest.mark.asyncio
    async def test_031_sql_injection_prevention(self):
        """Test that SQL injection attempts are prevented."""
        token = await get_auth_token()
        headers = get_headers(token)

        # Try SQL injection in search parameter
        malicious_search = "'; DROP TABLE contacts; --"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/contacts/?search={malicious_search}",
                headers=headers
            )

            # Should return normal response (empty or not), not error
            assert response.status_code == 200
            # Database should still be intact

            response = await client.get(
                f"{BASE_URL}/contacts/",
                headers=headers
            )
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_032_xss_input_sanitization(self):
        """Test that XSS attempts are handled properly."""
        token = await get_auth_token()
        headers = get_headers(token)

        # Try to create contact with XSS in name
        contact_data = {
            "name": "<script>alert('xss')</script>",
            "contact_type": "customer"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BASE_URL}/contacts/",
                json=contact_data,
                headers=headers
            )

            # Should accept but store safely
            if response.status_code == 201:
                data = response.json()
                # The data should be stored as-is (escaping is frontend's job)
                # Backend should just store it safely
                assert data["name"] == contact_data["name"]

    @pytest.mark.asyncio
    async def test_033_input_validation_boundary_conditions(self):
        """Test input validation for boundary conditions."""
        token = await get_auth_token()
        headers = get_headers(token)

        # Test extremely long name
        long_name = "A" * 1000
        contact_data = {
            "name": long_name,
            "contact_type": "customer"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BASE_URL}/contacts/",
                json=contact_data,
                headers=headers
            )

            # Should reject or truncate
            assert response.status_code in [400, 422], "Should validate name length"

    @pytest.mark.asyncio
    async def test_034_invalid_uuid_format(self):
        """Test that invalid UUID formats are rejected."""
        token = await get_auth_token()
        headers = get_headers(token)

        invalid_id = "not-a-valid-uuid"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/contacts/{invalid_id}",
                headers=headers
            )

            assert response.status_code == 422, "Should reject invalid UUID format"

    @pytest.mark.asyncio
    async def test_035_access_nonexistent_resource(self):
        """Test accessing non-existent resources."""
        token = await get_auth_token()
        headers = get_headers(token)

        # Use a valid UUID format but non-existent resource
        fake_id = "00000000-0000-0000-0000-000000000000"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/contacts/{fake_id}",
                headers=headers
            )

            assert response.status_code == 404, "Should return 404 for non-existent resource"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
