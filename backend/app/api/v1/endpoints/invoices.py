"""
Invoices API Endpoints

CRUD endpoints for invoice management with status workflow enforcement.
All endpoints require authentication and are scoped to the user's business.

Status Workflow:
- draft -> issued -> paid OR cancelled
- Only draft invoices can be edited
- Invoice numbers are auto-generated: INV-{year}-{sequence}

Security:
- Rate limiting on create, update, delete operations
- Strict rate limiting on PDF generation
- All operations business-scoped
"""

from typing import Optional
from uuid import UUID
from datetime import date
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_active_user, get_db
from app.models.user import User
from app.models.invoice import InvoiceStatus
from app.schemas.invoice import (
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceIssueRequest,
    InvoiceResponse,
    InvoiceDetailResponse,
    InvoiceListResponse,
    InvoicePDFResponse
)
from app.services.invoice_service import get_invoice_service
from app.core.rate_limiter import limiter, RATE_LIMITS


router = APIRouter()


@router.get("/", response_model=InvoiceListResponse)
@limiter.limit(RATE_LIMITS["read"])
async def list_invoices(
    request: Request,
    response: Response,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    status_filter: Optional[InvoiceStatus] = Query(None, alias="status", description="Filter by status"),
    start_date: Optional[date] = Query(None, description="Filter by issue_date >= start_date"),
    end_date: Optional[date] = Query(None, description="Filter by issue_date <= end_date"),
    contact_id: Optional[UUID] = Query(None, description="Filter by customer contact"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List invoices with pagination and filtering.

    Requires authentication. Returns only invoices for the user's business.
    """
    # Ensure user has a business
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a business"
        )

    # Get invoice service
    invoice_service = get_invoice_service(db)

    # List invoices
    invoices, total = await invoice_service.list_invoices(
        business_id=current_user.business_id,
        page=page,
        page_size=page_size,
        status=status_filter,
        start_date=start_date,
        end_date=end_date,
        contact_id=contact_id
    )

    # Convert to response schemas
    invoice_responses = [
        invoice_service.invoice_to_response(invoice)
        for invoice in invoices
    ]

    # Calculate total pages
    total_pages = ceil(total / page_size) if total > 0 else 0

    return InvoiceListResponse(
        invoices=invoice_responses,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/{invoice_id}", response_model=InvoiceDetailResponse)
@limiter.limit(RATE_LIMITS["read"])
async def get_invoice(
    request: Request,
    response: Response,
    invoice_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a single invoice by ID with line items.

    Requires authentication. Invoice must belong to the user's business.
    """
    # Ensure user has a business
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a business"
        )

    # Get invoice service
    invoice_service = get_invoice_service(db)

    # Get invoice with line items
    invoice = await invoice_service.get_invoice_by_id(
        invoice_id=invoice_id,
        business_id=current_user.business_id,
        include_line_items=True
    )

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )

    return invoice_service.invoice_to_detail_response(invoice)


