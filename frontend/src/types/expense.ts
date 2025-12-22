export type PaymentMethod = 'cash' | 'bank_transfer' | 'mpesa' | 'card' | 'other';

export interface Expense {
  id: string;
  businessId: string;
  category: string;
  description: string;
  amount: number;
  taxAmount: number;
  expenseDate: string; // ISO date
  vendorName?: string;
  receiptUrl?: string;
  paymentMethod: PaymentMethod;
  referenceNumber?: string;
  isReconciled: boolean;
  notes?: string;
  createdAt: string;
  updatedAt: string;
}

export interface ExpenseCategory {
  id: string;
  name: string;
  description?: string;
  isSystem: boolean;
  isActive: boolean;
}

export interface CreateExpenseRequest {
  category: string;
  description: string;
  amount: number;
  taxAmount?: number;
  expenseDate: string;
  vendorName?: string;
  receiptUrl?: string;
  paymentMethod: PaymentMethod;
  referenceNumber?: string;
  notes?: string;
}

export interface UpdateExpenseRequest {
  category?: string;
  description?: string;
  amount?: number;
  taxAmount?: number;
  expenseDate?: string;
  vendorName?: string;
  receiptUrl?: string;
  paymentMethod?: PaymentMethod;
  referenceNumber?: string;
  notes?: string;
  isReconciled?: boolean;
}

export interface ExpensesListParams {
  page?: number;
  limit?: number;
  category?: string;
  paymentMethod?: PaymentMethod;
  startDate?: string;
  endDate?: string;
  isReconciled?: boolean;
}

export interface ExpensesListResponse {
  expenses: Expense[];
  total: number;
  page: number;
  limit: number;
  totalPages: number;
}

export interface ExpenseSummary {
  category: string;
  total: number;
  count: number;
}

export interface ExpenseSummaryResponse {
  summary: ExpenseSummary[];
  totalAmount: number;
  totalCount: number;
}
