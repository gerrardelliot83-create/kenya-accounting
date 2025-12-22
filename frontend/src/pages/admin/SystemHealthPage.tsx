import { useSystemHealth } from '@/hooks/useAdmin';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Server,
  Database,
  Clock,
  AlertCircle,
  CheckCircle,
  Users,
  Activity,
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

interface MetricCardProps {
  title: string;
  value: string | number;
  icon: React.ComponentType<{ className?: string }>;
  status?: 'healthy' | 'warning' | 'critical';
  description?: string;
}

const MetricCard = ({ title, value, icon: Icon, status = 'healthy', description }: MetricCardProps) => {
  const statusColors = {
    healthy: 'border-green-200 bg-green-50',
    warning: 'border-yellow-200 bg-yellow-50',
    critical: 'border-red-200 bg-red-50',
  };

  const statusIcons = {
    healthy: <CheckCircle className="h-4 w-4 text-green-500" />,
    warning: <AlertCircle className="h-4 w-4 text-yellow-500" />,
    critical: <AlertCircle className="h-4 w-4 text-red-500" />,
  };

  return (
    <Card className={statusColors[status]}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <div className="flex items-center gap-2">
          {statusIcons[status]}
          <Icon className="h-4 w-4 text-muted-foreground" />
        </div>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {description && <p className="text-xs text-muted-foreground mt-1">{description}</p>}
      </CardContent>
    </Card>
  );
};

export const SystemHealthPage = () => {
  const { data: health, isLoading, error } = useSystemHealth();

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
          Failed to load system health metrics. Please try again later.
        </AlertDescription>
      </Alert>
    );
  }

  const getResponseTimeStatus = (ms: number): 'healthy' | 'warning' | 'critical' => {
    if (ms < 200) return 'healthy';
    if (ms < 500) return 'warning';
    return 'critical';
  };

  const getErrorRateStatus = (percent: number): 'healthy' | 'warning' | 'critical' => {
    if (percent < 1) return 'healthy';
    if (percent < 5) return 'warning';
    return 'critical';
  };

  const getDatabaseStatusVariant = (status: string): 'default' | 'secondary' | 'destructive' => {
    if (status === 'healthy') return 'default';
    if (status === 'degraded') return 'secondary';
    return 'destructive';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">System Health</h1>
          <p className="text-muted-foreground">
            Monitor application performance and status
          </p>
        </div>
        {health && (
          <Badge variant="outline" className="text-sm">
            Last updated: {formatDistanceToNow(new Date(health.last_updated), { addSuffix: true })}
          </Badge>
        )}
      </div>

      {/* Overall Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Overall System Status
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-3">
            {health?.database_status === 'healthy' &&
             health.api_response_time_ms < 500 &&
             health.error_rate_percent < 5 ? (
              <>
                <CheckCircle className="h-8 w-8 text-green-500" />
                <div>
                  <p className="text-lg font-semibold">All Systems Operational</p>
                  <p className="text-sm text-muted-foreground">
                    All services are running normally
                  </p>
                </div>
              </>
            ) : (
              <>
                <AlertCircle className="h-8 w-8 text-yellow-500" />
                <div>
                  <p className="text-lg font-semibold">Degraded Performance</p>
                  <p className="text-sm text-muted-foreground">
                    Some metrics are outside normal range
                  </p>
                </div>
              </>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Metrics Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="API Response Time"
          value={`${health?.api_response_time_ms || 0} ms`}
          icon={Clock}
          status={getResponseTimeStatus(health?.api_response_time_ms || 0)}
          description={
            health?.api_response_time_ms && health.api_response_time_ms < 200
              ? 'Excellent'
              : health?.api_response_time_ms && health.api_response_time_ms < 500
              ? 'Acceptable'
              : 'Slow'
          }
        />

        <MetricCard
          title="Error Rate"
          value={`${health?.error_rate_percent?.toFixed(2) || 0}%`}
          icon={AlertCircle}
          status={getErrorRateStatus(health?.error_rate_percent || 0)}
          description={
            health?.error_rate_percent && health.error_rate_percent < 1
              ? 'Normal'
              : health?.error_rate_percent && health.error_rate_percent < 5
              ? 'Elevated'
              : 'High'
          }
        />

        <MetricCard
          title="Active Sessions"
          value={health?.active_sessions || 0}
          icon={Users}
          status="healthy"
          description="Current user sessions"
        />

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Database Status</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <Badge variant={getDatabaseStatusVariant(health?.database_status || 'down')}>
                {health?.database_status?.toUpperCase() || 'UNKNOWN'}
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              {health?.database_status === 'healthy'
                ? 'All connections stable'
                : health?.database_status === 'degraded'
                ? 'Some connections slow'
                : 'Connection issues detected'}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Response Time Chart Placeholder */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Performance Over Time
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm font-medium">API Response Time</p>
                <span className="text-sm text-muted-foreground">
                  {health?.api_response_time_ms || 0} ms
                </span>
              </div>
              <Progress
                value={Math.min((health?.api_response_time_ms || 0) / 10, 100)}
                className="h-2"
              />
              <p className="text-xs text-muted-foreground mt-1">
                Target: &lt; 200ms for optimal performance
              </p>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm font-medium">Error Rate</p>
                <span className="text-sm text-muted-foreground">
                  {health?.error_rate_percent?.toFixed(2) || 0}%
                </span>
              </div>
              <Progress
                value={Math.min((health?.error_rate_percent || 0) * 20, 100)}
                className="h-2"
              />
              <p className="text-xs text-muted-foreground mt-1">
                Target: &lt; 1% for healthy system
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Service Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Server className="h-5 w-5" />
            Service Status
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 rounded-md bg-muted/50">
              <div className="flex items-center gap-3">
                <CheckCircle className="h-5 w-5 text-green-500" />
                <div>
                  <p className="font-medium">API Server</p>
                  <p className="text-xs text-muted-foreground">Main application backend</p>
                </div>
              </div>
              <Badge variant="default">Operational</Badge>
            </div>

            <div className="flex items-center justify-between p-3 rounded-md bg-muted/50">
              <div className="flex items-center gap-3">
                <CheckCircle
                  className={`h-5 w-5 ${
                    health?.database_status === 'healthy'
                      ? 'text-green-500'
                      : 'text-yellow-500'
                  }`}
                />
                <div>
                  <p className="font-medium">Database</p>
                  <p className="text-xs text-muted-foreground">PostgreSQL primary instance</p>
                </div>
              </div>
              <Badge variant={getDatabaseStatusVariant(health?.database_status || 'down')}>
                {health?.database_status || 'Unknown'}
              </Badge>
            </div>

            <div className="flex items-center justify-between p-3 rounded-md bg-muted/50">
              <div className="flex items-center gap-3">
                <CheckCircle className="h-5 w-5 text-green-500" />
                <div>
                  <p className="font-medium">Authentication Service</p>
                  <p className="text-xs text-muted-foreground">User authentication and sessions</p>
                </div>
              </div>
              <Badge variant="default">Operational</Badge>
            </div>

            <div className="flex items-center justify-between p-3 rounded-md bg-muted/50">
              <div className="flex items-center gap-3">
                <CheckCircle className="h-5 w-5 text-green-500" />
                <div>
                  <p className="font-medium">File Storage</p>
                  <p className="text-xs text-muted-foreground">Document and file management</p>
                </div>
              </div>
              <Badge variant="default">Operational</Badge>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
