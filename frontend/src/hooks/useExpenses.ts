import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import type {
  ExpensesListParams,
  CreateExpenseRequest,
  UpdateExpenseRequest,
} from '@/types/expense';
import { useToast } from '@/hooks/use-toast';

const EXPENSES_QUERY_KEY = 'expenses';
const EXPENSE_CATEGORIES_QUERY_KEY = 'expense-categories';
const EXPENSE_SUMMARY_QUERY_KEY = 'expense-summary';

export const useExpenses = (params?: ExpensesListParams) => {
  return useQuery({
    queryKey: [EXPENSES_QUERY_KEY, params],
    queryFn: () => apiClient.getExpenses(params),
  });
};

export const useExpense = (id: string) => {
  return useQuery({
    queryKey: [EXPENSES_QUERY_KEY, id],
    queryFn: () => apiClient.getExpense(id),
    enabled: !!id,
  });
};

export const useExpenseCategories = () => {
  return useQuery({
    queryKey: [EXPENSE_CATEGORIES_QUERY_KEY],
    queryFn: () => apiClient.getExpenseCategories(),
  });
};

export const useExpenseSummary = (startDate?: string, endDate?: string) => {
  return useQuery({
    queryKey: [EXPENSE_SUMMARY_QUERY_KEY, startDate, endDate],
    queryFn: () => apiClient.getExpenseSummary(startDate, endDate),
    enabled: !!startDate || !!endDate,
  });
};

export const useCreateExpense = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (data: CreateExpenseRequest) => apiClient.createExpense(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [EXPENSES_QUERY_KEY] });
      queryClient.invalidateQueries({ queryKey: [EXPENSE_SUMMARY_QUERY_KEY] });
      toast({
        title: 'Success',
        description: 'Expense created successfully',
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to create expense',
        variant: 'destructive',
      });
    },
  });
};

export const useUpdateExpense = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateExpenseRequest }) =>
      apiClient.updateExpense(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [EXPENSES_QUERY_KEY] });
      queryClient.invalidateQueries({ queryKey: [EXPENSE_SUMMARY_QUERY_KEY] });
      toast({
        title: 'Success',
        description: 'Expense updated successfully',
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to update expense',
        variant: 'destructive',
      });
    },
  });
};

export const useDeleteExpense = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (id: string) => apiClient.deleteExpense(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [EXPENSES_QUERY_KEY] });
      queryClient.invalidateQueries({ queryKey: [EXPENSE_SUMMARY_QUERY_KEY] });
      toast({
        title: 'Success',
        description: 'Expense deleted successfully',
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to delete expense',
        variant: 'destructive',
      });
    },
  });
};

export const useCreateExpenseCategory = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (data: { name: string; description?: string }) =>
      apiClient.createExpenseCategory(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [EXPENSE_CATEGORIES_QUERY_KEY] });
      toast({
        title: 'Success',
        description: 'Category created successfully',
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to create category',
        variant: 'destructive',
      });
    },
  });
};
