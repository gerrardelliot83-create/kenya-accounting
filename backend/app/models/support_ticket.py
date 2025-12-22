"""
Support Ticket Model

Customer support ticket management system.
Tracks support requests from creation to resolution.

Ticket Workflow:
1. open: New ticket created by customer
2. in_progress: Agent working on ticket
3. waiting_customer: Awaiting customer response
4. resolved: Issue resolved, awaiting confirmation
5. closed: Ticket closed and archived

Ticket Categories:
- billing: Billing and payment issues
- technical: Technical problems and bugs
- feature_request: Feature suggestions
- general: General inquiries

Priority Levels:
- low: Non-urgent, informational
- medium: Standard support request
- high: Business-impacting issue
- urgent: Critical business blocker
"""

import enum
from sqlalchemy import Column, String, Text, ForeignKey, Index, DateTime, Integer, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class TicketCategory(str, enum.Enum):
    """Support ticket category enumeration."""
    BILLING = "billing"
    TECHNICAL = "technical"
    FEATURE_REQUEST = "feature_request"
    GENERAL = "general"


class TicketPriority(str, enum.Enum):
    """Support ticket priority enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TicketStatus(str, enum.Enum):
    """Support ticket status enumeration."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_CUSTOMER = "waiting_customer"
    RESOLVED = "resolved"
    CLOSED = "closed"


class SupportTicket(Base):
    """
    Support ticket model for customer support management.

    Features:
    - Unique ticket numbering (TKT-YYYY-NNNNN)
    - Category and priority classification
    - Status workflow tracking
    - Agent assignment
    - Resolution tracking
    - Customer satisfaction rating

    Business Scoping:
    - Tickets belong to a specific business
    - Created by a specific user
    - Queries must filter by business_id for security

    Agent Assignment:
    - Tickets can be assigned to support agents
    - Assignment tracked for workload management
    """

    # Business and user association
    business_id = Column(
        UUID(as_uuid=True),
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Associated business"
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="User who created the ticket"
    )

    # Ticket identification
    ticket_number = Column(
        String(20),
        nullable=False,
        unique=True,
        index=True,
        comment="Unique ticket number (TKT-YYYY-NNNNN format)"
    )

    # Ticket details
    subject = Column(
        String(500),
        nullable=False,
        comment="Ticket subject/title"
    )

    description = Column(
        Text,
        nullable=False,
        comment="Detailed description of the issue"
    )

    # Classification
    category = Column(
        SQLEnum(TicketCategory, name="ticket_category_enum", create_type=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True,
        comment="Ticket category: billing, technical, feature_request, general"
    )

    priority = Column(
        SQLEnum(TicketPriority, name="ticket_priority_enum", create_type=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=TicketPriority.MEDIUM,
        index=True,
        comment="Ticket priority: low, medium, high, urgent"
    )

    status = Column(
        SQLEnum(TicketStatus, name="ticket_status_enum", create_type=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=TicketStatus.OPEN,
        index=True,
        comment="Ticket status: open, in_progress, waiting_customer, resolved, closed"
    )

    # Assignment
    assigned_agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Support agent assigned to ticket"
    )

    # Resolution tracking
    resolved_at = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="Timestamp when ticket was resolved"
    )

    # Customer satisfaction
    satisfaction_rating = Column(
        Integer,
        nullable=True,
        comment="Customer satisfaction rating (1-5 stars)"
    )

    # Relationships
    business = relationship(
        "Business",
        backref="support_tickets",
        foreign_keys=[business_id]
    )

    creator = relationship(
        "User",
        backref="created_tickets",
        foreign_keys=[user_id]
    )

    assigned_agent = relationship(
        "User",
        backref="assigned_tickets",
        foreign_keys=[assigned_agent_id]
    )

    messages = relationship(
        "TicketMessage",
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="TicketMessage.created_at"
    )

    # Indexes for common queries
    __table_args__ = (
        Index('ix_support_tickets_business_status', 'business_id', 'status'),
        Index('ix_support_tickets_business_priority', 'business_id', 'priority'),
        Index('ix_support_tickets_agent_status', 'assigned_agent_id', 'status'),
        Index('ix_support_tickets_status_priority', 'status', 'priority'),
        Index('ix_support_tickets_business_created', 'business_id', 'created_at'),
        Index('ix_support_tickets_category_status', 'category', 'status'),
    )

    def __repr__(self) -> str:
        return f"<SupportTicket(id={self.id}, number={self.ticket_number}, status={self.status}, priority={self.priority})>"

    @property
    def is_open(self) -> bool:
        """Check if ticket is still open."""
        return self.status in [TicketStatus.OPEN, TicketStatus.IN_PROGRESS, TicketStatus.WAITING_CUSTOMER]

    @property
    def is_resolved(self) -> bool:
        """Check if ticket is resolved or closed."""
        return self.status in [TicketStatus.RESOLVED, TicketStatus.CLOSED]

    @property
    def is_assigned(self) -> bool:
        """Check if ticket is assigned to an agent."""
        return self.assigned_agent_id is not None

    @property
    def is_high_priority(self) -> bool:
        """Check if ticket has high or urgent priority."""
        return self.priority in [TicketPriority.HIGH, TicketPriority.URGENT]

    @property
    def message_count(self) -> int:
        """Get count of messages in this ticket."""
        return len(self.messages) if self.messages else 0

    @property
    def has_rating(self) -> bool:
        """Check if customer has provided satisfaction rating."""
        return self.satisfaction_rating is not None

    def validate_rating(self) -> bool:
        """Validate satisfaction rating is between 1-5."""
        if self.satisfaction_rating is None:
            return True
        return 1 <= self.satisfaction_rating <= 5
