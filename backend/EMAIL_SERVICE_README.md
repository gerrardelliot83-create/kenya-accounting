# Email Notification Service - Kenya SMB Accounting MVP

## Overview

Complete email notification service for sending transactional emails including welcome emails, password resets, invoices, payment confirmations, support tickets, and application status updates.

## Features

- **Async Email Sending**: Non-blocking email delivery using `aiosmtplib`
- **Jinja2 Templates**: HTML email templates with consistent branding
- **Development Mode**: Log emails without sending (configurable via `EMAIL_ENABLED`)
- **Multiple Email Types**: Welcome, password reset, invoice, payment, ticket, application status
- **Attachment Support**: Send PDFs and other attachments
- **Error Handling**: Graceful failure - email errors don't break business logic
- **Security**: Auto-escaping in templates, encrypted sensitive data

## Installation

Dependencies are already added to `requirements.txt`:
```bash
pip install -r requirements.txt
```

Key packages:
- `aiosmtplib>=3.0.0` - Async SMTP client
- `email-validator>=2.1.0` - Email validation
- `jinja2>=3.1.2` - Template engine (already installed for PDF generation)

## Configuration

### Environment Variables (.env)

```env
# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@kenyaaccounting.com
SMTP_FROM_NAME=Kenya SMB Accounting
SMTP_USE_TLS=True
EMAIL_ENABLED=False  # Set to True in production
```

### Gmail Configuration (Development/Testing)

1. Enable 2-Factor Authentication on your Gmail account
2. Generate App Password:
   - Go to Google Account → Security → 2-Step Verification → App passwords
   - Create new app password for "Mail"
   - Copy the 16-character password
3. Set environment variables:
   ```env
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=your-16-char-app-password
   EMAIL_ENABLED=True
   ```

### Production Configuration

For production, use dedicated email services:

**Option 1: SendGrid**
```env
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=your-sendgrid-api-key
SMTP_FROM_EMAIL=noreply@kenyaaccounting.com
EMAIL_ENABLED=True
```

**Option 2: AWS SES**
```env
SMTP_HOST=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_USER=your-aws-ses-smtp-user
SMTP_PASSWORD=your-aws-ses-smtp-password
SMTP_FROM_EMAIL=noreply@kenyaaccounting.com
EMAIL_ENABLED=True
```

## Usage

### Import the Service

```python
from app.services.email_service import get_email_service

email_service = get_email_service()
```

### Available Email Methods

#### 1. Welcome Email
```python
await email_service.send_welcome_email(
    to_email="user@example.com",
    business_name="Acme Corp",
    user_name="John Doe",
    temporary_password="TempPass123!",
    login_url="https://app.kenyaaccounting.com/login"
)
```

#### 2. Password Reset
```python
await email_service.send_password_reset_email(
    to_email="user@example.com",
    user_name="John Doe",
    reset_token="abc123xyz789",
    reset_url="https://app.kenyaaccounting.com/reset-password"
)
```

#### 3. Invoice
```python
await email_service.send_invoice_email(
    to_email="customer@example.com",
    customer_name="Jane Smith",
    invoice_number="INV-2025-001",
    amount="50,000.00",
    due_date="January 31, 2025",
    business_name="Acme Corp",
    invoice_pdf=pdf_bytes,  # Optional PDF attachment
    view_url="https://app.kenyaaccounting.com/invoices/123"  # Optional
)
```

#### 4. Payment Confirmation
```python
await email_service.send_payment_confirmation_email(
    to_email="customer@example.com",
    customer_name="Jane Smith",
    invoice_number="INV-2025-001",
    payment_amount="25,000.00",
    payment_date="December 9, 2025",
    payment_method="M-Pesa",
    remaining_balance="25,000.00",  # Use "0.00" for paid in full
    business_name="Acme Corp"
)
```

#### 5. Support Ticket Update
```python
await email_service.send_ticket_update_email(
    to_email="user@example.com",
    user_name="John Doe",
    ticket_number="TKT-2025-001",
    ticket_subject="Cannot login",
    new_status="resolved",
    message_preview="Your issue has been resolved...",  # Optional
    ticket_url="https://app.kenyaaccounting.com/tickets/123"  # Optional
)
```

#### 6. Application Status
```python
# Approved
await email_service.send_application_status_email(
    to_email="applicant@example.com",
    applicant_name="John Doe",
    business_name="Acme Corp",
    status="approved",
    message="Welcome to Kenya SMB Accounting!",
    login_credentials={
        "email": "john@acme.com",
        "password": "TempPass123!",
        "login_url": "https://app.kenyaaccounting.com/login"
    }
)

# Rejected
await email_service.send_application_status_email(
    to_email="applicant@example.com",
    applicant_name="John Doe",
    business_name="Acme Corp",
    status="rejected",
    message="Incomplete documentation provided."
)

# Info Requested
await email_service.send_application_status_email(
    to_email="applicant@example.com",
    applicant_name="John Doe",
    business_name="Acme Corp",
    status="info_requested",
    message="Please provide your KRA PIN certificate."
)
```

