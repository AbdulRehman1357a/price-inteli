from typing import Any

from app.integrations.esl.base import ESLIntegrationAdapter
from app.models.esl_integration import ESLIntegration

_MOCK_DEVICES = [
    {
        "device_identifier": "MOCK-001",
        "device_name": "Mock Shelf Tag 1",
        "model_hint": "Generic",
        "status": "online",
    },
    {
        "device_identifier": "MOCK-002",
        "device_name": "Mock Shelf Tag 2",
        "model_hint": "Generic",
        "status": "online",
    },
    {
        "device_identifier": "MOCK-003",
        "device_name": "Mock Shelf Tag 3",
        "model_hint": "Generic",
        "status": "offline",
    },
]


class MockVendorAdapter(ESLIntegrationAdapter):
    """A canned, always-succeeds adapter with no external dependency (no
    broker, no real vendor account) — lets the entire 8-step Integration
    Setup Wizard be exercised end-to-end for testing/demos regardless of
    which real vendor integrations are actually available yet.
    """

    async def test_connection(
        self, integration: ESLIntegration, credentials: dict[str, Any]
    ) -> dict[str, Any]:
        del integration, credentials
        return {"success": True, "message": "Mock connection established."}

    async def discover_devices(
        self, integration: ESLIntegration, credentials: dict[str, Any]
    ) -> dict[str, Any]:
        del integration, credentials
        return {"success": True, "message": None, "devices": _MOCK_DEVICES}

    async def push_price(
        self,
        integration: ESLIntegration,
        credentials: dict[str, Any],
        *,
        device_identifier: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        del integration, credentials
        return {
            "success": True,
            "message": f"Mock price pushed to {device_identifier}.",
            "acknowledged_payload": payload,
        }

    async def push_template(
        self,
        integration: ESLIntegration,
        credentials: dict[str, Any],
        *,
        device_identifier: str,
        template: dict[str, Any],
    ) -> dict[str, Any]:
        del integration, credentials, template
        return {"success": True, "message": f"Mock template pushed to {device_identifier}."}

    async def get_device_status(
        self, integration: ESLIntegration, credentials: dict[str, Any], *, device_identifier: str
    ) -> dict[str, Any]:
        del integration, credentials
        return {
            "success": True,
            "message": None,
            "device_identifier": device_identifier,
            "battery_level": 87,
            "signal_strength": 92,
            "connectivity": "online",
        }

    async def get_sync_status(
        self, integration: ESLIntegration, credentials: dict[str, Any]
    ) -> dict[str, Any]:
        del credentials
        return {
            "success": True,
            "message": None,
            "integration_id": str(integration.id),
            "status": "healthy",
            "last_sync_at": integration.last_sync_at,
        }
