"""
Help Article Model

Comprehensive how-to guides and documentation articles.
Supports full markdown content for rich formatting.

Article Structure:
- Slug-based URLs for SEO-friendly access
- Category-based organization
- Tag-based cross-referencing
- View count tracking for analytics

Use Cases:
- Step-by-step tutorials
- Feature documentation
- Best practices guides
- Video transcripts

Public Access:
- Articles are publicly accessible (no business scoping)
- Managed by admin/content team
"""

from sqlalchemy import Column, String, Text, Boolean, Integer, Index, ARRAY
from sqlalchemy.orm import validates

from app.db.base import Base


class HelpArticle(Base):
    """
    Help article model for comprehensive documentation.

    Features:
    - SEO-friendly slug-based URLs
    - Full markdown content support
    - Category-based organization
    - Tag-based search and cross-referencing
    - Published/draft status
    - View count analytics

    Public Access:
    - Articles are publicly accessible (no business scoping)
    - Managed by admin/content team

    URL Structure:
    - /help/{slug} - e.g., /help/how-to-create-invoice
    """

    # URL and identification
    slug = Column(
        String(200),
        nullable=False,
        unique=True,
        index=True,
        comment="URL-friendly identifier (e.g., 'how-to-create-invoice')"
    )

    title = Column(
        String(500),
        nullable=False,
        index=True,
        comment="Article title"
    )

    # Content
    content = Column(
        Text,
        nullable=False,
        comment="Article content (markdown format)"
    )

    # Organization
    category = Column(
        String(100),
        nullable=False,
        index=True,
        comment="Article category (e.g., 'invoicing', 'expenses', 'banking')"
    )

    tags = Column(
        ARRAY(String(50)),
        nullable=True,
        comment="Tags for search and cross-referencing"
    )

    # Visibility
    is_published = Column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        comment="Whether article is visible to users"
    )

    # Analytics
    view_count = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of times article has been viewed"
    )

    # Indexes for common queries
    __table_args__ = (
        Index('ix_help_articles_category_published', 'category', 'is_published'),
        Index('ix_help_articles_published_views', 'is_published', 'view_count'),
    )

    @validates('slug')
    def validate_slug(self, key, slug):
        """Validate that slug is URL-friendly."""
        if not slug:
            raise ValueError("Slug cannot be empty")

        # Check for valid slug format (lowercase, hyphens, alphanumeric)
        import re
        if not re.match(r'^[a-z0-9-]+$', slug):
            raise ValueError("Slug must contain only lowercase letters, numbers, and hyphens")

        return slug

    def __repr__(self) -> str:
        return f"<HelpArticle(id={self.id}, slug={self.slug}, category={self.category}, views={self.view_count})>"

    def increment_view_count(self) -> None:
        """Increment the view count for this article."""
        self.view_count += 1

    @property
    def has_tags(self) -> bool:
        """Check if article has tags."""
        return self.tags is not None and len(self.tags) > 0

    @property
    def tag_string(self) -> str:
        """Get tags as comma-separated string."""
        if not self.has_tags:
            return ""
        return ", ".join(self.tags)

    @property
    def url_path(self) -> str:
        """Get the URL path for this article."""
        return f"/help/{self.slug}"

    @property
    def word_count(self) -> int:
        """Estimate word count in content."""
        if not self.content:
            return 0
        return len(self.content.split())

    @property
    def estimated_read_time(self) -> int:
        """Estimate reading time in minutes (assuming 200 words/minute)."""
        words = self.word_count
        if words == 0:
            return 0
        return max(1, round(words / 200))
