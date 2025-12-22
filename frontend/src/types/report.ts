/**
 * Report-related type definitions for financial reporting
 */

/**
 * Expense breakdown by category
 */
export interface ExpenseCategory {
  category: string;
  amount: number;
  percentage: number;
}

/**
 * Profit and Loss Report
 */
export interface ProfitLossReport {
  period_start: string;
  period_end: string;
  total_revenue: number;
  total_expenses: number;
  gross_profit: number;
  net_profit: number;
  profit_margin: number;
  expenses_by_category: ExpenseCategory[];
}

/**
 * Category total for expense summary
 */
export interface CategoryTotal {
  category: string;
  total: number;
  count: number;
  percentage: number;
}

/**
 * Expense Summary Report
 */
export interface ExpenseSummary {
  period_start: string;
  period_end: string;
  total_expenses: number;
  categories: CategoryTotal[];
  largest_category: string;
}

/**
 * Aging bucket for receivables
 */
export interface AgingBucket {
  label: string;
  days_range: string;
  total_amount: number;
  invoice_count: number;
  invoices?: InvoiceDetail[];
}

/**
 * Invoice detail in aging bucket
 */
export interface InvoiceDetail {
  invoice_id: string;
  invoice_number: string;
  customer_name: string;
  amount: number;
  due_date: string;
  days_overdue: number;
}

/**
 * Aged Receivables Report
 */
export interface AgedReceivables {
  as_of_date: string;
  total_outstanding: number;
  buckets: AgingBucket[];
  overdue_percentage: number;
}

/**
 * Sales by customer
 */
export interface CustomerSales {
  customer_id: string;
  customer_name: string;
  total_sales: number;
  invoice_count: number;
  percentage_of_total: number;
}

/**
 * Sales by item
 */
export interface ItemSales {
  item_id: string;
  item_name: string;
  quantity_sold: number;
  total_sales: number;
  percentage_of_total: number;
}

/**
 * Sales Summary Report
 */
export interface SalesSummary {
  period_start: string;
  period_end: string;
  total_sales: number;
  by_customer: CustomerSales[];
  by_item: ItemSales[];
}

/**
 * Report export formats
 */
export type ReportFormat = 'pdf' | 'excel' | 'csv';

/**
 * Date range for reports
 */
export interface DateRange {
  start_date: string;
  end_date: string;
}
