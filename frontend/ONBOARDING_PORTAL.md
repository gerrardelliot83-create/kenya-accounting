# Onboarding Portal - Documentation

## Overview

The Onboarding Portal is a dedicated interface for internal onboarding agents to set up new business accounts in the Kenya SMB Accounting system. It features a multi-step wizard, queue management, and comprehensive statistics tracking.

## Architecture

### Authentication & Authorization
- **Role-Based Access**: Only users with `onboarding_agent` role can access the portal
- **Protected Routes**: All routes are protected using the existing `ProtectedRoute` component
- **Separate Layout**: Custom `OnboardingLayout` component distinct from the main application

### State Management
- **Global State**: Zustand (via existing `authStore`)
- **Server State**: React Query for data fetching and caching
- **Form State**: React Hook Form with Zod validation

### Data Persistence
- **Mock Service Layer**: LocalStorage-based implementation for demonstration
- **Ready for Backend**: Service layer designed to easily swap with real API calls

## File Structure

```
frontend/src/
├── components/
│   └── layout/
│       └── OnboardingLayout.tsx           # Onboarding portal layout
├── lib/
│   ├── kenya-constants.ts                 # Kenya-specific data (counties, industries)
│   └── kenya-validation.ts                # Validation functions (KRA PIN, phone, VAT)
├── pages/
│   └── onboarding/
│       ├── OnboardingDashboardPage.tsx    # Dashboard with stats
│       ├── CreateBusinessPage.tsx         # Multi-step wizard
│       ├── OnboardingQueuePage.tsx        # Queue management
│       ├── OnboardingSettingsPage.tsx     # Settings (placeholder)
│       └── index.ts                       # Exports
├── services/
│   └── onboardingService.ts               # Mock service layer
├── types/
│   └── onboarding.ts                      # TypeScript type definitions
└── routes/
    └── index.tsx                          # Updated with onboarding routes
```

## Features

### 1. Onboarding Dashboard
**Route**: `/onboarding`

**Features**:
- Statistics cards showing businesses created today/week/month/total
- Recent onboardings list with status badges
- Quick action buttons
- Responsive grid layout

**API Calls**:
- `getOnboardingStats()` - Fetches statistics
- `getRecentOnboardings(5)` - Fetches 5 most recent items

### 2. Business Creation Wizard
**Route**: `/onboarding/create`

**Multi-Step Process**:

**Step 1: Business Information**
- Business Name (required)
- Business Type: Sole Proprietor | Partnership | Limited Company
- KRA PIN (validated format: A123456789Z)
- Industry/Sector (dropdown)

**Step 2: Contact Information**
- Phone Number (Kenya format: +254XXXXXXXXX or 07XXXXXXXX)
- Email Address
- Physical Address
- County (47 Kenyan counties)

**Step 3: Tax Configuration**
- Tax Regime: VAT or TOT (radio selection)
- VAT Number (if VAT selected, format: P123456789A)
- Estimated Annual Turnover (if TOT selected)
- Filing Frequency: Monthly | Quarterly

**Step 4: Primary User Setup**
- Full Name
- Email (login email)
- Phone Number
- Temporary Password (with generator and copy-to-clipboard)

**Step 5: Review & Confirm**
- Summary of all entered information
- Organized in collapsible sections
- Submit button to create business

**Validation**:
- Step-by-step validation using Zod schemas
- Cannot proceed to next step if current step is invalid
- Real-time error messages
- Kenya-specific format validation

**State Persistence**:
- Wizard state saved as user progresses
- Can navigate back without losing data
- Form values preserved across steps

### 3. Onboarding Queue
**Route**: `/onboarding/queue`

**Features**:
- Filterable list of all onboarding requests
- Search by business name or agent name
- Status filter: All | Pending | In Progress | Completed | Failed
- Date range filtering (start/end dates)
- Pagination (20 items per page)
- Status badges with color coding
- Responsive table layout

**Filters**:
- Search (client-side filtering)
- Status dropdown
- Date range pickers
- Clear all filters button

### 4. Settings Page
**Route**: `/onboarding/settings`

Currently a placeholder for future configuration options.

## Kenya-Specific Data

### Counties (47 total)
Baringo, Bomet, Bungoma, Busia, Elgeyo-Marakwet, Embu, Garissa, Homa Bay, Isiolo, Kajiado, Kakamega, Kericho, Kiambu, Kilifi, Kirinyaga, Kisii, Kisumu, Kitui, Kwale, Laikipia, Lamu, Machakos, Makueni, Mandera, Marsabit, Meru, Migori, Mombasa, Muranga, Nairobi, Nakuru, Nandi, Narok, Nyamira, Nyandarua, Nyeri, Samburu, Siaya, Taita-Taveta, Tana River, Tharaka-Nithi, Trans Nzoia, Turkana, Uasin Gishu, Vihiga, Wajir, West Pokot

### Industries
Agriculture, Construction, Education, Finance & Insurance, Healthcare, Hospitality, Information Technology, Manufacturing, Professional Services, Real Estate, Retail, Transportation, Wholesale Trade, Other

### Validation Rules

**KRA PIN**:
- Format: Letter + 9 digits + Letter
- Example: A123456789Z
- Regex: `/^[A-Z]\d{9}[A-Z]$/`

**Phone Number**:
- Formats: +254XXXXXXXXX or 07XXXXXXXX or 01XXXXXXXX
- Regex: `/^(\+254|0)[17]\d{8}$/`
- Auto-formats to international format (+254...)

**VAT Number**:
- Format: P followed by 9 digits, optional letter
- Example: P123456789A
- Regex: `/^P\d{9}[A-Z]?$/`

