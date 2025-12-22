# Comprehensive Audit Logging Implementation

## Overview
This document provides a complete guide for the audit logging implementation across all services in the Kenya SMB Accounting MVP backend.

## Completed Services

### 1. Audit Service (`app/services/audit_service.py`) ✅
**Status**: Fully implemented

Core audit logging service with the following features:
- `log()` - Generic logging method
- `log_create()` - Log create operations
- `log_update()` - Log update operations with old/new values
- `log_delete()` - Log delete operations
- `log_view_sensitive()` - Log access to sensitive data (email, phone, KRA PIN)
- `log_workflow_transition()` - Log status transitions
- `log_bulk_operation()` - Log bulk operations
- `_sanitize_values()` - Remove sensitive fields from logs
- `cleanup_old_logs()` - Retention policy implementation
- `get_audit_logs()` - Query audit logs with filters

**Key Features**:
- Automatic sanitization of sensitive fields (passwords, tokens, encrypted fields)
- Supports old/new value tracking for updates
- IP address and user agent tracking
- Session tracking support
- JSON serialization for complex types

---

### 2. Invoice Service (`app/services/invoice_service.py`) ✅
**Status**: Fully implemented

**Audit Logging Added To**:
- `create_invoice()` - Logs invoice creation with invoice number, totals, status
- `update_invoice()` - Logs invoice updates with old/new values
- `issue_invoice()` - Logs workflow transition from draft to issued
- `cancel_invoice()` - Logs workflow transition to cancelled

**Parameters Added**: `user_id`, `ip_address` to all relevant methods

**Sample Logged Data**:
```python
# Create
new_values = {
    "invoice_number": "INV-2025-00001",
    "contact_id": "uuid",
    "status": "draft",
    "subtotal": 1000.00,
    "tax_amount": 160.00,
    "total_amount": 1160.00,
    "line_items_count": 3
}

# Issue (workflow transition)
details = {
    "old_status": "draft",
    "new_status": "issued",
    "invoice_number": "INV-2025-00001",
    "issue_date": "2025-12-09"
}
```

---

### 3. Contact Service (`app/services/contact_service.py`) ✅
**Status**: Fully implemented

**Audit Logging Added To**:
- `create_contact()` - Logs contact creation (WITHOUT sensitive data)
- `update_contact()` - Logs contact updates (WITHOUT sensitive data)
- `soft_delete_contact()` - Logs contact deletion
- `contact_to_response()` - Logs when sensitive fields are accessed (email, phone, kra_pin)

**Key Security Features**:
- Does NOT log plaintext email, phone, or KRA PIN
- Logs only presence of sensitive data (has_email, has_phone, has_kra_pin)
- Logs access to sensitive data when decrypting for display

**Sample Logged Data**:
```python
# Create/Update (no sensitive data)
new_values = {
    "name": "John Doe",
    "contact_type": "customer",
    "has_email": True,
    "has_phone": True,
    "has_kra_pin": True,
    "address": "Nairobi",
    "notes": "VIP customer"
}

# View Sensitive Data
action = "view_sensitive_data"
details = {
    "fields_accessed": ["email", "phone", "kra_pin"]
}
```

---

### 4. Item Service (`app/services/item_service.py`) ✅
**Status**: Fully implemented

**Audit Logging Added To**:
- `create_item()` - Logs item creation
- `update_item()` - Logs item updates with old/new values
- `soft_delete_item()` - Logs item deletion

**Parameters Added**: `user_id`, `ip_address` to all relevant methods

**Sample Logged Data**:
```python
new_values = {
    "name": "Premium Widget",
    "item_type": "product",
    "sku": "WIDGET-001",
    "unit_price": 1000.00,
    "tax_rate": 16.0,
    "description": "High quality widget"
}
```

---

### 5. Expense Service (`app/services/expense_service.py`) ✅
**Status**: Fully implemented

