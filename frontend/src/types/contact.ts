export type ContactType = 'customer' | 'supplier' | 'both';
export type ContactStatus = 'active' | 'inactive';

export interface Contact {
  id: string;
  businessId: string;
  name: string;
  contactType: ContactType;
  email?: string;
  phone?: string;
  kraPin?: string;
  address?: string;
  notes?: string;
  status: ContactStatus;
  createdAt: string;
  updatedAt: string;
  deletedAt?: string;
}

export interface CreateContactRequest {
  name: string;
  contactType: ContactType;
  email?: string;
  phone?: string;
  kraPin?: string;
  address?: string;
  notes?: string;
}

export interface UpdateContactRequest {
  name?: string;
  contactType?: ContactType;
  email?: string;
  phone?: string;
  kraPin?: string;
  address?: string;
  notes?: string;
  status?: ContactStatus;
}

export interface ContactsListParams {
  page?: number;
  limit?: number;
  search?: string;
  contactType?: ContactType;
  status?: ContactStatus;
}

export interface ContactsListResponse {
  contacts: Contact[];
  total: number;
  page: number;
  limit: number;
  totalPages: number;
}
