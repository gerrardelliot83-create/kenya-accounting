import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import type {
  BankImportsListParams,
  BankTransactionsListParams,
  UpdateColumnMappingRequest,
  ProcessImportRequest,
  MatchTransactionRequest,
} from '@/types/bank-import';
import { useToast } from '@/hooks/use-toast';

const BANK_IMPORTS_QUERY_KEY = 'bank-imports';
const BANK_TRANSACTIONS_QUERY_KEY = 'bank-transactions';
const RECONCILIATION_SUGGESTIONS_QUERY_KEY = 'reconciliation-suggestions';

// Bank Imports Queries
export const useBankImports = (params?: BankImportsListParams) => {
  return useQuery({
    queryKey: [BANK_IMPORTS_QUERY_KEY, params],
    queryFn: () => apiClient.getBankImports(params),
  });
};

export const useBankImport = (id: string) => {
  return useQuery({
    queryKey: [BANK_IMPORTS_QUERY_KEY, id],
    queryFn: () => apiClient.getBankImport(id),
    enabled: !!id,
  });
};

export const useImportPreview = (id: string) => {
  return useQuery({
    queryKey: [BANK_IMPORTS_QUERY_KEY, id, 'preview'],
    queryFn: () => apiClient.getImportPreview(id),
    enabled: !!id,
  });
};

// Bank Imports Mutations
export const useCreateBankImport = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: ({ file, sourceBank }: { file: File; sourceBank: string }) =>
      apiClient.createBankImport(file, sourceBank),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [BANK_IMPORTS_QUERY_KEY] });
      toast({
        title: 'Success',
        description: 'Bank import file uploaded successfully',
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to upload bank import file',
        variant: 'destructive',
      });
    },
  });
};

export const useUpdateColumnMapping = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateColumnMappingRequest }) =>
      apiClient.updateColumnMapping(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: [BANK_IMPORTS_QUERY_KEY, variables.id] });
      queryClient.invalidateQueries({ queryKey: [BANK_IMPORTS_QUERY_KEY] });
      toast({
        title: 'Success',
        description: 'Column mapping updated successfully',
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to update column mapping',
        variant: 'destructive',
      });
    },
  });
};

export const useProcessImport = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data?: ProcessImportRequest }) =>
      apiClient.processImport(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: [BANK_IMPORTS_QUERY_KEY, variables.id] });
      queryClient.invalidateQueries({ queryKey: [BANK_IMPORTS_QUERY_KEY] });
      queryClient.invalidateQueries({ queryKey: [BANK_TRANSACTIONS_QUERY_KEY] });
      toast({
        title: 'Success',
        description: 'Bank import processed successfully',
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to process bank import',
        variant: 'destructive',
      });
    },
  });
};

export const useDeleteBankImport = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (id: string) => apiClient.deleteBankImport(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [BANK_IMPORTS_QUERY_KEY] });
      toast({
        title: 'Success',
        description: 'Bank import deleted successfully',
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to delete bank import',
        variant: 'destructive',
      });
    },
  });
};

// Bank Transactions Queries
export const useBankTransactions = (importId: string, params?: BankTransactionsListParams) => {
  return useQuery({
    queryKey: [BANK_TRANSACTIONS_QUERY_KEY, importId, params],
    queryFn: () => apiClient.getBankTransactions(importId, params),
    enabled: !!importId,
  });
};

export const useBankTransaction = (id: string) => {
  return useQuery({
    queryKey: [BANK_TRANSACTIONS_QUERY_KEY, id],
    queryFn: () => apiClient.getBankTransaction(id),
    enabled: !!id,
  });
};

export const useReconciliationSuggestions = (transactionId: string) => {
  return useQuery({
    queryKey: [RECONCILIATION_SUGGESTIONS_QUERY_KEY, transactionId],
    queryFn: () => apiClient.getReconciliationSuggestions(transactionId),
    enabled: !!transactionId,
  });
};

// Bank Transactions Mutations
export const useMatchTransaction = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: ({ transactionId, data }: { transactionId: string; data: MatchTransactionRequest }) =>
      apiClient.matchTransaction(transactionId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [BANK_TRANSACTIONS_QUERY_KEY] });
      queryClient.invalidateQueries({ queryKey: [BANK_IMPORTS_QUERY_KEY] });
      toast({
        title: 'Success',
        description: 'Transaction matched successfully',
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to match transaction',
        variant: 'destructive',
      });
    },
  });
};

export const useUnmatchTransaction = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (transactionId: string) => apiClient.unmatchTransaction(transactionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [BANK_TRANSACTIONS_QUERY_KEY] });
      queryClient.invalidateQueries({ queryKey: [BANK_IMPORTS_QUERY_KEY] });
      toast({
        title: 'Success',
        description: 'Transaction unmatched successfully',
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to unmatch transaction',
        variant: 'destructive',
      });
    },
  });
};

export const useIgnoreTransaction = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (transactionId: string) => apiClient.ignoreTransaction(transactionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [BANK_TRANSACTIONS_QUERY_KEY] });
      queryClient.invalidateQueries({ queryKey: [BANK_IMPORTS_QUERY_KEY] });
      toast({
        title: 'Success',
        description: 'Transaction ignored successfully',
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to ignore transaction',
        variant: 'destructive',
      });
    },
  });
};
