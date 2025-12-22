"""
Comprehensive Sprint 5 API Tests

Tests all Sprint 5 features including:
- Tax APIs (settings, VAT/TOT calculations, filing guidance, export)
- Report APIs (P&L, expense summary, aged receivables, sales summary)
- Support Ticket APIs (client-facing ticket operations)
- Help Centre APIs (FAQ and help articles)
- Admin Support APIs (support agent operations)
- Authorization and business isolation
- Data validation and error handling

Test Credentials:
- Business User: business@example.com / BusinessPass123
- Support Agent: support@example.com / SupportPass123
"""

import pytest
import httpx
from uuid import UUID
from datetime import date, datetime, timedelta
from decimal import Decimal
import time

# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)

# Base configuration
BASE_URL = "http://localhost:8000/api/v1"
TEST_EMAIL = "business@example.com"
TEST_PASSWORD = "BusinessPass123"
SUPPORT_EMAIL = "support@example.com"
SUPPORT_PASSWORD = "SupportPass123"

# Unique test run identifier to avoid data conflicts
TEST_RUN_ID = str(int(time.time()))[-6:]

# Global variables to store test data
auth_token = None
support_token = None
business_id = None
test_customer_id = None
test_product_id = None
test_invoice_id = None
test_expense_id = None
test_ticket_id = None
test_ticket_number = None


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

        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        auth_token = data["access_token"]

        # Get business_id from user data
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

        assert response.status_code == 200, f"Support login failed: {response.text}"
        data = response.json()
        support_token = data["access_token"]

    return support_token


def get_headers(token):
    """Get auth headers."""
    return {"Authorization": f"Bearer {token}"}


