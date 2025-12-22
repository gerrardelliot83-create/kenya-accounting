"""
Reports API Endpoints

Endpoints for financial report generation and export.
All endpoints require authentication and are scoped to the user's business.

Features:
- Profit & Loss statement
- Expense summary by category
- Aged receivables analysis
- Sales summary by customer and item
- Report export in multiple formats (JSON, PDF, CSV, Excel)

Reports:
1. Profit & Loss: Revenue vs expenses with profit margins
2. Expense Summary: Category breakdown with percentages
3. Aged Receivables: Outstanding invoices by age buckets
4. Sales Summary: Sales by customer and by item/service
"""

from typing import Optional
from uuid import UUID
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_active_user, get_db
from app.models.user import User
from app.schemas.report import (
    ReportRequest,
    ReportType,
    ReportFormat,
    ProfitLossResponse,
    ExpenseSummaryResponse,
    AgedReceivablesResponse,
    SalesSummaryResponse,
    ReportExportResponse
)
from app.services.report_service import get_report_service


router = APIRouter()


@router.get("/profit-loss", response_model=ProfitLossResponse)
async def get_profit_loss_report(
    start_date: date = Query(..., description="Report start date"),
    end_date: date = Query(..., description="Report end date"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate Profit & Loss (P&L) statement for a period.

    The P&L statement shows:
    - Total revenue from paid invoices
    - Expenses broken down by category
    - Gross profit and net profit
    - Profit margins as percentages

    Calculation:
    - Revenue: Sum of paid invoice totals
    - Expenses: Sum by category with percentages
    - Gross Profit: Revenue - Expenses
    - Net Profit: Revenue - All Expenses
    - Margins: Profit as percentage of revenue

    Requires authentication.
    """
    # Ensure user has a business
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a business"
        )

    # Validate date range
    if end_date < start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="end_date must be after start_date"
        )

    # Get report service
    report_service = get_report_service(db)

    # Generate report
    report = await report_service.generate_profit_loss(
        business_id=current_user.business_id,
        start_date=start_date,
        end_date=end_date
    )

    return report


@router.get("/expense-summary", response_model=ExpenseSummaryResponse)
async def get_expense_summary_report(
    start_date: date = Query(..., description="Report start date"),
    end_date: date = Query(..., description="Report end date"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate Expense Summary report for a period.

    The expense summary shows:
    - Expenses grouped by category
    - Total amount and percentage for each category
    - Number of expenses per category
    - Total expenses and tax amounts
    - Average expense amount
    - Largest spending category

    Useful for:
    - Understanding spending patterns
    - Identifying cost reduction opportunities
    - Budget variance analysis

    Requires authentication.
    """
    # Ensure user has a business
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a business"
        )

    # Validate date range
    if end_date < start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="end_date must be after start_date"
        )

    # Get report service
    report_service = get_report_service(db)

    # Generate report
    report = await report_service.generate_expense_summary(
        business_id=current_user.business_id,
        start_date=start_date,
        end_date=end_date
    )

    return report


@router.get("/aged-receivables", response_model=AgedReceivablesResponse)
async def get_aged_receivables_report(
    as_of_date: Optional[date] = Query(None, description="Report date (defaults to today)"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate Aged Receivables report.

    The aged receivables report shows outstanding invoices grouped by age:
    - Current: Not yet due
    - 1-30 days: Up to 30 days overdue
    - 31-60 days: 31 to 60 days overdue
    - 61-90 days: 61 to 90 days overdue
    - Over 90 days: More than 90 days overdue

    Each bucket shows:
    - Total amount outstanding
    - Number of invoices
    - Percentage of total receivables

    Summary includes:
    - Total receivables
    - Total overdue amount
    - Overdue percentage

    Useful for:
    - Cash flow management
    - Collection prioritization
    - Customer credit assessment
    - Bad debt provisioning

    Requires authentication.
    """
    # Ensure user has a business
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a business"
        )

    # Get report service
    report_service = get_report_service(db)

    # Generate report
    report = await report_service.generate_aged_receivables(
        business_id=current_user.business_id,
        as_of_date=as_of_date
    )

    return report


@router.get("/sales-summary", response_model=SalesSummaryResponse)
async def get_sales_summary_report(
    start_date: date = Query(..., description="Report start date"),
    end_date: date = Query(..., description="Report end date"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate Sales Summary report for a period.

    The sales summary shows:
    - Sales breakdown by customer (name, amount, invoice count, percentage)
    - Top customer by sales value
    - Sales breakdown by item/service (name, quantity, amount, percentage)
    - Top selling item by sales value
    - Total sales and invoice count
    - Average invoice value
    - Number of unique customers

    Useful for:
    - Customer relationship management
    - Revenue concentration analysis
    - Product/service performance
    - Sales forecasting
    - Marketing strategy

    Requires authentication.
    """
    # Ensure user has a business
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a business"
        )

    # Validate date range
    if end_date < start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="end_date must be after start_date"
        )

    # Get report service
    report_service = get_report_service(db)

    # Generate report
    report = await report_service.generate_sales_summary(
        business_id=current_user.business_id,
        start_date=start_date,
        end_date=end_date
    )

    return report


