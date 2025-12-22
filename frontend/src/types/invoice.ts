export type InvoiceStatus = 'draft' | 'issued' | 'paid' | 'cancelled';

export interface InvoiceLineItem {
  id: string;
  invoiceId: string;
  itemId?: string;
  description: string;
  quantity: number;
  unitPrice: number;
  taxRate: number;
  lineTotal: number;
  taxAmount: number;
  createdAt: string;
  updatedAt: string;
}

export interface Invoice {
  id: string;
  businessId: string;
  contactId: string;
  invoiceNumber: string;
  issueDate: string;
  dueDate: string;
  subtotal: number;
  taxAmount: number;
  total: number;
  status: InvoiceStatus;
  notes?: string;
  createdAt: string;
  updatedAt: string;
  deletedAt?: string;
  issuedAt?: string;
  cancelledAt?: string;
  lineItems?: InvoiceLineItem[];
  contact?: {
    id: string;
    name: string;
    email?: string;
    phone?: string;
  };
}

export interface CreateInvoiceLineItemRequest {
  itemId?: string;
  description: string;
  quantity: number;
  unitPrice: number;
  taxRate: number;
}

export interface CreateInvoiceRequest {
  contactId: string;
  issueDate: string;
  dueDate: string;
  notes?: string;
  lineItems: CreateInvoiceLineItemRequest[];
}

export interface UpdateInvoiceRequest {
  contactId?: string;
  issueDate?: string;
  dueDate?: string;
  notes?: string;
  lineItems?: CreateInvoiceLineItemRequest[];
}

export interface InvoicesListParams {
  page?: number;
  limit?: number;
  status?: InvoiceStatus;
  contactId?: string;
  startDate?: string;
  endDate?: string;
}

export interface InvoicesListResponse {
  invoices: Invoice[];
  total: number;
  page: number;
  limit: number;
  totalPages: number;
}
