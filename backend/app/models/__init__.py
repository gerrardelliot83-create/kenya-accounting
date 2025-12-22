"""Database models for the application."""

from app.models.user import User, UserRole
from app.models.business import Business
from app.models.audit_log import AuditLog, AuditAction, AuditStatus
from app.models.contact import Contact, ContactType
from app.models.item import Item, ItemType
from app.models.invoice import Invoice, InvoiceStatus
from app.models.invoice_item import InvoiceItem
from app.models.payment import Payment, PaymentMethod
from app.models.expense import Expense
from app.models.expense_category import ExpenseCategory
from app.models.bank_import import BankImport, FileType, ImportStatus
from app.models.bank_transaction import BankTransaction, ReconciliationStatus
from app.models.tax_settings import TaxSettings
from app.models.faq import FaqCategory, FaqArticle
from app.models.help_article import HelpArticle
from app.models.support_ticket import SupportTicket, TicketCategory, TicketPriority, TicketStatus
from app.models.ticket_message import TicketMessage, SenderType
from app.models.canned_response import CannedResponse

# Import all models here so Alembic can detect them
__all__ = [
    "User",
    "UserRole",
    "Business",
    "AuditLog",
    "AuditAction",
    "AuditStatus",
    "Contact",
    "ContactType",
    "Item",
    "ItemType",
    "Invoice",
    "InvoiceStatus",
    "InvoiceItem",
    "Payment",
    "PaymentMethod",
    "Expense",
    "ExpenseCategory",
    "BankImport",
    "FileType",
    "ImportStatus",
    "BankTransaction",
    "ReconciliationStatus",
    "TaxSettings",
    "FaqCategory",
    "FaqArticle",
    "HelpArticle",
    "SupportTicket",
    "TicketCategory",
    "TicketPriority",
    "TicketStatus",
    "TicketMessage",
    "SenderType",
    "CannedResponse",
]
