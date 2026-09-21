import uuid

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.orm import Session

from app.core.responses import APIResponse
from app.db.session import get_db
from app.models.integration_mapping import CanonicalEntityType
from app.services import integration_webhook_service

router = APIRouter(prefix="/integration-webhooks", tags=["integration-webhooks"])


@router.post("/{integration_id}/{entity_type}", response_model=APIResponse[dict[str, str]])
async def receive_webhook(
    integration_id: uuid.UUID,
    entity_type: CanonicalEntityType,
    request: Request,
    db: Session = Depends(get_db),
    x_webhook_signature: str | None = Header(default=None, alias="X-Webhook-Signature"),
) -> APIResponse[dict[str, str]]:
    """No auth dependency — the per-integration webhook secret IS the
    authentication (HMAC signature over the raw request body), same
    unauthenticated-by-design pattern as app/api/v1/public.py's
    GET /public/price/{product_id}. This is the real external-facing
    ingress the original Phase 10 WebhookAdapter never had — before this,
    "webhook" sync only meant a logged-in platform user POSTing pushed
    records to the authenticated /integrations/{id}/sync endpoint.
    """
    raw_body = await request.body()
    event = integration_webhook_service.receive_webhook(
        db,
        integration_id=integration_id,
        entity_type=entity_type,
        signature_header=x_webhook_signature,
        raw_body=raw_body,
    )
    return APIResponse(data={"event_id": str(event.id), "status": event.status.value})
