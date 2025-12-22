# Sprint 2 API Usage Examples

## Authentication
All endpoints require a JWT token. Obtain token from the auth endpoint:

```bash
# Login to get token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "YourPassword123!"
  }'

# Response:
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer",
  "user": { ... }
}

# Use token in subsequent requests
export TOKEN="eyJhbGc..."
```

---

## Contacts API Examples

### Create a Customer Contact
```bash
curl -X POST http://localhost:8000/api/v1/contacts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Acme Corporation",
    "contact_type": "customer",
    "email": "billing@acme.co.ke",
    "phone": "+254712345678",
    "kra_pin": "A012345678X",
    "address": "123 Kenyatta Avenue, Nairobi",
    "notes": "Preferred payment: M-PESA"
  }'

# Response:
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "business_id": "123e4567-e89b-12d3-a456-426614174001",
  "name": "Acme Corporation",
  "contact_type": "customer",
  "email": "billing@acme.co.ke",  # Decrypted for response
  "phone": "+254712345678",  # Decrypted
  "kra_pin": "A012345678X",  # Decrypted
  "address": "123 Kenyatta Avenue, Nairobi",
  "notes": "Preferred payment: M-PESA",
  "is_active": true,
  "created_at": "2025-12-07T10:30:00Z",
  "updated_at": "2025-12-07T10:30:00Z"
}
```

### List Contacts with Filtering
```bash
# All customers, paginated
curl "http://localhost:8000/api/v1/contacts?contact_type=customer&page=1&page_size=20" \
  -H "Authorization: Bearer $TOKEN"

# Search by name
curl "http://localhost:8000/api/v1/contacts?search=Acme" \
  -H "Authorization: Bearer $TOKEN"

# Only active suppliers
curl "http://localhost:8000/api/v1/contacts?contact_type=supplier&is_active=true" \
  -H "Authorization: Bearer $TOKEN"

# Response:
{
  "contacts": [ ... ],
  "total": 45,
  "page": 1,
  "page_size": 20,
  "total_pages": 3
}
```

### Update Contact
```bash
curl -X PUT http://localhost:8000/api/v1/contacts/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+254722334455",
    "notes": "Updated payment method to bank transfer"
  }'
```

### Soft Delete Contact
```bash
curl -X DELETE http://localhost:8000/api/v1/contacts/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer $TOKEN"

# Returns: 204 No Content
```

---

## Items/Services API Examples

### Create a Service Item
```bash
curl -X POST http://localhost:8000/api/v1/items \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Web Development Services",
    "item_type": "service",
    "description": "Custom website development and design",
    "sku": "WEB-DEV-001",
    "unit_price": 50000.00,
    "tax_rate": 16.0
  }'

# Response:
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "business_id": "123e4567-e89b-12d3-a456-426614174001",
  "name": "Web Development Services",
  "item_type": "service",
  "description": "Custom website development and design",
  "sku": "WEB-DEV-001",
  "unit_price": "50000.00",
  "tax_rate": "16.00",
  "is_active": true,
  "created_at": "2025-12-07T11:00:00Z",
  "updated_at": "2025-12-07T11:00:00Z"
}
```

### Create a Product Item
```bash
curl -X POST http://localhost:8000/api/v1/items \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Premium Coffee Beans",
    "item_type": "product",
    "description": "Arabica beans from Mt. Kenya",
    "sku": "COFFEE-ARB-250G",
    "unit_price": 1200.00,
    "tax_rate": 16.0
  }'
```

### List Items with Search
```bash
# Search by name or SKU
curl "http://localhost:8000/api/v1/items?search=coffee" \
  -H "Authorization: Bearer $TOKEN"

# Filter by type
curl "http://localhost:8000/api/v1/items?item_type=service" \
  -H "Authorization: Bearer $TOKEN"

# Response:
{
  "items": [ ... ],
  "total": 12,
  "page": 1,
  "page_size": 50,
  "total_pages": 1
}
```

### Update Item Price
```bash
curl -X PUT http://localhost:8000/api/v1/items/660e8400-e29b-41d4-a716-446655440001 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "unit_price": 55000.00
  }'
```

---

## Invoices API Examples

