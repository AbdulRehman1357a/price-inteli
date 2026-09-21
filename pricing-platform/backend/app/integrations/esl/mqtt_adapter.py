import uuid
from typing import Any

from app.integrations.esl.base import ESLIntegrationAdapter
from app.models.esl_integration import ESLIntegration
from app.services import mqtt_publisher

_SIMULATED_DISCOVERY = [
    {
        "device_identifier": f"MQTT-{uuid.uuid4().hex[:8].upper()}",
        "device_name": "Simulated MQTT Shelf Tag",
        "model_hint": "Generic Simulator Display",
        "status": "online",
    }
]


class MQTTESLAdapter(ESLIntegrationAdapter):
    """Talks to devices over MQTT (app/services/mqtt_publisher.py) — the
    same broker/topic shape as the Phase 8 device-sync flow. Publishing is
    genuinely real when a broker is reachable; test_connection() reports
    that honestly (no broker = a real failure, not a simulated pass).
    Device discovery over MQTT would normally mean subscribing to a
    device-announcement topic and waiting for devices to check in — not
    practical inside a single request/response call — so discover_devices()
    here returns one clearly-labeled simulated device instead, matching the
    Phase 8 "do not integrate physical hardware yet" scope. Price/template
    pushes still simulate the device's acknowledgement synchronously either
    way (see MQTTESLAdapter.push_price), consistent with
    app.integrations.esl_simulator.adapter.ESLSimulatorAdapter.
    """

    async def test_connection(
        self, integration: ESLIntegration, credentials: dict[str, Any]
    ) -> dict[str, Any]:
        del integration, credentials
        if mqtt_publisher.broker_reachable():
            return {"success": True, "message": "MQTT broker is reachable."}
        return {"success": False, "message": "MQTT broker is not reachable."}

    async def discover_devices(
        self, integration: ESLIntegration, credentials: dict[str, Any]
    ) -> dict[str, Any]:
        del integration, credentials
        return {
            "success": True,
            "message": "MQTT discovery is simulated — a real device-announcement topic is not implemented.",
            "devices": _SIMULATED_DISCOVERY,
        }

    async def push_price(
        self,
        integration: ESLIntegration,
        credentials: dict[str, Any],
        *,
        device_identifier: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        del credentials
        # The MQTT topic shape (app.services.mqtt_publisher.build_topic)
        # needs org/store/device UUIDs; this adapter only has a vendor-side
        # device_identifier string, not necessarily our internal Device.id,
        # so store_id (if the caller has one) rides along in payload and a
        # stable synthetic device UUID is derived from the identifier.
        store_id = uuid.UUID(payload["store_id"]) if payload.get("store_id") else integration.organization_id
        delivered = mqtt_publisher.publish_device_update(
            organization_id=integration.organization_id,
            store_id=store_id,
            device_id=uuid.uuid5(uuid.NAMESPACE_URL, device_identifier),
            payload={**payload, "action": "update_price", "device_identifier": device_identifier},
        )
        message = (
            "Acknowledged via MQTT broker."
            if delivered
            else "Acknowledged (simulated locally — no MQTT broker reachable)."
        )
        return {"success": True, "message": message}

    async def push_template(
        self,
        integration: ESLIntegration,
        credentials: dict[str, Any],
        *,
        device_identifier: str,
        template: dict[str, Any],
    ) -> dict[str, Any]:
        del credentials
        mqtt_publisher.publish_device_update(
            organization_id=integration.organization_id,
            store_id=integration.organization_id,
            device_id=uuid.uuid5(uuid.NAMESPACE_URL, device_identifier),
            payload={
                "action": "update_template",
                "device_identifier": device_identifier,
                "template": template,
            },
        )
        return {"success": True, "message": "Template update acknowledged."}

    async def get_device_status(
        self, integration: ESLIntegration, credentials: dict[str, Any], *, device_identifier: str
    ) -> dict[str, Any]:
        del integration, credentials
        return {
            "success": True,
            "message": None,
            "device_identifier": device_identifier,
            "connectivity": "online" if mqtt_publisher.broker_reachable() else "offline",
        }

    async def get_sync_status(
        self, integration: ESLIntegration, credentials: dict[str, Any]
    ) -> dict[str, Any]:
        del credentials
        return {
            "success": True,
            "message": None,
            "integration_id": str(integration.id),
            "status": "healthy" if mqtt_publisher.broker_reachable() else "degraded",
            "last_sync_at": integration.last_sync_at,
        }
