export type TicketCategory =
  | 'payment_issue'
  | 'technical_support'
  | 'account_access'
  | 'billing_question'
  | 'feature_request'
  | 'bug_report'
  | 'general_inquiry';

export type TicketPriority = 'urgent' | 'high' | 'medium' | 'low';

export type TicketStatus =
  | 'open'
  | 'in_progress'
  | 'waiting_customer'
  | 'resolved'
  | 'closed';

export interface MaskedBusinessInfo {
  business_name: string;
  business_type: string;
  // NO sensitive data (kra_pin, bank_account, etc.) - intentionally masked
}

export interface AdminTicket {
  id: string;
  ticket_number: string;
  subject: string;
  description: string;
  category: TicketCategory;
  priority: TicketPriority;
  status: TicketStatus;
  business_info: MaskedBusinessInfo;
  customer_name: string;
  customer_email: string;
  assigned_agent_id?: string;
  assigned_agent_name?: string;
  message_count: number;
  created_at: string;
  updated_at: string;
  resolved_at?: string;
}

export interface TicketMessage {
  id: string;
  ticket_id: string;
  sender_type: 'customer' | 'agent';
  sender_name: string;
  message: string;
  is_internal: boolean;
  created_at: string;
}

export interface AdminTicketDetail extends AdminTicket {
  messages: TicketMessage[];
}

export interface SupportStats {
  total_open: number;
  total_in_progress: number;
  total_waiting_customer: number;
  resolved_today: number;
  avg_resolution_time_hours: number;
  unassigned_count: number;
  high_priority_count: number;
}

export interface CannedResponse {
  id: string;
  title: string;
  content: string;
  category: string;
  created_at: string;
  updated_at: string;
}

export interface AgentMessage {
  message: string;
  is_internal: boolean;
}

export interface UpdateTicketRequest {
  status?: TicketStatus;
  priority?: TicketPriority;
  assigned_agent_id?: string;
}

export interface AssignTicketRequest {
  agent_id: string;
}

export interface TicketFilters {
  status?: TicketStatus | 'all';
  priority?: TicketPriority | 'all';
  category?: TicketCategory | 'all';
  assigned?: 'all' | 'unassigned' | 'assigned_to_me';
  search?: string;
  page?: number;
  limit?: number;
}

export interface TicketListResponse {
  tickets: AdminTicket[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export interface SupportAgent {
  id: string;
  name: string;
  email: string;
  active_tickets_count: number;
}