**Audit Logging Added To**:
- `create_expense()` - Logs expense creation
- `update_expense()` - Logs expense updates with old/new values
- `soft_delete_expense()` - Logs expense deletion

**Parameters Added**: `user_id`, `ip_address` to all relevant methods

**Sample Logged Data**:
```python
new_values = {
    "category": "office_supplies",
    "description": "Office furniture",
    "amount": 5000.00,
    "expense_date": "2025-12-09",
    "vendor_name": "Office Mart",
    "payment_method": "bank_transfer"
}
```

---

### 6. Payment Service (`app/services/payment_service.py`) ✅
**Status**: Fully implemented

**Audit Logging Added To**:
- `create_payment()` - Logs payment creation with invoice details
- `delete_payment()` - Logs payment deletion

**Parameters Added**: `user_id`, `ip_address` to relevant methods

**Sample Logged Data**:
```python
# Create
new_values = {
    "invoice_id": "uuid",
    "amount": 1160.00,
    "payment_date": "2025-12-09",
    "payment_method": "mpesa",
    "reference_number": "XYZ123456"
}
details = {
    "invoice_number": "INV-2025-00001"
}
```

---

## Services Requiring Completion

The following services need audit logging added. The pattern is consistent with the implemented services above.

### 7. Bank Import Service (`app/services/bank_import_service.py`)
**Status**: ⚠️ Needs Implementation

**Operations to Log**:
- `upload_statement()` - Log bank statement upload
  ```python
  await self.audit.log(
      action="upload_bank_statement",
      user_id=user_id,
      resource_type="bank_import",
      resource_id=import_record.id,
      details={
          "file_name": file_name,
          "statement_date": str(statement_date),
          "transactions_count": transaction_count
      },
      ip_address=ip_address
  )
  ```

- `process_import()` - Log processing start/completion
  ```python
  await self.audit.log(
      action="process_bank_import",
      user_id=user_id,
      resource_type="bank_import",
      resource_id=import_id,
      details={
          "status": "processed",
          "matched_count": matched_count,
          "unmatched_count": unmatched_count
      },
      ip_address=ip_address
  )
  ```

- `match_transaction()` - Log each transaction match
  ```python
  await self.audit.log(
      action="match_bank_transaction",
      user_id=user_id,
      resource_type="bank_transaction",
      resource_id=transaction_id,
      details={
          "matched_to": "expense" or "payment",
          "matched_id": str(matched_record_id),
          "amount": float(amount)
      },
      ip_address=ip_address
  )
  ```

- `unmatch_transaction()` - Log transaction unmatch
  ```python
  await self.audit.log(
      action="unmatch_bank_transaction",
      user_id=user_id,
      resource_type="bank_transaction",
      resource_id=transaction_id,
      details={
          "previously_matched_to": "expense" or "payment",
          "previously_matched_id": str(matched_record_id)
      },
      ip_address=ip_address
  )
  ```

**Implementation Steps**:
1. Add `self.audit = AuditService(db)` to `__init__`
2. Add `user_id` and `ip_address` parameters to relevant methods
3. Call audit logging methods after successful operations
4. Use `flush()` not `commit()` if the service method handles transaction

---

### 8. Tax Service (`app/services/tax_service.py`)
**Status**: ⚠️ Needs Implementation

**Operations to Log**:
- `update_tax_settings()` - Log tax settings changes
  ```python
  await self.audit.log_update(
      user_id=user_id,
      resource_type="tax_settings",
      resource_id=settings.id,
      old_values={
          "vat_rate": float(old_settings.vat_rate),
          "kra_pin": "[REDACTED]",  # Never log actual PIN
          "vat_registered": old_settings.vat_registered
      },
      new_values={
          "vat_rate": float(data.get("vat_rate", old_settings.vat_rate)),
          "vat_registered": data.get("vat_registered", old_settings.vat_registered)
      },
      ip_address=ip_address
  )
  ```

