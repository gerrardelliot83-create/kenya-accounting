import { useState } from 'react';
import { Link } from 'react-router-dom';
import { format } from 'date-fns';
import { Plus, Ticket } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { TicketStatusBadge } from '@/components/help/TicketStatusBadge';
import { useMyTickets } from '@/hooks/useSupport';
import type { TicketStatus, TicketCategory } from '@/types/support';

export const MyTicketsPage = () => {
  const [statusFilter, setStatusFilter] = useState<TicketStatus | 'all'>('all');
  const [categoryFilter, setCategoryFilter] = useState<TicketCategory | 'all'>('all');

  const { data, isLoading, error } = useMyTickets({
    status: statusFilter !== 'all' ? statusFilter : undefined,
    category: categoryFilter !== 'all' ? categoryFilter : undefined,
  });

  const tickets = data?.tickets || [];

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-1/3" />
        <Card>
          <CardContent className="pt-6">
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-16 w-full" />
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold tracking-tight">My Support Tickets</h1>
        </div>

        <Alert variant="destructive">
          <AlertDescription>
            Failed to load support tickets. Please try again later.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">My Support Tickets</h1>
          <p className="text-muted-foreground">
            View and manage your support tickets
          </p>
        </div>
        <Button asChild>
          <Link to="/help/tickets/new">
            <Plus className="mr-2 h-4 w-4" />
            Create Ticket
          </Link>
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Filters</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <label className="text-sm font-medium mb-2 block">Status</label>
              <Select
                value={statusFilter}
                onValueChange={(value) => setStatusFilter(value as TicketStatus | 'all')}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Statuses</SelectItem>
                  <SelectItem value="open">Open</SelectItem>
                  <SelectItem value="in_progress">In Progress</SelectItem>
                  <SelectItem value="waiting_customer">Waiting for You</SelectItem>
                  <SelectItem value="resolved">Resolved</SelectItem>
                  <SelectItem value="closed">Closed</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex-1">
              <label className="text-sm font-medium mb-2 block">Category</label>
              <Select
                value={categoryFilter}
                onValueChange={(value) => setCategoryFilter(value as TicketCategory | 'all')}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Categories</SelectItem>
                  <SelectItem value="billing">Billing</SelectItem>
                  <SelectItem value="technical">Technical</SelectItem>
                  <SelectItem value="feature_request">Feature Request</SelectItem>
                  <SelectItem value="general">General</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tickets Table */}
      <Card>
        <CardHeader>
          <CardTitle>Tickets</CardTitle>
          <CardDescription>
            {data?.total || 0} {data?.total === 1 ? 'ticket' : 'tickets'} found
          </CardDescription>
        </CardHeader>
        <CardContent>
          {tickets.length > 0 ? (
            <div className="border rounded-lg overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Ticket #</TableHead>
                    <TableHead>Subject</TableHead>
                    <TableHead>Category</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead>Updated</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {tickets.map((ticket) => (
                    <TableRow key={ticket.id} className="cursor-pointer hover:bg-muted/50">
                      <TableCell className="font-mono text-sm">
                        {ticket.ticket_number}
                      </TableCell>
                      <TableCell>
                        <div>
                          <p className="font-medium">{ticket.subject}</p>
                          <p className="text-sm text-muted-foreground line-clamp-1">
                            {ticket.description}
                          </p>
                        </div>
                      </TableCell>
                      <TableCell className="capitalize">
                        {ticket.category.replace('_', ' ')}
                      </TableCell>
                      <TableCell>
                        <TicketStatusBadge status={ticket.status} />
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {format(new Date(ticket.created_at), 'MMM dd, yyyy')}
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {format(new Date(ticket.updated_at), 'MMM dd, yyyy')}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button variant="ghost" size="sm" asChild>
                          <Link to={`/help/tickets/${ticket.id}`}>View</Link>
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          ) : (
            <div className="text-center py-12">
              <div className="flex justify-center mb-4">
                <div className="rounded-full bg-muted p-6">
                  <Ticket className="h-12 w-12 text-muted-foreground" />
                </div>
              </div>
              <h3 className="text-lg font-semibold mb-2">No tickets found</h3>
              <p className="text-muted-foreground mb-6">
                {statusFilter !== 'all' || categoryFilter !== 'all'
                  ? 'Try adjusting your filters or create a new ticket'
                  : "You haven't created any support tickets yet"}
              </p>
              <Button asChild>
                <Link to="/help/tickets/new">
                  <Plus className="mr-2 h-4 w-4" />
                  Create Your First Ticket
                </Link>
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
