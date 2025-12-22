# Payment Recording API - Quick Start Guide

## Overview
The Payment Recording API allows you to record payments against invoices and automatically updates invoice status based on payment totals.

## Base URL
```
/api/v1/payments
```

## Authentication
All endpoints require authentication. Include JWT token in Authorization header:
```
Authorization: Bearer <your-jwt-token>
```

---

## API Endpoints

### 1. Create Payment

**Endpoint**: `POST /payments/`

**Description**: Record a new payment against an invoice. Invoice status is automatically updated.

**Request Body**:
```json
{
  "invoice_id": "uuid-of-invoice",
  "amount": 5000.00,
  "payment_date": "2025-01-15",
  "payment_method": "mpesa",
  "reference_number": "QRT12345678",
  "notes": "Payment via M-Pesa"
}
```

**Payment Methods**:
- `cash`
- `bank_transfer`
- `mpesa`
- `card`
- `cheque`
- `other`

**Response** (201 Created):
```json
{
  "id": "payment-uuid",
  "business_id": "business-uuid",
  "invoice_id": "invoice-uuid",
  "amount": 5000.00,
  "payment_date": "2025-01-15",
  "payment_method": "mpesa",
  "reference_number": "QRT12345678",
  "notes": "Payment via M-Pesa",
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z"
}
```

**Validations**:
- Amount must be positive
- Amount cannot exceed invoice balance due
- Cannot add payment to cancelled invoices
- Payment date cannot be in the future

---

### 2. List All Payments

**Endpoint**: `GET /payments/`

**Description**: Get paginated list of payments with optional filters.

**Query Parameters**:
- `page` (default: 1) - Page number
- `page_size` (default: 50, max: 100) - Items per page
- `invoice_id` (optional) - Filter by invoice
- `start_date` (optional) - Filter by payment_date >= start_date
- `end_date` (optional) - Filter by payment_date <= end_date
- `payment_method` (optional) - Filter by payment method

**Example**:
```
GET /payments/?page=1&page_size=20&start_date=2025-01-01&end_date=2025-01-31&payment_method=mpesa
```

**Response** (200 OK):
```json
{
  "payments": [
    {
      "id": "payment-uuid",
      "business_id": "business-uuid",
      "invoice_id": "invoice-uuid",
      "amount": 5000.00,
      "payment_date": "2025-01-15",
      "payment_method": "mpesa",
      "reference_number": "QRT12345678",
      "notes": "Payment via M-Pesa",
      "created_at": "2025-01-15T10:30:00Z",
      "updated_at": "2025-01-15T10:30:00Z"
    }
  ],
  "total": 45,
  "page": 1,
  "page_size": 20,
  "total_pages": 3
}
```

---

### 3. Get Single Payment

**Endpoint**: `GET /payments/{payment_id}`

**Description**: Get details of a specific payment.

**Example**:
```
GET /payments/123e4567-e89b-12d3-a456-426614174000
```

**Response** (200 OK):
```json
{
  "id": "payment-uuid",
  "business_id": "business-uuid",
  "invoice_id": "invoice-uuid",
  "amount": 5000.00,
  "payment_date": "2025-01-15",
  "payment_method": "mpesa",
  "reference_number": "QRT12345678",
  "notes": "Payment via M-Pesa",
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z"
}
```

---

### 4. Delete Payment

**Endpoint**: `DELETE /payments/{payment_id}`

**Description**: Delete a payment. Invoice status is automatically recalculated.

**Example**:
```
DELETE /payments/123e4567-e89b-12d3-a456-426614174000
```

**Response** (204 No Content):
No response body.

**Note**: Deleting a payment will recalculate the invoice status. If this was the only payment, the invoice may revert to "issued" status.

---

### 5. List Payments for Invoice

**Endpoint**: `GET /payments/invoice/{invoice_id}/payments`

**Description**: Get all payments for a specific invoice, ordered chronologically.

**Example**:
```
GET /payments/invoice/123e4567-e89b-12d3-a456-426614174000/payments
```

