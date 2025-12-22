import axios, { AxiosError } from 'axios';
import type { AxiosInstance } from 'axios';
import type { LoginRequest, LoginResponse, ChangePasswordRequest, User } from '@/types/auth';
import type { ApiError } from '@/types/api';
import type {
  Contact,
  CreateContactRequest,
  UpdateContactRequest,
  ContactsListParams,
  ContactsListResponse,
} from '@/types/contact';
import type {
  Item,
  CreateItemRequest,
  UpdateItemRequest,
  ItemsListParams,
  ItemsListResponse,
} from '@/types/item';
import type {
  Invoice,
  CreateInvoiceRequest,
  UpdateInvoiceRequest,
  InvoicesListParams,
  InvoicesListResponse,
} from '@/types/invoice';
import type {
  Expense,
  CreateExpenseRequest,
  UpdateExpenseRequest,
  ExpensesListParams,
  ExpensesListResponse,
  ExpenseCategory,
  ExpenseSummaryResponse,
} from '@/types/expense';
import type {
  BankImport,
  BankImportsListParams,
  BankImportsListResponse,
  BankTransaction,
  BankTransactionsListParams,
  BankTransactionsListResponse,
  UpdateColumnMappingRequest,
  ProcessImportRequest,
  ReconciliationSuggestion,
  MatchTransactionRequest,
  PreviewData,
} from '@/types/bank-import';
import type {
  FaqCategory,
  FaqArticle,
  HelpArticle,
  FaqSearchRequest,
  FaqSearchResponse,
} from '@/types/help';
import type {
  SupportTicket,
  TicketMessage,
  CreateTicket,
  AddMessageRequest,
  RateTicketRequest,
  TicketListParams,
  TicketListResponse,
  TicketDetailResponse,
} from '@/types/support';
import type {
  TaxSettings,
  UpdateTaxSettingsRequest,
  VATSummary,
  TOTSummary,
  FilingGuidance,
} from '@/types/tax';
import type {
  ProfitLossReport,
  ExpenseSummary,
  AgedReceivables,
  SalesSummary,
} from '@/types/report';
import type {
  AdminDashboardStats,
  BusinessListParams,
  BusinessListResponse,
  BusinessDetailResponse,
  InternalUserListParams,
  InternalUserListResponse,
  CreateInternalUserRequest,
  InternalUser,
  AuditLogParams,
  AuditLogResponse,
  SystemHealthMetrics,
} from '@/types/admin';
import type {
  BusinessApplication,
  CreateApplicationRequest,
  UpdateApplicationRequest,
  ApplicationsListParams,
  ApplicationsListResponse,
  ApprovalResponse,
  OnboardingStats,
  RejectApplicationRequest,
  RequestInfoRequest,
} from '@/types/onboarding';

// Get API URL from environment, with fallback for local development
const getRawApiUrl = (): string => {
  return import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
};