- `export_vat_return()` - Log VAT return export (sensitive data access)
  ```python
  await self.audit.log(
      action="export_vat_return",
      user_id=user_id,
      resource_type="tax_settings",
      resource_id=settings.id,
      details={
          "period_start": str(start_date),
          "period_end": str(end_date),
          "total_vat": float(total_vat),
          "export_format": "json"
      },
      ip_address=ip_address
  )
  ```

- `generate_etims_export()` - Log eTIMS export
  ```python
  await self.audit.log(
      action="generate_etims_export",
      user_id=user_id,
      resource_type="invoice",
      details={
          "invoice_count": len(invoices),
          "period_start": str(start_date),
          "period_end": str(end_date),
          "export_format": "etims_json"
      },
      ip_address=ip_address
  )
  ```

**Implementation Steps**:
1. Add `self.audit = AuditService(db)` to `__init__`
2. Add `user_id` and `ip_address` parameters
3. Log settings changes and exports
4. Mark VAT/eTIMS exports as sensitive data access

---

### 9. Support Service (`app/services/support_service.py`)
**Status**: ⚠️ Partial - Needs Enhancement

**Operations to Log** (if not already logged):
- `create_ticket()` - Log ticket creation
- `update_ticket()` - Log ticket updates
- `assign_ticket()` - Log ticket assignments
  ```python
  await self.audit.log(
      action="assign_ticket",
      user_id=user_id,
      resource_type="support_ticket",
      resource_id=ticket_id,
      details={
          "assigned_to": str(assignee_id),
          "old_assignee": str(old_assignee_id) if old_assignee_id else None
      },
      ip_address=ip_address
  )
  ```

- `add_message()` - Log message additions
  ```python
  await self.audit.log_create(
      user_id=user_id,
      resource_type="ticket_message",
      resource_id=message.id,
      new_values={
          "ticket_id": str(ticket_id),
          "message_preview": message.content[:100],  # First 100 chars
          "is_internal": message.is_internal
      },
      ip_address=ip_address
  )
  ```

- `change_ticket_status()` - Log status changes
  ```python
  await self.audit.log_workflow_transition(
      user_id=user_id,
      resource_type="support_ticket",
      resource_id=ticket_id,
      action="change_ticket_status",
      old_status=old_status,
      new_status=new_status,
      ip_address=ip_address
  )
  ```

**Implementation Steps**:
1. Review existing audit logging
2. Add any missing operations
3. Ensure all ticket lifecycle events are logged

---

### 10. Onboarding Service (`app/services/onboarding_service.py`)
**Status**: ⚠️ Needs Implementation

**Operations to Log**:
- `create_application()` - Log application submission
  ```python
  await self.audit.log_create(
      user_id=user_id,
      resource_type="business_application",
      resource_id=application.id,
      new_values={
          "business_name": data["business_name"],
          "email": "[REDACTED]",  # Don't log email
          "status": "pending",
          "business_type": data.get("business_type")
      },
      ip_address=ip_address
  )
  ```

- `update_application()` - Log application updates
  ```python
  await self.audit.log_update(
      user_id=user_id,
      resource_type="business_application",
      resource_id=application_id,
      old_values=old_values,
      new_values=new_values,
      ip_address=ip_address
  )
  ```

- `submit_application()` - Log submission workflow
  ```python
  await self.audit.log_workflow_transition(
      user_id=user_id,
      resource_type="business_application",
      resource_id=application_id,
      action="submit_application",
      old_status="draft",
      new_status="pending_review",
      ip_address=ip_address
  )
  ```

- `approve_application()` - Log approval and business creation
  ```python
  await self.audit.log_workflow_transition(
      user_id=admin_user_id,
      resource_type="business_application",
      resource_id=application_id,
      action="approve_application",
      old_status="pending_review",
      new_status="approved",
      ip_address=ip_address,
      details={
          "business_created": str(business.id),
          "user_created": str(user.id)
      }
  )
  ```