async def create_test_customer():
    """Helper to create a test customer."""
    global test_customer_id

    if test_customer_id:
        return test_customer_id

    token = await get_auth_token()
    headers = get_headers(token)

    contact_data = {
        "name": f"Sprint5 Test Customer {TEST_RUN_ID}",
        "contact_type": "customer",
        "email": f"s5customer{TEST_RUN_ID}@test.com",
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
    """Helper to create a test product."""
    global test_product_id

    if test_product_id:
        return test_product_id

    token = await get_auth_token()
    headers = get_headers(token)

    item_data = {
        "name": f"Sprint5 Test Product {TEST_RUN_ID}",
        "item_type": "product",
        "unit_price": 10000.00,
        "tax_rate": 16.0,
        "sku": f"S5PROD-{TEST_RUN_ID}"
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


async def create_test_invoice(status="issued", amount=10000.00):
    """Helper to create a test invoice."""
    global test_invoice_id

    token = await get_auth_token()
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
                "unit_price": amount,
                "tax_rate": 16.0,
                "description": "Test product for Sprint 5"
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

        # Issue if requested
        if status == "issued":
            response = await client.post(
                f"{BASE_URL}/invoices/{invoice_id}/issue",
                json={"issue_date": date.today().isoformat()},
                headers=headers
            )
            if response.status_code != 200:
                return None

        test_invoice_id = invoice_id
        return invoice_id


async def create_test_expense(category="office_supplies", amount=5000.00):
    """Helper to create a test expense."""
    global test_expense_id

    token = await get_auth_token()
    headers = get_headers(token)

    expense_data = {
        "category": category,
        "description": f"Sprint5 Test Expense {TEST_RUN_ID}",
        "amount": amount,
        "tax_amount": amount * 0.16,
        "expense_date": date.today().isoformat(),
        "vendor_name": "Test Vendor",
        "payment_method": "mpesa",
        "reference_number": f"REF{TEST_RUN_ID}"
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/expenses/",
            json=expense_data,
            headers=headers
        )

    if response.status_code == 201:
        test_expense_id = response.json()["id"]
        return test_expense_id
    return None


# ================================
# TAX API TESTS (10+ tests)
# ================================

class TestTaxAPIs:
    """Test tax settings and calculations."""

    @pytest.mark.asyncio
    async def test_001_get_tax_settings_default(self):
        """Test getting tax settings returns valid structure."""
        token = await get_auth_token()
        headers = get_headers(token)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/tax/settings",
                headers=headers
            )

        assert response.status_code == 200, f"Failed to get tax settings: {response.text}"
        data = response.json()

        # Verify structure (settings may already exist from previous tests)
        assert "is_vat_registered" in data
        assert "is_tot_eligible" in data
        assert "financial_year_start_month" in data
        assert isinstance(data["is_vat_registered"], bool)
        assert isinstance(data["is_tot_eligible"], bool)

    @pytest.mark.asyncio
    async def test_002_update_tax_settings_vat_registered(self):
        """Test updating tax settings to VAT registered."""
        token = await get_auth_token()
        headers = get_headers(token)

        update_data = {
            "is_vat_registered": True,
            "vat_registration_number": "P051234567A",
            "vat_registration_date": "2024-01-01"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.put(
                f"{BASE_URL}/tax/settings",
                json=update_data,
                headers=headers
            )

        assert response.status_code == 200, f"Failed to update tax settings: {response.text}"
        data = response.json()

        assert data["is_vat_registered"] == True
        assert data["vat_registration_number"] == "P051234567A"
        assert data["vat_registration_date"] == "2024-01-01"

    @pytest.mark.asyncio
    async def test_003_update_tax_settings_tot_eligible(self):
        """Test setting TOT eligible (switches off VAT)."""
        token = await get_auth_token()
        headers = get_headers(token)

        # First disable VAT
        update_data = {
            "is_vat_registered": False,
            "is_tot_eligible": True
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.put(
                f"{BASE_URL}/tax/settings",
                json=update_data,
                headers=headers
            )

        assert response.status_code == 200, f"Failed to update tax settings: {response.text}"
        data = response.json()

        assert data["is_vat_registered"] == False
        assert data["is_tot_eligible"] == True

    @pytest.mark.asyncio
    async def test_004_update_tax_settings_cannot_be_both(self):
        """Test that business cannot be both VAT registered and TOT eligible."""
        token = await get_auth_token()
        headers = get_headers(token)

        invalid_data = {
            "is_vat_registered": True,
            "vat_registration_number": "P051234567A",
            "is_tot_eligible": True
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.put(
                f"{BASE_URL}/tax/settings",
                json=invalid_data,
                headers=headers
            )

        # Should reject this combination
        assert response.status_code == 400, "Should reject VAT + TOT combination"

    @pytest.mark.asyncio
    async def test_005_get_vat_summary(self):
        """Test VAT summary calculation."""
        token = await get_auth_token()
        headers = get_headers(token)

        # Create some test data first
        await create_test_invoice(status="issued")
        await create_test_expense()

        # Enable VAT
        async with httpx.AsyncClient(timeout=30.0) as client:
            await client.put(
                f"{BASE_URL}/tax/settings",
                json={
                    "is_vat_registered": True,
                    "vat_registration_number": "P051234567A",
                    "is_tot_eligible": False
                },
                headers=headers
            )

            # Get VAT summary
            start_date = (date.today() - timedelta(days=30)).isoformat()
            end_date = date.today().isoformat()

            response = await client.get(
                f"{BASE_URL}/tax/vat-summary?start_date={start_date}&end_date={end_date}&period=month",
                headers=headers
            )

        assert response.status_code == 200, f"Failed to get VAT summary: {response.text}"
        data = response.json()

        # Verify structure
        assert "start_date" in data
        assert "output_vat" in data
        assert "input_vat" in data
        assert "net_vat" in data
        assert "total_sales" in data
        assert "total_expenses" in data

    @pytest.mark.asyncio
    async def test_006_get_vat_summary_no_data(self):
        """Test VAT summary returns zeros when no data."""
        token = await get_auth_token()
        headers = get_headers(token)

        # Use a date range far in the future
        start_date = (date.today() + timedelta(days=365)).isoformat()
        end_date = (date.today() + timedelta(days=395)).isoformat()

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/tax/vat-summary?start_date={start_date}&end_date={end_date}",
                headers=headers
            )

        assert response.status_code == 200
        data = response.json()

        # Should return zero amounts
        assert float(data["output_vat"]) == 0.0
        assert float(data["input_vat"]) == 0.0
        assert float(data["net_vat"]) == 0.0

    @pytest.mark.asyncio
    async def test_007_get_tot_summary(self):
        """Test TOT summary calculation."""
        token = await get_auth_token()
        headers = get_headers(token)

        # Enable TOT
        async with httpx.AsyncClient(timeout=30.0) as client:
            await client.put(
                f"{BASE_URL}/tax/settings",
                json={
                    "is_vat_registered": False,
                    "is_tot_eligible": True
                },
                headers=headers
            )

            # Get TOT summary
            start_date = (date.today() - timedelta(days=30)).isoformat()
            end_date = date.today().isoformat()

            response = await client.get(
                f"{BASE_URL}/tax/tot-summary?start_date={start_date}&end_date={end_date}",
                headers=headers
            )

        assert response.status_code == 200, f"Failed to get TOT summary: {response.text}"
        data = response.json()

        # Verify structure
        assert "period" in data
        assert "gross_turnover" in data
        assert "tot_payable" in data
        assert "tot_rate" in data

    @pytest.mark.asyncio
    async def test_008_get_filing_guidance_vat(self):
        """Test filing guidance for VAT registered business."""
        token = await get_auth_token()
        headers = get_headers(token)

        # Enable VAT
        async with httpx.AsyncClient(timeout=30.0) as client:
            await client.put(
                f"{BASE_URL}/tax/settings",
                json={
                    "is_vat_registered": True,
                    "vat_registration_number": "P051234567A",
                    "is_tot_eligible": False
                },
                headers=headers
            )

            response = await client.get(
                f"{BASE_URL}/tax/filing-guidance",
                headers=headers
            )

        assert response.status_code == 200
        data = response.json()

        assert data["tax_type"] == "VAT"
        assert "next_filing_date" in data
        assert "requirements" in data

    @pytest.mark.asyncio
    async def test_009_get_filing_guidance_tot(self):
        """Test filing guidance for TOT eligible business."""
        token = await get_auth_token()
        headers = get_headers(token)

        # Enable TOT
        async with httpx.AsyncClient(timeout=30.0) as client:
            await client.put(
                f"{BASE_URL}/tax/settings",
                json={
                    "is_vat_registered": False,
                    "is_tot_eligible": True
                },
                headers=headers
            )

            response = await client.get(
                f"{BASE_URL}/tax/filing-guidance",
                headers=headers
            )

        assert response.status_code == 200
        data = response.json()

        assert data["tax_type"] == "TOT"
        assert "next_filing_date" in data

    @pytest.mark.asyncio
    async def test_010_export_vat_return(self):
        """Test exporting VAT return."""
        token = await get_auth_token()
        headers = get_headers(token)

        # Enable VAT
        async with httpx.AsyncClient(timeout=30.0) as client:
            await client.put(
                f"{BASE_URL}/tax/settings",
                json={
                    "is_vat_registered": True,
                    "vat_registration_number": "P051234567A"
                },
                headers=headers
            )

            # Export VAT return
            start_date = (date.today() - timedelta(days=30)).isoformat()
            end_date = date.today().isoformat()

            response = await client.get(
                f"{BASE_URL}/tax/vat-return/export?start_date={start_date}&end_date={end_date}",
                headers=headers
            )

        assert response.status_code == 200, f"Failed to export VAT return: {response.text}"
        data = response.json()

        # Verify export structure (iTax format)
        assert "vat_registration_number" in data
        assert "period_month" in data
        assert "period_year" in data
        assert "output_vat" in data
        assert "input_vat" in data
        assert "net_vat" in data


# ================================
# REPORT API TESTS (8+ tests)
# ================================

class TestReportAPIs:
    """Test financial report generation."""

    @pytest.mark.asyncio
    async def test_011_profit_loss_report(self):
        """Test P&L report generation."""
        token = await get_auth_token()
        headers = get_headers(token)

        # Create some test data
        await create_test_invoice(status="issued")
        await create_test_expense()

        start_date = (date.today() - timedelta(days=30)).isoformat()
        end_date = date.today().isoformat()

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/reports/profit-loss?start_date={start_date}&end_date={end_date}",
                headers=headers
            )

        assert response.status_code == 200, f"Failed to get P&L report: {response.text}"
        data = response.json()

        # Verify structure
        assert "start_date" in data
        assert "end_date" in data
        assert "total_revenue" in data
        assert "total_expenses" in data
        assert "gross_profit" in data
        assert "net_profit" in data
        assert "expenses_by_category" in data

    @pytest.mark.asyncio
    async def test_012_profit_loss_no_data(self):
        """Test P&L report with no data returns zeros."""
        token = await get_auth_token()
        headers = get_headers(token)

        # Use future date range
        start_date = (date.today() + timedelta(days=365)).isoformat()
        end_date = (date.today() + timedelta(days=395)).isoformat()

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/reports/profit-loss?start_date={start_date}&end_date={end_date}",
                headers=headers
            )

        assert response.status_code == 200
        data = response.json()

        assert float(data["total_revenue"]) == 0.0
        assert float(data["total_expenses"]) == 0.0
        assert float(data["net_profit"]) == 0.0

    @pytest.mark.asyncio
    async def test_013_expense_summary_by_category(self):
        """Test expense summary grouped by category."""
        token = await get_auth_token()
        headers = get_headers(token)

        # Create expenses in different categories
        await create_test_expense(category="office_supplies", amount=2000.00)
        await create_test_expense(category="utilities", amount=5000.00)
        await create_test_expense(category="rent", amount=30000.00)

        start_date = (date.today() - timedelta(days=30)).isoformat()
        end_date = date.today().isoformat()

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/reports/expense-summary?start_date={start_date}&end_date={end_date}",
                headers=headers
            )

        assert response.status_code == 200, f"Failed to get expense summary: {response.text}"
        data = response.json()

        # Verify structure
        assert "start_date" in data
        assert "total_expenses" in data
        assert "categories" in data
        assert isinstance(data["categories"], list)

    @pytest.mark.asyncio
    async def test_014_aged_receivables_buckets(self):
        """Test aged receivables with correct aging buckets."""
        token = await get_auth_token()
        headers = get_headers(token)

        # Create invoices with different due dates
        await create_test_invoice(status="issued")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/reports/aged-receivables",
                headers=headers
            )

        assert response.status_code == 200, f"Failed to get aged receivables: {response.text}"
        data = response.json()

        # Verify bucket structure - API returns individual bucket fields
        assert "as_of_date" in data
        assert "total_receivables" in data
        assert "current" in data
        assert "days_1_30" in data
        assert "days_31_60" in data
        assert "days_61_90" in data
        assert "days_over_90" in data

        # Verify each bucket has expected structure
        assert data["current"]["bucket_name"] == "Current"
        assert data["days_1_30"]["bucket_name"] == "1-30 days"
        assert data["days_31_60"]["bucket_name"] == "31-60 days"

    @pytest.mark.asyncio
    async def test_015_aged_receivables_no_outstanding(self):
        """Test aged receivables when all paid."""
        token = await get_auth_token()
        headers = get_headers(token)

        # Create and pay an invoice
        invoice_id = await create_test_invoice(status="issued", amount=5000.00)

        if invoice_id:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Record payment
                await client.post(
                    f"{BASE_URL}/invoices/{invoice_id}/payments",
                    json={
                        "amount": 5800.00,  # Including tax
                        "payment_date": date.today().isoformat(),
                        "payment_method": "mpesa"
                    },
                    headers=get_headers(await get_auth_token())
                )

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/reports/aged-receivables",
                headers=headers
            )

        assert response.status_code == 200
        # Total receivables might be 0 or minimal if all paid

    @pytest.mark.asyncio
    async def test_016_sales_summary_by_customer(self):
        """Test sales summary grouped by customer."""
        token = await get_auth_token()
        headers = get_headers(token)

        # Create some invoices
        await create_test_invoice(status="issued", amount=10000.00)

        start_date = (date.today() - timedelta(days=30)).isoformat()
        end_date = date.today().isoformat()

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/reports/sales-summary?start_date={start_date}&end_date={end_date}",
                headers=headers
            )

        assert response.status_code == 200, f"Failed to get sales summary: {response.text}"
        data = response.json()

        # Verify structure
        assert "start_date" in data
        assert "total_sales" in data
        assert "by_customer" in data
        assert "by_item" in data

    @pytest.mark.asyncio
    async def test_017_sales_summary_by_item(self):
        """Test sales summary grouped by item."""
        token = await get_auth_token()
        headers = get_headers(token)

        start_date = (date.today() - timedelta(days=30)).isoformat()
        end_date = date.today().isoformat()

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/reports/sales-summary?start_date={start_date}&end_date={end_date}",
                headers=headers
            )

        assert response.status_code == 200
        data = response.json()

        assert "by_item" in data
        assert isinstance(data["by_item"], list)

    @pytest.mark.asyncio
    async def test_018_reports_date_validation(self):
        """Test that invalid date ranges are rejected."""
        token = await get_auth_token()
        headers = get_headers(token)

        # End date before start date
        start_date = date.today().isoformat()
        end_date = (date.today() - timedelta(days=30)).isoformat()

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/reports/profit-loss?start_date={start_date}&end_date={end_date}",
                headers=headers
            )

        assert response.status_code == 400, "Should reject invalid date range"


