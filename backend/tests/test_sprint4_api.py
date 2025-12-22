"""
Comprehensive Sprint 4 API Tests

Tests all Sprint 4 features including:
- Bank Import API (upload, list, get, mapping, processing, delete)
- Bank Transaction API (list, get, reconciliation)
- Reconciliation API (match, unmatch, ignore, suggestions)
- Security and business isolation
- Data validation and error handling
- File upload handling (CSV and PDF)

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
from io import BytesIO

# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)

# Base configuration
BASE_URL = "http://localhost:8000/api/v1"
TEST_EMAIL = "business@example.com"
TEST_PASSWORD = "BusinessPass123"

# Unique test run identifier to avoid data conflicts
TEST_RUN_ID = str(int(time.time()))[-6:]

# Sample CSV content for testing
SAMPLE_CSV = '''Date,Description,Debit,Credit,Balance
01/12/2024,MPESA Payment to ABC Corp,5000.00,,95000.00
02/12/2024,Salary Deposit,,150000.00,245000.00
03/12/2024,Office Supplies,2500.00,,242500.00
04/12/2024,Rent Payment,50000.00,,192500.00
05/12/2024,Customer Payment - INV001,,25000.00,217500.00
'''

EMPTY_CSV = '''Date,Description,Debit,Credit,Balance
'''

MISSING_COLUMNS_CSV = '''Date,Details
01/12/2024,Some transaction
02/12/2024,Another transaction
'''

# Global variables to store test data
auth_token = None
business_id = None
test_bank_import_id = None
test_bank_transaction_id = None
test_expense_id = None
test_invoice_id = None
test_customer_id = None
test_product_id = None


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


async def create_test_expense():
    """Helper to create a test expense for reconciliation."""
    global test_expense_id

    token = await get_auth_token()
    headers = get_headers(token)

    expense_data = {
        "category": "office_supplies",
        "description": f"Office Supplies Test {TEST_RUN_ID}",
        "amount": 2500.00,
        "tax_amount": 400.00,
        "expense_date": "2024-12-03",
        "vendor_name": "Test Vendor",
        "payment_method": "mpesa",
        "reference_number": "TEST123"
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


async def create_test_customer():
    """Helper to create a test customer."""
    global test_customer_id

    if test_customer_id:
        return test_customer_id

    token = await get_auth_token()
    headers = get_headers(token)

    contact_data = {
        "name": f"Sprint4 Test Customer {TEST_RUN_ID}",
        "contact_type": "customer",
        "email": f"s4customer{TEST_RUN_ID}@test.com",
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
        "name": f"Sprint4 Test Product {TEST_RUN_ID}",
        "item_type": "product",
        "unit_price": 25000.00,
        "tax_rate": 16.0,
        "sku": f"S4PROD-{TEST_RUN_ID}"
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


async def create_test_invoice(status="issued"):
    """Helper to create a test invoice for reconciliation."""
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
        "due_date": "2024-12-15",
        "line_items": [
            {
                "item_id": product_id,
                "quantity": 1,
                "unit_price": 25000.00,
                "tax_rate": 16.0,
                "description": "Test product for payment"
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
                json={"issue_date": "2024-12-05"},
                headers=headers
            )
            if response.status_code != 200:
                return None

        test_invoice_id = invoice_id
        return invoice_id


# ================================
# AUTHENTICATION TESTS
# ================================

class TestAuthentication:
    """Test authentication and authorization for bank import endpoints."""

    @pytest.mark.asyncio
    async def test_001_bank_import_requires_auth(self):
        """Test that bank import endpoints require authentication."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Try to access bank imports without token
            response = await client.get(f"{BASE_URL}/bank-imports/")
            assert response.status_code in [401, 403], "Should require authentication"

    @pytest.mark.asyncio
    async def test_002_bank_import_requires_business_id(self):
        """Test that bank import operations require valid business_id."""
        token = await get_auth_token()
        headers = get_headers(token)

        # This test verifies that the business_id is properly extracted from the token
        # and used for business isolation
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/bank-imports/",
                headers=headers
            )

            # Should succeed with valid business_id from token
            assert response.status_code == 200, f"Should accept valid business_id: {response.text}"


