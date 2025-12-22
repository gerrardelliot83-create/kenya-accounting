import { useState, useMemo } from 'react';
import { useAdminTickets } from '@/hooks/useAdminSupport';
import { useAuth } from '@/hooks/useAuth';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
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
import { Link, useSearchParams } from 'react-router-dom';
import { Search, RefreshCw, ChevronLeft, ChevronRight } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import type { TicketFilters, TicketStatus, TicketPriority, TicketCategory } from '@/types/admin-support';

const ITEMS_PER_PAGE = 20;

export const SupportTicketListPage = () => {
  const { user } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();

  // Get filter values from URL params
  const [filters, setFilters] = useState<TicketFilters>({
    status: (searchParams.get('status') as TicketStatus) || 'all',
    priority: (searchParams.get('priority') as TicketPriority) || 'all',
    category: (searchParams.get('category') as TicketCategory) || 'all',
    assigned: searchParams.get('assigned') || 'all',
    search: searchParams.get('search') || '',
    page: parseInt(searchParams.get('page') || '1'),
    limit: ITEMS_PER_PAGE,
  });

  const [searchInput, setSearchInput] = useState(filters.search || '');

  // Build API filters (exclude 'all' values)
  const apiFilters = useMemo(() => {
    const params: TicketFilters = {
      page: filters.page,
      limit: filters.limit,
    };

    if (filters.status && filters.status !== 'all') {
      params.status = filters.status;
    }
    if (filters.priority && filters.priority !== 'all') {
      params.priority = filters.priority;
    }
    if (filters.category && filters.category !== 'all') {
      params.category = filters.category;
    }
    if (filters.search) {
      params.search = filters.search;
    }
    if (filters.assigned === 'unassigned') {
      // Backend expects specific param for unassigned
      params.assigned = 'unassigned';
    } else if (filters.assigned === 'assigned_to_me' && user?.id) {
      // Backend expects agent_id for assigned to me
      params.assigned = 'assigned_to_me';
    }

    return params;
  }, [filters, user?.id]);

  const { data, isLoading, refetch, isFetching } = useAdminTickets(apiFilters);

  const handleFilterChange = (key: keyof TicketFilters, value: string) => {
    const newFilters = { ...filters, [key]: value, page: 1 };
    setFilters(newFilters);

    // Update URL params
    const params = new URLSearchParams();
    Object.entries(newFilters).forEach(([k, v]) => {
      if (v && v !== 'all' && v !== '') {
        params.set(k, v.toString());
      }
    });
    setSearchParams(params);
  };

  const handleSearch = () => {
    handleFilterChange('search', searchInput);
  };

  const handlePageChange = (newPage: number) => {
    setFilters({ ...filters, page: newPage });
    const params = new URLSearchParams(searchParams);
    params.set('page', newPage.toString());
    setSearchParams(params);
  };

  const handleReset = () => {
    setFilters({
      status: 'all',
      priority: 'all',
      category: 'all',
      assigned: 'all',
      search: '',
      page: 1,
      limit: ITEMS_PER_PAGE,
    });
    setSearchInput('');
    setSearchParams({});
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Support Tickets</h1>
          <p className="text-muted-foreground">
            Manage and track all support tickets
          </p>
        </div>
        <Button
          variant="outline"
          onClick={() => refetch()}
          disabled={isFetching}
        >
          <RefreshCw className={`mr-2 h-4 w-4 ${isFetching ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Filters</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
            {/* Status Filter */}
            <div>
              <label className="mb-2 block text-sm font-medium">Status</label>
              <Select
                value={filters.status || 'all'}
                onValueChange={(value) => handleFilterChange('status', value)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Statuses</SelectItem>
                  <SelectItem value="open">Open</SelectItem>
                  <SelectItem value="in_progress">In Progress</SelectItem>
                  <SelectItem value="waiting_customer">Waiting Customer</SelectItem>
                  <SelectItem value="resolved">Resolved</SelectItem>
                  <SelectItem value="closed">Closed</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Priority Filter */}
            <div>
              <label className="mb-2 block text-sm font-medium">Priority</label>
              <Select
                value={filters.priority || 'all'}
                onValueChange={(value) => handleFilterChange('priority', value)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Priorities</SelectItem>
                  <SelectItem value="urgent">Urgent</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="low">Low</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Category Filter */}
            <div>
              <label className="mb-2 block text-sm font-medium">Category</label>
              <Select
                value={filters.category || 'all'}
                onValueChange={(value) => handleFilterChange('category', value)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Categories</SelectItem>
                  <SelectItem value="payment_issue">Payment Issue</SelectItem>
                  <SelectItem value="technical_support">Technical Support</SelectItem>
                  <SelectItem value="account_access">Account Access</SelectItem>
                  <SelectItem value="billing_question">Billing Question</SelectItem>
                  <SelectItem value="feature_request">Feature Request</SelectItem>
                  <SelectItem value="bug_report">Bug Report</SelectItem>
                  <SelectItem value="general_inquiry">General Inquiry</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Assignment Filter */}
            <div>
              <label className="mb-2 block text-sm font-medium">Assignment</label>
              <Select
                value={filters.assigned || 'all'}
                onValueChange={(value) => handleFilterChange('assigned', value)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Tickets</SelectItem>
                  <SelectItem value="unassigned">Unassigned</SelectItem>
                  <SelectItem value="assigned_to_me">Assigned to Me</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Search */}
            <div>
              <label className="mb-2 block text-sm font-medium">Search</label>
              <div className="flex gap-2">
                <Input
                  placeholder="Ticket #, subject..."
                  value={searchInput}
                  onChange={(e) => setSearchInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                />
                <Button onClick={handleSearch} size="icon">
                  <Search className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>

          <div className="flex justify-end">
            <Button variant="outline" onClick={handleReset}>
              Reset Filters
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Tickets Table */}
      <Card>
        <CardHeader>
          <CardTitle>
            Tickets {data && `(${data.total} total)`}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex h-96 items-center justify-center">
              <LoadingSpinner size="lg" />
            </div>
          ) : !data?.tickets || data.tickets.length === 0 ? (
            <div className="flex h-96 flex-col items-center justify-center text-muted-foreground">
              <p className="text-lg font-medium">No tickets found</p>
              <p className="text-sm">Try adjusting your filters</p>
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Ticket #</TableHead>
                      <TableHead>Subject</TableHead>
                      <TableHead>Business</TableHead>
                      <TableHead>Category</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Priority</TableHead>
                      <TableHead>Assigned To</TableHead>
                      <TableHead>Messages</TableHead>
                      <TableHead>Created</TableHead>
                      <TableHead>Last Updated</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {data.tickets.map((ticket) => (
                      <TableRow key={ticket.id}>
                        <TableCell>
                          <Link
                            to={`/support-portal/tickets/${ticket.id}`}
                            className="font-medium text-primary hover:underline"
                          >
                            {ticket.ticket_number}
                          </Link>
                        </TableCell>
                        <TableCell className="max-w-xs">
                          <div className="truncate font-medium">{ticket.subject}</div>
                          <div className="truncate text-sm text-muted-foreground">
                            {ticket.description}
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="font-medium">
                            {ticket.business_info.business_name}
                          </div>
                          <div className="text-sm text-muted-foreground">
                            {ticket.customer_name}
                          </div>
                        </TableCell>
                        <TableCell className="capitalize">
                          {ticket.category.replace(/_/g, ' ')}
                        </TableCell>
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
                        <TableCell>
                          <span className="text-sm">{ticket.message_count}</span>
                        </TableCell>
                        <TableCell className="text-sm text-muted-foreground">
                          {formatDistanceToNow(new Date(ticket.created_at), {
                            addSuffix: true,
                          })}
                        </TableCell>
                        <TableCell className="text-sm text-muted-foreground">
                          {formatDistanceToNow(new Date(ticket.updated_at), {
                            addSuffix: true,
                          })}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>

              {/* Pagination */}
              {data.total_pages > 1 && (
                <div className="mt-4 flex items-center justify-between">
                  <div className="text-sm text-muted-foreground">
                    Page {data.page} of {data.total_pages} ({data.total} tickets)
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handlePageChange(data.page - 1)}
                      disabled={data.page <= 1}
                    >
                      <ChevronLeft className="mr-1 h-4 w-4" />
                      Previous
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handlePageChange(data.page + 1)}
                      disabled={data.page >= data.total_pages}
                    >
                      Next
                      <ChevronRight className="ml-1 h-4 w-4" />
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
