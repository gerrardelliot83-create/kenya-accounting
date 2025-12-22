import { useState, useMemo } from 'react';
import { useBusinesses } from '@/hooks/useAdmin';
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
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Search, Download, Building2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import type { BusinessListParams } from '@/types/admin';
import { DEFAULT_PAGE_SIZE } from '@/lib/constants';
import { formatDistanceToNow } from 'date-fns';

export const BusinessDirectoryPage = () => {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState<string>('all');
  const [businessType, setBusinessType] = useState<string>('all');

  const queryParams = useMemo(() => {
    const params: BusinessListParams = { page, limit: DEFAULT_PAGE_SIZE };
    if (search) params.search = search;
    if (status !== 'all') params.status = status;
    if (businessType !== 'all') params.business_type = businessType;
    return params;
  }, [page, search, status, businessType]);

  const { data, isLoading } = useBusinesses(queryParams);

  const handleExportCSV = () => {
    if (!data?.businesses) return;

    const headers = ['Name', 'Type', 'Status', 'Users', 'Invoices', 'Revenue', 'Created'];
    const rows = data.businesses.map((business) => [
      business.business_name,
      business.business_type,
      business.status,
      business.user_count.toString(),
      business.invoice_count.toString(),
      business.total_revenue.toFixed(2),
      new Date(business.created_at).toLocaleDateString(),
    ]);

    const csvContent = [
      headers.join(','),
      ...rows.map((row) => row.map((cell) => `"${cell}"`).join(',')),
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `businesses-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Business Directory</h1>
          <p className="text-muted-foreground">
            View and manage all businesses in the system
          </p>
        </div>
        <Button onClick={handleExportCSV} disabled={!data?.businesses || data.businesses.length === 0}>
          <Download className="mr-2 h-4 w-4" />
          Export to CSV
        </Button>
      </div>

      {/* Filters */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search by business name..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            className="pl-10"
          />
        </div>

        <Select
          value={status}
          onValueChange={(value) => {
            setStatus(value);
            setPage(1);
          }}
        >
          <SelectTrigger className="w-full md:w-[180px]">
            <SelectValue placeholder="Filter by status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Statuses</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="inactive">Inactive</SelectItem>
            <SelectItem value="suspended">Suspended</SelectItem>
          </SelectContent>
        </Select>

        <Select
          value={businessType}
          onValueChange={(value) => {
            setBusinessType(value);
            setPage(1);
          }}
        >
          <SelectTrigger className="w-full md:w-[200px]">
            <SelectValue placeholder="Filter by type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            <SelectItem value="sole_proprietorship">Sole Proprietorship</SelectItem>
            <SelectItem value="partnership">Partnership</SelectItem>
            <SelectItem value="limited_company">Limited Company</SelectItem>
            <SelectItem value="ngo">NGO</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Table Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Building2 className="h-5 w-5" />
            Businesses
            {data && <span className="text-sm font-normal text-muted-foreground">({data.total} total)</span>}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Business Name</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Users</TableHead>
                  <TableHead className="text-right">Invoices</TableHead>
                  <TableHead className="text-right">Revenue (KES)</TableHead>
                  <TableHead>Created</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading ? (
                  Array.from({ length: 5 }).map((_, index) => (
                    <TableRow key={index}>
                      <TableCell><Skeleton className="h-4 w-40" /></TableCell>
                      <TableCell><Skeleton className="h-4 w-32" /></TableCell>
                      <TableCell><Skeleton className="h-4 w-20" /></TableCell>
                      <TableCell><Skeleton className="h-4 w-12" /></TableCell>
                      <TableCell><Skeleton className="h-4 w-12" /></TableCell>
                      <TableCell><Skeleton className="h-4 w-24" /></TableCell>
                      <TableCell><Skeleton className="h-4 w-32" /></TableCell>
                    </TableRow>
                  ))
                ) : !data?.businesses || data.businesses.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="h-48 text-center">
                      <div className="flex flex-col items-center justify-center text-muted-foreground">
                        <Building2 className="mb-2 h-8 w-8" />
                        <p>No businesses found</p>
                        {search && <p className="text-sm">Try adjusting your search or filters</p>}
                      </div>
                    </TableCell>
                  </TableRow>
                ) : (
                  data.businesses.map((business) => (
                    <TableRow
                      key={business.id}
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={() => navigate(`/admin/businesses/${business.id}`)}
                    >
                      <TableCell className="font-medium">{business.business_name}</TableCell>
                      <TableCell className="capitalize">
                        {business.business_type.replace(/_/g, ' ')}
                      </TableCell>
                      <TableCell>{getStatusBadge(business.status)}</TableCell>
                      <TableCell className="text-right">{business.user_count}</TableCell>
                      <TableCell className="text-right">{business.invoice_count}</TableCell>
                      <TableCell className="text-right">
                        {business.total_revenue.toLocaleString('en-KE', {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2,
                        })}
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {formatDistanceToNow(new Date(business.created_at), { addSuffix: true })}
                      </TableCell>
                    </TableRow>
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
                {Math.min(page * DEFAULT_PAGE_SIZE, data.total)} of {data.total} businesses
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
