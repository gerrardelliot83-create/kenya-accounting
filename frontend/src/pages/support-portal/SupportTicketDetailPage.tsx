import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  useAdminTicket,
  useUpdateTicket,
  useAddAgentMessage,
  useCannedResponses,
} from '@/hooks/useAdminSupport';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  TicketStatusBadge,
  TicketPriorityBadge,
  InternalNoteBadge,
  InternalNoteAlert,
  AgentAssignSelect,
} from '@/components/support-portal';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';
import {
  ArrowLeft,
  Building2,
  User,
  Mail,
  Calendar,
  Send,
  FileText,
  Loader2,
} from 'lucide-react';
import { format } from 'date-fns';
import type { TicketStatus, TicketPriority, TicketMessage, CannedResponse } from '@/types/admin-support';
import { useToast } from '@/hooks/use-toast';

export const SupportTicketDetailPage = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();

  const { data: ticket, isLoading } = useAdminTicket(id!);
  const updateTicket = useUpdateTicket();
  const addMessage = useAddAgentMessage();
  const { data: templates } = useCannedResponses();

  const [replyMessage, setReplyMessage] = useState('');
  const [isInternal, setIsInternal] = useState(false);
  const [showTemplateDialog, setShowTemplateDialog] = useState(false);

  if (isLoading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (!ticket) {
    return (
      <div className="flex h-96 flex-col items-center justify-center">
        <p className="text-lg font-medium">Ticket not found</p>
        <Button onClick={() => navigate('/support-portal/tickets')} className="mt-4">
          Back to Tickets
        </Button>
      </div>
    );
  }

  const handleStatusChange = (status: TicketStatus) => {
    updateTicket.mutate(
      {
        id: ticket.id,
        data: { status },
      },
      {
        onSuccess: () => {
          toast({
            title: 'Status updated',
            description: `Ticket status changed to ${status}`,
          });
        },
        onError: () => {
          toast({
            title: 'Error',
            description: 'Failed to update status',
            variant: 'destructive',
          });
        },
      }
    );
  };

  const handlePriorityChange = (priority: TicketPriority) => {
    updateTicket.mutate(
      {
        id: ticket.id,
        data: { priority },
      },
      {
        onSuccess: () => {
          toast({
            title: 'Priority updated',
            description: `Ticket priority changed to ${priority}`,
          });
        },
        onError: () => {
          toast({
            title: 'Error',
            description: 'Failed to update priority',
            variant: 'destructive',
          });
        },
      }
    );
  };

  const handleSendMessage = () => {
    if (!replyMessage.trim()) {
      toast({
        title: 'Error',
        description: 'Please enter a message',
        variant: 'destructive',
      });
      return;
    }

    addMessage.mutate(
      {
        id: ticket.id,
        data: {
          message: replyMessage,
          is_internal: isInternal,
        },
      },
      {
        onSuccess: () => {
          setReplyMessage('');
          setIsInternal(false);
          toast({
            title: 'Message sent',
            description: isInternal
              ? 'Internal note added'
              : 'Reply sent to customer',
          });
        },
        onError: () => {
          toast({
            title: 'Error',
            description: 'Failed to send message',
            variant: 'destructive',
          });
        },
      }
    );
  };

  const handleInsertTemplate = (templateContent: string) => {
    setReplyMessage(templateContent);
    setShowTemplateDialog(false);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => navigate('/support-portal/tickets')}
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-3xl font-bold tracking-tight">
              {ticket.ticket_number}
            </h1>
            <p className="text-muted-foreground">{ticket.subject}</p>
          </div>
        </div>
        <div className="flex gap-2">
          <TicketStatusBadge status={ticket.status} showIcon />
          <TicketPriorityBadge priority={ticket.priority} showIcon />
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Main Content - Left Column (2/3) */}
        <div className="space-y-6 lg:col-span-2">
          {/* Quick Actions */}
          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                {/* Status Update */}
                <div>
                  <Label className="mb-2 block">Update Status</Label>
                  <Select
                    value={ticket.status}
                    onValueChange={(value) => handleStatusChange(value as TicketStatus)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="open">Open</SelectItem>
                      <SelectItem value="in_progress">In Progress</SelectItem>
                      <SelectItem value="waiting_customer">Waiting Customer</SelectItem>
                      <SelectItem value="resolved">Resolved</SelectItem>
                      <SelectItem value="closed">Closed</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Priority Update */}
                <div>
                  <Label className="mb-2 block">Update Priority</Label>
                  <Select
                    value={ticket.priority}
                    onValueChange={(value) => handlePriorityChange(value as TicketPriority)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="urgent">Urgent</SelectItem>
                      <SelectItem value="high">High</SelectItem>
                      <SelectItem value="medium">Medium</SelectItem>
                      <SelectItem value="low">Low</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Assign Agent */}
              <div>
                <Label className="mb-2 block">Assign Agent</Label>
                <AgentAssignSelect
                  ticketId={ticket.id}
                  currentAgentId={ticket.assigned_agent_id}
                  currentAgentName={ticket.assigned_agent_name}
                  onAssignComplete={() => {
                    toast({
                      title: 'Agent assigned',
                      description: 'Ticket has been assigned successfully',
                    });
                  }}
                />
              </div>
            </CardContent>
          </Card>

          {/* Conversation */}
          <Card>
            <CardHeader>
              <CardTitle>Conversation ({ticket.messages.length})</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {ticket.messages.length === 0 ? (
                <div className="py-8 text-center text-muted-foreground">
                  No messages yet
                </div>
              ) : (
                <div className="space-y-4">
                  {ticket.messages.map((message: TicketMessage) => (
                    <div
                      key={message.id}
                      className={`rounded-lg border p-4 ${
                        message.is_internal
                          ? 'border-yellow-200 bg-yellow-50 dark:border-yellow-900 dark:bg-yellow-900/10'
                          : 'border-border bg-card'
                      }`}
                    >
                      <div className="mb-2 flex items-start justify-between">
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-semibold">
                              {message.sender_name}
                            </span>
                            <Badge variant="outline" className="text-xs">
                              {message.sender_type === 'customer'
                                ? 'Customer'
                                : 'Agent'}
                            </Badge>
                            {message.is_internal && <InternalNoteBadge />}
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {format(new Date(message.created_at), 'PPpp')}
                          </div>
                        </div>
                      </div>
                      <div className="whitespace-pre-wrap text-sm">
                        {message.message}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Reply Section */}
          <Card>
            <CardHeader>
              <CardTitle>Reply</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {isInternal && <InternalNoteAlert />}

              <Textarea
                placeholder="Type your message here..."
                value={replyMessage}
                onChange={(e) => setReplyMessage(e.target.value)}
                rows={6}
                className="resize-none"
              />

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="internal"
                      checked={isInternal}
                      onCheckedChange={(checked) => setIsInternal(checked as boolean)}
                    />
                    <Label htmlFor="internal" className="cursor-pointer text-sm">
                      Internal Note (not visible to customer)
                    </Label>
                  </div>

                  <Dialog open={showTemplateDialog} onOpenChange={setShowTemplateDialog}>
                    <DialogTrigger asChild>
                      <Button variant="outline" size="sm">
                        <FileText className="mr-2 h-4 w-4" />
                        Insert Template
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="max-w-2xl">
                      <DialogHeader>
                        <DialogTitle>Canned Responses</DialogTitle>
                        <DialogDescription>
                          Select a template to insert into your reply
                        </DialogDescription>
                      </DialogHeader>
                      <div className="max-h-96 space-y-2 overflow-y-auto">
                        {templates?.map((template: CannedResponse) => (
                          <div
                            key={template.id}
                            className="cursor-pointer rounded-lg border p-3 hover:bg-accent"
                            onClick={() => handleInsertTemplate(template.content)}
                          >
                            <div className="font-medium">{template.title}</div>
                            <div className="mt-1 text-sm text-muted-foreground">
                              {template.category}
                            </div>
                            <div className="mt-2 line-clamp-2 text-sm">
                              {template.content}
                            </div>
                          </div>
                        ))}
                      </div>
                    </DialogContent>
                  </Dialog>
                </div>

                <Button
                  onClick={handleSendMessage}
                  disabled={!replyMessage.trim() || addMessage.isPending}
                >
                  {addMessage.isPending ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Sending...
                    </>
                  ) : (
                    <>
                      <Send className="mr-2 h-4 w-4" />
                      Send {isInternal ? 'Note' : 'Reply'}
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Sidebar - Right Column (1/3) */}
        <div className="space-y-6">
          {/* Business Context */}
          <Card>
            <CardHeader>
              <CardTitle>Business Context</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-start gap-3">
                <Building2 className="mt-0.5 h-5 w-5 text-muted-foreground" />
                <div className="flex-1">
                  <div className="text-sm font-medium text-muted-foreground">
                    Business Name
                  </div>
                  <div className="font-medium">
                    {ticket.business_info.business_name}
                  </div>
                </div>
              </div>

              <Separator />

              <div className="flex items-start gap-3">
                <Building2 className="mt-0.5 h-5 w-5 text-muted-foreground" />
                <div className="flex-1">
                  <div className="text-sm font-medium text-muted-foreground">
                    Business Type
                  </div>
                  <div className="capitalize">
                    {ticket.business_info.business_type.replace(/_/g, ' ')}
                  </div>
                </div>
              </div>

              <Separator />

              <div className="flex items-start gap-3">
                <User className="mt-0.5 h-5 w-5 text-muted-foreground" />
                <div className="flex-1">
                  <div className="text-sm font-medium text-muted-foreground">
                    Customer Name
                  </div>
                  <div>{ticket.customer_name}</div>
                </div>
              </div>

              <Separator />

              <div className="flex items-start gap-3">
                <Mail className="mt-0.5 h-5 w-5 text-muted-foreground" />
                <div className="flex-1">
                  <div className="text-sm font-medium text-muted-foreground">
                    Customer Email
                  </div>
                  <div className="break-all text-sm">{ticket.customer_email}</div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Ticket Details */}
          <Card>
            <CardHeader>
              <CardTitle>Ticket Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div>
                <div className="text-sm font-medium text-muted-foreground">Category</div>
                <div className="capitalize">
                  {ticket.category.replace(/_/g, ' ')}
                </div>
              </div>

              <Separator />

              <div>
                <div className="text-sm font-medium text-muted-foreground">
                  Description
                </div>
                <div className="mt-1 whitespace-pre-wrap text-sm">
                  {ticket.description}
                </div>
              </div>

              <Separator />

              <div className="flex items-start gap-3">
                <Calendar className="mt-0.5 h-5 w-5 text-muted-foreground" />
                <div className="flex-1">
                  <div className="text-sm font-medium text-muted-foreground">
                    Created
                  </div>
                  <div className="text-sm">
                    {format(new Date(ticket.created_at), 'PPpp')}
                  </div>
                </div>
              </div>

              <Separator />

              <div className="flex items-start gap-3">
                <Calendar className="mt-0.5 h-5 w-5 text-muted-foreground" />
                <div className="flex-1">
                  <div className="text-sm font-medium text-muted-foreground">
                    Last Updated
                  </div>
                  <div className="text-sm">
                    {format(new Date(ticket.updated_at), 'PPpp')}
                  </div>
                </div>
              </div>

              {ticket.resolved_at && (
                <>
                  <Separator />
                  <div className="flex items-start gap-3">
                    <Calendar className="mt-0.5 h-5 w-5 text-muted-foreground" />
                    <div className="flex-1">
                      <div className="text-sm font-medium text-muted-foreground">
                        Resolved
                      </div>
                      <div className="text-sm">
                        {format(new Date(ticket.resolved_at), 'PPpp')}
                      </div>
                    </div>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};