### Custom Email (Advanced)
```python
await email_service.send_email(
    to_email="recipient@example.com",
    subject="Custom Email Subject",
    html_content="<h1>Hello</h1><p>Custom content</p>",
    text_content="Hello\n\nCustom content",  # Optional plain text fallback
    cc=["cc@example.com"],  # Optional
    bcc=["bcc@example.com"],  # Optional
    attachments=[
        ("filename.pdf", pdf_bytes, "application/pdf")
    ]  # Optional
)
```

## Email Templates

All templates are in `app/templates/email/`:

- `base.html` - Base template with header/footer
- `welcome.html` - Welcome email with credentials
- `password_reset.html` - Password reset link
- `invoice_sent.html` - Invoice notification
- `payment_received.html` - Payment confirmation
- `ticket_update.html` - Support ticket updates
- `application_approved.html` - Application approved
- `application_rejected.html` - Application rejected
- `application_info_requested.html` - More info needed

### Customizing Templates

Templates use Jinja2. To customize:

1. Edit template in `app/templates/email/`
2. Variables available depend on email type (see service method)
3. All templates extend `base.html` for consistent branding

Example customization:
```html
{% extends "base.html" %}
{% block content %}
<h2>Custom Header</h2>
<p>Custom content with {{ variable_name }}</p>
{% endblock %}
```

## Integration with Services

The email service is already integrated with:

### Onboarding Service
- **Approval**: Sends welcome email with credentials
- **Rejection**: Sends rejection email with reason
- **Info Request**: Sends email requesting additional information

### Support Service
- **Ticket Updates**: Sends notification when ticket status changes

### Payment Service (Pending)
- Can be integrated to send payment confirmations

### Invoice Service (Pending)
- Can be integrated with "Send Invoice" endpoint

## Testing

### Run Test Suite
```bash
python test_email_service.py
```

This will:
1. Test all email template rendering
2. Test all email sending methods
3. Show results in console

### Development Mode Testing
With `EMAIL_ENABLED=False`:
- Emails are logged to console
- No actual emails are sent
- Check logs to verify email content

### Production Testing
With `EMAIL_ENABLED=True`:
1. Send test email to yourself
2. Verify formatting and links
3. Check spam folder if not received
4. Verify attachments if applicable

## Error Handling

Email errors are gracefully handled:

```python
try:
    success = await email_service.send_welcome_email(...)
    if not success:
        # Email failed but logged
        logger.warning("Failed to send email")
except Exception as e:
    # Email service error (shouldn't break business logic)
    logger.error(f"Email error: {str(e)}")
```

In integrated services:
- Email failures are logged but don't break the operation
- Business logic continues even if email fails
- Users can still access the system

## Security Considerations

1. **Never log email content with sensitive data** (passwords, PINs, etc.)
2. **Use App Passwords** for Gmail (not account password)
3. **Enable TLS** for SMTP connections (default: True)
4. **Validate email addresses** before sending
5. **Rate limiting**: Implement in production to prevent abuse
6. **SPF/DKIM/DMARC**: Configure for production domain

## Production Checklist

Before going to production:

- [ ] Set `EMAIL_ENABLED=True`
- [ ] Configure production SMTP (SendGrid/AWS SES)
- [ ] Verify sender domain (SPF/DKIM records)
- [ ] Test all email types with real SMTP
- [ ] Set up email monitoring/logging
- [ ] Configure retry logic for failed emails
- [ ] Implement rate limiting
- [ ] Update email addresses in templates
- [ ] Set correct login URLs in `.env`

## Troubleshooting

### Emails not sending
1. Check `EMAIL_ENABLED=True` in `.env`
2. Verify SMTP credentials
3. Check SMTP host/port
4. Review logs for error messages
5. Test SMTP connection manually

### Gmail "Less secure app" error
- Use App Password instead of account password
- Enable 2FA first, then generate app password

### Emails in spam folder
- Configure SPF/DKIM/DMARC records
- Use verified sender domain
- Warm up new IP/domain gradually
- Check email content for spam triggers

### Template rendering errors
- Check Jinja2 syntax
- Verify all required variables are passed
- Check file paths and permissions

## File Structure

```
backend/
├── app/
│   ├── config.py                      # Email configuration added
│   ├── services/
│   │   ├── email_service.py           # Email service (NEW)
│   │   ├── onboarding_service.py      # Integrated
│   │   └── support_service.py         # Integrated
│   └── templates/
│       └── email/                     # Email templates (NEW)
│           ├── base.html
│           ├── welcome.html
│           ├── password_reset.html
│           ├── invoice_sent.html
│           ├── payment_received.html
│           ├── ticket_update.html
│           ├── application_approved.html
│           ├── application_rejected.html
│           └── application_info_requested.html
├── requirements.txt                   # Updated with email deps
├── .env                              # Email config added
└── test_email_service.py             # Test script (NEW)
```

## Support

For issues or questions about the email service:
1. Check logs for error messages
2. Review this documentation
3. Test with `test_email_service.py`
4. Contact the development team

---

**Last Updated**: December 9, 2025
**Version**: 1.0.0
**Status**: Production Ready ✅
