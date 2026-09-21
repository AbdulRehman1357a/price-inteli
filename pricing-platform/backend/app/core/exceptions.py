from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.responses import APIErrorDetail, APIErrorResponse


class AppError(Exception):
    """Base class for expected, domain-level errors raised from services."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    code: str = "app_error"

    def __init__(self, message: str, *, code: str | None = None, status_code: int | None = None):
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code
        if status_code is not None:
            self.status_code = status_code


class UnauthorizedError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    code = "unauthorized"


class NotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "not_found"


class ConflictError(AppError):
    status_code = status.HTTP_409_CONFLICT
    code = "conflict"


class ForbiddenError(AppError):
    status_code = status.HTTP_403_FORBIDDEN
    code = "forbidden"


class ValidationError(AppError):
    """Service-layer validation failure (as opposed to FastAPI's own
    RequestValidationError for malformed request bodies) — e.g. an
    unsupported file type, or an import column mapping that doesn't match
    the uploaded file.
    """

    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    code = "validation_error"


def _error_response(status_code: int, code: str, message: str, field: str | None = None) -> JSONResponse:
    body = APIErrorResponse(error=APIErrorDetail(code=code, message=message, field=field))
    return JSONResponse(status_code=status_code, content=body.model_dump())


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        return _error_response(exc.status_code, exc.code, exc.message)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        first = exc.errors()[0] if exc.errors() else {}
        field = ".".join(str(loc) for loc in first.get("loc", [])) or None
        message = first.get("msg", "Invalid request")
        return _error_response(status.HTTP_422_UNPROCESSABLE_ENTITY, "validation_error", message, field)

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        return _error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR, "internal_error", "An unexpected error occurred."
        )
