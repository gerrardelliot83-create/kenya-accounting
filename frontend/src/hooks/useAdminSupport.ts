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

// Add methods to apiClient prototype
Object.assign(apiClient, {
  async getAdminTickets(filters?: TicketFilters): Promise<TicketListResponse> {
    const response = await (apiClient as any).client.get<TicketListResponse>(
      '/admin/support/tickets',
      { params: filters }
    );
    return response.data;
  },

  async getAdminTicket(id: string): Promise<AdminTicketDetail> {
    const response = await (apiClient as any).client.get<AdminTicketDetail>(
      `/admin/support/tickets/${id}`
    );
    return response.data;
  },

  async updateTicket(id: string, data: UpdateTicketRequest): Promise<AdminTicket> {
    const response = await (apiClient as any).client.put<AdminTicket>(
      `/admin/support/tickets/${id}`,
      data
    );
    return response.data;
  },

  async assignTicket(id: string, data: AssignTicketRequest): Promise<AdminTicket> {
    const response = await (apiClient as any).client.post<AdminTicket>(
      `/admin/support/tickets/${id}/assign`,
      data
    );
    return response.data;
  },

  async addAgentMessage(id: string, data: AgentMessage): Promise<AdminTicketDetail> {
    const response = await (apiClient as any).client.post<AdminTicketDetail>(
      `/admin/support/tickets/${id}/messages`,
      data
    );
    return response.data;
  },

  async getSupportStats(): Promise<SupportStats> {
    const response = await (apiClient as any).client.get<SupportStats>('/admin/support/stats');
    return response.data;
  },

  async getCannedResponses(): Promise<CannedResponse[]> {
    const response = await (apiClient as any).client.get<CannedResponse[]>(
      '/admin/support/templates'
    );
    return response.data;
  },

  async getCannedResponse(id: string): Promise<CannedResponse> {
    const response = await (apiClient as any).client.get<CannedResponse>(
      `/admin/support/templates/${id}`
    );
    return response.data;
  },

  async getSupportAgents(): Promise<SupportAgent[]> {
    const response = await (apiClient as any).client.get<SupportAgent[]>('/admin/support/agents');
    return response.data;
  },
});

// Hook: Get all tickets with filters
export const useAdminTickets = (filters?: TicketFilters) => {
  return useQuery({
    queryKey: SUPPORT_KEYS.ticketsList(filters),
    queryFn: () => apiClient.getAdminTickets(filters),
    staleTime: 30000, // 30 seconds
  });
};

// Hook: Get single ticket with full details
export const useAdminTicket = (id: string) => {
  return useQuery({
    queryKey: SUPPORT_KEYS.ticket(id),
    queryFn: () => apiClient.getAdminTicket(id),
    enabled: !!id,
  });
};

// Hook: Update ticket (status, priority, assignment)
export const useUpdateTicket = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateTicketRequest }) =>
      apiClient.updateTicket(id, data),
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
      apiClient.assignTicket(id, data),
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
      apiClient.addAgentMessage(id, data),
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
    queryFn: () => apiClient.getSupportStats(),
    staleTime: 60000, // 1 minute
  });
};

// Hook: Get all canned responses/templates
export const useCannedResponses = () => {
  return useQuery({
    queryKey: SUPPORT_KEYS.templates(),
    queryFn: () => apiClient.getCannedResponses(),
    staleTime: 300000, // 5 minutes - templates don't change often
  });
};

// Hook: Get single canned response
export const useCannedResponse = (id: string) => {
  return useQuery({
    queryKey: SUPPORT_KEYS.template(id),
    queryFn: () => apiClient.getCannedResponse(id),
    enabled: !!id,
  });
};

// Hook: Get available support agents
export const useSupportAgents = () => {
  return useQuery({
    queryKey: SUPPORT_KEYS.agents(),
    queryFn: () => apiClient.getSupportAgents(),
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
