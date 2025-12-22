import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { useContacts } from '@/hooks/useContacts';
import { useItems } from '@/hooks/useItems';
import { useInvoices } from '@/hooks/useInvoices';
import { Users, Package, FileText, Plus } from 'lucide-react';
import { formatCurrency, formatDate } from '@/lib/formatters';
import { DASHBOARD_RECENT_INVOICES_LIMIT } from '@/lib/constants';

export const DashboardPage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const { data: contactsData, isLoading: contactsLoading } = useContacts({ limit: 1 });
  const { data: itemsData, isLoading: itemsLoading } = useItems({ limit: 1 });
  const { data: draftInvoicesData, isLoading: draftLoading } = useInvoices({
    status: 'draft',
    limit: 1,
  });
  const { data: issuedInvoicesData, isLoading: issuedLoading } = useInvoices({
    status: 'issued',
    limit: 1,
  });
  const { data: recentInvoicesData, isLoading: recentLoading } = useInvoices({
    limit: DASHBOARD_RECENT_INVOICES_LIMIT
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold">Dashboard</h1>
        <p className="mt-2 text-muted-foreground">
          Welcome back{user?.firstName ? `, ${user.firstName}` : ''}
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Contacts</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {contactsLoading ? (
              <Skeleton className="h-8 w-16" />
            ) : (
              <div className="text-2xl font-bold">{contactsData?.total || 0}</div>
            )}
            <p className="text-xs text-muted-foreground">
              Customers and suppliers
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Items</CardTitle>
            <Package className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {itemsLoading ? (
              <Skeleton className="h-8 w-16" />
            ) : (
              <div className="text-2xl font-bold">{itemsData?.total || 0}</div>
            )}
            <p className="text-xs text-muted-foreground">
              Products and services
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Draft Invoices</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {draftLoading ? (
              <Skeleton className="h-8 w-16" />
            ) : (
              <div className="text-2xl font-bold">{draftInvoicesData?.total || 0}</div>
            )}
            <p className="text-xs text-muted-foreground">
              Awaiting issue
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Issued Invoices</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {issuedLoading ? (
              <Skeleton className="h-8 w-16" />
            ) : (
              <div className="text-2xl font-bold">{issuedInvoicesData?.total || 0}</div>
            )}
            <p className="text-xs text-muted-foreground">
              Awaiting payment
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Recent Invoices</CardTitle>
            <CardDescription>Your latest {DASHBOARD_RECENT_INVOICES_LIMIT} invoices</CardDescription>
          </CardHeader>
          <CardContent>
            {recentLoading ? (
              <div className="space-y-3">
                {Array.from({ length: 3 }).map((_, i) => (
                  <Skeleton key={i} className="h-12 w-full" />
                ))}
              </div>
            ) : recentInvoicesData?.invoices.length === 0 ? (
              <p className="text-sm text-muted-foreground">No invoices yet</p>
            ) : (
              <div className="space-y-3">
                {recentInvoicesData?.invoices.map((invoice) => (
                  <div
                    key={invoice.id}
                    className="flex items-center justify-between rounded-lg border p-3 hover:bg-accent cursor-pointer"
                    onClick={() => navigate(`/invoices/${invoice.id}`)}
                  >
                    <div>
                      <p className="font-medium">{invoice.invoiceNumber}</p>
                      <p className="text-sm text-muted-foreground">
                        {invoice.contact?.name}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="font-medium">{formatCurrency(invoice.total)}</p>
                      <p className="text-sm text-muted-foreground">
                        {formatDate(invoice.issueDate)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <CardDescription>Common tasks</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            <Button
              className="w-full justify-start"
              variant="outline"
              onClick={() => navigate('/contacts')}
            >
              <Plus className="mr-2 h-4 w-4" />
              New Contact
            </Button>
            <Button
              className="w-full justify-start"
              variant="outline"
              onClick={() => navigate('/items')}
            >
              <Plus className="mr-2 h-4 w-4" />
              New Item
            </Button>
            <Button
              className="w-full justify-start"
              onClick={() => navigate('/invoices/new')}
            >
              <Plus className="mr-2 h-4 w-4" />
              New Invoice
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
