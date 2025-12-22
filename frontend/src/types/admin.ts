export interface BusinessListItem {
  id: string;
  business_name: string;
  business_type: string;
  status: string;
  created_at: string;
  user_count: number;
  invoice_count: number;
  total_revenue: number;
}

export interface InternalUser {
  id: string;
  full_name: string;
  email_masked: string;
  role: 'system_admin' | 'support_agent' | 'onboarding_agent';
  is_active: boolean;
  created_at: string;
  last_login?: string;
}

export interface AuditLogEntry {
  id: string;
  user_id?: string;
  user_name?: string;
  action: string;
  resource_type?: string;
  resource_id?: string;
  status: 'success' | 'failure' | 'error';
  ip_address?: string;
  created_at: string;
  details?: Record<string, any>;
}

export interface AdminDashboardStats {
  total_businesses: number;
  active_businesses: number;
  total_users: number;
  active_users: number;
  total_invoices: number;
  total_revenue: number;
  pending_applications: number;
  open_tickets: number;
}

export interface BusinessDetailResponse {
  id: string;
  business_name: string;
  business_type: string;
  status: string;
  created_at: string;
  updated_at: string;
  business_admin_name?: string;
  business_admin_email_masked?: string;
  user_count: number;
  invoice_count: number;
  expense_count: number;
  total_revenue: number;
  total_expenses: number;
  users: Array<{
    id: string;
    full_name: string;
    email_masked: string;
    role: string;
    is_active: boolean;
    last_login?: string;
  }>;
}

export interface BusinessListParams {
  page?: number;
  limit?: number;
  search?: string;
  status?: string;
  business_type?: string;
}

export interface BusinessListResponse {
  businesses: BusinessListItem[];
  total: number;
  page: number;
  totalPages: number;
}

export interface InternalUserListParams {
  page?: number;
  limit?: number;
  role?: string;
  is_active?: boolean;
}

export interface InternalUserListResponse {
  users: InternalUser[];
  total: number;
  page: number;
  totalPages: number;
}

export interface CreateInternalUserRequest {
  full_name: string;
  email: string;
  role: 'system_admin' | 'support_agent' | 'onboarding_agent';
  temporary_password: string;
}

export interface AuditLogParams {
  page?: number;
  limit?: number;
  user_id?: string;
  action?: string;
  resource_type?: string;
  status?: 'success' | 'failure' | 'error';
  start_date?: string;
  end_date?: string;
}

export interface AuditLogResponse {
  logs: AuditLogEntry[];
  total: number;
  page: number;
  totalPages: number;
}

export interface SystemHealthMetrics {
  api_response_time_ms: number;
  error_rate_percent: number;
  active_sessions: number;
  database_status: 'healthy' | 'degraded' | 'down';
  last_updated: string;
}
