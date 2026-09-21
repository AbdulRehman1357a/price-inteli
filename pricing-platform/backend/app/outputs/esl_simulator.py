from typing import Any

from app.models.output_job import OutputJob
from app.outputs.base import OutputAdapter, OutputRenderContext, validate_known_keys

_CONFIG_SCHEMA: dict[str, type] = {
    "label_size": str,  # e.g. "2.9in" — cosmetic hint only, consumed by the frontend simulator
    "orientation": str,  # "landscape" | "portrait"
    "theme": str,  # "light" | "dark" — frontend simulator color scheme
}


class ESLSimulatorAdapter(OutputAdapter):
    """Renders a fake electronic shelf label — no hardware or vendor
    protocol involved. The React frontend is what actually "displays" the
    label; this adapter just produces the data it renders from.
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
            "public_url": context.public_url,
            "label_size": context.configuration.get("label_size", "2.9in"),
            "orientation": context.configuration.get("orientation", "landscape"),
            "theme": context.configuration.get("theme", "light"),
        }

    def send_update(
        self, *, job: OutputJob, context: OutputRenderContext, payload: dict[str, Any]
    ) -> dict[str, Any]:
        del job, context  # simulated — nothing to send, the payload itself is what the UI renders
        return payload

    def get_status(self, job: OutputJob) -> str:
        return job.status.value
