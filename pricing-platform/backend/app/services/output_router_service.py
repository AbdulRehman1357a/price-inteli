import logging
import socket
import uuid
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.output_channel import OutputType
from app.models.output_job import OutputJob, OutputJobStatus
from app.models.output_routing_rule import OutputRoutingRule
from app.models.price import Price
from app.models.product import Product
from app.repositories.output_channel_repository import OutputChannelRepository
from app.repositories.output_job_repository import OutputJobRepository
from app.repositories.output_routing_rule_repository import OutputRoutingRuleRepository

logger = logging.getLogger(__name__)


def _rule_matches(rule: OutputRoutingRule, *, product: Product, store_id: uuid.UUID | None) -> bool:
    """Same conditions_json shape as PricingRule.conditions_json
    (app/services/pricing_engine.py) — product_ids/category_ids/store_ids,
    all optional and AND'ed together; an absent/empty key means "no
    restriction on this dimension."
    """
    conditions = rule.conditions_json or {}

    product_ids = conditions.get("product_ids")
    if product_ids and str(product.id) not in {str(p) for p in product_ids}:
        return False

    category_ids = conditions.get("category_ids")
    if category_ids and str(product.category_id) not in {str(c) for c in category_ids}:
        return False

    store_ids = conditions.get("store_ids")
    if store_ids and (store_id is None or str(store_id) not in {str(s) for s in store_ids}):
        return False

    return True


def route_price_change(
    db: Session, *, organization_id: uuid.UUID, product: Product, store_id: uuid.UUID | None, price: Price
) -> list[OutputJob]:
    """The "Execution Event -> Output Router -> Create Output Jobs" step of
    Phase 14's pipeline. Called by app.services.price_service after a price
    create/update that changes selling_price commits successfully.

    Matches every ACTIVE routing rule against this product/store, unions
    the target output types across all matches (a product can be routed by
    more than one matching rule), and creates one idempotency-keyed
    OutputJob per (target output type x active channel of that type
    reachable by this store). Re-routing the exact same price is a no-op
    for any channel that already has a job for it, via the unique
    idempotency_key.
    """
    rules = OutputRoutingRuleRepository(db).list_in_force(organization_id)
    matched_rules = [r for r in rules if _rule_matches(r, product=product, store_id=store_id)]
    if not matched_rules:
        return []

    target_types: dict[OutputType, uuid.UUID] = {}
    for rule in matched_rules:
        for output_type in rule.target_outputs_json:
            target_types.setdefault(OutputType(output_type), rule.id)

    channel_repo = OutputChannelRepository(db)
    job_repo = OutputJobRepository(db)
    created: list[OutputJob] = []

    for output_type, routing_rule_id in target_types.items():
        channels = channel_repo.list_active_by_type(
            organization_id, output_type=output_type, store_id=store_id
        )
        for channel in channels:
            idempotency_key = f"price:{price.id}:channel:{channel.id}"
            if job_repo.get_by_idempotency_key(organization_id, idempotency_key) is not None:
                continue

            job = OutputJob(
                id=uuid.uuid4(),
                organization_id=organization_id,
                output_channel_id=channel.id,
                product_id=product.id,
                store_id=store_id,
                status=OutputJobStatus.PENDING,
                attempts=0,
                idempotency_key=idempotency_key,
                routing_rule_id=routing_rule_id,
                source_price_id=price.id,
            )
            job = job_repo.add(job)
            created.append(job)

    for job in created:
        _dispatch(job.id)
    return created


def _dispatch(job_id: uuid.UUID) -> None:
    if _broker_reachable():
        try:
            from app.tasks.outputs import process_output_job_task

            process_output_job_task.delay(str(job_id))
        except Exception:  # noqa: BLE001 — broker went away between the check and the dispatch
            logger.warning("Could not dispatch routed output job %s to Celery.", job_id)
    else:
        logger.warning(
            "Redis broker unreachable — routed output job %s will stay pending until a worker is available.",
            job_id,
        )


def _broker_reachable(timeout: float = 0.5) -> bool:
    """Deliberately-duplicated copy of output_job_service._broker_reachable,
    matching this project's established preference for independent copies
    of small infra logic over cross-module coupling.
    """
    url = urlparse(get_settings().redis_url)
    try:
        with socket.create_connection((url.hostname or "localhost", url.port or 6379), timeout=timeout):
            return True
    except OSError:
        return False
