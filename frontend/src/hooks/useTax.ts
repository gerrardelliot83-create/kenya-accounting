import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import type { UpdateTaxSettingsRequest } from '@/types/tax';
import { useToast } from '@/hooks/use-toast';

const TAX_SETTINGS_QUERY_KEY = 'tax-settings';
const VAT_SUMMARY_QUERY_KEY = 'vat-summary';
const TOT_SUMMARY_QUERY_KEY = 'tot-summary';
const FILING_GUIDANCE_QUERY_KEY = 'filing-guidance';

/**
 * Hook to fetch tax settings
 */
export const useTaxSettings = () => {
  return useQuery({
    queryKey: [TAX_SETTINGS_QUERY_KEY],
    queryFn: () => apiClient.getTaxSettings(),
  });
};

/**
 * Hook to update tax settings
 */
export const useUpdateTaxSettings = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (data: UpdateTaxSettingsRequest) => apiClient.updateTaxSettings(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [TAX_SETTINGS_QUERY_KEY] });
      queryClient.invalidateQueries({ queryKey: [VAT_SUMMARY_QUERY_KEY] });
      queryClient.invalidateQueries({ queryKey: [TOT_SUMMARY_QUERY_KEY] });
      queryClient.invalidateQueries({ queryKey: [FILING_GUIDANCE_QUERY_KEY] });
      toast({
        title: 'Success',
        description: 'Tax settings updated successfully',
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to update tax settings',
        variant: 'destructive',
      });
    },
  });
};

/**
 * Hook to fetch VAT summary for a date range
 */
export const useVATSummary = (startDate: string, endDate: string) => {
  return useQuery({
    queryKey: [VAT_SUMMARY_QUERY_KEY, startDate, endDate],
    queryFn: () => apiClient.getVATSummary(startDate, endDate),
    enabled: !!startDate && !!endDate,
  });
};

/**
 * Hook to fetch TOT summary for a date range
 */
export const useTOTSummary = (startDate: string, endDate: string) => {
  return useQuery({
    queryKey: [TOT_SUMMARY_QUERY_KEY, startDate, endDate],
    queryFn: () => apiClient.getTOTSummary(startDate, endDate),
    enabled: !!startDate && !!endDate,
  });
};

/**
 * Hook to fetch filing guidance
 */
export const useFilingGuidance = () => {
  return useQuery({
    queryKey: [FILING_GUIDANCE_QUERY_KEY],
    queryFn: () => apiClient.getFilingGuidance(),
  });
};

/**
 * Hook to export VAT return as CSV
 */
export const useExportVATReturn = () => {
  const { toast } = useToast();

  return useMutation({
    mutationFn: ({ startDate, endDate }: { startDate: string; endDate: string }) =>
      apiClient.exportVATReturn(startDate, endDate),
    onSuccess: (blob) => {
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `vat-return-${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      toast({
        title: 'Success',
        description: 'VAT return exported successfully',
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to export VAT return',
        variant: 'destructive',
      });
    },
  });
};
