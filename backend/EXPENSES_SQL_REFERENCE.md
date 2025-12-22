# Expenses API - SQL Migration Reference

## Quick Migration Guide

### File Location
`/mnt/c/Users/Dell/Desktop/Kenya-Accounting/backend/migrations/003_create_expenses_tables.sql`

---

## Tables Created

### 1. expense_categories

```sql
CREATE TABLE expense_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID REFERENCES businesses(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_system BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT expense_categories_name_business_unique UNIQUE (business_id, name)
);
```

**Indexes**:
- `ix_expense_categories_id` - Primary key index
- `ix_expense_categories_business` - (business_id, is_active)
- `ix_expense_categories_system` - (is_system, is_active)
- `ix_expense_categories_name` - (name)
- `ix_expense_categories_created_at` - (created_at)

---

### 2. expenses

```sql
CREATE TABLE expenses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    category VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    amount DECIMAL(15, 2) NOT NULL CHECK (amount > 0),
    tax_amount DECIMAL(15, 2) NOT NULL DEFAULT 0.00 CHECK (tax_amount >= 0),
    expense_date DATE NOT NULL,
    vendor_name VARCHAR(200),
    receipt_url VARCHAR(500),
    payment_method VARCHAR(50) NOT NULL,
    reference_number VARCHAR(100),
    is_reconciled BOOLEAN NOT NULL DEFAULT FALSE,
    notes TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

**Indexes**:
- `ix_expenses_id` - Primary key index
- `ix_expenses_business_id` - (business_id)
- `ix_expenses_category` - (category)
- `ix_expenses_expense_date` - (expense_date)
- `ix_expenses_vendor_name` - (vendor_name)
- `ix_expenses_payment_method` - (payment_method)
- `ix_expenses_is_reconciled` - (is_reconciled)
- `ix_expenses_is_active` - (is_active)
- `ix_expenses_created_at` - (created_at)

**Composite Indexes**:
- `ix_expenses_business_date` - (business_id, expense_date)
- `ix_expenses_business_category` - (business_id, category)
- `ix_expenses_business_vendor` - (business_id, vendor_name)
- `ix_expenses_business_reconciled` - (business_id, is_reconciled)
- `ix_expenses_business_active` - (business_id, is_active)
- `ix_expenses_date_range` - (business_id, expense_date, category)

---

## System Categories Inserted

14 Kenya-relevant expense categories are automatically inserted:

1. Office Supplies
2. Travel & Transport
3. Utilities
4. Rent
5. Salaries & Wages
6. Professional Services
7. Marketing & Advertising
8. Bank Charges
9. **M-Pesa Charges** (Kenya-specific)
10. Insurance
11. Maintenance & Repairs
12. Licenses & Permits
13. Training & Development
14. Other

---

## Row Level Security (RLS)

### expense_categories Policies

```sql
-- Users can view system categories and their business categories
CREATE POLICY expense_categories_select_policy ON expense_categories
    FOR SELECT USING (
        is_system = TRUE OR
        business_id IN (SELECT business_id FROM users WHERE id = auth.uid())
    );

-- Users can insert custom categories for their business
CREATE POLICY expense_categories_insert_policy ON expense_categories
    FOR INSERT WITH CHECK (
        business_id IN (SELECT business_id FROM users WHERE id = auth.uid())
        AND is_system = FALSE
    );

-- Users can update their business categories (not system categories)
CREATE POLICY expense_categories_update_policy ON expense_categories
    FOR UPDATE USING (
        business_id IN (SELECT business_id FROM users WHERE id = auth.uid())
        AND is_system = FALSE
    );

-- Users can delete their business categories (not system categories)
CREATE POLICY expense_categories_delete_policy ON expense_categories
    FOR DELETE USING (
        business_id IN (SELECT business_id FROM users WHERE id = auth.uid())
        AND is_system = FALSE
    );
```

### expenses Policies

```sql
-- All operations scoped to user's business
CREATE POLICY expenses_select_policy ON expenses
    FOR SELECT USING (
        business_id IN (SELECT business_id FROM users WHERE id = auth.uid())
    );

CREATE POLICY expenses_insert_policy ON expenses
    FOR INSERT WITH CHECK (
        business_id IN (SELECT business_id FROM users WHERE id = auth.uid())
    );

CREATE POLICY expenses_update_policy ON expenses
    FOR UPDATE USING (
        business_id IN (SELECT business_id FROM users WHERE id = auth.uid())
    );

