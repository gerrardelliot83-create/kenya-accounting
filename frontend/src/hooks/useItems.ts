import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import type {
  ItemsListParams,
  CreateItemRequest,
  UpdateItemRequest,
} from '@/types/item';
import { useToast } from '@/hooks/use-toast';

const ITEMS_QUERY_KEY = 'items';

export const useItems = (params?: ItemsListParams) => {
  return useQuery({
    queryKey: [ITEMS_QUERY_KEY, params],
    queryFn: () => apiClient.getItems(params),
  });
};

export const useItem = (id: string) => {
  return useQuery({
    queryKey: [ITEMS_QUERY_KEY, id],
    queryFn: () => apiClient.getItem(id),
    enabled: !!id,
  });
};

export const useCreateItem = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (data: CreateItemRequest) => apiClient.createItem(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [ITEMS_QUERY_KEY] });
      toast({
        title: 'Success',
        description: 'Item created successfully',
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to create item',
        variant: 'destructive',
      });
    },
  });
};

export const useUpdateItem = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateItemRequest }) =>
      apiClient.updateItem(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [ITEMS_QUERY_KEY] });
      toast({
        title: 'Success',
        description: 'Item updated successfully',
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to update item',
        variant: 'destructive',
      });
    },
  });
};

export const useDeleteItem = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (id: string) => apiClient.deleteItem(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [ITEMS_QUERY_KEY] });
      toast({
        title: 'Success',
        description: 'Item deleted successfully',
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to delete item',
        variant: 'destructive',
      });
    },
  });
};