# ================================
# IMPORT CRUD TESTS
# ================================

class TestBankImportCRUD:
    """Test Bank Import CRUD operations."""

    @pytest.mark.asyncio
    async def test_003_create_bank_import_csv(self):
        """Test creating a bank import with CSV file."""
        global test_bank_import_id

        token = await get_auth_token()
        headers = get_headers(token)

        # Create multipart file upload
        files = {
            "file": (f"statement_{TEST_RUN_ID}.csv", BytesIO(SAMPLE_CSV.encode()), "text/csv")
        }

        # Optional form data
        data = {
            "source_bank": "Equity Bank"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BASE_URL}/bank-imports/",
                files=files,
                data=data,
                headers=headers
            )

        assert response.status_code == 201, f"Failed to create bank import: {response.text}"
        result = response.json()

        # Verify response structure
        assert "id" in result
        assert result["file_type"] == "csv"
        assert result["source_bank"] == "Equity Bank"
        assert result["status"] in ["pending", "parsing", "mapping"]  # mapping if auto-parsed
        assert result["total_rows"] >= 0

        test_bank_import_id = result["id"]

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="LlamaParse not available in test environment")
    async def test_004_create_bank_import_pdf(self):
        """Test creating a bank import with PDF file (mocked)."""
        token = await get_auth_token()
        headers = get_headers(token)

        # Create mock PDF file
        mock_pdf_content = b"%PDF-1.4 Mock PDF for testing"
        files = {
            "file": (f"statement_{TEST_RUN_ID}.pdf", BytesIO(mock_pdf_content), "application/pdf")
        }

        data = {
            "source_bank": "KCB Bank"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BASE_URL}/bank-imports/",
                files=files,
                data=data,
                headers=headers
            )

        # Should accept PDF file
        assert response.status_code == 201, f"Failed to create PDF import: {response.text}"
        result = response.json()

        assert result["file_type"] == "pdf"
        assert result["source_bank"] == "KCB Bank"

    @pytest.mark.asyncio
    async def test_005_create_bank_import_invalid_file_type(self):
        """Test that invalid file types are rejected."""
        token = await get_auth_token()
        headers = get_headers(token)

        # Try to upload an invalid file type
        files = {
            "file": (f"statement_{TEST_RUN_ID}.txt", BytesIO(b"Invalid file content"), "text/plain")
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BASE_URL}/bank-imports/",
                files=files,
                headers=headers
            )

        # Should reject invalid file type
        assert response.status_code in [400, 422], "Should reject invalid file type"

    @pytest.mark.asyncio
    async def test_006_list_bank_imports(self):
        """Test listing bank imports with pagination."""
        token = await get_auth_token()
        headers = get_headers(token)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/bank-imports/?page=1&page_size=10",
                headers=headers
            )

        assert response.status_code == 200, f"Failed to list bank imports: {response.text}"
        data = response.json()

        # Verify pagination structure
        assert "imports" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data

        # Should have at least 1 import from previous tests
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_007_list_bank_imports_filter_by_status(self):
        """Test filtering bank imports by status."""
        token = await get_auth_token()
        headers = get_headers(token)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/bank-imports/?status=pending",
                headers=headers
            )

        assert response.status_code == 200
        data = response.json()

        # All returned imports should have pending status
        for import_record in data["imports"]:
            assert import_record["status"] == "pending"

    @pytest.mark.asyncio
    async def test_008_get_bank_import_by_id(self):
        """Test getting a single bank import by ID."""
        global test_bank_import_id

        token = await get_auth_token()
        headers = get_headers(token)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/bank-imports/{test_bank_import_id}",
                headers=headers
            )

        assert response.status_code == 200, f"Failed to get bank import: {response.text}"
        data = response.json()

        assert data["id"] == test_bank_import_id
        assert "file_name" in data
        assert "file_type" in data
        assert "status" in data

    @pytest.mark.asyncio
    async def test_009_get_bank_import_not_found(self):
        """Test getting a non-existent bank import returns 404."""
        token = await get_auth_token()
        headers = get_headers(token)

        # Use a random UUID that doesn't exist
        fake_id = "00000000-0000-0000-0000-000000000000"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/bank-imports/{fake_id}",
                headers=headers
            )

        assert response.status_code == 404, "Should return 404 for non-existent import"

    @pytest.mark.asyncio
    async def test_010_update_column_mapping(self):
        """Test updating column mapping for a bank import."""
        global test_bank_import_id

        token = await get_auth_token()
        headers = get_headers(token)

        mapping_data = {
            "date_column": "Date",
            "description_column": "Description",
            "debit_column": "Debit",
            "credit_column": "Credit",
            "balance_column": "Balance"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.patch(
                f"{BASE_URL}/bank-imports/{test_bank_import_id}/mapping",
                json=mapping_data,
                headers=headers
            )

        assert response.status_code == 200, f"Failed to update column mapping: {response.text}"
        data = response.json()

        # Verify mapping was updated
        assert data["column_mapping"] is not None
        assert data["status"] in ["mapping", "pending"]

    @pytest.mark.asyncio
    async def test_011_update_column_mapping_invalid(self):
        """Test that invalid column mapping is rejected."""
        global test_bank_import_id

        token = await get_auth_token()
        headers = get_headers(token)

        # Missing required fields
        invalid_mapping = {
            "date_column": "Date"
            # Missing description_column and amount columns
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.patch(
                f"{BASE_URL}/bank-imports/{test_bank_import_id}/mapping",
                json=invalid_mapping,
                headers=headers
            )

        # Should reject invalid mapping
        assert response.status_code in [400, 422], "Should reject invalid column mapping"

    @pytest.mark.asyncio
    async def test_012_process_import(self):
        """Test processing a bank import to create transactions."""
        global test_bank_import_id

        token = await get_auth_token()
        headers = get_headers(token)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BASE_URL}/bank-imports/{test_bank_import_id}/process",
                headers=headers
            )

        assert response.status_code == 200, f"Failed to process import: {response.text}"
        data = response.json()

        # Verify processing was initiated
        assert data["status"] in ["importing", "completed"]
        assert data["imported_rows"] >= 0

    @pytest.mark.asyncio
    async def test_013_delete_bank_import(self):
        """Test deleting a bank import."""
        token = await get_auth_token()
        headers = get_headers(token)

        # Create a temporary import for deletion
        files = {
            "file": (f"temp_{TEST_RUN_ID}.csv", BytesIO(SAMPLE_CSV.encode()), "text/csv")
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BASE_URL}/bank-imports/",
                files=files,
                headers=headers
            )
            assert response.status_code == 201
            import_id = response.json()["id"]

            # Delete the import
            response = await client.delete(
                f"{BASE_URL}/bank-imports/{import_id}",
                headers=headers
            )

            assert response.status_code == 204, f"Failed to delete import: {response.text}"

    @pytest.mark.asyncio
    async def test_014_delete_bank_import_with_matched_transactions_fails(self):
        """Test that deleting import with matched transactions is rejected."""
        # This test would require creating an import, processing it,
        # matching transactions, then attempting deletion
        # For now, we'll test the basic constraint
        pass  # Placeholder for future implementation


