import logging
import random
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from app.integrations.base import ESLSyncContext, ESLSyncResult, ESLVendorAdapter
from app.models.device import Device
from app.models.product import Product
from app.services import mqtt_publisher

logger = logging.getLogger(__name__)

_OFFLINE_AFTER = timedelta(minutes=15)


def _as_aware(value: datetime) -> datetime:
    """SQLite (used in tests) drops tzinfo on round-trip even for
    DateTime(timezone=True) columns; MySQL always returns naive values
    already normalized to UTC. Either way, a naive value from the DB means
    UTC — attach tzinfo so it can be compared against an aware `now`. Same
    helper as app.services.price_service._as_aware, duplicated rather than
    imported per this project's preference for independent copies of small
    infra logic over cross-module coupling (see tests/conftest.py).
    """
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


def _simulate_telemetry(device: Device) -> dict[str, Any]:
    """No physical hardware is integrated in this phase — every sync
    simulates plausible battery drain and signal jitter instead.
    """
    current_battery = device.battery_level if device.battery_level is not None else 100
    new_battery = max(0, current_battery - random.randint(0, 2))
    new_signal = max(40, min(100, random.randint(70, 100)))
    return {
        "battery_level": new_battery,
        "signal_strength": new_signal,
        "firmware_version": device.firmware_version or "1.0.0-sim",
    }


class ESLSimulatorAdapter(ESLVendorAdapter):
    """The Phase 8 "ESL Simulator" vendor: publishes real MQTT messages when
    a broker is reachable, and always simulates the device's acknowledgement
    synchronously (there's no physical hardware to actually wait on). This
    is the adapter DeviceVendor(code="esl_simulator") resolves to via
    app.integrations.registry.
    """

    def register_device(self, device: Device) -> None:
        logger.info("Registered simulated ESL device %s (%s)", device.device_name, device.id)

    def discover_devices(self) -> list[dict[str, Any]]:
        return [
            {
                "device_identifier": f"SIM-{uuid.uuid4().hex[:8].upper()}",
                "signal_strength": random.randint(70, 100),
            }
            for _ in range(2)
        ]

    def assign_product(self, device: Device, product: Product) -> None:
        mqtt_publisher.publish_device_update(
            organization_id=device.organization_id,
            store_id=device.store_id,
            device_id=device.id,
            payload={"action": "assign", "product_id": str(product.id), "sku": product.sku},
        )

    def unassign_product(self, device: Device) -> None:
        mqtt_publisher.publish_device_update(
            organization_id=device.organization_id,
            store_id=device.store_id,
            device_id=device.id,
            payload={"action": "clear"},
        )

    def update_price(self, context: ESLSyncContext) -> ESLSyncResult:
        payload = {
            "action": "update_price",
            "product_id": str(context.product.id),
            "product_name": context.product.product_name,
            "sku": context.product.sku,
            "price": str(context.price),
            "currency": context.currency,
            "store_name": context.store_name,
        }
        delivered = mqtt_publisher.publish_device_update(
            organization_id=context.device.organization_id,
            store_id=context.device.store_id,
            device_id=context.device.id,
            payload=payload,
        )
        message = (
            "Acknowledged via MQTT broker."
            if delivered
            else "Acknowledged (simulated locally — no MQTT broker reachable)."
        )
        return ESLSyncResult(success=True, message=message)

    def update_template(self, device: Device, template: dict[str, Any]) -> ESLSyncResult:
        mqtt_publisher.publish_device_update(
            organization_id=device.organization_id,
            store_id=device.store_id,
            device_id=device.id,
            payload={"action": "update_template", "template": template},
        )
        return ESLSyncResult(success=True, message="Template update acknowledged.")

    def get_status(self, device: Device) -> str:
        if device.last_seen_at is None:
            return "offline"
        now = datetime.now(UTC)
        if now - _as_aware(device.last_seen_at) > _OFFLINE_AFTER:
            return "offline"
        return "online"

    def get_health(self, device: Device) -> dict[str, Any]:
        return {
            "battery_level": device.battery_level,
            "signal_strength": device.signal_strength,
            "firmware_version": device.firmware_version,
            "last_seen_at": device.last_seen_at,
            "connectivity": self.get_status(device),
        }

    def sync_device(self, context: ESLSyncContext) -> ESLSyncResult:
        result = self.update_price(context)
        result.device_status = _simulate_telemetry(context.device)
        return result
