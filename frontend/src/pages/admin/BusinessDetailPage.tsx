import { useParams, useNavigate } from 'react-router-dom';
import { useBusiness } from '@/hooks/useAdmin';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  ArrowLeft,
  Building2,
  Users,
  FileText,
  DollarSign,
  TrendingDown,
  Calendar,
  Shield,
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

export const BusinessDetailPage = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: business, isLoading, error } = useBusiness(id!);

  if (isLoading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error || !business) {
    return (
      <div className="space-y-6">
        <Button variant="ghost" onClick={() => navigate('/admin/businesses')}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Businesses
        </Button>
        <Alert variant="destructive">
          <AlertDescription>
            Failed to load business details. The business may not exist or you may not have permission to view it.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  const getStatusBadge = (status: string) => {
    const variants: Record<string, 'default' | 'secondary' | 'destructive'> = {
      active: 'default',
      inactive: 'secondary',
      suspended: 'destructive',
    };

    return (
      <Badge variant={variants[status] || 'secondary'}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </Badge>
    );
  };

  const getUserRoleBadge = (role: string) => {
    const variants: Record<string, 'default' | 'secondary'> = {
      business_admin: 'default',
      bookkeeper: 'secondary',
    };

    return (
      <Badge variant={variants[role] || 'secondary'}>
        {role.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
      </Badge>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" onClick={() => navigate('/admin/businesses')}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back
          </Button>
          <div>
            <h1 className="text-3xl font-bold tracking-tight">{business.business_name}</h1>
            <p className="text-muted-foreground">Business Details</p>
          </div>
        </div>
        <div className="flex gap-2">
          {getStatusBadge(business.status)}
        </div>
      </div>

      {/* Business Information */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Building2 className="h-5 w-5" />
              Business Information
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Business Type</p>
              <p className="capitalize">{business.business_type.replace(/_/g, ' ')}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Status</p>
              <p className="capitalize">{business.status}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Created</p>
              <p>
                {new Date(business.created_at).toLocaleDateString()} (
                {formatDistanceToNow(new Date(business.created_at), { addSuffix: true })})
              </p>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Last Updated</p>
              <p>
                {new Date(business.updated_at).toLocaleDateString()} (
                {formatDistanceToNow(new Date(business.updated_at), { addSuffix: true })})
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5" />
              Business Admin
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Name</p>
              <p>{business.business_admin_name || 'N/A'}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Email</p>
              <p className="font-mono text-sm">{business.business_admin_email_masked || 'N/A'}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Activity Summary */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Users</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{business.user_count}</div>
            <p className="text-xs text-muted-foreground">Total users</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Invoices</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{business.invoice_count}</div>
            <p className="text-xs text-muted-foreground">Total invoices</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Revenue</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              KES {business.total_revenue.toLocaleString('en-KE', { minimumFractionDigits: 2 })}
            </div>
            <p className="text-xs text-muted-foreground">Total revenue</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Expenses</CardTitle>
            <TrendingDown className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              KES {business.total_expenses.toLocaleString('en-KE', { minimumFractionDigits: 2 })}
            </div>
            <p className="text-xs text-muted-foreground">{business.expense_count} expenses</p>
          </CardContent>
        </Card>
      </div>

      {/* Users Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Business Users
          </CardTitle>
        </CardHeader>
        <CardContent>
          {business.users.length === 0 ? (
            <div className="flex h-32 items-center justify-center text-muted-foreground">
              No users found for this business
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Email</TableHead>
                    <TableHead>Role</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Last Login</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {business.users.map((user) => (
                    <TableRow key={user.id}>
                      <TableCell className="font-medium">{user.full_name}</TableCell>
                      <TableCell className="font-mono text-sm">{user.email_masked}</TableCell>
                      <TableCell>{getUserRoleBadge(user.role)}</TableCell>
                      <TableCell>
                        <Badge variant={user.is_active ? 'default' : 'secondary'}>
                          {user.is_active ? 'Active' : 'Inactive'}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {user.last_login
                          ? formatDistanceToNow(new Date(user.last_login), { addSuffix: true })
                          : 'Never'}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-3">
          <Button variant="outline" disabled>
            <FileText className="mr-2 h-4 w-4" />
            View Invoices
          </Button>
          <Button variant="outline" disabled>
            <Calendar className="mr-2 h-4 w-4" />
            View Activity Log
          </Button>
          <Button variant="destructive" disabled>
            Deactivate Business
          </Button>
        </CardContent>
      </Card>
    </div>
  );
};
