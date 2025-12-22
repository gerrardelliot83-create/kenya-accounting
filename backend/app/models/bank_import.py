"""
Bank Import Model

Represents bank statement imports for transaction reconciliation.
Supports CSV and PDF file formats with column mapping configuration.

Import Workflow:
1. pending: File uploaded, awaiting parsing
2. parsing: File is being parsed
3. mapping: Column mapping being configured
4. importing: Transactions being created
5. completed: Import successful
6. failed: Import failed with error

Security:
- Raw data is encrypted for audit purposes
- All operations scoped to business_id
- Status transitions tracked for audit trail
"""

from sqlalchemy import Column, String, Text, Integer, ForeignKey, Index, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
import enum

from app.db.base import Base


class FileType(str, enum.Enum):
    """Bank statement file type enumeration."""
    CSV = "csv"
    PDF = "pdf"


class ImportStatus(str, enum.Enum):
    """Bank import status enumeration."""
    PENDING = "pending"
    PARSING = "parsing"
    MAPPING = "mapping"
    IMPORTING = "importing"
    COMPLETED = "completed"
    FAILED = "failed"


class BankImport(Base):
    """
    Bank import model for tracking bank statement uploads.

    Features:
    - Supports CSV and PDF file formats
    - Configurable column mapping
    - Status tracking through import lifecycle
    - Encrypted raw data storage for audit
    - Progress tracking (total vs imported rows)
    - Error message capture for failed imports

    Business Scoping:
    - All imports belong to a specific business
    - Queries must filter by business_id for security

    Encryption:
    - raw_data_encrypted: Encrypted parsed file content for audit trail
    """

    # Business association
    business_id = Column(
        UUID(as_uuid=True),
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Associated business"
    )

    # File information
    file_name = Column(
        String(255),
        nullable=False,
        comment="Original uploaded filename"
    )

    file_type = Column(
        SQLEnum(FileType, name="file_type_enum", create_type=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True,
        comment="File format: csv or pdf"
    )

    source_bank = Column(
        String(100),
        nullable=True,
        index=True,
        comment="Bank name (e.g., Equity, KCB, M-Pesa)"
    )

    # Import status and progress
    status = Column(
        SQLEnum(ImportStatus, name="import_status_enum", create_type=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=ImportStatus.PENDING,
        index=True,
        comment="Current import status"
    )

    column_mapping = Column(
        JSON,
        nullable=True,
        comment="JSON mapping of file columns to our fields"
    )

    total_rows = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Total number of rows in file"
    )

    imported_rows = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of rows successfully imported"
    )

    # Error tracking
    error_message = Column(
        Text,
        nullable=True,
        comment="Error message if import failed"
    )

    # Encrypted audit data
    raw_data_encrypted = Column(
        Text,
        nullable=True,
        comment="Encrypted raw parsed content for audit trail"
    )

    # Relationships
    business = relationship(
        "Business",
        backref="bank_imports",
        foreign_keys=[business_id]
    )

    transactions = relationship(
        "BankTransaction",
        back_populates="bank_import",
        cascade="all, delete-orphan"
    )

    # Indexes for common queries
    __table_args__ = (
        Index('ix_bank_imports_business_status', 'business_id', 'status'),
        Index('ix_bank_imports_business_bank', 'business_id', 'source_bank'),
        Index('ix_bank_imports_created', 'created_at'),
    )

    def __repr__(self) -> str:
        return f"<BankImport(id={self.id}, file={self.file_name}, status={self.status}, rows={self.imported_rows}/{self.total_rows})>"

    @property
    def import_progress(self) -> float:
        """Calculate import progress percentage."""
        if self.total_rows == 0:
            return 0.0
        return round((self.imported_rows / self.total_rows) * 100, 2)

    @property
    def is_complete(self) -> bool:
        """Check if import is completed."""
        return self.status == ImportStatus.COMPLETED

    @property
    def is_failed(self) -> bool:
        """Check if import has failed."""
        return self.status == ImportStatus.FAILED

    @property
    def can_process(self) -> bool:
        """Check if import can be processed."""
        return self.status in [ImportStatus.PENDING, ImportStatus.MAPPING] and self.column_mapping is not None
