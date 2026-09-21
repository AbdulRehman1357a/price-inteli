from app.integrations.base import IntegrationAdapter
from app.integrations.hub.csv_adapter import CSVAdapter
from app.integrations.hub.rest_api_adapter import RESTAPIAdapter
from app.integrations.hub.vendor_stubs import (
    CloverAdapter,
    LightspeedAdapter,
    MicrosoftDynamicsAdapter,
    NetSuiteAdapter,
    OracleAdapter,
    SAPAdapter,
    ShopifyAdapter,
    SquareAdapter,
    ToastAdapter,
)
from app.integrations.hub.webhook_adapter import WebhookAdapter
from app.models.integration import IntegrationProvider

_ADAPTERS: dict[IntegrationProvider, IntegrationAdapter] = {
    IntegrationProvider.CSV: CSVAdapter(),
    IntegrationProvider.REST_API: RESTAPIAdapter(),
    IntegrationProvider.WEBHOOK: WebhookAdapter(),
    IntegrationProvider.SAP: SAPAdapter(),
    IntegrationProvider.ORACLE: OracleAdapter(),
    IntegrationProvider.SQUARE: SquareAdapter(),
    IntegrationProvider.CLOVER: CloverAdapter(),
    IntegrationProvider.SHOPIFY: ShopifyAdapter(),
    IntegrationProvider.LIGHTSPEED: LightspeedAdapter(),
    IntegrationProvider.TOAST: ToastAdapter(),
    IntegrationProvider.MICROSOFT_DYNAMICS: MicrosoftDynamicsAdapter(),
    IntegrationProvider.NETSUITE: NetSuiteAdapter(),
}


def get_hub_adapter(provider: IntegrationProvider) -> IntegrationAdapter:
    return _ADAPTERS[provider]
