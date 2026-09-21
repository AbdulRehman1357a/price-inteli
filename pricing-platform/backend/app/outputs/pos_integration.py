from typing import Any

from app.models.output_job import OutputJob
from app.outputs.base import OutputAdapter, OutputRenderContext, validate_known_keys

_CONFIG_SCHEMA: dict[str, type] = {
    "pos_terminal_id": str,  # which POS terminal/register this channel targets, cosmetic in this phase
}


class POSIntegrationAdapter(OutputAdapter):
    """Pushes a price update toward a connected point-of-sale system. No
    live POS terminal integration exists in this phase — same "simulate,
    don't fake a real vendor connection" honesty as the Phase 8 ESL
    Simulator: this renders the correct payload a real POS push would
    carry and simulates a successful send. A future phase could route this
    through a configured Enterprise Integration Hub connection
    (app/integrations/hub/) instead of simulating.
    """

    def validate_configuration(self, configuration: dict[str, Any]) -> None:
        validate_known_keys(configuration or {}, _CONFIG_SCHEMA)

    def render_payload(self, context: OutputRenderContext) -> dict[str, Any]:
        return {
            "product_name": context.product.product_name,
            "sku": context.product.sku,
            "barcode": context.product.barcode,
            "price": str(context.price),
            "currency": context.currency,
            "store_name": context.store.name if context.store else None,
            "pos_terminal_id": context.configuration.get("pos_terminal_id"),
        }

    def send_update(
        self, *, job: OutputJob, context: OutputRenderContext, payload: dict[str, Any]
    ) -> dict[str, Any]:
        del job, context
        return {**payload, "pos_sync_status": "simulated_success"}

    def get_status(self, job: OutputJob) -> str:
        return job.status.value