- `reject_application()` - Log rejection
  ```python
  await self.audit.log_workflow_transition(
      user_id=admin_user_id,
      resource_type="business_application",
      resource_id=application_id,
      action="reject_application",
      old_status="pending_review",
      new_status="rejected",
      ip_address=ip_address,
      details={
          "rejection_reason": reason
      }
  )
  ```

**Implementation Steps**:
1. Add `self.audit = AuditService(db)` to `__init__`
2. Add `user_id` and `ip_address` parameters
3. Log all application lifecycle events
4. Log business and user creation on approval

---

## API Endpoint Updates

All API endpoints need to be updated to extract and pass the IP address to services.

### Example Pattern:

```python
from fastapi import Request

@router.post("/")
async def create_invoice(
    invoice_data: InvoiceCreate,
    request: Request,  # Add Request parameter
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    # Extract IP address
    ip_address = request.client.host if request.client else None

    # Pass to service
    invoice_service = InvoiceService(db)
    invoice = await invoice_service.create_invoice(
        business_id=current_user.business_id,
        contact_id=invoice_data.contact_id,
        line_items_data=invoice_data.line_items,
        due_date=invoice_data.due_date,
        notes=invoice_data.notes,
        user_id=current_user.id,  # Pass user ID
        ip_address=ip_address      # Pass IP address
    )

    return invoice
```

### Endpoints to Update:
- `app/api/v1/endpoints/invoices.py`
- `app/api/v1/endpoints/contacts.py`
- `app/api/v1/endpoints/items.py`
- `app/api/v1/endpoints/expenses.py`
- `app/api/v1/endpoints/payments.py`
- `app/api/v1/endpoints/bank_imports.py`
- `app/api/v1/endpoints/tax.py`
- `app/api/v1/endpoints/support.py`
- `app/api/v1/endpoints/onboarding.py`

---

## Testing Audit Logs

### 1. Verify Audit Log Creation

```python
from app.services.audit_service import AuditService

async def test_audit_log_creation(db: AsyncSession):
    audit = AuditService(db)

    # Create a test log
    log = await audit.log_create(
        user_id=user_id,
        resource_type="test",
        resource_id=test_id,
        new_values={"test": "data"},
        ip_address="127.0.0.1"
    )

    assert log.action == "create_test"
    assert log.status == "success"
    assert log.new_values["test"] == "data"
```

### 2. Verify Sensitive Data Sanitization

```python
async def test_sensitive_data_sanitization(db: AsyncSession):
    audit = AuditService(db)

    # Try to log sensitive data
    log = await audit.log_create(
        user_id=user_id,
        resource_type="test",
        resource_id=test_id,
        new_values={
            "password": "secret123",
            "email_encrypted": "encrypted_value",
            "safe_field": "visible"
        }
    )

    # Verify sanitization
    assert log.new_values["password"] == "[REDACTED]"
    assert log.new_values["email_encrypted"] == "[REDACTED]"
    assert log.new_values["safe_field"] == "visible"
```

### 3. Query Audit Logs

```python
async def test_query_audit_logs(db: AsyncSession):
    audit = AuditService(db)

    # Query logs for specific user
    logs = await audit.get_audit_logs(
        user_id=user_id,
        resource_type="invoice",
        action="create_invoice",
        limit=10
    )

    assert len(logs) > 0
    assert logs[0].user_id == user_id
```

---

## Security Considerations

### 1. Sensitive Data Protection
- **NEVER** log plaintext passwords, tokens, or API keys
- **NEVER** log unencrypted personal data (email, phone, KRA PIN)
- Use `_sanitize_values()` for all logged data
- Log only presence of sensitive data, not the data itself

### 2. Access Control
- Audit log queries should be restricted to:
  - `system_admin` role
  - `support_agent` role
- Implement RLS (Row Level Security) in PostgreSQL for audit_logs table

