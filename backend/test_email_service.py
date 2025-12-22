"""
Test Email Service

Simple script to test email service functionality.
Run this to verify email templates and service configuration.

Usage:
    python test_email_service.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.email_service import get_email_service


async def test_email_templates():
    """Test all email templates by sending test emails."""
    email_service = get_email_service()

    print("=" * 60)
    print("EMAIL SERVICE TEST")
    print("=" * 60)
    print(f"Email enabled: {email_service.settings.email_enabled}")
    print(f"SMTP Host: {email_service.settings.smtp_host}")
    print(f"SMTP Port: {email_service.settings.smtp_port}")
    print(f"From Email: {email_service.settings.smtp_from_email}")
    print(f"From Name: {email_service.settings.smtp_from_name}")
    print("=" * 60)

    test_email = "test@example.com"

    # Test 1: Welcome Email
    print("\n[1/6] Testing Welcome Email...")
    success = await email_service.send_welcome_email(
        to_email=test_email,
        business_name="Test Business Ltd",
        user_name="John Doe",
        temporary_password="TempPass123!",
        login_url="https://app.kenyaaccounting.com/login"
    )
    print(f"   Result: {'✓ SUCCESS' if success else '✗ FAILED'}")

    # Test 2: Password Reset Email
    print("\n[2/6] Testing Password Reset Email...")
    success = await email_service.send_password_reset_email(
        to_email=test_email,
        user_name="John Doe",
        reset_token="abc123xyz789",
        reset_url="https://app.kenyaaccounting.com/reset-password"
    )
    print(f"   Result: {'✓ SUCCESS' if success else '✗ FAILED'}")

    # Test 3: Invoice Email
    print("\n[3/6] Testing Invoice Email...")
    success = await email_service.send_invoice_email(
        to_email=test_email,
        customer_name="Jane Smith",
        invoice_number="INV-2025-001",
        amount="50,000.00",
        due_date="January 31, 2025",
        business_name="Test Business Ltd",
        view_url="https://app.kenyaaccounting.com/invoices/123"
    )
    print(f"   Result: {'✓ SUCCESS' if success else '✗ FAILED'}")

    # Test 4: Payment Confirmation Email
    print("\n[4/6] Testing Payment Confirmation Email...")
    success = await email_service.send_payment_confirmation_email(
        to_email=test_email,
        customer_name="Jane Smith",
        invoice_number="INV-2025-001",
        payment_amount="25,000.00",
        payment_date="December 9, 2025",
        payment_method="M-Pesa",
        remaining_balance="25,000.00",
        business_name="Test Business Ltd"
    )
    print(f"   Result: {'✓ SUCCESS' if success else '✗ FAILED'}")

    # Test 5: Ticket Update Email
    print("\n[5/6] Testing Ticket Update Email...")
    success = await email_service.send_ticket_update_email(
        to_email=test_email,
        user_name="John Doe",
        ticket_number="TKT-2025-001",
        ticket_subject="Cannot login to my account",
        new_status="resolved",
        message_preview="Your issue has been resolved. Please try logging in again.",
        ticket_url="https://app.kenyaaccounting.com/support/tickets/123"
    )
    print(f"   Result: {'✓ SUCCESS' if success else '✗ FAILED'}")

    # Test 6: Application Approved Email
    print("\n[6/6] Testing Application Approved Email...")
    success = await email_service.send_application_status_email(
        to_email=test_email,
        applicant_name="John Doe",
        business_name="Test Business Ltd",
        status="approved",
        message="Welcome! Your application has been approved.",
        login_credentials={
            "email": "john@testbusiness.com",
            "password": "TempPass123!",
            "login_url": "https://app.kenyaaccounting.com/login"
        }
    )
    print(f"   Result: {'✓ SUCCESS' if success else '✗ FAILED'}")

    print("\n" + "=" * 60)
    print("EMAIL SERVICE TEST COMPLETED")
    print("=" * 60)

    if email_service.settings.email_enabled:
        print("\nNote: Emails were sent to SMTP server.")
        print("Check your inbox for test emails.")
    else:
        print("\nNote: EMAIL_ENABLED=False (Development Mode)")
        print("Emails were logged but not sent.")
        print("Check console output above for email details.")


async def test_template_rendering():
    """Test that all templates can be rendered without errors."""
    email_service = get_email_service()

    print("\n" + "=" * 60)
    print("TEMPLATE RENDERING TEST")
    print("=" * 60)

    templates = [
        ("base.html", {}),
        ("welcome.html", {
            "business_name": "Test Business",
            "user_name": "John Doe",
            "email": "test@example.com",
            "temporary_password": "Pass123!",
            "login_url": "https://example.com"
        }),
        ("password_reset.html", {
            "user_name": "John Doe",
            "reset_url": "https://example.com/reset",
            "expires_in": "1 hour"
        }),
        ("invoice_sent.html", {
            "customer_name": "Customer",
            "invoice_number": "INV-001",
            "amount": "10,000.00",
            "due_date": "Dec 31, 2025",
            "business_name": "Business",
            "view_url": "https://example.com"
        }),
        ("payment_received.html", {
            "customer_name": "Customer",
            "invoice_number": "INV-001",
            "payment_amount": "5,000.00",
            "payment_date": "Dec 9, 2025",
            "payment_method": "M-Pesa",
            "remaining_balance": "5,000.00",
            "business_name": "Business"
        }),
        ("ticket_update.html", {
            "user_name": "User",
            "ticket_number": "TKT-001",
            "ticket_subject": "Issue",
            "new_status": "resolved",
            "message_preview": "Message",
            "ticket_url": "https://example.com"
        }),
        ("application_approved.html", {
            "applicant_name": "Applicant",
            "business_name": "Business",
            "message": "Welcome",
            "credentials": {
                "email": "test@example.com",
                "password": "Pass123!",
                "login_url": "https://example.com"
            }
        }),
        ("application_rejected.html", {
            "applicant_name": "Applicant",
            "business_name": "Business",
            "message": "Sorry"
        }),
        ("application_info_requested.html", {
            "applicant_name": "Applicant",
            "business_name": "Business",
            "message": "Need more info"
        })
    ]

    for template_name, context in templates:
        try:
            html = email_service.render_template(template_name, context)
            print(f"✓ {template_name:<35} OK ({len(html)} chars)")
        except Exception as e:
            print(f"✗ {template_name:<35} FAILED: {str(e)}")

    print("=" * 60)


if __name__ == "__main__":
    print("\n🧪 Starting Email Service Tests...\n")

    # Run template rendering test
    asyncio.run(test_template_rendering())

    # Run email sending test
    asyncio.run(test_email_templates())

    print("\n✅ All tests completed!\n")
