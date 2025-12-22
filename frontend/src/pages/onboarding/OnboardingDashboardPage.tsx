import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { UserPlus, TrendingUp, CalendarDays, Building2, Clock, CheckCircle } from 'lucide-react';
import { useOnboardingStats, useApplications } from '@/hooks/useOnboarding';
import { formatDate } from '@/lib/formatters';
import type { OnboardingStatus } from '@/types/onboarding';

const statusColors: Record<OnboardingStatus, string> = {
  draft: 'bg-gray-500',
  submitted: 'bg-blue-500',
  under_review: 'bg-yellow-500',
  approved: 'bg-green-500',
  rejected: 'bg-red-500',
  info_requested: 'bg-orange-500',
};

const statusLabels: Record<OnboardingStatus, string> = {
  draft: 'Draft',
  submitted: 'Submitted',
  under_review: 'Under Review',
  approved: 'Approved',
  rejected: 'Rejected',
  info_requested: 'Info Requested',
};

export const OnboardingDashboardPage = () => {
  const navigate = useNavigate();

  const { data: stats, isLoading: statsLoading } = useOnboardingStats();

  // Get recent applications (first 5)
  const { data: recentData, isLoading: recentLoading } = useApplications({
    page: 1,
    page_size: 5,
  });

  const recentApplications = recentData?.items || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold">Onboarding Dashboard</h1>
          <p className="mt-2 text-muted-foreground">
            Manage business onboarding and view statistics
          </p>
        </div>
        <Button onClick={() => navigate('/onboarding/create')} size="lg">
          <UserPlus className="mr-2 h-5 w-5" />
          Create New Application
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Applications</CardTitle>
            <Building2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {statsLoading ? (
              <Skeleton className="h-8 w-16" />
            ) : (
              <div className="text-2xl font-bold">{stats?.total_applications || 0}</div>
            )}
            <p className="text-xs text-muted-foreground">All time</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Approved This Month</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {statsLoading ? (
              <Skeleton className="h-8 w-16" />
            ) : (
              <div className="text-2xl font-bold">{stats?.approved_this_month || 0}</div>
            )}
            <p className="text-xs text-muted-foreground">Approved in current month</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Review</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {statsLoading ? (
              <Skeleton className="h-8 w-16" />
            ) : (
              <div className="text-2xl font-bold">
                {(stats?.submitted || 0) + (stats?.under_review || 0)}
              </div>
            )}
            <p className="text-xs text-muted-foreground">Awaiting action</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Processing Time</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {statsLoading ? (
              <Skeleton className="h-8 w-16" />
            ) : (
              <div className="text-2xl font-bold">
                {stats?.avg_processing_days ? `${stats.avg_processing_days.toFixed(1)}d` : 'N/A'}
              </div>
            )}
            <p className="text-xs text-muted-foreground">Average days</p>
          </CardContent>
        </Card>
      </div>

      {/* Status Breakdown */}
      <Card>
        <CardHeader>
          <CardTitle>Applications by Status</CardTitle>
          <CardDescription>Current distribution of application statuses</CardDescription>
        </CardHeader>
        <CardContent>
          {statsLoading ? (
            <div className="grid gap-3 md:grid-cols-3 lg:grid-cols-6">
              {Array.from({ length: 6 }).map((_, i) => (
                <Skeleton key={i} className="h-20 w-full" />
              ))}
            </div>
          ) : (
            <div className="grid gap-3 md:grid-cols-3 lg:grid-cols-6">
              <div className="rounded-lg border p-4">
                <div className="text-2xl font-bold">{stats?.draft || 0}</div>
                <p className="text-xs text-muted-foreground">Draft</p>
              </div>
              <div className="rounded-lg border p-4">
                <div className="text-2xl font-bold">{stats?.submitted || 0}</div>
                <p className="text-xs text-muted-foreground">Submitted</p>
              </div>
              <div className="rounded-lg border p-4">
                <div className="text-2xl font-bold">{stats?.under_review || 0}</div>
                <p className="text-xs text-muted-foreground">Under Review</p>
              </div>
              <div className="rounded-lg border p-4">
                <div className="text-2xl font-bold">{stats?.approved || 0}</div>
                <p className="text-xs text-muted-foreground">Approved</p>
              </div>
              <div className="rounded-lg border p-4">
                <div className="text-2xl font-bold">{stats?.rejected || 0}</div>
                <p className="text-xs text-muted-foreground">Rejected</p>
              </div>
              <div className="rounded-lg border p-4">
                <div className="text-2xl font-bold">{stats?.info_requested || 0}</div>
                <p className="text-xs text-muted-foreground">Info Requested</p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Recent Applications */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Recent Applications</CardTitle>
              <CardDescription>Latest applications submitted to the system</CardDescription>
            </div>
            <Button variant="outline" onClick={() => navigate('/onboarding/queue')}>
              View All
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {recentLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-20 w-full" />
              ))}
            </div>
          ) : recentApplications && recentApplications.length > 0 ? (
            <div className="space-y-3">
              {recentApplications.map((app) => (
                <div
                  key={app.id}
                  className="flex items-center justify-between rounded-lg border p-4 hover:bg-accent cursor-pointer transition-colors"
                  onClick={() => navigate(`/onboarding/applications/${app.id}`)}
                >
                  <div className="flex items-center gap-4">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10">
                      <Building2 className="h-5 w-5 text-primary" />
                    </div>
                    <div>
                      <p className="font-medium">{app.business_name}</p>
                      <p className="text-sm text-muted-foreground">
                        {app.owner_name} - {formatDate(app.created_at)}
                      </p>
                    </div>
                  </div>
                  <Badge
                    variant="secondary"
                    className={`${statusColors[app.status]} text-white`}
                  >
                    {statusLabels[app.status]}
                  </Badge>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Building2 className="mb-4 h-12 w-12 text-muted-foreground/50" />
              <h3 className="mb-2 text-lg font-semibold">No applications yet</h3>
              <p className="mb-4 text-sm text-muted-foreground">
                Get started by creating your first application
              </p>
              <Button onClick={() => navigate('/onboarding/create')}>
                <UserPlus className="mr-2 h-4 w-4" />
                Create New Application
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
          <CardDescription>Common tasks and shortcuts</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-2">
          <Button
            variant="outline"
            className="h-auto flex-col items-start gap-2 p-4"
            onClick={() => navigate('/onboarding/create')}
          >
            <UserPlus className="h-5 w-5" />
            <div className="text-left">
              <p className="font-medium">Create New Application</p>
              <p className="text-xs text-muted-foreground">
                Start a new business application
              </p>
            </div>
          </Button>

          <Button
            variant="outline"
            className="h-auto flex-col items-start gap-2 p-4"
            onClick={() => navigate('/onboarding/queue')}
          >
            <Building2 className="h-5 w-5" />
            <div className="text-left">
              <p className="font-medium">View Queue</p>
              <p className="text-xs text-muted-foreground">
                See all onboarding applications
              </p>
            </div>
          </Button>
        </CardContent>
      </Card>
    </div>
  );
};