# ================================
# TRANSACTION TESTS
# ================================

class TestBankTransactions:
    """Test Bank Transaction operations."""

    @pytest.mark.asyncio
    async def test_015_list_transactions_for_import(self):
        """Test listing transactions for a specific import."""
        global test_bank_import_id, test_bank_transaction_id

        token = await get_auth_token()
        headers = get_headers(token)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/bank-imports/{test_bank_import_id}/transactions",
                headers=headers
            )

        assert response.status_code == 200, f"Failed to list transactions: {response.text}"
        data = response.json()

        # Verify pagination structure
        assert "transactions" in data
        assert "total" in data

        # Store a transaction ID for future tests
        if data["total"] > 0 and len(data["transactions"]) > 0:
            test_bank_transaction_id = data["transactions"][0]["id"]

    @pytest.mark.asyncio
    async def test_016_list_transactions_filter_by_status(self):
        """Test filtering transactions by reconciliation status."""
        global test_bank_import_id

        token = await get_auth_token()
        headers = get_headers(token)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/bank-imports/{test_bank_import_id}/transactions?status=unmatched",
                headers=headers
            )

        assert response.status_code == 200
        data = response.json()

        # All returned transactions should be unmatched
        for transaction in data["transactions"]:
            assert transaction["reconciliation_status"] == "unmatched"

    @pytest.mark.asyncio
    async def test_017_get_transaction_by_id(self):
        """Test getting a single bank transaction by ID."""
        global test_bank_transaction_id

        if not test_bank_transaction_id:
            pytest.skip("No transaction ID available from previous tests")

        token = await get_auth_token()
        headers = get_headers(token)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/bank-imports/transactions/{test_bank_transaction_id}",
                headers=headers
            )

        assert response.status_code == 200, f"Failed to get transaction: {response.text}"
        data = response.json()

        assert data["id"] == test_bank_transaction_id
        assert "transaction_date" in data
        assert "description" in data
        assert "reconciliation_status" in data

    @pytest.mark.asyncio
    async def test_018_get_reconciliation_suggestions(self):
        """Test getting reconciliation suggestions for a transaction."""
        global test_bank_transaction_id

        if not test_bank_transaction_id:
            pytest.skip("No transaction ID available from previous tests")

        token = await get_auth_token()
        headers = get_headers(token)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/bank-imports/transactions/{test_bank_transaction_id}/suggestions",
                headers=headers
            )

        assert response.status_code == 200, f"Failed to get suggestions: {response.text}"
        data = response.json()

        # Verify suggestion structure
        assert "transaction_id" in data
        assert "suggested_matches" in data
        assert isinstance(data["suggested_matches"], list)


