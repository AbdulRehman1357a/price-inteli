import enum
import uuid
from decimal import Decimal

from sqlalchemy import Enum, ForeignKey, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import CreatedAtMixin, UUIDPrimaryKeyMixin


class AdjustmentType(enum.StrEnum):
    INCREASE = "increase"
    DECREASE = "decrease"
    CORRECTION = "correction"


class InventoryAdjustment(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """Audit trail for every stock adjustment applied through
    POST /api/v1/inventory/bulk-update. Not in the Phase 4 DB spec, but
    added so the adjustment form's required Reason/Notes fields land
    somewhere durable — per the project's "maintain audit logs for
    important changes" rule, a quantity_on_hand change is exactly that.
    Not yet exposed through its own read API/UI; a future phase can add a
    "view adjustment history" endpoint against this table.
    """

    __tablename__ = "inventory_adjustments"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("organizations.id"), nullable=False, index=True
    )
    inventory_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("inventory.id"), nullable=False, index=True
    )
    adjustment_type: Mapped[AdjustmentType] = mapped_column(
        Enum(AdjustmentType, native_enum=False, length=20), nullable=False
    )
    adjustment_quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    quantity_before: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    quantity_after: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("users.id"), nullable=True
    )
