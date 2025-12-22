"""
Document Parser Service

Parses bank statements from CSV and PDF formats.
Provides automatic column detection for mapping configuration.

Features:
- CSV parsing with encoding detection
- PDF parsing using LlamaParse for table extraction
- Automatic column detection using heuristics
- Data normalization and validation
- Support for various bank statement formats

Security:
- Input validation for file content
- Size limits to prevent DoS
- Safe parsing with error handling
"""

import csv
import io
import re
from typing import List, Dict, Optional, Any
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
import logging

# PDF parsing
try:
    from llama_cloud_services import LlamaParse
    LLAMAPARSE_AVAILABLE = True
except ImportError:
    LLAMAPARSE_AVAILABLE = False

from app.config import get_settings

logger = logging.getLogger(__name__)


class DocumentParserService:
    """
    Service for parsing bank statement documents (CSV and PDF).

    Provides:
    - CSV parsing with automatic delimiter detection
    - PDF parsing using LlamaParse for table extraction
    - Column detection using heuristics
    - Data normalization
    """

    # Maximum file size: 10MB
    MAX_FILE_SIZE = 10 * 1024 * 1024

    # Common date formats used in Kenya bank statements
    DATE_FORMATS = [
        "%d/%m/%Y",      # 31/12/2025
        "%d-%m-%Y",      # 31-12-2025
        "%Y-%m-%d",      # 2025-12-31
        "%d %b %Y",      # 31 Dec 2025
        "%d %B %Y",      # 31 December 2025
        "%d.%m.%Y",      # 31.12.2025
        "%m/%d/%Y",      # 12/31/2025
    ]

    # Keywords for column detection
    DATE_KEYWORDS = [
        "date", "transaction date", "value date", "posting date", "txn date", "trans date"
    ]

    DESCRIPTION_KEYWORDS = [
        "description", "details", "particulars", "narration", "transaction details",
        "transaction description", "remarks", "narrative"
    ]

    DEBIT_KEYWORDS = [
        "debit", "withdrawal", "withdrawals", "debit amount", "dr", "debits",
        "money out", "paid out", "payments"
    ]

    CREDIT_KEYWORDS = [
        "credit", "deposit", "deposits", "credit amount", "cr", "credits",
        "money in", "received", "receipts"
    ]

    BALANCE_KEYWORDS = [
        "balance", "running balance", "account balance", "balance amount", "bal"
    ]

    REFERENCE_KEYWORDS = [
        "reference", "ref", "transaction ref", "ref no", "reference number",
        "transaction id", "txn ref", "receipt no"
    ]

    def __init__(self):
        """Initialize document parser service."""
        self.settings = get_settings()
        self._llama_parser: Optional[Any] = None

    def _get_llama_parser(self) -> Any:
        """
        Get or create LlamaParse instance.

        Returns:
            LlamaParse instance

        Raises:
            ValueError: If LlamaParse is not available or API key not configured
        """
        if not LLAMAPARSE_AVAILABLE:
            raise ValueError("LlamaParse library not installed. Run: pip install llama-cloud-services")

        if not self.settings.llama_cloud_api_key:
            raise ValueError("LLAMA_CLOUD_API_KEY not configured in environment")

        if self._llama_parser is None:
            self._llama_parser = LlamaParse(
                api_key=self.settings.llama_cloud_api_key,
                preset="agentic_plus"  # Best preset for table extraction
            )

        return self._llama_parser

    async def parse_csv(self, file_content: bytes) -> List[Dict[str, str]]:
        """
        Parse CSV file content.

        Args:
            file_content: Raw CSV file bytes

        Returns:
            List of dictionaries (one per row, keys are column headers)

        Raises:
            ValueError: If file is invalid or too large
        """
        # Check file size
        if len(file_content) > self.MAX_FILE_SIZE:
            raise ValueError(f"File too large. Maximum size: {self.MAX_FILE_SIZE / 1024 / 1024}MB")

        try:
            # Decode content with various encodings
            text_content = None
            for encoding in ['utf-8', 'utf-8-sig', 'latin-1', 'iso-8859-1', 'cp1252']:
                try:
                    text_content = file_content.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue

            if text_content is None:
                raise ValueError("Unable to decode file. Please ensure it's a valid CSV file.")

            # Detect CSV dialect
            sample = text_content[:4096]
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=',;\t|')
            except csv.Error:
                # Default to comma-separated
                dialect = csv.excel

            # Parse CSV
            csv_reader = csv.DictReader(io.StringIO(text_content), dialect=dialect)

            rows = []
            for row_num, row in enumerate(csv_reader, start=1):
                # Skip empty rows
                if not any(value.strip() for value in row.values() if value):
                    continue

                # Clean up row data
                cleaned_row = {
                    key.strip(): value.strip() if value else ""
                    for key, value in row.items()
                    if key  # Skip unnamed columns
                }

                rows.append(cleaned_row)

                # Safety limit: max 10,000 rows
                if row_num > 10000:
                    raise ValueError("CSV file too large. Maximum 10,000 rows allowed.")

            if not rows:
                raise ValueError("CSV file contains no data rows")

            logger.info(f"Successfully parsed CSV with {len(rows)} rows")
            return rows

        except csv.Error as e:
            raise ValueError(f"CSV parsing error: {str(e)}")
        except Exception as e:
            logger.error(f"Error parsing CSV: {str(e)}")
            raise ValueError(f"Failed to parse CSV file: {str(e)}")

    async def parse_pdf(self, file_content: bytes) -> List[Dict[str, str]]:
        """
        Parse PDF file content using LlamaParse.

        Args:
            file_content: Raw PDF file bytes

        Returns:
            List of dictionaries (one per row, keys are column headers)

        Raises:
            ValueError: If file is invalid, too large, or LlamaParse fails
        """
        # Check file size
        if len(file_content) > self.MAX_FILE_SIZE:
            raise ValueError(f"File too large. Maximum size: {self.MAX_FILE_SIZE / 1024 / 1024}MB")

        try:
            # Get LlamaParse instance
            parser = self._get_llama_parser()

            # Parse PDF - LlamaParse expects file-like object or path
            # For bytes, we need to create a temporary file-like object
            pdf_file = io.BytesIO(file_content)
            pdf_file.name = "statement.pdf"  # LlamaParse may use this

            # Parse the document
            documents = await parser.aparse(pdf_file)

            if not documents or len(documents) == 0:
                raise ValueError("No tables found in PDF")

            # Extract table data from parsed document
            # LlamaParse returns structured data - we need to convert to our format
            rows = []

            for doc in documents:
                # The parsed content should contain table data
                # This is a simplified version - actual implementation depends on LlamaParse output format
                if hasattr(doc, 'table_data'):
                    table_data = doc.table_data
                    if table_data and len(table_data) > 0:
                        # First row is typically headers
                        headers = table_data[0]

                        # Remaining rows are data
                        for row in table_data[1:]:
                            if len(row) == len(headers):
                                row_dict = {
                                    str(headers[i]).strip(): str(row[i]).strip()
                                    for i in range(len(headers))
                                }
                                rows.append(row_dict)

            if not rows:
                raise ValueError("No transaction data extracted from PDF")

            logger.info(f"Successfully parsed PDF with {len(rows)} rows")
            return rows

        except Exception as e:
            logger.error(f"Error parsing PDF: {str(e)}")
            raise ValueError(f"Failed to parse PDF file: {str(e)}")

    def detect_columns(self, rows: List[Dict[str, str]]) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Automatically detect column mappings using heuristics.

        Args:
            rows: Parsed rows from CSV/PDF

        Returns:
            Dictionary with detected columns and confidence scores

        Example:
            {
                "date": {"column": "Transaction Date", "confidence": 95, "samples": [...]},
                "description": {"column": "Details", "confidence": 90, "samples": [...]},
                ...
            }
        """
        if not rows or len(rows) == 0:
            return {}

        # Get all column names
        all_columns = list(rows[0].keys())

        # Sample rows for detection (use first 10 rows)
        sample_rows = rows[:min(10, len(rows))]

        result = {
            "date": self._detect_date_column(all_columns, sample_rows),
            "description": self._detect_description_column(all_columns, sample_rows),
            "debit": self._detect_amount_column(all_columns, sample_rows, self.DEBIT_KEYWORDS),
            "credit": self._detect_amount_column(all_columns, sample_rows, self.CREDIT_KEYWORDS),
            "balance": self._detect_amount_column(all_columns, sample_rows, self.BALANCE_KEYWORDS),
            "reference": self._detect_text_column(all_columns, sample_rows, self.REFERENCE_KEYWORDS),
            "all_columns": all_columns
        }

        logger.info(f"Column detection completed: {result}")
        return result

    def _detect_date_column(
        self,
        columns: List[str],
        sample_rows: List[Dict[str, str]]
    ) -> Optional[Dict[str, Any]]:
        """Detect date column."""
        best_match = None
        best_confidence = 0

        for col in columns:
            col_lower = col.lower()

            # Check if column name matches keywords
            name_score = 0
            for keyword in self.DATE_KEYWORDS:
                if keyword in col_lower:
                    name_score = 80
                    break

            # Check if values look like dates
            date_count = 0
            sample_values = []

            for row in sample_rows:
                value = row.get(col, "").strip()
                if value and self._is_date(value):
                    date_count += 1
                    sample_values.append(value)

            value_score = (date_count / len(sample_rows)) * 100 if sample_rows else 0

            # Combined confidence
            confidence = (name_score * 0.4) + (value_score * 0.6)

            if confidence > best_confidence:
                best_confidence = confidence
                best_match = {
                    "column": col,
                    "confidence": round(confidence, 2),
                    "samples": sample_values[:5]
                }

        return best_match if best_confidence > 50 else None

    def _detect_description_column(
        self,
        columns: List[str],
        sample_rows: List[Dict[str, str]]
    ) -> Optional[Dict[str, Any]]:
        """Detect description column."""
        best_match = None
        best_confidence = 0

        for col in columns:
            col_lower = col.lower()

            # Check if column name matches keywords
            name_score = 0
            for keyword in self.DESCRIPTION_KEYWORDS:
                if keyword in col_lower:
                    name_score = 80
                    break

            # Check if values look like descriptions (longer text)
            text_count = 0
            sample_values = []

            for row in sample_rows:
                value = row.get(col, "").strip()
                if value and len(value) > 10 and not self._is_number(value):
                    text_count += 1
                    sample_values.append(value)

            value_score = (text_count / len(sample_rows)) * 100 if sample_rows else 0

            # Combined confidence
            confidence = (name_score * 0.5) + (value_score * 0.5)

            if confidence > best_confidence:
                best_confidence = confidence
                best_match = {
                    "column": col,
                    "confidence": round(confidence, 2),
                    "samples": sample_values[:5]
                }

        return best_match if best_confidence > 50 else None

    def _detect_amount_column(
        self,
        columns: List[str],
        sample_rows: List[Dict[str, str]],
        keywords: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Detect amount column (debit, credit, or balance)."""
        best_match = None
        best_confidence = 0

        for col in columns:
            col_lower = col.lower()

            # Check if column name matches keywords
            name_score = 0
            for keyword in keywords:
                if keyword in col_lower:
                    name_score = 80
                    break

            # Check if values look like numbers/amounts
            amount_count = 0
            sample_values = []

            for row in sample_rows:
                value = row.get(col, "").strip()
                if value and self._is_amount(value):
                    amount_count += 1
                    sample_values.append(value)

            value_score = (amount_count / len(sample_rows)) * 100 if sample_rows else 0

            # Combined confidence
            confidence = (name_score * 0.5) + (value_score * 0.5)

            if confidence > best_confidence:
                best_confidence = confidence
                best_match = {
                    "column": col,
                    "confidence": round(confidence, 2),
                    "samples": sample_values[:5]
                }

        return best_match if best_confidence > 50 else None

    def _detect_text_column(
        self,
        columns: List[str],
        sample_rows: List[Dict[str, str]],
        keywords: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Detect text column (like reference)."""
        best_match = None
        best_confidence = 0

        for col in columns:
            col_lower = col.lower()

            # Check if column name matches keywords
            name_score = 0
            for keyword in keywords:
                if keyword in col_lower:
                    name_score = 90
                    break

            if name_score > best_confidence:
                sample_values = [
                    row.get(col, "").strip()
                    for row in sample_rows[:5]
                    if row.get(col, "").strip()
                ]

                best_confidence = name_score
                best_match = {
                    "column": col,
                    "confidence": round(name_score, 2),
                    "samples": sample_values
                }

        return best_match if best_confidence > 50 else None

    def normalize_transaction(self, row: Dict[str, str], mapping: Dict[str, str]) -> Dict[str, Any]:
        """
        Normalize a transaction row using the provided column mapping.

        Args:
            row: Raw row data
            mapping: Column mapping configuration

        Returns:
            Normalized transaction data

        Raises:
            ValueError: If required fields are missing or invalid
        """
        try:
            # Extract and normalize date
            date_value = row.get(mapping.get("date", ""), "").strip()
            transaction_date = self._parse_date(date_value)
            if not transaction_date:
                raise ValueError(f"Invalid or missing date: {date_value}")

            # Extract description
            description = row.get(mapping.get("description", ""), "").strip()
            if not description:
                raise ValueError("Description is required")

            # Extract amounts
            debit_col = mapping.get("debit")
            credit_col = mapping.get("credit")
            balance_col = mapping.get("balance")
            reference_col = mapping.get("reference")

            debit_amount = None
            if debit_col:
                debit_value = row.get(debit_col, "").strip()
                if debit_value:
                    debit_amount = self._parse_amount(debit_value)

            credit_amount = None
            if credit_col:
                credit_value = row.get(credit_col, "").strip()
                if credit_value:
                    credit_amount = self._parse_amount(credit_value)

            balance = None
            if balance_col:
                balance_value = row.get(balance_col, "").strip()
                if balance_value:
                    balance = self._parse_amount(balance_value)

            reference = None
            if reference_col:
                reference = row.get(reference_col, "").strip() or None

            return {
                "transaction_date": transaction_date,
                "description": description,
                "reference": reference,
                "debit_amount": debit_amount,
                "credit_amount": credit_amount,
                "balance": balance,
                "raw_data": row  # Keep original data
            }

        except Exception as e:
            logger.error(f"Error normalizing transaction: {str(e)}")
            raise ValueError(f"Failed to normalize transaction: {str(e)}")

    def _is_date(self, value: str) -> bool:
        """Check if value looks like a date."""
        return self._parse_date(value) is not None

    def _parse_date(self, value: str) -> Optional[date]:
        """Parse date from string."""
        if not value:
            return None

        value = value.strip()

        for fmt in self.DATE_FORMATS:
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue

        return None

    def _is_number(self, value: str) -> bool:
        """Check if value looks like a number."""
        try:
            float(value.replace(',', '').replace(' ', ''))
            return True
        except (ValueError, AttributeError):
            return False

    def _is_amount(self, value: str) -> bool:
        """Check if value looks like a monetary amount."""
        return self._parse_amount(value) is not None

    def _parse_amount(self, value: str) -> Optional[Decimal]:
        """Parse amount from string."""
        if not value:
            return None

        try:
            # Remove common formatting
            cleaned = value.strip()

            # Remove currency symbols
            cleaned = re.sub(r'[KSh$€£¥]', '', cleaned)

            # Remove spaces
            cleaned = cleaned.replace(' ', '')

            # Handle parentheses (negative numbers)
            if cleaned.startswith('(') and cleaned.endswith(')'):
                cleaned = '-' + cleaned[1:-1]

            # Remove commas (thousand separators)
            cleaned = cleaned.replace(',', '')

            # Parse as decimal
            amount = Decimal(cleaned)
            return amount if amount >= 0 else None  # Bank statements typically show absolute values

        except (ValueError, InvalidOperation, AttributeError):
            return None


def get_document_parser_service() -> DocumentParserService:
    """
    Get document parser service instance.

    Returns:
        DocumentParserService instance
    """
    return DocumentParserService()
