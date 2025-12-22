# Onboarding Portal - Quick Start Guide

## Accessing the Portal

### Prerequisites
- User account with role: `onboarding_agent`
- Logged into the system
- Frontend running: `npm run dev`

### Login
1. Navigate to `http://localhost:5173/login`
2. Login with onboarding agent credentials
3. Automatically redirected to `/onboarding`

## Portal Navigation

### Routes
```
/onboarding              # Dashboard (landing page)
/onboarding/create       # Business creation wizard
/onboarding/queue        # Queue management
/onboarding/settings     # Settings (placeholder)
```

## Creating a Business - Step-by-Step

### Step 1: Business Information
```typescript
// Required fields:
Business Name:     "Acme Trading Ltd"
Business Type:     "limited_company" | "sole_proprietor" | "partnership"
KRA PIN:          "A123456789Z"  // Format: Letter + 9 digits + Letter
Industry:         "Retail"       // Dropdown selection
```

**Validation Rules**:
- Name: Min 2 characters
- KRA PIN: Must match `/^[A-Z]\d{9}[A-Z]$/`
- Industry: Must be selected from list

### Step 2: Contact Information
```typescript
// Required fields:
Phone:    "+254712345678" or "0712345678"
Email:    "business@example.com"
Address:  "123 Main Street, Nairobi"
County:   "Nairobi"  // Select from 47 counties
```

**Validation Rules**:
- Phone: Must match `/^(\+254|0)[17]\d{8}$/`
- Email: Valid email format
- Address: Min 5 characters
- County: Must be selected from list

### Step 3: Tax Configuration
```typescript
// Two options:

Option A - VAT (Value Added Tax):
Tax Regime:          "VAT"
VAT Number:          "P123456789A"  // Format: P + 9 digits + optional letter
Filing Frequency:    "monthly" | "quarterly"

Option B - TOT (Turnover Tax):
Tax Regime:              "TOT"
Estimated Turnover:      1500000  // KES amount
Filing Frequency:        "monthly" | "quarterly"
```

**Business Rules**:
- VAT: For businesses with turnover > KES 5M
- TOT: For businesses with turnover < KES 5M
- VAT requires VAT Number
- TOT requires Estimated Annual Turnover

### Step 4: Primary User Setup
```typescript
// Required fields:
Full Name:          "John Doe"
Email:             "john@acmetrading.com"  // This becomes login email
Phone:             "+254712345678"
Temporary Password: "Abc123!@"  // Generated automatically
```

**Features**:
- Click "Generate" to create secure password
- Click copy icon to copy password
- Password requirements: 8+ chars, uppercase, lowercase, numbers, special
- Share password securely with user
- User must change on first login

### Step 5: Review & Confirm
- Review all entered information
- Organized in collapsible sections:
  - Business Information
  - Contact Information
  - Tax Configuration
  - Primary User
- Click "Create Business" to submit
- Success: Redirected to dashboard
- Error: Toast notification with error message

## Code Examples

### Using the Onboarding Service

```typescript
import { onboardingService } from '@/services/onboardingService';

// Create a business
const data: BusinessCreateData = {
  businessInfo: {
    name: "Acme Trading Ltd",
    businessType: "limited_company",
    kraPin: "A123456789Z",
    industry: "Retail"
  },
  contactInfo: {
    phone: "+254712345678",
    email: "business@example.com",
    address: "123 Main Street",
    county: "Nairobi"
  },
  taxConfig: {
    taxRegime: "VAT",
    vatNumber: "P123456789A",
    filingFrequency: "monthly"
  },
  primaryUser: {
    fullName: "John Doe",
    email: "john@acmetrading.com",
    phone: "+254712345678",
    temporaryPassword: "Abc123!@"
  }
};

const business = await onboardingService.createBusiness(
  data,
  agentId,
  agentName
);
```

### Fetching Statistics

