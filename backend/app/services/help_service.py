"""
Help Service

Business logic for FAQ and help article operations.
Supports self-service knowledge base functionality.

Security Notes:
- All content is publicly accessible (no business scoping)
- Only published content is shown to users by default
- View count tracking for analytics
"""

from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import select, update, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.faq import FaqCategory, FaqArticle
from app.models.help_article import HelpArticle
from app.schemas.help import HelpArticleFilters


class HelpService:
    """Service for FAQ and help article database operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize help service.

        Args:
            db: Database session
        """
        self.db = db

    # FAQ Category operations
    async def get_faq_categories(
        self,
        active_only: bool = True
    ) -> List[FaqCategory]:
        """
        Get all FAQ categories with article counts.

        Args:
            active_only: Whether to return only active categories

        Returns:
            List of FAQ categories
        """
        query = select(FaqCategory)

        if active_only:
            query = query.where(FaqCategory.is_active == True)

        query = query.options(
            selectinload(FaqCategory.articles)
        ).order_by(FaqCategory.display_order.asc())

        result = await self.db.execute(query)
        categories = result.scalars().all()

        return list(categories)

    async def get_faq_category(
        self,
        category_id: UUID
    ) -> Optional[FaqCategory]:
        """
        Get a single FAQ category by ID.

        Args:
            category_id: Category UUID

        Returns:
            FAQ category or None if not found
        """
        result = await self.db.execute(
            select(FaqCategory)
            .where(FaqCategory.id == category_id)
            .options(selectinload(FaqCategory.articles))
        )
        return result.scalar_one_or_none()

    # FAQ Article operations
    async def get_faq_articles(
        self,
        category_id: Optional[UUID] = None,
        published_only: bool = True,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[FaqArticle], int]:
        """
        Get FAQ articles with optional category filter and pagination.

        Args:
            category_id: Optional category filter
            published_only: Whether to return only published articles
            page: Page number
            page_size: Items per page

        Returns:
            Tuple of (articles, total_count)
        """
        query = select(FaqArticle)

        # Apply filters
        if category_id:
            query = query.where(FaqArticle.category_id == category_id)

        if published_only:
            query = query.where(FaqArticle.is_published == True)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        # Apply pagination and ordering
        query = query.options(
            selectinload(FaqArticle.category)
        ).order_by(
            FaqArticle.display_order.asc(),
            FaqArticle.created_at.desc()
        )
        query = query.offset((page - 1) * page_size).limit(page_size)

        # Execute query
        result = await self.db.execute(query)
        articles = result.scalars().all()

        return list(articles), total

    async def get_faq_article(
        self,
        article_id: UUID
    ) -> Optional[FaqArticle]:
        """
        Get a single FAQ article by ID.

        Args:
            article_id: Article UUID

        Returns:
            FAQ article or None if not found
        """
        result = await self.db.execute(
            select(FaqArticle)
            .where(FaqArticle.id == article_id)
            .options(selectinload(FaqArticle.category))
        )
        return result.scalar_one_or_none()

    async def search_faq(
        self,
        query_text: str,
        category_id: Optional[UUID] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[FaqArticle], int]:
        """
        Search FAQ articles by keywords.

        Args:
            query_text: Search query
            category_id: Optional category filter
            page: Page number
            page_size: Items per page

        Returns:
            Tuple of (articles, total_count)
        """
        # Build search query
        query = select(FaqArticle).where(FaqArticle.is_published == True)

        # Category filter
        if category_id:
            query = query.where(FaqArticle.category_id == category_id)

        # Text search in question, answer, and keywords
        search_term = f"%{query_text}%"
        query = query.where(
            or_(
                FaqArticle.question.ilike(search_term),
                FaqArticle.answer.ilike(search_term),
                FaqArticle.keywords.any(query_text.lower())
            )
        )

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        # Apply pagination and ordering (by view count for relevance)
        query = query.options(
            selectinload(FaqArticle.category)
        ).order_by(
            FaqArticle.view_count.desc(),
            FaqArticle.display_order.asc()
        )
        query = query.offset((page - 1) * page_size).limit(page_size)

        # Execute query
        result = await self.db.execute(query)
        articles = result.scalars().all()

        return list(articles), total

    async def increment_faq_view_count(
        self,
        article_id: UUID
    ) -> bool:
        """
        Increment view count for an FAQ article.

        Args:
            article_id: Article UUID

        Returns:
            True if successful, False if article not found
        """
        result = await self.db.execute(
            update(FaqArticle)
            .where(FaqArticle.id == article_id)
            .values(view_count=FaqArticle.view_count + 1)
        )

        await self.db.commit()

        return result.rowcount > 0

    # Help Article operations
    async def get_help_articles(
        self,
        filters: Optional[HelpArticleFilters] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[HelpArticle], int]:
        """
        Get help articles with filters and pagination.

        Args:
            filters: Optional filters
            page: Page number
            page_size: Items per page

        Returns:
            Tuple of (articles, total_count)
        """
        query = select(HelpArticle)

        # Apply filters
        if filters:
            if filters.published_only:
                query = query.where(HelpArticle.is_published == True)

            if filters.category:
                query = query.where(HelpArticle.category == filters.category)

            if filters.tag:
                query = query.where(HelpArticle.tags.any(filters.tag))

            if filters.search:
                search_term = f"%{filters.search}%"
                query = query.where(
                    or_(
                        HelpArticle.title.ilike(search_term),
                        HelpArticle.content.ilike(search_term),
                        HelpArticle.slug.ilike(search_term)
                    )
                )
        else:
            # Default to published only
            query = query.where(HelpArticle.is_published == True)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        # Apply pagination and ordering (by view count and date)
        query = query.order_by(
            HelpArticle.view_count.desc(),
            HelpArticle.created_at.desc()
        )
        query = query.offset((page - 1) * page_size).limit(page_size)

        # Execute query
        result = await self.db.execute(query)
        articles = result.scalars().all()

        return list(articles), total

    async def get_help_article_by_slug(
        self,
        slug: str,
        published_only: bool = True
    ) -> Optional[HelpArticle]:
        """
        Get a help article by its slug.

        Args:
            slug: Article slug
            published_only: Whether to require published status

        Returns:
            Help article or None if not found
        """
        query = select(HelpArticle).where(HelpArticle.slug == slug)

        if published_only:
            query = query.where(HelpArticle.is_published == True)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_help_article(
        self,
        article_id: UUID,
        published_only: bool = True
    ) -> Optional[HelpArticle]:
        """
        Get a help article by ID.

        Args:
            article_id: Article UUID
            published_only: Whether to require published status

        Returns:
            Help article or None if not found
        """
        query = select(HelpArticle).where(HelpArticle.id == article_id)

        if published_only:
            query = query.where(HelpArticle.is_published == True)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def increment_help_article_view_count(
        self,
        article_id: UUID
    ) -> bool:
        """
        Increment view count for a help article.

        Args:
            article_id: Article UUID

        Returns:
            True if successful, False if article not found
        """
        result = await self.db.execute(
            update(HelpArticle)
            .where(HelpArticle.id == article_id)
            .values(view_count=HelpArticle.view_count + 1)
        )

        await self.db.commit()

        return result.rowcount > 0

    async def get_popular_help_articles(
        self,
        category: Optional[str] = None,
        limit: int = 10
    ) -> List[HelpArticle]:
        """
        Get most popular help articles by view count.

        Args:
            category: Optional category filter
            limit: Number of articles to return

        Returns:
            List of popular help articles
        """
        query = select(HelpArticle).where(HelpArticle.is_published == True)

        if category:
            query = query.where(HelpArticle.category == category)

        query = query.order_by(HelpArticle.view_count.desc()).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_recent_help_articles(
        self,
        category: Optional[str] = None,
        limit: int = 10
    ) -> List[HelpArticle]:
        """
        Get most recently published help articles.

        Args:
            category: Optional category filter
            limit: Number of articles to return

        Returns:
            List of recent help articles
        """
        query = select(HelpArticle).where(HelpArticle.is_published == True)

        if category:
            query = query.where(HelpArticle.category == category)

        query = query.order_by(HelpArticle.created_at.desc()).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_related_articles(
        self,
        article: HelpArticle,
        limit: int = 5
    ) -> List[HelpArticle]:
        """
        Get related articles based on category and tags.

        Args:
            article: Current article
            limit: Number of related articles to return

        Returns:
            List of related articles
        """
        query = select(HelpArticle).where(
            and_(
                HelpArticle.is_published == True,
                HelpArticle.id != article.id
            )
        )

        # Prioritize articles in same category
        query = query.where(HelpArticle.category == article.category)

        # If article has tags, prefer articles with matching tags
        if article.has_tags:
            # This is a simple approach - could be enhanced with tag overlap scoring
            query = query.where(
                or_(*[HelpArticle.tags.any(tag) for tag in article.tags])
            )

        query = query.order_by(
            HelpArticle.view_count.desc()
        ).limit(limit)

        result = await self.db.execute(query)
        related = list(result.scalars().all())

        # If we didn't get enough related articles, fill with popular from same category
        if len(related) < limit:
            additional_query = select(HelpArticle).where(
                and_(
                    HelpArticle.is_published == True,
                    HelpArticle.id != article.id,
                    HelpArticle.category == article.category,
                    HelpArticle.id.not_in([a.id for a in related])
                )
            ).order_by(HelpArticle.view_count.desc()).limit(limit - len(related))

            additional_result = await self.db.execute(additional_query)
            related.extend(list(additional_result.scalars().all()))

        return related[:limit]
