"""
Bank Import API Endpoints

Endpoints for bank statement import, transaction management, and reconciliation.
All endpoints require authentication and are scoped to the user's business.

Features:
- CSV/PDF bank statement upload and parsing
- Automatic column detection and mapping
- Transaction import and processing
- Fuzzy matching reconciliation with expenses/invoices
- Manual match confirmation and management
- Reconciliation statistics and reporting

Security:
- All operations require authentication
- Business-scoped data access (user must have business_id)
- File type validation (CSV and PDF only)
- Input sanitization and validation
- Strict rate limiting on file uploads (5/minute)
- Moderate rate limiting on processing operations
"""

from typing import Optional
from uuid import UUID
from datetime import date
from math import ceil
import logging

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_active_user, get_db
from app.models.user import User
from app.schemas.bank_import import (
    BankImportResponse,
    BankImportListResponse,
    BankTransactionResponse,
    BankTransactionListResponse,
    ColumnMappingRequest,
    MatchRequest,
    ReconciliationSuggestion,
    ReconciliationMatch,
    ReconciliationStats,
    FileType,
    ImportStatus,
    ReconciliationStatus
)
from app.services.bank_import_service import get_bank_import_service
from app.core.encryption import get_encryption_service
from app.core.rate_limiter import limiter, RATE_LIMITS

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Helper Functions
# ============================================================================

def _validate_file_type(filename: str) -> str:
    """
    Validate and extract file type from filename.

    Args:
        filename: Original filename with extension

    Returns:
        File type ('csv' or 'pdf')

    Raises:
        HTTPException: If file type is not supported
    """
    filename_lower = filename.lower()

    if filename_lower.endswith('.csv'):
        return FileType.CSV.value
    elif filename_lower.endswith('.pdf'):
        return FileType.PDF.value
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV and PDF files are supported"
        )


def _import_to_response(bank_import) -> BankImportResponse:
    """Convert BankImport model to response schema."""
    return BankImportResponse(
        id=bank_import.id,
        business_id=bank_import.business_id,
        file_name=bank_import.file_name,
        file_type=bank_import.file_type.value,
        source_bank=bank_import.source_bank,
        status=bank_import.status.value,
        column_mapping=bank_import.column_mapping,
        total_rows=bank_import.total_rows,
        imported_rows=bank_import.imported_rows,
        error_message=bank_import.error_message,
        created_at=bank_import.created_at,
        updated_at=bank_import.updated_at
    )


def _transaction_to_response(transaction) -> BankTransactionResponse:
    """Convert BankTransaction model to response schema."""
    encryption_service = get_encryption_service()

    # Decrypt sensitive fields
    description = encryption_service.decrypt(transaction.description)
    reference = encryption_service.decrypt_optional(transaction.reference)

    return BankTransactionResponse(
        id=transaction.id,
        business_id=transaction.business_id,
        bank_import_id=transaction.bank_import_id,
        transaction_date=transaction.transaction_date,
        description=description,
        reference=reference,
        debit_amount=transaction.debit_amount,
        credit_amount=transaction.credit_amount,
        balance=transaction.balance,
        reconciliation_status=transaction.reconciliation_status.value,
        matched_expense_id=transaction.matched_expense_id,
        matched_invoice_id=transaction.matched_invoice_id,
        match_confidence=transaction.match_confidence,
        created_at=transaction.created_at,
        updated_at=transaction.updated_at
    )


# ============================================================================
# Bank Import Management Endpoints
# ============================================================================