CREATE POLICY expenses_delete_policy ON expenses
    FOR DELETE USING (
        business_id IN (SELECT business_id FROM users WHERE id = auth.uid())
    );
```

---

## Triggers

### Auto-update updated_at timestamp

```sql
-- For expense_categories
CREATE OR REPLACE FUNCTION update_expense_categories_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_expense_categories_updated_at
    BEFORE UPDATE ON expense_categories
    FOR EACH ROW
    EXECUTE FUNCTION update_expense_categories_updated_at();

-- For expenses
CREATE OR REPLACE FUNCTION update_expenses_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_expenses_updated_at
    BEFORE UPDATE ON expenses
    FOR EACH ROW
    EXECUTE FUNCTION update_expenses_updated_at();
```

---

## How to Apply Migration

### Method 1: Using psql

```bash
# Replace <SUPABASE_HOST> with your Supabase database host
# Replace <PASSWORD> with your database password

psql "postgresql://postgres:<PASSWORD>@<SUPABASE_HOST>:5432/postgres" \
  -f migrations/003_create_expenses_tables.sql
```

### Method 2: Using Supabase Dashboard

1. Go to your Supabase project
2. Navigate to **SQL Editor**
3. Click **New Query**
4. Copy and paste the contents of `migrations/003_create_expenses_tables.sql`
5. Click **Run** or press `Ctrl+Enter`

### Method 3: Using Supabase CLI

```bash
# If you have Supabase CLI installed
supabase db execute -f migrations/003_create_expenses_tables.sql
```

---

## Verification Queries

### Check if tables were created

```sql
SELECT table_name, table_type
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN ('expenses', 'expense_categories');
```

**Expected Output**: 2 rows

---

### Check system categories

```sql
SELECT id, name, is_system, is_active
FROM expense_categories
WHERE is_system = TRUE
ORDER BY name;
```

**Expected Output**: 14 rows

---

### Check RLS is enabled

```sql
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
  AND tablename IN ('expenses', 'expense_categories');
```

**Expected Output**:
```
    tablename        | rowsecurity
---------------------+-------------
 expense_categories  | t
 expenses           | t
```

---

### Check indexes

```sql
-- Expense categories indexes
SELECT indexname
FROM pg_indexes
WHERE tablename = 'expense_categories'
ORDER BY indexname;

-- Expenses indexes
SELECT indexname
FROM pg_indexes
WHERE tablename = 'expenses'
ORDER BY indexname;
```

---

### Check triggers

```sql
SELECT trigger_name, event_manipulation, event_object_table
FROM information_schema.triggers
WHERE event_object_table IN ('expenses', 'expense_categories')
ORDER BY event_object_table, trigger_name;
```

**Expected Output**: 2 triggers

---

## Sample Data Insertion (for testing)

### Insert a test expense

```sql
-- Replace <YOUR_BUSINESS_ID> with actual business_id
INSERT INTO expenses (
    business_id,
    category,
    description,
    amount,
    tax_amount,
    expense_date,
    vendor_name,
    payment_method,
    reference_number,
    notes
) VALUES (
    '<YOUR_BUSINESS_ID>'::UUID,
    'Office Supplies',
    'Monthly stationery purchase',
    5000.00,
    800.00,
    '2025-12-01',
    'ABC Stationery Ltd',
    'mpesa',
    'SH12345678',
    'December office supplies'
) RETURNING *;
```

### Insert a custom expense category

```sql
-- Replace <YOUR_BUSINESS_ID> with actual business_id
INSERT INTO expense_categories (
    business_id,
    name,
    description,
    is_system
) VALUES (
    '<YOUR_BUSINESS_ID>'::UUID,
    'Equipment',
    'Office equipment and machinery',
    FALSE
) RETURNING *;
```

---

## Common Queries

### Get all expenses for a business (with pagination)

```sql
SELECT * FROM expenses
WHERE business_id = '<YOUR_BUSINESS_ID>'::UUID
  AND is_active = TRUE
ORDER BY expense_date DESC, created_at DESC
LIMIT 50 OFFSET 0;
```

### Get expense summary by category

```sql
SELECT
    category,
    SUM(amount) as total_amount,
    SUM(tax_amount) as total_tax,
    COUNT(*) as expense_count
FROM expenses
WHERE business_id = '<YOUR_BUSINESS_ID>'::UUID
  AND is_active = TRUE
  AND expense_date BETWEEN '2025-12-01' AND '2025-12-31'
