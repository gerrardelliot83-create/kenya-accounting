"""
Email Notification Service

Provides transactional email functionality for the Kenya SMB Accounting MVP.
Supports welcome emails, password resets, invoices, payments, and support tickets.

Features:
- Async SMTP sending using aiosmtplib
- Jinja2 templating for HTML emails
- Development mode (logging only, no actual sending)
- Support for attachments (PDFs, etc.)
- Configurable via environment variables
"""

import asyncio
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import Optional, List, Tuple
from pathlib import Path
import aiosmtplib
from jinja2 import Environment, FileSystemLoader

from app.config import get_settings

# Setup logging
logger = logging.getLogger(__name__)


class EmailService:
    """
    Service for sending transactional emails.

    In development mode (email_enabled=False), emails are logged but not sent.
    In production, configure SMTP settings via environment variables.
    """

    def __init__(self):
        """Initialize email service with settings and Jinja2 template environment."""
        self.settings = get_settings()

        # Setup Jinja2 template loader
        template_path = Path(__file__).parent.parent / "templates" / "email"
        self.template_env = Environment(
            loader=FileSystemLoader(str(template_path)),
            autoescape=True  # Security: auto-escape HTML
        )

        logger.info(
            f"EmailService initialized. Email sending: "
            f"{'ENABLED' if self.settings.email_enabled else 'DISABLED (dev mode)'}"
        )

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[Tuple[str, bytes, str]]] = None
    ) -> bool:
        """
        Send an email asynchronously.

        Args:
            to_email: Recipient email address
            subject: Email subject line
            html_content: HTML body content
            text_content: Plain text fallback (optional)
            cc: CC recipients (optional)
            bcc: BCC recipients (optional)
            attachments: List of (filename, content_bytes, mime_type) tuples

        Returns:
            bool: True if email was sent successfully (or logged in dev mode)
        """
        if not self.settings.email_enabled:
            # Development mode: log but don't send
            logger.info(
                f"[DEV MODE] Email would be sent:\n"
                f"  To: {to_email}\n"
                f"  Subject: {subject}\n"
                f"  CC: {cc}\n"
                f"  BCC: {bcc}\n"
                f"  Attachments: {len(attachments) if attachments else 0}"
            )
            return True

        try:
            # Create multipart message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.settings.smtp_from_name} <{self.settings.smtp_from_email}>"
            message["To"] = to_email

            if cc:
                message["Cc"] = ", ".join(cc)

            if bcc:
                message["Bcc"] = ", ".join(bcc)

            # Add plain text version (fallback)
            if text_content:
                message.attach(MIMEText(text_content, "plain", "utf-8"))

            # Add HTML version (preferred)
            message.attach(MIMEText(html_content, "html", "utf-8"))

            # Add attachments if provided
            if attachments:
                for filename, content, mime_type in attachments:
                    attachment = MIMEApplication(content, _subtype=mime_type.split('/')[-1])
                    attachment.add_header('Content-Disposition', 'attachment', filename=filename)
                    message.attach(attachment)

            # Build recipient list (to + cc + bcc)
            recipients = [to_email]
            if cc:
                recipients.extend(cc)
            if bcc:
                recipients.extend(bcc)

            # Send email via SMTP
            await aiosmtplib.send(
                message,
                hostname=self.settings.smtp_host,
                port=self.settings.smtp_port,
                username=self.settings.smtp_user,
                password=self.settings.smtp_password,
                start_tls=self.settings.smtp_use_tls,
                recipients=recipients
            )

            logger.info(f"Email sent successfully to {to_email}: {subject}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}", exc_info=True)
            return False

    def render_template(self, template_name: str, context: dict) -> str:
        """
        Render an email template with the given context.

        Args:
            template_name: Template filename (e.g., "welcome.html")
            context: Dictionary of variables to pass to template

        Returns:
            str: Rendered HTML content
        """
        try:
            template = self.template_env.get_template(template_name)
            return template.render(**context)
        except Exception as e:
            logger.error(f"Failed to render template {template_name}: {str(e)}")
            raise

    # ==================== TRANSACTIONAL EMAILS ====================

    async def send_welcome_email(
        self,
        to_email: str,
        business_name: str,
        user_name: str,
        temporary_password: str,
        login_url: str = "https://app.kenyaaccounting.com/login"
    ) -> bool:
        """
        Send welcome email with login credentials to new users.

        Args:
            to_email: User's email address
            business_name: Name of the business
            user_name: User's full name
            temporary_password: Temporary password (should be changed on first login)
            login_url: URL to login page

        Returns:
            bool: True if email was sent successfully
        """
        html_content = self.render_template("welcome.html", {
            "business_name": business_name,
            "user_name": user_name,
            "email": to_email,
            "temporary_password": temporary_password,
            "login_url": login_url
        })

        return await self.send_email(
            to_email=to_email,
            subject=f"Welcome to Kenya SMB Accounting - {business_name}",
            html_content=html_content
        )

    async def send_password_reset_email(
        self,
        to_email: str,
        user_name: str,
        reset_token: str,
        reset_url: str = "https://app.kenyaaccounting.com/reset-password"
    ) -> bool:
        """
        Send password reset email with reset token.

        Args:
            to_email: User's email address
            user_name: User's full name
            reset_token: Password reset token
            reset_url: Base URL for password reset page

        Returns:
            bool: True if email was sent successfully
        """
        html_content = self.render_template("password_reset.html", {
            "user_name": user_name,
            "reset_url": f"{reset_url}?token={reset_token}",
            "expires_in": "1 hour"
        })

        return await self.send_email(
            to_email=to_email,
            subject="Password Reset Request - Kenya SMB Accounting",
            html_content=html_content
        )

    async def send_invoice_email(
        self,
        to_email: str,
        customer_name: str,
        invoice_number: str,
        amount: str,
        due_date: str,
        business_name: str,
        invoice_pdf: Optional[bytes] = None,
        view_url: Optional[str] = None
    ) -> bool:
        """
        Send invoice to customer via email.

        Args:
            to_email: Customer's email address
            customer_name: Customer's name
            invoice_number: Invoice number (e.g., "INV-001")
            amount: Formatted amount (e.g., "25,000.00")
            due_date: Formatted due date (e.g., "December 31, 2025")
            business_name: Sender business name
            invoice_pdf: PDF file content as bytes (optional)
            view_url: URL to view invoice online (optional)

        Returns:
            bool: True if email was sent successfully
        """
        html_content = self.render_template("invoice_sent.html", {
            "customer_name": customer_name,
            "invoice_number": invoice_number,
            "amount": amount,
            "due_date": due_date,
            "business_name": business_name,
            "view_url": view_url
        })

        attachments = None
        if invoice_pdf:
            attachments = [(f"Invoice-{invoice_number}.pdf", invoice_pdf, "application/pdf")]

        return await self.send_email(
            to_email=to_email,
            subject=f"Invoice {invoice_number} from {business_name}",
            html_content=html_content,
            attachments=attachments
        )

    async def send_payment_confirmation_email(
        self,
        to_email: str,
        customer_name: str,
        invoice_number: str,
        payment_amount: str,
        payment_date: str,
        payment_method: str,
        remaining_balance: str,
        business_name: str
    ) -> bool:
        """
        Send payment confirmation email to customer.

        Args:
            to_email: Customer's email address
            customer_name: Customer's name
            invoice_number: Related invoice number
            payment_amount: Formatted payment amount
            payment_date: Formatted payment date
            payment_method: Payment method (e.g., "M-Pesa", "Bank Transfer")
            remaining_balance: Formatted remaining balance
            business_name: Business name

        Returns:
            bool: True if email was sent successfully
        """
        html_content = self.render_template("payment_received.html", {
            "customer_name": customer_name,
            "invoice_number": invoice_number,
            "payment_amount": payment_amount,
            "payment_date": payment_date,
            "payment_method": payment_method,
            "remaining_balance": remaining_balance,
            "business_name": business_name
        })

        return await self.send_email(
            to_email=to_email,
            subject=f"Payment Received - Invoice {invoice_number}",
            html_content=html_content
        )

    async def send_ticket_update_email(
        self,
        to_email: str,
        user_name: str,
        ticket_number: str,
        ticket_subject: str,
        new_status: str,
        message_preview: Optional[str] = None,
        ticket_url: Optional[str] = None
    ) -> bool:
        """
        Send support ticket update notification.

        Args:
            to_email: User's email address
            user_name: User's name
            ticket_number: Ticket number (e.g., "TICK-001")
            ticket_subject: Ticket subject line
            new_status: New ticket status
            message_preview: Preview of latest message (optional)
            ticket_url: URL to view ticket (optional)

        Returns:
            bool: True if email was sent successfully
        """
        html_content = self.render_template("ticket_update.html", {
            "user_name": user_name,
            "ticket_number": ticket_number,
            "ticket_subject": ticket_subject,
            "new_status": new_status,
            "message_preview": message_preview,
            "ticket_url": ticket_url
        })

        return await self.send_email(
            to_email=to_email,
            subject=f"Ticket #{ticket_number} Updated - {new_status}",
            html_content=html_content
        )

    async def send_application_status_email(
        self,
        to_email: str,
        applicant_name: str,
        business_name: str,
        status: str,
        message: Optional[str] = None,
        login_credentials: Optional[dict] = None
    ) -> bool:
        """
        Send business application status update email.

        Args:
            to_email: Applicant's email address
            applicant_name: Applicant's name
            business_name: Business name
            status: Application status ("approved", "rejected", "info_requested")
            message: Additional message/reason (optional)
            login_credentials: Dict with {email, password, login_url} for approved apps

        Returns:
            bool: True if email was sent successfully
        """
        # Select template and subject based on status
        if status == "approved":
            template = "application_approved.html"
            subject = f"Application Approved - Welcome to Kenya SMB Accounting"
        elif status == "rejected":
            template = "application_rejected.html"
            subject = f"Application Update - {business_name}"
        else:  # info_requested
            template = "application_info_requested.html"
            subject = f"Additional Information Required - {business_name}"

        html_content = self.render_template(template, {
            "applicant_name": applicant_name,
            "business_name": business_name,
            "message": message,
            "credentials": login_credentials
        })

        return await self.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content
        )


# ==================== SINGLETON INSTANCE ====================

_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """
    Get or create the singleton EmailService instance.

    This ensures only one instance exists throughout the application lifecycle.

    Returns:
        EmailService: The email service instance
    """
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