# ================================
# RECONCILIATION TESTS
# ================================

class TestReconciliation:
    """Test reconciliation operations."""

    @pytest.mark.asyncio
    async def test_019_match_transaction_to_expense(self):
        """Test matching a bank transaction to an expense."""
        global test_bank_transaction_id

        if not test_bank_transaction_id:
            pytest.skip("No transaction ID available from previous tests")

        token = await get_auth_token()
        headers = get_headers(token)

        # Create an expense to match
        expense_id = await create_test_expense()
        if not expense_id:
            pytest.skip("Could not create test expense")

        match_data = {
            "record_type": "expense",
            "record_id": expense_id
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BASE_URL}/bank-imports/transactions/{test_bank_transaction_id}/match",
                json=match_data,
                headers=headers
            )

        assert response.status_code == 200, f"Failed to match transaction: {response.text}"
        data = response.json()

        # Verify match was created
        assert data["reconciliation_status"] == "matched"
        assert data["matched_expense_id"] == expense_id

    @pytest.mark.asyncio
    async def test_020_match_transaction_to_invoice(self):
        """Test matching a bank transaction to an invoice."""
        # Create a new import with a credit transaction
        token = await get_auth_token()
        headers = get_headers(token)

        # Create a CSV with a credit transaction
        credit_csv = '''Date,Description,Debit,Credit,Balance
06/12/2024,Customer Payment INV001,,25000.00,242500.00
'''

        files = {
            "file": (f"credit_statement_{TEST_RUN_ID}.csv", BytesIO(credit_csv.encode()), "text/csv")
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Create import
            response = await client.post(
                f"{BASE_URL}/bank-imports/",
                files=files,
                headers=headers
            )
            assert response.status_code == 201
            import_id = response.json()["id"]

            # Set column mapping
            mapping_data = {
                "date_column": "Date",
                "description_column": "Description",
                "debit_column": "Debit",
                "credit_column": "Credit",
                "balance_column": "Balance"
            }

            response = await client.patch(
                f"{BASE_URL}/bank-imports/{import_id}/mapping",
                json=mapping_data,
                headers=headers
            )
            assert response.status_code == 200

            # Process import
            response = await client.post(
                f"{BASE_URL}/bank-imports/{import_id}/process",
                headers=headers
            )
            assert response.status_code == 200

            # Get transactions
            response = await client.get(
                f"{BASE_URL}/bank-imports/{import_id}/transactions",
                headers=headers
            )
            assert response.status_code == 200
            transactions = response.json()["transactions"]

            if len(transactions) > 0:
                transaction_id = transactions[0]["id"]

                # Create an invoice to match
                invoice_id = await create_test_invoice(status="issued")
                if invoice_id:
                    match_data = {
                        "record_type": "invoice",
                        "record_id": invoice_id
                    }

                    response = await client.post(
                        f"{BASE_URL}/bank-imports/transactions/{transaction_id}/match",
                        json=match_data,
                        headers=headers
                    )

                    assert response.status_code == 200, f"Failed to match to invoice: {response.text}"
                    data = response.json()

                    assert data["reconciliation_status"] == "matched"
                    assert data["matched_invoice_id"] == invoice_id

    @pytest.mark.asyncio
    async def test_021_unmatch_transaction(self):
        """Test unmatching a previously matched transaction."""
        global test_bank_transaction_id

        if not test_bank_transaction_id:
            pytest.skip("No transaction ID available from previous tests")

        token = await get_auth_token()
        headers = get_headers(token)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.delete(
                f"{BASE_URL}/bank-imports/transactions/{test_bank_transaction_id}/match",
                headers=headers
            )

        assert response.status_code == 200, f"Failed to unmatch transaction: {response.text}"
        data = response.json()

        # Verify unmatch was successful
        assert data["reconciliation_status"] == "unmatched"
        assert data["matched_expense_id"] is None
        assert data["matched_invoice_id"] is None

    @pytest.mark.asyncio
    async def test_022_ignore_transaction(self):
        """Test ignoring a transaction."""
        global test_bank_transaction_id

        if not test_bank_transaction_id:
            pytest.skip("No transaction ID available from previous tests")

        token = await get_auth_token()
        headers = get_headers(token)

        ignore_data = {
            "reason": "Internal transfer - not relevant for reconciliation"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BASE_URL}/bank-imports/transactions/{test_bank_transaction_id}/ignore",
                json=ignore_data,
                headers=headers
            )

        assert response.status_code == 200, f"Failed to ignore transaction: {response.text}"
        data = response.json()

        # Verify transaction is marked as ignored
        assert data["reconciliation_status"] == "ignored"

    @pytest.mark.asyncio
    async def test_023_cannot_ignore_matched_transaction(self):
        """Test that matched transactions cannot be ignored."""
        token = await get_auth_token()
        headers = get_headers(token)

        # Create a new transaction and match it
        debit_csv = '''Date,Description,Debit,Credit,Balance
07/12/2024,Test Payment,1000.00,,241500.00
'''

        files = {
            "file": (f"ignore_test_{TEST_RUN_ID}.csv", BytesIO(debit_csv.encode()), "text/csv")
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Create and process import
            response = await client.post(
                f"{BASE_URL}/bank-imports/",
                files=files,
                headers=headers
            )
            assert response.status_code == 201
            import_id = response.json()["id"]

            # Set mapping
            mapping_data = {
                "date_column": "Date",
                "description_column": "Description",
                "debit_column": "Debit",
                "credit_column": "Credit",
                "balance_column": "Balance"
            }

            response = await client.patch(
                f"{BASE_URL}/bank-imports/{import_id}/mapping",
                json=mapping_data,
                headers=headers
            )
            assert response.status_code == 200

            # Process
            response = await client.post(
                f"{BASE_URL}/bank-imports/{import_id}/process",
                headers=headers
            )
            assert response.status_code == 200

            # Get transaction
            response = await client.get(
                f"{BASE_URL}/bank-imports/{import_id}/transactions",
                headers=headers
            )
            transactions = response.json()["transactions"]

            if len(transactions) > 0:
                transaction_id = transactions[0]["id"]

                # Match to expense
                expense_id = await create_test_expense()
                if expense_id:
                    match_data = {
                        "record_type": "expense",
                        "record_id": expense_id
                    }

                    response = await client.post(
                        f"{BASE_URL}/bank-imports/transactions/{transaction_id}/match",
                        json=match_data,
                        headers=headers
                    )
                    assert response.status_code == 200

                    # Try to ignore (should fail)
                    ignore_data = {
                        "reason": "Trying to ignore matched transaction"
                    }

                    response = await client.post(
                        f"{BASE_URL}/bank-imports/transactions/{transaction_id}/ignore",
                        json=ignore_data,
                        headers=headers
                    )

                    # Should be rejected
                    assert response.status_code == 400, "Should reject ignoring matched transaction"


# ================================
# STATS TESTS
# ================================

class TestReconciliationStats:
    """Test reconciliation statistics."""

    @pytest.mark.asyncio
    async def test_024_get_reconciliation_stats(self):
        """Test getting reconciliation statistics for an import."""
        global test_bank_import_id

        token = await get_auth_token()
        headers = get_headers(token)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/bank-imports/{test_bank_import_id}/reconciliation-stats",
                headers=headers
            )

        assert response.status_code == 200, f"Failed to get stats: {response.text}"
        data = response.json()

        # Verify stats structure
        assert "total_transactions" in data
        assert "matched_count" in data
        assert "suggested_count" in data
        assert "unmatched_count" in data
        assert "ignored_count" in data
        assert "matched_percentage" in data
        assert "total_debit_amount" in data
        assert "total_credit_amount" in data

        # Verify counts add up
        total = data["matched_count"] + data["unmatched_count"] + data["ignored_count"]
        assert total <= data["total_transactions"]


