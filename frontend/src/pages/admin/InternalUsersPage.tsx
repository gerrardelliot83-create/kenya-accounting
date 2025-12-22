import { useState, useMemo } from 'react';
import {
  useInternalUsers,
  useCreateInternalUser,
  useDeactivateInternalUser,
  useActivateInternalUser,
} from '@/hooks/useAdmin';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Search, Plus, UserX, UserCheck, Shield } from 'lucide-react';
import type { InternalUserListParams, CreateInternalUserRequest } from '@/types/admin';
import { DEFAULT_PAGE_SIZE } from '@/lib/constants';
import { formatDistanceToNow } from 'date-fns';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useToast } from '@/hooks/use-toast';

export const InternalUsersPage = () => {
  const { toast } = useToast();
  const [page, setPage] = useState(1);
  const [roleFilter, setRoleFilter] = useState<string>('all');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [formData, setFormData] = useState<CreateInternalUserRequest>({
    full_name: '',
    email: '',
    role: 'support_agent',
    temporary_password: '',
  });
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});

  const queryParams = useMemo(() => {
    const params: InternalUserListParams = { page, limit: DEFAULT_PAGE_SIZE };
    if (roleFilter !== 'all') params.role = roleFilter;
    return params;
  }, [page, roleFilter]);

  const { data, isLoading } = useInternalUsers(queryParams);
  const createUser = useCreateInternalUser();
  const deactivateUser = useDeactivateInternalUser();
  const activateUser = useActivateInternalUser();

  const validateForm = () => {
    const errors: Record<string, string> = {};

    if (!formData.full_name.trim()) {
      errors.full_name = 'Full name is required';
    }

    if (!formData.email.trim()) {
      errors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      errors.email = 'Invalid email format';
    }

    if (!formData.temporary_password) {
      errors.temporary_password = 'Temporary password is required';
    } else if (formData.temporary_password.length < 8) {
      errors.temporary_password = 'Password must be at least 8 characters';
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleCreateUser = async () => {
    if (!validateForm()) return;

    try {
      await createUser.mutateAsync(formData);
      toast({
        title: 'Success',
        description: 'Internal user created successfully',
      });
      setIsModalOpen(false);
      setFormData({
        full_name: '',
        email: '',
        role: 'support_agent',
        temporary_password: '',
      });
      setFormErrors({});
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to create user',
        variant: 'destructive',
      });
    }
  };

  const handleToggleUserStatus = async (userId: string, isActive: boolean) => {
    try {
      if (isActive) {
        await deactivateUser.mutateAsync(userId);
        toast({
          title: 'Success',
          description: 'User deactivated successfully',
        });
      } else {
        await activateUser.mutateAsync(userId);
        toast({
          title: 'Success',
          description: 'User activated successfully',
        });
      }
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to update user status',
        variant: 'destructive',
      });
    }
  };

  const getRoleBadge = (role: string) => {
    const variants: Record<string, 'default' | 'secondary' | 'destructive'> = {
      system_admin: 'destructive',
      support_agent: 'default',
      onboarding_agent: 'secondary',
    };

    const labels: Record<string, string> = {
      system_admin: 'System Admin',
      support_agent: 'Support Agent',
      onboarding_agent: 'Onboarding Agent',
    };

    return (
      <Badge variant={variants[role] || 'secondary'}>
        {labels[role] || role}
      </Badge>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Internal Users</h1>
          <p className="text-muted-foreground">
            Manage system administrators and support agents
          </p>
        </div>
        <Button onClick={() => setIsModalOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Add User
        </Button>
      </div>

      {/* Filters */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center">
        <Select
          value={roleFilter}
          onValueChange={(value) => {
            setRoleFilter(value);
            setPage(1);
          }}
        >
          <SelectTrigger className="w-full md:w-[220px]">
            <SelectValue placeholder="Filter by role" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Roles</SelectItem>
            <SelectItem value="system_admin">System Admin</SelectItem>
            <SelectItem value="support_agent">Support Agent</SelectItem>
            <SelectItem value="onboarding_agent">Onboarding Agent</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Table Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Users
            {data && <span className="text-sm font-normal text-muted-foreground">({data.total} total)</span>}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Last Login</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading ? (
                  Array.from({ length: 5 }).map((_, index) => (
                    <TableRow key={index}>
                      <TableCell><Skeleton className="h-4 w-32" /></TableCell>
                      <TableCell><Skeleton className="h-4 w-48" /></TableCell>
                      <TableCell><Skeleton className="h-4 w-24" /></TableCell>
                      <TableCell><Skeleton className="h-4 w-16" /></TableCell>
                      <TableCell><Skeleton className="h-4 w-32" /></TableCell>
                      <TableCell><Skeleton className="h-4 w-32" /></TableCell>
                      <TableCell><Skeleton className="h-8 w-24" /></TableCell>
                    </TableRow>
                  ))
                ) : !data?.users || data.users.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="h-48 text-center">
                      <div className="flex flex-col items-center justify-center text-muted-foreground">
                        <Shield className="mb-2 h-8 w-8" />
                        <p>No internal users found</p>
                      </div>
                    </TableCell>
                  </TableRow>
                ) : (
                  data.users.map((user) => (
                    <TableRow key={user.id}>
                      <TableCell className="font-medium">{user.full_name}</TableCell>
                      <TableCell className="font-mono text-sm">{user.email_masked}</TableCell>
                      <TableCell>{getRoleBadge(user.role)}</TableCell>
                      <TableCell>
                        <Badge variant={user.is_active ? 'default' : 'secondary'}>
                          {user.is_active ? 'Active' : 'Inactive'}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {user.last_login
                          ? formatDistanceToNow(new Date(user.last_login), { addSuffix: true })
                          : 'Never'}
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {formatDistanceToNow(new Date(user.created_at), { addSuffix: true })}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleToggleUserStatus(user.id, user.is_active)}
                          disabled={deactivateUser.isPending || activateUser.isPending}
                        >
                          {user.is_active ? (
                            <>
                              <UserX className="mr-2 h-4 w-4" />
                              Deactivate
                            </>
                          ) : (
                            <>
                              <UserCheck className="mr-2 h-4 w-4" />
                              Activate
                            </>
                          )}
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>

          {/* Pagination */}
          {data && data.totalPages > 1 && (
            <div className="mt-4 flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                Showing {(page - 1) * DEFAULT_PAGE_SIZE + 1} to{' '}
                {Math.min(page * DEFAULT_PAGE_SIZE, data.total)} of {data.total} users
              </p>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(page - 1)}
                  disabled={page === 1}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(page + 1)}
                  disabled={page === data.totalPages}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Create User Modal */}
      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create Internal User</DialogTitle>
            <DialogDescription>
              Add a new system administrator or support agent. They will receive a temporary password and must change it on first login.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="full_name">Full Name</Label>
              <Input
                id="full_name"
                placeholder="John Doe"
                value={formData.full_name}
                onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
              />
              {formErrors.full_name && (
                <p className="text-sm text-destructive">{formErrors.full_name}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="john.doe@example.com"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              />
              {formErrors.email && (
                <p className="text-sm text-destructive">{formErrors.email}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="role">Role</Label>
              <Select
                value={formData.role}
                onValueChange={(value) => setFormData({ ...formData, role: value as any })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="support_agent">Support Agent</SelectItem>
                  <SelectItem value="onboarding_agent">Onboarding Agent</SelectItem>
                  <SelectItem value="system_admin">System Admin</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="temporary_password">Temporary Password</Label>
              <Input
                id="temporary_password"
                type="password"
                placeholder="Minimum 8 characters"
                value={formData.temporary_password}
                onChange={(e) => setFormData({ ...formData, temporary_password: e.target.value })}
              />
              {formErrors.temporary_password && (
                <p className="text-sm text-destructive">{formErrors.temporary_password}</p>
              )}
              <p className="text-xs text-muted-foreground">
                User will be required to change this password on first login
              </p>
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setIsModalOpen(false);
                setFormErrors({});
              }}
            >
              Cancel
            </Button>
            <Button onClick={handleCreateUser} disabled={createUser.isPending}>
              {createUser.isPending ? 'Creating...' : 'Create User'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};
