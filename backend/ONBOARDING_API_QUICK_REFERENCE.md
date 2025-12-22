# Onboarding Portal API - Quick Reference

## Base URL
```
/api/v1/onboarding
```

## Authentication
All endpoints require JWT token with role: `onboarding_agent` or `system_admin`

```http
Authorization: Bearer {jwt_token}
```

---

## Endpoints

### 1. Create Application
```http
POST /applications
```

**Request Body:**
```json
{
  "business_name": "required string",
  "business_type": "sole_proprietor | partnership | limited_company",
  "kra_pin": "optional string (encrypted)",
  "phone": "optional string (encrypted)",
  "email": "optional email (encrypted)",
  "county": "optional string",
  "sub_county": "optional string",
  "owner_name": "optional string",
  "owner_national_id": "optional string (encrypted)",
  "owner_phone": "optional string (encrypted)",
  "owner_email": "optional email (encrypted)",
  "bank_account": "optional string (encrypted)",
  "vat_registered": "boolean (default: false)",
  "tot_registered": "boolean (default: false)",
  "notes": "optional string"
}
```

**Response:** 201 Created

---

### 2. List Applications
```http
GET /applications?page=1&page_size=20&status=submitted
```

**Query Parameters:**
- `page` (optional) - Page number, default: 1
- `page_size` (optional) - Items per page (1-100), default: 20
- `status` (optional) - Filter: draft, submitted, under_review, approved, rejected, info_requested
- `created_by` (optional) - Agent UUID
- `reviewed_by` (optional) - Reviewer UUID
- `county` (optional) - County name
- `search` (optional) - Search in business_name, owner_name

**Response:** 200 OK
```json
{
  "applications": [...],
  "total": 150,
  "page": 1,
  "page_size": 20,
  "total_pages": 8
}
```

---

### 3. Get Application Details
```http
GET /applications/{application_id}
```

**Response:** 200 OK (with all decrypted fields)

---

### 4. Update Application
```http
PUT /applications/{application_id}
```

**Note:** Only draft or info_requested applications can be updated

**Request Body:** Same as create (all fields optional)

**Response:** 200 OK

---

### 5. Submit Application
```http
POST /applications/{application_id}/submit
```

**Response:** 200 OK (status changed to submitted)

---

### 6. Approve Application
```http
POST /applications/{application_id}/approve
```

**Request Body:**
```json
{
  "notes": "optional string"
}
```

**Response:** 200 OK
```json
{
  "application_id": "uuid",
  "business_id": "uuid",
  "business_name": "string",
  "admin_user_id": "uuid",
  "admin_email": "email",
  "temporary_password": "SecureP@ss123",
  "message": "Business application approved successfully. Admin account created.",
  "password_change_required": true
}
```

**⚠️ IMPORTANT:** Save the credentials! Password shown only once.

---

### 7. Reject Application
```http
POST /applications/{application_id}/reject
```

**Request Body:**
```json
{
  "rejection_reason": "required string (min 10 chars)"
}
```

**Response:** 200 OK (status changed to rejected)

---

### 8. Request More Information
```http
POST /applications/{application_id}/request-info
```

**Request Body:**
```json
{
  "info_request_note": "required string (min 10 chars)"
}
```

**Response:** 200 OK (status changed to info_requested)

---

### 9. Get Statistics
```http
GET /stats
```

**Response:** 200 OK
```json
{
  "total_applications": 150,
  "draft_count": 10,
  "submitted_count": 25,
  "under_review_count": 5,
  "info_requested_count": 3,
  "approved_count": 100,
  "rejected_count": 7,
  "submitted_today": 8,
  "approved_today": 5,
  "rejected_today": 1,
  "avg_review_time_hours": 4.5,
  "pending_review_count": 28
}
```

---

## Status Flow

```
draft → submitted → under_review → approved
                                 ↓
                              rejected
                                 ↓
                          info_requested → submitted
```

---

## Error Responses

### 400 Bad Request
Invalid input data, validation error

### 401 Unauthorized
Missing or invalid JWT token

### 403 Forbidden
User doesn't have required role (onboarding_agent or system_admin)

### 404 Not Found
Application not found or operation not allowed for current status

### 500 Internal Server Error
Server error, check logs

---

## Examples

### Create Draft Application
```bash
curl -X POST https://api.example.com/api/v1/onboarding/applications \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "business_name": "Acme Ltd",
    "business_type": "limited_company",
    "kra_pin": "A123456789X",
    "phone": "0712345678",
    "email": "info@acme.co.ke",
    "county": "Nairobi",
    "owner_name": "John Doe",
    "owner_email": "john@acme.co.ke",
    "vat_registered": true
  }'
```

### Submit Application
```bash
curl -X POST https://api.example.com/api/v1/onboarding/applications/{id}/submit \
  -H "Authorization: Bearer {token}"
```

### Approve Application
```bash
curl -X POST https://api.example.com/api/v1/onboarding/applications/{id}/approve \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "notes": "All documents verified. KRA PIN confirmed."
  }'
```

### List Pending Applications
```bash
curl -X GET "https://api.example.com/api/v1/onboarding/applications?status=submitted&page=1&page_size=50" \
  -H "Authorization: Bearer {token}"
```

---

## Field Validations

### KRA PIN
- Format: Letter + 9 digits + Letter (e.g., A123456789X)
- Minimum 11 characters
- Automatically converted to uppercase

### Phone Numbers
- Format: 0XXXXXXXXX (10 digits)
- Must start with 0
- Automatically cleaned (removes +254, spaces, dashes)

### Business Type
- Must be one of: `sole_proprietor`, `partnership`, `limited_company`

### Email
- Must be valid email format
- Validated using EmailStr

---

## Encrypted Fields

These fields are automatically encrypted in the database:
1. kra_pin
2. phone
3. email
4. owner_national_id
5. owner_phone
6. owner_email
7. bank_account

Decrypted values are only shown to authorized agents in API responses.

---

## Notes

- Applications in `approved` or `rejected` status cannot be modified
- Applications in `draft` or `info_requested` can be updated and resubmitted
- Temporary passwords are 12+ characters with uppercase, lowercase, digits, and symbols
- Business admins must change password on first login
- All status changes are audit logged
