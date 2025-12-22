import { useState, useMemo } from 'react';
import { Plus, Search, MoreVertical, Edit, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
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
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { useContacts, useDeleteContact } from '@/hooks/useContacts';
import { ContactFormModal } from './ContactFormModal';
import type { Contact, ContactType, ContactStatus, ContactsListParams } from '@/types/contact';
import { DEFAULT_PAGE_SIZE } from '@/lib/constants';

export const ContactsPage = () => {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [contactType, setContactType] = useState<ContactType | 'all'>('all');
  const [status, setStatus] = useState<ContactStatus | 'all'>('all');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedContact, setSelectedContact] = useState<Contact | undefined>();

  const queryParams = useMemo(() => {
    const params: ContactsListParams = { page, limit: DEFAULT_PAGE_SIZE };
    if (search) params.search = search;
    if (contactType !== 'all') params.contactType = contactType;
    if (status !== 'all') params.status = status;
    return params;
  }, [page, search, contactType, status]);

  const { data, isLoading } = useContacts(queryParams);
  const deleteContact = useDeleteContact();

  const handleAddContact = () => {
    setSelectedContact(undefined);
    setIsModalOpen(true);
  };

  const handleEditContact = (contact: Contact) => {
    setSelectedContact(contact);
    setIsModalOpen(true);
  };

  const handleDeleteContact = async (contact: Contact) => {
    if (window.confirm(`Are you sure you want to delete ${contact.name}?`)) {
      await deleteContact.mutateAsync(contact.id);
    }
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedContact(undefined);
  };

  const getContactTypeBadge = (type: ContactType) => {
    const variants: Record<ContactType, 'default' | 'secondary' | 'outline'> = {
      customer: 'default',
      supplier: 'secondary',
      both: 'outline',
    };
    return (
      <Badge variant={variants[type]}>
        {type.charAt(0).toUpperCase() + type.slice(1)}
      </Badge>
    );
  };

  const getStatusBadge = (status: ContactStatus) => {
    return (
      <Badge variant={status === 'active' ? 'default' : 'secondary'}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </Badge>
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-semibold">Contacts</h1>
          <p className="mt-2 text-muted-foreground">
            Manage your customers and suppliers
          </p>
        </div>
        <Button onClick={handleAddContact}>
          <Plus className="mr-2 h-4 w-4" />
          Add Contact
        </Button>
      </div>

      <div className="flex flex-col gap-4 md:flex-row md:items-center">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search by name..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            className="pl-10"
          />
        </div>

        <Select
          value={contactType}
          onValueChange={(value) => {
            setContactType(value as ContactType | 'all');
            setPage(1);
          }}
        >
          <SelectTrigger className="w-full md:w-[180px]">
            <SelectValue placeholder="Filter by type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            <SelectItem value="customer">Customer</SelectItem>
            <SelectItem value="supplier">Supplier</SelectItem>
            <SelectItem value="both">Both</SelectItem>
          </SelectContent>
        </Select>

        <Select
          value={status}
          onValueChange={(value) => {
            setStatus(value as ContactStatus | 'all');
            setPage(1);
          }}
        >
          <SelectTrigger className="w-full md:w-[180px]">
            <SelectValue placeholder="Filter by status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Statuses</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="inactive">Inactive</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Email</TableHead>
              <TableHead>Phone</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="w-[70px]">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              Array.from({ length: 5 }).map((_, index) => (
                <TableRow key={index}>
                  <TableCell>
                    <Skeleton className="h-4 w-32" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="h-4 w-20" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="h-4 w-40" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="h-4 w-32" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="h-4 w-16" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="h-8 w-8" />
                  </TableCell>
                </TableRow>
              ))
            ) : data?.contacts.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-8">
                  <p className="text-muted-foreground">No contacts found</p>
                  <Button variant="link" onClick={handleAddContact} className="mt-2">
                    Create your first contact
                  </Button>
                </TableCell>
              </TableRow>
            ) : (
              data?.contacts.map((contact) => (
                <TableRow key={contact.id}>
                  <TableCell className="font-medium">{contact.name}</TableCell>
                  <TableCell>{getContactTypeBadge(contact.contactType)}</TableCell>
                  <TableCell className="text-muted-foreground">
                    {contact.email || '-'}
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {contact.phone || '-'}
                  </TableCell>
                  <TableCell>{getStatusBadge(contact.status)}</TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon" aria-label="Contact actions">
                          <MoreVertical className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => handleEditContact(contact)}>
                          <Edit className="mr-2 h-4 w-4" />
                          Edit
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          onClick={() => handleDeleteContact(contact)}
                          className="text-destructive"
                        >
                          <Trash2 className="mr-2 h-4 w-4" />
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {data && data.totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Showing {(page - 1) * DEFAULT_PAGE_SIZE + 1} to {Math.min(page * DEFAULT_PAGE_SIZE, data.total)} of{' '}
            {data.total} contacts
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

      <ContactFormModal
        open={isModalOpen}
        onClose={handleCloseModal}
        contact={selectedContact}
      />
    </div>
  );
};
