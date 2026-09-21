import json
import logging
import socket
import uuid
from typing import Any

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def build_topic(organization_id: uuid.UUID, store_id: uuid.UUID, device_id: uuid.UUID) -> str:
    prefix = get_settings().mqtt_topic_prefix
    return f"{prefix}/{organization_id}/store/{store_id}/device/{device_id}/update"


def broker_reachable() -> bool:
    """Public reachability check against the configured broker — used by
    app.integrations.esl.mqtt_adapter.MQTTESLAdapter.test_connection() for
    a genuine (not simulated) pass/fail, unlike the always-successful
    acknowledgement path used elsewhere for actual device syncs.
    """
    settings = get_settings()
    return _broker_reachable(settings.mqtt_broker_host, settings.mqtt_broker_port)


def publish_device_update(
    *, organization_id: uuid.UUID, store_id: uuid.UUID, device_id: uuid.UUID, payload: dict[str, Any]
) -> bool:
    """The FastAPI MQTT publisher service. Best-effort, one-shot publish —
    mirrors the Celery/Redis broker-reachability pre-check used elsewhere
    (app.services.import_service._broker_reachable /
    app.services.output_job_service._broker_reachable): if no MQTT broker
    is reachable, logs a warning and returns False rather than blocking a
    request. The ESL simulator adapter treats this as informational only —
    it simulates the device's acknowledgement synchronously either way,
    since there's no physical hardware to wait on (see
    app/integrations/esl_simulator/adapter.py).
    """
    topic = build_topic(organization_id, store_id, device_id)
    settings = get_settings()
    if not _broker_reachable(settings.mqtt_broker_host, settings.mqtt_broker_port):
        logger.warning("MQTT broker unreachable — skipping publish to %s", topic)
        return False

    try:
        import paho.mqtt.publish as mqtt_publish

        mqtt_publish.single(
            topic,
            payload=json.dumps(payload, default=str),
            hostname=settings.mqtt_broker_host,
            port=settings.mqtt_broker_port,
            client_id=f"rpip-publisher-{uuid.uuid4()}",
        )
        return True
    except Exception:  # noqa: BLE001 — publish failures must never break the request
        logger.exception("Failed to publish MQTT update to %s", topic)
        return False


def _broker_reachable(host: str, port: int, timeout: float = 0.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False