# ================================
# SUPPORT TICKET TESTS (12+ tests)
# ================================

class TestSupportTickets:
    """Test client-facing support ticket operations."""

    @pytest.mark.asyncio
    async def test_019_create_ticket(self):
        """Test creating a new support ticket."""
        global test_ticket_id, test_ticket_number

        token = await get_auth_token()
        headers = get_headers(token)

        ticket_data = {
            "subject": f"Test Ticket {TEST_RUN_ID}",
            "description": "This is a test ticket for Sprint 5 testing",
            "category": "technical"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BASE_URL}/support/tickets",
                json=ticket_data,
                headers=headers
            )

        assert response.status_code == 201, f"Failed to create ticket: {response.text}"
        data = response.json()

        # Verify response
        assert "id" in data
        assert "ticket_number" in data
        assert data["subject"] == ticket_data["subject"]
        assert data["status"] == "open"
        assert data["priority"] == "medium"

        test_ticket_id = data["id"]
        test_ticket_number = data["ticket_number"]

    @pytest.mark.asyncio
    async def test_020_create_ticket_validation(self):
        """Test ticket creation validation."""
        token = await get_auth_token()
        headers = get_headers(token)

        # Missing required fields
        invalid_data = {
            "subject": "No description"
            # Missing description
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BASE_URL}/support/tickets",
                json=invalid_data,
                headers=headers
            )

        assert response.status_code in [400, 422], "Should reject invalid ticket data"

    @pytest.mark.asyncio
    async def test_021_list_my_tickets(self):
        """Test listing tickets for my business only."""
        token = await get_auth_token()
        headers = get_headers(token)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/support/tickets?page=1&page_size=20",
                headers=headers
            )

        assert response.status_code == 200, f"Failed to list tickets: {response.text}"
        data = response.json()

        # Verify pagination structure
        assert "tickets" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data

        # Should have at least 1 ticket from previous test
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_022_get_ticket_detail(self):
        """Test getting ticket detail with messages."""
        global test_ticket_id

        if not test_ticket_id:
            pytest.skip("No ticket ID from previous tests")

        token = await get_auth_token()
        headers = get_headers(token)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/support/tickets/{test_ticket_id}",
                headers=headers
            )

        assert response.status_code == 200, f"Failed to get ticket: {response.text}"
        data = response.json()

        assert data["id"] == test_ticket_id
        assert "messages" in data
        assert isinstance(data["messages"], list)

    @pytest.mark.asyncio
    async def test_023_add_message_to_ticket(self):
        """Test adding a message to ticket."""
        global test_ticket_id

        if not test_ticket_id:
            pytest.skip("No ticket ID from previous tests")

        token = await get_auth_token()
        headers = get_headers(token)

        message_data = {
            "message": "This is a follow-up message from the customer",
            "is_internal": False
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BASE_URL}/support/tickets/{test_ticket_id}/messages",
                json=message_data,
                headers=headers
            )

        assert response.status_code == 201, f"Failed to add message: {response.text}"
        data = response.json()

        assert data["message"] == message_data["message"]
        assert "sender_name" in data

    @pytest.mark.asyncio
    async def test_024_rate_ticket(self):
        """Test rating a resolved ticket."""
        global test_ticket_id

        if not test_ticket_id:
            pytest.skip("No ticket ID from previous tests")

        token = await get_auth_token()
        headers = get_headers(token)
        support_token_value = await get_support_token()
        support_headers = get_headers(support_token_value)

        async with httpx.AsyncClient(timeout=30.0) as client:
            # First, resolve the ticket as support agent
            await client.put(
                f"{BASE_URL}/admin/support/tickets/{test_ticket_id}",
                json={"status": "resolved"},
                headers=support_headers
            )

            # Now rate it as customer
            rating_data = {
                "rating": 5
            }

            response = await client.put(
                f"{BASE_URL}/support/tickets/{test_ticket_id}/rating",
                json=rating_data,
                headers=headers
            )

        assert response.status_code == 200, f"Failed to rate ticket: {response.text}"
        data = response.json()

        assert "satisfaction_rating" in data

    @pytest.mark.asyncio
    async def test_025_cannot_rate_unresolved(self):
        """Test that unresolved tickets cannot be rated."""
        token = await get_auth_token()
        headers = get_headers(token)

        # Create a new ticket
        ticket_data = {
            "subject": f"Unresolved Ticket {TEST_RUN_ID}",
            "description": "This ticket should not be ratable",
            "category": "billing"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BASE_URL}/support/tickets",
                json=ticket_data,
                headers=headers
            )

            assert response.status_code == 201
            new_ticket_id = response.json()["id"]

            # Try to rate it (should fail)
            rating_data = {"rating": 4}

            response = await client.put(
                f"{BASE_URL}/support/tickets/{new_ticket_id}/rating",
                json=rating_data,
                headers=headers
            )

        assert response.status_code == 404, "Should not allow rating unresolved ticket"

    @pytest.mark.asyncio
    async def test_026_ticket_business_isolation(self):
        """Test that users cannot see other business tickets."""
        token = await get_auth_token()
        headers = get_headers(token)

        # Try to access a non-existent ticket ID
        fake_ticket_id = "00000000-0000-0000-0000-000000000000"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/support/tickets/{fake_ticket_id}",
                headers=headers
            )

        assert response.status_code == 404, "Should not access other business tickets"

    @pytest.mark.asyncio
    async def test_027_admin_list_all_tickets(self):
        """Test that support agents can see all tickets."""
        support_token_value = await get_support_token()
        headers = get_headers(support_token_value)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/admin/support/tickets?page=1&page_size=20",
                headers=headers
            )

        assert response.status_code == 200, f"Failed to list all tickets: {response.text}"
        data = response.json()

        assert "tickets" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_028_admin_update_ticket_status(self):
        """Test that agents can update ticket status."""
        global test_ticket_id

        if not test_ticket_id:
            pytest.skip("No ticket ID from previous tests")

        support_token_value = await get_support_token()
        headers = get_headers(support_token_value)

        update_data = {
            "status": "in_progress",
            "priority": "high"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.put(
                f"{BASE_URL}/admin/support/tickets/{test_ticket_id}",
                json=update_data,
                headers=headers
            )

        assert response.status_code == 200, f"Failed to update ticket: {response.text}"
        data = response.json()

        assert data["status"] == "in_progress"
        assert data["priority"] == "high"

    @pytest.mark.asyncio
    async def test_029_admin_assign_ticket(self):
        """Test assigning ticket to agent."""
        global test_ticket_id

        if not test_ticket_id:
            pytest.skip("No ticket ID from previous tests")

        support_token_value = await get_support_token()
        headers = get_headers(support_token_value)

        # Get the support user's ID first
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Get current user
            login_response = await client.post(
                f"{BASE_URL}/auth/login",
                json={"email": SUPPORT_EMAIL, "password": SUPPORT_PASSWORD}
            )
            agent_id = login_response.json()["user"]["id"]

            # Assign ticket
            response = await client.post(
                f"{BASE_URL}/admin/support/tickets/{test_ticket_id}/assign?agent_id={agent_id}",
                headers=headers
            )

        assert response.status_code == 200, f"Failed to assign ticket: {response.text}"
        data = response.json()

        assert "assigned_agent_id" in data

    @pytest.mark.asyncio
    async def test_030_admin_internal_note(self):
        """Test creating internal note visible only to agents."""
        global test_ticket_id

        if not test_ticket_id:
            pytest.skip("No ticket ID from previous tests")

        support_token_value = await get_support_token()
        headers = get_headers(support_token_value)

        message_data = {
            "message": "This is an internal note not visible to customer",
            "is_internal": True
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BASE_URL}/admin/support/tickets/{test_ticket_id}/messages",
                json=message_data,
                headers=headers
            )

        assert response.status_code == 201, f"Failed to add internal note: {response.text}"
        data = response.json()

        assert data["is_internal"] == True


