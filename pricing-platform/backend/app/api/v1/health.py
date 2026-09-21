from fastapi import APIRouter

from app.core.config import get_settings
from app.core.responses import APIResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=APIResponse[dict[str, str]])
def health_check() -> APIResponse[dict[str, str]]:
    settings = get_settings()
    return APIResponse(
        data={
            "status": "healthy",
            "service": settings.service_name,
            "version": settings.app_version,
        }
    )
