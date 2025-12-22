"""
Help Centre Pydantic Schemas

Request/response schemas for FAQ and help article endpoints.
Supports self-service knowledge base functionality.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.schemas.validators import sanitize_text_input


# FAQ Category schemas
class FaqCategoryResponse(BaseModel):
    """Schema for FAQ category response."""
    id: UUID
    name: str
    description: Optional[str]
    icon: Optional[str]
    display_order: int
    is_active: bool
    article_count: int = Field(default=0, description="Number of published articles in category")
    created_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Getting Started",
                "description": "Learn the basics of using the platform",
                "icon": "rocket",
                "display_order": 1,
                "is_active": True,
                "article_count": 12,
                "created_at": "2025-01-01T00:00:00"
            }
        }
    }


class FaqCategoryListResponse(BaseModel):
    """Schema for FAQ category list response."""
    categories: List[FaqCategoryResponse]
    total: int


# FAQ Article schemas
class FaqArticleResponse(BaseModel):
    """Schema for FAQ article response."""
    id: UUID
    category_id: UUID
    category_name: Optional[str] = Field(None, description="Category name for convenience")
    question: str
    answer: str
    keywords: Optional[List[str]] = None
    display_order: int
    is_published: bool
    view_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "category_id": "123e4567-e89b-12d3-a456-426614174001",
                "category_name": "Invoicing",
                "question": "How do I create my first invoice?",
                "answer": "To create your first invoice, navigate to the Invoices section...",
                "keywords": ["invoice", "create", "new", "first"],
                "display_order": 1,
                "is_published": True,
                "view_count": 245,
                "created_at": "2025-01-01T00:00:00",
                "updated_at": "2025-01-01T00:00:00"
            }
        }
    }


class FaqArticleListResponse(BaseModel):
    """Schema for FAQ article list response."""
    articles: List[FaqArticleResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class FaqSearchRequest(BaseModel):
    """Schema for FAQ search request."""
    query: str = Field(..., min_length=2, max_length=200, description="Search query")
    category_id: Optional[UUID] = Field(None, description="Optional category filter")

    @field_validator("query")
    @classmethod
    def sanitize_query(cls, v: str) -> str:
        """Sanitize search query."""
        sanitized = sanitize_text_input(v, allow_html=False)
        if not sanitized or len(sanitized.strip()) < 2:
            raise ValueError("Search query must be at least 2 characters")
        return sanitized


# Help Article schemas
class HelpArticleResponse(BaseModel):
    """Schema for help article response."""
    id: UUID
    slug: str
    title: str
    content: str
    category: str
    tags: Optional[List[str]] = None
    is_published: bool
    view_count: int
    estimated_read_time: int = Field(..., description="Estimated reading time in minutes")
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "slug": "how-to-create-recurring-invoices",
                "title": "How to Create Recurring Invoices",
                "content": "# How to Create Recurring Invoices\n\nRecurring invoices allow you to...",
                "category": "invoicing",
                "tags": ["invoices", "recurring", "automation"],
                "is_published": True,
                "view_count": 1234,
                "estimated_read_time": 5,
                "created_at": "2025-01-01T00:00:00",
                "updated_at": "2025-01-01T00:00:00"
            }
        }
    }


class HelpArticleSummaryResponse(BaseModel):
    """Schema for help article summary (for lists)."""
    id: UUID
    slug: str
    title: str
    category: str
    tags: Optional[List[str]] = None
    is_published: bool
    view_count: int
    estimated_read_time: int
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class HelpArticleListResponse(BaseModel):
    """Schema for help article list response."""
    articles: List[HelpArticleSummaryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class HelpArticleFilters(BaseModel):
    """Filters for help article queries."""
    category: Optional[str] = Field(None, max_length=100, description="Filter by category")
    tag: Optional[str] = Field(None, max_length=50, description="Filter by tag")
    search: Optional[str] = Field(None, max_length=200, description="Search in title/content")
    published_only: bool = Field(default=True, description="Show only published articles")

    @field_validator("search", "category", "tag")
    @classmethod
    def sanitize_text(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize text fields."""
        if v is None:
            return None
        return sanitize_text_input(v, allow_html=False)


# Search result schema (combined FAQ and articles)
class SearchResultItem(BaseModel):
    """Single search result item."""
    id: UUID
    type: str = Field(..., description="Result type: 'faq' or 'article'")
    title: str
    excerpt: str = Field(..., description="Short excerpt from content")
    url: str = Field(..., description="URL to view the full content")
    relevance_score: float = Field(..., description="Search relevance score (0-1)")


class SearchResultsResponse(BaseModel):
    """Combined search results response."""
    results: List[SearchResultItem]
    total: int
    query: str
