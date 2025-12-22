import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import type {
  AdminTicket,
  AdminTicketDetail,
  SupportStats,
  CannedResponse,
  AgentMessage,
  UpdateTicketRequest,
  AssignTicketRequest,
  TicketFilters,
  TicketListResponse,
  SupportAgent,
} from '@/types/admin-support';
import { useAuth } from './useAuth';

// Query keys
const SUPPORT_KEYS = {
  all: ['admin-support'] as const,
  tickets: () => [...SUPPORT_KEYS.all, 'tickets'] as const,
  ticketsList: (filters?: TicketFilters) => [...SUPPORT_KEYS.tickets(), 'list', filters] as const,
  ticket: (id: string) => [...SUPPORT_KEYS.tickets(), 'detail', id] as const,
  stats: () => [...SUPPORT_KEYS.all, 'stats'] as const,
  templates: () => [...SUPPORT_KEYS.all, 'templates'] as const,
  template: (id: string) => [...SUPPORT_KEYS.templates(), id] as const,
  agents: () => [...SUPPORT_KEYS.all, 'agents'] as const,
};

// Extend ApiClient with admin support methods
declare module '@/lib/api' {
  interface ApiClient {
    getAdminTickets(filters?: TicketFilters): Promise<TicketListResponse>;
    getAdminTicket(id: string): Promise<AdminTicketDetail>;
    updateTicket(id: string, data: UpdateTicketRequest): Promise<AdminTicket>;
    assignTicket(id: string, data: AssignTicketRequest): Promise<AdminTicket>;
    addAgentMessage(id: string, data: AgentMessage): Promise<AdminTicketDetail>;
    getSupportStats(): Promise<SupportStats>;
    getCannedResponses(): Promise<CannedResponse[]>;
    getCannedResponse(id: string): Promise<CannedResponse>;
    getSupportAgents(): Promise<SupportAgent[]>;
  }
}

// Admin support API methods using the apiClient's internal axios instance
const adminSupportApi = {
  async getAdminTickets(filters?: TicketFilters): Promise<TicketListResponse> {
    const client = (apiClient as any).client;
    const response = await client.get('/admin/support/tickets', { params: filters });
    return response.data as TicketListResponse;
  },

  async getAdminTicket(id: string): Promise<AdminTicketDetail> {
    const client = (apiClient as any).client;
    const response = await client.get(`/admin/support/tickets/${id}`);
    return response.data as AdminTicketDetail;
  },

  async updateTicket(id: string, data: UpdateTicketRequest): Promise<AdminTicket> {
    const client = (apiClient as any).client;
    const response = await client.put(`/admin/support/tickets/${id}`, data);
    return response.data as AdminTicket;
  },

  async assignTicket(id: string, data: AssignTicketRequest): Promise<AdminTicket> {
    const client = (apiClient as any).client;
    const response = await client.post(`/admin/support/tickets/${id}/assign`, data);
    return response.data as AdminTicket;
  },

  async addAgentMessage(id: string, data: AgentMessage): Promise<AdminTicketDetail> {
    const client = (apiClient as any).client;
    const response = await client.post(`/admin/support/tickets/${id}/messages`, data);
    return response.data as AdminTicketDetail;
  },

  async getSupportStats(): Promise<SupportStats> {
    const client = (apiClient as any).client;
    const response = await client.get('/admin/support/stats');
    return response.data as SupportStats;
  },

  async getCannedResponses(): Promise<CannedResponse[]> {
    const client = (apiClient as any).client;
    const response = await client.get('/admin/support/templates');
    return response.data as CannedResponse[];
  },

  async getCannedResponse(id: string): Promise<CannedResponse> {
    const client = (apiClient as any).client;
    const response = await client.get(`/admin/support/templates/${id}`);
    return response.data as CannedResponse;
  },

  async getSupportAgents(): Promise<SupportAgent[]> {
    const client = (apiClient as any).client;
    const response = await client.get('/admin/support/agents');
    return response.data as SupportAgent[];
  },
};

