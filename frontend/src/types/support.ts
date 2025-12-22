export type TicketCategory = 'billing' | 'technical' | 'feature_request' | 'general';
export type TicketPriority = 'low' | 'medium' | 'high' | 'urgent';
export type TicketStatus = 'open' | 'in_progress' | 'waiting_customer' | 'resolved' | 'closed';

export interface SupportTicket {
  id: string;
  ticket_number: string;
  subject: string;
  description: string;
  category: TicketCategory;
  priority: TicketPriority;
  status: TicketStatus;
  created_at: string;
  updated_at: string;
  resolved_at?: string;
  satisfaction_rating?: number;
}

export interface TicketMessage {
  id: string;
  ticket_id: string;
  sender_type: 'customer' | 'agent';
  sender_name: string;
  message: string;
  attachments?: Attachment[];
  created_at: string;
}

export interface Attachment {
  id: string;
  filename: string;
  url: string;
  size: number;
  content_type: string;
}

export interface CreateTicket {
  subject: string;
  description: string;
  category: TicketCategory;
}

export interface AddMessageRequest {
  message: string;
  attachments?: File[];
}

export interface RateTicketRequest {
  rating: number; // 1-5
  feedback?: string;
}

export interface TicketListParams {
  page?: number;
  limit?: number;
  status?: TicketStatus;
  category?: TicketCategory;
}

export interface TicketListResponse {
  tickets: SupportTicket[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export interface TicketDetailResponse {
  ticket: SupportTicket;
  messages: TicketMessage[];
}
