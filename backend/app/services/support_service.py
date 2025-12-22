"""
Support Service

Business logic for support ticket management operations.
Handles ticket CRUD, messaging, assignment, and statistics.

Security Notes:
- All ticket operations are scoped to business_id
- Internal notes are filtered for customer-facing APIs
- Support agents can see all tickets but with masked sensitive data
- Audit logging is performed for all ticket state changes
"""

from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime, date, timedelta

from sqlalchemy import select, update, func, and_, or_, extract
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.models.support_ticket import SupportTicket, TicketStatus, TicketPriority, TicketCategory
from app.models.ticket_message import TicketMessage, SenderType
from app.models.canned_response import CannedResponse
from app.models.user import User
from app.models.business import Business
from app.models.audit_log import AuditLog, AuditAction
from app.schemas.support import (
    TicketCreate,
    TicketUpdate,
    MessageCreate,
    TicketFilters,
    SupportStatsResponse
)
from app.services.email_service import get_email_service
from app.core.encryption import get_encryption_service


class SupportService:
    """Service for support ticket database operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize support service.

        Args:
            db: Database session
        """
        self.db = db

    async def _generate_ticket_number(self) -> str:
        """
        Generate unique ticket number in format TKT-YYYY-NNNNN.

        The sequence is global across all businesses and resets annually.
        Uses SELECT FOR UPDATE to prevent race conditions.

        Returns:
            Generated ticket number (e.g., TKT-2025-00001)
        """
        current_year = datetime.utcnow().year

        # Get the highest sequence number for this year
        result = await self.db.execute(
            select(SupportTicket.ticket_number)
            .where(
                SupportTicket.ticket_number.like(f"TKT-{current_year}-%")
            )
            .order_by(SupportTicket.ticket_number.desc())
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        max_number = result.scalar_one_or_none()

        if max_number:
            # Extract sequence from last ticket number (TKT-2025-00001 -> 00001)
            sequence = int(max_number.split("-")[-1]) + 1
        else:
            # First ticket for this year
            sequence = 1

        # Format with zero padding (5 digits)
        return f"TKT-{current_year}-{sequence:05d}"

    async def _log_ticket_audit(
        self,
        ticket_id: UUID,
        user_id: UUID,
        action: AuditAction,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ) -> None:
        """
        Log ticket-related action to audit log.

        Args:
            ticket_id: Ticket UUID
            user_id: User performing action
            action: Audit action type
            details: Additional details
            ip_address: User's IP address
        """
        audit_entry = AuditLog(
            user_id=user_id,
            action=action,
            resource_type="support_ticket",
            resource_id=ticket_id,
            details=details or {},
            ip_address=ip_address
        )
        self.db.add(audit_entry)

    async def create_ticket(
        self,
        business_id: UUID,
        user_id: UUID,
        ticket_data: TicketCreate,
        ip_address: Optional[str] = None
    ) -> SupportTicket:
        """
        Create a new support ticket.

        Args:
            business_id: Business UUID
            user_id: User creating the ticket
            ticket_data: Ticket creation data
            ip_address: User's IP address for audit

        Returns:
            Created ticket instance
        """
        # Generate ticket number
        ticket_number = await self._generate_ticket_number()

        # Create ticket
        ticket = SupportTicket(
            business_id=business_id,
            user_id=user_id,
            ticket_number=ticket_number,
            subject=ticket_data.subject,
            description=ticket_data.description,
            category=ticket_data.category,
            priority=TicketPriority.MEDIUM,  # Default priority
            status=TicketStatus.OPEN
        )

        self.db.add(ticket)
        await self.db.flush()

        # Log audit entry
        await self._log_ticket_audit(
            ticket_id=ticket.id,
            user_id=user_id,
            action=AuditAction.CREATE,
            details={
                "ticket_number": ticket_number,
                "category": ticket_data.category.value,
                "subject": ticket_data.subject
            },
            ip_address=ip_address
        )

        await self.db.commit()

        # Fetch the ticket with messages loaded to avoid lazy loading issues
        return await self.get_ticket(ticket.id, include_messages=True)

    async def get_ticket(
        self,
        ticket_id: UUID,
        business_id: Optional[UUID] = None,
        include_messages: bool = False
    ) -> Optional[SupportTicket]:
        """
        Get a support ticket by ID.

        Args:
            ticket_id: Ticket UUID
            business_id: Optional business UUID for scoping (if None, allows agent access)
            include_messages: Whether to include messages

        Returns:
            Ticket instance or None if not found
        """
        query = select(SupportTicket).where(SupportTicket.id == ticket_id)

        # Scope to business if provided
        if business_id is not None:
            query = query.where(SupportTicket.business_id == business_id)

        # Include relationships if requested
        if include_messages:
            query = query.options(
                selectinload(SupportTicket.messages).selectinload(TicketMessage.sender),
                selectinload(SupportTicket.creator),
                selectinload(SupportTicket.assigned_agent),
                selectinload(SupportTicket.business)
            )
        else:
            query = query.options(
                selectinload(SupportTicket.creator),
                selectinload(SupportTicket.assigned_agent)
            )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_ticket_by_number(
        self,
        ticket_number: str,
        business_id: Optional[UUID] = None
    ) -> Optional[SupportTicket]:
        """
        Get a support ticket by ticket number.

        Args:
            ticket_number: Ticket number (e.g., TKT-2025-00001)
            business_id: Optional business UUID for scoping

        Returns:
            Ticket instance or None if not found
        """
        query = select(SupportTicket).where(SupportTicket.ticket_number == ticket_number)

        if business_id is not None:
            query = query.where(SupportTicket.business_id == business_id)

        query = query.options(
            selectinload(SupportTicket.creator),
            selectinload(SupportTicket.assigned_agent)
        )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_business_tickets(
        self,
        business_id: UUID,
        filters: Optional[TicketFilters] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[SupportTicket], int]:
        """
        Get tickets for a specific business with pagination.

        Args:
            business_id: Business UUID
            filters: Optional filters
            page: Page number
            page_size: Items per page

        Returns:
            Tuple of (tickets, total_count)
        """
        query = select(SupportTicket).where(SupportTicket.business_id == business_id)

        # Apply filters
        if filters:
            if filters.status:
                query = query.where(SupportTicket.status == filters.status)
            if filters.priority:
                query = query.where(SupportTicket.priority == filters.priority)
            if filters.category:
                query = query.where(SupportTicket.category == filters.category)
            if filters.search:
                search_term = f"%{filters.search}%"
                query = query.where(
                    or_(
                        SupportTicket.subject.ilike(search_term),
                        SupportTicket.description.ilike(search_term),
                        SupportTicket.ticket_number.ilike(search_term)
                    )
                )

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        # Apply pagination and ordering
        query = query.options(
            selectinload(SupportTicket.assigned_agent),
            selectinload(SupportTicket.messages)  # Needed for message_count property
        ).order_by(SupportTicket.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        # Execute query
        result = await self.db.execute(query)
        tickets = result.scalars().all()

        return list(tickets), total

    async def get_all_tickets(
        self,
        filters: Optional[TicketFilters] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[SupportTicket], int]:
        """
        Get all tickets (for support agents) with pagination.

        Args:
            filters: Optional filters
            page: Page number
            page_size: Items per page

        Returns:
            Tuple of (tickets, total_count)
        """
        query = select(SupportTicket)

        # Apply filters
        if filters:
            if filters.status:
                query = query.where(SupportTicket.status == filters.status)
            if filters.priority:
                query = query.where(SupportTicket.priority == filters.priority)
            if filters.category:
                query = query.where(SupportTicket.category == filters.category)
            if filters.assigned_agent_id:
                query = query.where(SupportTicket.assigned_agent_id == filters.assigned_agent_id)
            if filters.unassigned:
                query = query.where(SupportTicket.assigned_agent_id.is_(None))
            if filters.business_id:
                query = query.where(SupportTicket.business_id == filters.business_id)
            if filters.search:
                search_term = f"%{filters.search}%"
                query = query.where(
                    or_(
                        SupportTicket.subject.ilike(search_term),
                        SupportTicket.description.ilike(search_term),
                        SupportTicket.ticket_number.ilike(search_term)
                    )
                )

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        # Apply pagination and ordering
        # Sort by priority (urgent first) then by creation date
        query = query.options(
            selectinload(SupportTicket.assigned_agent),
            selectinload(SupportTicket.business),
            selectinload(SupportTicket.creator),
            selectinload(SupportTicket.messages)  # Needed for message_count property
        ).order_by(
            SupportTicket.priority.desc(),
            SupportTicket.created_at.desc()
        )
        query = query.offset((page - 1) * page_size).limit(page_size)

        # Execute query
        result = await self.db.execute(query)
        tickets = result.scalars().all()

        return list(tickets), total

    async def update_ticket(
        self,
        ticket_id: UUID,
        update_data: TicketUpdate,
        agent_id: UUID,
        ip_address: Optional[str] = None
    ) -> Optional[SupportTicket]:
        """
        Update ticket status, priority, or assignment (agents only).

        Args:
            ticket_id: Ticket UUID
            update_data: Update data
            agent_id: Agent performing the update
            ip_address: Agent's IP address for audit

        Returns:
            Updated ticket or None if not found
        """
        ticket = await self.get_ticket(ticket_id, include_messages=False)
        if not ticket:
            return None

        changes = {}

        # Track changes for audit
        if update_data.status is not None and update_data.status != ticket.status:
            changes["status"] = {
                "old": ticket.status.value,
                "new": update_data.status.value
            }
            ticket.status = update_data.status

            # Set resolved_at timestamp if status changed to resolved
            if update_data.status == TicketStatus.RESOLVED:
                ticket.resolved_at = datetime.utcnow()
                changes["resolved_at"] = ticket.resolved_at.isoformat()

        if update_data.priority is not None and update_data.priority != ticket.priority:
            changes["priority"] = {
                "old": ticket.priority.value,
                "new": update_data.priority.value
            }
            ticket.priority = update_data.priority

        if update_data.assigned_agent_id is not None and update_data.assigned_agent_id != ticket.assigned_agent_id:
            changes["assigned_agent_id"] = {
                "old": str(ticket.assigned_agent_id) if ticket.assigned_agent_id else None,
                "new": str(update_data.assigned_agent_id)
            }
            ticket.assigned_agent_id = update_data.assigned_agent_id

        # Log audit if there were changes
        if changes:
            await self._log_ticket_audit(
                ticket_id=ticket_id,
                user_id=agent_id,
                action=AuditAction.UPDATE,
                details={"changes": changes},
                ip_address=ip_address
            )

        await self.db.commit()

        # Send email notification if status changed
        if "status" in changes:
            # Get ticket with full details for email
            ticket_with_details = await self.get_ticket(ticket_id, include_messages=True)
            if ticket_with_details and ticket_with_details.creator:
                email_service = get_email_service()
                encryption_service = get_encryption_service()

                # Get creator email (ticket requester)
                creator_email = None
                if ticket_with_details.creator.email_encrypted:
                    try:
                        creator_email = encryption_service.decrypt(ticket_with_details.creator.email_encrypted)
                    except Exception:
                        pass  # Continue without email if decryption fails

                if creator_email:
                    # Get latest message preview
                    message_preview = None
                    if ticket_with_details.messages and len(ticket_with_details.messages) > 0:
                        latest_message = ticket_with_details.messages[-1]
                        message_preview = latest_message.message[:200] + "..." if len(latest_message.message) > 200 else latest_message.message

                    try:
                        await email_service.send_ticket_update_email(
                            to_email=creator_email,
                            user_name=f"{ticket_with_details.creator.first_name} {ticket_with_details.creator.last_name}",
                            ticket_number=ticket_with_details.ticket_number,
                            ticket_subject=ticket_with_details.subject,
                            new_status=changes["status"]["new"],
                            message_preview=message_preview,
                            ticket_url=None  # Can be set to actual ticket URL if frontend supports it
                        )
                    except Exception as e:
                        # Log email error but don't fail the update
                        import logging
                        logging.error(f"Failed to send ticket update email: {str(e)}")

        # Fetch the ticket with messages loaded to avoid lazy loading issues
        return await self.get_ticket(ticket_id, include_messages=True)

    async def assign_ticket(
        self,
        ticket_id: UUID,
        agent_id: UUID,
        assigned_by: UUID,
        ip_address: Optional[str] = None
    ) -> Optional[SupportTicket]:
        """
        Assign ticket to an agent.

        Args:
            ticket_id: Ticket UUID
            agent_id: Agent to assign to
            assigned_by: User performing the assignment
            ip_address: IP address for audit

        Returns:
            Updated ticket or None if not found
        """
        update_data = TicketUpdate(assigned_agent_id=agent_id)
        return await self.update_ticket(ticket_id, update_data, assigned_by, ip_address)

    async def add_message(
        self,
        ticket_id: UUID,
        user_id: UUID,
        message_data: MessageCreate,
        is_agent: bool = False,
        ip_address: Optional[str] = None
    ) -> Optional[TicketMessage]:
        """
        Add a message to a ticket.

        Args:
            ticket_id: Ticket UUID
            user_id: User sending the message
            message_data: Message data
            is_agent: Whether sender is a support agent
            ip_address: User's IP address for audit

        Returns:
            Created message or None if ticket not found
        """
        # Verify ticket exists
        ticket = await self.get_ticket(ticket_id, include_messages=False)
        if not ticket:
            return None

        # Validate internal notes (only agents can create internal notes)
        if message_data.is_internal and not is_agent:
            message_data.is_internal = False

        # Create message
        message = TicketMessage(
            ticket_id=ticket_id,
            sender_id=user_id,
            sender_type=SenderType.AGENT if is_agent else SenderType.CUSTOMER,
            message=message_data.message,
            attachments=message_data.attachments if message_data.attachments else None,
            is_internal=message_data.is_internal
        )

        self.db.add(message)

        # Update ticket status if needed
        if is_agent and ticket.status == TicketStatus.OPEN:
            ticket.status = TicketStatus.IN_PROGRESS
        elif not is_agent and ticket.status == TicketStatus.WAITING_CUSTOMER:
            ticket.status = TicketStatus.IN_PROGRESS

        # Log audit entry
        await self._log_ticket_audit(
            ticket_id=ticket_id,
            user_id=user_id,
            action=AuditAction.UPDATE,
            details={
                "action": "message_added",
                "sender_type": "agent" if is_agent else "customer",
                "is_internal": message_data.is_internal
            },
            ip_address=ip_address
        )

        await self.db.commit()
        await self.db.refresh(message)

        return message

    async def get_ticket_messages(
        self,
        ticket_id: UUID,
        include_internal: bool = False
    ) -> List[TicketMessage]:
        """
        Get all messages for a ticket.

        Args:
            ticket_id: Ticket UUID
            include_internal: Whether to include internal notes (agents only)

        Returns:
            List of ticket messages
        """
        query = select(TicketMessage).where(TicketMessage.ticket_id == ticket_id)

        # Filter out internal notes for customers
        if not include_internal:
            query = query.where(TicketMessage.is_internal == False)

        query = query.options(
            selectinload(TicketMessage.sender)
        ).order_by(TicketMessage.created_at.asc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_support_stats(self) -> SupportStatsResponse:
        """
        Get support dashboard statistics.

        Returns:
            Support statistics
        """
        # Get counts by status
        status_counts = await self.db.execute(
            select(
                SupportTicket.status,
                func.count(SupportTicket.id)
            ).group_by(SupportTicket.status)
        )
        status_dict = dict(status_counts.all())

        # Get today's date range
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        # Get resolved/closed today
        resolved_today = await self.db.execute(
            select(func.count(SupportTicket.id))
            .where(
                and_(
                    SupportTicket.resolved_at >= today_start,
                    SupportTicket.status == TicketStatus.RESOLVED
                )
            )
        )
        resolved_count = resolved_today.scalar_one()

        closed_today = await self.db.execute(
            select(func.count(SupportTicket.id))
            .where(
                and_(
                    SupportTicket.updated_at >= today_start,
                    SupportTicket.status == TicketStatus.CLOSED
                )
            )
        )
        closed_count = closed_today.scalar_one()

        # Calculate average resolution time (in hours)
        avg_resolution = await self.db.execute(
            select(
                func.avg(
                    extract('epoch', SupportTicket.resolved_at - SupportTicket.created_at) / 3600
                )
            ).where(
                SupportTicket.resolved_at.isnot(None)
            )
        )
        avg_hours = avg_resolution.scalar_one()

        # Get unassigned count
        unassigned = await self.db.execute(
            select(func.count(SupportTicket.id))
            .where(
                and_(
                    SupportTicket.assigned_agent_id.is_(None),
                    SupportTicket.status.in_([TicketStatus.OPEN, TicketStatus.IN_PROGRESS])
                )
            )
        )
        unassigned_count = unassigned.scalar_one()

        # Get high priority count
        high_priority = await self.db.execute(
            select(func.count(SupportTicket.id))
            .where(
                and_(
                    SupportTicket.priority.in_([TicketPriority.HIGH, TicketPriority.URGENT]),
                    SupportTicket.status.in_([TicketStatus.OPEN, TicketStatus.IN_PROGRESS, TicketStatus.WAITING_CUSTOMER])
                )
            )
        )
        high_priority_count = high_priority.scalar_one()

        # Get total tickets
        total = await self.db.execute(select(func.count(SupportTicket.id)))
        total_count = total.scalar_one()

        return SupportStatsResponse(
            open_count=status_dict.get(TicketStatus.OPEN, 0),
            in_progress_count=status_dict.get(TicketStatus.IN_PROGRESS, 0),
            waiting_customer_count=status_dict.get(TicketStatus.WAITING_CUSTOMER, 0),
            resolved_today=resolved_count,
            closed_today=closed_count,
            avg_resolution_time_hours=round(avg_hours, 2) if avg_hours else None,
            unassigned_count=unassigned_count,
            high_priority_count=high_priority_count,
            total_tickets=total_count
        )

    async def get_canned_responses(
        self,
        category: Optional[str] = None
    ) -> List[CannedResponse]:
        """
        Get canned response templates.

        Args:
            category: Optional category filter

        Returns:
            List of canned responses
        """
        query = select(CannedResponse).where(CannedResponse.is_active == True)

        if category:
            query = query.where(CannedResponse.category == category)

        query = query.order_by(CannedResponse.title.asc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_satisfaction_rating(
        self,
        ticket_id: UUID,
        business_id: UUID,
        rating: int
    ) -> Optional[SupportTicket]:
        """
        Update customer satisfaction rating for a ticket.

        Args:
            ticket_id: Ticket UUID
            business_id: Business UUID (for security scoping)
            rating: Rating (1-5)

        Returns:
            Updated ticket or None if not found
        """
        ticket = await self.get_ticket(ticket_id, business_id=business_id)
        if not ticket:
            return None

        # Validate rating
        if rating < 1 or rating > 5:
            return None

        # Only allow rating on resolved/closed tickets
        if not ticket.is_resolved:
            return None

        ticket.satisfaction_rating = rating

        await self.db.commit()

        # Fetch the ticket with messages loaded to avoid lazy loading issues
        return await self.get_ticket(ticket_id, business_id=business_id, include_messages=True)
