import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';
import type {
  ApplicationsListParams,
  CreateApplicationRequest,
  UpdateApplicationRequest,
  RejectApplicationRequest,
  RequestInfoRequest,
  BusinessApplication,
  ApplicationsListResponse,
  ApprovalResponse,
  OnboardingStats,
} from '@/types/onboarding';

const APPLICATIONS_QUERY_KEY = 'applications';
const ONBOARDING_STATS_QUERY_KEY = 'onboarding-stats';

// List applications with filters
export const useApplications = (params?: ApplicationsListParams) => {
  return useQuery<ApplicationsListResponse>({
    queryKey: [APPLICATIONS_QUERY_KEY, params],
    queryFn: () => apiClient.getApplications(params),
  });
};

// Get single application
export const useApplication = (id: string) => {
  return useQuery<BusinessApplication>({
    queryKey: [APPLICATIONS_QUERY_KEY, id],
    queryFn: () => apiClient.getApplication(id),
    enabled: !!id,
  });
};

// Create application
export const useCreateApplication = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation<BusinessApplication, Error, CreateApplicationRequest>({
    mutationFn: (data: CreateApplicationRequest) => apiClient.createApplication(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [APPLICATIONS_QUERY_KEY] });
      queryClient.invalidateQueries({ queryKey: [ONBOARDING_STATS_QUERY_KEY] });
      toast({
        title: 'Success',
        description: 'Application created successfully',
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to create application',
        variant: 'destructive',
      });
    },
  });
};

// Update application
export const useUpdateApplication = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation<
    BusinessApplication,
    Error,
    { id: string; data: UpdateApplicationRequest }
  >({
    mutationFn: ({ id, data }) => apiClient.updateApplication(id, data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: [APPLICATIONS_QUERY_KEY] });
      queryClient.invalidateQueries({ queryKey: [APPLICATIONS_QUERY_KEY, data.id] });
      toast({
        title: 'Success',
        description: 'Application updated successfully',
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to update application',
        variant: 'destructive',
      });
    },
  });
};

// Submit application for review
export const useSubmitApplication = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation<BusinessApplication, Error, string>({
    mutationFn: (id: string) => apiClient.submitApplication(id),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: [APPLICATIONS_QUERY_KEY] });
      queryClient.invalidateQueries({ queryKey: [APPLICATIONS_QUERY_KEY, data.id] });
      queryClient.invalidateQueries({ queryKey: [ONBOARDING_STATS_QUERY_KEY] });
      toast({
        title: 'Success',
        description: 'Application submitted for review',
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to submit application',
        variant: 'destructive',
      });
    },
  });
};

// Approve application
export const useApproveApplication = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation<ApprovalResponse, Error, string>({
    mutationFn: (id: string) => apiClient.approveApplication(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [APPLICATIONS_QUERY_KEY] });
      queryClient.invalidateQueries({ queryKey: [ONBOARDING_STATS_QUERY_KEY] });
      toast({
        title: 'Success',
        description: 'Application approved successfully',
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to approve application',
        variant: 'destructive',
      });
    },
  });
};

// Reject application
export const useRejectApplication = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation<
    BusinessApplication,
    Error,
    { id: string; data: RejectApplicationRequest }
  >({
    mutationFn: ({ id, data }) => apiClient.rejectApplication(id, data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: [APPLICATIONS_QUERY_KEY] });
      queryClient.invalidateQueries({ queryKey: [APPLICATIONS_QUERY_KEY, data.id] });
      queryClient.invalidateQueries({ queryKey: [ONBOARDING_STATS_QUERY_KEY] });
      toast({
        title: 'Success',
        description: 'Application rejected',
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to reject application',
        variant: 'destructive',
      });
    },
  });
};

// Request more information
export const useRequestInfo = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation<BusinessApplication, Error, { id: string; data: RequestInfoRequest }>({
    mutationFn: ({ id, data }) => apiClient.requestInfo(id, data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: [APPLICATIONS_QUERY_KEY] });
      queryClient.invalidateQueries({ queryKey: [APPLICATIONS_QUERY_KEY, data.id] });
      queryClient.invalidateQueries({ queryKey: [ONBOARDING_STATS_QUERY_KEY] });
      toast({
        title: 'Success',
        description: 'Information request sent',
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to request information',
        variant: 'destructive',
      });
    },
  });
};

// Get onboarding statistics
export const useOnboardingStats = () => {
  return useQuery<OnboardingStats>({
    queryKey: [ONBOARDING_STATS_QUERY_KEY],
    queryFn: () => apiClient.getOnboardingStats(),
  });
};
