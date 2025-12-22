# Admin Portal Quick Start Guide

## Accessing the Admin Portal

1. **Login as System Admin**
   - Use credentials with `system_admin` role
   - After login, you'll see "Administration" section in sidebar

2. **Navigate to Admin Portal**
   - Click "Admin Dashboard" in sidebar, or
   - Navigate directly to `/admin`

## Key Features at a Glance

### Admin Dashboard (`/admin`)
View system-wide statistics and quick links:
- Total businesses, users, revenue, invoices
- Pending applications and open tickets
- Quick action buttons

### Business Directory (`/admin/businesses`)
Manage all businesses:
- Search by business name
- Filter by status and type
- Export to CSV
- Click any row to view details

### Business Detail (`/admin/businesses/:id`)
View detailed business information:
- Business info and admin contact
- Activity metrics
- List of users in the business

### Internal Users (`/admin/users`)
Manage system users:
- Filter by role (System Admin, Support Agent, Onboarding Agent)
- Create new users with temporary passwords
- Activate/deactivate users
- View last login times

### Audit Logs (`/admin/audit-logs`)
Monitor system activity:
- Filter by action, status, date range
- Expand rows to see full details
- Track user actions and system events

### System Health (`/admin/system`)
Monitor application performance:
- API response time
- Error rate
- Active sessions
- Database status
- Service status indicators

## Common Tasks

### Creating an Internal User

1. Navigate to `/admin/users`
2. Click "Add User" button
3. Fill in the form:
   - Full Name
   - Email address
   - Role (Support Agent, Onboarding Agent, or System Admin)
   - Temporary Password (min 8 characters)
4. Click "Create User"
5. User will be required to change password on first login

### Exporting Business Data

1. Navigate to `/admin/businesses`
2. Apply desired filters (optional)
3. Click "Export to CSV" button
4. CSV file will download automatically

### Reviewing Audit Logs

1. Navigate to `/admin/audit-logs`
2. Set filters:
   - Action type (login, create, update, delete, etc.)
   - Status (success, failure, error)
   - Date range
3. Click on any row's chevron icon to expand and see full details
4. Use pagination to browse through logs

### Checking System Health

1. Navigate to `/admin/system`
2. Review metrics:
   - Green indicators = healthy
   - Yellow indicators = warning
   - Red indicators = critical
3. Page auto-refreshes every 30 seconds

## API Endpoints Reference

All admin endpoints are prefixed with `/api/v1/admin/`:

```
GET    /admin/dashboard/stats          - Dashboard statistics
GET    /admin/businesses               - List businesses
GET    /admin/businesses/:id           - Get business details
GET    /admin/users                    - List internal users
POST   /admin/users                    - Create internal user
POST   /admin/users/:id/activate       - Activate user
POST   /admin/users/:id/deactivate     - Deactivate user
GET    /admin/audit-logs               - Get audit logs
GET    /admin/system/health            - Get system health
```

## Security Notes

### Email Masking
All email addresses are masked in the UI:
- Format: `j***@example.com`
- First character visible, rest masked
- Prevents accidental exposure of PII

### Role Requirements
- Only users with `system_admin` role can access admin portal
- Routes are protected with `ProtectedRoute` component
- Sidebar items filter based on user role

### Token Storage
- Auth tokens stored in httpOnly cookies
- No sensitive data in localStorage
- Automatic redirect to login on 401

## Development Tips

### Adding a New Admin Page

1. Create page component in `src/pages/admin/`
2. Add route in `src/routes/index.tsx` under `/admin` parent
3. Add navigation item to `adminNavItems` in `Sidebar.tsx`
4. Export from `src/pages/admin/index.ts`

### Creating a New API Endpoint

1. Add method to `ApiClient` class in `src/lib/api.ts`
2. Create React Query hook in `src/hooks/useAdmin.ts`
3. Add type definitions in `src/types/admin.ts`

### Using the Custom Hooks

```typescript
import { useAdminDashboard } from '@/hooks/useAdmin';

const MyComponent = () => {
  const { data, isLoading, error } = useAdminDashboard();

  if (isLoading) return <LoadingSpinner />;
  if (error) return <Alert>Error loading data</Alert>;

  return <div>{data.total_businesses}</div>;
};
```

### Mutation Example

```typescript
import { useCreateInternalUser } from '@/hooks/useAdmin';

const MyComponent = () => {
  const createUser = useCreateInternalUser();

  const handleSubmit = async (data) => {
    try {
      await createUser.mutateAsync(data);
      // Success - query will auto-invalidate
    } catch (error) {
      // Handle error
    }
  };

  return <button onClick={handleSubmit}>Create</button>;
};
```

## Troubleshooting

### "Failed to load dashboard statistics"
- Check if backend API is running
- Verify `/api/v1/admin/dashboard/stats` endpoint exists
- Check browser console for network errors
- Ensure user has `system_admin` role

### Sidebar doesn't show admin section
- Verify user role is `system_admin`
- Check `authStore` for current user
- Clear localStorage and re-login if needed

### Routes return 404
- Ensure `AdminLayout` is imported in routes
- Check route definitions in `src/routes/index.tsx`
- Verify `ProtectedRoute` allows `system_admin` role

### CSV export not working
- Check browser console for errors
- Ensure `data.businesses` array exists
- Verify browser allows downloads

## Component Library

Admin portal uses these Shadcn/UI components:
- `Card`, `CardHeader`, `CardContent`, `CardTitle`
- `Table`, `TableHeader`, `TableBody`, `TableRow`, `TableCell`
- `Button`
- `Input`
- `Select`, `SelectTrigger`, `SelectValue`, `SelectContent`, `SelectItem`
- `Badge`
- `Dialog`, `DialogContent`, `DialogHeader`, `DialogTitle`, `DialogFooter`
- `Skeleton`
- `Progress`
- `Alert`, `AlertDescription`
- `Label`
- `Separator`

## Icons Used

From `lucide-react`:
- `LayoutDashboard`, `Building2`, `Users`, `Shield`, `Server`
- `FileText`, `DollarSign`, `TrendingDown`, `Clock`
- `CheckCircle`, `AlertCircle`, `Search`, `Download`
- `Plus`, `UserX`, `UserCheck`, `ArrowLeft`
- `ChevronDown`, `ChevronRight`, `Activity`, `Database`

## Best Practices

1. **Always handle loading states**
   ```typescript
   if (isLoading) return <LoadingSpinner size="lg" />;
   ```

2. **Always handle error states**
   ```typescript
   if (error) return <Alert variant="destructive">Error message</Alert>;
   ```

3. **Always handle empty states**
   ```typescript
   if (!data?.items.length) return <EmptyState />;
   ```

4. **Use proper TypeScript types**
   ```typescript
   const { data } = useBusinesses(params); // data is BusinessListResponse
   ```

5. **Invalidate queries after mutations**
   ```typescript
   onSuccess: () => {
     queryClient.invalidateQueries({ queryKey: ['admin-internal-users'] });
   }
   ```

## Support

For issues or questions:
1. Check the implementation documentation
2. Review the component source code
3. Check browser console for errors
4. Verify API endpoint responses in Network tab