// Force HTTPS in production to prevent mixed content errors
const getApiUrl = (): string => {
  const rawUrl = getRawApiUrl();

  // In production (non-localhost), always use HTTPS
  if (!rawUrl.includes('localhost') && !rawUrl.includes('127.0.0.1')) {
    return rawUrl.replace(/^http:\/\//i, 'https://');
  }

  return rawUrl;
};

const API_URL = getApiUrl();

// Token storage keys
const ACCESS_TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor for adding auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem(ACCESS_TOKEN_KEY);
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError<ApiError>) => {
        if (error.response) {
          // Server responded with error
          const apiError: ApiError = {
            message: error.response.data?.message || 'An error occurred',
            code: error.response.data?.code,
            details: error.response.data?.details,
          };

          // Handle 401 Unauthorized
          if (error.response.status === 401) {
            // Clear tokens and redirect to login
            localStorage.removeItem(ACCESS_TOKEN_KEY);
            localStorage.removeItem(REFRESH_TOKEN_KEY);
            window.location.href = '/login';
          }

          return Promise.reject(apiError);
        } else if (error.request) {
          // Request made but no response
          return Promise.reject({
            message: 'No response from server. Please check your connection.',
          });
        } else {
          // Error setting up request
          return Promise.reject({
            message: error.message || 'An unexpected error occurred',
          });
        }
      }
    );
  }

  // Auth endpoints
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await this.client.post<LoginResponse>('/auth/login', credentials);
    // Store tokens
    localStorage.setItem(ACCESS_TOKEN_KEY, response.data.accessToken);
    localStorage.setItem(REFRESH_TOKEN_KEY, response.data.refreshToken);
    return response.data;
  }

  async logout(): Promise<void> {
    try {
      await this.client.post('/auth/logout');
    } finally {
      // Clear tokens
      localStorage.removeItem(ACCESS_TOKEN_KEY);
      localStorage.removeItem(REFRESH_TOKEN_KEY);
    }
  }

  // Clear tokens (for use when session expires)
  clearTokens(): void {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  }

  async changePassword(data: ChangePasswordRequest): Promise<void> {
    await this.client.post('/auth/change-password', data);
  }

  async getCurrentUser(): Promise<User> {
    const response = await this.client.get<User>('/auth/me');
    return response.data;
  }

  async refreshToken(): Promise<{ accessToken: string }> {
    const response = await this.client.post<{ accessToken: string }>('/auth/refresh');
    return response.data;
  }

  // Contacts endpoints
  async getContacts(params?: ContactsListParams): Promise<ContactsListResponse> {
    const response = await this.client.get<ContactsListResponse>('/contacts', { params });
    return response.data;
  }

  async getContact(id: string): Promise<Contact> {
    const response = await this.client.get<Contact>(`/contacts/${id}`);
    return response.data;
  }

  async createContact(data: CreateContactRequest): Promise<Contact> {
    const response = await this.client.post<Contact>('/contacts', data);
    return response.data;
  }

  async updateContact(id: string, data: UpdateContactRequest): Promise<Contact> {
    const response = await this.client.put<Contact>(`/contacts/${id}`, data);
    return response.data;
  }

  async deleteContact(id: string): Promise<void> {
    await this.client.delete(`/contacts/${id}`);
  }

  // Items endpoints
  async getItems(params?: ItemsListParams): Promise<ItemsListResponse> {
    const response = await this.client.get<ItemsListResponse>('/items', { params });
    return response.data;
  }

  async getItem(id: string): Promise<Item> {
    const response = await this.client.get<Item>(`/items/${id}`);
    return response.data;
  }

  async createItem(data: CreateItemRequest): Promise<Item> {
    const response = await this.client.post<Item>('/items', data);
    return response.data;
  }

  async updateItem(id: string, data: UpdateItemRequest): Promise<Item> {
    const response = await this.client.put<Item>(`/items/${id}`, data);
    return response.data;
  }

  async deleteItem(id: string): Promise<void> {
    await this.client.delete(`/items/${id}`);
  }

  // Invoices endpoints
  async getInvoices(params?: InvoicesListParams): Promise<InvoicesListResponse> {
    const response = await this.client.get<InvoicesListResponse>('/invoices', { params });
    return response.data;
  }

  async getInvoice(id: string): Promise<Invoice> {
    const response = await this.client.get<Invoice>(`/invoices/${id}`);
    return response.data;
  }

  async createInvoice(data: CreateInvoiceRequest): Promise<Invoice> {
    const response = await this.client.post<Invoice>('/invoices', data);
    return response.data;
  }

  async updateInvoice(id: string, data: UpdateInvoiceRequest): Promise<Invoice> {
    const response = await this.client.put<Invoice>(`/invoices/${id}`, data);
    return response.data;
  }

  async issueInvoice(id: string): Promise<Invoice> {
    const response = await this.client.post<Invoice>(`/invoices/${id}/issue`);
    return response.data;
  }

  async cancelInvoice(id: string): Promise<Invoice> {
    const response = await this.client.post<Invoice>(`/invoices/${id}/cancel`);
    return response.data;
  }

  async getInvoicePdf(id: string): Promise<Blob> {
    const response = await this.client.get(`/invoices/${id}/pdf`, {
      responseType: 'blob',
    });
    return response.data;
  }

  // Expenses endpoints
  async getExpenses(params?: ExpensesListParams): Promise<ExpensesListResponse> {
    const response = await this.client.get<ExpensesListResponse>('/expenses', { params });
    return response.data;
  }

  async getExpense(id: string): Promise<Expense> {
    const response = await this.client.get<Expense>(`/expenses/${id}`);
    return response.data;
  }

  async createExpense(data: CreateExpenseRequest): Promise<Expense> {
    const response = await this.client.post<Expense>('/expenses', data);
    return response.data;
  }

  async updateExpense(id: string, data: UpdateExpenseRequest): Promise<Expense> {
    const response = await this.client.put<Expense>(`/expenses/${id}`, data);
    return response.data;
  }

  async deleteExpense(id: string): Promise<void> {
    await this.client.delete(`/expenses/${id}`);
  }

  async getExpenseCategories(): Promise<ExpenseCategory[]> {
    const response = await this.client.get<ExpenseCategory[]>('/expenses/categories');
    return response.data;
  }

  async createExpenseCategory(data: { name: string; description?: string }): Promise<ExpenseCategory> {
    const response = await this.client.post<ExpenseCategory>('/expenses/categories', data);
    return response.data;
  }

  async getExpenseSummary(startDate?: string, endDate?: string): Promise<ExpenseSummaryResponse> {
    const response = await this.client.get<ExpenseSummaryResponse>('/expenses/summary', {
      params: { start_date: startDate, end_date: endDate },
    });
    return response.data;
  }

  // Bank Imports endpoints
  async createBankImport(file: File, sourceBank: string): Promise<BankImport> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('source_bank', sourceBank);

    const response = await this.client.post<BankImport>('/bank-imports', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  async getBankImports(params?: BankImportsListParams): Promise<BankImportsListResponse> {
    const response = await this.client.get<BankImportsListResponse>('/bank-imports', { params });
    return response.data;
  }

  async getBankImport(id: string): Promise<BankImport> {
    const response = await this.client.get<BankImport>(`/bank-imports/${id}`);
    return response.data;
  }

  async updateColumnMapping(id: string, data: UpdateColumnMappingRequest): Promise<BankImport> {
    const response = await this.client.patch<BankImport>(`/bank-imports/${id}/mapping`, data);
    return response.data;
  }

  async processImport(id: string, data?: ProcessImportRequest): Promise<BankImport> {
    const response = await this.client.post<BankImport>(`/bank-imports/${id}/process`, data);
    return response.data;
  }

  async getImportPreview(id: string): Promise<PreviewData> {
    const response = await this.client.get<PreviewData>(`/bank-imports/${id}/preview`);
    return response.data;
  }

  async deleteBankImport(id: string): Promise<void> {
    await this.client.delete(`/bank-imports/${id}`);
  }

  // Bank Transactions endpoints
  async getBankTransactions(
    importId: string,
    params?: BankTransactionsListParams
  ): Promise<BankTransactionsListResponse> {
    const response = await this.client.get<BankTransactionsListResponse>(
      `/bank-imports/${importId}/transactions`,
      { params }
    );
    return response.data;
  }

  async getBankTransaction(id: string): Promise<BankTransaction> {
    const response = await this.client.get<BankTransaction>(`/bank-transactions/${id}`);
    return response.data;
  }

  async getReconciliationSuggestions(transactionId: string): Promise<ReconciliationSuggestion[]> {
    const response = await this.client.get<ReconciliationSuggestion[]>(
      `/bank-transactions/${transactionId}/suggestions`
    );
    return response.data;
  }

  async matchTransaction(transactionId: string, data: MatchTransactionRequest): Promise<BankTransaction> {
    const response = await this.client.post<BankTransaction>(
      `/bank-transactions/${transactionId}/match`,
      data
    );
    return response.data;
  }

  async unmatchTransaction(transactionId: string): Promise<BankTransaction> {
    const response = await this.client.delete<BankTransaction>(`/bank-transactions/${transactionId}/match`);
    return response.data;
  }

  async ignoreTransaction(transactionId: string): Promise<BankTransaction> {
    const response = await this.client.post<BankTransaction>(`/bank-transactions/${transactionId}/ignore`);
    return response.data;
  }

  // FAQ & Help Articles endpoints
  async getFaqCategories(): Promise<FaqCategory[]> {
    const response = await this.client.get<{ categories: FaqCategory[]; total: number }>('/support/faq/categories');
    return response.data.categories || [];
  }

  async getFaqArticles(categoryId?: string): Promise<FaqArticle[]> {
    const response = await this.client.get<{ articles: FaqArticle[]; total: number }>('/support/faq', {
      params: categoryId ? { category_id: categoryId } : undefined,
    });
    return response.data.articles || [];
  }

  async searchFaq(data: FaqSearchRequest): Promise<FaqSearchResponse> {
    const response = await this.client.post<FaqSearchResponse>('/support/faq/search', data);
    return response.data;
  }

  async getFaqArticle(id: string): Promise<FaqArticle> {
    const response = await this.client.get<FaqArticle>(`/support/faq/${id}`);
    return response.data;
  }

  async getHelpArticles(): Promise<HelpArticle[]> {
    const response = await this.client.get<{ articles: HelpArticle[]; total: number }>('/support/articles');
    return response.data.articles || [];
  }

  async getHelpArticle(slug: string): Promise<HelpArticle> {
    const response = await this.client.get<HelpArticle>(`/support/articles/${slug}`);
    return response.data;
  }

  // Support Tickets endpoints
  async getMyTickets(params?: TicketListParams): Promise<TicketListResponse> {
    const response = await this.client.get<TicketListResponse>('/support/tickets', { params });
    return response.data;
  }

  async getTicket(id: string): Promise<TicketDetailResponse> {
    const response = await this.client.get<TicketDetailResponse>(`/support/tickets/${id}`);
    return response.data;
  }

  async createTicket(data: CreateTicket): Promise<SupportTicket> {
    const response = await this.client.post<SupportTicket>('/support/tickets', data);
    return response.data;
  }

  async addTicketMessage(ticketId: string, data: AddMessageRequest): Promise<TicketMessage> {
    const formData = new FormData();
    formData.append('message', data.message);
    if (data.attachments) {
      data.attachments.forEach((file) => {
        formData.append('attachments', file);
      });
    }

    const response = await this.client.post<TicketMessage>(
      `/support/tickets/${ticketId}/messages`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  }

  async rateTicket(ticketId: string, data: RateTicketRequest): Promise<SupportTicket> {
    const response = await this.client.post<SupportTicket>(`/support/tickets/${ticketId}/rate`, data);
    return response.data;
  }

  // Tax endpoints
  async getTaxSettings(): Promise<TaxSettings> {
    const response = await this.client.get<TaxSettings>('/tax/settings');
    return response.data;
  }

  async updateTaxSettings(data: UpdateTaxSettingsRequest): Promise<TaxSettings> {
    const response = await this.client.put<TaxSettings>('/tax/settings', data);
    return response.data;
  }

  async getVATSummary(startDate: string, endDate: string): Promise<VATSummary> {
    const response = await this.client.get<VATSummary>('/tax/vat-summary', {
      params: { start_date: startDate, end_date: endDate },
    });
    return response.data;
  }

  async getTOTSummary(startDate: string, endDate: string): Promise<TOTSummary> {
    const response = await this.client.get<TOTSummary>('/tax/tot-summary', {
      params: { start_date: startDate, end_date: endDate },
    });
    return response.data;
  }

  async getFilingGuidance(): Promise<FilingGuidance> {
    const response = await this.client.get<FilingGuidance>('/tax/filing-guidance');
    return response.data;
  }

  async exportVATReturn(startDate: string, endDate: string): Promise<Blob> {
    const response = await this.client.get('/tax/vat-return/export', {
      params: { start_date: startDate, end_date: endDate },
      responseType: 'blob',
    });
    return response.data;
  }

  // Reports endpoints
  async getProfitLossReport(startDate: string, endDate: string): Promise<ProfitLossReport> {
    const response = await this.client.get<ProfitLossReport>('/reports/profit-loss', {
      params: { start_date: startDate, end_date: endDate },
    });
    return response.data;
  }

  async getExpenseSummaryReport(startDate: string, endDate: string): Promise<ExpenseSummary> {
    const response = await this.client.get<ExpenseSummary>('/reports/expense-summary', {
      params: { start_date: startDate, end_date: endDate },
    });
    return response.data;
  }

  async getAgedReceivablesReport(asOfDate?: string): Promise<AgedReceivables> {
    const response = await this.client.get<AgedReceivables>('/reports/aged-receivables', {
      params: asOfDate ? { as_of_date: asOfDate } : undefined,
    });
    return response.data;
  }

  async getSalesSummaryReport(startDate: string, endDate: string): Promise<SalesSummary> {
    const response = await this.client.get<SalesSummary>('/reports/sales-summary', {
      params: { start_date: startDate, end_date: endDate },
    });
    return response.data;
  }

  // Admin endpoints
  async getAdminDashboardStats(): Promise<AdminDashboardStats> {
    const response = await this.client.get<AdminDashboardStats>('/admin/dashboard/stats');
    return response.data;
  }

  async getBusinesses(params?: BusinessListParams): Promise<BusinessListResponse> {
    const response = await this.client.get<BusinessListResponse>('/admin/businesses', { params });
    return response.data;
  }

  async getBusiness(id: string): Promise<BusinessDetailResponse> {
    const response = await this.client.get<BusinessDetailResponse>(`/admin/businesses/${id}`);
    return response.data;
  }

  async getInternalUsers(params?: InternalUserListParams): Promise<InternalUserListResponse> {
    const response = await this.client.get<InternalUserListResponse>('/admin/users', { params });
    return response.data;
  }

  async createInternalUser(data: CreateInternalUserRequest): Promise<InternalUser> {
    const response = await this.client.post<InternalUser>('/admin/users', data);
    return response.data;
  }

  async deactivateInternalUser(id: string): Promise<InternalUser> {
    const response = await this.client.post<InternalUser>(`/admin/users/${id}/deactivate`);
    return response.data;
  }

  async activateInternalUser(id: string): Promise<InternalUser> {
    const response = await this.client.post<InternalUser>(`/admin/users/${id}/activate`);
    return response.data;
  }

  async getAuditLogs(params?: AuditLogParams): Promise<AuditLogResponse> {
    const response = await this.client.get<AuditLogResponse>('/admin/audit-logs', { params });
    return response.data;
  }

  async getSystemHealth(): Promise<SystemHealthMetrics> {
    const response = await this.client.get<SystemHealthMetrics>('/admin/system/health');
    return response.data;
  }

  // Onboarding endpoints
  async createApplication(data: CreateApplicationRequest): Promise<BusinessApplication> {
    const response = await this.client.post<BusinessApplication>('/onboarding/applications', data);
    return response.data;
  }

  async getApplications(params?: ApplicationsListParams): Promise<ApplicationsListResponse> {
    const response = await this.client.get<ApplicationsListResponse>('/onboarding/applications', {
      params,
    });
    return response.data;
  }

  async getApplication(id: string): Promise<BusinessApplication> {
    const response = await this.client.get<BusinessApplication>(`/onboarding/applications/${id}`);
    return response.data;
  }

  async updateApplication(id: string, data: UpdateApplicationRequest): Promise<BusinessApplication> {
    const response = await this.client.put<BusinessApplication>(
      `/onboarding/applications/${id}`,
      data
    );
    return response.data;
  }

  async submitApplication(id: string): Promise<BusinessApplication> {
    const response = await this.client.post<BusinessApplication>(
      `/onboarding/applications/${id}/submit`
    );
    return response.data;
  }

  async approveApplication(id: string): Promise<ApprovalResponse> {
    const response = await this.client.post<ApprovalResponse>(
      `/onboarding/applications/${id}/approve`
    );
    return response.data;
  }

  async rejectApplication(id: string, data: RejectApplicationRequest): Promise<BusinessApplication> {
    const response = await this.client.post<BusinessApplication>(
      `/onboarding/applications/${id}/reject`,
      data
    );
    return response.data;
  }

  async requestInfo(id: string, data: RequestInfoRequest): Promise<BusinessApplication> {
    const response = await this.client.post<BusinessApplication>(
      `/onboarding/applications/${id}/request-info`,
      data
    );
    return response.data;
  }

  async getOnboardingStats(): Promise<OnboardingStats> {
    const response = await this.client.get<OnboardingStats>('/onboarding/stats');
    return response.data;
  }
}

export const apiClient = new ApiClient();
