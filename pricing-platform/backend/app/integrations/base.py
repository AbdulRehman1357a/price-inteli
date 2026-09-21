from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.models.device import Device
    from app.models.integration import Integration
    from app.models.product import Product


class IntegrationAdapter(ABC):
    """Rule: every external integration (ERP, POS, ecommerce/marketplace)
    implements this interface — the Phase 10 Enterprise Integration Hub's
    counterpart to Phase 9's ESLIntegrationAdapter, for pulling canonical
    retail data (app/schemas/canonical.py) rather than pushing device price
    updates. This was a Phase 0 placeholder (connect/sync/health_check)
    with no concrete implementation anywhere in the codebase until now, so
    it's redefined here rather than left alongside a second interface —
    unlike ESLVendorAdapter/ESLIntegrationAdapter in Phase 8/9, there was
    no existing implementation to preserve. Concrete adapters live under
    app/integrations/hub/ (app/integrations/hub/registry.py resolves one by
    Integration.provider) and are never called directly from services —
    services depend on this abstraction so providers can be swapped per
    integration.
    """

    # --- Phase 10 upgrade: capability flags ---
    # Plain (non-abstract) class attributes, not properties — a subclass
    # overrides whichever ones apply. All default to False rather than
    # True so a new adapter is unsupported-by-default until it explicitly
    # declares otherwise (fits "never fake unsupported provider
    # capabilities"). IntegrationOut.capabilities (app/schemas/integration.py)
    # surfaces these to the frontend so the Sync Jobs tab can disable/hide
    # entity-type options the resolved adapter doesn't support.
    supports_product_read: bool = False
    supports_product_write: bool = False
    supports_price_read: bool = False
    supports_price_write: bool = False
    supports_inventory_read: bool = False
    supports_inventory_write: bool = False
    supports_promotion_read: bool = False
    supports_promotion_write: bool = False
    supports_sales_read: bool = False
    supports_webhooks: bool = False
    supports_incremental_sync: bool = False

    @abstractmethod
    def test_connection(self, integration: "Integration", credentials: dict[str, Any]) -> dict[str, Any]:
        """Verifies the stored credentials/configuration actually reach the
        source system. Returns {"success": bool, "message": str | None}.
        """
        ...

    @abstractmethod
    def fetch_records(
        self,
        integration: "Integration",
        credentials: dict[str, Any],
        *,
        entity_type: str,
        records: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        """Returns raw external records (pre-mapping) for one canonical
        entity_type. CSV/REST adapters pull these themselves; the Webhook
        adapter has no way to "pull" (data arrives by push), so its sync
        trigger passes the pushed `records` straight through — see
        app/integrations/hub/webhook_adapter.py.
        """
        ...

    def push_records(
        self,
        integration: "Integration",
        credentials: dict[str, Any],
        *,
        entity_type: str,
        records: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Outbound execution (PIP -> External) — approved-price push, in
        this pass. Concrete (not abstract) so every pre-existing subclass
        keeps working unchanged; the default simply reports "unsupported."
        Only RESTAPIAdapter overrides this with a real implementation —
        every provider stub inherits this default's NotImplementedError
        (which vendor_stubs.py's method still overrides with its own
        explicit "not available" message for a clearer error either way).
        """
        raise NotImplementedError(f"{type(self).__name__} does not support pushing records outward.")


@dataclass
class ESLSyncContext:
    """Everything a vendor adapter needs to push a price update to one
    device, resolved by the caller (app.services.device_sync_service)
    before handing off — an adapter never queries the database directly.
    """

    device: "Device"
    product: "Product"
    price: Decimal
    currency: str
    store_name: str | None


@dataclass
class ESLSyncResult:
    success: bool
    message: str | None = None
    # Simulated telemetry the adapter observed while syncing (battery_level,
    # signal_strength, firmware_version) — merged onto Device by the caller.
    device_status: dict[str, Any] = field(default_factory=dict)


class ESLVendorAdapter(ABC):
    """Rule: every ESL (electronic shelf label) integration goes through this
    vendor abstraction layer so pricing/services code never depends on a
    specific ESL vendor's protocol (e.g. MQTT topic shape). Concrete vendors
    live under app/integrations/<vendor>/ — see
    app/integrations/esl_simulator/adapter.py for the Phase 8 MQTT-based
    simulator (no real hardware/vendor integration yet, per spec).
    """

    @abstractmethod
    def register_device(self, device: "Device") -> None:
        """Called once when a device is first registered with this vendor."""
        ...

    @abstractmethod
    def discover_devices(self) -> list[dict[str, Any]]:
        """Scans for devices this vendor can see but that aren't yet
        registered in our `devices` table. Not wired to any UI in Phase 8
        (the Device Form takes a manually-entered Device Identifier
        instead) — implemented to satisfy the vendor contract for a future
        "auto-discover" flow.
        """
        ...

    @abstractmethod
    def assign_product(self, device: "Device", product: "Product") -> None:
        """Notifies the device-side of a new product assignment (distinct
        from persisting the assignment row, which the service layer does).
        """
        ...

    @abstractmethod
    def unassign_product(self, device: "Device") -> None:
        """Clears whatever the device is currently displaying."""
        ...

    @abstractmethod
    def update_price(self, context: ESLSyncContext) -> ESLSyncResult:
        """Pushes a price update to one device."""
        ...

    @abstractmethod
    def update_template(self, device: "Device", template: dict[str, Any]) -> ESLSyncResult:
        """Pushes a display-layout/template change to one device."""
        ...

    @abstractmethod
    def get_status(self, device: "Device") -> str:
        """Live connectivity status derived from the vendor's own signal
        (e.g. last-seen freshness) — distinct from Device.status, which is
        an administrative state a user sets.
        """
        ...

    @abstractmethod
    def get_health(self, device: "Device") -> dict[str, Any]:
        """Battery/signal/firmware telemetry for the Device Health tab."""
        ...

    @abstractmethod
    def sync_device(self, context: ESLSyncContext) -> ESLSyncResult:
        """Orchestrates a full price sync: update_price() plus whatever
        housekeeping (health refresh, last_seen/last_sync bookkeeping) the
        vendor needs. This is what app.services.device_sync_service calls.
        """
        ...