GROUP BY category
ORDER BY total_amount DESC;
```

### Get expenses by date range

```sql
SELECT * FROM expenses
WHERE business_id = '<YOUR_BUSINESS_ID>'::UUID
  AND is_active = TRUE
  AND expense_date BETWEEN '2025-12-01' AND '2025-12-31'
ORDER BY expense_date DESC;
```

### Get unreconciled expenses

```sql
SELECT * FROM expenses
WHERE business_id = '<YOUR_BUSINESS_ID>'::UUID
  AND is_active = TRUE
  AND is_reconciled = FALSE
ORDER BY expense_date DESC;
```

### Get expenses by payment method

```sql
SELECT * FROM expenses
WHERE business_id = '<YOUR_BUSINESS_ID>'::UUID
  AND is_active = TRUE
  AND payment_method = 'mpesa'
ORDER BY expense_date DESC;
```

### Search expenses by vendor (partial match)

```sql
SELECT * FROM expenses
WHERE business_id = '<YOUR_BUSINESS_ID>'::UUID
  AND is_active = TRUE
  AND vendor_name ILIKE '%ABC%'
ORDER BY expense_date DESC;
```

---

## Rollback Migration (if needed)

```sql
-- Drop tables (will cascade delete all data)
DROP TABLE IF EXISTS expenses CASCADE;
DROP TABLE IF EXISTS expense_categories CASCADE;

-- Drop functions
DROP FUNCTION IF EXISTS update_expenses_updated_at() CASCADE;
DROP FUNCTION IF EXISTS update_expense_categories_updated_at() CASCADE;
```

**WARNING**: This will permanently delete all expense data!

---

## Performance Considerations

### Index Usage

The migration creates the following composite indexes for optimal query performance:

1. **Date range queries**: `ix_expenses_business_date` (business_id, expense_date)
2. **Category filtering**: `ix_expenses_business_category` (business_id, category)
3. **Vendor filtering**: `ix_expenses_business_vendor` (business_id, vendor_name)
4. **Reconciliation queries**: `ix_expenses_business_reconciled` (business_id, is_reconciled)
5. **Combined filters**: `ix_expenses_date_range` (business_id, expense_date, category)

### Query Optimization Tips

1. Always filter by `business_id` first (leverages indexes)
2. Use date range filters with indexed columns
3. Leverage pagination to avoid loading large datasets
4. Use `EXPLAIN ANALYZE` to verify index usage

Example:
```sql
EXPLAIN ANALYZE
SELECT * FROM expenses
WHERE business_id = '<YOUR_BUSINESS_ID>'::UUID
  AND expense_date BETWEEN '2025-12-01' AND '2025-12-31'
ORDER BY expense_date DESC
LIMIT 50;
```

---

## Troubleshooting

### Issue: Migration fails with "relation already exists"

**Solution**: Tables already exist. Either drop them first or modify migration to use `CREATE TABLE IF NOT EXISTS`.

### Issue: RLS policies prevent data access

**Solution**: Ensure the `auth.uid()` function is available and user is properly authenticated via Supabase Auth.

### Issue: System categories not inserted

**Solution**: Check for conflicts on unique constraint. The migration uses `ON CONFLICT DO NOTHING` for idempotency.

### Issue: Performance issues with large datasets

**Solution**:
1. Verify indexes are created: `\d expenses` in psql
2. Use `EXPLAIN ANALYZE` to check query plans
3. Add `VACUUM ANALYZE expenses;` to update statistics
4. Consider partitioning by expense_date for very large tables

---

## Migration Checklist

Before running migration:
- [ ] Backup database
- [ ] Verify `businesses` table exists
- [ ] Verify `users` table exists
- [ ] Check Supabase Auth is configured

After running migration:
- [ ] Verify tables created (2 tables)
- [ ] Verify system categories inserted (14 categories)
- [ ] Verify RLS enabled on both tables
- [ ] Verify triggers created (2 triggers)
- [ ] Verify indexes created
- [ ] Test basic INSERT/SELECT operations
- [ ] Verify RLS policies work correctly

---

## Support

For issues or questions:
1. Check Supabase logs in dashboard
2. Review migration SQL for errors
3. Verify all dependencies exist
4. Check RLS policies if access denied
5. Contact backend-developer-2 for assistance

---

**Migration Version**: 003
**Created**: 2025-12-07
**Status**: Ready for deployment