**Response** (200 OK):
```json
[
  {
    "id": "payment-uuid-1",
    "business_id": "business-uuid",
    "invoice_id": "invoice-uuid",
    "amount": 3000.00,
    "payment_date": "2025-01-10",
    "payment_method": "bank_transfer",
    "reference_number": "TRX123",
    "notes": "First payment",
    "created_at": "2025-01-10T09:00:00Z",
    "updated_at": "2025-01-10T09:00:00Z"
  },
  {
    "id": "payment-uuid-2",
    "business_id": "business-uuid",
    "invoice_id": "invoice-uuid",
    "amount": 2000.00,
    "payment_date": "2025-01-15",
    "payment_method": "mpesa",
    "reference_number": "QRT12345678",
    "notes": "Second payment",
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-01-15T10:30:00Z"
  }
]
```

---

### 6. Get Payment Summary for Invoice

**Endpoint**: `GET /payments/invoice/{invoice_id}/summary`

**Description**: Get payment summary showing total paid, balance due, etc.

**Example**:
```
GET /payments/invoice/123e4567-e89b-12d3-a456-426614174000/summary
```

**Response** (200 OK):
```json
{
  "total_payments": 2,
  "total_amount_paid": 5000.00,
  "invoice_total": 11600.00,
  "balance_due": 6600.00
}
```

---

## Invoice Status Workflow

When payments are created or deleted, invoice status is automatically updated:

### Status Transitions

```
draft
  ↓ (invoice issued)
issued
  ↓ (partial payment)
partially_paid
  ↓ (remaining payment)
paid ✓
```

### Status Rules

1. **Paid**: `total_paid >= total_amount`
   - Invoice is fully paid
   - Terminal state
   - Cannot add more payments if overpaid

2. **Partially Paid**: `0 < total_paid < total_amount`
   - Some payment received
   - More payments can be added
   - Balance due = total_amount - total_paid

3. **Issued**: `total_paid = 0`
   - No payments yet
   - Can receive payments
   - If payments deleted, reverts to issued

4. **Cancelled**:
   - Cannot add payments
   - Cannot change status via payments

---

## Common Use Cases

### 1. Record Full Payment
```bash
curl -X POST /api/v1/payments/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "invoice_id": "invoice-uuid",
    "amount": 11600.00,
    "payment_date": "2025-01-15",
    "payment_method": "bank_transfer",
    "reference_number": "TRX123456",
    "notes": "Full payment received"
  }'
```

Result: Invoice status → "paid"

---

### 2. Record Partial Payment
```bash
curl -X POST /api/v1/payments/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "invoice_id": "invoice-uuid",
    "amount": 5000.00,
    "payment_date": "2025-01-10",
    "payment_method": "mpesa",
    "reference_number": "QRT12345678"
  }'
```

Result: Invoice status → "partially_paid"

---

### 3. Check Payment Status
```bash
curl -X GET /api/v1/payments/invoice/{invoice_id}/summary \
  -H "Authorization: Bearer <token>"
```

Response shows:
- How much has been paid
- How much is still owed
- Number of payments received

---

### 4. List M-Pesa Payments for Month
```bash
curl -X GET "/api/v1/payments/?payment_method=mpesa&start_date=2025-01-01&end_date=2025-01-31" \
  -H "Authorization: Bearer <token>"
```

---

### 5. Correct Payment Entry Error
```bash
# Delete incorrect payment
curl -X DELETE /api/v1/payments/{payment_id} \
  -H "Authorization: Bearer <token>"

# Create correct payment
curl -X POST /api/v1/payments/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "invoice_id": "invoice-uuid",
    "amount": 5500.00,
    "payment_date": "2025-01-15",
    "payment_method": "mpesa",
    "reference_number": "QRT87654321",
    "notes": "Corrected payment entry"
  }'
```

---

## Error Handling

### Common Errors

**400 Bad Request** - Validation Error
```json
{
  "detail": "Payment amount (15000.00) exceeds invoice balance due (11600.00)"
}
```

**403 Forbidden** - No Business Association
```json
{
  "detail": "User must be associated with a business"
}
```

**404 Not Found** - Payment or Invoice Not Found
```json
{
  "detail": "Payment not found"
}
```

