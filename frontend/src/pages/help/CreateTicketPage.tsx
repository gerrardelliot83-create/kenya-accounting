import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { ArrowLeft, Search } from 'lucide-react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form';
import { Separator } from '@/components/ui/separator';
import { FaqAccordion } from '@/components/help/FaqAccordion';
import { useCreateTicket } from '@/hooks/useSupport';
import { useFaqSearch } from '@/hooks/useHelp';
import { useToast } from '@/hooks/use-toast';

const createTicketSchema = z.object({
  subject: z.string().min(5, 'Subject must be at least 5 characters'),
  category: z.enum(['billing', 'technical', 'feature_request', 'general']),
  description: z.string().min(20, 'Description must be at least 20 characters'),
});

type CreateTicketForm = z.infer<typeof createTicketSchema>;

export const CreateTicketPage = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [searchQuery, setSearchQuery] = useState('');

  const createTicketMutation = useCreateTicket();
  const { data: searchResults } = useFaqSearch({ query: searchQuery });

  const form = useForm<CreateTicketForm>({
    resolver: zodResolver(createTicketSchema),
    defaultValues: {
      subject: '',
      category: 'general',
      description: '',
    },
  });

  const onSubmit = async (data: CreateTicketForm) => {
    try {
      const ticket = await createTicketMutation.mutateAsync(data);
      toast({
        title: 'Ticket created',
        description: `Your support ticket ${ticket.ticket_number} has been created`,
      });
      navigate(`/help/tickets/${ticket.id}`);
    } catch (err) {
      toast({
        title: 'Error',
        description: 'Failed to create ticket. Please try again.',
        variant: 'destructive',
      });
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
  };

  const suggestedArticles = searchResults?.results?.slice(0, 3) || [];
  const showSuggestions = searchQuery.length > 2 && suggestedArticles.length > 0;

  return (
    <div className="space-y-6">
      {/* Back Button */}
      <Button variant="ghost" asChild>
        <Link to="/help">
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Help Centre
        </Link>
      </Button>

      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Create Support Ticket</h1>
        <p className="text-muted-foreground">
          Our support team will respond to your ticket as soon as possible
        </p>
      </div>

      {/* Search Before Submitting */}
      <Card className="border-2 border-dashed">
        <CardHeader>
          <CardTitle className="text-lg">Search for answers first</CardTitle>
          <CardDescription>
            You might find the answer to your question in our help articles
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSearch}>
            <div className="flex gap-2">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  type="search"
                  placeholder="Search help articles..."
                  className="pl-9"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
              <Button type="button" variant="outline" asChild>
                <Link to={`/help/faq/search?q=${encodeURIComponent(searchQuery)}`}>
                  View All Results
                </Link>
              </Button>
            </div>
          </form>

          {showSuggestions && (
            <div className="mt-4">
              <p className="text-sm font-medium mb-2">Suggested articles:</p>
              <FaqAccordion articles={suggestedArticles} />
            </div>
          )}
        </CardContent>
      </Card>

      <Separator />

      {/* Ticket Form */}
      <Card>
        <CardHeader>
          <CardTitle>Ticket Details</CardTitle>
          <CardDescription>
            Provide as much detail as possible to help us assist you better
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
              {/* Subject */}
              <FormField
                control={form.control}
                name="subject"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Subject</FormLabel>
                    <FormControl>
                      <Input placeholder="Brief summary of your issue" {...field} />
                    </FormControl>
                    <FormDescription>
                      A clear, concise subject helps us route your ticket faster
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              {/* Category */}
              <FormField
                control={form.control}
                name="category"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Category</FormLabel>
                    <Select onValueChange={field.onChange} defaultValue={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select a category" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="general">General Question</SelectItem>
                        <SelectItem value="billing">Billing & Payments</SelectItem>
                        <SelectItem value="technical">Technical Issue</SelectItem>
                        <SelectItem value="feature_request">Feature Request</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormDescription>
                      Choose the category that best describes your issue
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              {/* Description */}
              <FormField
                control={form.control}
                name="description"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Description</FormLabel>
                    <FormControl>
                      <Textarea
                        placeholder="Provide detailed information about your issue..."
                        className="resize-none min-h-[150px]"
                        {...field}
                      />
                    </FormControl>
                    <FormDescription>
                      Include steps to reproduce the issue, error messages, or any other relevant
                      details
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              {/* Submit Button */}
              <div className="flex gap-3 justify-end">
                <Button type="button" variant="outline" asChild>
                  <Link to="/help">Cancel</Link>
                </Button>
                <Button type="submit" disabled={createTicketMutation.isPending}>
                  {createTicketMutation.isPending ? 'Creating...' : 'Create Ticket'}
                </Button>
              </div>
            </form>
          </Form>
        </CardContent>
      </Card>

      {/* What Happens Next */}
      <Alert>
        <AlertDescription>
          <strong>What happens next?</strong> Our support team will review your ticket and respond
          within 24-48 hours. You'll receive an email notification when there's an update.
        </AlertDescription>
      </Alert>
    </div>
  );
};
