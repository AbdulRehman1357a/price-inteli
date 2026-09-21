import hashlib
import hmac
import json
import logging
import uuid

from sqlalchemy.orm import Session

from app.core.crypto import decrypt_credentials, encrypt_credentials
from app.core.exceptions import UnauthorizedError
from app.db.session import SessionLocal
from app.models.integration import Integration
from app.models.integration_mapping import CanonicalEntityType
from app.models.integration_sync_job import (
    IntegrationSyncDirection,
    IntegrationSyncJob,
    IntegrationSyncJobStatus,
    IntegrationSyncJobType,
)
from app.models.integration_webhook_event import IntegrationWebhookEvent, IntegrationWebhookEventStatus
from app.models.mixins import utcnow
from app.repositories.integration_repository import IntegrationRepository
from app.repositories.integration_sync_job_repository import IntegrationSyncJobRepository
from app.repositories.integration_webhook_event_repository import IntegrationWebhookEventRepository
from app.services.integration_service import get_integration

logger = logging.getLogger(__name__)


def list_webhook_events(
    db: Session, *, organization_id: uuid.UUID, integration_id: uuid.UUID, offset: int, limit: int
) -> tuple[list[IntegrationWebhookEvent], int]:
    get_integration(db, organization_id=organization_id, integration_id=integration_id)  # tenant check
    return IntegrationWebhookEventRepository(db).search_for_integration(
        integration_id=integration_id, organization_id=organization_id, offset=offset, limit=limit
    )


def generate_webhook_secret() -> str:
    return uuid.uuid4().hex + uuid.uuid4().hex


def rotate_webhook_secret(db: Session, *, integration: Integration) -> str:
    secret = generate_webhook_secret()
    integration.webhook_secret_encrypted = encrypt_credentials({"secret": secret})
    IntegrationRepository(db).add(integration)
    return secret


def _decrypt_secret(integration: Integration) -> str | None:
    if not integration.webhook_secret_encrypted:
        return None
    return decrypt_credentials(integration.webhook_secret_encrypted).get("secret")


def verify_signature(secret: str, payload_bytes: bytes, signature_header: str | None) -> bool:
    """One generic HMAC-SHA256 scheme for every provider (Phase 10 upgrade
    scope decision — not a per-provider signature dialect). signature_header
    may or may not carry a "sha256=" prefix (Shopify/GitHub-style); both
    forms are accepted.
    """
    if not signature_header:
        return False
    expected = hmac.new(secret.encode(), payload_bytes, hashlib.sha256).hexdigest()
    provided = signature_header.removeprefix("sha256=")
    return hmac.compare_digest(expected, provided)


def receive_webhook(
    db: Session,
    *,
    integration_id: uuid.UUID,
    entity_type: CanonicalEntityType,
    signature_header: str | None,
    raw_body: bytes,
) -> IntegrationWebhookEvent:
    """No tenant/auth check by identity — the per-integration webhook
    secret *is* the authentication for this unauthenticated endpoint (see
    app/api/v1/integration_webhooks.py). entity_type comes from the URL
    path rather than being inferred from the payload, since provider
    payload shapes vary too much to parse generically.
    """
    integration = IntegrationRepository(db).get_by_id(integration_id)
    if integration is None:
        raise UnauthorizedError("Unknown integration.", code="integration_not_found")

    secret = _decrypt_secret(integration)
    signature_valid = bool(secret) and verify_signature(secret, raw_body, signature_header)

    try:
        payload = json.loads(raw_body.decode("utf-8")) if raw_body else {}
    except (ValueError, UnicodeDecodeError):
        payload = {}

    provider_event_id = str(
        payload.get("event_id") or payload.get("id") or hashlib.sha256(raw_body).hexdigest()
    )

    event_repo = IntegrationWebhookEventRepository(db)
    existing = event_repo.get_by_integration_and_event_id(integration_id, provider_event_id)

    if not signature_valid:
        event = event_repo.add(
            IntegrationWebhookEvent(
                id=uuid.uuid4(),
                integration_id=integration_id,
                provider_event_id=provider_event_id,
                entity_type=entity_type,
                payload=payload,
                signature_valid=False,
                status=IntegrationWebhookEventStatus.FAILED,
                error_message="Webhook signature verification failed.",
            )
        )
        db.commit()
        raise UnauthorizedError("Webhook signature verification failed.", code="invalid_webhook_signature")

    if existing is not None:
        existing.status = IntegrationWebhookEventStatus.DUPLICATE
        event_repo.add(existing)
        db.commit()
        return existing

    event = event_repo.add(
        IntegrationWebhookEvent(
            id=uuid.uuid4(),
            integration_id=integration_id,
            provider_event_id=provider_event_id,
            entity_type=entity_type,
            payload=payload,
            signature_valid=True,
            status=IntegrationWebhookEventStatus.RECEIVED,
        )
    )
    db.commit()

    _dispatch(event.id)
    # See integration_sync_service.create_sync_job's comment: the dev-only
    # synchronous fallback processes this event through a different
    # session, so refresh to reflect its real status instead of a stale
    # "received".
    db.refresh(event)
    return event