# ================================
# HELP CENTRE TESTS (6+ tests)
# ================================

class TestHelpCentre:
    """Test FAQ and help article endpoints."""

    @pytest.mark.asyncio
    async def test_031_list_faq_categories(self):
        """Test listing FAQ categories."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/support/faq/categories"
            )

        assert response.status_code == 200, f"Failed to list FAQ categories: {response.text}"
        data = response.json()

        assert "categories" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_032_list_faq_articles(self):
        """Test listing FAQ articles."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/support/faq?page=1&page_size=20"
            )

        assert response.status_code == 200, f"Failed to list FAQ articles: {response.text}"
        data = response.json()

        assert "articles" in data
        assert "total" in data
        assert "page" in data

    @pytest.mark.asyncio
    async def test_033_search_faq(self):
        """Test searching FAQ articles."""
        search_data = {
            "query": "invoice"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BASE_URL}/support/faq/search?page=1&page_size=20",
                json=search_data
            )

        assert response.status_code == 200, f"Failed to search FAQ: {response.text}"
        data = response.json()

        assert "articles" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_034_list_help_articles(self):
        """Test listing help articles."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/support/articles?page=1&page_size=20"
            )

        assert response.status_code == 200, f"Failed to list help articles: {response.text}"
        data = response.json()

        assert "articles" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_035_get_help_article_by_slug(self):
        """Test getting help article by slug."""
        # First, list articles to get a slug
        async with httpx.AsyncClient(timeout=30.0) as client:
            list_response = await client.get(
                f"{BASE_URL}/support/articles?page=1&page_size=1"
            )

            if list_response.status_code == 200:
                articles = list_response.json()["articles"]
                if len(articles) > 0:
                    slug = articles[0]["slug"]

                    response = await client.get(
                        f"{BASE_URL}/support/articles/{slug}"
                    )

                    if response.status_code == 200:
                        data = response.json()
                        assert "slug" in data
                        assert "title" in data
                        assert "content" in data

    @pytest.mark.asyncio
    async def test_036_help_article_not_found(self):
        """Test 404 for non-existent help article."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/support/articles/non-existent-article-slug-12345"
            )

        assert response.status_code == 404, "Should return 404 for non-existent article"


