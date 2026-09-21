from app.integrations.esl.base import ESLIntegrationAdapter
from app.integrations.esl.mock_adapter import MockVendorAdapter
from app.integrations.esl.mqtt_adapter import MQTTESLAdapter
from app.integrations.esl.pricer_adapter import PricerAdapter
from app.integrations.esl.vendor_stubs import (
    HanshowAdapter,
    SolumAdapter,
    VusionAdapter,
    ZKongAdapter,
)
from app.models.esl_integration import ESLIntegrationType

# integration_type "mock"/"mqtt" are generic mechanisms, independent of
# which vendor catalog entry (device_vendors.code) they're attached to.
# "api" dispatches per-vendor, to the five stub adapters Phase 9 asks the
# framework to be "ready for" — see app/integrations/esl/vendor_stubs.py.
_GENERIC_ADAPTERS: dict[ESLIntegrationType, ESLIntegrationAdapter] = {
    ESLIntegrationType.MOCK: MockVendorAdapter(),
    ESLIntegrationType.MQTT: MQTTESLAdapter(),
}

_VENDOR_API_ADAPTERS: dict[str, ESLIntegrationAdapter] = {
    "vusion": VusionAdapter(),
    "hanshow": HanshowAdapter(),
    "solum": SolumAdapter(),
    "pricer": PricerAdapter(),
    "zkong": ZKongAdapter(),
}


def get_integration_adapter(integration_type: ESLIntegrationType, vendor_code: str) -> ESLIntegrationAdapter:
    if integration_type != ESLIntegrationType.API:
        return _GENERIC_ADAPTERS[integration_type]

    adapter = _VENDOR_API_ADAPTERS.get(vendor_code)
    if adapter is None:
        raise ValueError(f"No API adapter registered for vendor code {vendor_code!r}.")
    return adapter
