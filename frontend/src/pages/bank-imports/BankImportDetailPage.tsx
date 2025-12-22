import { useState, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ChevronLeft, Download, FileText, AlertCircle } from 'lucide-react';
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
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import {
  useBankImport,
  useBankTransactions,
  useUnmatchTransaction,
} from '@/hooks/useBankImports';
import { ReconciliationModal } from './ReconciliationModal';
import type {
  BankTransaction,
  ReconciliationStatus,
  BankTransactionsListParams,
} from '@/types/bank-import';
import { DEFAULT_PAGE_SIZE } from '@/lib/constants';
import { formatCurrency, formatDate } from '@/lib/formatters';

export const BankImportDetailPage = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [reconciliationStatus, setReconciliationStatus] = useState<ReconciliationStatus | 'all'>('all');
  const [selectedTransaction, setSelectedTransaction] = useState<BankTransaction | null>(null);
  const [isReconciliationModalOpen, setIsReconciliationModalOpen] = useState(false);

  const { data: importData, isLoading: isLoadingImport } = useBankImport(id || '');
  const unmatchTransaction = useUnmatchTransaction();

  const queryParams = useMemo(() => {
    const params: BankTransactionsListParams = { page, limit: DEFAULT_PAGE_SIZE };
    if (reconciliationStatus !== 'all') params.reconciliationStatus = reconciliationStatus;
    return params;
  }, [page, reconciliationStatus]);

  const { data: transactionsData, isLoading: isLoadingTransactions } = useBankTransactions(
    id || '',
    queryParams
  );

  const handleMatchTransaction = (transaction: BankTransaction) => {
    setSelectedTransaction(transaction);
    setIsReconciliationModalOpen(true);
  };

  const handleUnmatchTransaction = async (transaction: BankTransaction) => {
    if (window.confirm('Are you sure you want to unmatch this transaction?')) {
      await unmatchTransaction.mutateAsync(transaction.id);
    }
  };

  const handleCloseModal = () => {
    setIsReconciliationModalOpen(false);
    setSelectedTransaction(null);
  };

  const getReconciliationStatusBadge = (status: ReconciliationStatus) => {
    const variants: Record<
      ReconciliationStatus,
      { label: string; variant: 'default' | 'secondary' | 'destructive' | 'outline' }
    > = {
      unmatched: { label: 'Unmatched', variant: 'secondary' },
      suggested: { label: 'Suggested', variant: 'outline' },
      matched: { label: 'Matched', variant: 'default' },
      ignored: { label: 'Ignored', variant: 'outline' },
    };
    const config = variants[status];
    return <Badge variant={config.variant}>{config.label}</Badge>;
  };

  const getStatusColor = (status: ReconciliationStatus) => {
    switch (status) {
      case 'matched':
        return 'text-green-600';
      case 'suggested':
        return 'text-blue-600';
      case 'unmatched':
        return 'text-yellow-600';
      case 'ignored':
        return 'text-gray-600';
      default:
        return '';
    }
  };

  const getImportStatusBadge = (status: string) => {
    const variants: Record<string, { label: string; variant: 'default' | 'secondary' | 'destructive' | 'outline' }> = {
      pending: { label: 'Pending', variant: 'secondary' },
      mapping: { label: 'Mapping', variant: 'outline' },
      processing: { label: 'Processing', variant: 'outline' },
      completed: { label: 'Completed', variant: 'default' },
      failed: { label: 'Failed', variant: 'destructive' },
    };
    const config = variants[status] || { label: status, variant: 'outline' };
    return <Badge variant={config.variant}>{config.label}</Badge>;
  };

  const matchPercentage = importData
    ? Math.round((importData.matchedRows / importData.totalRows) * 100)
    : 0;

  if (isLoadingImport) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-64" />
        <div className="grid gap-4 md:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-4 w-24" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-8 w-16" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (!importData) {
    return (
      <div className="space-y-6">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>
            Bank import not found or you don't have permission to view it.
          </AlertDescription>
        </Alert>
        <Button variant="outline" onClick={() => navigate('/bank-imports')}>
          <ChevronLeft className="mr-2 h-4 w-4" />
          Back to Imports
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-semibold">Bank Import Details</h1>
            {getImportStatusBadge(importData.status)}
          </div>
          <p className="mt-2 text-muted-foreground">{importData.fileName}</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => navigate('/bank-imports')}>
            <ChevronLeft className="mr-2 h-4 w-4" />
            Back
          </Button>
          <Button variant="outline">
            <Download className="mr-2 h-4 w-4" />
            Export
          </Button>
        </div>
      </div>

      {/* Import failed alert */}
      {importData.status === 'failed' && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Import Failed</AlertTitle>
          <AlertDescription>
            There was an error processing this bank import. Please check the file format and try again.
          </AlertDescription>
        </Alert>
      )}

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Transactions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{importData.totalRows}</div>
            <p className="text-xs text-muted-foreground mt-1">
              Uploaded on {formatDate(importData.uploadedAt)}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Matched</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{importData.matchedRows}</div>
            <p className="text-xs text-muted-foreground mt-1">
              {matchPercentage}% reconciled
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Unmatched</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">{importData.unmatchedRows}</div>
            <p className="text-xs text-muted-foreground mt-1">Needs review</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Errors</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{importData.errorRows}</div>
            <p className="text-xs text-muted-foreground mt-1">Failed to process</p>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4">
        <Select
          value={reconciliationStatus}
          onValueChange={(value) => {
            setReconciliationStatus(value as ReconciliationStatus | 'all');
            setPage(1);
          }}
        >
          <SelectTrigger className="w-[200px]">
            <SelectValue placeholder="All Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="unmatched">Unmatched</SelectItem>
            <SelectItem value="suggested">Suggested</SelectItem>
            <SelectItem value="matched">Matched</SelectItem>
            <SelectItem value="ignored">Ignored</SelectItem>
          </SelectContent>
        </Select>

        {reconciliationStatus !== 'all' && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              setReconciliationStatus('all');
              setPage(1);
            }}
          >
            Clear Filter
          </Button>
        )}
      </div>

      {/* Transactions Table */}
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Date</TableHead>
              <TableHead>Description</TableHead>
              <TableHead className="text-right">Debit</TableHead>
              <TableHead className="text-right">Credit</TableHead>
              <TableHead className="text-right">Balance</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoadingTransactions ? (
              Array.from({ length: 5 }).map((_, index) => (
                <TableRow key={index}>
                  <TableCell>
                    <Skeleton className="h-4 w-24" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="h-4 w-48" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="h-4 w-20" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="h-4 w-20" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="h-4 w-20" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="h-4 w-20" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="h-8 w-20" />
                  </TableCell>
                </TableRow>
              ))
            ) : transactionsData?.transactions.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="text-center py-8">
                  <p className="text-muted-foreground">No transactions found</p>
                </TableCell>
              </TableRow>
            ) : (
              transactionsData?.transactions.map((transaction) => (
                <TableRow key={transaction.id}>
                  <TableCell className="font-medium">
                    {formatDate(transaction.transactionDate)}
                  </TableCell>
                  <TableCell className="max-w-[300px]">
                    <div className="truncate">{transaction.description}</div>
                    {transaction.reference && (
                      <div className="text-xs text-muted-foreground truncate">
                        Ref: {transaction.reference}
                      </div>
                    )}
                  </TableCell>
                  <TableCell className="text-right text-red-600 font-medium">
                    {transaction.debit ? formatCurrency(transaction.debit) : '-'}
                  </TableCell>
                  <TableCell className="text-right text-green-600 font-medium">
                    {transaction.credit ? formatCurrency(transaction.credit) : '-'}
                  </TableCell>
                  <TableCell className="text-right font-medium">
                    {transaction.balance ? formatCurrency(transaction.balance) : '-'}
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      {getReconciliationStatusBadge(transaction.reconciliationStatus)}
                      {transaction.matchConfidence && transaction.reconciliationStatus === 'suggested' && (
                        <span className="text-xs text-muted-foreground">
                          {transaction.matchConfidence}%
                        </span>
                      )}
                    </div>
                  </TableCell>
                  <TableCell className="text-right">
                    {transaction.reconciliationStatus === 'matched' ? (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleUnmatchTransaction(transaction)}
                      >
                        Unmatch
                      </Button>
                    ) : transaction.reconciliationStatus === 'ignored' ? (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleMatchTransaction(transaction)}
                      >
                        Review
                      </Button>
                    ) : (
                      <Button
                        variant="default"
                        size="sm"
                        onClick={() => handleMatchTransaction(transaction)}
                      >
                        Match
                      </Button>
                    )}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      {transactionsData && transactionsData.totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Showing {(page - 1) * DEFAULT_PAGE_SIZE + 1} to{' '}
            {Math.min(page * DEFAULT_PAGE_SIZE, transactionsData.total)} of{' '}
            {transactionsData.total} transactions
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
              disabled={page === transactionsData.totalPages}
            >
              Next
            </Button>
          </div>
        </div>
      )}

      {/* Reconciliation Modal */}
      {selectedTransaction && (
        <ReconciliationModal
          open={isReconciliationModalOpen}
          onClose={handleCloseModal}
          transaction={selectedTransaction}
        />
      )}
    </div>
  );
};
