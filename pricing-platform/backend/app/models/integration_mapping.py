import enum
import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, String, Uuid, false
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import CreatedAtMixin, UUIDPrimaryKeyMixin


class CanonicalEntityType(enum.StrEnum):
    """The canonical retail entities (app/schemas/canonical.py) an external
    system's fields can be mapped into. ORDER added in the Phase 10
    upgrade for sales/order sync — see CanonicalOrder/CanonicalOrderLine
    and app.models.external_order.ExternalOrder.
    """

    PRODUCT = "product"
    PRICE = "price"
    INVENTORY = "inventory"
    PROMOTION = "promotion"
    STORE = "store"
    ORDER = "order"


class IntegrationMapping(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """One field-mapping rule: this integration's raw `source_field` feeds
    the canonical model's `canonical_field`, optionally passed through
    `transformation_rule` first (app/services/integration_mapping_engine.py).
    No organization_id column per the literal Phase 10 spec — tenant
    scoping joins through integration_id, same as integration_sync_jobs.
    """

    __tablename__ = "integration_mappings"

    integration_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("integrations.id"), nullable=False, index=True
    )
    entity_type: Mapped[CanonicalEntityType] = mapped_column(
        Enum(CanonicalEntityType, native_enum=False, length=20), nullable=False
    )
    source_field: Mapped[str] = mapped_column(String(255), nullable=False)
    canonical_field: Mapped[str] = mapped_column(String(255), nullable=False)
    transformation_rule: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # --- Phase 10 upgrade: Field Mapping Engine table columns ---
    # data_type is a UI/documentation hint only — not enforced at the DB
    # or mapping-engine level (Pydantic already validates the final
    # canonical value's real type when the Canonical* model is built).
    data_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=false())
    # Feeds the mapping engine's existing "default:<fallback>" transformation
    # convention (app/services/integration_mapping_engine.py) without
    # requiring the UI to hand-type that string into transformation_rule.
    default_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # A second mini-DSL entry recognized by apply_transformation, e.g.
    # "regex:^[A-Z0-9]+$" — unrecognized rules still pass through
    # unchanged, same backward-compatible philosophy as transformation_rule.
    validation_rule: Mapped[str | None] = mapped_column(String(255), nullable=True)
