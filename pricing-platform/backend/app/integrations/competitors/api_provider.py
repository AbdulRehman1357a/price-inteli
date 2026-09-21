from decimal import Decimal, InvalidOperation

import httpx

from app.core.exceptions import ValidationError
from app.integrations.competitors.base import CompetitorPriceProvider, RawCompetitorPriceObservation


class APICompetitorPriceProvider(CompetitorPriceProvider):
    """A generic JSON API client — no vendor-specific shape hard-coded, same
    spirit as app/integrations/hub/rest_api_adapter.py. GETs
    external_product_url and expects a JSON object with "price" (required),
    "currency" (optional, defaults to "USD"), and "availability" (optional)
    keys. Whoever configures a CompetitorProduct's external_product_url for
    API ingestion is responsible for it being a URL they're authorized to
    call — this adapter does not crawl, parse HTML, or bypass any access
    control.
    """

    def fetch_price(self, external_product_url: str) -> RawCompetitorPriceObservation:
        try:
            response = httpx.get(external_product_url, timeout=10.0, follow_redirects=True)
        except httpx.HTTPError as exc:
            raise ValidationError(f"Could not reach {external_product_url}: {exc}") from exc
        if response.status_code >= 400:
            raise ValidationError(f"{external_product_url} returned HTTP {response.status_code}.")

        try:
            payload = response.json()
        except ValueError as exc:
            raise ValidationError(f"{external_product_url} did not return valid JSON.") from exc
        if not isinstance(payload, dict) or "price" not in payload:
            raise ValidationError(f"{external_product_url} response did not include a 'price' field.")

        try:
            price = Decimal(str(payload["price"]))
        except InvalidOperation as exc:
            raise ValidationError(f"'{payload['price']}' is not a valid price.") from exc

        return RawCompetitorPriceObservation(
            price=price,
            currency=str(payload.get("currency") or "USD"),
            availability=str(payload["availability"]) if payload.get("availability") is not None else None,
        )
