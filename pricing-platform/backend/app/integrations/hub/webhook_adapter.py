from typing import Any

from app.integrations.base import IntegrationAdapter
from app.models.integration import Integration


class WebhookAdapter(IntegrationAdapter):
    """Webhooks are push-based — the external system sends us data, we
    don't poll it. There is nothing to actively "connect" to ahead of time
    (test_connection just confirms a Webhook URL has been configured, since
    that's the only thing we can verify without a live inbound request),
    and fetch_records has nothing to pull: it returns whatever was pushed
    in as `records` when the sync was triggered (see
    app.services.integration_sync_service — the sync request body carries
    the pushed payload straight through to here for a webhook-type
    integration). supports_webhooks=True reflects the real inbound webhook
    receiver (app/api/v1/integration_webhooks.py) now available for this
    provider type; write flags stay False — there's no outbound API to
    push to, only whatever inbound URL was configured.
    """

    supports_product_read = True
    supports_price_read = True
    supports_inventory_read = True
    supports_promotion_read = True
    supports_sales_read = True
    supports_webhooks = True

    def test_connection(self, integration: Integration, credentials: dict[str, Any]) -> dict[str, Any]:
        del integration
        webhook_url = credentials.get("webhook_url")
        if not webhook_url:
            return {"success": False, "message": "No Webhook URL configured."}
        return {
            "success": True,
            "message": f"Webhook URL {webhook_url} is configured. Delivery is verified by pushed records.",
        }

    def fetch_records(
        self,
        integration: Integration,
        credentials: dict[str, Any],
        *,
        entity_type: str,
        records: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        del integration, credentials, entity_type
        return records or []