### Tax Regimes
- **VAT (Value Added Tax)**: For businesses with turnover > KES 5M
- **TOT (Turnover Tax)**: For businesses with turnover < KES 5M

### Filing Frequencies
- Monthly
- Quarterly

## API Service Layer

### Mock Implementation
The `onboardingService.ts` uses localStorage to simulate backend operations:

```typescript
// Create a business
await onboardingService.createBusiness(data, agentId, agentName);

// Get onboarding queue
await onboardingService.getOnboardingQueue({ status: 'completed', limit: 20 });

// Get statistics
await onboardingService.getOnboardingStats();

// Get recent onboardings
await onboardingService.getRecentOnboardings(5);

// Update status
await onboardingService.updateOnboardingStatus(id, 'completed', 'Notes...');
```

### Replacing with Real API
To integrate with backend:

1. Update `onboardingService.ts` to use `apiClient` (similar to contacts/invoices)
2. Add API endpoints to `lib/api.ts`:
   ```typescript
   async createBusiness(data: BusinessCreateData): Promise<Business> {
     const response = await this.client.post<Business>('/onboarding/businesses', data);
     return response.data;
   }
   ```
3. No changes needed to components - they use the service layer

## TypeScript Types

All types are defined in `types/onboarding.ts`:

```typescript
BusinessType = 'sole_proprietor' | 'partnership' | 'limited_company'
TaxRegime = 'VAT' | 'TOT'
FilingFrequency = 'monthly' | 'quarterly'
OnboardingStatus = 'pending' | 'in_progress' | 'completed' | 'failed'

Business
BusinessCreateData
OnboardingItem
OnboardingStats
OnboardingQueueParams
OnboardingQueueResponse
```

## Routing Configuration

**Protected Routes** (require `onboarding_agent` role):
- `/onboarding` - Dashboard
- `/onboarding/create` - Create business wizard
- `/onboarding/queue` - Queue management
- `/onboarding/settings` - Settings

**Access Control**:
- Users without authentication → Redirected to `/login`
- Users with wrong role → "Access Denied" page
- Must change password → Redirected to `/change-password`

## UI/UX Features

### Layout
- Responsive sidebar (collapsible on mobile)
- Agent info displayed in sidebar and header
- Logo and portal branding
- Consistent navigation

### Progress Indicator
- Visual wizard steps (1-5)
- Check marks on completed steps
- Color-coded progress bar
- Mobile-friendly

### Form Experience
- Real-time validation
- Clear error messages
- Helpful placeholder text
- Format hints (e.g., "Format: A123456789Z")
- Auto-uppercase for KRA PIN and VAT number
- Password generator with copy button
- Disabled states during submission

### Data Display
- Color-coded status badges
- Skeleton loaders during fetch
- Empty states with helpful CTAs
- Hover effects on interactive elements
- Responsive tables and cards

### Accessibility
- Semantic HTML
- ARIA labels on interactive elements
- Keyboard navigation support
- Focus management
- Screen reader friendly

## Security Considerations

### [SECURITY] Authentication Tokens
- Tokens stored in httpOnly cookies (via existing auth system)
- No sensitive data in localStorage except mock demo data
- Role-based access control enforced at route level

### Input Validation
- All inputs validated with Zod schemas
- Kenya-specific format validation
- Email validation
- Phone number format validation
- No XSS vulnerabilities (React escapes by default)

### Data Handling
- Temporary passwords should be transmitted securely (HTTPS)
- Users forced to change password on first login
- No sensitive data logged to console in production

## Testing Recommendations

### Unit Tests
- Validation functions (`kenya-validation.ts`)
- Form schemas
- Service layer methods

### Integration Tests
- Multi-step wizard flow
- Form validation across steps
- Queue filtering and pagination
- Statistics calculations

### E2E Tests
- Complete onboarding flow
- Role-based access control
- Error handling
- Mobile responsiveness

## Future Enhancements

### Phase 2 Features
1. **Bulk Onboarding**: CSV import for multiple businesses
2. **Document Upload**: KRA certificate, business registration
3. **Email Notifications**: Send credentials to new users
4. **Onboarding Templates**: Pre-filled forms for common business types
5. **Audit Trail**: Track all changes to onboarding records
6. **Export Functionality**: Download queue as CSV/PDF
7. **Advanced Analytics**: Charts and graphs for onboarding metrics
8. **Business Profile**: Detailed view of onboarded businesses
9. **User Management**: Edit/deactivate primary users
10. **Settings**: Configurable default values, email templates

### Technical Improvements
1. **Real-time Updates**: WebSocket for queue updates
2. **Optimistic Updates**: Immediate UI feedback
3. **Form Auto-save**: Persist wizard state to backend
4. **File Upload**: Drag-and-drop for documents
5. **Print Support**: Printable summary for onboarding records

## Support & Maintenance

### Common Issues

**Issue**: User can't access portal
**Solution**: Verify user role is `onboarding_agent` in auth system

**Issue**: Form validation errors
**Solution**: Check Kenya-specific format requirements (KRA PIN, phone, VAT)

**Issue**: Stats not updating
**Solution**: Invalidate React Query cache or refresh browser

### Monitoring
- Track onboarding completion times
- Monitor form abandonment rates
- Log validation errors for improvement
- Track agent performance metrics

## Conclusion

The Onboarding Portal is production-ready for internal use with mock data. It follows all established patterns from the existing codebase, maintains type safety, implements proper validation, and provides an excellent user experience for onboarding agents.

To deploy with real backend:
1. Implement backend API endpoints
2. Update `onboardingService.ts` to use API client
3. Test thoroughly
4. Deploy
