"""
Tax API Endpoints

Endpoints for Kenya tax compliance operations (VAT and TOT).
All endpoints require authentication and are scoped to the user's business.

Features:
- Tax settings management (VAT/TOT registration)
- VAT summary calculation (16% rate)
- TOT summary calculation (1% rate)
- Filing guidance and deadlines
- VAT return export in iTax format

Kenya Tax Rules:
- VAT: 16% for businesses with turnover > KES 5M
- TOT: 1% for businesses with KES 1-50M turnover
- Filing deadline: 20th of following month
"""

from typing import Optional
from uuid import UUID
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_active_user, get_db
from app.models.user import User
from app.schemas.tax import (
    TaxSettingsCreate,
    TaxSettingsUpdate,
    TaxSettingsResponse,
    VATSummaryRequest,
    VATSummaryResponse,
    TOTSummaryRequest,
    TOTSummaryResponse,
    FilingGuidanceResponse,
    VATReturnExport,
    TaxPeriod
)
from app.services.tax_service import get_tax_service


router = APIRouter()


@router.get("/settings", response_model=TaxSettingsResponse)
async def get_tax_settings(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get tax settings for the current business.

    Creates default settings if none exist.
    Requires authentication.
    """
    # Ensure user has a business
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a business"
        )

    # Get tax service
    tax_service = get_tax_service(db)

    # Get settings (creates default if not exists)
    settings = await tax_service.get_tax_settings(current_user.business_id)

    return tax_service.settings_to_response(settings)


@router.put("/settings", response_model=TaxSettingsResponse)
async def update_tax_settings(
    settings_update: TaxSettingsUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update tax settings for the current business.

    Business Rules:
    - Cannot be both VAT registered and TOT eligible
    - VAT registration number required if VAT registered
    - VAT registration date cannot be in the future

    Requires authentication.
    """
    # Ensure user has a business
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a business"
        )

    # Get tax service
    tax_service = get_tax_service(db)

    try:
        # Update settings
        settings = await tax_service.update_tax_settings(
            business_id=current_user.business_id,
            data=settings_update.model_dump(exclude_unset=True)
        )

        return tax_service.settings_to_response(settings)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/vat-summary", response_model=VATSummaryResponse)
async def get_vat_summary(
    start_date: date = Query(..., description="Start date for VAT calculation"),
    end_date: date = Query(..., description="End date for VAT calculation"),
    period: TaxPeriod = Query(TaxPeriod.MONTH, description="Period type: month, quarter, or year"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get VAT summary for a specified period.

    VAT Calculation:
    - Output VAT: VAT collected from customers (16% of sales)
    - Input VAT: VAT paid on business expenses
    - Net VAT: Output VAT - Input VAT
      - Positive: Amount owed to KRA
      - Negative: Refund due from KRA

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

    # Get tax service
    tax_service = get_tax_service(db)

    # Calculate VAT summary
    vat_summary = await tax_service.calculate_vat_summary(
        business_id=current_user.business_id,
        start_date=start_date,
        end_date=end_date,
        period=period
    )

    return vat_summary


@router.get("/tot-summary", response_model=TOTSummaryResponse)
async def get_tot_summary(
    start_date: date = Query(..., description="Start date for TOT calculation"),
    end_date: date = Query(..., description="End date for TOT calculation"),
    period: TaxPeriod = Query(TaxPeriod.MONTH, description="Period type: month, quarter, or year"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get TOT (Turnover Tax) summary for a specified period.

    TOT Calculation:
    - Gross Turnover: Total sales for period
    - TOT Payable: 1% of gross turnover

    Note: TOT rate changed from 3% to 1% in 2024.

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

    # Get tax service
    tax_service = get_tax_service(db)

    # Calculate TOT summary
    tot_summary = await tax_service.calculate_tot_summary(
        business_id=current_user.business_id,
        start_date=start_date,
        end_date=end_date,
        period=period
    )

    return tot_summary


@router.get("/filing-guidance", response_model=FilingGuidanceResponse)
async def get_filing_guidance(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get tax filing guidance and deadlines for the current business.

    Returns:
    - Tax type (VAT, TOT, or None)
    - Next filing deadline (20th of following month)
    - Filing requirements and documents needed
    - KRA iTax portal URL
    - Helpful notes and reminders

    Requires authentication.
    """
    # Ensure user has a business
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a business"
        )

    # Get tax service
    tax_service = get_tax_service(db)

    # Get filing guidance
    guidance = await tax_service.get_filing_guidance(current_user.business_id)

    return guidance


@router.get("/vat-return/export", response_model=VATReturnExport)
async def export_vat_return(
    start_date: date = Query(..., description="Period start date"),
    end_date: date = Query(..., description="Period end date"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Export VAT return data in iTax format.

    Returns VAT return data suitable for uploading to KRA iTax portal.
    Only available for VAT-registered businesses.

    Format includes:
    - Period details (month/year)
    - VAT registration number
    - Standard rated, zero rated, and exempt sales/purchases
    - Output and input VAT
    - Net VAT payable/refundable

    Requires authentication and VAT registration.
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

    # Get tax service
    tax_service = get_tax_service(db)

    try:
        # Export VAT return
        vat_return = await tax_service.export_vat_return(
            business_id=current_user.business_id,
            start_date=start_date,
            end_date=end_date
        )

        return vat_return

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
