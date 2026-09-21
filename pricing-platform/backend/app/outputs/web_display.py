from typing import Any

from app.models.output_job import OutputJob
from app.outputs.base import OutputAdapter, OutputRenderContext, validate_known_keys

_CONFIG_SCHEMA: dict[str, type] = {
    "theme": str,  # "light" | "dark" — cosmetic hint for the public price page
}


class WebDisplayAdapter(OutputAdapter):
    """Exposes a product's price on the public, unauthenticated price page
    (app/api/v1/public.py). There's nothing to "send" — the public page
    reads the live current price at request time — so this adapter just
    confirms the product/store combination is publishable.
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
            "theme": context.configuration.get("theme", "light"),
        }

    def send_update(
        self, *, job: OutputJob, context: OutputRenderContext, payload: dict[str, Any]
    ) -> dict[str, Any]:
        del job, context
        return {**payload, "published": True}

    def get_status(self, job: OutputJob) -> str:
        return job.status.value
