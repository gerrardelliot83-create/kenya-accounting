import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import type { FaqCategory, FaqArticle, HelpArticle, FaqSearchRequest } from '@/types/help';

// FAQ Categories
export const useFaqCategories = () => {
  return useQuery<FaqCategory[]>({
    queryKey: ['faq-categories'],
    queryFn: () => apiClient.getFaqCategories(),
  });
};

// FAQ Articles - with optional category filter
export const useFaqArticles = (categoryId?: string) => {
  return useQuery<FaqArticle[]>({
    queryKey: ['faq-articles', categoryId],
    queryFn: () => apiClient.getFaqArticles(categoryId),
  });
};

// FAQ Search
export const useFaqSearch = (searchRequest: FaqSearchRequest) => {
  return useQuery({
    queryKey: ['faq-search', searchRequest],
    queryFn: () => apiClient.searchFaq(searchRequest),
    enabled: searchRequest.query.length > 0, // Only run when there's a query
  });
};

// Single FAQ Article
export const useFaqArticle = (id: string) => {
  return useQuery<FaqArticle>({
    queryKey: ['faq-article', id],
    queryFn: () => apiClient.getFaqArticle(id),
    enabled: !!id,
  });
};

// Help Articles List
export const useHelpArticles = () => {
  return useQuery<HelpArticle[]>({
    queryKey: ['help-articles'],
    queryFn: () => apiClient.getHelpArticles(),
  });
};

// Single Help Article by slug
export const useHelpArticle = (slug: string) => {
  return useQuery<HelpArticle>({
    queryKey: ['help-article', slug],
    queryFn: () => apiClient.getHelpArticle(slug),
    enabled: !!slug,
  });
};
