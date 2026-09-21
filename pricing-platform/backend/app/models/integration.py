import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class IntegrationCategory(enum.StrEnum):
    """Business classification (Integration UI's "Category*" field) —
    independent of `provider`, which selects the actual adapter mechanism.
    """

    ERP = "erp"
    POS = "pos"
    ECOMMERCE = "ecommerce"
    MARKETPLACE = "marketplace"
    CUSTOM = "custom"


class IntegrationProvider(enum.StrEnum):
    """Selects the concrete adapter (app/integrations/hub/registry.py).
    CSV/REST_API/WEBHOOK are fully implemented; SAP/ORACLE/SQUARE/CLOVER/
    SHOPIFY/LIGHTSPEED/TOAST/MICROSOFT_DYNAMICS/NETSUITE are catalog
    entries only — every call on their adapter fails with an explicit
    "not available" message (app/integrations/hub/vendor_stubs.py), per
    "do not claim production compatibility with a provider unless its
    required API/SDK/documentation has been verified" (Phase 10 upgrade
    spec). Each still declares realistic IntegrationAdapter capability
    flags so the UI can honestly describe what the provider *would*
    support once a real integration exists.
    """

    CSV = "csv"
    REST_API = "rest_api"
    WEBHOOK = "webhook"
    SAP = "sap"
    ORACLE = "oracle"
    SQUARE = "square"
    CLOVER = "clover"
    SHOPIFY = "shopify"
    LIGHTSPEED = "lightspeed"
    TOAST = "toast"
    MICROSOFT_DYNAMICS = "microsoft_dynamics"
    NETSUITE = "netsuite"


class IntegrationStatus(enum.StrEnum):
    PENDING = "pending"
    ACTIVE = "active"
    ERROR = "error"
    INACTIVE = "inactive"


class IntegrationEnvironment(enum.StrEnum):
    SANDBOX = "sandbox"
    PRODUCTION = "production"


class Integration(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One tenant's configured connection to an external ERP/POS/ecommerce
    system — the Enterprise Integration Hub's counterpart to Phase 9's
    ESLIntegration, for non-ESL data (products, prices, inventory,
    promotions, stores instead of device price pushes).
    configuration_encrypted holds credentials as Fernet ciphertext
    (app/core/crypto.py, reused as-is from Phase 9) — never decrypted back
    out through the API (see IntegrationOut).
    """

    __tablename__ = "integrations"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("organizations.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    integration_category: Mapped[IntegrationCategory] = mapped_column(
        Enum(IntegrationCategory, native_enum=False, length=20), nullable=False
    )
    provider: Mapped[IntegrationProvider] = mapped_column(
        Enum(IntegrationProvider, native_enum=False, length=20), nullable=False
    )
    status: Mapped[IntegrationStatus] = mapped_column(
        Enum(IntegrationStatus, native_enum=False, length=20),
        nullable=False,
        default=IntegrationStatus.PENDING,
    )
    configuration_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # --- Phase 10 upgrade: connection-management/onboarding metadata ---
    # provider_version/base_url_display/auth_type are deliberately plain
    # text, not part of configuration_encrypted — they're read by the UI
    # (connection status, Setup Checklist) without ever decrypting
    # credentials; base_url_display/auth_type are non-secret copies the
    # service layer keeps in sync with the corresponding encrypted
    # credential keys at create/update time.
    provider_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    environment: Mapped[IntegrationEnvironment] = mapped_column(
        Enum(IntegrationEnvironment, native_enum=False, length=20),
        nullable=False,
        default=IntegrationEnvironment.PRODUCTION,
        server_default=IntegrationEnvironment.PRODUCTION.name,
    )
    base_url_display: Mapped[str | None] = mapped_column(String(500), nullable=True)
    auth_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    last_successful_connection_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_failed_connection_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_connection_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Reserved for a future OAuth token-refresh flow — unused by the
    # CSV/REST/Webhook adapters and every provider stub in this pass.
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Fernet ciphertext (app/core/crypto.py), the HMAC signing secret the
    # webhook receiver (app/api/v1/integration_webhooks.py) verifies
    # inbound payloads against — separate from configuration_encrypted so
    # rotating it doesn't touch the adapter's own credentials.
    webhook_secret_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
