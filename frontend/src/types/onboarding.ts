// Onboarding API Types - Aligned with Backend API

export type BusinessType = 'sole_proprietor' | 'partnership' | 'limited_company';
export type OnboardingStatus = 'draft' | 'submitted' | 'under_review' | 'approved' | 'rejected' | 'info_requested' | 'completed';

// Local/Mock types for onboarding service
export interface Business {
  id: string;
  name: string;
  businessType: BusinessType;
  kraPin: string;
  industry?: string;
  phone: string;
  email: string;
  address?: string;
  county: string;
  taxRegime?: string;
  vatNumber?: string;
  estimatedAnnualTurnover?: number;
  filingFrequency?: string;
  createdAt: string;
  createdBy: string;
}

export interface BusinessCreateData {
  businessInfo: {
    name: string;
    businessType: BusinessType;
    kraPin: string;
    industry?: string;
  };
  contactInfo: {
    phone: string;
    email: string;
    address?: string;
    county: string;
  };
  taxConfig: {
    taxRegime?: string;
    vatNumber?: string;
    estimatedAnnualTurnover?: number;
    filingFrequency?: string;
  };
  primaryUser: {
    fullName: string;
    email: string;
  };
}

export interface OnboardingItem {
  id: string;
  businessId: string;
  businessName: string;
  status: OnboardingStatus;
  agentId: string;
  agentName: string;
  createdAt: string;
  completedAt?: string;
  notes?: string;
}

export interface OnboardingQueueParams {
  status?: OnboardingStatus;
  startDate?: string;
  endDate?: string;
  offset?: number;
  limit?: number;
}

export interface OnboardingQueueResponse {
  items: OnboardingItem[];
  total: number;
  limit: number;
  offset: number;
}

// Application entity returned by API
export interface BusinessApplication {
  id: string;
  business_name: string;
  business_type: BusinessType;
  kra_pin: string;
  county: string;
  sub_county?: string;
  phone: string;
  email: string;
  owner_name: string;
  owner_national_id: string;
  owner_phone: string;
  owner_email: string;
  vat_registered: boolean;
  tot_registered: boolean;
  status: OnboardingStatus;
  submitted_at?: string;
  reviewed_by?: string;
  reviewed_at?: string;
  rejection_reason?: string;
  info_request_note?: string;
  created_by?: string;
  created_at: string;
  updated_at: string;
}

// Response when approving an application
export interface ApprovalResponse {
  message: string;
  business_id: string;
  user_id: string;
  temporary_password: string;
  login_email: string;
}

// Dashboard statistics
export interface OnboardingStats {
  total_applications: number;
  draft: number;
  submitted: number;
  under_review: number;
  approved: number;
  rejected: number;
  info_requested: number;
  approved_this_month: number;
  avg_processing_days: number;
  // Additional properties for mock service
  today?: number;
  thisWeek?: number;
  thisMonth?: number;
  total?: number;
}

// Request types for creating/updating applications
export interface CreateApplicationRequest {
  business_name: string;
  business_type: BusinessType;
  kra_pin: string;
  county: string;
  sub_county?: string;
  phone: string;
  email: string;
  owner_name: string;
  owner_national_id: string;
  owner_phone: string;
  owner_email: string;
  vat_registered?: boolean;
  tot_registered?: boolean;
}

export interface UpdateApplicationRequest {
  business_name?: string;
  business_type?: BusinessType;
  kra_pin?: string;
  county?: string;
  sub_county?: string;
  phone?: string;
  email?: string;
  owner_name?: string;
  owner_national_id?: string;
  owner_phone?: string;
  owner_email?: string;
  vat_registered?: boolean;
  tot_registered?: boolean;
}

// Query parameters for listing applications
export interface ApplicationsListParams {
  status?: OnboardingStatus;
  search?: string;
  page?: number;
  page_size?: number;
}

// Paginated response
export interface ApplicationsListResponse {
  items: BusinessApplication[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// Action request types
export interface RejectApplicationRequest {
  reason: string;
}

export interface RequestInfoRequest {
  note: string;
}
