"""
Ticket Message Model

Messages and conversation thread for support tickets.
Supports both customer and agent messages with attachments.

Message Types:
- customer: Message from the customer
- agent: Message from support agent

Features:
- Chronological message threading
- File attachments support (JSONB)
- Internal notes (visible only to agents)
- Sender tracking
- Timestamp tracking

Internal Notes:
- is_internal flag allows agents to add notes not visible to customers
- Useful for collaboration between support team members
"""

import enum
from sqlalchemy import Column, String, Text, ForeignKey, Index, Boolean, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.db.base import Base


class SenderType(str, enum.Enum):
    """Message sender type enumeration."""
    CUSTOMER = "customer"
    AGENT = "agent"


class TicketMessage(Base):
    """
    Ticket message model for support ticket conversations.

    Features:
    - Chronological message threading
    - Customer and agent message differentiation
    - File attachment support (stored as JSONB)
    - Internal notes for agent collaboration
    - Sender tracking

    Business Scoping:
    - Messages belong to tickets which belong to businesses
    - Access controlled through ticket ownership

    Attachments Format:
    [
        {
            "name": "screenshot.png",
            "url": "https://storage.example.com/...",
            "type": "image/png",
            "size": 12345
        }
    ]
    """

    # Ticket association
    ticket_id = Column(
        UUID(as_uuid=True),
        ForeignKey("support_tickets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Associated support ticket"
    )

    # Sender information
    sender_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="User who sent the message"
    )

    sender_type = Column(
        SQLEnum(SenderType, name="sender_type_enum", create_type=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True,
        comment="Sender type: customer or agent"
    )

    # Message content
    message = Column(
        Text,
        nullable=False,
        comment="Message content"
    )

    # Attachments
    attachments = Column(
        JSONB,
        nullable=True,
        comment="Attachment metadata array: [{name, url, type, size}]"
    )

    # Internal notes flag
    is_internal = Column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
        comment="Internal note (not visible to customer)"
    )

    # Relationships
    ticket = relationship(
        "SupportTicket",
        back_populates="messages"
    )

    sender = relationship(
        "User",
        backref="ticket_messages",
        foreign_keys=[sender_id]
    )

    # Indexes for common queries
    __table_args__ = (
        Index('ix_ticket_messages_ticket_created', 'ticket_id', 'created_at'),
        Index('ix_ticket_messages_ticket_internal', 'ticket_id', 'is_internal'),
        Index('ix_ticket_messages_sender_type', 'sender_id', 'sender_type'),
    )

    def __repr__(self) -> str:
        return f"<TicketMessage(id={self.id}, ticket_id={self.ticket_id}, sender_type={self.sender_type}, internal={self.is_internal})>"

    @property
    def has_attachments(self) -> bool:
        """Check if message has attachments."""
        return self.attachments is not None and len(self.attachments) > 0

    @property
    def attachment_count(self) -> int:
        """Get count of attachments."""
        if not self.has_attachments:
            return 0
        return len(self.attachments)

    @property
    def is_from_customer(self) -> bool:
        """Check if message is from customer."""
        return self.sender_type == SenderType.CUSTOMER

    @property
    def is_from_agent(self) -> bool:
        """Check if message is from agent."""
        return self.sender_type == SenderType.AGENT

    @property
    def is_visible_to_customer(self) -> bool:
        """Check if message is visible to customer."""
        return not self.is_internal

    def get_attachment_urls(self) -> list:
        """Get list of attachment URLs."""
        if not self.has_attachments:
            return []
        return [att.get('url') for att in self.attachments if att.get('url')]

    def validate_attachments(self) -> bool:
        """Validate attachment structure."""
        if not self.attachments:
            return True

        required_fields = ['name', 'url', 'type']
        for attachment in self.attachments:
            if not all(field in attachment for field in required_fields):
                return False
        return True
