import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  useApplication,
  useApproveApplication,
  useRejectApplication,
  useRequestInfo,
} from '@/hooks/useOnboarding';
import { useToast } from '@/hooks/use-toast';
import { formatDate } from '@/lib/formatters';
import {
  ArrowLeft,
  Building2,
  User,
  Mail,
  Phone,
  MapPin,
  FileText,
  CheckCircle,
  XCircle,
  AlertCircle,
  Copy,
  CheckCircle2,
} from 'lucide-react';
import type { OnboardingStatus, ApprovalResponse } from '@/types/onboarding';

const statusColors: Record<OnboardingStatus, string> = {
  draft: 'bg-gray-500',
  submitted: 'bg-blue-500',
  under_review: 'bg-yellow-500',
  approved: 'bg-green-500',
  rejected: 'bg-red-500',
  info_requested: 'bg-orange-500',
};

const statusLabels: Record<OnboardingStatus, string> = {
  draft: 'Draft',
  submitted: 'Submitted',
  under_review: 'Under Review',
  approved: 'Approved',
  rejected: 'Rejected',
  info_requested: 'Info Requested',
};

export const ApplicationDetailPage = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();

  const { data: application, isLoading } = useApplication(id!);
  const approveMutation = useApproveApplication();
  const rejectMutation = useRejectApplication();
  const requestInfoMutation = useRequestInfo();

  const [showApproveDialog, setShowApproveDialog] = useState(false);
  const [showRejectDialog, setShowRejectDialog] = useState(false);
  const [showRequestInfoDialog, setShowRequestInfoDialog] = useState(false);
  const [showCredentialsDialog, setShowCredentialsDialog] = useState(false);
  const [credentials, setCredentials] = useState<ApprovalResponse | null>(null);
  const [rejectionReason, setRejectionReason] = useState('');
  const [infoRequestNote, setInfoRequestNote] = useState('');
  const [copiedField, setCopiedField] = useState<string | null>(null);

  const handleApprove = async () => {
    if (!id) return;

    try {
      const result = await approveMutation.mutateAsync(id);
      setCredentials(result);
      setShowApproveDialog(false);
      setShowCredentialsDialog(true);
    } catch (error) {
      // Error handled by mutation
    }
  };

  const handleReject = async () => {
    if (!id || !rejectionReason.trim()) {
      toast({
        title: 'Error',
        description: 'Please provide a rejection reason',
        variant: 'destructive',
      });
      return;
    }

    try {
      await rejectMutation.mutateAsync({
        id,
        data: { reason: rejectionReason },
      });
      setShowRejectDialog(false);
      setRejectionReason('');
    } catch (error) {
      // Error handled by mutation
    }
  };

  const handleRequestInfo = async () => {
    if (!id || !infoRequestNote.trim()) {
      toast({
        title: 'Error',
        description: 'Please provide a note for the information request',
        variant: 'destructive',
      });
      return;
    }

    try {
      await requestInfoMutation.mutateAsync({
        id,
        data: { note: infoRequestNote },
      });
      setShowRequestInfoDialog(false);
      setInfoRequestNote('');
    } catch (error) {
      // Error handled by mutation
    }
  };

  const handleCopy = (text: string, field: string) => {
    navigator.clipboard.writeText(text);
    setCopiedField(field);
    setTimeout(() => setCopiedField(null), 2000);
    toast({
      title: 'Copied',
      description: `${field} copied to clipboard`,
    });
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-20 w-full" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  if (!application) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <AlertCircle className="mb-4 h-12 w-12 text-muted-foreground" />
        <h2 className="mb-2 text-2xl font-semibold">Application Not Found</h2>
        <p className="mb-4 text-muted-foreground">
          The application you're looking for doesn't exist.
        </p>
        <Button onClick={() => navigate('/onboarding/queue')}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Queue
        </Button>
      </div>
    );
  }

  const canTakeAction = ['submitted', 'under_review', 'info_requested'].includes(
    application.status
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="outline" onClick={() => navigate('/onboarding/queue')}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back
          </Button>
          <div>
            <h1 className="text-3xl font-semibold">{application.business_name}</h1>
            <p className="mt-1 text-muted-foreground">Application Details</p>
          </div>
        </div>
        <Badge variant="secondary" className={`${statusColors[application.status]} text-white`}>
          {statusLabels[application.status]}
        </Badge>
      </div>

      {/* Action Buttons */}
      {canTakeAction && (
        <Card>
          <CardContent className="flex gap-3 pt-6">
            <Button
              onClick={() => setShowApproveDialog(true)}
              disabled={approveMutation.isPending}
              className="flex-1"
            >
              <CheckCircle className="mr-2 h-4 w-4" />
              Approve Application
            </Button>
            <Button
              variant="outline"
              onClick={() => setShowRequestInfoDialog(true)}
              disabled={requestInfoMutation.isPending}
              className="flex-1"
            >
              <AlertCircle className="mr-2 h-4 w-4" />
              Request Information
            </Button>
            <Button
              variant="destructive"
              onClick={() => setShowRejectDialog(true)}
              disabled={rejectMutation.isPending}
              className="flex-1"
            >
              <XCircle className="mr-2 h-4 w-4" />
              Reject Application
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Business Information */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Building2 className="h-5 w-5" />
            Business Information
          </CardTitle>
        </CardHeader>
        <CardContent>
          <dl className="grid gap-4 md:grid-cols-2">
            <div>
              <dt className="text-sm font-medium text-muted-foreground">Business Name</dt>
              <dd className="mt-1 text-sm font-semibold">{application.business_name}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-muted-foreground">Business Type</dt>
              <dd className="mt-1 text-sm">
                {application.business_type === 'sole_proprietor'
                  ? 'Sole Proprietor'
                  : application.business_type === 'partnership'
                  ? 'Partnership'
                  : 'Limited Company'}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-muted-foreground">KRA PIN</dt>
              <dd className="mt-1 text-sm font-mono">{application.kra_pin}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-muted-foreground">County</dt>
              <dd className="mt-1 text-sm">
                {application.county}
                {application.sub_county && ` - ${application.sub_county}`}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-muted-foreground">VAT Registered</dt>
              <dd className="mt-1 text-sm">{application.vat_registered ? 'Yes' : 'No'}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-muted-foreground">TOT Registered</dt>
              <dd className="mt-1 text-sm">{application.tot_registered ? 'Yes' : 'No'}</dd>
            </div>
          </dl>
        </CardContent>
      </Card>

      {/* Contact Information */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MapPin className="h-5 w-5" />
            Contact Information
          </CardTitle>
        </CardHeader>
        <CardContent>
          <dl className="grid gap-4 md:grid-cols-2">
            <div>
              <dt className="text-sm font-medium text-muted-foreground">Phone</dt>
              <dd className="mt-1 flex items-center gap-2 text-sm">
                <Phone className="h-4 w-4" />
                {application.phone}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-muted-foreground">Email</dt>
              <dd className="mt-1 flex items-center gap-2 text-sm">
                <Mail className="h-4 w-4" />
                {application.email}
              </dd>
            </div>
          </dl>
        </CardContent>
      </Card>

      {/* Owner Information */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <User className="h-5 w-5" />
            Owner Information
          </CardTitle>
        </CardHeader>
        <CardContent>
          <dl className="grid gap-4 md:grid-cols-2">
            <div>
              <dt className="text-sm font-medium text-muted-foreground">Full Name</dt>
              <dd className="mt-1 text-sm font-semibold">{application.owner_name}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-muted-foreground">National ID</dt>
              <dd className="mt-1 text-sm font-mono">{application.owner_national_id}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-muted-foreground">Phone</dt>
              <dd className="mt-1 flex items-center gap-2 text-sm">
                <Phone className="h-4 w-4" />
                {application.owner_phone}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-muted-foreground">Email</dt>
              <dd className="mt-1 flex items-center gap-2 text-sm">
                <Mail className="h-4 w-4" />
                {application.owner_email}
              </dd>
            </div>
          </dl>
        </CardContent>
      </Card>

      {/* Status Information */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Status Information
          </CardTitle>
        </CardHeader>
        <CardContent>
          <dl className="grid gap-4 md:grid-cols-2">
            <div>
              <dt className="text-sm font-medium text-muted-foreground">Created At</dt>
              <dd className="mt-1 text-sm">{formatDate(application.created_at)}</dd>
            </div>
            {application.submitted_at && (
              <div>
                <dt className="text-sm font-medium text-muted-foreground">Submitted At</dt>
                <dd className="mt-1 text-sm">{formatDate(application.submitted_at)}</dd>
              </div>
            )}
            {application.reviewed_at && (
              <div>
                <dt className="text-sm font-medium text-muted-foreground">Reviewed At</dt>
                <dd className="mt-1 text-sm">{formatDate(application.reviewed_at)}</dd>
              </div>
            )}
            {application.reviewed_by && (
              <div>
                <dt className="text-sm font-medium text-muted-foreground">Reviewed By</dt>
                <dd className="mt-1 text-sm">{application.reviewed_by}</dd>
              </div>
            )}
            {application.rejection_reason && (
              <div className="md:col-span-2">
                <dt className="text-sm font-medium text-muted-foreground">Rejection Reason</dt>
                <dd className="mt-1 rounded-md bg-destructive/10 p-3 text-sm text-destructive">
                  {application.rejection_reason}
                </dd>
              </div>
            )}
            {application.info_request_note && (
              <div className="md:col-span-2">
                <dt className="text-sm font-medium text-muted-foreground">Information Request</dt>
                <dd className="mt-1 rounded-md bg-orange-50 p-3 text-sm text-orange-900">
                  {application.info_request_note}
                </dd>
              </div>
            )}
          </dl>
        </CardContent>
      </Card>

      {/* Approve Dialog */}
      <Dialog open={showApproveDialog} onOpenChange={setShowApproveDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Approve Application</DialogTitle>
            <DialogDescription>
              Are you sure you want to approve this application? This will create a new business
              and user account with temporary credentials.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowApproveDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleApprove} disabled={approveMutation.isPending}>
              {approveMutation.isPending ? 'Approving...' : 'Approve'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Credentials Dialog */}
      <Dialog open={showCredentialsDialog} onOpenChange={setShowCredentialsDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5 text-green-500" />
              Application Approved
            </DialogTitle>
            <DialogDescription>
              Business and user account created successfully. Please share these credentials
              securely with the business owner.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="rounded-lg border bg-muted/50 p-4">
              <h3 className="mb-3 font-semibold">Login Credentials</h3>
              <dl className="space-y-3">
                <div>
                  <dt className="text-sm text-muted-foreground">Email</dt>
                  <dd className="mt-1 flex items-center justify-between rounded bg-background p-2 font-mono text-sm">
                    {credentials?.login_email}
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleCopy(credentials?.login_email || '', 'Email')}
                    >
                      {copiedField === 'Email' ? (
                        <CheckCircle2 className="h-4 w-4" />
                      ) : (
                        <Copy className="h-4 w-4" />
                      )}
                    </Button>
                  </dd>
                </div>
                <div>
                  <dt className="text-sm text-muted-foreground">Temporary Password</dt>
                  <dd className="mt-1 flex items-center justify-between rounded bg-background p-2 font-mono text-sm">
                    {credentials?.temporary_password}
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() =>
                        handleCopy(credentials?.temporary_password || '', 'Password')
                      }
                    >
                      {copiedField === 'Password' ? (
                        <CheckCircle2 className="h-4 w-4" />
                      ) : (
                        <Copy className="h-4 w-4" />
                      )}
                    </Button>
                  </dd>
                </div>
                <div>
                  <dt className="text-sm text-muted-foreground">Business ID</dt>
                  <dd className="mt-1 rounded bg-background p-2 font-mono text-sm">
                    {credentials?.business_id}
                  </dd>
                </div>
              </dl>
            </div>
            <div className="rounded-lg border border-orange-200 bg-orange-50 p-4 text-sm text-orange-900">
              <p className="font-semibold">Important:</p>
              <ul className="ml-4 mt-2 list-disc space-y-1">
                <li>Share these credentials securely with the business owner</li>
                <li>User will be required to change password on first login</li>
                <li>These credentials will not be shown again</li>
              </ul>
            </div>
          </div>
          <DialogFooter>
            <Button onClick={() => setShowCredentialsDialog(false)}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Reject Dialog */}
      <Dialog open={showRejectDialog} onOpenChange={setShowRejectDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Reject Application</DialogTitle>
            <DialogDescription>
              Please provide a reason for rejecting this application. This will be visible to the
              applicant.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="rejection-reason">Rejection Reason *</Label>
              <Textarea
                id="rejection-reason"
                placeholder="Enter reason for rejection..."
                value={rejectionReason}
                onChange={(e) => setRejectionReason(e.target.value)}
                rows={4}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowRejectDialog(false)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleReject}
              disabled={rejectMutation.isPending || !rejectionReason.trim()}
            >
              {rejectMutation.isPending ? 'Rejecting...' : 'Reject Application'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Request Info Dialog */}
      <Dialog open={showRequestInfoDialog} onOpenChange={setShowRequestInfoDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Request More Information</DialogTitle>
            <DialogDescription>
              Request additional information from the applicant. They will be notified and can
              update their application.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="info-request">Information Request *</Label>
              <Textarea
                id="info-request"
                placeholder="Enter what information you need..."
                value={infoRequestNote}
                onChange={(e) => setInfoRequestNote(e.target.value)}
                rows={4}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowRequestInfoDialog(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleRequestInfo}
              disabled={requestInfoMutation.isPending || !infoRequestNote.trim()}
            >
              {requestInfoMutation.isPending ? 'Sending...' : 'Send Request'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};
