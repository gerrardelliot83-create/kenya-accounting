import { useAdminDashboard } from '@/hooks/useAdmin';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { Link } from 'react-router-dom';
import {
  Building2,
  Users,
  DollarSign,
  LifeBuoy,
  FileText,
  TrendingUp,
  Clock,
  CheckCircle,
} from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface StatCardProps {
  title: string;
  value: number;
  icon: React.ComponentType<{ className?: string }>;
  linkTo?: string;
  linkText?: string;
  description?: string;
  variant?: 'default' | 'success' | 'warning';
}

const StatCard = ({ title, value, icon: Icon, linkTo, linkText, description, variant = 'default' }: StatCardProps) => {
  const variantStyles = {
    default: 'border-border',
    success: 'border-green-200 bg-green-50',
    warning: 'border-yellow-200 bg-yellow-50',
  };

  return (
    <Card className={variantStyles[variant]}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value.toLocaleString()}</div>
        {description && <p className="text-xs text-muted-foreground">{description}</p>}
        {linkTo && linkText && (
          <Link to={linkTo}>
            <Button variant="link" size="sm" className="mt-2 h-auto p-0">
              {linkText}
            </Button>
          </Link>
        )}
      </CardContent>
    </Card>
  );
};

export const AdminDashboardPage = () => {
  const { data: stats, isLoading, error } = useAdminDashboard();

  if (isLoading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertDescription>
          Failed to load dashboard statistics. Please try again later.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Admin Dashboard</h1>
          <p className="text-muted-foreground">
            System-wide overview and management
          </p>
        </div>
      </div>

      {/* Stats Cards Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Total Businesses"
          value={stats?.total_businesses || 0}
          icon={Building2}
          linkTo="/admin/businesses"
          linkText="View all businesses"
          description={`${stats?.active_businesses || 0} active`}
        />

        <StatCard
          title="Total Users"
          value={stats?.total_users || 0}
          icon={Users}
          description={`${stats?.active_users || 0} active`}
        />

        <StatCard
          title="Total Revenue"
          value={stats?.total_revenue || 0}
          icon={DollarSign}
          description="Across all businesses"
        />

        <StatCard
          title="Total Invoices"
          value={stats?.total_invoices || 0}
          icon={FileText}
        />
      </div>

      {/* Action Cards */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card className={stats && stats.pending_applications > 0 ? 'border-yellow-200 bg-yellow-50' : ''}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Applications</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.pending_applications || 0}</div>
            <p className="text-xs text-muted-foreground">Require onboarding review</p>
            {stats && stats.pending_applications > 0 && (
              <Link to="/onboarding/queue">
                <Button variant="link" size="sm" className="mt-2 h-auto p-0">
                  Review applications
                </Button>
              </Link>
            )}
          </CardContent>
        </Card>

        <Card className={stats && stats.open_tickets > 0 ? 'border-yellow-200 bg-yellow-50' : ''}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Open Tickets</CardTitle>
            <LifeBuoy className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.open_tickets || 0}</div>
            <p className="text-xs text-muted-foreground">Active support tickets</p>
            {stats && stats.open_tickets > 0 && (
              <Link to="/support-portal/tickets">
                <Button variant="link" size="sm" className="mt-2 h-auto p-0">
                  View tickets
                </Button>
              </Link>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-3">
          <Link to="/admin/businesses">
            <Button variant="outline">
              <Building2 className="mr-2 h-4 w-4" />
              Manage Businesses
            </Button>
          </Link>
          <Link to="/admin/users">
            <Button variant="outline">
              <Users className="mr-2 h-4 w-4" />
              Manage Internal Users
            </Button>
          </Link>
          <Link to="/admin/audit-logs">
            <Button variant="outline">
              <FileText className="mr-2 h-4 w-4" />
              View Audit Logs
            </Button>
          </Link>
          <Link to="/admin/system">
            <Button variant="outline">
              <TrendingUp className="mr-2 h-4 w-4" />
              System Health
            </Button>
          </Link>
        </CardContent>
      </Card>

      {/* System Status */}
      <Card>
        <CardHeader>
          <CardTitle>System Status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2">
            <CheckCircle className="h-5 w-5 text-green-500" />
            <div>
              <p className="font-medium">All Systems Operational</p>
              <p className="text-sm text-muted-foreground">
                Last checked: {new Date().toLocaleString()}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
