import csv
import io
from pathlib import Path
from typing import Any

import httpx

from app.integrations.base import IntegrationAdapter
from app.models.integration import Integration


class CSVAdapter(IntegrationAdapter):
    """Reads records from a CSV file at credentials["base_url"] — a local
    file path or an http(s) URL. The "Base URL" field is shared across
    provider types in the Integration Form; for CSV it points at the file
    rather than an API endpoint. Read-only: a flat file has no write
    destination, and no webhook/incremental concept.
    """

    supports_product_read = True
    supports_price_read = True
    supports_inventory_read = True
    supports_promotion_read = True
    supports_sales_read = True

    def test_connection(self, integration: Integration, credentials: dict[str, Any]) -> dict[str, Any]:
        del integration
        location = credentials.get("base_url")
        if not location:
            return {"success": False, "message": "No file path/URL configured (Base URL)."}
        try:
            if location.startswith(("http://", "https://")):
                response = httpx.head(location, timeout=5.0, follow_redirects=True)
                if response.status_code >= 400:
                    return {"success": False, "message": f"CSV URL returned HTTP {response.status_code}."}
            elif not Path(location).is_file():
                return {"success": False, "message": f"No file found at {location!r}."}
        except httpx.HTTPError as exc:
            return {"success": False, "message": f"Could not reach the CSV URL: {exc}"}
        return {"success": True, "message": "CSV source is reachable."}

    def fetch_records(
        self,
        integration: Integration,
        credentials: dict[str, Any],
        *,
        entity_type: str,
        records: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        del integration, entity_type, records
        location = credentials.get("base_url")
        if not location:
            raise ValueError("No file path/URL configured (Base URL).")

        if location.startswith(("http://", "https://")):
            response = httpx.get(location, timeout=15.0, follow_redirects=True)
            response.raise_for_status()
            content = response.text
        else:
            content = Path(location).read_text(encoding="utf-8")

        return list(csv.DictReader(io.StringIO(content)))
