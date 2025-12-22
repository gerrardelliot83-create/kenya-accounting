import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useForm, useFieldArray } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { ArrowLeft, Plus, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { useContacts } from '@/hooks/useContacts';
import { useItems } from '@/hooks/useItems';
import { useCreateInvoice, useUpdateInvoice, useInvoice, useIssueInvoice } from '@/hooks/useInvoices';
import { formatCurrency } from '@/lib/formatters';

const lineItemSchema = z.object({
  itemId: z.string().optional(),
  description: z.string().min(1, 'Description is required'),
  quantity: z.string().min(1, 'Quantity is required'),
  unitPrice: z.string().min(1, 'Unit price is required'),
  taxRate: z.string().min(1, 'Tax rate is required'),
});

const invoiceFormSchema = z.object({
  contactId: z.string().min(1, 'Customer is required'),
  issueDate: z.string().min(1, 'Issue date is required'),
  dueDate: z.string().min(1, 'Due date is required'),
  notes: z.string().optional(),
  lineItems: z.array(lineItemSchema).min(1, 'At least one line item is required'),
});

type InvoiceFormValues = z.infer<typeof invoiceFormSchema>;

export const InvoiceFormPage = () => {
  const navigate = useNavigate();
  const { id } = useParams();
  const isEditMode = !!id;

  const [selectedItemIds, setSelectedItemIds] = useState<Record<number, string>>({});

  const { data: contactsData } = useContacts({ limit: 100 });
  const { data: itemsData } = useItems({ limit: 100 });
  const { data: invoice } = useInvoice(id || '');

  const createInvoice = useCreateInvoice();
  const updateInvoice = useUpdateInvoice();
  const issueInvoice = useIssueInvoice();

  const form = useForm<InvoiceFormValues>({
    resolver: zodResolver(invoiceFormSchema),
    defaultValues: {
      contactId: '',
      issueDate: new Date().toISOString().split('T')[0],
      dueDate: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      notes: '',
      lineItems: [
        {
          itemId: '',
          description: '',
          quantity: '1',
          unitPrice: '0',
          taxRate: '16.0',
        },
      ],
    },
  });

  const { fields, append, remove } = useFieldArray({
    control: form.control,
    name: 'lineItems',
  });

  useEffect(() => {
    if (invoice && isEditMode) {
      form.reset({
        contactId: invoice.contactId,
        issueDate: invoice.issueDate.split('T')[0],
        dueDate: invoice.dueDate.split('T')[0],
        notes: invoice.notes || '',
        lineItems: invoice.lineItems?.map((item) => ({
          itemId: item.itemId || '',
          description: item.description,
          quantity: item.quantity.toString(),
          unitPrice: item.unitPrice.toString(),
          taxRate: item.taxRate.toString(),
        })) || [],
      });
    }
  }, [invoice, isEditMode, form]);

  const handleItemSelect = (index: number, itemId: string) => {
    const item = itemsData?.items.find((i) => i.id === itemId);
    if (item) {
      form.setValue(`lineItems.${index}.description`, item.name);
      form.setValue(`lineItems.${index}.unitPrice`, item.unitPrice.toString());
      form.setValue(`lineItems.${index}.taxRate`, item.taxRate.toString());
      setSelectedItemIds({ ...selectedItemIds, [index]: itemId });
    }
  };

  const calculateLineTotal = (quantity: string, unitPrice: string, taxRate: string) => {
    const qty = parseFloat(quantity) || 0;
    const price = parseFloat(unitPrice) || 0;
    const tax = parseFloat(taxRate) || 0;
    const subtotal = qty * price;
    const taxAmount = subtotal * (tax / 100);
    return subtotal + taxAmount;
  };

  const calculateTotals = () => {
    const lineItems = form.watch('lineItems');
    let subtotal = 0;
    let taxAmount = 0;

    lineItems.forEach((item) => {
      const qty = parseFloat(item.quantity) || 0;
      const price = parseFloat(item.unitPrice) || 0;
      const tax = parseFloat(item.taxRate) || 0;
      const itemSubtotal = qty * price;
      const itemTax = itemSubtotal * (tax / 100);
      subtotal += itemSubtotal;
      taxAmount += itemTax;
    });

    return { subtotal, taxAmount, total: subtotal + taxAmount };
  };

  const totals = calculateTotals();

  const onSubmit = async (data: InvoiceFormValues, shouldIssue: boolean = false) => {
    try {
      const payload = {
        contactId: data.contactId,
        issueDate: new Date(data.issueDate).toISOString(),
        dueDate: new Date(data.dueDate).toISOString(),
        notes: data.notes || undefined,
        lineItems: data.lineItems.map((item) => ({
          itemId: item.itemId || undefined,
          description: item.description,
          quantity: parseFloat(item.quantity),
          unitPrice: parseFloat(item.unitPrice),
          taxRate: parseFloat(item.taxRate),
        })),
      };

      let invoiceId = id;

      if (isEditMode && id) {
        await updateInvoice.mutateAsync({ id, data: payload });
      } else {
        const newInvoice = await createInvoice.mutateAsync(payload);
        invoiceId = newInvoice.id;
      }

      if (shouldIssue && invoiceId) {
        await issueInvoice.mutateAsync(invoiceId);
      }

      navigate('/invoices');
    } catch (error) {
      // Error is handled by the mutation hooks
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate('/invoices')} aria-label="Back to invoices">
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div>
          <h1 className="text-3xl font-semibold">
            {isEditMode ? 'Edit Invoice' : 'New Invoice'}
          </h1>
          <p className="mt-2 text-muted-foreground">
            {isEditMode ? 'Update invoice details' : 'Create a new invoice'}
          </p>
        </div>
      </div>

      <Form {...form}>
        <form className="space-y-6">
          <div className="grid grid-cols-1 gap-6 rounded-lg border p-6 md:grid-cols-2">
            <FormField
              control={form.control}
              name="contactId"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Customer</FormLabel>
                  <Select onValueChange={field.onChange} value={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Select customer" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {contactsData?.contacts
                        .filter((c) => c.id && (c.contactType === 'customer' || c.contactType === 'both'))
                        .map((contact) => (
                          <SelectItem key={contact.id} value={contact.id}>
                            {contact.name}
                          </SelectItem>
                        ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="issueDate"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Issue Date</FormLabel>
                    <FormControl>
                      <Input type="date" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="dueDate"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Due Date</FormLabel>
                    <FormControl>
                      <Input type="date" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
          </div>

          <div className="rounded-lg border">
            <div className="border-b p-4">
              <h2 className="text-lg font-semibold">Line Items</h2>
            </div>

            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[200px]">Item (Optional)</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead className="w-[100px]">Quantity</TableHead>
                    <TableHead className="w-[120px]">Unit Price</TableHead>
                    <TableHead className="w-[100px]">Tax Rate %</TableHead>
                    <TableHead className="w-[120px]">Total</TableHead>
                    <TableHead className="w-[70px]"></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {fields.map((field, index) => {
                    const quantity = form.watch(`lineItems.${index}.quantity`);
                    const unitPrice = form.watch(`lineItems.${index}.unitPrice`);
                    const taxRate = form.watch(`lineItems.${index}.taxRate`);
                    const lineTotal = calculateLineTotal(quantity, unitPrice, taxRate);

                    return (
                      <TableRow key={field.id}>
                        <TableCell>
                          <Select
                            value={selectedItemIds[index] || '_none'}
                            onValueChange={(value) => {
                              if (value === '_none') {
                                setSelectedItemIds({ ...selectedItemIds, [index]: '' });
                                form.setValue(`lineItems.${index}.itemId`, '');
                              } else {
                                handleItemSelect(index, value);
                                form.setValue(`lineItems.${index}.itemId`, value);
                              }
                            }}
                          >
                            <SelectTrigger>
                              <SelectValue placeholder="Select item" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="_none">None</SelectItem>
                              {itemsData?.items
                                .filter((item) => item.id)
                                .map((item) => (
                                  <SelectItem key={item.id} value={item.id}>
                                    {item.name}
                                  </SelectItem>
                                ))}
                            </SelectContent>
                          </Select>
                        </TableCell>
                        <TableCell>
                          <FormField
                            control={form.control}
                            name={`lineItems.${index}.description`}
                            render={({ field }) => (
                              <FormItem>
                                <FormControl>
                                  <Input placeholder="Description" {...field} />
                                </FormControl>
                              </FormItem>
                            )}
                          />
                        </TableCell>
                        <TableCell>
                          <FormField
                            control={form.control}
                            name={`lineItems.${index}.quantity`}
                            render={({ field }) => (
                              <FormItem>
                                <FormControl>
                                  <Input type="number" step="0.01" min="0" {...field} />
                                </FormControl>
                              </FormItem>
                            )}
                          />
                        </TableCell>
                        <TableCell>
                          <FormField
                            control={form.control}
                            name={`lineItems.${index}.unitPrice`}
                            render={({ field }) => (
                              <FormItem>
                                <FormControl>
                                  <Input type="number" step="0.01" min="0" {...field} />
                                </FormControl>
                              </FormItem>
                            )}
                          />
                        </TableCell>
                        <TableCell>
                          <FormField
                            control={form.control}
                            name={`lineItems.${index}.taxRate`}
                            render={({ field }) => (
                              <FormItem>
                                <FormControl>
                                  <Input type="number" step="0.1" min="0" {...field} />
                                </FormControl>
                              </FormItem>
                            )}
                          />
                        </TableCell>
                        <TableCell className="text-right font-medium">
                          {formatCurrency(lineTotal)}
                        </TableCell>
                        <TableCell>
                          <Button
                            type="button"
                            variant="ghost"
                            size="icon"
                            onClick={() => remove(index)}
                            disabled={fields.length === 1}
                            aria-label="Remove line item"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>

            <div className="border-t p-4">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() =>
                  append({
                    itemId: '',
                    description: '',
                    quantity: '1',
                    unitPrice: '0',
                    taxRate: '16.0',
                  })
                }
              >
                <Plus className="mr-2 h-4 w-4" />
                Add Line Item
              </Button>
            </div>
          </div>

          <div className="flex justify-end">
            <div className="w-full max-w-sm space-y-2 rounded-lg border p-4">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Subtotal:</span>
                <span>{formatCurrency(totals.subtotal)}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Tax:</span>
                <span>{formatCurrency(totals.taxAmount)}</span>
              </div>
              <div className="flex justify-between border-t pt-2 text-lg font-semibold">
                <span>Total:</span>
                <span>{formatCurrency(totals.total)}</span>
              </div>
            </div>
          </div>

          <FormField
            control={form.control}
            name="notes"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Notes</FormLabel>
                <FormControl>
                  <Textarea
                    placeholder="Additional notes or payment terms"
                    className="min-h-[100px]"
                    {...field}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <div className="flex justify-end gap-3">
            <Button type="button" variant="outline" onClick={() => navigate('/invoices')}>
              Cancel
            </Button>
            <Button
              type="button"
              variant="secondary"
              onClick={form.handleSubmit((data) => onSubmit(data, false))}
              disabled={createInvoice.isPending || updateInvoice.isPending}
            >
              {createInvoice.isPending || updateInvoice.isPending
                ? 'Saving...'
                : 'Save as Draft'}
            </Button>
            <Button
              type="button"
              onClick={form.handleSubmit((data) => onSubmit(data, true))}
              disabled={createInvoice.isPending || updateInvoice.isPending || issueInvoice.isPending}
            >
              {createInvoice.isPending || updateInvoice.isPending || issueInvoice.isPending
                ? 'Processing...'
                : 'Save and Issue'}
            </Button>
          </div>
        </form>
      </Form>
    </div>
  );
};
