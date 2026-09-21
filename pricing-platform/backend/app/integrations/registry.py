from app.integrations.base import ESLVendorAdapter
from app.integrations.esl_simulator.adapter import ESLSimulatorAdapter

_DEFAULT_ADAPTER = ESLSimulatorAdapter()

_ADAPTERS: dict[str, ESLVendorAdapter] = {
    "esl_simulator": _DEFAULT_ADAPTER,
}


def get_esl_adapter(vendor_code: str) -> ESLVendorAdapter:
    """Phase 8's per-device sync layer (Device Health tab, manual Resync,
    assignment-triggered sync) is a different concern from Phase 9's
    per-vendor API integration layer (app.integrations.esl — test
    connection/discover/push against the real vendor). Phase 8 only ever
    had one real sync implementation (the simulator), so any vendor code
    without a dedicated entry here — including the vendors Phase 9's
    Integration Setup Wizard can create devices for (mock, vusion, etc.) —
    falls back to it rather than failing device creation/health lookups
    outright: day-to-day device-management simulation still works the same
    way regardless of which vendor catalog entry a device belongs to.
    """
    return _ADAPTERS.get(vendor_code, _DEFAULT_ADAPTER)