def _dispatch(event_id: uuid.UUID) -> None:
    from app.services.integration_sync_service import _broker_reachable

    if _broker_reachable():
        try:
            from app.tasks.integrations import process_webhook_event_task

            process_webhook_event_task.delay(str(event_id))
            return
        except Exception:  # noqa: BLE001 — broker went away between the check and the dispatch
            logger.warning("Could not dispatch webhook event %s to Celery.", event_id)
            return

    # Dev-only fallback — see integration_sync_service._dispatch's comment
    # for why: without a reachable broker the event would otherwise sit
    # "received" forever, so process it synchronously here instead. Wrapped
    # in try/except so a failure (e.g. no real DB reachable in a test/CI
    # environment) fails soft rather than bubbling up into the request.
    logger.warning(
        "Redis broker unreachable — processing webhook event %s synchronously instead of leaving "
        "it received (dev-only fallback; production always has a Celery worker available).",
        event_id,
    )
    try:
        process_webhook_event(event_id)
    except Exception:  # noqa: BLE001 — see comment above; leave the event received rather than raise
        logger.warning("Synchronous fallback processing failed for webhook event %s.", event_id)


def process_webhook_event(event_id: uuid.UUID, db: Session | None = None) -> None:
    owns_session = db is None
    session = db if db is not None else SessionLocal()
    try:
        _process(session, event_id)
    finally:
        if owns_session:
            session.close()


def _process(db: Session, event_id: uuid.UUID) -> None:
    from app.services.integration_sync_service import process_sync_job

    event_repo = IntegrationWebhookEventRepository(db)
    event = event_repo.get_by_id(event_id)
    if event is None or event.status != IntegrationWebhookEventStatus.RECEIVED:
        return

    event.status = IntegrationWebhookEventStatus.PROCESSING
    event_repo.add(event)
    db.commit()

    entity_type = event.entity_type or CanonicalEntityType.PRODUCT
    job = IntegrationSyncJobRepository(db).add(
        IntegrationSyncJob(
            id=uuid.uuid4(),
            integration_id=event.integration_id,
            job_type=IntegrationSyncJobType.INCREMENTAL_SYNC,
            entity_type=entity_type,
            status=IntegrationSyncJobStatus.PENDING,
            direction=IntegrationSyncDirection.INBOUND,
            pushed_records=[event.payload],
            correlation_id=event.id,
        )
    )
    event.sync_job_id = job.id
    event_repo.add(event)
    db.commit()

    process_sync_job(job.id, db)

    db.refresh(job)
    event.status = (
        IntegrationWebhookEventStatus.PROCESSED
        if job.status in (IntegrationSyncJobStatus.COMPLETED, IntegrationSyncJobStatus.COMPLETED_WITH_ERRORS)
        else IntegrationWebhookEventStatus.FAILED
    )
    event.processed_at = utcnow()
    if event.status == IntegrationWebhookEventStatus.FAILED and job.error_details:
        event.error_message = str(job.error_details[0].get("message"))
    event_repo.add(event)
    db.commit()
