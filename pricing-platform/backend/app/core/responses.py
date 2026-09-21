from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Consistent success envelope returned by every /api/v1 endpoint."""

    success: bool = True
    data: T | None = None
    meta: dict[str, Any] | None = None


class APIErrorDetail(BaseModel):
    code: str
    message: str
    field: str | None = None


class APIErrorResponse(BaseModel):
    """Consistent error envelope returned by every /api/v1 endpoint."""

    success: bool = False
    error: APIErrorDetail