### 3. Retention Policy
- Run `cleanup_old_logs()` via scheduled task (e.g., monthly)
- Default retention: 365 days
- Adjust based on compliance requirements

### 4. Audit Log Immutability
- Audit logs should **NEVER** be updated or deleted (except by retention policy)
- No UPDATE or DELETE endpoints for audit logs
- Only INSERT operations allowed

---

## Performance Considerations

### 1. Flush vs Commit
- Audit logging uses `flush()` instead of `commit()`
- This allows the calling service to control transaction boundaries
- Ensures audit logs persist even if outer transaction fails

### 2. Asynchronous Logging
- All audit logging is asynchronous
- Minimal performance impact on API operations
- Logs are flushed immediately to ensure persistence

### 3. Indexing
- Audit logs table has indexes on:
  - `user_id`
  - `resource_type` + `resource_id`
  - `action`
  - `created_at`
  - `ip_address` + `created_at`

---

## Compliance and Monitoring

### 1. Security Event Monitoring
Use `is_security_event` property to identify critical events:
```python
security_events = [
    log for log in audit_logs
    if log.is_security_event
]
```

### 2. Failed Operations Monitoring
Use `is_failure` property to identify errors:
```python
failed_operations = [
    log for log in audit_logs
    if log.is_failure
]
```

### 3. Data Modification Tracking
Use `is_data_modification` property:
```python
data_changes = [
    log for log in audit_logs
    if log.is_data_modification
]
```

---

## Summary

### Implemented ✅
- Audit Service (core functionality)
- Invoice Service (create, update, issue, cancel)
- Contact Service (create, update, delete, view sensitive data)
- Item Service (create, update, delete)
- Expense Service (create, update, delete)
- Payment Service (create, delete)

### Remaining ⚠️
- Bank Import Service (upload, process, match, unmatch)
- Tax Service (settings, exports, eTIMS)
- Support Service (enhance existing logging)
- Onboarding Service (application lifecycle)
- API Endpoint Updates (all endpoints)

### Next Steps
1. Complete remaining services (bank, tax, support, onboarding)
2. Update all API endpoints to pass `request` and extract IP
3. Test audit logging across all operations
4. Implement RLS for audit_logs table
5. Set up scheduled task for log retention
6. Create admin dashboard for audit log viewing

---

## File Locations

**Implemented Files**:
- `/mnt/c/Users/Dell/Desktop/Kenya-Accounting/backend/app/services/audit_service.py` ✅
- `/mnt/c/Users/Dell/Desktop/Kenya-Accounting/backend/app/services/invoice_service.py` ✅
- `/mnt/c/Users/Dell/Desktop/Kenya-Accounting/backend/app/services/contact_service.py` ✅
- `/mnt/c/Users/Dell/Desktop/Kenya-Accounting/backend/app/services/item_service.py` ✅
- `/mnt/c/Users/Dell/Desktop/Kenya-Accounting/backend/app/services/expense_service.py` ✅
- `/mnt/c/Users/Dell/Desktop/Kenya-Accounting/backend/app/services/payment_service.py` ✅

**Files Needing Updates**:
- `/mnt/c/Users/Dell/Desktop/Kenya-Accounting/backend/app/services/bank_import_service.py` ⚠️
- `/mnt/c/Users/Dell/Desktop/Kenya-Accounting/backend/app/services/tax_service.py` ⚠️
- `/mnt/c/Users/Dell/Desktop/Kenya-Accounting/backend/app/services/support_service.py` ⚠️
- `/mnt/c/Users/Dell/Desktop/Kenya-Accounting/backend/app/services/onboarding_service.py` ⚠️
- All API endpoint files in `/mnt/c/Users/Dell/Desktop/Kenya-Accounting/backend/app/api/v1/endpoints/` ⚠️

---

## Contact
For questions or issues with audit logging implementation, contact the senior backend developer for review.
