import base64
import logging
from decimal import Decimal
from io import BytesIO
from typing import Any

from reportlab.lib.colors import HexColor
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from app.core.exceptions import ValidationError
from app.models.output_job import OutputJob
from app.outputs.base import OutputAdapter, OutputRenderContext, validate_known_keys
from app.outputs.qr_render import render_qr_png
from app.storage import get_storage_adapter

_CONFIG_SCHEMA: dict[str, type] = {
    "label_width_mm": (int, float),     # default 85
    "label_height_mm": (int, float),    # default 55
    "show_qr": bool,                    # default True
    "qr_position": str,                 # "left" | "right", default "right"
    "qr_size_mm": (int, float),         # default 18
    "show_unit_price": bool,            # default True
    "banner_position": str,             # "top" | "bottom", default "bottom"
    "banner_text": str,                 # store name override (advanced/API)
}

logger = logging.getLogger(__name__)

# ── Black & white palette (base of the Stage 2 template colors) ─────────
# A LabelTemplate (resolved into context.template_colors by the service
# layer) overrides any of these keys; every other key keeps its default.
_DEFAULT_COLORS: dict[str, str] = {
    "background": "#FFFFFF",
    "border": "#111111",
    "text": "#111111",
    "banner": "#111111",
    "unit_border": "#111111",
    "sublabel": "#666666",
    "placeholder": "#AAAAAA",
}

_QR_POSITIONS = {"left", "right"}
_BANNER_POSITIONS = {"top", "bottom"}

_CURRENCY_SYMBOLS: dict[str, str] = {
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
    "CAD": "C$",
    "AUD": "A$",
}


def _format_price(value: str) -> str:
    """Strip trailing zeros: '249.9900' -> '249.99', '100.00' -> '100.00' (2dp min)."""
    d = Decimal(value).quantize(Decimal("0.01"))
    return str(d)


def _format_unit_price(value: Decimal) -> str:
    """Per-unit price: >= 1 -> 2dp, < 1 -> up to 3dp (trailing zeros stripped)."""
    d = value.quantize(Decimal("0.0001"))
    precision = Decimal("0.01") if d >= Decimal("1") else Decimal("0.001")
    return format(d.quantize(precision), "f").rstrip("0").rstrip(".")


def _truncate(pdf: canvas.Canvas, text: str, font: str, size: float, max_w: float) -> str:
    """Truncate text with ellipsis to fit within *max_w* points."""
    if pdf.stringWidth(text, font, size) <= max_w:
        return text
    while len(text) > 1 and pdf.stringWidth(text + "…", font, size) > max_w:
        text = text[:-1]
    return text + "…" if text else ""