@router.get("/profit-loss/pdf")
async def export_profit_loss_pdf(
    start_date: date = Query(..., description="Report start date"),
    end_date: date = Query(..., description="Report end date"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate and download Profit & Loss report as PDF.

    Requires authentication. Returns PDF file as binary content.
    """
    from fastapi.responses import Response
    from app.services.pdf_service import get_pdf_service

    # Ensure user has a business
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a business"
        )

    # Validate date range
    if end_date < start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="end_date must be after start_date"
        )

    # Generate PDF
    try:
        pdf_service = get_pdf_service(db)
        pdf_bytes = await pdf_service.generate_profit_loss_pdf(
            business_id=current_user.business_id,
            start_date=start_date,
            end_date=end_date
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating PDF: {str(e)}"
        )

    # Return PDF as downloadable file
    filename = f"profit-loss-{start_date}-to-{end_date}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get("/expense-summary/pdf")
async def export_expense_summary_pdf(
    start_date: date = Query(..., description="Report start date"),
    end_date: date = Query(..., description="Report end date"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate and download Expense Summary report as PDF.

    Requires authentication. Returns PDF file as binary content.
    """
    from fastapi.responses import Response
    from app.services.pdf_service import get_pdf_service

    # Ensure user has a business
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a business"
        )

    # Validate date range
    if end_date < start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="end_date must be after start_date"
        )

    # Generate PDF
    try:
        pdf_service = get_pdf_service(db)
        pdf_bytes = await pdf_service.generate_expense_summary_pdf(
            business_id=current_user.business_id,
            start_date=start_date,
            end_date=end_date
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating PDF: {str(e)}"
        )

    # Return PDF as downloadable file
    filename = f"expense-summary-{start_date}-to-{end_date}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get("/aged-receivables/pdf")
async def export_aged_receivables_pdf(
    as_of_date: Optional[date] = Query(None, description="Report date (defaults to today)"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate and download Aged Receivables report as PDF.

    Requires authentication. Returns PDF file as binary content.
    """
    from fastapi.responses import Response
    from app.services.pdf_service import get_pdf_service

    # Ensure user has a business
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a business"
        )

    # Use today if as_of_date not provided
    if as_of_date is None:
        as_of_date = date.today()

    # Generate PDF
    try:
        pdf_service = get_pdf_service(db)
        pdf_bytes = await pdf_service.generate_aged_receivables_pdf(
            business_id=current_user.business_id,
            as_of_date=as_of_date
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating PDF: {str(e)}"
        )

    # Return PDF as downloadable file
    filename = f"aged-receivables-{as_of_date}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.post("/export", response_model=ReportExportResponse)
async def export_report(
    report_request: ReportRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate and export a report in the requested format.

    Supports:
    - Report types: profit_loss, expense_summary, aged_receivables, sales_summary
    - Formats: json, pdf, csv, excel

    For JSON format:
    - Returns report data directly in the response

    For PDF format:
    - Use the dedicated PDF endpoints instead (/profit-loss/pdf, /expense-summary/pdf, etc.)

    For CSV/Excel formats:
    - Not yet implemented

    Requires authentication.
    """
    # Ensure user has a business
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a business"
        )

    # Validate date range
    if report_request.end_date < report_request.start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="end_date must be after start_date"
        )

    # Get report service
    report_service = get_report_service(db)

    # Generate report based on type
    report_data = None

    try:
        if report_request.report_type == ReportType.PROFIT_LOSS:
            report = await report_service.generate_profit_loss(
                business_id=current_user.business_id,
                start_date=report_request.start_date,
                end_date=report_request.end_date
            )
            report_data = report.model_dump()

        elif report_request.report_type == ReportType.EXPENSE_SUMMARY:
            report = await report_service.generate_expense_summary(
                business_id=current_user.business_id,
                start_date=report_request.start_date,
                end_date=report_request.end_date
            )
            report_data = report.model_dump()

        elif report_request.report_type == ReportType.AGED_RECEIVABLES:
            report = await report_service.generate_aged_receivables(
                business_id=current_user.business_id,
                as_of_date=report_request.end_date
            )
            report_data = report.model_dump()

        elif report_request.report_type == ReportType.SALES_SUMMARY:
            report = await report_service.generate_sales_summary(
                business_id=current_user.business_id,
                start_date=report_request.start_date,
                end_date=report_request.end_date
            )
            report_data = report.model_dump()

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported report type: {report_request.report_type}"
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating report: {str(e)}"
        )

    # For JSON format, return data directly
    if report_request.format == ReportFormat.JSON:
        return ReportExportResponse(
            success=True,
            report_type=report_request.report_type.value,
            format=report_request.format.value,
            file_url=None,
            data=report_data,
            generated_at=datetime.utcnow(),
            expires_at=None
        )

    # For PDF format, suggest using dedicated endpoints
    elif report_request.format == ReportFormat.PDF:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"For PDF export, please use the dedicated endpoint: /reports/{report_request.report_type.value}/pdf"
        )

    # For CSV/Excel formats, not yet implemented
    else:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=f"{report_request.format.value.upper()} export is not yet implemented. "
                   f"Please use JSON format or PDF endpoints."
        )