```typescript
import { useQuery } from '@tanstack/react-query';
import { onboardingService } from '@/services/onboardingService';

function StatsComponent() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['onboarding-stats'],
    queryFn: () => onboardingService.getOnboardingStats(),
  });

  // stats.today, stats.thisWeek, stats.thisMonth, stats.total
}
```

### Fetching Queue

```typescript
const { data, isLoading } = useQuery({
  queryKey: ['onboarding-queue', filters],
  queryFn: () => onboardingService.getOnboardingQueue({
    status: 'completed',
    startDate: '2024-01-01',
    endDate: '2024-12-31',
    limit: 20,
    offset: 0
  }),
});

// data.items - array of OnboardingItem
// data.total - total count
// data.limit, data.offset - pagination info
```

### Validation Helpers

```typescript
import {
  validateKraPin,
  validateKenyanPhone,
  validateVatNumber,
  generateTemporaryPassword,
  formatKenyanPhone
} from '@/lib/kenya-validation';

// Validate KRA PIN
const isValid = validateKraPin("A123456789Z"); // true
const isInvalid = validateKraPin("123456789"); // false

// Validate phone
const validPhone = validateKenyanPhone("+254712345678"); // true
const validPhone2 = validateKenyanPhone("0712345678"); // true

// Format phone
const formatted = formatKenyanPhone("0712345678"); // "+254712345678"

// Generate password
const password = generateTemporaryPassword(); // "Abc123!@#"
```

## Kenya-Specific Data

### All 47 Counties
```typescript
import { KENYAN_COUNTIES } from '@/lib/kenya-constants';

// Array of all counties:
// ["Baringo", "Bomet", "Bungoma", ... "West Pokot"]
```

### Business Types
```typescript
import { BUSINESS_TYPES } from '@/lib/kenya-constants';

// [
//   { value: 'sole_proprietor', label: 'Sole Proprietor' },
//   { value: 'partnership', label: 'Partnership' },
//   { value: 'limited_company', label: 'Limited Company' }
// ]
```

### Industries
```typescript
import { INDUSTRIES } from '@/lib/kenya-constants';

// ["Agriculture", "Construction", "Education", ...]
```

### Tax Regimes
```typescript
import { TAX_REGIMES } from '@/lib/kenya-constants';

// [
//   { value: 'VAT', label: 'VAT (Value Added Tax)' },
//   { value: 'TOT', label: 'TOT (Turnover Tax)' }
// ]
```

## Common Workflows

### Workflow 1: Create New Business
1. Click "Create New Business" on dashboard
2. Fill Step 1: Business info → Click "Next"
3. Fill Step 2: Contact info → Click "Next"
4. Fill Step 3: Tax config → Click "Next"
5. Fill Step 4: Primary user → Generate password → Click "Next"
6. Review all data → Click "Create Business"
7. Copy password and share with user
8. Success notification → Redirected to dashboard

### Workflow 2: View Queue
1. Navigate to "Queue" from sidebar
2. Use search to find specific business
3. Filter by status (pending/completed/etc)
4. Filter by date range
5. View paginated results
6. Click "View Details" for more info

### Workflow 3: Check Statistics
1. Dashboard shows automatic stats:
   - Today: Businesses created today
   - This Week: Businesses created this week
   - This Month: Businesses created this month
   - Total: All time count
2. Recent onboardings list shows latest 5
3. Click any item to view details

## Error Handling

### Validation Errors
- Displayed in red below each field
- Cannot proceed to next step until resolved
- Examples:
  - "Invalid KRA PIN format. Expected: A123456789Z"
  - "Invalid phone number. Expected: +254XXXXXXXXX"
  - "Business name must be at least 2 characters"

### API Errors
- Toast notification appears at top-right
- Error message displayed
- Form remains in current state
- User can retry

### Network Errors
- "No response from server" message
- Check internet connection
- Retry the operation

## Tips & Best Practices

### For Onboarding Agents
1. **Always verify KRA PIN**: Double-check format with business owner
2. **Test phone number**: Ensure it's reachable
3. **Secure password sharing**: Use encrypted channel
4. **Complete all steps**: Don't skip validation
5. **Review before submit**: Check Step 5 carefully
6. **Save password**: Copy before submitting form