@router.post("/", response_model=InvoiceDetailResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(RATE_LIMITS["create"])
async def create_invoice(
    request: Request,
    response: Response,
    invoice_data: InvoiceCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new invoice in draft status.

    Requires authentication. Invoice will be associated with the user's business.
    Invoice number is auto-generated in format INV-{year}-{sequence}.
    Line items are required (at least one).
    """
    # Ensure user has a business
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a business"
        )

    # Get invoice service
    invoice_service = get_invoice_service(db)

    # Convert line items to dict format
    line_items_data = [
        item.model_dump() for item in invoice_data.line_items
    ]

    # Create invoice
    try:
        invoice = await invoice_service.create_invoice(
            business_id=current_user.business_id,
            contact_id=invoice_data.contact_id,
            line_items_data=line_items_data,
            due_date=invoice_data.due_date,
            notes=invoice_data.notes
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # Reload with line items
    invoice = await invoice_service.get_invoice_by_id(
        invoice_id=invoice.id,
        business_id=current_user.business_id,
        include_line_items=True
    )

    return invoice_service.invoice_to_detail_response(invoice)


@router.put("/{invoice_id}", response_model=InvoiceDetailResponse)
@limiter.limit(RATE_LIMITS["update"])
async def update_invoice(
    request: Request,
    response: Response,
    invoice_id: UUID,
    invoice_data: InvoiceUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update an invoice (only allowed in draft status).

    Requires authentication. Invoice must belong to the user's business.
    Only draft invoices can be edited. Issued, paid, or cancelled invoices are locked.
    """
    # Ensure user has a business
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a business"
        )

    # Get invoice service
    invoice_service = get_invoice_service(db)

    # Convert Pydantic model to dict, excluding unset fields
    update_data = invoice_data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update"
        )

    # Convert line items if present
    if "line_items" in update_data:
        update_data["line_items"] = [
            item.model_dump() if hasattr(item, 'model_dump') else item
            for item in update_data["line_items"]
        ]

    # Update invoice
    try:
        invoice = await invoice_service.update_invoice(
            invoice_id=invoice_id,
            business_id=current_user.business_id,
            data=update_data
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )

    # Reload with line items
    invoice = await invoice_service.get_invoice_by_id(
        invoice_id=invoice.id,
        business_id=current_user.business_id,
        include_line_items=True
    )

    return invoice_service.invoice_to_detail_response(invoice)


@router.post("/{invoice_id}/issue", response_model=InvoiceResponse)
async def issue_invoice(
    invoice_id: UUID,
    issue_data: InvoiceIssueRequest = InvoiceIssueRequest(),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Issue an invoice (change status from draft to issued).

    Requires authentication. Invoice must belong to the user's business.
    Only draft invoices can be issued. Once issued, the invoice is locked from editing.
    """
    # Ensure user has a business
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a business"
        )

    # Get invoice service
    invoice_service = get_invoice_service(db)

    # Issue invoice
    try:
        invoice = await invoice_service.issue_invoice(
            invoice_id=invoice_id,
            business_id=current_user.business_id,
            issue_date=issue_data.issue_date
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )

    return invoice_service.invoice_to_response(invoice)


@router.post("/{invoice_id}/cancel", response_model=InvoiceResponse)
async def cancel_invoice(
    invoice_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Cancel an invoice.

    Requires authentication. Invoice must belong to the user's business.
    Draft, issued, or overdue invoices can be cancelled.
    Paid invoices cannot be cancelled.
    """
    # Ensure user has a business
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a business"
        )

    # Get invoice service
    invoice_service = get_invoice_service(db)

    # Cancel invoice
    try:
        invoice = await invoice_service.cancel_invoice(
            invoice_id=invoice_id,
            business_id=current_user.business_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )

    return invoice_service.invoice_to_response(invoice)


@router.get("/{invoice_id}/pdf")
@limiter.limit(RATE_LIMITS["export_pdf"])
async def generate_invoice_pdf(
    request: Request,
    response: Response,
    invoice_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate and download PDF for an invoice.

    Requires authentication. Invoice must belong to the user's business.
    Returns PDF file as binary content with appropriate headers.
    """
    from fastapi.responses import Response
    from app.services.pdf_service import get_pdf_service

    # Ensure user has a business
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a business"
        )

    # Get invoice service to verify invoice exists
    invoice_service = get_invoice_service(db)
    invoice = await invoice_service.get_invoice_by_id(
        invoice_id=invoice_id,
        business_id=current_user.business_id,
        include_line_items=False
    )

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )

    # Generate PDF
    try:
        pdf_service = get_pdf_service(db)
        pdf_bytes = await pdf_service.generate_invoice_pdf(
            invoice_id=invoice_id,
            business_id=current_user.business_id
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
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=invoice-{invoice.invoice_number}.pdf"
        }
    )
