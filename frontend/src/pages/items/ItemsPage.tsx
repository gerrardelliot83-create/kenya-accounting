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
import { useItems, useDeleteItem } from '@/hooks/useItems';
import { ItemFormModal } from './ItemFormModal';
import type { Item, ItemType, ItemStatus, ItemsListParams } from '@/types/item';
import { formatCurrency } from '@/lib/formatters';
import { DEFAULT_PAGE_SIZE } from '@/lib/constants';

export const ItemsPage = () => {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [itemType, setItemType] = useState<ItemType | 'all'>('all');
  const [status, setStatus] = useState<ItemStatus | 'all'>('all');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedItem, setSelectedItem] = useState<Item | undefined>();

  const queryParams = useMemo(() => {
    const params: ItemsListParams = { page, limit: DEFAULT_PAGE_SIZE };
    if (search) params.search = search;
    if (itemType !== 'all') params.itemType = itemType;
    if (status !== 'all') params.status = status;
    return params;
  }, [page, search, itemType, status]);

  const { data, isLoading } = useItems(queryParams);
  const deleteItem = useDeleteItem();

  const handleAddItem = () => {
    setSelectedItem(undefined);
    setIsModalOpen(true);
  };

  const handleEditItem = (item: Item) => {
    setSelectedItem(item);
    setIsModalOpen(true);
  };

  const handleDeleteItem = async (item: Item) => {
    if (window.confirm(`Are you sure you want to delete ${item.name}?`)) {
      await deleteItem.mutateAsync(item.id);
    }
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedItem(undefined);
  };

  const getItemTypeBadge = (type: ItemType) => {
    const variant = type === 'product' ? 'default' : 'secondary';
    return (
      <Badge variant={variant}>
        {type.charAt(0).toUpperCase() + type.slice(1)}
      </Badge>
    );
  };

  const getStatusBadge = (status: ItemStatus) => {
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
          <h1 className="text-3xl font-semibold">Items</h1>
          <p className="mt-2 text-muted-foreground">
            Manage your products and services catalog
          </p>
        </div>
        <Button onClick={handleAddItem}>
          <Plus className="mr-2 h-4 w-4" />
          Add Item
        </Button>
      </div>

      <div className="flex flex-col gap-4 md:flex-row md:items-center">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search by name or SKU..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            className="pl-10"
          />
        </div>

        <Select
          value={itemType}
          onValueChange={(value) => {
            setItemType(value as ItemType | 'all');
            setPage(1);
          }}
        >
          <SelectTrigger className="w-full md:w-[180px]">
            <SelectValue placeholder="Filter by type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            <SelectItem value="product">Product</SelectItem>
            <SelectItem value="service">Service</SelectItem>
          </SelectContent>
        </Select>

        <Select
          value={status}
          onValueChange={(value) => {
            setStatus(value as ItemStatus | 'all');
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
              <TableHead>SKU</TableHead>
              <TableHead>Unit Price</TableHead>
              <TableHead>Tax Rate</TableHead>
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
                    <Skeleton className="h-4 w-24" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="h-4 w-20" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="h-4 w-16" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="h-4 w-16" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="h-8 w-8" />
                  </TableCell>
                </TableRow>
              ))
            ) : data?.items.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="text-center py-8">
                  <p className="text-muted-foreground">No items found</p>
                  <Button variant="link" onClick={handleAddItem} className="mt-2">
                    Create your first item
                  </Button>
                </TableCell>
              </TableRow>
            ) : (
              data?.items.map((item) => (
                <TableRow key={item.id}>
                  <TableCell className="font-medium">{item.name}</TableCell>
                  <TableCell>{getItemTypeBadge(item.itemType)}</TableCell>
                  <TableCell className="text-muted-foreground">
                    {item.sku || '-'}
                  </TableCell>
                  <TableCell>{formatCurrency(item.unitPrice)}</TableCell>
                  <TableCell>{item.taxRate}%</TableCell>
                  <TableCell>{getStatusBadge(item.status)}</TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon" aria-label="Item actions">
                          <MoreVertical className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => handleEditItem(item)}>
                          <Edit className="mr-2 h-4 w-4" />
                          Edit
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          onClick={() => handleDeleteItem(item)}
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
            {data.total} items
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

      <ItemFormModal
        open={isModalOpen}
        onClose={handleCloseModal}
        item={selectedItem}
      />
    </div>
  );
};