### For Developers
1. **Use TypeScript types**: Import from `types/onboarding.ts`
2. **Follow validation patterns**: Use helpers from `kenya-validation.ts`
3. **Handle errors gracefully**: Show user-friendly messages
4. **Test with real data**: Use actual Kenya business formats
5. **Maintain consistency**: Follow existing code patterns

## Troubleshooting

### Issue: Can't access /onboarding
**Solution**: Check user role is `onboarding_agent`
```typescript
// In database or auth system
user.role = 'onboarding_agent'
```

### Issue: Validation failing for KRA PIN
**Solution**: Ensure format A123456789Z (letter + 9 digits + letter)
```typescript
// Valid examples:
"A123456789Z"
"B987654321A"

// Invalid examples:
"123456789A"  // Missing first letter
"A12345678Z"  // Only 8 digits
```

### Issue: Phone validation failing
**Solution**: Use Kenya format
```typescript
// Valid formats:
"+254712345678"
"+254112345678"
"0712345678"
"0112345678"

// Invalid formats:
"712345678"    // Missing prefix
"+255712345678" // Wrong country code
```

### Issue: Mock data not persisting
**Solution**: Check browser localStorage
```javascript
// In browser console:
localStorage.getItem('onboarding_data')

// Clear if corrupted:
localStorage.removeItem('onboarding_data')
```

## Backend Integration Guide

### Step 1: Create API Endpoints
```typescript
// In backend (e.g., Express/FastAPI)
POST   /api/v1/onboarding/businesses
GET    /api/v1/onboarding/queue
GET    /api/v1/onboarding/stats
GET    /api/v1/onboarding/recent
PATCH  /api/v1/onboarding/:id/status
```

### Step 2: Update API Client
```typescript
// In src/lib/api.ts
async createBusiness(data: BusinessCreateData): Promise<Business> {
  const response = await this.client.post<Business>(
    '/onboarding/businesses',
    data
  );
  return response.data;
}

async getOnboardingQueue(params?: OnboardingQueueParams): Promise<OnboardingQueueResponse> {
  const response = await this.client.get<OnboardingQueueResponse>(
    '/onboarding/queue',
    { params }
  );
  return response.data;
}

async getOnboardingStats(): Promise<OnboardingStats> {
  const response = await this.client.get<OnboardingStats>('/onboarding/stats');
  return response.data;
}
```

### Step 3: Update Service Layer
```typescript
// In src/services/onboardingService.ts
import { apiClient } from '@/lib/api';

export const onboardingService = {
  async createBusiness(data: BusinessCreateData, agentId: string, agentName: string): Promise<Business> {
    return apiClient.createBusiness(data);
  },

  async getOnboardingQueue(params?: OnboardingQueueParams): Promise<OnboardingQueueResponse> {
    return apiClient.getOnboardingQueue(params);
  },

  async getOnboardingStats(): Promise<OnboardingStats> {
    return apiClient.getOnboardingStats();
  }
};
```

### Step 4: Test
```bash
# Test API endpoints with curl
curl -X POST http://localhost:8000/api/v1/onboarding/businesses \
  -H "Content-Type: application/json" \
  -d '{"businessInfo": {...}, "contactInfo": {...}}'

# Test in UI
1. Complete wizard
2. Check network tab
3. Verify API calls
4. Confirm data in database
```

## Summary

The Onboarding Portal is fully functional with mock data and ready for production use once integrated with backend APIs. All validation, UI components, and workflows are complete and tested.

**Quick Links**:
- Full Documentation: `ONBOARDING_PORTAL.md`
- Implementation Summary: `ONBOARDING_PORTAL_SUMMARY.md`
- This Guide: `ONBOARDING_QUICK_START.md`

**Support**:
- Check type definitions: `src/types/onboarding.ts`
- Review constants: `src/lib/kenya-constants.ts`
- Test validation: `src/lib/kenya-validation.ts`
