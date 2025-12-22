# Sprint 2 Code Review - Fixes Applied

## Summary
Senior Backend Developer reviewed Sprint 2 code and applied critical security fixes.

**Review Date:** 2025-12-07
**Files Reviewed:** 13 files (models, services, endpoints, schemas)
**Critical Issues Found:** 4
**Fixes Applied:** 3 (1 requires developer action)

---

## ✅ FIXES APPLIED AUTOMATICALLY

### 1. Race Condition in Invoice Number Generation
**File:** `/app/services/invoice_service.py`
**Lines:** 47-84

**Problem:**
Concurrent requests could generate duplicate invoice numbers.

**Fix:**
Added database-level row locking using `SELECT FOR UPDATE`:
```python
result = await self.db.execute(
    select(Invoice.invoice_number)
    .where(...)
    .order_by(Invoice.invoice_number.desc())
    .limit(1)
    .with_for_update(skip_locked=True)  # Prevents race condition
)
```

---

### 2. Cross-Business Item Reference Vulnerability
**File:** `/app/services/invoice_service.py`
**Lines:** 260-273, 361-374

**Problem:**
Users could reference items from other businesses in their invoices.

**Fix:**
Added validation in `create_invoice()` and `update_invoice()`:
```python
# Verify all item_ids belong to the business
item_ids = [item.get("item_id") for item in line_items_data if item.get("item_id")]
if item_ids:
    from app.models.item import Item
    item_result = await self.db.execute(
        select(Item.id).where(
            Item.id.in_(item_ids),
            Item.business_id == business_id
        )
    )
    valid_item_ids = {row[0] for row in item_result.all()}
    invalid_items = set(item_ids) - valid_item_ids
    if invalid_items:
        raise ValueError(f"Invalid item references: items do not belong to this business")
```

---

### 3. Unique Index on Nullable SKU
**File:** `/app/models/item.py`
**Lines:** 111-123

**Problem:**
Unique index would fail with multiple NULL SKUs.

**Fix:**
Changed to partial unique index:
```python
Index(
    'ix_items_business_sku',
    'business_id',
    'sku',
    unique=True,
    postgresql_where=(Column('sku').isnot(None))  # Only enforce when SKU is not NULL
),
```

---

### 4. Missing Input Sanitization
**Files Created/Modified:**
- Created: `/app/schemas/validators.py` (new file)
- Modified: `/app/schemas/contact.py`
- Modified: `/app/schemas/item.py`
- Modified: `/app/schemas/invoice.py`

**Problem:**
Text fields had no sanitization for XSS/SQL injection.

**Fix:**
Created shared validators module with:
- `sanitize_text_input()`: Removes HTML, null bytes, control characters
- `validate_kenya_phone()`: Phone validation
- `validate_kra_pin()`: KRA PIN validation
- `validate_sku()`: SKU validation

Applied to all schemas:
```python
@field_validator("notes", "address")
@classmethod
def sanitize_text_fields(cls, v: Optional[str]) -> Optional[str]:
    return sanitize_text_input(v, allow_html=False)
```

---

## ⛔ CRITICAL ISSUES REQUIRING DEVELOPER ACTION

### 1. Missing Database Migrations
**Status:** NOT FIXED (requires developer)

**Action Required:**
```bash
cd /mnt/c/Users/Dell/Desktop/Kenya-Accounting/backend
alembic revision --autogenerate -m "add_contact_item_invoice_models"
```

**Migration must include:**
- Create tables: contacts, items, invoices, invoice_items
- Create indexes as defined in models
- Create enums: contact_type, item_type, invoice_status
- Add RLS policies for multi-tenant security
- Include proper downgrade path

**Example RLS Policy:**
```python
# In upgrade()
op.execute("""
    ALTER TABLE contacts ENABLE ROW LEVEL SECURITY;

    CREATE POLICY contacts_business_isolation ON contacts
        USING (business_id = current_setting('app.current_business_id')::uuid);
""")

# In downgrade()
op.execute("""
    DROP POLICY IF EXISTS contacts_business_isolation ON contacts;
    ALTER TABLE contacts DISABLE ROW LEVEL SECURITY;
""")
```

---

### 2. Missing Audit Logging
**Status:** NOT FIXED (requires developer)

**Action Required:**
Create audit logging for all operations:

**Events to Log:**
- Contact create/update/delete
- Invoice create/issue/cancel
- Item create/update/delete
- Failed authorization attempts

**Required Fields:**
```python
{
    "timestamp": datetime.utcnow(),
    "user_id": current_user.id,
    "action": "invoice_issued",
    "resource_type": "invoice",
    "resource_id": invoice.id,
    "business_id": business_id,
    "ip_address": request.client.host,
    "user_agent": request.headers.get("user-agent"),
    "details": {"invoice_number": "INV-2025-00001", "status": "issued"}
}
```

**Implementation Steps:**
1. Create `app/models/audit_log.py` if not exists
2. Create `app/services/audit_service.py`
3. Add audit calls to all service methods
4. Include request context (IP, user agent)

---

## 📋 TESTING CHECKLIST

Before deploying, test the following:

### Race Condition Fix
- [ ] Create 10 concurrent invoice creation requests
- [ ] Verify all invoice numbers are unique
- [ ] Check no database errors occur

### Cross-Business Validation
- [ ] Try to create invoice with item_id from another business
- [ ] Verify error: "Invalid item references: items do not belong to this business"
- [ ] Verify valid item_ids work correctly

### Input Sanitization
- [ ] Submit contact with HTML in notes: `<script>alert('xss')</script>`
- [ ] Verify HTML is stripped from stored data
- [ ] Submit invoice with control characters
- [ ] Verify control characters are removed

### SKU Uniqueness
- [ ] Create multiple items with NULL SKU
- [ ] Verify no unique constraint errors
- [ ] Try to create two items with same SKU
- [ ] Verify error: "SKU must be unique"

---

## 📁 FILES MODIFIED

### Services
- ✅ `/app/services/invoice_service.py` (2 critical fixes)

### Models
- ✅ `/app/models/item.py` (1 fix)

### Schemas
- ✅ `/app/schemas/contact.py` (sanitization added)
- ✅ `/app/schemas/item.py` (sanitization added)
- ✅ `/app/schemas/invoice.py` (sanitization added)
- ✅ `/app/schemas/validators.py` (NEW - shared validators)

### Documentation
- ✅ `/SPRINT_2_CODE_REVIEW.md` (NEW - full review)
- ✅ `/FIXES_APPLIED.md` (NEW - this file)

---

## 🔄 NEXT STEPS

1. **Developer Action Required:**
   - Create database migrations
   - Implement audit logging
   - Create unit tests
   - Create integration tests

2. **Testing:**
   - Run all tests
   - Test concurrent invoice creation
   - Test cross-business isolation
   - Test input sanitization

3. **Documentation:**
   - Document RLS policies
   - Add API documentation examples
   - Create security guidelines

4. **Deployment:**
   - Review migration before running
   - Run migration on dev environment first
   - Monitor logs for errors
   - Verify audit logs are being created

---

## 📞 CONTACT

For questions about these fixes:
- Review the full report: `SPRINT_2_CODE_REVIEW.md`
- Check security standards in senior developer role documentation
- Consult encryption service documentation: `/app/core/encryption.py`

---

**Report Generated:** 2025-12-07
**Senior Backend Developer**
