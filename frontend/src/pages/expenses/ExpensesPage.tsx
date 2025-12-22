import { useState, useMemo } from 'react';
import { Plus, MoreVertical, Edit, Trash2 } from 'lucide-react';
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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { useExpenses, useDeleteExpense, useExpenseCategories, useExpenseSummary } from '@/hooks/useExpenses';
import { ExpenseFormModal } from './ExpenseFormModal';
import type { Expense, PaymentMethod, ExpensesListParams } from '@/types/expense';
import { DEFAULT_PAGE_SIZE } from '@/lib/constants';
import { formatCurrency } from '@/lib/formatters';

export const ExpensesPage = () => {
  const [page, setPage] = useState(1);
  const [category, setCategory] = useState<string>('all');
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod | 'all'>('all');
  const [isReconciled, setIsReconciled] = useState<string>('all');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedExpense, setSelectedExpense] = useState<Expense | undefined>();

  const { data: categories } = useExpenseCategories();

  const queryParams = useMemo(() => {
    const params: ExpensesListParams = { page, limit: DEFAULT_PAGE_SIZE };
    if (category !== 'all') params.category = category;
    if (paymentMethod !== 'all') params.paymentMethod = paymentMethod;
    if (isReconciled !== 'all') params.isReconciled = isReconciled === 'true';
    if (startDate) params.startDate = startDate;
    if (endDate) params.endDate = endDate;
    return params;
  }, [page, category, paymentMethod, isReconciled, startDate, endDate]);

  const { data, isLoading } = useExpenses(queryParams);
  const { data: summary } = useExpenseSummary(startDate, endDate);
  const deleteExpense = useDeleteExpense();

  const handleAddExpense = () => {
    setSelectedExpense(undefined);
    setIsModalOpen(true);
  };

  const handleEditExpense = (expense: Expense) => {
    setSelectedExpense(expense);
    setIsModalOpen(true);
  };

  const handleDeleteExpense = async (expense: Expense) => {
    if (window.confirm(`Are you sure you want to delete this expense: ${expense.description}?`)) {
      await deleteExpense.mutateAsync(expense.id);
    }
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedExpense(undefined);
  };

  const getPaymentMethodBadge = (method: PaymentMethod) => {
    const variants: Record<PaymentMethod, string> = {
      cash: 'Cash',
      bank_transfer: 'Bank Transfer',
      mpesa: 'M-Pesa',
      card: 'Card',
      other: 'Other',
    };
    return <Badge variant="outline">{variants[method]}</Badge>;
  };

  const getReconciledBadge = (reconciled: boolean) => {
    return (
      <Badge variant={reconciled ? 'default' : 'secondary'}>
        {reconciled ? 'Reconciled' : 'Pending'}
      </Badge>
    );
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-KE', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-semibold">Expenses</h1>
          <p className="mt-2 text-muted-foreground">
            Track and manage your business expenses
          </p>
        </div>
        <Button onClick={handleAddExpense}>
          <Plus className="mr-2 h-4 w-4" />
          Add Expense
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Expenses</CardTitle>
          </CardHeader>
          <CardContent>
            {summary ? (
              <div className="text-2xl font-bold">
                {formatCurrency(summary.totalAmount)}
              </div>
            ) : (
              <Skeleton className="h-8 w-32" />
            )}
            {summary && (
              <p className="text-xs text-muted-foreground mt-1">
                {summary.totalCount} transactions
              </p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Top Category</CardTitle>
          </CardHeader>
          <CardContent>
            {summary && summary.summary.length > 0 ? (
              <>
                <div className="text-2xl font-bold">
                  {summary.summary[0].category}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  {formatCurrency(summary.summary[0].total)}
                </p>
              </>
            ) : (
              <div className="text-sm text-muted-foreground">No expenses yet</div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Categories</CardTitle>
          </CardHeader>
          <CardContent>
            {summary ? (
              <div className="text-2xl font-bold">{summary.summary.length}</div>
            ) : (
              <Skeleton className="h-8 w-16" />
            )}
            {summary && (
              <p className="text-xs text-muted-foreground mt-1">
                Active expense categories
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex flex-col gap-4">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-5">
          <Select
            value={category}
            onValueChange={(value) => {
              setCategory(value);
              setPage(1);
            }}
          >
            <SelectTrigger>
              <SelectValue placeholder="All Categories" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Categories</SelectItem>
              {categories?.map((cat) => (
                <SelectItem key={cat.id} value={cat.name}>
                  {cat.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select
            value={paymentMethod}
            onValueChange={(value) => {
              setPaymentMethod(value as PaymentMethod | 'all');
              setPage(1);
            }}
          >
            <SelectTrigger>
              <SelectValue placeholder="Payment Method" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Methods</SelectItem>
              <SelectItem value="cash">Cash</SelectItem>
              <SelectItem value="bank_transfer">Bank Transfer</SelectItem>
              <SelectItem value="mpesa">M-Pesa</SelectItem>
              <SelectItem value="card">Card</SelectItem>
              <SelectItem value="other">Other</SelectItem>
            </SelectContent>
          </Select>

          <Select
            value={isReconciled}
            onValueChange={(value) => {
              setIsReconciled(value);
              setPage(1);
            }}
          >
            <SelectTrigger>
              <SelectValue placeholder="Reconciliation Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="true">Reconciled</SelectItem>
              <SelectItem value="false">Pending</SelectItem>
            </SelectContent>
          </Select>

          <Input
            type="date"
            placeholder="Start Date"
            value={startDate}
            onChange={(e) => {
              setStartDate(e.target.value);
              setPage(1);
            }}
          />

          <Input
            type="date"
            placeholder="End Date"
            value={endDate}
            onChange={(e) => {
              setEndDate(e.target.value);
              setPage(1);
            }}
          />
        </div>

        {(category !== 'all' || paymentMethod !== 'all' || isReconciled !== 'all' || startDate || endDate) && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              setCategory('all');
              setPaymentMethod('all');
              setIsReconciled('all');
              setStartDate('');
              setEndDate('');
              setPage(1);
            }}
            className="w-fit"
          >
            Clear Filters
          </Button>
        )}
      </div>

      {/* Expenses Table */}
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Date</TableHead>
              <TableHead>Category</TableHead>
              <TableHead>Vendor</TableHead>
              <TableHead>Description</TableHead>
              <TableHead className="text-right">Amount</TableHead>
              <TableHead>Payment Method</TableHead>
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
                    <Skeleton className="h-4 w-24" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="h-4 w-32" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="h-4 w-40" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="h-4 w-20" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="h-4 w-24" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="h-4 w-20" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="h-8 w-8" />
                  </TableCell>
                </TableRow>
              ))
            ) : data?.expenses.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} className="text-center py-8">
                  <p className="text-muted-foreground">No expenses found</p>
                  <Button variant="link" onClick={handleAddExpense} className="mt-2">
                    Create your first expense
                  </Button>
                </TableCell>
              </TableRow>
            ) : (
              data?.expenses.map((expense) => (
                <TableRow key={expense.id}>
                  <TableCell className="font-medium">
                    {formatDate(expense.expenseDate)}
                  </TableCell>
                  <TableCell>
                    <Badge variant="secondary">{expense.category}</Badge>
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {expense.vendorName || '-'}
                  </TableCell>
                  <TableCell className="max-w-[200px] truncate">
                    {expense.description}
                  </TableCell>
                  <TableCell className="text-right font-medium">
                    {formatCurrency(expense.amount)}
                  </TableCell>
                  <TableCell>{getPaymentMethodBadge(expense.paymentMethod)}</TableCell>
                  <TableCell>{getReconciledBadge(expense.isReconciled)}</TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon" aria-label="Expense actions">
                          <MoreVertical className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => handleEditExpense(expense)}>
                          <Edit className="mr-2 h-4 w-4" />
                          Edit
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          onClick={() => handleDeleteExpense(expense)}
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
            {data.total} expenses
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

      <ExpenseFormModal
        open={isModalOpen}
        onClose={handleCloseModal}
        expense={selectedExpense}
      />
    </div>
  );
};