### Create Invoice (Draft)
```bash
curl -X POST http://localhost:8000/api/v1/invoices \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "contact_id": "550e8400-e29b-41d4-a716-446655440000",
    "due_date": "2025-01-31",
    "notes": "Payment terms: Net 30 days",
    "line_items": [
      {
        "item_id": "660e8400-e29b-41d4-a716-446655440001",
        "description": "Web Development Services - Homepage",
        "quantity": 1,
        "unit_price": 50000.00,
        "tax_rate": 16.0
      },
      {
        "description": "Additional pages (5 pages)",
        "quantity": 5,
        "unit_price": 5000.00,
        "tax_rate": 16.0
      }
    ]
  }'

# Response:
{
  "id": "770e8400-e29b-41d4-a716-446655440002",
  "business_id": "123e4567-e89b-12d3-a456-426614174001",
  "contact_id": "550e8400-e29b-41d4-a716-446655440000",
  "invoice_number": "INV-2025-00001",  # Auto-generated
  "status": "draft",
  "issue_date": null,
  "due_date": "2025-01-31",
  "subtotal": "75000.00",  # Auto-calculated
  "tax_amount": "12000.00",  # Auto-calculated
  "total_amount": "87000.00",  # Auto-calculated
  "notes": "Payment terms: Net 30 days",
  "created_at": "2025-12-07T11:30:00Z",
  "updated_at": "2025-12-07T11:30:00Z",
  "line_items": [
    {
      "id": "880e8400-e29b-41d4-a716-446655440003",
      "invoice_id": "770e8400-e29b-41d4-a716-446655440002",
      "item_id": "660e8400-e29b-41d4-a716-446655440001",
      "description": "Web Development Services - Homepage",
      "quantity": "1.00",
      "unit_price": "50000.00",
      "tax_rate": "16.00",
      "line_total": "58000.00",
      "created_at": "2025-12-07T11:30:00Z"
    },
    {
      "id": "990e8400-e29b-41d4-a716-446655440004",
      "invoice_id": "770e8400-e29b-41d4-a716-446655440002",
      "item_id": null,
      "description": "Additional pages (5 pages)",
      "quantity": "5.00",
      "unit_price": "5000.00",
      "tax_rate": "16.00",
      "line_total": "29000.00",
      "created_at": "2025-12-07T11:30:00Z"
    }
  ]
}
```

### Update Invoice (Draft Only)
```bash
# Update line items
curl -X PUT http://localhost:8000/api/v1/invoices/770e8400-e29b-41d4-a716-446655440002 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "due_date": "2025-02-15",
    "line_items": [
      {
        "description": "Web Development Services - Full Package",
        "quantity": 1,
        "unit_price": 75000.00,
        "tax_rate": 16.0
      }
    ]
  }'

# Note: This only works if status is "draft"
# Attempting to update issued/paid invoices returns 400 error
```

### Issue Invoice (Lock for Payment)
```bash
curl -X POST http://localhost:8000/api/v1/invoices/770e8400-e29b-41d4-a716-446655440002/issue \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "issue_date": "2025-12-07"
  }'

# Response:
{
  "id": "770e8400-e29b-41d4-a716-446655440002",
  "invoice_number": "INV-2025-00001",
  "status": "issued",  # Changed from "draft"
  "issue_date": "2025-12-07",  # Set when issued
  "due_date": "2025-01-31",
  "total_amount": "87000.00",
  ...
}

# Invoice is now locked - cannot be edited
```

### List Invoices with Filters
```bash
# All issued invoices
curl "http://localhost:8000/api/v1/invoices?status=issued" \
  -H "Authorization: Bearer $TOKEN"

# Invoices for specific customer
curl "http://localhost:8000/api/v1/invoices?contact_id=550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer $TOKEN"

# Date range filter
curl "http://localhost:8000/api/v1/invoices?start_date=2025-01-01&end_date=2025-12-31" \
  -H "Authorization: Bearer $TOKEN"

# Combine filters
curl "http://localhost:8000/api/v1/invoices?status=paid&start_date=2025-01-01&page=1&page_size=20" \
  -H "Authorization: Bearer $TOKEN"

# Response:
{
  "invoices": [ ... ],
  "total": 156,
  "page": 1,
  "page_size": 20,
  "total_pages": 8
}
```

### Get Invoice with Line Items
```bash
curl http://localhost:8000/api/v1/invoices/770e8400-e29b-41d4-a716-446655440002 \
  -H "Authorization: Bearer $TOKEN"

# Returns full invoice with nested line_items array
```

### Cancel Invoice
```bash
curl -X POST http://localhost:8000/api/v1/invoices/770e8400-e29b-41d4-a716-446655440002/cancel \
  -H "Authorization: Bearer $TOKEN"

# Response:
{
  "id": "770e8400-e29b-41d4-a716-446655440002",
  "invoice_number": "INV-2025-00001",
  "status": "cancelled",  # Terminal state
  ...
}

# Cancelled invoices cannot be edited or issued
```

### Generate PDF (Placeholder)
```bash
curl http://localhost:8000/api/v1/invoices/770e8400-e29b-41d4-a716-446655440002/pdf \
  -H "Authorization: Bearer $TOKEN"

# Response (currently returns JSON, PDF generation to be implemented):
{
  "invoice_id": "770e8400-e29b-41d4-a716-446655440002",
  "invoice_number": "INV-2025-00001",
  "pdf_url": null,
  "invoice_data": {
    # Full invoice details with line items
  }
}
```

---

## Status Workflow Examples

### Valid Transitions
```bash
# 1. Create invoice (draft)
POST /api/v1/invoices
# status: "draft"

# 2. Issue invoice
POST /api/v1/invoices/{id}/issue
# draft → issued

# 3. Mark as paid (future: via Payments API)
# issued → paid (terminal)

# Alternative: Cancel anytime before paid
POST /api/v1/invoices/{id}/cancel
# draft/issued/overdue → cancelled (terminal)
```