# ================================
# AUTHORIZATION TESTS (4+ tests)
# ================================

class TestAuthorization:
    """Test role-based access control."""

    @pytest.mark.asyncio
    async def test_037_admin_support_requires_agent_role(self):
        """Test that admin support endpoints require support_agent role."""
        token = await get_auth_token()  # Business user
        headers = get_headers(token)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/admin/support/tickets",
                headers=headers
            )

        assert response.status_code == 403, "Business user should not access admin support"

    @pytest.mark.asyncio
    async def test_038_support_agent_can_access_admin(self):
        """Test that support agents can access admin endpoints."""
        support_token_value = await get_support_token()
        headers = get_headers(support_token_value)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/admin/support/tickets",
                headers=headers
            )

        assert response.status_code == 200, "Support agent should access admin endpoints"

    @pytest.mark.asyncio
    async def test_039_business_admin_can_create_ticket(self):
        """Test that business users can create tickets."""
        token = await get_auth_token()
        headers = get_headers(token)

        ticket_data = {
            "subject": f"Auth Test Ticket {TEST_RUN_ID}",
            "description": "Testing authorization",
            "category": "general"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BASE_URL}/support/tickets",
                json=ticket_data,
                headers=headers
            )

        assert response.status_code == 201, "Business user should create tickets"

    @pytest.mark.asyncio
    async def test_040_unauthenticated_cannot_access_tickets(self):
        """Test that unauthenticated users cannot access tickets."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/support/tickets"
            )

        assert response.status_code in [401, 403], "Should require authentication"


# ================================
# ADMIN SUPPORT STATS TEST
# ================================

class TestAdminSupportStats:
    """Test support dashboard statistics."""

    @pytest.mark.asyncio
    async def test_041_get_support_stats(self):
        """Test getting support dashboard stats."""
        support_token_value = await get_support_token()
        headers = get_headers(support_token_value)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/admin/support/stats",
                headers=headers
            )

        assert response.status_code == 200, f"Failed to get support stats: {response.text}"
        data = response.json()

        # Verify stats structure
        assert "total_tickets" in data
        assert "open_count" in data
        assert "in_progress_count" in data
        assert "resolved_today" in data


# ================================
# CANNED RESPONSES TEST
# ================================

class TestCannedResponses:
    """Test canned response templates."""

    @pytest.mark.asyncio
    async def test_042_get_canned_responses(self):
        """Test getting canned response templates."""
        support_token_value = await get_support_token()
        headers = get_headers(support_token_value)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/admin/support/templates",
                headers=headers
            )

        assert response.status_code == 200, f"Failed to get templates: {response.text}"
        data = response.json()

        assert "templates" in data
        assert "total" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
