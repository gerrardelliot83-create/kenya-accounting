export interface FaqCategory {
  id: string;
  name: string;
  description: string;
  icon?: string;
  article_count: number;
}

export interface FaqArticle {
  id: string;
  category_id: string;
  category_name: string;
  question: string;
  answer: string; // markdown
  keywords: string[];
  view_count: number;
}

export interface HelpArticle {
  id: string;
  slug: string;
  title: string;
  content: string; // markdown
  category: string;
  tags: string[];
  estimated_read_time: number;
  view_count: number;
}

export interface FaqSearchRequest {
  query: string;
  category_id?: string;
}

export interface FaqSearchResponse {
  results: FaqArticle[];
  total: number;
}
