export type ItemType = 'product' | 'service';
export type ItemStatus = 'active' | 'inactive';

export interface Item {
  id: string;
  businessId: string;
  name: string;
  itemType: ItemType;
  description?: string;
  sku?: string;
  unitPrice: number;
  taxRate: number;
  status: ItemStatus;
  createdAt: string;
  updatedAt: string;
  deletedAt?: string;
}

export interface CreateItemRequest {
  name: string;
  itemType: ItemType;
  description?: string;
  sku?: string;
  unitPrice: number;
  taxRate?: number;
}

export interface UpdateItemRequest {
  name?: string;
  itemType?: ItemType;
  description?: string;
  sku?: string;
  unitPrice?: number;
  taxRate?: number;
  status?: ItemStatus;
}

export interface ItemsListParams {
  page?: number;
  limit?: number;
  search?: string;
  itemType?: ItemType;
  status?: ItemStatus;
}

export interface ItemsListResponse {
  items: Item[];
  total: number;
  page: number;
  limit: number;
  totalPages: number;
}
