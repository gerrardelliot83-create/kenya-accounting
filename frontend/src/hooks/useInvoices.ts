import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import type {
  InvoicesListParams,
  CreateInvoiceRequest,
  UpdateInvoiceRequest,
} from '@/types/invoice';
import { useToast } from '@/hooks/use-toast';

const INVOICES_QUERY_KEY = 'invoices';

export const useInvoices = (params?: InvoicesListParams) => {
  return useQuery({
    queryKey: [INVOICES_QUERY_KEY, params],
    queryFn: () => apiClient.getInvoices(params),
  });
};

export const useInvoice = (id: string) => {
  return useQuery({
    queryKey: [INVOICES_QUERY_KEY, id],
    queryFn: () => apiClient.getInvoice(id),
    enabled: !!id,
  });
};

export const useCreateInvoice = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (data: CreateInvoiceRequest) => apiClient.createInvoice(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [INVOICES_QUERY_KEY] });
      toast({
        title: 'Success',
        description: 'Invoice created successfully',
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to create invoice',
        variant: 'destructive',
      });
    },
  });
};

export const useUpdateInvoice = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateInvoiceRequest }) =>
      apiClient.updateInvoice(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [INVOICES_QUERY_KEY] });
      toast({
        title: 'Success',
        description: 'Invoice updated successfully',
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to update invoice',
        variant: 'destructive',
      });
    },
  });
};

export const useIssueInvoice = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (id: string) => apiClient.issueInvoice(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [INVOICES_QUERY_KEY] });
      toast({
        title: 'Success',
        description: 'Invoice issued successfully',
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to issue invoice',
        variant: 'destructive',
      });
    },
  });
};

export const useCancelInvoice = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (id: string) => apiClient.cancelInvoice(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [INVOICES_QUERY_KEY] });
      toast({
        title: 'Success',
        description: 'Invoice cancelled successfully',
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to cancel invoice',
        variant: 'destructive',
      });
    },
  });
};

export const useDownloadInvoicePdf = () => {
  const { toast } = useToast();

  return useMutation({
    mutationFn: async (id: string) => {
      const blob = await apiClient.getInvoicePdf(id);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `invoice-${id}.pdf`;
      link.click();
      window.URL.revokeObjectURL(url);
    },
    onSuccess: () => {
      toast({
        title: 'Success',
        description: 'Invoice downloaded successfully',
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to download invoice',
        variant: 'destructive',
      });
    },
  });
};
