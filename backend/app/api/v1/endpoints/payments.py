"""
Payments API Endpoints

CRUD endpoints for payment recording and management.
All endpoints require authentication and are scoped to the user's business.

Payment Workflow:
- Payments are linked to invoices
- When payment is created, invoice status is automatically updated
- Payment amount cannot exceed invoice balance due
- Cannot add payment to cancelled invoices
- Deleting a payment recalculates invoice status
"""

from typing import Optional
from uuid import UUID
from datetime import date
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_active_user, get_db
from app.models.user import User
from app.models.payment import PaymentMethod
from app.schemas.payment import (
    PaymentCreate,
    PaymentResponse,
    PaymentListResponse,
    PaymentSummary
)
from app.services.payment_service import get_payment_service
from app.services.invoice_service import get_invoice_service


router = APIRouter()


@router.get("/", response_model=PaymentListResponse)
async def list_payments(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    invoice_id: Optional[UUID] = Query(None, description="Filter by invoice"),
    start_date: Optional[date] = Query(None, description="Filter by payment_date >= start_date"),
    end_date: Optional[date] = Query(None, description="Filter by payment_date <= end_date"),
    payment_method: Optional[PaymentMethod] = Query(None, description="Filter by payment method"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List payments with pagination and filtering.

    Requires authentication. Returns only payments for the user's business.
    """
    # Ensure user has a business
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a business"
        )

    # Get payment service
    payment_service = get_payment_service(db)

    # List payments
    payments, total = await payment_service.list_payments(
        business_id=current_user.business_id,
        page=page,
        page_size=page_size,
        invoice_id=invoice_id,
        start_date=start_date,
        end_date=end_date,
        payment_method=payment_method
    )

    # Convert to response schemas
    payment_responses = [
        payment_service.payment_to_response(payment)
        for payment in payments
    ]

    # Calculate total pages
    total_pages = ceil(total / page_size) if total > 0 else 0

    return PaymentListResponse(
        payments=payment_responses,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a single payment by ID.

    Requires authentication. Payment must belong to the user's business.
    """
    # Ensure user has a business
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a business"
        )

    # Get payment service
    payment_service = get_payment_service(db)

    # Get payment
    payment = await payment_service.get_payment_by_id(
        payment_id=payment_id,
        business_id=current_user.business_id
    )

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )

    return payment_service.payment_to_response(payment)


@router.post("/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    payment_data: PaymentCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new payment and update invoice status.

    Requires authentication. Payment will be associated with the user's business.

    Business Rules:
    - Payment amount must be positive
    - Payment amount cannot exceed invoice balance due
    - Cannot add payment to cancelled invoices
    - Invoice status is automatically updated based on total payments:
      - Fully paid: status = "paid"
      - Partially paid: status = "partially_paid"
    """
    # Ensure user has a business
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a business"
        )

    # Get payment service
    payment_service = get_payment_service(db)

    # Create payment
    try:
        payment = await payment_service.create_payment(
            business_id=current_user.business_id,
            invoice_id=payment_data.invoice_id,
            amount=payment_data.amount,
            payment_date=payment_data.payment_date,
            payment_method=payment_data.payment_method,
            reference_number=payment_data.reference_number,
            notes=payment_data.notes
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    return payment_service.payment_to_response(payment)


@router.delete("/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_payment(
    payment_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a payment and recalculate invoice status.

    Requires authentication. Payment must belong to the user's business.

    Note: Deleting a payment will automatically recalculate the invoice status.
    If this was the only payment, the invoice status may revert to "issued".
    """
    # Ensure user has a business
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a business"
        )

    # Get payment service
    payment_service = get_payment_service(db)

    # Delete payment
    deleted = await payment_service.delete_payment(
        payment_id=payment_id,
        business_id=current_user.business_id
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )

    return None


@router.get("/invoice/{invoice_id}/payments", response_model=list[PaymentResponse])
async def list_payments_for_invoice(
    invoice_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all payments for a specific invoice.

    Requires authentication. Invoice must belong to the user's business.
    Returns payments ordered by payment_date ascending (oldest first).
    """
    # Ensure user has a business
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a business"
        )

    # Verify invoice exists and belongs to business
    invoice_service = get_invoice_service(db)
    invoice = await invoice_service.get_invoice_by_id(
        invoice_id=invoice_id,
        business_id=current_user.business_id
    )

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )

    # Get payments
    payment_service = get_payment_service(db)
    payments = await payment_service.list_payments_for_invoice(
        invoice_id=invoice_id,
        business_id=current_user.business_id
    )

    return [
        payment_service.payment_to_response(payment)
        for payment in payments
    ]


@router.get("/invoice/{invoice_id}/summary", response_model=PaymentSummary)
async def get_payment_summary_for_invoice(
    invoice_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get payment summary for a specific invoice.

    Requires authentication. Invoice must belong to the user's business.

    Returns:
    - Total number of payments
    - Total amount paid
    - Invoice total amount
    - Remaining balance due
    """
    # Ensure user has a business
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a business"
        )

    # Get invoice
    invoice_service = get_invoice_service(db)
    invoice = await invoice_service.get_invoice_by_id(
        invoice_id=invoice_id,
        business_id=current_user.business_id
    )

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )

    # Get payments
    payment_service = get_payment_service(db)
    payments = await payment_service.list_payments_for_invoice(
        invoice_id=invoice_id,
        business_id=current_user.business_id
    )

    total_amount_paid = await payment_service.get_total_paid_for_invoice(
        invoice_id=invoice_id,
        business_id=current_user.business_id
    )

    return PaymentSummary(
        total_payments=len(payments),
        total_amount_paid=total_amount_paid,
        invoice_total=invoice.total_amount,
        balance_due=invoice.balance_due
    )


@router.get("/{payment_id}/receipt/pdf")
async def generate_payment_receipt_pdf(
    payment_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate and download payment receipt as PDF.

    Requires authentication. Payment must belong to the user's business.
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

    # Get payment service to verify payment exists
    payment_service = get_payment_service(db)
    payment = await payment_service.get_payment_by_id(
        payment_id=payment_id,
        business_id=current_user.business_id
    )

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )

    # Generate PDF
    try:
        pdf_service = get_pdf_service(db)
        pdf_bytes = await pdf_service.generate_receipt_pdf(
            payment_id=payment_id,
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
            "Content-Disposition": f"attachment; filename=receipt-{payment_id}.pdf"
        }
    )
