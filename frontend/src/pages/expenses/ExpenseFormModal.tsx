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
import { useCreateExpense, useUpdateExpense, useExpenseCategories } from '@/hooks/useExpenses';
import { Skeleton } from '@/components/ui/skeleton';
import type { Expense } from '@/types/expense';

const expenseFormSchema = z.object({
  category: z.string().min(1, 'Category is required'),
  description: z.string().min(1, 'Description is required'),
  amount: z.string().min(1, 'Amount is required').refine((val) => {
    const num = parseFloat(val);
    return !isNaN(num) && num > 0;
  }, 'Amount must be a positive number'),
  taxAmount: z.string().refine((val) => {
    if (!val) return true;
    const num = parseFloat(val);
    return !isNaN(num) && num >= 0;
  }, 'Tax amount must be a non-negative number').optional(),
  expenseDate: z.string().min(1, 'Expense date is required'),
  vendorName: z.string().optional(),
  paymentMethod: z.enum(['cash', 'bank_transfer', 'mpesa', 'card', 'other']),
  referenceNumber: z.string().optional(),
  receiptUrl: z.string().url('Must be a valid URL').optional().or(z.literal('')),
  notes: z.string().optional(),
});

type ExpenseFormValues = z.infer<typeof expenseFormSchema>;

interface ExpenseFormModalProps {
  open: boolean;
  onClose: () => void;
  expense?: Expense;
}

export const ExpenseFormModal = ({ open, onClose, expense }: ExpenseFormModalProps) => {
  const createExpense = useCreateExpense();
  const updateExpense = useUpdateExpense();
  const { data: categories, isLoading: categoriesLoading } = useExpenseCategories();

  const form = useForm<ExpenseFormValues>({
    resolver: zodResolver(expenseFormSchema),
    defaultValues: {
      category: '',
      description: '',
      amount: '',
      taxAmount: '0',
      expenseDate: new Date().toISOString().split('T')[0],
      vendorName: '',
      paymentMethod: 'cash',
      referenceNumber: '',
      receiptUrl: '',
      notes: '',
    },
  });

  useEffect(() => {
    if (expense) {
      form.reset({
        category: expense.category,
        description: expense.description,
        amount: expense.amount.toString(),
        taxAmount: expense.taxAmount.toString(),
        expenseDate: expense.expenseDate.split('T')[0],
        vendorName: expense.vendorName || '',
        paymentMethod: expense.paymentMethod,
        referenceNumber: expense.referenceNumber || '',
        receiptUrl: expense.receiptUrl || '',
        notes: expense.notes || '',
      });
    } else {
      form.reset({
        category: '',
        description: '',
        amount: '',
        taxAmount: '0',
        expenseDate: new Date().toISOString().split('T')[0],
        vendorName: '',
        paymentMethod: 'cash',
        referenceNumber: '',
        receiptUrl: '',
        notes: '',
      });
    }
  }, [expense, form]);

  const onSubmit = async (data: ExpenseFormValues) => {
    try {
      const payload = {
        category: data.category,
        description: data.description,
        amount: parseFloat(data.amount),
        taxAmount: data.taxAmount ? parseFloat(data.taxAmount) : 0,
        expenseDate: data.expenseDate,
        paymentMethod: data.paymentMethod,
        vendorName: data.vendorName || undefined,
        referenceNumber: data.referenceNumber || undefined,
        receiptUrl: data.receiptUrl || undefined,
        notes: data.notes || undefined,
      };

      if (expense) {
        await updateExpense.mutateAsync({ id: expense.id, data: payload });
      } else {
        await createExpense.mutateAsync(payload);
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
          <DialogTitle>{expense ? 'Edit Expense' : 'Create Expense'}</DialogTitle>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="category"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Category</FormLabel>
                  {categoriesLoading ? (
                    <Skeleton className="h-10 w-full" />
                  ) : (
                    <Select onValueChange={field.onChange} value={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select category" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {categories?.map((category) => (
                          <SelectItem key={category.id} value={category.name}>
                            {category.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  )}
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
                    <Input placeholder="Expense description" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <FormField
                control={form.control}
                name="amount"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Amount (KES)</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        step="0.01"
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
                name="taxAmount"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Tax Amount (KES)</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        step="0.01"
                        placeholder="0.00"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <FormField
                control={form.control}
                name="expenseDate"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Expense Date</FormLabel>
                    <FormControl>
                      <Input type="date" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="vendorName"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Vendor Name</FormLabel>
                    <FormControl>
                      <Input placeholder="Vendor name (optional)" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <FormField
                control={form.control}
                name="paymentMethod"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Payment Method</FormLabel>
                    <Select onValueChange={field.onChange} value={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select payment method" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="cash">Cash</SelectItem>
                        <SelectItem value="bank_transfer">Bank Transfer</SelectItem>
                        <SelectItem value="mpesa">M-Pesa</SelectItem>
                        <SelectItem value="card">Card</SelectItem>
                        <SelectItem value="other">Other</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="referenceNumber"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Reference Number</FormLabel>
                    <FormControl>
                      <Input placeholder="e.g., M-Pesa code (optional)" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <FormField
              control={form.control}
              name="receiptUrl"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Receipt URL</FormLabel>
                  <FormControl>
                    <Input
                      type="url"
                      placeholder="https://example.com/receipt.jpg (optional)"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="notes"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Notes</FormLabel>
                  <FormControl>
                    <Textarea placeholder="Additional notes (optional)" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="flex justify-end gap-3 pt-4">
              <Button type="button" variant="outline" onClick={handleClose}>
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={createExpense.isPending || updateExpense.isPending}
              >
                {createExpense.isPending || updateExpense.isPending
                  ? 'Saving...'
                  : expense
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