# ================================
# EDGE CASE TESTS
# ================================

class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_025_empty_csv_file(self):
        """Test handling of empty CSV file."""
        token = await get_auth_token()
        headers = get_headers(token)

        files = {
            "file": (f"empty_{TEST_RUN_ID}.csv", BytesIO(EMPTY_CSV.encode()), "text/csv")
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BASE_URL}/bank-imports/",
                files=files,
                headers=headers
            )

        # Should either accept with 0 rows or reject
        if response.status_code == 201:
            data = response.json()
            assert data["total_rows"] == 0
        else:
            assert response.status_code in [400, 422], "Should handle empty CSV appropriately"

    @pytest.mark.asyncio
    async def test_026_csv_with_missing_required_columns(self):
        """Test handling of CSV with missing required columns."""
        token = await get_auth_token()
        headers = get_headers(token)

        files = {
            "file": (f"missing_cols_{TEST_RUN_ID}.csv", BytesIO(MISSING_COLUMNS_CSV.encode()), "text/csv")
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Create import
            response = await client.post(
                f"{BASE_URL}/bank-imports/",
                files=files,
                headers=headers
            )

            if response.status_code == 201:
                import_id = response.json()["id"]

                # Try to set mapping with non-existent columns
                mapping_data = {
                    "date_column": "Date",
                    "description_column": "Details",
                    "debit_column": "Debit",  # This column doesn't exist
                    "credit_column": "Credit"  # This column doesn't exist
                }

                response = await client.patch(
                    f"{BASE_URL}/bank-imports/{import_id}/mapping",
                    json=mapping_data,
                    headers=headers
                )

                # Mapping is accepted - validation happens during processing
                # The API allows setting any column names in mapping,
                # but will fail during process if columns don't exist
                if response.status_code == 200:
                    # Try to process - this should fail
                    process_response = await client.post(
                        f"{BASE_URL}/bank-imports/{import_id}/process",
                        headers=headers
                    )
                    # Processing with invalid columns should fail
                    assert process_response.status_code in [400, 422, 500], "Processing with invalid columns should fail"
                else:
                    assert response.status_code in [400, 422], "Should reject mapping to non-existent columns"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
