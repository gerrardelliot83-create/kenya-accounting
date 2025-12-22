import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import type {
  ContactsListParams,
  CreateContactRequest,
  UpdateContactRequest,
} from '@/types/contact';
import { useToast } from '@/hooks/use-toast';

const CONTACTS_QUERY_KEY = 'contacts';

export const useContacts = (params?: ContactsListParams) => {
  return useQuery({
    queryKey: [CONTACTS_QUERY_KEY, params],
    queryFn: () => apiClient.getContacts(params),
  });
};

export const useContact = (id: string) => {
  return useQuery({
    queryKey: [CONTACTS_QUERY_KEY, id],
    queryFn: () => apiClient.getContact(id),
    enabled: !!id,
  });
};

export const useCreateContact = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (data: CreateContactRequest) => apiClient.createContact(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [CONTACTS_QUERY_KEY] });
      toast({
        title: 'Success',
        description: 'Contact created successfully',
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to create contact',
        variant: 'destructive',
      });
    },
  });
};

export const useUpdateContact = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateContactRequest }) =>
      apiClient.updateContact(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [CONTACTS_QUERY_KEY] });
      toast({
        title: 'Success',
        description: 'Contact updated successfully',
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to update contact',
        variant: 'destructive',
      });
    },
  });
};

export const useDeleteContact = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (id: string) => apiClient.deleteContact(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [CONTACTS_QUERY_KEY] });
      toast({
        title: 'Success',
        description: 'Contact deleted successfully',
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to delete contact',
        variant: 'destructive',
      });
    },
  });
};
