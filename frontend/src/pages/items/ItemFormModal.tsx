import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { useCreateItem, useUpdateItem } from '@/hooks/useItems';
import type { Item } from '@/types/item';

const itemFormSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  itemType: z.enum(['product', 'service']),
  description: z.string().optional(),
  sku: z.string().optional(),
  unitPrice: z.string().min(1, 'Unit price is required'),
  taxRate: z.string(),
});

type ItemFormValues = z.infer<typeof itemFormSchema>;

interface ItemFormModalProps {
  open: boolean;
  onClose: () => void;
  item?: Item;
}

export const ItemFormModal = ({ open, onClose, item }: ItemFormModalProps) => {
  const createItem = useCreateItem();
  const updateItem = useUpdateItem();

  const form = useForm<ItemFormValues>({
    resolver: zodResolver(itemFormSchema),
    defaultValues: {
      name: '',
      itemType: 'product',
      description: '',
      sku: '',
      unitPrice: '',
      taxRate: '16.0',
    },
  });

  useEffect(() => {
    if (item) {
      form.reset({
        name: item.name,
        itemType: item.itemType,
        description: item.description || '',
        sku: item.sku || '',
        unitPrice: item.unitPrice.toString(),
        taxRate: item.taxRate.toString(),
      });
    } else {
      form.reset({
        name: '',
        itemType: 'product',
        description: '',
        sku: '',
        unitPrice: '',
        taxRate: '16.0',
      });
    }
  }, [item, form]);

  const onSubmit = async (data: ItemFormValues) => {
    try {
      const payload = {
        name: data.name,
        itemType: data.itemType,
        description: data.description || undefined,
        sku: data.sku || undefined,
        unitPrice: parseFloat(data.unitPrice),
        taxRate: parseFloat(data.taxRate),
      };

      if (item) {
        await updateItem.mutateAsync({ id: item.id, data: payload });
      } else {
        await createItem.mutateAsync(payload);
      }
      onClose();
      form.reset();
    } catch (error) {
      // Error is handled by the mutation hooks
    }
  };

  const handleClose = () => {
    onClose();
    form.reset();
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{item ? 'Edit Item' : 'Create Item'}</DialogTitle>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Name</FormLabel>
                  <FormControl>
                    <Input placeholder="Item name" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="itemType"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Item Type</FormLabel>
                  <Select onValueChange={field.onChange} value={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Select item type" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="product">Product</SelectItem>
                      <SelectItem value="service">Service</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Description</FormLabel>
                  <FormControl>
                    <Textarea placeholder="Item description" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="sku"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>SKU</FormLabel>
                  <FormControl>
                    <Input placeholder="Stock keeping unit" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <FormField
                control={form.control}
                name="unitPrice"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Unit Price</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        step="0.01"
                        min="0"
                        placeholder="0.00"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="taxRate"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Tax Rate (%)</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        step="0.1"
                        min="0"
                        max="100"
                        placeholder="16.0"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <div className="flex justify-end gap-3 pt-4">
              <Button type="button" variant="outline" onClick={handleClose}>
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={createItem.isPending || updateItem.isPending}
              >
                {createItem.isPending || updateItem.isPending
                  ? 'Saving...'
                  : item
                  ? 'Update'
                  : 'Create'}
              </Button>
            </div>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
};
