"""
FAQ Models

Frequently Asked Questions system for user self-service support.
Two-tier structure: Categories and Articles.

FAQ Structure:
- Categories: High-level groupings (e.g., "Getting Started", "Invoicing")
- Articles: Individual Q&A pairs with search keywords

Features:
- Display ordering for both categories and articles
- Active/published flags for visibility control
- View count tracking for analytics
- Keyword-based search capability
- Icon support for category visualization
"""

from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey, Index, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class FaqCategory(Base):
    """
    FAQ category model for organizing help articles.

    Features:
    - Hierarchical organization of FAQs
    - Custom display order
    - Icon support for UI
    - Active/inactive status control

    Public Access:
    - Categories are publicly accessible (no business scoping)
    - Managed by admin/support team
    """

    # Category information
    name = Column(
        String(200),
        nullable=False,
        unique=True,
        index=True,
        comment="Category name (e.g., 'Getting Started', 'Invoicing')"
    )

    description = Column(
        Text,
        nullable=True,
        comment="Category description"
    )

    icon = Column(
        String(50),
        nullable=True,
        comment="Icon name for UI display"
    )

    # Display and visibility
    display_order = Column(
        Integer,
        nullable=False,
        default=0,
        index=True,
        comment="Display order (lower numbers first)"
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        comment="Whether category is visible to users"
    )

    # Relationships
    articles = relationship(
        "FaqArticle",
        back_populates="category",
        cascade="all, delete-orphan",
        order_by="FaqArticle.display_order"
    )

    # Indexes for common queries
    __table_args__ = (
        Index('ix_faq_categories_active_order', 'is_active', 'display_order'),
    )

    def __repr__(self) -> str:
        return f"<FaqCategory(id={self.id}, name={self.name}, active={self.is_active}, order={self.display_order})>"

    @property
    def article_count(self) -> int:
        """Get count of published articles in this category."""
        return len([a for a in self.articles if a.is_published])


class FaqArticle(Base):
    """
    FAQ article model for individual question-answer pairs.

    Features:
    - Question and markdown-supported answer
    - Keyword array for search optimization
    - Display ordering within category
    - Published/draft status
    - View count tracking

    Public Access:
    - Articles are publicly accessible (no business scoping)
    - Managed by admin/support team

    Search Optimization:
    - Keywords array for fast full-text search
    - View count for popularity ranking
    """

    # Category association
    category_id = Column(
        UUID(as_uuid=True),
        ForeignKey("faq_categories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent FAQ category"
    )

    # Question and answer
    question = Column(
        Text,
        nullable=False,
        comment="FAQ question"
    )

    answer = Column(
        Text,
        nullable=False,
        comment="FAQ answer (supports markdown)"
    )

    # Search optimization
    keywords = Column(
        ARRAY(Text),
        nullable=True,
        comment="Search keywords for article discovery"
    )

    # Display and visibility
    display_order = Column(
        Integer,
        nullable=False,
        default=0,
        index=True,
        comment="Display order within category (lower numbers first)"
    )

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

    # Relationships
    category = relationship(
        "FaqCategory",
        back_populates="articles"
    )

    # Indexes for common queries
    __table_args__ = (
        Index('ix_faq_articles_category_order', 'category_id', 'display_order'),
        Index('ix_faq_articles_category_published', 'category_id', 'is_published'),
        Index('ix_faq_articles_published_views', 'is_published', 'view_count'),
    )

    def __repr__(self) -> str:
        return f"<FaqArticle(id={self.id}, question={self.question[:50]}..., views={self.view_count})>"

    def increment_view_count(self) -> None:
        """Increment the view count for this article."""
        self.view_count += 1

    @property
    def has_keywords(self) -> bool:
        """Check if article has search keywords."""
        return self.keywords is not None and len(self.keywords) > 0

    @property
    def keyword_string(self) -> str:
        """Get keywords as comma-separated string."""
        if not self.has_keywords:
            return ""
        return ", ".join(self.keywords)
