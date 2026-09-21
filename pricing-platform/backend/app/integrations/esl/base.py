from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.models.esl_integration import ESLIntegration


class ESLIntegrationAdapter(ABC):
    """The Phase 9 vendor plugin contract: given a stored ESLIntegration
    (connection config) and its already-decrypted credentials, talk to that
    vendor's actual system. Named ESLIntegrationAdapter rather than
    ESLVendorAdapter (the name used in the Phase 9 spec's example) to avoid
    colliding with app.integrations.base.ESLVendorAdapter — Phase 8's
    existing, already-implemented interface for per-device sync operations
    once a device is already registered in our `devices` table. This
    interface operates one level up: testing/discovering/pushing at the
    vendor CONNECTION level, which is what the Integration Setup Wizard
    drives. Same contract shape as the spec's example, same "core
    application must not know vendor-specific details" rule — concrete
    vendors live under app/integrations/esl/, resolved by
    app/integrations/esl/registry.py, and credentials are decrypted once by
    the service layer (app/services/esl_integration_service.py) rather than
    by each adapter, so no adapter implementation ever touches
    app.core.crypto directly.

    Every method returns a plain dict with at least {"success": bool,
    "message": str | None} plus method-specific keys — kept simple rather
    than a proliferation of per-method dataclasses, since every concrete
    adapter (including the 5 vendor stubs) needs to express the same
    "not available" shape uniformly.
    """

    @abstractmethod
    async def test_connection(
        self, integration: "ESLIntegration", credentials: dict[str, Any]
    ) -> dict[str, Any]:
        """Verifies the stored credentials/base_url actually reach the
        vendor. Drives Integration Setup Wizard Step 3.
        """
        ...

    @abstractmethod
    async def discover_devices(
        self, integration: "ESLIntegration", credentials: dict[str, Any]
    ) -> dict[str, Any]:
        """Lists devices visible to this vendor connection that aren't
        necessarily registered in our `devices` table yet — the candidate
        list Wizard Step 4 shows for Step 6 ("Import Devices") to pick
        from. Returns {"success", "message", "devices": [{"device_identifier",
        "device_name", "model_hint", "status"}, ...]}.
        """
        ...

    @abstractmethod
    async def push_price(
        self,
        integration: "ESLIntegration",
        credentials: dict[str, Any],
        *,
        device_identifier: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Pushes a price update to one vendor-side device. Drives Wizard
        Step 8 ("Test Price Update") and any later resync of an imported
        device.
        """
        ...

    @abstractmethod
    async def push_template(
        self,
        integration: "ESLIntegration",
        credentials: dict[str, Any],
        *,
        device_identifier: str,
        template: dict[str, Any],
    ) -> dict[str, Any]:
        """Pushes a display-layout/template change to one vendor-side device."""
        ...

    @abstractmethod
    async def get_device_status(
        self, integration: "ESLIntegration", credentials: dict[str, Any], *, device_identifier: str
    ) -> dict[str, Any]:
        """Live status for one vendor-side device (battery/signal/connectivity,
        vendor-shape dependent).
        """
        ...

    @abstractmethod
    async def get_sync_status(
        self, integration: "ESLIntegration", credentials: dict[str, Any]
    ) -> dict[str, Any]:
        """Overall health/last-sync summary for the whole integration."""
        ...
