from typing import Any

from app.integrations.esl.base import ESLIntegrationAdapter
from app.models.esl_integration import ESLIntegration

_NOT_AVAILABLE = (
    "{vendor} integration requires a signed partner API/SDK agreement that is not "
    "available in this build. This adapter exists to prove the plugin architecture "
    "is ready to receive a real implementation — it does not claim to talk to {vendor}."
)


class _UnavailableVendorAdapter(ESLIntegrationAdapter):
    """Base for the five named-but-not-yet-available vendors (Vusion,
    Hanshow, SOLUM, Pricer, ZKong — see app/integrations/esl/registry.py).
    Every method fails gracefully and explicitly rather than either raising
    an unhandled exception or, worse, pretending to succeed — per the
    Phase 9 spec: "Do not claim integration with a vendor unless an actual
    supported API/SDK/partner integration is available."
    """

    vendor_display_name: str = "This vendor"

    def _unavailable(self) -> dict[str, Any]:
        return {"success": False, "message": _NOT_AVAILABLE.format(vendor=self.vendor_display_name)}

    async def test_connection(
        self, integration: ESLIntegration, credentials: dict[str, Any]
    ) -> dict[str, Any]:
        del integration, credentials
        return self._unavailable()

    async def discover_devices(
        self, integration: ESLIntegration, credentials: dict[str, Any]
    ) -> dict[str, Any]:
        del integration, credentials
        return {**self._unavailable(), "devices": []}

    async def push_price(
        self,
        integration: ESLIntegration,
        credentials: dict[str, Any],
        *,
        device_identifier: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        del integration, credentials, device_identifier, payload
        return self._unavailable()

    async def push_template(
        self,
        integration: ESLIntegration,
        credentials: dict[str, Any],
        *,
        device_identifier: str,
        template: dict[str, Any],
    ) -> dict[str, Any]:
        del integration, credentials, device_identifier, template
        return self._unavailable()

    async def get_device_status(
        self, integration: ESLIntegration, credentials: dict[str, Any], *, device_identifier: str
    ) -> dict[str, Any]:
        del integration, credentials, device_identifier
        return self._unavailable()

    async def get_sync_status(
        self, integration: ESLIntegration, credentials: dict[str, Any]
    ) -> dict[str, Any]:
        del credentials
        return {**self._unavailable(), "integration_id": str(integration.id)}


class VusionAdapter(_UnavailableVendorAdapter):
    vendor_display_name = "Vusion"


class HanshowAdapter(_UnavailableVendorAdapter):
    vendor_display_name = "Hanshow"


class SolumAdapter(_UnavailableVendorAdapter):
    vendor_display_name = "SOLUM"


class ZKongAdapter(_UnavailableVendorAdapter):
    vendor_display_name = "ZKong"
