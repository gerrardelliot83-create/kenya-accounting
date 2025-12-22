import { useState, useMemo } from 'react';
import { useAuditLogs } from '@/hooks/useAdmin';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
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
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { FileText, ChevronDown, ChevronRight } from 'lucide-react';
import type { AuditLogParams, AuditLogEntry } from '@/types/admin';
import { DEFAULT_PAGE_SIZE } from '@/lib/constants';
import { formatDistanceToNow } from 'date-fns';

export const AuditLogViewerPage = () => {
  const [page, setPage] = useState(1);
  const [actionFilter, setActionFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [selectedLog, setSelectedLog] = useState<AuditLogEntry | null>(null);
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());

  const queryParams = useMemo(() => {
    const params: AuditLogParams = { page, limit: DEFAULT_PAGE_SIZE };
    if (actionFilter !== 'all') params.action = actionFilter;
    if (statusFilter !== 'all') params.status = statusFilter as 'success' | 'failure' | 'error';
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    return params;
  }, [page, actionFilter, statusFilter, startDate, endDate]);

  const { data, isLoading } = useAuditLogs(queryParams);

  const toggleRowExpanded = (logId: string) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(logId)) {
      newExpanded.delete(logId);
    } else {
      newExpanded.add(logId);
    }
    setExpandedRows(newExpanded);
  };

  const getStatusBadge = (status: string) => {
    const variants: Record<string, 'default' | 'secondary' | 'destructive'> = {
      success: 'default',
      failure: 'destructive',
      error: 'destructive',
    };

    return (
      <Badge variant={variants[status] || 'secondary'}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </Badge>
    );
  };

  const clearFilters = () => {
    setActionFilter('all');
    setStatusFilter('all');
    setStartDate('');
    setEndDate('');
    setPage(1);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Audit Logs</h1>
          <p className="text-muted-foreground">
            View system activity and security events
          </p>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Filters</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <div className="space-y-2">
              <Label htmlFor="action">Action</Label>
              <Select
                value={actionFilter}
                onValueChange={(value) => {
                  setActionFilter(value);
                  setPage(1);
                }}
              >
                <SelectTrigger id="action">
                  <SelectValue placeholder="All actions" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Actions</SelectItem>
                  <SelectItem value="login">Login</SelectItem>
                  <SelectItem value="logout">Logout</SelectItem>
                  <SelectItem value="create">Create</SelectItem>
                  <SelectItem value="update">Update</SelectItem>
                  <SelectItem value="delete">Delete</SelectItem>
                  <SelectItem value="export">Export</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="status">Status</Label>
              <Select
                value={statusFilter}
                onValueChange={(value) => {
                  setStatusFilter(value);
                  setPage(1);
                }}
              >
                <SelectTrigger id="status">
                  <SelectValue placeholder="All statuses" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Statuses</SelectItem>
                  <SelectItem value="success">Success</SelectItem>
                  <SelectItem value="failure">Failure</SelectItem>
                  <SelectItem value="error">Error</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="start_date">Start Date</Label>
              <Input
                id="start_date"
                type="date"
                value={startDate}
                onChange={(e) => {
                  setStartDate(e.target.value);
                  setPage(1);
                }}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="end_date">End Date</Label>
              <Input
                id="end_date"
                type="date"
                value={endDate}
                onChange={(e) => {
                  setEndDate(e.target.value);
                  setPage(1);
                }}
              />
            </div>
          </div>

          <div className="mt-4">
            <Button variant="outline" size="sm" onClick={clearFilters}>
              Clear Filters
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Logs Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Audit Logs
            {data && <span className="text-sm font-normal text-muted-foreground">({data.total} total)</span>}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[40px]"></TableHead>
                  <TableHead>Timestamp</TableHead>
                  <TableHead>User</TableHead>
                  <TableHead>Action</TableHead>
                  <TableHead>Resource</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>IP Address</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading ? (
                  Array.from({ length: 10 }).map((_, index) => (
                    <TableRow key={index}>
                      <TableCell><Skeleton className="h-4 w-4" /></TableCell>
                      <TableCell><Skeleton className="h-4 w-32" /></TableCell>
                      <TableCell><Skeleton className="h-4 w-40" /></TableCell>
                      <TableCell><Skeleton className="h-4 w-24" /></TableCell>
                      <TableCell><Skeleton className="h-4 w-32" /></TableCell>
                      <TableCell><Skeleton className="h-4 w-20" /></TableCell>
                      <TableCell><Skeleton className="h-4 w-32" /></TableCell>
                    </TableRow>
                  ))
                ) : !data?.logs || data.logs.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="h-48 text-center">
                      <div className="flex flex-col items-center justify-center text-muted-foreground">
                        <FileText className="mb-2 h-8 w-8" />
                        <p>No audit logs found</p>
                        <p className="text-sm">Try adjusting your filters</p>
                      </div>
                    </TableCell>
                  </TableRow>
                ) : (
                  data.logs.map((log) => (
                    <>
                      <TableRow key={log.id} className="cursor-pointer hover:bg-muted/50">
                        <TableCell onClick={() => toggleRowExpanded(log.id)}>
                          {expandedRows.has(log.id) ? (
                            <ChevronDown className="h-4 w-4" />
                          ) : (
                            <ChevronRight className="h-4 w-4" />
                          )}
                        </TableCell>
                        <TableCell className="text-sm">
                          {new Date(log.created_at).toLocaleString()}
                          <br />
                          <span className="text-xs text-muted-foreground">
                            {formatDistanceToNow(new Date(log.created_at), { addSuffix: true })}
                          </span>
                        </TableCell>
                        <TableCell className="font-medium">
                          {log.user_name || 'System'}
                          {log.user_id && (
                            <div className="text-xs text-muted-foreground font-mono">
                              {log.user_id.substring(0, 8)}...
                            </div>
                          )}
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline">{log.action}</Badge>
                        </TableCell>
                        <TableCell>
                          {log.resource_type && (
                            <>
                              <div className="capitalize">{log.resource_type}</div>
                              {log.resource_id && (
                                <div className="text-xs text-muted-foreground font-mono">
                                  {log.resource_id.substring(0, 8)}...
                                </div>
                              )}
                            </>
                          )}
                          {!log.resource_type && <span className="text-muted-foreground">-</span>}
                        </TableCell>
                        <TableCell>{getStatusBadge(log.status)}</TableCell>
                        <TableCell className="font-mono text-sm">
                          {log.ip_address || '-'}
                        </TableCell>
                      </TableRow>
                      {expandedRows.has(log.id) && log.details && (
                        <TableRow>
                          <TableCell></TableCell>
                          <TableCell colSpan={6}>
                            <div className="rounded-md bg-muted p-3">
                              <p className="mb-2 text-sm font-medium">Details:</p>
                              <pre className="text-xs overflow-auto">
                                {JSON.stringify(log.details, null, 2)}
                              </pre>
                            </div>
                          </TableCell>
                        </TableRow>
                      )}
                    </>
                  ))
                )}
              </TableBody>
            </Table>
          </div>

          {/* Pagination */}
          {data && data.totalPages > 1 && (
            <div className="mt-4 flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                Showing {(page - 1) * DEFAULT_PAGE_SIZE + 1} to{' '}
                {Math.min(page * DEFAULT_PAGE_SIZE, data.total)} of {data.total} logs
              </p>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(page - 1)}
                  disabled={page === 1}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(page + 1)}
                  disabled={page === data.totalPages}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
