"""
Common Pydantic Schemas

Shared schemas used across the application.
"""

from typing import Optional, Any, Generic, TypeVar
from pydantic import BaseModel, Field


# Generic type for data
DataT = TypeVar("DataT")


class HealthCheckResponse(BaseModel):
    """Health check response schema."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    database: str = Field(..., description="Database connection status")
    timestamp: str = Field(..., description="Current server timestamp")


class ErrorResponse(BaseModel):
    """Standard error response schema."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    detail: Optional[Any] = Field(None, description="Additional error details")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")

    model_config = {
        "json_schema_extra": {
            "example": {
                "error": "ValidationError",
                "message": "Invalid input data",
                "detail": {"field": ["Field is required"]},
                "request_id": "abc123"
            }
        }
    }


class SuccessResponse(BaseModel, Generic[DataT]):
    """Generic success response schema."""
    success: bool = Field(default=True, description="Operation success status")
    message: str = Field(..., description="Success message")
    data: Optional[DataT] = Field(None, description="Response data")

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "message": "Operation completed successfully",
                "data": {}
            }
        }
    }


class PaginationParams(BaseModel):
    """Pagination parameters for list endpoints."""
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    sort_by: Optional[str] = Field(None, description="Sort field")
    sort_order: Optional[str] = Field(
        default="asc",
        description="Sort order: asc or desc"
    )

    @property
    def offset(self) -> int:
        """Calculate offset for database query."""
        return (self.page - 1) * self.page_size


class FilterParams(BaseModel):
    """Common filter parameters."""
    search: Optional[str] = Field(None, description="Search term")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    created_after: Optional[str] = Field(None, description="Filter by creation date (ISO format)")
    created_before: Optional[str] = Field(None, description="Filter by creation date (ISO format)")


class MessageResponse(BaseModel):
    """Simple message response."""
    message: str = Field(..., description="Response message")

    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "Operation completed successfully"
            }
        }
    }
