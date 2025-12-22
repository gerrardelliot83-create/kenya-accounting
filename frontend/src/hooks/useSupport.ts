import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import type {
  SupportTicket,
  TicketMessage,
  CreateTicket,
  AddMessageRequest,
  RateTicketRequest,
  TicketListParams,
  TicketListResponse,
  TicketDetailResponse,
} from '@/types/support';

// List my tickets with pagination and filters
export const useMyTickets = (params?: TicketListParams) => {
  return useQuery<TicketListResponse>({
    queryKey: ['my-tickets', params],
    queryFn: () => apiClient.getMyTickets(params),
  });
};

// Get single ticket with messages
export const useTicket = (id: string) => {
  return useQuery<TicketDetailResponse>({
    queryKey: ['ticket', id],
    queryFn: () => apiClient.getTicket(id),
    enabled: !!id,
  });
};

// Create a new ticket
export const useCreateTicket = () => {
  const queryClient = useQueryClient();

  return useMutation<SupportTicket, Error, CreateTicket>({
    mutationFn: (data: CreateTicket) => apiClient.createTicket(data),
    onSuccess: () => {
      // Invalidate tickets list to refetch
      queryClient.invalidateQueries({ queryKey: ['my-tickets'] });
    },
  });
};

// Add a message to a ticket
export const useAddMessage = (ticketId: string) => {
  const queryClient = useQueryClient();

  return useMutation<TicketMessage, Error, AddMessageRequest>({
    mutationFn: (data: AddMessageRequest) => apiClient.addTicketMessage(ticketId, data),
    onSuccess: () => {
      // Invalidate the ticket detail to refetch messages
      queryClient.invalidateQueries({ queryKey: ['ticket', ticketId] });
      queryClient.invalidateQueries({ queryKey: ['my-tickets'] });
    },
  });
};

// Rate a resolved ticket
export const useRateTicket = (ticketId: string) => {
  const queryClient = useQueryClient();

  return useMutation<SupportTicket, Error, RateTicketRequest>({
    mutationFn: (data: RateTicketRequest) => apiClient.rateTicket(ticketId, data),
    onSuccess: () => {
      // Invalidate the ticket detail to show updated rating
      queryClient.invalidateQueries({ queryKey: ['ticket', ticketId] });
      queryClient.invalidateQueries({ queryKey: ['my-tickets'] });
    },
  });
};
