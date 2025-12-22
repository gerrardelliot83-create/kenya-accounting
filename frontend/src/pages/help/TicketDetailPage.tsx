import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { format } from 'date-fns';
import { ArrowLeft, Send, Star } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Separator } from '@/components/ui/separator';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { TicketStatusBadge } from '@/components/help/TicketStatusBadge';
import { useTicket, useAddMessage, useRateTicket } from '@/hooks/useSupport';
import { useToast } from '@/hooks/use-toast';
import { cn } from '@/lib/utils';

export const TicketDetailPage = () => {
  const { id } = useParams<{ id: string }>();
  const { toast } = useToast();

  const [replyMessage, setReplyMessage] = useState('');
  const [rating, setRating] = useState<number | null>(null);

  const { data, isLoading, error } = useTicket(id || '');
  const addMessageMutation = useAddMessage(id || '');
  const rateTicketMutation = useRateTicket(id || '');

  const ticket = data?.ticket;
  const messages = data?.messages || [];

  const handleSendMessage = async () => {
    if (!replyMessage.trim()) return;

    try {
      await addMessageMutation.mutateAsync({ message: replyMessage });
      setReplyMessage('');
      toast({
        title: 'Message sent',
        description: 'Your reply has been added to the ticket',
      });
    } catch (err) {
      toast({
        title: 'Error',
        description: 'Failed to send message. Please try again.',
        variant: 'destructive',
      });
    }
  };

  const handleRateTicket = async (stars: number) => {
    try {
      await rateTicketMutation.mutateAsync({ rating: stars });
      setRating(stars);
      toast({
        title: 'Thank you for your feedback',
        description: 'Your rating has been recorded',
      });
    } catch (err) {
      toast({
        title: 'Error',
        description: 'Failed to submit rating. Please try again.',
        variant: 'destructive',
      });
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-1/3" />
        <Card>
          <CardContent className="pt-6 space-y-4">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-24 w-full" />
            ))}
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error || !ticket) {
    return (
      <div className="space-y-6">
        <Button variant="ghost" asChild>
          <Link to="/help/tickets">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Tickets
          </Link>
        </Button>

        <Alert variant="destructive">
          <AlertDescription>
            Failed to load ticket details. Please try again later.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  const canReply = ticket.status !== 'closed' && ticket.status !== 'resolved';
  const canRate = ticket.status === 'resolved' && !ticket.satisfaction_rating;

  return (
    <div className="space-y-6">
      {/* Back Button */}
      <Button variant="ghost" asChild>
        <Link to="/help/tickets">
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Tickets
        </Link>
      </Button>

      {/* Ticket Header */}
      <Card>
        <CardHeader>
          <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <span className="font-mono text-sm text-muted-foreground">
                  {ticket.ticket_number}
                </span>
                <TicketStatusBadge status={ticket.status} />
              </div>
              <CardTitle className="text-2xl">{ticket.subject}</CardTitle>
              <CardDescription className="mt-2 capitalize">
                {ticket.category.replace('_', ' ')} · Priority: {ticket.priority}
              </CardDescription>
            </div>
            <div className="text-sm text-muted-foreground space-y-1">
              <p>Created: {format(new Date(ticket.created_at), 'PPp')}</p>
              <p>Updated: {format(new Date(ticket.updated_at), 'PPp')}</p>
              {ticket.resolved_at && (
                <p>Resolved: {format(new Date(ticket.resolved_at), 'PPp')}</p>
              )}
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Conversation Thread */}
      <Card>
        <CardHeader>
          <CardTitle>Conversation</CardTitle>
          <CardDescription>
            {messages.length} {messages.length === 1 ? 'message' : 'messages'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {/* Initial Description */}
            <div className="flex gap-4">
              <div className="flex-shrink-0">
                <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
                  <span className="text-sm font-medium text-primary">You</span>
                </div>
              </div>
              <div className="flex-1 space-y-2">
                <div className="flex items-center gap-2">
                  <span className="font-medium">You</span>
                  <span className="text-xs text-muted-foreground">
                    {format(new Date(ticket.created_at), 'PPp')}
                  </span>
                </div>
                <div className="rounded-lg bg-muted p-4">
                  <p className="text-sm whitespace-pre-wrap">{ticket.description}</p>
                </div>
              </div>
            </div>

            {/* Messages */}
            {messages.map((message) => {
              const isCustomer = message.sender_type === 'customer';

              return (
                <div key={message.id} className={cn('flex gap-4', !isCustomer && 'flex-row-reverse')}>
                  <div className="flex-shrink-0">
                    <div
                      className={cn(
                        'h-10 w-10 rounded-full flex items-center justify-center',
                        isCustomer ? 'bg-primary/10' : 'bg-secondary'
                      )}
                    >
                      <span
                        className={cn(
                          'text-sm font-medium',
                          isCustomer ? 'text-primary' : 'text-secondary-foreground'
                        )}
                      >
                        {isCustomer ? 'You' : 'Support'}
                      </span>
                    </div>
                  </div>
                  <div className={cn('flex-1 space-y-2', !isCustomer && 'items-end')}>
                    <div className={cn('flex items-center gap-2', !isCustomer && 'justify-end')}>
                      <span className="font-medium">{message.sender_name}</span>
                      <span className="text-xs text-muted-foreground">
                        {format(new Date(message.created_at), 'PPp')}
                      </span>
                    </div>
                    <div
                      className={cn(
                        'rounded-lg p-4 max-w-[80%]',
                        isCustomer ? 'bg-muted' : 'bg-primary text-primary-foreground'
                      )}
                    >
                      <p className="text-sm whitespace-pre-wrap">{message.message}</p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          <Separator className="my-6" />

          {/* Reply Input */}
          {canReply ? (
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">Add a reply</label>
                <Textarea
                  placeholder="Type your message here..."
                  value={replyMessage}
                  onChange={(e) => setReplyMessage(e.target.value)}
                  rows={4}
                  className="resize-none"
                />
              </div>
              <div className="flex justify-end">
                <Button
                  onClick={handleSendMessage}
                  disabled={!replyMessage.trim() || addMessageMutation.isPending}
                >
                  <Send className="mr-2 h-4 w-4" />
                  {addMessageMutation.isPending ? 'Sending...' : 'Send Reply'}
                </Button>
              </div>
            </div>
          ) : (
            <Alert>
              <AlertDescription>
                {ticket.status === 'closed'
                  ? 'This ticket is closed and cannot receive new messages.'
                  : 'This ticket is resolved. You can rate your experience below.'}
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Rating */}
      {canRate && (
        <Card className="bg-muted/50">
          <CardContent className="pt-6">
            <div className="text-center space-y-4">
              <div>
                <h3 className="font-semibold text-lg">How was your experience?</h3>
                <p className="text-sm text-muted-foreground mt-1">
                  Rate your support experience to help us improve
                </p>
              </div>
              <div className="flex justify-center gap-2">
                {[1, 2, 3, 4, 5].map((stars) => (
                  <Button
                    key={stars}
                    variant={rating === stars ? 'default' : 'outline'}
                    size="lg"
                    onClick={() => handleRateTicket(stars)}
                    disabled={rateTicketMutation.isPending}
                    className="flex-col h-auto p-4"
                  >
                    <Star
                      className={cn(
                        'h-6 w-6 mb-1',
                        rating === stars && 'fill-current'
                      )}
                    />
                    <span className="text-xs">{stars}</span>
                  </Button>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {ticket.satisfaction_rating && (
        <Alert>
          <AlertDescription>
            You rated this ticket {ticket.satisfaction_rating} out of 5 stars. Thank you for your
            feedback!
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
};
