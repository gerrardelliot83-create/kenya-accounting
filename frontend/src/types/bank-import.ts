export type FileType = 'csv' | 'pdf' | 'ofx' | 'other';
export type ImportStatus = 'pending' | 'mapping' | 'processing' | 'completed' | 'failed';
export type ReconciliationStatus = 'unmatched' | 'suggested' | 'matched' | 'ignored';
export type SourceBank = 'equity' | 'kcb' | 'cooperative' | 'mpesa' | 'other';
export type MatchType = 'expense' | 'invoice';

export interface ColumnMapping {
  sourceColumn: string;
  targetField: 'date' | 'description' | 'debit' | 'credit' | 'balance' | 'reference' | null;
}

export interface BankImport {
  id: string;
  businessId: string;
  fileName: string;
  fileType: FileType;
  sourceBank: SourceBank;
  status: ImportStatus;
  totalRows: number;
  processedRows: number;
  matchedRows: number;
  unmatchedRows: number;
  errorRows: number;
  columnMappings: ColumnMapping[];
  uploadedAt: string;
  processedAt?: string;
  createdAt: string;
  updatedAt: string;
}

export interface BankTransaction {
  id: string;
  bankImportId: string;
  transactionDate: string;
  description: string;
  debit?: number;
  credit?: number;
  balance?: number;
  reference?: string;
  reconciliationStatus: ReconciliationStatus;
  matchedExpenseId?: string;
  matchedInvoiceId?: string;
  matchConfidence?: number;
  createdAt: string;
  updatedAt: string;
}

export interface ReconciliationSuggestion {
  id: string;
  matchType: MatchType;
  matchId: string;
  confidence: number;
  reasons: string[];
  // Expense or Invoice details
  amount: number;
  date: string;
  description: string;
  category?: string;
  contactName?: string;
  invoiceNumber?: string;
}

export interface CreateBankImportRequest {
  file: File;
  sourceBank: SourceBank;
}

export interface UpdateColumnMappingRequest {
  columnMappings: ColumnMapping[];
}

export interface ProcessImportRequest {
  validate?: boolean;
}

export interface BankImportsListParams {
  page?: number;
  limit?: number;
  status?: ImportStatus;
  sourceBank?: SourceBank;
  startDate?: string;
  endDate?: string;
}

export interface BankImportsListResponse {
  imports: BankImport[];
  total: number;
  page: number;
  limit: number;
  totalPages: number;
}

export interface BankTransactionsListParams {
  page?: number;
  limit?: number;
  reconciliationStatus?: ReconciliationStatus;
  startDate?: string;
  endDate?: string;
}

export interface BankTransactionsListResponse {
  transactions: BankTransaction[];
  total: number;
  page: number;
  limit: number;
  totalPages: number;
}

export interface MatchTransactionRequest {
  matchType: MatchType;
  matchId: string;
}

export interface PreviewData {
  headers: string[];
  rows: Record<string, string>[];
}
