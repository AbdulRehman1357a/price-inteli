import base64
from decimal import Decimal
from typing import Any

from app.core.exceptions import ValidationError
from app.models.output_job import OutputJob
from app.outputs.base import OutputAdapter, OutputRenderContext, validate_known_keys
from app.outputs.qr_render import render_qr_png

_CONFIG_SCHEMA: dict[str, type] = {
    "box_size": int,
    "border": int,
    "error_correction": str,  # "L" | "M" | "Q" | "H"
}

_ERROR_CORRECTION_LEVELS = ("L", "M", "Q", "H")


def _format_price(value: str) -> str:
    """Strip trailing zeros: '249.9900' -> '249.99', '100.00' -> '100.00' (2dp minimum)."""
    d = Decimal(value).quantize(Decimal("0.01"))
    return str(d)


class QRCodeAdapter(OutputAdapter):
    """Generates a QR code pointing at the product's public price page.
    No print-out/physical delivery — the generated image is returned as a
    base64 PNG on the job payload for the frontend to display/download.
    """

    def validate_configuration(self, configuration: dict[str, Any]) -> None:
        validate_known_keys(configuration or {}, _CONFIG_SCHEMA)
        error_correction = (configuration or {}).get("error_correction")
        if error_correction is not None and error_correction not in _ERROR_CORRECTION_LEVELS:
            raise ValidationError("configuration.error_correction must be one of L, M, Q, H.")

    def render_payload(self, context: OutputRenderContext) -> dict[str, Any]:
        base_price = context.base_price or context.price
        saving = base_price - context.price if base_price and base_price > context.price else Decimal("0")
        # inventory.quantity_on_hand is Numeric, so MySQL returns a Decimal;
        # it's a unit count in the payload and must be JSON-serializable.
        stock = int(context.stock_qty) if context.stock_qty is not None else None
        return {
            "product_name": context.product.product_name,
            "sku": context.product.sku,
            "base_price": _format_price(str(base_price)),
            "price": _format_price(str(context.price)),
            "currency": context.currency,
            "saving": _format_price(str(saving)),
            "store_name": context.store.name if context.store else None,
            "stock_qty": stock,
        }

    def send_update(
        self, *, job: OutputJob, context: OutputRenderContext, payload: dict[str, Any]
    ) -> dict[str, Any]:
        del job
        config = context.configuration
        qr_text = context.product.product_url or ""
        png_bytes = render_qr_png(
            qr_text,
            box_size=config.get("box_size", 8),
            border=config.get("border", 2),
            error_correction=config.get("error_correction", "M"),
        )
        encoded = base64.b64encode(png_bytes).decode("ascii")

        return {**payload, "qr_text": qr_text, "qr_image_base64": encoded, "qr_image_mime": "image/png"}

    def get_status(self, job: OutputJob) -> str:
        return job.status.value
