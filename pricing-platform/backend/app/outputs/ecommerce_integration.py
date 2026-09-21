from typing import Any

from app.models.output_job import OutputJob
from app.outputs.base import OutputAdapter, OutputRenderContext, validate_known_keys

_CONFIG_SCHEMA: dict[str, type] = {
    "platform": str,  # e.g. "shopify"/"custom" — cosmetic label in this phase
}


class EcommerceIntegrationAdapter(OutputAdapter):
    """Pushes a price update toward a connected e-commerce storefront. No
    live e-commerce platform integration exists in this phase — same
    simulate-rather-than-fake-a-vendor pattern as the ESL Simulator. A
    future phase could route this through a configured Enterprise
    Integration Hub connection (app/integrations/hub/) instead.
    """

    def validate_configuration(self, configuration: dict[str, Any]) -> None:
        validate_known_keys(configuration or {}, _CONFIG_SCHEMA)

    def render_payload(self, context: OutputRenderContext) -> dict[str, Any]:
        return {
            "product_name": context.product.product_name,
            "sku": context.product.sku,
            "price": str(context.price),
            "currency": context.currency,
            "store_name": context.store.name if context.store else None,
            "public_url": context.public_url,
            "platform": context.configuration.get("platform"),
        }

    def send_update(
        self, *, job: OutputJob, context: OutputRenderContext, payload: dict[str, Any]
    ) -> dict[str, Any]:
        del job, context
        return {**payload, "ecommerce_sync_status": "simulated_success"}

    def get_status(self, job: OutputJob) -> str:
        return job.status.value
