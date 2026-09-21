from typing import Any

from app.models.output_job import OutputJob
from app.outputs.base import OutputAdapter, OutputRenderContext, validate_known_keys

_CONFIG_SCHEMA: dict[str, type] = {
    "screen_id": str,
    "theme": str,  # "light" | "dark"
}


class DigitalSignageAdapter(OutputAdapter):
    """Renders a price for an in-store digital signage screen. No live
    signage network is connected in this phase — same simulate-don't-fake
    pattern as the ESL Simulator and Web Display adapters; the data itself
    (product, price, store) is fully correct.
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
            "screen_id": context.configuration.get("screen_id"),
            "theme": context.configuration.get("theme", "light"),
        }

    def send_update(
        self, *, job: OutputJob, context: OutputRenderContext, payload: dict[str, Any]
    ) -> dict[str, Any]:
        del job, context
        return {**payload, "signage_sync_status": "simulated_success"}

    def get_status(self, job: OutputJob) -> str:
        return job.status.value
