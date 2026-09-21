import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import CreatedAtMixin, UUIDPrimaryKeyMixin


class OutputJobStatus(enum.StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"  # Phase 14 — only reachable from PENDING, see output_job_service.cancel_job


class OutputJob(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """One dispatch of a product's price to an output channel. payload holds
    the rendered/sent result (e.g. a QR image or PDF label as base64, or the
    ESL simulator's display data) once processing completes.

    idempotency_key, routing_rule_id, and source_price_id are Phase 14
    additions (not in the literal Phase 7 spec): a router-created job (see
    app/services/output_router_service.py) sets all three — the key is
    "price:{price_id}:channel:{channel_id}", unique-indexed, so re-routing
    the same price change never creates a second job for the same channel
    ("implement idempotency to prevent duplicate output execution").
    Manually-dispatched jobs (POST /outputs/jobs) leave all three NULL —
    a human can deliberately re-send the same product/channel combination
    as many times as they want.
    """

    __tablename__ = "output_jobs"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("organizations.id"), nullable=False, index=True
    )
    output_channel_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("output_channels.id"), nullable=False, index=True
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("products.id"), nullable=False, index=True
    )
    store_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("stores.id"), nullable=True
    )
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[OutputJobStatus] = mapped_column(
        Enum(OutputJobStatus, native_enum=False, length=20), nullable=False, default=OutputJobStatus.PENDING
    )
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True, index=True)
    routing_rule_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("output_routing_rules.id"), nullable=True
    )
    source_price_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("prices.id"), nullable=True
    )
