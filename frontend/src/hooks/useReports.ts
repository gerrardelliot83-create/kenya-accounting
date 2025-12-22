import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';

const PROFIT_LOSS_QUERY_KEY = 'profit-loss-report';
const EXPENSE_SUMMARY_QUERY_KEY = 'expense-summary-report';
const AGED_RECEIVABLES_QUERY_KEY = 'aged-receivables-report';
const SALES_SUMMARY_QUERY_KEY = 'sales-summary-report';

/**
 * Hook to fetch Profit & Loss report
 */
export const useProfitLoss = (startDate: string, endDate: string) => {
  return useQuery({
    queryKey: [PROFIT_LOSS_QUERY_KEY, startDate, endDate],
    queryFn: () => apiClient.getProfitLossReport(startDate, endDate),
    enabled: !!startDate && !!endDate,
  });
};

/**
 * Hook to fetch Expense Summary report
 */
export const useExpenseSummaryReport = (startDate: string, endDate: string) => {
  return useQuery({
    queryKey: [EXPENSE_SUMMARY_QUERY_KEY, startDate, endDate],
    queryFn: () => apiClient.getExpenseSummaryReport(startDate, endDate),
    enabled: !!startDate && !!endDate,
  });
};

/**
 * Hook to fetch Aged Receivables report
 */
export const useAgedReceivables = (asOfDate?: string) => {
  return useQuery({
    queryKey: [AGED_RECEIVABLES_QUERY_KEY, asOfDate],
    queryFn: () => apiClient.getAgedReceivablesReport(asOfDate),
  });
};

/**
 * Hook to fetch Sales Summary report
 */
export const useSalesSummary = (startDate: string, endDate: string) => {
  return useQuery({
    queryKey: [SALES_SUMMARY_QUERY_KEY, startDate, endDate],
    queryFn: () => apiClient.getSalesSummaryReport(startDate, endDate),
    enabled: !!startDate && !!endDate,
  });
};
