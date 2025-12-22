"""
Bank Import Service

Business logic for bank statement import and transaction reconciliation.
Handles the complete import workflow from file upload to transaction matching.

Features:
- Import creation and management
- Column mapping configuration
- Transaction processing and creation
- Automatic reconciliation matching
- Progress tracking

Security:
- All operations scoped to business_id
- Sensitive fields encrypted (description, reference, raw_data)
- Input validation and sanitization
- Proper error handling
"""

from typing import Optional, Dict, Any, List, Tuple
from uuid import UUID
from datetime import date
from decimal import Decimal
import json
import logging

from sqlalchemy import select, update, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bank_import import BankImport, ImportStatus, FileType
from app.models.bank_transaction import BankTransaction, ReconciliationStatus
from app.models.expense import Expense
from app.models.invoice import Invoice
from app.core.encryption import get_encryption_service
from app.services.document_parser import DocumentParserService

logger = logging.getLogger(__name__)


class BankImportService:
    """Service for bank import database operations."""

    # Reconciliation matching thresholds
    EXACT_MATCH_THRESHOLD = 95.0  # 95% confidence for exact matches
    GOOD_MATCH_THRESHOLD = 80.0   # 80% confidence for good matches
    WEAK_MATCH_THRESHOLD = 60.0   # 60% minimum for suggestions

    # Date tolerance for matching (in days)
    DATE_TOLERANCE_DAYS = 3

    def __init__(self, db: AsyncSession):
        """
        Initialize bank import service.

        Args:
            db: Database session
        """
        self.db = db
        self.encryption_service = get_encryption_service()
        self.parser_service = DocumentParserService()

    async def create_import(
        self,
        business_id: UUID,
        file_name: str,
        file_type: str,
        file_content: bytes,
        source_bank: Optional[str] = None
    ) -> BankImport:
        """
        Create a new bank import and parse the file.

        Args:
            business_id: Business UUID
            file_name: Original filename
            file_type: File type (csv or pdf)
            file_content: Raw file bytes
            source_bank: Optional bank name

        Returns:
            Created BankImport model

        Raises:
            ValueError: If file parsing fails
        """
        # Create import record
        bank_import = BankImport(
            business_id=business_id,
            file_name=file_name,
            file_type=FileType(file_type),
            source_bank=source_bank,
            status=ImportStatus.PENDING,
            total_rows=0,
            imported_rows=0
        )

        self.db.add(bank_import)
        await self.db.commit()
        await self.db.refresh(bank_import)

        try:
            # Update status to parsing
            bank_import.status = ImportStatus.PARSING
            await self.db.commit()

            # Parse file
            if file_type == "csv":
                rows = await self.parser_service.parse_csv(file_content)
            elif file_type == "pdf":
                rows = await self.parser_service.parse_pdf(file_content)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")

            # Encrypt and store raw data for audit
            raw_data_json = json.dumps(rows[:100])  # Store first 100 rows for audit
            bank_import.raw_data_encrypted = self.encryption_service.encrypt(raw_data_json)

            # Update total rows
            bank_import.total_rows = len(rows)

            # Auto-detect columns
            detected = self.parser_service.detect_columns(rows)

            # Build initial column mapping if columns detected with high confidence
            if detected.get("date") and detected["date"]["confidence"] > 70:
                column_mapping = {}

                if detected.get("date"):
                    column_mapping["date"] = detected["date"]["column"]
                if detected.get("description"):
                    column_mapping["description"] = detected["description"]["column"]
                if detected.get("debit"):
                    column_mapping["debit"] = detected["debit"]["column"]
                if detected.get("credit"):
                    column_mapping["credit"] = detected["credit"]["column"]
                if detected.get("balance"):
                    column_mapping["balance"] = detected["balance"]["column"]
                if detected.get("reference"):
                    column_mapping["reference"] = detected["reference"]["column"]

                bank_import.column_mapping = column_mapping
                bank_import.status = ImportStatus.MAPPING
            else:
                # Needs manual column mapping
                bank_import.status = ImportStatus.MAPPING

            await self.db.commit()
            await self.db.refresh(bank_import)

            logger.info(f"Created bank import {bank_import.id} with {len(rows)} rows")
            return bank_import

        except Exception as e:
            # Mark as failed
            bank_import.status = ImportStatus.FAILED
            bank_import.error_message = str(e)
            await self.db.commit()
            logger.error(f"Failed to parse import {bank_import.id}: {str(e)}")
            raise

    async def get_import_by_id(
        self,
        import_id: UUID,
        business_id: UUID
    ) -> Optional[BankImport]:
        """
        Get bank import by ID with business scoping.

        Args:
            import_id: Import UUID
            business_id: Business UUID for security scoping

        Returns:
            BankImport model or None if not found
        """
        result = await self.db.execute(
            select(BankImport).where(
                BankImport.id == import_id,
                BankImport.business_id == business_id
            )
        )
        return result.scalar_one_or_none()

    async def list_imports(
        self,
        business_id: UUID,
        page: int = 1,
        page_size: int = 50,
        status: Optional[str] = None,
        source_bank: Optional[str] = None
    ) -> Tuple[List[BankImport], int]:
        """
        List bank imports with pagination and filtering.

        Args:
            business_id: Business UUID for security scoping
            page: Page number (1-indexed)
            page_size: Number of items per page
            status: Optional filter by status
            source_bank: Optional filter by source bank

        Returns:
            Tuple of (imports list, total count)
        """
        # Build base query
        query = select(BankImport).where(
            BankImport.business_id == business_id
        )

        # Apply filters
        if status:
            query = query.where(BankImport.status == ImportStatus(status))

        if source_bank:
            query = query.where(BankImport.source_bank.ilike(f"%{source_bank}%"))

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        # Order by created_at descending (newest first)
        query = query.order_by(BankImport.created_at.desc())

        # Execute query
        result = await self.db.execute(query)
        imports = result.scalars().all()

        return list(imports), total

    async def update_column_mapping(
        self,
        import_id: UUID,
        business_id: UUID,
        mapping: Dict[str, str]
    ) -> BankImport:
        """
        Update column mapping for an import.

        Args:
            import_id: Import UUID
            business_id: Business UUID for security scoping
            mapping: Column mapping configuration

        Returns:
            Updated BankImport model

        Raises:
            ValueError: If import not found or already processed
        """
        # Get import
        bank_import = await self.get_import_by_id(import_id, business_id)
        if not bank_import:
            raise ValueError("Import not found")

        # Check if can update mapping
        if bank_import.status not in [ImportStatus.PENDING, ImportStatus.MAPPING]:
            raise ValueError(f"Cannot update mapping for import with status: {bank_import.status}")

        # Validate mapping has required fields
        if "date" not in mapping or "description" not in mapping:
            raise ValueError("Mapping must include 'date' and 'description' columns")

        if "debit" not in mapping and "credit" not in mapping:
            raise ValueError("Mapping must include at least one amount column (debit or credit)")

        # Update mapping
        bank_import.column_mapping = mapping
        bank_import.status = ImportStatus.MAPPING

        await self.db.commit()
        await self.db.refresh(bank_import)

        logger.info(f"Updated column mapping for import {import_id}")
        return bank_import

    async def process_import(
        self,
        import_id: UUID,
        business_id: UUID
    ) -> BankImport:
        """
        Process bank import and create transactions.

        Args:
            import_id: Import UUID
            business_id: Business UUID for security scoping

        Returns:
            Updated BankImport model

        Raises:
            ValueError: If import cannot be processed
        """
        # Get import
        bank_import = await self.get_import_by_id(import_id, business_id)
        if not bank_import:
            raise ValueError("Import not found")

        # Check if can process
        if not bank_import.can_process:
            raise ValueError(
                f"Cannot process import with status {bank_import.status} or missing column mapping"
            )

        try:
            # Update status
            bank_import.status = ImportStatus.IMPORTING
            await self.db.commit()

            # Decrypt and parse raw data
            raw_data_json = self.encryption_service.decrypt(bank_import.raw_data_encrypted)
            rows = json.loads(raw_data_json)

            # Process each row
            imported_count = 0
            errors = []

            for idx, row in enumerate(rows):
                try:
                    # Normalize transaction
                    normalized = self.parser_service.normalize_transaction(
                        row,
                        bank_import.column_mapping
                    )

                    # Encrypt sensitive fields
                    encrypted_description = self.encryption_service.encrypt(normalized["description"])
                    encrypted_reference = self.encryption_service.encrypt_optional(normalized.get("reference"))
                    encrypted_raw_data = self.encryption_service.encrypt(json.dumps(normalized["raw_data"]))

                    # Create transaction
                    transaction = BankTransaction(
                        business_id=business_id,
                        bank_import_id=bank_import.id,
                        transaction_date=normalized["transaction_date"],
                        description=encrypted_description,
                        reference=encrypted_reference,
                        debit_amount=normalized.get("debit_amount"),
                        credit_amount=normalized.get("credit_amount"),
                        balance=normalized.get("balance"),
                        raw_data=encrypted_raw_data,
                        reconciliation_status=ReconciliationStatus.UNMATCHED
                    )

                    self.db.add(transaction)
                    imported_count += 1

                    # Commit in batches of 100
                    if imported_count % 100 == 0:
                        await self.db.commit()
                        bank_import.imported_rows = imported_count
                        await self.db.commit()

                except Exception as e:
                    logger.error(f"Error processing row {idx} in import {import_id}: {str(e)}")
                    errors.append(f"Row {idx + 1}: {str(e)}")
                    continue

            # Final commit
            await self.db.commit()

            # Update import status
            bank_import.imported_rows = imported_count
            if errors:
                bank_import.error_message = f"Completed with {len(errors)} errors: " + "; ".join(errors[:5])

            bank_import.status = ImportStatus.COMPLETED
            await self.db.commit()
            await self.db.refresh(bank_import)

            logger.info(f"Processed import {import_id}: {imported_count} transactions created")
            return bank_import

        except Exception as e:
            # Mark as failed
            bank_import.status = ImportStatus.FAILED
            bank_import.error_message = str(e)
            await self.db.commit()
            logger.error(f"Failed to process import {import_id}: {str(e)}")
            raise

    async def list_transactions(
        self,
        business_id: UUID,
        page: int = 1,
        page_size: int = 50,
        import_id: Optional[UUID] = None,
        status: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Tuple[List[BankTransaction], int]:
        """
        List bank transactions with pagination and filtering.

        Args:
            business_id: Business UUID for security scoping
            page: Page number (1-indexed)
            page_size: Number of items per page
            import_id: Optional filter by import
            status: Optional filter by reconciliation status
            start_date: Optional filter by transaction_date >= start_date
            end_date: Optional filter by transaction_date <= end_date

        Returns:
            Tuple of (transactions list, total count)
        """
        # Build base query
        query = select(BankTransaction).where(
            BankTransaction.business_id == business_id
        )

        # Apply filters
        if import_id:
            query = query.where(BankTransaction.bank_import_id == import_id)

        if status:
            query = query.where(BankTransaction.reconciliation_status == ReconciliationStatus(status))

        if start_date:
            query = query.where(BankTransaction.transaction_date >= start_date)

        if end_date:
            query = query.where(BankTransaction.transaction_date <= end_date)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        # Order by transaction_date descending (newest first)
        query = query.order_by(BankTransaction.transaction_date.desc(), BankTransaction.created_at.desc())

        # Execute query
        result = await self.db.execute(query)
        transactions = result.scalars().all()

        return list(transactions), total

    async def get_transaction_by_id(
        self,
        transaction_id: UUID,
        business_id: UUID
    ) -> Optional[BankTransaction]:
        """
        Get bank transaction by ID with business scoping.

        Args:
            transaction_id: Transaction UUID
            business_id: Business UUID for security scoping

        Returns:
            BankTransaction model or None if not found
        """
        result = await self.db.execute(
            select(BankTransaction).where(
                BankTransaction.id == transaction_id,
                BankTransaction.business_id == business_id
            )
        )
        return result.scalar_one_or_none()

    async def get_reconciliation_suggestions(
        self,
        transaction_id: UUID,
        business_id: UUID,
        max_suggestions: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get reconciliation suggestions for a transaction.

        Uses matching algorithms to find potential expense/invoice matches.

        Args:
            transaction_id: Transaction UUID
            business_id: Business UUID
            max_suggestions: Maximum number of suggestions to return

        Returns:
            List of suggestion dictionaries with match details
        """
        # Get transaction
        transaction = await self.get_transaction_by_id(transaction_id, business_id)
        if not transaction:
            return []

        # Decrypt description for matching
        description = self.encryption_service.decrypt(transaction.description)

        # Determine if debit or credit
        is_debit = transaction.is_debit

        suggestions = []

        if is_debit:
            # Match with expenses
            suggestions = await self._match_with_expenses(
                transaction,
                description,
                business_id,
                max_suggestions
            )
        else:
            # Match with invoices (payments)
            suggestions = await self._match_with_invoices(
                transaction,
                description,
                business_id,
                max_suggestions
            )

        return suggestions

    async def _match_with_expenses(
        self,
        transaction: BankTransaction,
        description: str,
        business_id: UUID,
        max_suggestions: int
    ) -> List[Dict[str, Any]]:
        """Match transaction with expenses."""
        from datetime import timedelta

        # Query unreconciled expenses near the transaction date
        date_start = transaction.transaction_date - timedelta(days=self.DATE_TOLERANCE_DAYS)
        date_end = transaction.transaction_date + timedelta(days=self.DATE_TOLERANCE_DAYS)

        result = await self.db.execute(
            select(Expense).where(
                Expense.business_id == business_id,
                Expense.is_active == True,
                Expense.is_reconciled == False,
                Expense.expense_date >= date_start,
                Expense.expense_date <= date_end
            )
        )
        expenses = result.scalars().all()

        matches = []
        for expense in expenses:
            confidence, reasons = self._calculate_match_confidence(
                transaction,
                description,
                expense.expense_date,
                expense.amount,
                expense.description,
                expense.vendor_name
            )

            if confidence >= self.WEAK_MATCH_THRESHOLD:
                matches.append({
                    "record_type": "expense",
                    "record_id": expense.id,
                    "record_date": expense.expense_date,
                    "record_amount": expense.amount,
                    "record_description": expense.description,
                    "confidence": confidence,
                    "match_reasons": reasons
                })

        # Sort by confidence and return top matches
        matches.sort(key=lambda x: x["confidence"], reverse=True)
        return matches[:max_suggestions]

    async def _match_with_invoices(
        self,
        transaction: BankTransaction,
        description: str,
        business_id: UUID,
        max_suggestions: int
    ) -> List[Dict[str, Any]]:
        """Match transaction with invoices (payments)."""
        from datetime import timedelta

        # Query unpaid or partially paid invoices near the transaction date
        date_start = transaction.transaction_date - timedelta(days=self.DATE_TOLERANCE_DAYS)
        date_end = transaction.transaction_date + timedelta(days=self.DATE_TOLERANCE_DAYS)

        result = await self.db.execute(
            select(Invoice).where(
                Invoice.business_id == business_id,
                Invoice.issue_date >= date_start,
                Invoice.issue_date <= date_end,
                Invoice.status.in_(["sent", "partial"])  # Invoices expecting payment
            )
        )
        invoices = result.scalars().all()

        matches = []
        for invoice in invoices:
            # Calculate remaining amount
            remaining = invoice.total_amount - invoice.amount_paid

            confidence, reasons = self._calculate_match_confidence(
                transaction,
                description,
                invoice.issue_date,
                remaining,
                f"Invoice {invoice.invoice_number}",
                invoice.contact.name if hasattr(invoice, 'contact') and invoice.contact else None
            )

            if confidence >= self.WEAK_MATCH_THRESHOLD:
                matches.append({
                    "record_type": "invoice",
                    "record_id": invoice.id,
                    "record_date": invoice.issue_date,
                    "record_amount": remaining,
                    "record_description": f"Invoice {invoice.invoice_number}",
                    "confidence": confidence,
                    "match_reasons": reasons
                })

        # Sort by confidence and return top matches
        matches.sort(key=lambda x: x["confidence"], reverse=True)
        return matches[:max_suggestions]

    def _calculate_match_confidence(
        self,
        transaction: BankTransaction,
        transaction_description: str,
        record_date: date,
        record_amount: Decimal,
        record_description: str,
        record_party: Optional[str]
    ) -> Tuple[Decimal, List[str]]:
        """
        Calculate match confidence score and reasons.

        Returns:
            Tuple of (confidence score 0-100, list of match reasons)
        """
        confidence = Decimal("0.0")
        reasons = []

        transaction_amount = transaction.transaction_amount

        # Amount matching (40 points max)
        if transaction_amount and record_amount:
            amount_diff = abs(transaction_amount - record_amount)
            if amount_diff == 0:
                confidence += Decimal("40.0")
                reasons.append("Exact amount match")
            elif amount_diff <= Decimal("1.0"):
                confidence += Decimal("35.0")
                reasons.append("Very close amount match")
            elif amount_diff / record_amount <= Decimal("0.05"):  # Within 5%
                confidence += Decimal("25.0")
                reasons.append("Close amount match")

        # Date matching (30 points max)
        date_diff = abs((transaction.transaction_date - record_date).days)
        if date_diff == 0:
            confidence += Decimal("30.0")
            reasons.append("Same date")
        elif date_diff == 1:
            confidence += Decimal("25.0")
            reasons.append("1 day difference")
        elif date_diff <= 3:
            confidence += Decimal("20.0")
            reasons.append(f"{date_diff} days difference")

        # Description/party matching (30 points max)
        transaction_desc_lower = transaction_description.lower()
        record_desc_lower = record_description.lower()

        # Check for common keywords
        common_words = set(transaction_desc_lower.split()) & set(record_desc_lower.split())
        if len(common_words) >= 3:
            confidence += Decimal("30.0")
            reasons.append("Multiple matching keywords in description")
        elif len(common_words) >= 2:
            confidence += Decimal("20.0")
            reasons.append("Some matching keywords in description")

        # Check party name match
        if record_party:
            party_lower = record_party.lower()
            if party_lower in transaction_desc_lower:
                confidence += Decimal("15.0")
                reasons.append(f"Description contains '{record_party}'")

        return confidence, reasons

    async def match_transaction(
        self,
        transaction_id: UUID,
        business_id: UUID,
        record_type: str,
        record_id: UUID
    ) -> BankTransaction:
        """
        Manually match a transaction with an expense or invoice.

        Args:
            transaction_id: Transaction UUID
            business_id: Business UUID
            record_type: Type of record ('expense' or 'invoice')
            record_id: Record UUID

        Returns:
            Updated BankTransaction

        Raises:
            ValueError: If transaction or record not found, or already matched
        """
        # Get transaction
        transaction = await self.get_transaction_by_id(transaction_id, business_id)
        if not transaction:
            raise ValueError("Transaction not found")

        if transaction.is_matched:
            raise ValueError("Transaction is already matched")

        # Verify record exists and belongs to business
        if record_type == "expense":
            result = await self.db.execute(
                select(Expense).where(
                    Expense.id == record_id,
                    Expense.business_id == business_id,
                    Expense.is_active == True
                )
            )
            record = result.scalar_one_or_none()
            if not record:
                raise ValueError("Expense not found")

            # Update transaction
            transaction.matched_expense_id = record_id
            transaction.matched_invoice_id = None
            transaction.reconciliation_status = ReconciliationStatus.MATCHED
            transaction.match_confidence = Decimal("100.0")  # Manual match

            # Mark expense as reconciled
            record.is_reconciled = True

        elif record_type == "invoice":
            result = await self.db.execute(
                select(Invoice).where(
                    Invoice.id == record_id,
                    Invoice.business_id == business_id
                )
            )
            record = result.scalar_one_or_none()
            if not record:
                raise ValueError("Invoice not found")

            # Update transaction
            transaction.matched_invoice_id = record_id
            transaction.matched_expense_id = None
            transaction.reconciliation_status = ReconciliationStatus.MATCHED
            transaction.match_confidence = Decimal("100.0")  # Manual match

            # Note: Invoice payment status is managed separately via payments table

        else:
            raise ValueError("record_type must be 'expense' or 'invoice'")

        await self.db.commit()
        await self.db.refresh(transaction)

        logger.info(f"Matched transaction {transaction_id} with {record_type} {record_id}")
        return transaction

    async def unmatch_transaction(
        self,
        transaction_id: UUID,
        business_id: UUID
    ) -> BankTransaction:
        """
        Unmatch a transaction.

        Args:
            transaction_id: Transaction UUID
            business_id: Business UUID

        Returns:
            Updated BankTransaction

        Raises:
            ValueError: If transaction not found
        """
        # Get transaction
        transaction = await self.get_transaction_by_id(transaction_id, business_id)
        if not transaction:
            raise ValueError("Transaction not found")

        # Unmark expense if matched
        if transaction.matched_expense_id:
            result = await self.db.execute(
                select(Expense).where(Expense.id == transaction.matched_expense_id)
            )
            expense = result.scalar_one_or_none()
            if expense:
                expense.is_reconciled = False

        # Clear match
        transaction.matched_expense_id = None
        transaction.matched_invoice_id = None
        transaction.reconciliation_status = ReconciliationStatus.UNMATCHED
        transaction.match_confidence = None

        await self.db.commit()
        await self.db.refresh(transaction)

        logger.info(f"Unmatched transaction {transaction_id}")
        return transaction

    async def ignore_transaction(
        self,
        transaction_id: UUID,
        business_id: UUID
    ) -> BankTransaction:
        """
        Mark a transaction as ignored for reconciliation.

        Args:
            transaction_id: Transaction UUID
            business_id: Business UUID

        Returns:
            Updated BankTransaction

        Raises:
            ValueError: If transaction not found or already matched
        """
        # Get transaction
        transaction = await self.get_transaction_by_id(transaction_id, business_id)
        if not transaction:
            raise ValueError("Transaction not found")

        if transaction.is_matched:
            raise ValueError("Cannot ignore a matched transaction. Unmatch it first.")

        # Update status
        transaction.reconciliation_status = ReconciliationStatus.IGNORED
        transaction.match_confidence = None

        await self.db.commit()
        await self.db.refresh(transaction)

        logger.info(f"Ignored transaction {transaction_id}")
        return transaction

    async def delete_import(
        self,
        import_id: UUID,
        business_id: UUID
    ) -> bool:
        """
        Delete a bank import and all its transactions.

        Args:
            import_id: Import UUID
            business_id: Business UUID for security scoping

        Returns:
            True if deleted, False if not found

        Raises:
            ValueError: If import has matched transactions
        """
        # Get import
        bank_import = await self.get_import_by_id(import_id, business_id)
        if not bank_import:
            return False

        # Check if any transactions are matched
        result = await self.db.execute(
            select(func.count()).select_from(BankTransaction).where(
                BankTransaction.bank_import_id == import_id,
                BankTransaction.reconciliation_status == ReconciliationStatus.MATCHED
            )
        )
        matched_count = result.scalar()

        if matched_count > 0:
            raise ValueError(
                f"Cannot delete import with {matched_count} matched transactions. "
                "Unmatch them first."
            )

        # Delete import (transactions will be cascade deleted)
        await self.db.delete(bank_import)
        await self.db.commit()

        logger.info(f"Deleted bank import {import_id} and its transactions")
        return True

    async def get_reconciliation_stats(
        self,
        import_id: UUID,
        business_id: UUID
    ) -> Dict[str, Any]:
        """
        Get reconciliation statistics for an import.

        Args:
            import_id: Import UUID
            business_id: Business UUID

        Returns:
            Dictionary with reconciliation statistics
        """
        from sqlalchemy import case

        # Query transaction counts by status
        result = await self.db.execute(
            select(
                func.count().label("total"),
                func.sum(
                    case((BankTransaction.reconciliation_status == ReconciliationStatus.MATCHED, 1), else_=0)
                ).label("matched"),
                func.sum(
                    case((BankTransaction.reconciliation_status == ReconciliationStatus.SUGGESTED, 1), else_=0)
                ).label("suggested"),
                func.sum(
                    case((BankTransaction.reconciliation_status == ReconciliationStatus.UNMATCHED, 1), else_=0)
                ).label("unmatched"),
                func.sum(
                    case((BankTransaction.reconciliation_status == ReconciliationStatus.IGNORED, 1), else_=0)
                ).label("ignored"),
                func.sum(
                    case((BankTransaction.debit_amount.isnot(None), BankTransaction.debit_amount), else_=0)
                ).label("total_debit"),
                func.sum(
                    case((BankTransaction.credit_amount.isnot(None), BankTransaction.credit_amount), else_=0)
                ).label("total_credit"),
                func.sum(
                    case(
                        (
                            and_(
                                BankTransaction.reconciliation_status == ReconciliationStatus.MATCHED,
                                BankTransaction.debit_amount.isnot(None)
                            ),
                            BankTransaction.debit_amount
                        ),
                        else_=0
                    )
                ).label("matched_debit"),
                func.sum(
                    case(
                        (
                            and_(
                                BankTransaction.reconciliation_status == ReconciliationStatus.MATCHED,
                                BankTransaction.credit_amount.isnot(None)
                            ),
                            BankTransaction.credit_amount
                        ),
                        else_=0
                    )
                ).label("matched_credit")
            ).where(
                BankTransaction.bank_import_id == import_id,
                BankTransaction.business_id == business_id
            )
        )

        stats = result.one()

        total = stats.total or 0
        matched = stats.matched or 0
        suggested = stats.suggested or 0
        unmatched = stats.unmatched or 0
        ignored = stats.ignored or 0

        matched_percentage = (matched / total * 100.0) if total > 0 else 0.0

        return {
            "total_transactions": total,
            "matched_count": matched,
            "suggested_count": suggested,
            "unmatched_count": unmatched,
            "ignored_count": ignored,
            "matched_percentage": round(matched_percentage, 2),
            "total_debit_amount": stats.total_debit or Decimal("0.00"),
            "total_credit_amount": stats.total_credit or Decimal("0.00"),
            "matched_debit_amount": stats.matched_debit or Decimal("0.00"),
            "matched_credit_amount": stats.matched_credit or Decimal("0.00")
        }


def get_bank_import_service(db: AsyncSession) -> BankImportService:
    """
    Get bank import service instance.

    Args:
        db: Database session

    Returns:
        BankImportService instance
    """
    return BankImportService(db)
