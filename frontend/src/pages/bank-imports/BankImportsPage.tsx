import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, MoreVertical, Eye, Trash2, FileText, FileSpreadsheet, File } from 'lucide-react';
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
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { useBankImports, useDeleteBankImport } from '@/hooks/useBankImports';
import type { BankImport, ImportStatus, SourceBank, BankImportsListParams } from '@/types/bank-import';
import { DEFAULT_PAGE_SIZE } from '@/lib/constants';
import { formatDate } from '@/lib/formatters';

export const BankImportsPage = () => {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState<ImportStatus | 'all'>('all');
  const [sourceBank, setSourceBank] = useState<SourceBank | 'all'>('all');

  const queryParams = useMemo(() => {
    const params: BankImportsListParams = { page, limit: DEFAULT_PAGE_SIZE };
    if (status !== 'all') params.status = status;
    if (sourceBank !== 'all') params.sourceBank = sourceBank;
    return params;
  }, [page, status, sourceBank]);

  const { data, isLoading } = useBankImports(queryParams);
  const deleteBankImport = useDeleteBankImport();

  const handleNewImport = () => {
    navigate('/bank-imports/new');
  };

  const handleViewImport = (importItem: BankImport) => {
    navigate(`/bank-imports/${importItem.id}`);
  };

  const handleDeleteImport = async (importItem: BankImport) => {
    if (window.confirm(`Are you sure you want to delete this import: ${importItem.fileName}?`)) {
      await deleteBankImport.mutateAsync(importItem.id);
    }
  };

  const getStatusBadge = (status: ImportStatus) => {
    const variants: Record<ImportStatus, { label: string; variant: 'default' | 'secondary' | 'destructive' | 'outline' }> = {
      pending: { label: 'Pending', variant: 'secondary' },
      mapping: { label: 'Mapping', variant: 'outline' },
      processing: { label: 'Processing', variant: 'outline' },
      completed: { label: 'Completed', variant: 'default' },
      failed: { label: 'Failed', variant: 'destructive' },
    };
    const config = variants[status];
    return <Badge variant={config.variant}>{config.label}</Badge>;
  };

  const getSourceBankLabel = (bank: SourceBank) => {
    const labels: Record<SourceBank, string> = {
      equity: 'Equity Bank',
      kcb: 'KCB',
      cooperative: 'Co-operative Bank',
      mpesa: 'M-Pesa',
      other: 'Other',
    };
    return labels[bank];
  };

  const getFileIcon = (fileType: string) => {
    switch (fileType) {
      case 'csv':
        return <FileSpreadsheet className="h-4 w-4" />;
      case 'pdf':
        return <FileText className="h-4 w-4" />;
      default:
        return <File className="h-4 w-4" />;
    }
  };

  const totalImports = data?.total || 0;
  const completedImports = data?.imports.filter(imp => imp.status === 'completed').length || 0;
  const pendingImports = data?.imports.filter(imp => imp.status !== 'completed' && imp.status !== 'failed').length || 0;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-semibold">Bank Imports</h1>
          <p className="mt-2 text-muted-foreground">
            Upload and reconcile bank statements
          </p>
        </div>
        <Button onClick={handleNewImport}>
          <Plus className="mr-2 h-4 w-4" />
          New Import
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Imports</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalImports}</div>
            <p className="text-xs text-muted-foreground mt-1">
              All bank imports
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Completed</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{completedImports}</div>
            <p className="text-xs text-muted-foreground mt-1">
              Successfully processed
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{pendingImports}</div>
            <p className="text-xs text-muted-foreground mt-1">
              Awaiting processing
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex flex-col gap-4">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <Select
            value={status}
            onValueChange={(value) => {
              setStatus(value as ImportStatus | 'all');
              setPage(1);
            }}
          >
            <SelectTrigger>
              <SelectValue placeholder="All Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="pending">Pending</SelectItem>
              <SelectItem value="mapping">Mapping</SelectItem>
              <SelectItem value="processing">Processing</SelectItem>
              <SelectItem value="completed">Completed</SelectItem>
              <SelectItem value="failed">Failed</SelectItem>
            </SelectContent>
          </Select>

          <Select
            value={sourceBank}
            onValueChange={(value) => {
              setSourceBank(value as SourceBank | 'all');
              setPage(1);
            }}
          >
            <SelectTrigger>
              <SelectValue placeholder="All Banks" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Banks</SelectItem>
              <SelectItem value="equity">Equity Bank</SelectItem>
              <SelectItem value="kcb">KCB</SelectItem>
              <SelectItem value="cooperative">Co-operative Bank</SelectItem>
              <SelectItem value="mpesa">M-Pesa</SelectItem>
              <SelectItem value="other">Other</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {(status !== 'all' || sourceBank !== 'all') && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              setStatus('all');
              setSourceBank('all');
              setPage(1);
            }}
            className="w-fit"
          >
            Clear Filters
          </Button>
        )}
      </div>

      {/* Imports Table */}
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>File</TableHead>
              <TableHead>Source Bank</TableHead>
              <TableHead>Uploaded</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">Total Rows</TableHead>
              <TableHead className="text-right">Matched</TableHead>
              <TableHead className="text-right">Unmatched</TableHead>
              <TableHead className="w-[70px]">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              Array.from({ length: 5 }).map((_, index) => (
                <TableRow key={index}>
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
                    <Skeleton className="h-4 w-16" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="h-4 w-16" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="h-8 w-8" />
                  </TableCell>
                </TableRow>
              ))
            ) : data?.imports.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} className="text-center py-8">
                  <p className="text-muted-foreground">No bank imports found</p>
                  <Button variant="link" onClick={handleNewImport} className="mt-2">
                    Upload your first bank statement
                  </Button>
                </TableCell>
              </TableRow>
            ) : (
              data?.imports.map((importItem) => (
                <TableRow
                  key={importItem.id}
                  className="cursor-pointer hover:bg-muted/50"
                  onClick={() => handleViewImport(importItem)}
                >
                  <TableCell className="font-medium">
                    <div className="flex items-center gap-2">
                      {getFileIcon(importItem.fileType)}
                      <span className="max-w-[200px] truncate">{importItem.fileName}</span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline">{getSourceBankLabel(importItem.sourceBank)}</Badge>
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {formatDate(importItem.uploadedAt)}
                  </TableCell>
                  <TableCell>{getStatusBadge(importItem.status)}</TableCell>
                  <TableCell className="text-right font-medium">
                    {importItem.totalRows}
                  </TableCell>
                  <TableCell className="text-right text-green-600 font-medium">
                    {importItem.matchedRows}
                  </TableCell>
                  <TableCell className="text-right text-yellow-600 font-medium">
                    {importItem.unmatchedRows}
                  </TableCell>
                  <TableCell onClick={(e) => e.stopPropagation()}>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon" aria-label="Import actions">
                          <MoreVertical className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => handleViewImport(importItem)}>
                          <Eye className="mr-2 h-4 w-4" />
                          View Details
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          onClick={() => handleDeleteImport(importItem)}
                          className="text-destructive"
                        >
                          <Trash2 className="mr-2 h-4 w-4" />
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      {data && data.totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Showing {(page - 1) * DEFAULT_PAGE_SIZE + 1} to {Math.min(page * DEFAULT_PAGE_SIZE, data.total)} of{' '}
            {data.total} imports
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
