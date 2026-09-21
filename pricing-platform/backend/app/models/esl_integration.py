import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class ESLIntegrationType(enum.StrEnum):
    """The transport/mechanism a given integration uses — independent of
    which vendor it's for (device_vendors.id): MOCK always succeeds (for
    testing the wizard end-to-end without real credentials), MQTT talks to
    an MQTT broker (app/services/mqtt_publisher.py), API is a real
    vendor REST/SDK integration.
    """

    MOCK = "mock"
    MQTT = "mqtt"
    API = "api"


class ESLIntegrationStatus(enum.StrEnum):
    PENDING = "pending"  # created, test_connection not yet run/passed
    ACTIVE = "active"
    ERROR = "error"
    INACTIVE = "inactive"


class ESLIntegration(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One tenant's configured connection to an ESL vendor — distinct from
    device_vendors (the global hardware catalog) and devices (individual
    registered devices, see app/models/device.py). configuration_encrypted
    holds vendor credentials as Fernet ciphertext (app/core/crypto.py) —
    never decrypted back out through the API (see ESLIntegrationOut).
    """

    __tablename__ = "esl_integrations"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("organizations.id"), nullable=False, index=True
    )
    # Nullable at the DB level (migration safety for any pre-existing rows),
    # but required one layer up by ESLIntegrationCreate — one integration
    # is set up for exactly one store, and its devices inherit this store
    # instead of asking for one again per-device/per-import (see
    # app/services/esl_integration_service.py, app/services/device_service.py).
    store_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("stores.id"), nullable=True, index=True
    )
    vendor_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("device_vendors.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    integration_type: Mapped[ESLIntegrationType] = mapped_column(
        Enum(ESLIntegrationType, native_enum=False, length=20), nullable=False
    )
    base_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    configuration_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ESLIntegrationStatus] = mapped_column(
        Enum(ESLIntegrationStatus, native_enum=False, length=20),
        nullable=False,
        default=ESLIntegrationStatus.PENDING,
    )
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