@router.post("/", response_model=BankImportResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(RATE_LIMITS["upload"])
async def create_bank_import(
    request: Request,
    response: Response,
    file: UploadFile = File(..., description="Bank statement file (CSV or PDF)"),
    source_bank: Optional[str] = Form(None, description="Bank name (e.g., Equity, KCB)"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload and create a new bank import.

    Accepts CSV or PDF bank statement files. The file will be parsed and
    column detection will be attempted automatically.

    Workflow:
    1. File is uploaded and validated (CSV or PDF only)
    2. File is parsed and rows are extracted
    3. Automatic column detection is attempted
    4. Import is created with MAPPING status
    5. User confirms/updates column mapping
    6. User triggers processing to create transactions

    Args:
        file: Bank statement file (CSV or PDF)
        source_bank: Optional bank name for better column detection

    Returns:
        Created BankImport with parsing status and detected columns

    Raises:
        400: Invalid file type or parsing error
        403: User has no business association
    """
    # Ensure user has a business
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a business"
        )

    # Validate file type
    file_type = _validate_file_type(file.filename)

    # Read file content
    try:
        file_content = await file.read()

        if not file_content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty"
            )

        # Check file size (max 10MB)
        if len(file_content) > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size exceeds 10MB limit"
            )

    except Exception as e:
        logger.error(f"Error reading uploaded file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error reading uploaded file"
        )

    # Create import
    bank_import_service = get_bank_import_service(db)

    try:
        bank_import = await bank_import_service.create_import(
            business_id=current_user.business_id,
            file_name=file.filename,
            file_type=file_type,
            file_content=file_content,
            source_bank=source_bank
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating bank import: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process bank statement file"
        )

    return _import_to_response(bank_import)


@router.get("/", response_model=BankImportListResponse)
async def list_bank_imports(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    status_filter: Optional[ImportStatus] = Query(None, alias="status", description="Filter by import status"),
    source_bank: Optional[str] = Query(None, description="Filter by bank name (partial match)"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List bank imports with pagination and filtering.

    Returns all imports for the user's business, ordered by creation date (newest first).

    Filters:
    - status: Filter by import status (pending, parsing, mapping, importing, completed, failed)
    - source_bank: Partial match on bank name

    Returns:
        Paginated list of bank imports with metadata

    Raises:
        403: User has no business association
    """
    # Ensure user has a business
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a business"
        )

    # Get bank import service
    bank_import_service = get_bank_import_service(db)

    # List imports
    imports, total = await bank_import_service.list_imports(
        business_id=current_user.business_id,
        page=page,
        page_size=page_size,
        status=status_filter.value if status_filter else None,
        source_bank=source_bank
    )

    # Convert to response schemas
    import_responses = [_import_to_response(imp) for imp in imports]

    # Calculate total pages
    total_pages = ceil(total / page_size) if total > 0 else 0

    return BankImportListResponse(
        imports=import_responses,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/{import_id}", response_model=BankImportResponse)
async def get_bank_import(
    import_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get details of a specific bank import.

    Returns complete import details including column mapping and status.

    Args:
        import_id: UUID of the bank import

    Returns:
        Bank import details

    Raises:
        403: User has no business association
        404: Import not found or doesn't belong to user's business
    """
    # Ensure user has a business
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a business"
        )

    # Get bank import service
    bank_import_service = get_bank_import_service(db)

    # Get import
    bank_import = await bank_import_service.get_import_by_id(
        import_id=import_id,
        business_id=current_user.business_id
    )

    if not bank_import:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank import not found"
        )

    return _import_to_response(bank_import)


@router.patch("/{import_id}/mapping", response_model=BankImportResponse)
async def update_column_mapping(
    import_id: UUID,
    mapping_data: ColumnMappingRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update column mapping configuration for an import.

    Required before processing the import. Maps CSV/PDF columns to transaction fields.

    Required mappings:
    - date_column: Column containing transaction date
    - description_column: Column containing transaction description
    - At least one of: debit_column or credit_column

    Optional mappings:
    - balance_column: Column containing running balance
    - reference_column: Column containing transaction reference/code

    Args:
        import_id: UUID of the bank import
        mapping_data: Column mapping configuration

    Returns:
        Updated bank import with new mapping

    Raises:
        400: Invalid mapping or import already processed
        403: User has no business association
        404: Import not found
    """
    # Ensure user has a business
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a business"
        )

    # Build mapping dictionary
    mapping = {
        "date": mapping_data.date_column,
        "description": mapping_data.description_column,
    }

    if mapping_data.debit_column:
        mapping["debit"] = mapping_data.debit_column

    if mapping_data.credit_column:
        mapping["credit"] = mapping_data.credit_column

    if mapping_data.balance_column:
        mapping["balance"] = mapping_data.balance_column

    if mapping_data.reference_column:
        mapping["reference"] = mapping_data.reference_column

    # Get bank import service
    bank_import_service = get_bank_import_service(db)

    # Update mapping
    try:
        bank_import = await bank_import_service.update_column_mapping(
            import_id=import_id,
            business_id=current_user.business_id,
            mapping=mapping
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    return _import_to_response(bank_import)


@router.post("/{import_id}/process", response_model=BankImportResponse)
@limiter.limit(RATE_LIMITS["import"])
async def process_bank_import(
    request: Request,
    response: Response,
    import_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Process bank import and create transactions.

    Processes all rows in the import file using the configured column mapping.
    Creates BankTransaction records for each row.

    Prerequisites:
    - Import must have status MAPPING
    - Column mapping must be configured

    After processing:
    - Transactions are created and available for reconciliation
    - Import status changes to COMPLETED (or FAILED if errors occur)

    Args:
        import_id: UUID of the bank import

    Returns:
        Updated bank import with COMPLETED/FAILED status

    Raises:
        400: Import cannot be processed (missing mapping, wrong status)
        403: User has no business association
        404: Import not found
    """
    # Ensure user has a business
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a business"
        )

    # Get bank import service
    bank_import_service = get_bank_import_service(db)

    # Process import
    try:
        bank_import = await bank_import_service.process_import(
            import_id=import_id,
            business_id=current_user.business_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error processing import {import_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process import"
        )

    return _import_to_response(bank_import)


@router.delete("/{import_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bank_import(
    import_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a bank import and all its transactions.

    WARNING: This will permanently delete:
    - The import record
    - All transactions created from this import
    - All reconciliation matches for these transactions

    Cascading deletes are handled by the database.

    Args:
        import_id: UUID of the bank import

    Returns:
        204 No Content on success

    Raises:
        400: Import has matched transactions (should unmatch first)
        403: User has no business association
        404: Import not found
    """
    # Ensure user has a business
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a business"
        )

    # Get bank import service
    bank_import_service = get_bank_import_service(db)

    # Delete import
    try:
        deleted = await bank_import_service.delete_import(
            import_id=import_id,
            business_id=current_user.business_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank import not found"
        )

    return None


# ============================================================================
# Transaction Management Endpoints
# ============================================================================

@router.get("/{import_id}/transactions", response_model=BankTransactionListResponse)
async def list_import_transactions(
    import_id: UUID,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    status_filter: Optional[ReconciliationStatus] = Query(None, alias="status", description="Filter by reconciliation status"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List transactions for a specific import.

    Returns all transactions created from this import, with optional filtering by
    reconciliation status.

    Filters:
    - status: Filter by reconciliation status (unmatched, suggested, matched, ignored)

    Returns:
        Paginated list of bank transactions

    Raises:
        403: User has no business association
        404: Import not found
    """
    # Ensure user has a business
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a business"
        )

    # Verify import exists and belongs to user's business
    bank_import_service = get_bank_import_service(db)
    bank_import = await bank_import_service.get_import_by_id(
        import_id=import_id,
        business_id=current_user.business_id
    )

    if not bank_import:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank import not found"
        )

    # List transactions
    transactions, total = await bank_import_service.list_transactions(
        business_id=current_user.business_id,
        page=page,
        page_size=page_size,
        import_id=import_id,
        status=status_filter.value if status_filter else None
    )

    # Convert to response schemas
    transaction_responses = [_transaction_to_response(txn) for txn in transactions]

    # Calculate total pages
    total_pages = ceil(total / page_size) if total > 0 else 0

    return BankTransactionListResponse(
        transactions=transaction_responses,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/transactions/{transaction_id}", response_model=BankTransactionResponse)
async def get_bank_transaction(
    transaction_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get details of a specific bank transaction.

    Returns complete transaction details including reconciliation status and
    matched records.

    Args:
        transaction_id: UUID of the bank transaction

    Returns:
        Bank transaction details

    Raises:
        403: User has no business association
        404: Transaction not found
    """
    # Ensure user has a business
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a business"
        )

    # Get bank import service
    bank_import_service = get_bank_import_service(db)

    # Get transaction
    transaction = await bank_import_service.get_transaction_by_id(
        transaction_id=transaction_id,
        business_id=current_user.business_id
    )

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )

    return _transaction_to_response(transaction)


# ============================================================================
# Reconciliation Endpoints
# ============================================================================

@router.get("/transactions/{transaction_id}/suggestions", response_model=ReconciliationSuggestion)
async def get_reconciliation_suggestions(
    transaction_id: UUID,
    max_suggestions: int = Query(5, ge=1, le=10, description="Maximum number of suggestions"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get reconciliation suggestions for a transaction.

    Uses fuzzy matching algorithms to find potential matches with expenses or invoices.

    Matching criteria:
    - Amount similarity (exact or within tolerance)
    - Date proximity (within 3 days by default)
    - Description keyword matching
    - Party/vendor name matching

    Each suggestion includes:
    - Match confidence score (0-100)
    - Reasons for the match
    - Record details (date, amount, description)

    Args:
        transaction_id: UUID of the bank transaction
        max_suggestions: Maximum number of suggestions to return (default 5)

    Returns:
        List of suggested matches with confidence scores

    Raises:
        403: User has no business association
        404: Transaction not found
    """
    # Ensure user has a business
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a business"
        )

    # Get bank import service
    bank_import_service = get_bank_import_service(db)

    # Get transaction
    transaction = await bank_import_service.get_transaction_by_id(
        transaction_id=transaction_id,
        business_id=current_user.business_id
    )

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )

    # Get suggestions
    suggestions = await bank_import_service.get_reconciliation_suggestions(
        transaction_id=transaction_id,
        business_id=current_user.business_id,
        max_suggestions=max_suggestions
    )

    # Convert to response schema
    encryption_service = get_encryption_service()
    description = encryption_service.decrypt(transaction.description)

    suggested_matches = [
        ReconciliationMatch(
            record_type=s["record_type"],
            record_id=s["record_id"],
            record_date=s["record_date"],
            record_amount=s["record_amount"],
            record_description=s["record_description"],
            confidence=s["confidence"],
            match_reasons=s["match_reasons"]
        )
        for s in suggestions
    ]

    return ReconciliationSuggestion(
        transaction_id=transaction.id,
        transaction_date=transaction.transaction_date,
        transaction_description=description,
        transaction_amount=transaction.transaction_amount,
        suggested_matches=suggested_matches
    )


@router.post("/transactions/{transaction_id}/match", response_model=BankTransactionResponse)
@limiter.limit(RATE_LIMITS["reconcile"])
async def match_transaction(
    request: Request,
    response: Response,
    transaction_id: UUID,
    match_data: MatchRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Manually confirm a reconciliation match.

    Links a bank transaction with an expense or invoice. This marks the
    transaction as MATCHED and updates the linked record.

    Effects:
    - Transaction status changes to MATCHED
    - Expense is marked as reconciled (if matching with expense)
    - Invoice payment is recorded (if matching with invoice)
    - Match confidence is set to 100 (manual match)

    Args:
        transaction_id: UUID of the bank transaction
        match_data: Match details (record_type and record_id)

    Returns:
        Updated transaction with match details

    Raises:
        400: Transaction already matched or record not found
        403: User has no business association
        404: Transaction not found
    """
    # Ensure user has a business
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a business"
        )

    # Get bank import service
    bank_import_service = get_bank_import_service(db)

    # Match transaction
    try:
        transaction = await bank_import_service.match_transaction(
            transaction_id=transaction_id,
            business_id=current_user.business_id,
            record_type=match_data.record_type,
            record_id=match_data.record_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    return _transaction_to_response(transaction)


@router.delete("/transactions/{transaction_id}/match", response_model=BankTransactionResponse)
async def unmatch_transaction(
    transaction_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Remove a reconciliation match.

    Unlinks a bank transaction from its matched expense or invoice.

    Effects:
    - Transaction status changes to UNMATCHED
    - Matched expense is unmarked as reconciled (if applicable)
    - Match confidence is cleared

    Args:
        transaction_id: UUID of the bank transaction

    Returns:
        Updated transaction with cleared match

    Raises:
        403: User has no business association
        404: Transaction not found
    """
    # Ensure user has a business
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a business"
        )

    # Get bank import service
    bank_import_service = get_bank_import_service(db)

    # Unmatch transaction
    try:
        transaction = await bank_import_service.unmatch_transaction(
            transaction_id=transaction_id,
            business_id=current_user.business_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    return _transaction_to_response(transaction)


@router.post("/transactions/{transaction_id}/ignore", response_model=BankTransactionResponse)
async def ignore_transaction(
    transaction_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Mark a transaction as ignored for reconciliation.

    Use this for transactions that don't need to be reconciled (e.g., bank fees,
    internal transfers, ATM withdrawals).

    Effects:
    - Transaction status changes to IGNORED
    - Transaction will be excluded from unmatched counts

    Args:
        transaction_id: UUID of the bank transaction

    Returns:
        Updated transaction with IGNORED status

    Raises:
        400: Transaction is already matched
        403: User has no business association
        404: Transaction not found
    """
    # Ensure user has a business
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a business"
        )

    # Get bank import service
    bank_import_service = get_bank_import_service(db)

    # Ignore transaction
    try:
        transaction = await bank_import_service.ignore_transaction(
            transaction_id=transaction_id,
            business_id=current_user.business_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    return _transaction_to_response(transaction)


# ============================================================================
# Reconciliation Statistics
# ============================================================================

@router.get("/{import_id}/reconciliation-stats", response_model=ReconciliationStats)
async def get_reconciliation_stats(
    import_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get reconciliation statistics for an import.

    Provides a summary of reconciliation progress including:
    - Total transaction counts by status
    - Matched percentage
    - Total amounts (debit/credit)
    - Matched amounts

    Useful for:
    - Tracking reconciliation progress
    - Identifying unmatched transactions
    - Reporting and auditing

    Args:
        import_id: UUID of the bank import

    Returns:
        Reconciliation statistics summary

    Raises:
        403: User has no business association
        404: Import not found
    """
    # Ensure user has a business
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a business"
        )

    # Verify import exists
    bank_import_service = get_bank_import_service(db)
    bank_import = await bank_import_service.get_import_by_id(
        import_id=import_id,
        business_id=current_user.business_id
    )

    if not bank_import:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank import not found"
        )

    # Get statistics
    stats = await bank_import_service.get_reconciliation_stats(
        import_id=import_id,
        business_id=current_user.business_id
    )

    return stats
