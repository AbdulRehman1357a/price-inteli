from typing import Any

from app.integrations.base import IntegrationAdapter
from app.models.integration import Integration

_NOT_AVAILABLE = (
    "{provider} integration requires a signed partner API/SDK agreement that is not "
    "available in this build. Selecting {provider} registers the framework's readiness "
    "to support it — it does not claim to talk to {provider} yet, per the Phase 10 spec: "
    '"do not claim production compatibility with a provider unless its required '
    'API/SDK/documentation has been verified."'
)


class _UnavailableProviderAdapter(IntegrationAdapter):
    """Base for every provider catalog entry with no real implementation
    (SAP, Oracle, and the Phase 10 upgrade's Square/Clover/Shopify/
    Lightspeed/Toast/Microsoft Dynamics/NetSuite). Same honesty pattern as
    Phase 9's ESL vendor stubs: every method fails explicitly rather than
    silently succeeding. Subclasses still declare realistic
    IntegrationAdapter capability flags (based on each platform's
    genuinely public API shape) — the flags describe what the framework
    is *ready* to support once a real integration exists; they are not a
    claim that this build can actually talk to the provider. No stub here
    fabricates mock/canned response data.
    """

    provider_display_name: str = "This provider"

    def _unavailable(self) -> dict[str, Any]:
        return {"success": False, "message": _NOT_AVAILABLE.format(provider=self.provider_display_name)}

    def test_connection(self, integration: Integration, credentials: dict[str, Any]) -> dict[str, Any]:
        del integration, credentials
        return self._unavailable()

    def fetch_records(
        self,
        integration: Integration,
        credentials: dict[str, Any],
        *,
        entity_type: str,
        records: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        del integration, credentials, entity_type, records
        raise NotImplementedError(_NOT_AVAILABLE.format(provider=self.provider_display_name))

    def push_records(
        self,
        integration: Integration,
        credentials: dict[str, Any],
        *,
        entity_type: str,
        records: list[dict[str, Any]],
    ) -> dict[str, Any]:
        del integration, credentials, entity_type, records
        raise NotImplementedError(_NOT_AVAILABLE.format(provider=self.provider_display_name))


class SAPAdapter(_UnavailableProviderAdapter):
    provider_display_name = "SAP"
    supports_product_read = True
    supports_product_write = True
    supports_price_read = True
    supports_price_write = True
    supports_inventory_read = True
    supports_inventory_write = True
    supports_promotion_read = True
    supports_promotion_write = True
    supports_sales_read = True
    supports_webhooks = True
    supports_incremental_sync = True


class OracleAdapter(_UnavailableProviderAdapter):
    provider_display_name = "Oracle"
    supports_product_read = True
    supports_product_write = True
    supports_price_read = True
    supports_price_write = True
    supports_inventory_read = True
    supports_inventory_write = True
    supports_promotion_read = True
    supports_promotion_write = True
    supports_sales_read = True
    supports_webhooks = True
    supports_incremental_sync = True


class SquareAdapter(_UnavailableProviderAdapter):
    """Square's real Connect API supports product/price/inventory
    read+write, promotion read only (no first-class promotions-write
    endpoint), sales read, and genuine webhooks — per Square's public
    developer documentation. This build does not talk to Square.
    """

    provider_display_name = "Square"
    supports_product_read = True
    supports_product_write = True
    supports_price_read = True
    supports_price_write = True
    supports_inventory_read = True
    supports_inventory_write = True
    supports_promotion_read = True
    supports_sales_read = True
    supports_webhooks = True
    supports_incremental_sync = True


class CloverAdapter(_UnavailableProviderAdapter):
    """Clover's REST API supports product/price/inventory read+write and
    webhooks, but has no first-class promotions API. This build does not
    talk to Clover.
    """

    provider_display_name = "Clover"
    supports_product_read = True
    supports_product_write = True
    supports_price_read = True
    supports_price_write = True
    supports_inventory_read = True
    supports_inventory_write = True
    supports_sales_read = True
    supports_webhooks = True
    supports_incremental_sync = True


class ShopifyAdapter(_UnavailableProviderAdapter):
    """Shopify's Admin API supports product/price/inventory/promotion
    (price rules/discounts) read+write and genuine webhooks. This build
    does not talk to Shopify.
    """

    provider_display_name = "Shopify"
    supports_product_read = True
    supports_product_write = True
    supports_price_read = True
    supports_price_write = True
    supports_inventory_read = True
    supports_inventory_write = True
    supports_promotion_read = True
    supports_promotion_write = True
    supports_sales_read = True
    supports_webhooks = True
    supports_incremental_sync = True


class LightspeedAdapter(_UnavailableProviderAdapter):
    """Lightspeed Retail's API supports product/price/inventory read+write
    and webhooks, but no first-class promotions API. This build does not
    talk to Lightspeed.
    """

    provider_display_name = "Lightspeed"
    supports_product_read = True
    supports_product_write = True
    supports_price_read = True
    supports_price_write = True
    supports_inventory_read = True
    supports_inventory_write = True
    supports_sales_read = True
    supports_webhooks = True
    supports_incremental_sync = True


class ToastAdapter(_UnavailableProviderAdapter):
    """Toast is a restaurant POS with a narrower public API surface —
    menu/price read access and order data, no public inventory or
    promotions write API, and no native webhook push (its public
    integration surface is polling-oriented). This build does not talk to
    Toast.
    """

    provider_display_name = "Toast"
    supports_product_read = True
    supports_price_read = True
    supports_sales_read = True
    supports_incremental_sync = True


class MicrosoftDynamicsAdapter(_UnavailableProviderAdapter):
    """Dynamics 365 Business Central's OData/REST API supports full
    product/price/inventory/promotion read+write, but its integration
    surface is polling-oriented (no native webhook push comparable to a
    POS/ecommerce platform's). This build does not talk to Dynamics.
    """

    provider_display_name = "Microsoft Dynamics"
    supports_product_read = True
    supports_product_write = True
    supports_price_read = True
    supports_price_write = True
    supports_inventory_read = True
    supports_inventory_write = True
    supports_promotion_read = True
    supports_promotion_write = True
    supports_sales_read = True
    supports_incremental_sync = True


class NetSuiteAdapter(_UnavailableProviderAdapter):
    """NetSuite's SuiteTalk/REST API supports full product/price/inventory/
    promotion read+write, but is likewise polling-oriented — no native
    webhook push. This build does not talk to NetSuite.
    """

    provider_display_name = "NetSuite"
    supports_product_read = True
    supports_product_write = True
    supports_price_read = True
    supports_price_write = True
    supports_inventory_read = True
    supports_inventory_write = True
    supports_promotion_read = True
    supports_promotion_write = True
    supports_sales_read = True
    supports_incremental_sync = True
