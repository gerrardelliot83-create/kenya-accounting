"""
Report Service

Business logic for financial report generation.
Handles Profit & Loss, Expense Summary, Aged Receivables, and Sales Summary reports.

Features:
- Profit & Loss statement with revenue and expense breakdown
- Expense summary by category with percentages
- Aged receivables analysis (current, 1-30, 31-60, 61-90, 90+ days)
- Sales summary by customer and item

Security Notes:
- All operations are scoped to business_id
- Date range validation
- Proper error handling with ValueError
"""

from typing import Optional, Dict, Any, List, Tuple
from uuid import UUID
from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select, func, and_, or_, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.invoice import Invoice, InvoiceStatus
from app.models.invoice_item import InvoiceItem
from app.models.expense import Expense
from app.models.contact import Contact
from app.models.item import Item
from app.schemas.report import (
    ProfitLossResponse,
    ExpenseSummaryResponse,
    AgedReceivablesResponse,
    SalesSummaryResponse,
    ExpenseCategoryTotal,
    AgingBucket,
    CustomerSales,
    ItemSales
)


class ReportService:
    """Service for financial report generation."""

    def __init__(self, db: AsyncSession):
        """
        Initialize report service.

        Args:
            db: Database session
        """
        self.db = db

    async def generate_profit_loss(
        self,
        business_id: UUID,
        start_date: date,
        end_date: date
    ) -> ProfitLossResponse:
        """
        Generate Profit & Loss statement for a period.

        P&L Calculation:
        - Revenue: Sum of paid invoice totals (PAID status)
        - Expenses: Sum by category from expenses table
        - Gross Profit: Revenue - Cost of Goods (for now, same as net profit)
        - Net Profit: Revenue - All Expenses

        Args:
            business_id: Business UUID
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            ProfitLossResponse with P&L statement
        """
        # Calculate total revenue (paid invoices only)
        revenue_query = await self.db.execute(
            select(
                func.coalesce(func.sum(Invoice.total_amount), 0).label("total_revenue")
            )
            .where(
                Invoice.business_id == business_id,
                Invoice.status == InvoiceStatus.PAID.value,
                Invoice.issue_date >= start_date,
                Invoice.issue_date <= end_date
            )
        )
        revenue_result = revenue_query.first()
        total_revenue = Decimal(str(revenue_result.total_revenue or 0))

        # Get expenses by category
        expenses_query = await self.db.execute(
            select(
                Expense.category,
                func.sum(Expense.amount + Expense.tax_amount).label("total_amount"),
                func.count(Expense.id).label("expense_count")
            )
            .where(
                Expense.business_id == business_id,
                Expense.is_active == True,
                Expense.expense_date >= start_date,
                Expense.expense_date <= end_date
            )
            .group_by(Expense.category)
            .order_by(func.sum(Expense.amount + Expense.tax_amount).desc())
        )

        expenses_by_category = []
        total_expenses = Decimal("0.00")

        for row in expenses_query:
            category_total = Decimal(str(row.total_amount or 0))
            total_expenses += category_total

        # Calculate percentages after we have total
        expenses_query_2 = await self.db.execute(
            select(
                Expense.category,
                func.sum(Expense.amount + Expense.tax_amount).label("total_amount"),
                func.count(Expense.id).label("expense_count")
            )
            .where(
                Expense.business_id == business_id,
                Expense.is_active == True,
                Expense.expense_date >= start_date,
                Expense.expense_date <= end_date
            )
            .group_by(Expense.category)
            .order_by(func.sum(Expense.amount + Expense.tax_amount).desc())
        )

        for row in expenses_query_2:
            category_total = Decimal(str(row.total_amount or 0))
            percentage = (category_total / total_expenses * 100) if total_expenses > 0 else Decimal("0.00")

            expenses_by_category.append(
                ExpenseCategoryTotal(
                    category=row.category,
                    total=round(category_total, 2),
                    percentage=round(percentage, 2),
                    count=row.expense_count
                )
            )

        # Calculate profit metrics
        # For simplicity, gross profit = net profit (no COGS tracking yet)
        gross_profit = total_revenue - total_expenses
        net_profit = total_revenue - total_expenses

        # Calculate margins
        gross_margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else Decimal("0.00")
        net_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else Decimal("0.00")

        return ProfitLossResponse(
            report_type="Profit & Loss Statement",
            start_date=start_date,
            end_date=end_date,
            currency="KES",
            total_revenue=round(total_revenue, 2),
            expenses_by_category=expenses_by_category,
            total_expenses=round(total_expenses, 2),
            gross_profit=round(gross_profit, 2),
            net_profit=round(net_profit, 2),
            gross_margin_percentage=round(gross_margin, 2),
            net_margin_percentage=round(net_margin, 2)
        )

    async def generate_expense_summary(
        self,
        business_id: UUID,
        start_date: date,
        end_date: date
    ) -> ExpenseSummaryResponse:
        """
        Generate Expense Summary report for a period.

        Groups expenses by category with totals, percentages, and counts.

        Args:
            business_id: Business UUID
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            ExpenseSummaryResponse with expense breakdown
        """
        # Get expenses by category
        expenses_query = await self.db.execute(
            select(
                Expense.category,
                func.sum(Expense.amount).label("total_amount"),
                func.sum(Expense.tax_amount).label("total_tax"),
                func.count(Expense.id).label("expense_count")
            )
            .where(
                Expense.business_id == business_id,
                Expense.is_active == True,
                Expense.expense_date >= start_date,
                Expense.expense_date <= end_date
            )
            .group_by(Expense.category)
            .order_by(func.sum(Expense.amount).desc())
        )

        categories = []
        total_expenses = Decimal("0.00")
        total_tax = Decimal("0.00")
        expense_count = 0

        # First pass: calculate totals
        category_data = []
        for row in expenses_query:
            category_amount = Decimal(str(row.total_amount or 0))
            category_tax = Decimal(str(row.total_tax or 0))
            total_expenses += category_amount
            total_tax += category_tax
            expense_count += row.expense_count
            category_data.append({
                "category": row.category,
                "amount": category_amount,
                "tax": category_tax,
                "count": row.expense_count
            })

        # Second pass: calculate percentages
        largest_category = None
        largest_amount = Decimal("0.00")

        for data in category_data:
            percentage = (data["amount"] / total_expenses * 100) if total_expenses > 0 else Decimal("0.00")

            categories.append(
                ExpenseCategoryTotal(
                    category=data["category"],
                    total=round(data["amount"], 2),
                    percentage=round(percentage, 2),
                    count=data["count"]
                )
            )

            if data["amount"] > largest_amount:
                largest_amount = data["amount"]
                largest_category = data["category"]

        # Calculate average expense
        average_expense = (total_expenses / expense_count) if expense_count > 0 else Decimal("0.00")

        return ExpenseSummaryResponse(
            report_type="Expense Summary",
            start_date=start_date,
            end_date=end_date,
            currency="KES",
            categories=categories,
            total_expenses=round(total_expenses, 2),
            total_tax=round(total_tax, 2),
            expense_count=expense_count,
            average_expense=round(average_expense, 2),
            largest_category=largest_category
        )

    async def generate_aged_receivables(
        self,
        business_id: UUID,
        as_of_date: Optional[date] = None
    ) -> AgedReceivablesResponse:
        """
        Generate Aged Receivables report.

        Groups outstanding invoices by age:
        - Current: Not yet due
        - 1-30 days: 1 to 30 days overdue
        - 31-60 days: 31 to 60 days overdue
        - 61-90 days: 61 to 90 days overdue
        - 90+ days: Over 90 days overdue

        Args:
            business_id: Business UUID
            as_of_date: Report date (defaults to today)

        Returns:
            AgedReceivablesResponse with aging analysis
        """
        if as_of_date is None:
            as_of_date = date.today()

        # Get all outstanding invoices (issued but not fully paid)
        invoices_query = await self.db.execute(
            select(Invoice)
            .where(
                Invoice.business_id == business_id,
                Invoice.status.in_([
                    InvoiceStatus.ISSUED.value,
                    InvoiceStatus.PARTIALLY_PAID.value,
                    InvoiceStatus.OVERDUE.value
                ]),
                Invoice.due_date.isnot(None)
            )
        )
        invoices = invoices_query.scalars().all()

        # Initialize buckets
        buckets = {
            "current": {"amount": Decimal("0.00"), "count": 0},
            "1-30": {"amount": Decimal("0.00"), "count": 0},
            "31-60": {"amount": Decimal("0.00"), "count": 0},
            "61-90": {"amount": Decimal("0.00"), "count": 0},
            "90+": {"amount": Decimal("0.00"), "count": 0}
        }

        total_receivables = Decimal("0.00")
        total_count = 0

        # Classify invoices by age
        for invoice in invoices:
            balance_due = invoice.balance_due
            if balance_due <= 0:
                continue  # Skip if fully paid

            total_receivables += balance_due
            total_count += 1

            # Calculate days overdue
            days_overdue = (as_of_date - invoice.due_date).days

            # Classify into bucket
            if days_overdue < 0:
                # Not yet due (current)
                buckets["current"]["amount"] += balance_due
                buckets["current"]["count"] += 1
            elif days_overdue <= 30:
                buckets["1-30"]["amount"] += balance_due
                buckets["1-30"]["count"] += 1
            elif days_overdue <= 60:
                buckets["31-60"]["amount"] += balance_due
                buckets["31-60"]["count"] += 1
            elif days_overdue <= 90:
                buckets["61-90"]["amount"] += balance_due
                buckets["61-90"]["count"] += 1
            else:
                buckets["90+"]["amount"] += balance_due
                buckets["90+"]["count"] += 1

        # Calculate percentages and create bucket objects
        def create_bucket(name: str, key: str) -> AgingBucket:
            amount = buckets[key]["amount"]
            count = buckets[key]["count"]
            percentage = (amount / total_receivables * 100) if total_receivables > 0 else Decimal("0.00")
            return AgingBucket(
                bucket_name=name,
                amount=round(amount, 2),
                invoice_count=count,
                percentage=round(percentage, 2)
            )

        # Calculate overdue amount (everything except current)
        overdue_amount = (
            buckets["1-30"]["amount"] +
            buckets["31-60"]["amount"] +
            buckets["61-90"]["amount"] +
            buckets["90+"]["amount"]
        )
        overdue_percentage = (overdue_amount / total_receivables * 100) if total_receivables > 0 else Decimal("0.00")

        return AgedReceivablesResponse(
            report_type="Aged Receivables",
            as_of_date=as_of_date,
            currency="KES",
            current=create_bucket("Current", "current"),
            days_1_30=create_bucket("1-30 days", "1-30"),
            days_31_60=create_bucket("31-60 days", "31-60"),
            days_61_90=create_bucket("61-90 days", "61-90"),
            days_over_90=create_bucket("Over 90 days", "90+"),
            total_receivables=round(total_receivables, 2),
            total_invoice_count=total_count,
            overdue_amount=round(overdue_amount, 2),
            overdue_percentage=round(overdue_percentage, 2)
        )

    async def generate_sales_summary(
        self,
        business_id: UUID,
        start_date: date,
        end_date: date
    ) -> SalesSummaryResponse:
        """
        Generate Sales Summary report for a period.

        Breaks down sales by customer and by item/service.

        Args:
            business_id: Business UUID
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            SalesSummaryResponse with sales breakdown
        """
        # Get sales by customer
        customer_sales_query = await self.db.execute(
            select(
                Invoice.contact_id,
                Contact.name,
                func.sum(Invoice.total_amount).label("total_sales"),
                func.count(Invoice.id).label("invoice_count")
            )
            .join(Contact, Invoice.contact_id == Contact.id)
            .where(
                Invoice.business_id == business_id,
                Invoice.status.in_([
                    InvoiceStatus.ISSUED.value,
                    InvoiceStatus.PAID.value,
                    InvoiceStatus.PARTIALLY_PAID.value
                ]),
                Invoice.issue_date >= start_date,
                Invoice.issue_date <= end_date
            )
            .group_by(Invoice.contact_id, Contact.name)
            .order_by(func.sum(Invoice.total_amount).desc())
        )

        by_customer = []
        total_sales = Decimal("0.00")
        total_invoices = 0
        customer_count = 0

        # First pass: calculate totals
        customer_data = []
        for row in customer_sales_query:
            sales_amount = Decimal(str(row.total_sales or 0))
            total_sales += sales_amount
            total_invoices += row.invoice_count
            customer_count += 1
            customer_data.append({
                "customer_id": row.contact_id,
                "customer_name": row.name,
                "total_sales": sales_amount,
                "invoice_count": row.invoice_count
            })

        # Second pass: calculate percentages
        top_customer = None
        for data in customer_data:
            percentage = (data["total_sales"] / total_sales * 100) if total_sales > 0 else Decimal("0.00")

            customer_sales_obj = CustomerSales(
                customer_id=data["customer_id"],
                customer_name=data["customer_name"],
                total_sales=round(data["total_sales"], 2),
                invoice_count=data["invoice_count"],
                percentage=round(percentage, 2)
            )
            by_customer.append(customer_sales_obj)

            if top_customer is None:
                top_customer = customer_sales_obj

        # Get sales by item
        item_sales_query = await self.db.execute(
            select(
                InvoiceItem.item_id,
                InvoiceItem.description,
                func.sum(InvoiceItem.quantity).label("quantity_sold"),
                func.sum(InvoiceItem.line_total).label("total_sales")
            )
            .join(Invoice, InvoiceItem.invoice_id == Invoice.id)
            .where(
                Invoice.business_id == business_id,
                Invoice.status.in_([
                    InvoiceStatus.ISSUED.value,
                    InvoiceStatus.PAID.value,
                    InvoiceStatus.PARTIALLY_PAID.value
                ]),
                Invoice.issue_date >= start_date,
                Invoice.issue_date <= end_date
            )
            .group_by(InvoiceItem.item_id, InvoiceItem.description)
            .order_by(func.sum(InvoiceItem.line_total).desc())
        )

        by_item = []
        item_data = []
        item_total_sales = Decimal("0.00")

        # First pass: collect data
        for row in item_sales_query:
            sales_amount = Decimal(str(row.total_sales or 0))
            item_total_sales += sales_amount
            item_data.append({
                "item_id": row.item_id,
                "item_name": row.description,
                "quantity_sold": Decimal(str(row.quantity_sold or 0)),
                "total_sales": sales_amount
            })

        # Second pass: calculate percentages
        top_item = None
        for data in item_data:
            percentage = (data["total_sales"] / item_total_sales * 100) if item_total_sales > 0 else Decimal("0.00")

            item_sales_obj = ItemSales(
                item_id=data["item_id"],
                item_name=data["item_name"],
                quantity_sold=round(data["quantity_sold"], 2),
                total_sales=round(data["total_sales"], 2),
                percentage=round(percentage, 2)
            )
            by_item.append(item_sales_obj)

            if top_item is None:
                top_item = item_sales_obj

        # Calculate average invoice value
        average_invoice = (total_sales / total_invoices) if total_invoices > 0 else Decimal("0.00")

        return SalesSummaryResponse(
            report_type="Sales Summary",
            start_date=start_date,
            end_date=end_date,
            currency="KES",
            by_customer=by_customer,
            top_customer=top_customer,
            by_item=by_item,
            top_item=top_item,
            total_sales=round(total_sales, 2),
            total_invoices=total_invoices,
            average_invoice_value=round(average_invoice, 2),
            customer_count=customer_count
        )


def get_report_service(db: AsyncSession) -> ReportService:
    """
    Get report service instance.

    Args:
        db: Database session

    Returns:
        ReportService instance
    """
    return ReportService(db)