// Hook: Get all tickets with filters
export const useAdminTickets = (filters?: TicketFilters) => {
  return useQuery({
    queryKey: SUPPORT_KEYS.ticketsList(filters),
    queryFn: () => adminSupportApi.getAdminTickets(filters),
    staleTime: 30000, // 30 seconds
  });
};

// Hook: Get single ticket with full details
export const useAdminTicket = (id: string) => {
  return useQuery({
    queryKey: SUPPORT_KEYS.ticket(id),
    queryFn: () => adminSupportApi.getAdminTicket(id),
    enabled: !!id,
  });
};

// Hook: Update ticket (status, priority, assignment)
export const useUpdateTicket = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateTicketRequest }) =>
      adminSupportApi.updateTicket(id, data),
    onSuccess: (updatedTicket) => {
      // Invalidate tickets list
      queryClient.invalidateQueries({ queryKey: SUPPORT_KEYS.tickets() });
      // Update single ticket cache
      queryClient.setQueryData(SUPPORT_KEYS.ticket(updatedTicket.id), updatedTicket);
      // Invalidate stats
      queryClient.invalidateQueries({ queryKey: SUPPORT_KEYS.stats() });
    },
  });
};

// Hook: Assign ticket to agent
export const useAssignTicket = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: AssignTicketRequest }) =>
      adminSupportApi.assignTicket(id, data),
    onSuccess: (updatedTicket) => {
      // Invalidate tickets list
      queryClient.invalidateQueries({ queryKey: SUPPORT_KEYS.tickets() });
      // Update single ticket cache
      queryClient.setQueryData(SUPPORT_KEYS.ticket(updatedTicket.id), updatedTicket);
      // Invalidate stats
      queryClient.invalidateQueries({ queryKey: SUPPORT_KEYS.stats() });
    },
  });
};

// Hook: Add agent message or internal note
export const useAddAgentMessage = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: AgentMessage }) =>
      adminSupportApi.addAgentMessage(id, data),
    onSuccess: (updatedTicket) => {
      // Update single ticket cache with new message
      queryClient.setQueryData(SUPPORT_KEYS.ticket(updatedTicket.id), updatedTicket);
      // Invalidate tickets list to update message counts
      queryClient.invalidateQueries({ queryKey: SUPPORT_KEYS.tickets() });
    },
  });
};

// Hook: Get support dashboard statistics
export const useSupportStats = () => {
  return useQuery({
    queryKey: SUPPORT_KEYS.stats(),
    queryFn: () => adminSupportApi.getSupportStats(),
    staleTime: 60000, // 1 minute
  });
};

// Hook: Get all canned responses/templates
export const useCannedResponses = () => {
  return useQuery({
    queryKey: SUPPORT_KEYS.templates(),
    queryFn: () => adminSupportApi.getCannedResponses(),
    staleTime: 300000, // 5 minutes - templates don't change often
  });
};

// Hook: Get single canned response
export const useCannedResponse = (id: string) => {
  return useQuery({
    queryKey: SUPPORT_KEYS.template(id),
    queryFn: () => adminSupportApi.getCannedResponse(id),
    enabled: !!id,
  });
};

// Hook: Get available support agents
export const useSupportAgents = () => {
  return useQuery({
    queryKey: SUPPORT_KEYS.agents(),
    queryFn: () => adminSupportApi.getSupportAgents(),
    staleTime: 300000, // 5 minutes
  });
};

// Hook: Assign ticket to current user
export const useAssignToMe = () => {
  const { user } = useAuth();
  const assignTicket = useAssignTicket();

  return {
    ...assignTicket,
    assignToMe: (ticketId: string) => {
      if (!user?.id) {
        throw new Error('User not authenticated');
      }
      return assignTicket.mutate({
        id: ticketId,
        data: { agent_id: user.id },
      });
    },
  };
};