**404 Not Found** - Invoice Not Found
```json
{
  "detail": "Invoice not found or does not belong to this business"
}
```

**400 Bad Request** - Cannot Add Payment to Cancelled Invoice
```json
{
  "detail": "Cannot add payment to cancelled invoice"
}
```

**400 Bad Request** - Payment Date in Future
```json
{
  "detail": "Payment date cannot be in the future"
}
```

---

## Business Rules

### Payment Creation
1. Amount must be positive (> 0)
2. Amount cannot exceed invoice balance due
3. Payment date cannot be in the future
4. Cannot add payment to cancelled invoices
5. Invoice must belong to the same business

### Payment Deletion
1. Deletes payment record
2. Recalculates invoice.amount_paid
3. Updates invoice status based on new total
4. If last payment deleted, invoice reverts to "issued"

### Invoice Status Update (Automatic)
1. Triggered on payment create/delete
2. Calculates total from all payments
3. Updates invoice.amount_paid
4. Updates invoice.status based on rules
5. Cannot update cancelled invoices

---

## Best Practices

1. **Reference Numbers**: Always include reference numbers for bank transfers, M-Pesa, cheques
   - M-Pesa: Use transaction code (e.g., QRT12345678)
   - Bank Transfer: Use transaction reference
   - Cheque: Use cheque number

2. **Payment Date**: Use the actual date payment was received, not today's date

3. **Notes**: Add context for future reference
   - Who paid
   - Any special circumstances
   - Payment arrangements

4. **Error Handling**: Check balance due before creating payment to avoid validation errors

5. **Reconciliation**: Use payment summary endpoint to verify totals match

6. **Deletions**: Use with caution - consider adding corrective payment instead

---

## Integration Examples

### JavaScript/TypeScript
```typescript
// Create payment
const createPayment = async (invoiceId: string, paymentData: PaymentCreate) => {
  const response = await fetch('/api/v1/payments/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      invoice_id: invoiceId,
      ...paymentData
    })
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail);
  }

  return await response.json();
};

// Get payment summary
const getPaymentSummary = async (invoiceId: string) => {
  const response = await fetch(`/api/v1/payments/invoice/${invoiceId}/summary`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  return await response.json();
};
```

### Python
```python
import requests

# Create payment
def create_payment(invoice_id: str, amount: float, payment_method: str, token: str):
    response = requests.post(
        'http://api.example.com/api/v1/payments/',
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        },
        json={
            'invoice_id': invoice_id,
            'amount': amount,
            'payment_date': '2025-01-15',
            'payment_method': payment_method,
            'reference_number': 'TRX123456'
        }
    )
    response.raise_for_status()
    return response.json()

# Get payment summary
def get_payment_summary(invoice_id: str, token: str):
    response = requests.get(
        f'http://api.example.com/api/v1/payments/invoice/{invoice_id}/summary',
        headers={'Authorization': f'Bearer {token}'}
    )
    response.raise_for_status()
    return response.json()
```

---

## Testing the API

### Using curl

```bash
# Set your token
export TOKEN="your-jwt-token-here"

# Create payment
curl -X POST http://localhost:8000/api/v1/payments/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "invoice_id": "invoice-uuid",
    "amount": 5000.00,
    "payment_date": "2025-01-15",
    "payment_method": "mpesa",
    "reference_number": "QRT12345678"
  }'

# List payments
curl -X GET "http://localhost:8000/api/v1/payments/?page=1&page_size=10" \
  -H "Authorization: Bearer $TOKEN"

# Get payment summary
curl -X GET "http://localhost:8000/api/v1/payments/invoice/{invoice-uuid}/summary" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Next Steps

1. Review the [Implementation Summary](SPRINT3_PAYMENT_API_IMPLEMENTATION.md) for technical details
2. Run the database migration: `migrations/003_add_payments_table.sql`
3. Test the endpoints using the examples above
4. Integrate with your frontend application
5. Review audit logging requirements
6. Consider adding payment reconciliation features

---

## Support

For questions or issues:
1. Check the implementation summary document
2. Review the source code comments
3. Contact the senior backend developer for review
4. Refer to the main project README for setup instructions
