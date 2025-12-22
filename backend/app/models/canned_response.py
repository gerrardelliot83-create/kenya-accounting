"""
Canned Response Model

Pre-written response templates for support agents.
Enables quick responses to common support queries.

Use Cases:
- Frequently asked questions
- Standard troubleshooting steps
- Policy explanations
- Greeting and closing messages

Categories:
- greeting: Welcome messages
- billing: Billing-related responses
- technical: Technical support responses
- closing: Closing messages
- general: General purpose responses

Features:
- Title for easy identification
- Full content template
- Category-based organization
- Active/inactive status control
"""

from sqlalchemy import Column, String, Text, Boolean, Index

from app.db.base import Base


class CannedResponse(Base):
    """
    Canned response model for support agent templates.

    Features:
    - Pre-written response templates
    - Category-based organization
    - Active/inactive status control
    - Title for quick reference

    Access Control:
    - Available to all support agents
    - Managed by admin/support team

    Usage:
    - Agents can insert templates into ticket responses
    - Templates can include placeholders (e.g., {{customer_name}})
    - Can be customized before sending
    """

    # Response identification
    title = Column(
        String(200),
        nullable=False,
        index=True,
        comment="Response title for easy identification"
    )

    # Response content
    content = Column(
        Text,
        nullable=False,
        comment="Response content template (supports placeholders)"
    )

    # Organization
    category = Column(
        String(100),
        nullable=False,
        index=True,
        comment="Response category (e.g., 'greeting', 'billing', 'technical')"
    )

    # Visibility
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        comment="Whether response is available for use"
    )

    # Indexes for common queries
    __table_args__ = (
        Index('ix_canned_responses_category_active', 'category', 'is_active'),
        Index('ix_canned_responses_active_title', 'is_active', 'title'),
    )

    def __repr__(self) -> str:
        return f"<CannedResponse(id={self.id}, title={self.title}, category={self.category}, active={self.is_active})>"

    @property
    def has_placeholders(self) -> bool:
        """Check if content contains placeholders."""
        return '{{' in self.content and '}}' in self.content

    @property
    def placeholder_list(self) -> list:
        """Extract list of placeholders from content."""
        import re
        if not self.has_placeholders:
            return []

        # Find all placeholders in format {{placeholder_name}}
        pattern = r'\{\{(\w+)\}\}'
        matches = re.findall(pattern, self.content)
        return list(set(matches))  # Return unique placeholders

    def render(self, **kwargs) -> str:
        """
        Render the template with provided values.

        Args:
            **kwargs: Placeholder values (e.g., customer_name="John")

        Returns:
            Rendered content with placeholders replaced
        """
        content = self.content

        # Replace placeholders
        for key, value in kwargs.items():
            placeholder = f"{{{{{key}}}}}"
            content = content.replace(placeholder, str(value))

        return content

    @property
    def preview(self) -> str:
        """Get a preview of the content (first 100 characters)."""
        if len(self.content) <= 100:
            return self.content
        return f"{self.content[:100]}..."

    @property
    def word_count(self) -> int:
        """Get word count of content."""
        return len(self.content.split())