### Invalid Transitions (Return 400 Error)
```bash
# Cannot edit issued invoice
PUT /api/v1/invoices/{id}
# Error: "Invoice with status 'issued' cannot be edited"

# Cannot issue paid invoice
POST /api/v1/invoices/{id}/issue
# Error: "Cannot issue invoice with status 'paid'. Only draft invoices can be issued."

# Cannot cancel paid invoice
POST /api/v1/invoices/{id}/cancel
# Error: "Cannot cancel invoice with status 'paid'."
```

---

## Error Handling Examples

### 400 Bad Request
```bash
# Missing required field
curl -X POST http://localhost:8000/api/v1/contacts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "contact_type": "customer"
  }'

# Response:
{
  "detail": [
    {
      "loc": ["body", "name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### 401 Unauthorized
```bash
# Missing or invalid token
curl http://localhost:8000/api/v1/contacts

# Response:
{
  "detail": "Not authenticated"
}
```

### 403 Forbidden
```bash
# User without business_id
{
  "detail": "User must be associated with a business"
}
```

### 404 Not Found
```bash
# Resource doesn't exist or belongs to different business
curl http://localhost:8000/api/v1/contacts/invalid-uuid-here \
  -H "Authorization: Bearer $TOKEN"

# Response:
{
  "detail": "Contact not found"
}
```

### 422 Validation Error
```bash
# Invalid phone format
curl -X POST http://localhost:8000/api/v1/contacts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Contact",
    "contact_type": "customer",
    "phone": "12345"
  }'

# Response:
{
  "detail": [
    {
      "loc": ["body", "phone"],
      "msg": "Invalid Kenya phone number format",
      "type": "value_error"
    }
  ]
}
```

---

## Pagination Examples

### Standard Pagination
```bash
# Page 1, 20 items per page
curl "http://localhost:8000/api/v1/contacts?page=1&page_size=20" \
  -H "Authorization: Bearer $TOKEN"

# Response:
{
  "contacts": [ ... ],  # 20 items
  "total": 156,
  "page": 1,
  "page_size": 20,
  "total_pages": 8
}

# Page 2
curl "http://localhost:8000/api/v1/contacts?page=2&page_size=20" \
  -H "Authorization: Bearer $TOKEN"

# Response:
{
  "contacts": [ ... ],  # Items 21-40
  "total": 156,
  "page": 2,
  "page_size": 20,
  "total_pages": 8
}
```

### Custom Page Size
```bash
# Get 100 items per page
curl "http://localhost:8000/api/v1/items?page=1&page_size=100" \
  -H "Authorization: Bearer $TOKEN"

# Maximum: 100 items per page
```

---

## Testing with Python

### Using requests library
```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# Login
response = requests.post(
    f"{BASE_URL}/auth/login",
    json={"email": "admin@example.com", "password": "Password123!"}
)
token = response.json()["access_token"]

headers = {"Authorization": f"Bearer {token}"}

# Create contact
contact_data = {
    "name": "Test Customer",
    "contact_type": "customer",
    "email": "test@example.com",
    "phone": "+254712345678"
}
response = requests.post(f"{BASE_URL}/contacts", json=contact_data, headers=headers)
contact = response.json()
print(f"Created contact: {contact['id']}")

# Create item
item_data = {
    "name": "Test Service",
    "item_type": "service",
    "unit_price": 1000.00,
    "tax_rate": 16.0
}
response = requests.post(f"{BASE_URL}/items", json=item_data, headers=headers)
item = response.json()
print(f"Created item: {item['id']}")

# Create invoice
invoice_data = {
    "contact_id": contact["id"],
    "due_date": "2025-01-31",
    "line_items": [
        {
            "item_id": item["id"],
            "description": "Test Service",
            "quantity": 5,
            "unit_price": 1000.00,
            "tax_rate": 16.0
        }
    ]
}
response = requests.post(f"{BASE_URL}/invoices", json=invoice_data, headers=headers)
invoice = response.json()
print(f"Created invoice: {invoice['invoice_number']}")
print(f"Total amount: KES {invoice['total_amount']}")

# Issue invoice
response = requests.post(
    f"{BASE_URL}/invoices/{invoice['id']}/issue",
    json={},
    headers=headers
)
issued_invoice = response.json()
print(f"Issued invoice, status: {issued_invoice['status']}")
```

---

## Quick Start Guide

1. **Setup Environment**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or: venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

2. **Run Migrations**
   ```bash
   psql -h <supabase-host> -U postgres -d postgres -f migrations/sprint2_create_tables.sql
   ```

3. **Start Server**
   ```bash
   uvicorn app.main:app --reload
   ```

4. **Access API Docs**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

5. **Test Endpoints**
   - Use examples above with curl or Python
   - Or use the interactive Swagger UI
