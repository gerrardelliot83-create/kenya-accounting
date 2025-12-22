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
import { useCreateContact, useUpdateContact } from '@/hooks/useContacts';
import type { Contact } from '@/types/contact';

const contactFormSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  contactType: z.enum(['customer', 'supplier', 'both']),
  email: z.string().email('Invalid email').optional().or(z.literal('')),
  phone: z.string().optional(),
  kraPin: z.string().optional(),
  address: z.string().optional(),
  notes: z.string().optional(),
});

type ContactFormValues = z.infer<typeof contactFormSchema>;

interface ContactFormModalProps {
  open: boolean;
  onClose: () => void;
  contact?: Contact;
}

export const ContactFormModal = ({ open, onClose, contact }: ContactFormModalProps) => {
  const createContact = useCreateContact();
  const updateContact = useUpdateContact();

  const form = useForm<ContactFormValues>({
    resolver: zodResolver(contactFormSchema),
    defaultValues: {
      name: '',
      contactType: 'customer',
      email: '',
      phone: '',
      kraPin: '',
      address: '',
      notes: '',
    },
  });

  useEffect(() => {
    if (contact) {
      form.reset({
        name: contact.name,
        contactType: contact.contactType,
        email: contact.email || '',
        phone: contact.phone || '',
        kraPin: contact.kraPin || '',
        address: contact.address || '',
        notes: contact.notes || '',
      });
    } else {
      form.reset({
        name: '',
        contactType: 'customer',
        email: '',
        phone: '',
        kraPin: '',
        address: '',
        notes: '',
      });
    }
  }, [contact, form]);

  const onSubmit = async (data: ContactFormValues) => {
    try {
      const payload = {
        ...data,
        email: data.email || undefined,
        phone: data.phone || undefined,
        kraPin: data.kraPin || undefined,
        address: data.address || undefined,
        notes: data.notes || undefined,
      };

      if (contact) {
        await updateContact.mutateAsync({ id: contact.id, data: payload });
      } else {
        await createContact.mutateAsync(payload);
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
          <DialogTitle>{contact ? 'Edit Contact' : 'Create Contact'}</DialogTitle>
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
                    <Input placeholder="Contact name" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="contactType"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Contact Type</FormLabel>
                  <Select onValueChange={field.onChange} value={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Select contact type" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="customer">Customer</SelectItem>
                      <SelectItem value="supplier">Supplier</SelectItem>
                      <SelectItem value="both">Both</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <FormField
                control={form.control}
                name="email"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Email</FormLabel>
                    <FormControl>
                      <Input type="email" placeholder="contact@example.com" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="phone"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Phone</FormLabel>
                    <FormControl>
                      <Input placeholder="+254 700 000 000" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <FormField
              control={form.control}
              name="kraPin"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>KRA PIN</FormLabel>
                  <FormControl>
                    <Input placeholder="A000000000X" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="address"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Address</FormLabel>
                  <FormControl>
                    <Textarea placeholder="Street address, city, country" {...field} />
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
                    <Textarea placeholder="Additional notes" {...field} />
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
                disabled={createContact.isPending || updateContact.isPending}
              >
                {createContact.isPending || updateContact.isPending
                  ? 'Saving...'
                  : contact
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