class PDFLabelAdapter(OutputAdapter):
    """Generates a printable shelf-label PDF in a black-and-white three-column
    layout matching a real grocery price tag: product name + price on one side,
    a bordered unit-price box in the middle, and the product's QR code on the
    other side, with a store-name banner on top or bottom and a shelf-number
    badge in the top-right corner.

    Every element's position is configurable through the output channel
    configuration (QR left/right, banner top/bottom, per-element sizes).
    """

    def validate_configuration(self, configuration: dict[str, Any]) -> None:
        validate_known_keys(configuration or {}, _CONFIG_SCHEMA)
        qr_position = (configuration or {}).get("qr_position")
        if qr_position is not None and qr_position not in _QR_POSITIONS:
            raise ValidationError("configuration.qr_position must be one of left, right.")
        banner_position = (configuration or {}).get("banner_position")
        if banner_position is not None and banner_position not in _BANNER_POSITIONS:
            raise ValidationError("configuration.banner_position must be one of top, bottom.")

    def render_payload(self, context: OutputRenderContext) -> dict[str, Any]:
        base_price = context.base_price or context.price
        saving = (
            base_price - context.price if base_price and base_price > context.price else Decimal("0")
        )
        # inventory.quantity_on_hand is Numeric, so MySQL returns a Decimal;
        # it's a unit count in the payload and must be JSON-serializable.
        stock = int(context.stock_qty) if context.stock_qty is not None else None
        return {
            "product_name": context.product.product_name,
            "sku": context.product.sku,
            "brand": context.product.brand,
            "shelf_id": context.product.shelf_id,
            "price": _format_price(str(context.price)),
            "base_price": _format_price(str(base_price)),
            "saving": _format_price(str(saving)),
            "currency": context.currency,
            "store_name": context.store.name if context.store else None,
            "stock_qty": stock,
            "public_url": context.public_url,
        }

    # -----------------------------------------------------------------
    # Drawing
    # -----------------------------------------------------------------

    @staticmethod
    def _sym(currency: str) -> str:
        return _CURRENCY_SYMBOLS.get(currency, currency + " ")

    @staticmethod
    def _unit_price_label(context: OutputRenderContext, price: Decimal) -> tuple[str, str]:
        """(formatted per-unit price, 'PER <UNIT>' suffix). Derives per-unit
        from product weight when available, otherwise the whole-product price.
        """
        weight = context.product.weight
        weight_unit = context.product.weight_unit
        if weight and weight > 0 and weight_unit:
            return _format_unit_price(price / weight), f"PER {weight_unit.upper()}"
        return _format_unit_price(price), "PER EA"

    def send_update(
        self, *, job: OutputJob, context: OutputRenderContext, payload: dict[str, Any]
    ) -> dict[str, Any]:
        del job
        cfg = context.configuration
        # Stage 2: template colors (from a LabelTemplate resolved into the
        # context by the service layer) override the defaults key-by-key.
        colors = dict(_DEFAULT_COLORS)
        if context.template_colors:
            colors.update(context.template_colors)
        C = {key: HexColor(value) for key, value in colors.items()}

        w = cfg.get("label_width_mm", 85) * mm
        h = cfg.get("label_height_mm", 55) * mm
        show_qr = cfg.get("show_qr", True)
        qr_position = cfg.get("qr_position", "right")
        qr_mm = cfg.get("qr_size_mm", 18)
        show_unit = cfg.get("show_unit_price", True)
        banner_position = cfg.get("banner_position", "bottom")
        banner_text = cfg.get("banner_text") or payload.get("store_name") or "Store Name"

        sym = self._sym(payload["currency"])
        price = Decimal(payload["price"])
        unit_price, unit_suffix = self._unit_price_label(context, price)

        buf = BytesIO()
        c = canvas.Canvas(buf, pagesize=(w, h))
        c.setTitle(f"Shelf label {payload['sku']}")

        pad = 2 * mm
        gap = 1.5 * mm
        banner_h = 4.5 * mm

        # ── Banner zone (top or bottom) ───────────────────────────────
        if banner_position == "bottom":
            banner_x, banner_y = pad, pad
            # Extra top margin so the product name doesn't clip the border
            content_top = h - pad - 3 * mm
            content_bot = pad + banner_h + gap
        else:  # top
            banner_x, banner_y = pad, h - pad - banner_h
            content_top = h - pad - banner_h - gap
            content_bot = pad
        content_h = content_top - content_bot

        # ── Background + outer border ─────────────────────────────────
        c.setFillColor(C["background"])
        c.rect(pad, pad, w - 2 * pad, h - 2 * pad, fill=1, stroke=0)

        # Optional template background image (from a LabelTemplate). Drawn
        # after the color fill so it can cover it, before every element so
        # text/QR/unit-box/banner render on top. Any failure (missing file,
        # bad bytes, backend down) skips the image and the label still
        # renders on the plain color background — a job never fails just
        # because its decoration is unavailable.
        if context.template_background_image_url:
            try:
                image_bytes = get_storage_adapter().download(context.template_background_image_url)
                c.drawImage(
                    ImageReader(BytesIO(image_bytes)),
                    pad,
                    pad,
                    w - 2 * pad,
                    h - 2 * pad,
                    preserveAspectRatio=False,
                )
            except Exception:  # noqa: BLE001 — background is decorative-only
                logger.warning(
                    "Could not draw template background image %s; using plain color.",
                    context.template_background_image_url,
                )

        c.setStrokeColor(C["border"])
        c.setLineWidth(2)
        c.rect(pad, pad, w - 2 * pad, h - 2 * pad, fill=0, stroke=1)

        # ── Banner ────────────────────────────────────────────────────
        c.setFillColor(C["banner"])
        c.rect(banner_x, banner_y, w - 2 * pad, banner_h, fill=1, stroke=0)
        if banner_text:
            c.setFillColor(HexColor("#FFFFFF"))
            c.setFont("Helvetica", 10)
            fitted = _truncate(c, banner_text, "Helvetica", 10, w - 2 * pad - 4 * mm)
            c.drawCentredString(w / 2, banner_y + banner_h / 2 - 10 / 3, fitted)

        # ── Column layout (widths first, then positions) ──────────────
        inner_w = w - 2 * pad
        x0 = pad
        unit_w = 20 * mm
        qr_zone_w = (qr_mm * mm + 4 * mm) if show_qr else 0.0

        # total width consumed by non-text columns + gaps
        non_text = 0.0
        if show_qr:
            non_text += qr_zone_w + gap
        if show_unit:
            non_text += unit_w + gap
        text_w = max(float(inner_w - non_text), 8 * mm)

        # Position columns left → right based on qr_position
        if qr_position == "left":
            # [QR] [unit] [text]
            qr_x = x0
            unit_x = x0 + (qr_zone_w + gap if show_qr else 0)
            text_x = unit_x + (unit_w + gap if show_unit else 0)
        else:
            # [text] [unit] [QR]
            text_x = x0
            unit_x = x0 + text_w + gap
            qr_x = unit_x + (unit_w + gap if show_unit else 0)

        # ── Text zone: name / RETAIL PRICE / big price / SKU + brand ──
        name_size = 9
        name_font = "Helvetica-Bold"
        raw_name = payload.get("product_name") or ""
        if raw_name.strip():
            c.setFillColor(C["text"])
            c.setFont(name_font, name_size)
            name_text = _truncate(c, raw_name, name_font, name_size, text_w)
        else:
            c.setFillColor(C["placeholder"])
            c.setFont("Helvetica-Oblique", name_size)
            name_text = "Product Name"
        name_baseline = content_top - 1.5 * mm
        c.drawString(text_x, name_baseline, name_text)

        # "RETAIL PRICE" sublabel
        c.setFillColor(C["sublabel"])
        c.setFont("Helvetica", 5.5)
        retail_label_y = name_baseline - 3 * mm
        c.drawString(text_x, retail_label_y, "RETAIL PRICE")

        # Big price: size the digits so the whole price fits the column.
        # Then place baseline far enough below the sublabel so the tall
        # price characters don't overlap upward into the name area.
        digit_size = 16
        dollar_size = 9
        price_text = payload["price"]
        while (
            c.stringWidth(sym, "Helvetica-Bold", dollar_size)
            + c.stringWidth(price_text, "Helvetica-Bold", digit_size)
            + 1.5 * mm
            > text_w
            and digit_size > 12
        ):
            digit_size -= 2
            dollar_size -= 1
        # Cap height ≈ 70 % of font size.  Ensure price top stays below
        # the sublabel baseline with a 1 mm breathing gap.
        price_char_h = digit_size * 0.7 * mm / 2.835
        price_baseline = retail_label_y - price_char_h - 1 * mm
        c.setFillColor(C["text"])
        c.setFont("Helvetica-Bold", dollar_size)
        c.drawString(text_x, price_baseline, sym)
        c.setFont("Helvetica-Bold", digit_size)
        digits_x = text_x + c.stringWidth(sym, "Helvetica-Bold", dollar_size) + 1 * mm
        c.drawString(digits_x, price_baseline, price_text)

        # SKU + brand pinned to the bottom of the content zone
        raw_sku = payload.get("sku") or ""
        if raw_sku.strip():
            c.setFillColor(C["text"])
            c.setFont("Helvetica", 7)
            c.drawString(text_x, content_bot + 3.5 * mm, raw_sku)
        else:
            c.setFillColor(C["placeholder"])
            c.setFont("Helvetica-Oblique", 7)
            c.drawString(text_x, content_bot + 3.5 * mm, "SKU-000")
        if payload.get("brand"):
            c.setFillColor(C["sublabel"])
            c.setFont("Helvetica", 6)
            brand_text = _truncate(c, payload["brand"], "Helvetica", 6, text_w)
            c.drawString(text_x, content_bot + 1.5 * mm, brand_text)

        # ── Unit price box (center column) ────────────────────────────
        if show_unit:
            unit_box_h = 20 * mm
            unit_box_y = content_bot + (content_h - unit_box_h) / 2
            box_top = unit_box_y + unit_box_h
            c.setStrokeColor(C["unit_border"])
            c.setLineWidth(0.8)
            c.roundRect(unit_x, unit_box_y, unit_w, unit_box_h, 1.5 * mm, fill=0, stroke=1)
            unit_center_x = unit_x + unit_w / 2

            c.setFillColor(C["text"])
            c.setFont("Helvetica-Bold", 7)
            c.drawCentredString(unit_center_x, box_top - 4 * mm, "UNIT PRICE")
            c.setFont("Helvetica-Bold", 14)
            unit_price_text = f"{sym}{unit_price}"
            # shrink per-unit price to fit the box if needed
            up_size = 14
            while c.stringWidth(unit_price_text, "Helvetica-Bold", up_size) > unit_w - 2 * mm and up_size > 8:
                up_size -= 1
            c.setFont("Helvetica-Bold", up_size)
            c.drawCentredString(unit_center_x, box_top - 10 * mm, unit_price_text)
            c.setFont("Helvetica", 6)
            c.drawCentredString(unit_center_x, box_top - 13.5 * mm, unit_suffix)

        # ── QR zone ───────────────────────────────────────────────────
        if show_qr:
            qr_size = float(qr_mm) * mm
            qr_left = qr_x + (qr_zone_w - qr_size) / 2
            qr_top = content_top - 1.5 * mm
            qr_bottom = qr_top - qr_size
            qr_bytes = render_qr_png(context.product.product_url or "")
            c.drawImage(ImageReader(BytesIO(qr_bytes)), qr_left, qr_bottom, qr_size, qr_size)
            c.setFillColor(C["text"])
            c.setFont("Helvetica", 7)
            c.drawCentredString(qr_x + qr_zone_w / 2, qr_bottom - 2.5 * mm, payload["sku"])

        # ── Shelf number badge ────────────────────────────────────────
        shelf_id = payload.get("shelf_id") or ""
        if str(shelf_id).strip():
            badge_w = 14 * mm
            badge_h = 5.5 * mm
            if banner_position == "top":
                bx = w - pad - badge_w
                by = pad  # bottom-right, clear of QR zone at top
            else:
                # Place below the QR code, centred in its zone, so it
                # doesn't collide with the product name or the banner.
                bx = qr_x + (qr_zone_w - badge_w) / 2
                by = content_bot + 2 * mm
            c.setFillColor(C["banner"])
            c.roundRect(bx, by, badge_w, badge_h, 2 * mm, fill=1, stroke=0)
            c.setFillColor(HexColor("#FFFFFF"))
            c.setFont("Helvetica-Bold", 13)
            badge_text = _truncate(c, str(shelf_id), "Helvetica-Bold", 13, badge_w - 2 * mm)
            c.drawCentredString(bx + badge_w / 2, by + badge_h / 2 - 13 / 3, badge_text)

        c.showPage()
        c.save()

        encoded = base64.b64encode(buf.getvalue()).decode("ascii")
        return {
            **payload,
            "unit_price": unit_price,
            "unit_suffix": unit_suffix,
            "pdf_base64": encoded,
            "pdf_mime": "application/pdf",
        }

    def get_status(self, job: OutputJob) -> str:
        return job.status.value