import { useSupportStats, useAdminTickets } from '@/hooks/useAdminSupport';
import { SupportStatCard } from '@/components/support-portal';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { TicketStatusBadge, TicketPriorityBadge } from '@/components/support-portal';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { Link } from 'react-router-dom';
import {
  AlertCircle,
  Clock,
  CheckCircle,
  UserX,
  TrendingUp,
  Inbox,
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

export const SupportDashboardPage = () => {
  const { data: stats, isLoading: statsLoading } = useSupportStats();
  const { data: recentTickets, isLoading: ticketsLoading } = useAdminTickets({
    limit: 10,
    page: 1,
  });

  if (statsLoading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Support Dashboard</h1>
          <p className="text-muted-foreground">
            Monitor and manage customer support tickets
          </p>
        </div>
      </div>

      {/* Stats Cards Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        <SupportStatCard
          title="Open Tickets"
          count={stats?.total_open || 0}
          icon={Inbox}
          linkTo="/support-portal/tickets?status=open"
          linkText="View all"
          variant="default"
        />

        <SupportStatCard
          title="In Progress"
          count={stats?.total_in_progress || 0}
          icon={Clock}
          linkTo="/support-portal/tickets?status=in_progress"
          linkText="View all"
          variant="default"
        />

        <SupportStatCard
          title="Awaiting Response"
          count={stats?.total_waiting_customer || 0}
          icon={TrendingUp}
          linkTo="/support-portal/tickets?status=waiting_customer"
          linkText="View all"
          variant="default"
        />

        <SupportStatCard
          title="Unassigned"
          count={stats?.unassigned_count || 0}
          icon={UserX}
          linkTo="/support-portal/tickets?assigned=unassigned"
          linkText="View all"
          variant={stats && stats.unassigned_count > 0 ? 'urgent' : 'default'}
        />

        <SupportStatCard
          title="High Priority"
          count={stats?.high_priority_count || 0}
          icon={AlertCircle}
          linkTo="/support-portal/tickets?priority=urgent,high"
          linkText="View all"
          variant={stats && stats.high_priority_count > 0 ? 'urgent' : 'default'}
        />

        <SupportStatCard
          title="Resolved Today"
          count={stats?.resolved_today || 0}
          icon={CheckCircle}
          linkTo="/support-portal/tickets?status=resolved"
          linkText="View all"
          variant="success"
        />
      </div>

      {/* Average Resolution Time */}
      {stats && stats.avg_resolution_time_hours > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Performance Metrics</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <Clock className="h-5 w-5 text-muted-foreground" />
              <div>
                <p className="text-sm text-muted-foreground">Average Resolution Time</p>
                <p className="text-2xl font-bold">
                  {stats.avg_resolution_time_hours.toFixed(1)} hours
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-3">
          <Link to="/support-portal/tickets?assigned=unassigned">
            <Button variant="outline">
              <UserX className="mr-2 h-4 w-4" />
              View Unassigned Tickets
            </Button>
          </Link>
          <Link to="/support-portal/tickets?priority=urgent,high">
            <Button variant="outline">
              <AlertCircle className="mr-2 h-4 w-4" />
              View High Priority
            </Button>
          </Link>
          <Link to="/support-portal/my-tickets">
            <Button variant="outline">
              View My Assigned Tickets
            </Button>
          </Link>
        </CardContent>
      </Card>

      {/* Recent Tickets */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Recent Tickets</CardTitle>
          <Link to="/support-portal/tickets">
            <Button variant="link">View All Tickets</Button>
          </Link>
        </CardHeader>
        <CardContent>
          {ticketsLoading ? (
            <div className="flex h-48 items-center justify-center">
              <LoadingSpinner />
            </div>
          ) : !recentTickets?.tickets || recentTickets.tickets.length === 0 ? (
            <div className="flex h-48 items-center justify-center text-muted-foreground">
              No tickets found
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Ticket #</TableHead>
                    <TableHead>Subject</TableHead>
                    <TableHead>Business</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Priority</TableHead>
                    <TableHead>Assigned To</TableHead>
                    <TableHead>Created</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {recentTickets.tickets.map((ticket) => (
                    <TableRow key={ticket.id}>
                      <TableCell>
                        <Link
                          to={`/support-portal/tickets/${ticket.id}`}
                          className="font-medium text-primary hover:underline"
                        >
                          {ticket.ticket_number}
                        </Link>
                      </TableCell>
                      <TableCell className="max-w-xs truncate">
                        {ticket.subject}
                      </TableCell>
                      <TableCell>{ticket.business_info.business_name}</TableCell>
                      <TableCell>
                        <TicketStatusBadge status={ticket.status} />
                      </TableCell>
                      <TableCell>
                        <TicketPriorityBadge priority={ticket.priority} />
                      </TableCell>
                      <TableCell>
                        {ticket.assigned_agent_name || (
                          <span className="text-muted-foreground">Unassigned</span>
                        )}
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {formatDistanceToNow(new Date(ticket.created_at), {
                          addSuffix: true,
                        })}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
