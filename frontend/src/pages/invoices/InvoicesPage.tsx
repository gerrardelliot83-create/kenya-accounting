import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Eye, MoreVertical, Edit, XCircle, Download } from 'lucide-react';
import { Button } from '@/components/ui/button';
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
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { useInvoices, useCancelInvoice, useDownloadInvoicePdf } from '@/hooks/useInvoices';
import type { Invoice, InvoiceStatus, InvoicesListParams } from '@/types/invoice';
import { formatCurrency, formatDate } from '@/lib/formatters';
import { DEFAULT_PAGE_SIZE } from '@/lib/constants';

export const InvoicesPage = () => {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState<InvoiceStatus | 'all'>('all');

  const queryParams = useMemo(() => {
    const params: InvoicesListParams = { page, limit: DEFAULT_PAGE_SIZE };
    if (status !== 'all') params.status = status;
    return params;
  }, [page, status]);

  const { data, isLoading } = useInvoices(queryParams);
  const cancelInvoice = useCancelInvoice();
  const downloadPdf = useDownloadInvoicePdf();

  const handleViewInvoice = (invoice: Invoice) => {
    navigate(`/invoices/${invoice.id}`);
  };

  const handleEditInvoice = (invoice: Invoice) => {
    navigate(`/invoices/${invoice.id}/edit`);
  };

  const handleCancelInvoice = async (invoice: Invoice) => {
    if (window.confirm(`Are you sure you want to cancel invoice ${invoice.invoiceNumber}?`)) {
      await cancelInvoice.mutateAsync(invoice.id);
    }
  };

  const handleDownloadPdf = async (invoice: Invoice) => {
    await downloadPdf.mutateAsync(invoice.id);
  };

  const getStatusBadge = (status: InvoiceStatus) => {
    const variants: Record<InvoiceStatus, 'default' | 'secondary' | 'outline' | 'destructive'> = {
      draft: 'secondary',
      issued: 'default',
      paid: 'outline',
      cancelled: 'destructive',
    };
    return (
      <Badge variant={variants[status]}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </Badge>
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-semibold">Invoices</h1>
          <p className="mt-2 text-muted-foreground">
            Manage and track your invoices
          </p>
        </div>
        <Button onClick={() => navigate('/invoices/new')}>
          <Plus className="mr-2 h-4 w-4" />
          New Invoice
        </Button>
      </div>

      <div className="flex flex-col gap-4 md:flex-row md:items-center">
        <Select
          value={status}
          onValueChange={(value) => {
            setStatus(value as InvoiceStatus | 'all');
            setPage(1);
          }}
        >
          <SelectTrigger className="w-full md:w-[180px]">
            <SelectValue placeholder="Filter by status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Statuses</SelectItem>
            <SelectItem value="draft">Draft</SelectItem>
            <SelectItem value="issued">Issued</SelectItem>
            <SelectItem value="paid">Paid</SelectItem>
            <SelectItem value="cancelled">Cancelled</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Invoice #</TableHead>
              <TableHead>Customer</TableHead>
              <TableHead>Issue Date</TableHead>
              <TableHead>Due Date</TableHead>
              <TableHead>Total</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="w-[70px]">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              Array.from({ length: 5 }).map((_, index) => (
                <TableRow key={index}>
                  <TableCell>
                    <Skeleton className="h-4 w-24" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="h-4 w-32" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="h-4 w-24" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="h-4 w-24" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="h-4 w-20" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="h-4 w-16" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="h-8 w-8" />
                  </TableCell>
                </TableRow>
              ))
            ) : data?.invoices.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="text-center py-8">
                  <p className="text-muted-foreground">No invoices found</p>
                  <Button
                    variant="link"
                    onClick={() => navigate('/invoices/new')}
                    className="mt-2"
                  >
                    Create your first invoice
                  </Button>
                </TableCell>
              </TableRow>
            ) : (
              data?.invoices.map((invoice) => (
                <TableRow key={invoice.id}>
                  <TableCell className="font-medium">{invoice.invoiceNumber}</TableCell>
                  <TableCell>{invoice.contact?.name || 'N/A'}</TableCell>
                  <TableCell className="text-muted-foreground">
                    {formatDate(invoice.issueDate)}
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {formatDate(invoice.dueDate)}
                  </TableCell>
                  <TableCell className="font-medium">{formatCurrency(invoice.total)}</TableCell>
                  <TableCell>{getStatusBadge(invoice.status)}</TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon" aria-label="Invoice actions">
                          <MoreVertical className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => handleViewInvoice(invoice)}>
                          <Eye className="mr-2 h-4 w-4" />
                          View
                        </DropdownMenuItem>
                        {invoice.status === 'draft' && (
                          <DropdownMenuItem onClick={() => handleEditInvoice(invoice)}>
                            <Edit className="mr-2 h-4 w-4" />
                            Edit
                          </DropdownMenuItem>
                        )}
                        <DropdownMenuItem onClick={() => handleDownloadPdf(invoice)}>
                          <Download className="mr-2 h-4 w-4" />
                          Download PDF
                        </DropdownMenuItem>
                        {(invoice.status === 'draft' || invoice.status === 'issued') && (
                          <DropdownMenuItem
                            onClick={() => handleCancelInvoice(invoice)}
                            className="text-destructive"
                          >
                            <XCircle className="mr-2 h-4 w-4" />
                            Cancel
                          </DropdownMenuItem>
                        )}
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {data && data.totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Showing {(page - 1) * DEFAULT_PAGE_SIZE + 1} to {Math.min(page * DEFAULT_PAGE_SIZE, data.total)} of{' '}
            {data.total} invoices
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
    </div>
  );
};
