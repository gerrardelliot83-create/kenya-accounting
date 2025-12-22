import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Edit, XCircle, Download, CheckCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  useInvoice,
  useIssueInvoice,
  useCancelInvoice,
  useDownloadInvoicePdf,
} from '@/hooks/useInvoices';
import type { InvoiceStatus } from '@/types/invoice';
import { formatCurrency, formatDateLong } from '@/lib/formatters';

export const InvoiceDetailPage = () => {
  const navigate = useNavigate();
  const { id } = useParams();

  const { data: invoice, isLoading } = useInvoice(id || '');
  const issueInvoice = useIssueInvoice();
  const cancelInvoice = useCancelInvoice();
  const downloadPdf = useDownloadInvoicePdf();

  const handleIssue = async () => {
    if (id && window.confirm('Are you sure you want to issue this invoice?')) {
      await issueInvoice.mutateAsync(id);
    }
  };

  const handleCancel = async () => {
    if (id && window.confirm('Are you sure you want to cancel this invoice?')) {
      await cancelInvoice.mutateAsync(id);
    }
  };

  const handleDownload = async () => {
    if (id) {
      await downloadPdf.mutateAsync(id);
    }
  };

  const getStatusBadge = (status: InvoiceStatus) => {
    const variants: Record<InvoiceStatus, 'default' | 'secondary' | 'outline' | 'destructive'> = {
      draft: 'secondary',
      issued: 'default',
      paid: 'outline',
      cancelled: 'destructive',
    };
    return (
      <Badge variant={variants[status]} className="text-sm">
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </Badge>
    );
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Skeleton className="h-10 w-10" />
          <div className="flex-1">
            <Skeleton className="h-8 w-48" />
            <Skeleton className="mt-2 h-4 w-32" />
          </div>
        </div>
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (!invoice) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate('/invoices')} aria-label="Back to invoices">
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-3xl font-semibold">Invoice Not Found</h1>
          </div>
        </div>
        <p className="text-muted-foreground">
          The invoice you are looking for does not exist.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate('/invoices')} aria-label="Back to invoices">
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-3xl font-semibold">{invoice.invoiceNumber}</h1>
              {getStatusBadge(invoice.status)}
            </div>
            <p className="mt-2 text-muted-foreground">
              Invoice details and line items
            </p>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          {invoice.status === 'draft' && (
            <>
              <Button variant="outline" onClick={() => navigate(`/invoices/${id}/edit`)}>
                <Edit className="mr-2 h-4 w-4" />
                Edit
              </Button>
              <Button onClick={handleIssue} disabled={issueInvoice.isPending}>
                <CheckCircle className="mr-2 h-4 w-4" />
                {issueInvoice.isPending ? 'Issuing...' : 'Issue Invoice'}
              </Button>
            </>
          )}
          {(invoice.status === 'draft' || invoice.status === 'issued') && (
            <Button
              variant="destructive"
              onClick={handleCancel}
              disabled={cancelInvoice.isPending}
            >
              <XCircle className="mr-2 h-4 w-4" />
              {cancelInvoice.isPending ? 'Cancelling...' : 'Cancel Invoice'}
            </Button>
          )}
          <Button variant="outline" onClick={handleDownload} disabled={downloadPdf.isPending}>
            <Download className="mr-2 h-4 w-4" />
            {downloadPdf.isPending ? 'Downloading...' : 'Download PDF'}
          </Button>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <div className="rounded-lg border p-6">
          <h2 className="mb-4 text-lg font-semibold">Invoice Information</h2>
          <dl className="space-y-3">
            <div className="flex justify-between">
              <dt className="text-muted-foreground">Invoice Number:</dt>
              <dd className="font-medium">{invoice.invoiceNumber}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted-foreground">Status:</dt>
              <dd>{getStatusBadge(invoice.status)}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted-foreground">Issue Date:</dt>
              <dd>{formatDateLong(invoice.issueDate)}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted-foreground">Due Date:</dt>
              <dd>{formatDateLong(invoice.dueDate)}</dd>
            </div>
            {invoice.issuedAt && (
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Issued At:</dt>
                <dd>{formatDateLong(invoice.issuedAt)}</dd>
              </div>
            )}
          </dl>
        </div>

        <div className="rounded-lg border p-6">
          <h2 className="mb-4 text-lg font-semibold">Customer Information</h2>
          <dl className="space-y-3">
            <div className="flex justify-between">
              <dt className="text-muted-foreground">Name:</dt>
              <dd className="font-medium">{invoice.contact?.name || 'N/A'}</dd>
            </div>
            {invoice.contact?.email && (
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Email:</dt>
                <dd>{invoice.contact.email}</dd>
              </div>
            )}
            {invoice.contact?.phone && (
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Phone:</dt>
                <dd>{invoice.contact.phone}</dd>
              </div>
            )}
          </dl>
        </div>
      </div>

      <div className="rounded-lg border">
        <div className="border-b p-4">
          <h2 className="text-lg font-semibold">Line Items</h2>
        </div>

        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Description</TableHead>
              <TableHead className="text-right">Quantity</TableHead>
              <TableHead className="text-right">Unit Price</TableHead>
              <TableHead className="text-right">Tax Rate</TableHead>
              <TableHead className="text-right">Tax Amount</TableHead>
              <TableHead className="text-right">Line Total</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {invoice.lineItems?.map((item) => (
              <TableRow key={item.id}>
                <TableCell className="font-medium">{item.description}</TableCell>
                <TableCell className="text-right">{item.quantity}</TableCell>
                <TableCell className="text-right">{formatCurrency(item.unitPrice)}</TableCell>
                <TableCell className="text-right">{item.taxRate}%</TableCell>
                <TableCell className="text-right">{formatCurrency(item.taxAmount)}</TableCell>
                <TableCell className="text-right font-medium">
                  {formatCurrency(item.lineTotal)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>

        <div className="border-t p-6">
          <div className="flex justify-end">
            <div className="w-full max-w-sm space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Subtotal:</span>
                <span>{formatCurrency(invoice.subtotal)}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Tax:</span>
                <span>{formatCurrency(invoice.taxAmount)}</span>
              </div>
              <div className="flex justify-between border-t pt-2 text-xl font-semibold">
                <span>Total:</span>
                <span>{formatCurrency(invoice.total)}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {invoice.notes && (
        <div className="rounded-lg border p-6">
          <h2 className="mb-4 text-lg font-semibold">Notes</h2>
          <p className="text-muted-foreground whitespace-pre-wrap">{invoice.notes}</p>
        </div>
      )}
    </div>
  );
};
