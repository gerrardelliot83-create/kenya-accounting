import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
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

// Admin Dashboard Stats
export const useAdminDashboard = () => {
  return useQuery<AdminDashboardStats>({
    queryKey: ['admin-dashboard-stats'],
    queryFn: () => apiClient.getAdminDashboardStats(),
  });
};

// Businesses Management
export const useBusinesses = (params?: BusinessListParams) => {
  return useQuery<BusinessListResponse>({
    queryKey: ['admin-businesses', params],
    queryFn: () => apiClient.getBusinesses(params),
  });
};

export const useBusiness = (id: string) => {
  return useQuery<BusinessDetailResponse>({
    queryKey: ['admin-business', id],
    queryFn: () => apiClient.getBusiness(id),
    enabled: !!id,
  });
};

// Internal Users Management
export const useInternalUsers = (params?: InternalUserListParams) => {
  return useQuery<InternalUserListResponse>({
    queryKey: ['admin-internal-users', params],
    queryFn: () => apiClient.getInternalUsers(params),
  });
};

export const useCreateInternalUser = () => {
  const queryClient = useQueryClient();

  return useMutation<InternalUser, Error, CreateInternalUserRequest>({
    mutationFn: (data: CreateInternalUserRequest) => apiClient.createInternalUser(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-internal-users'] });
    },
  });
};

export const useDeactivateInternalUser = () => {
  const queryClient = useQueryClient();

  return useMutation<InternalUser, Error, string>({
    mutationFn: (id: string) => apiClient.deactivateInternalUser(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-internal-users'] });
    },
  });
};

export const useActivateInternalUser = () => {
  const queryClient = useQueryClient();

  return useMutation<InternalUser, Error, string>({
    mutationFn: (id: string) => apiClient.activateInternalUser(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-internal-users'] });
    },
  });
};

// Audit Logs
export const useAuditLogs = (params?: AuditLogParams) => {
  return useQuery<AuditLogResponse>({
    queryKey: ['admin-audit-logs', params],
    queryFn: () => apiClient.getAuditLogs(params),
  });
};

// System Health
export const useSystemHealth = () => {
  return useQuery<SystemHealthMetrics>({
    queryKey: ['admin-system-health'],
    queryFn: () => apiClient.getSystemHealth(),
    refetchInterval: 30000, // Refetch every 30 seconds
  });
};
