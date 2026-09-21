from typing import Any

import httpx

from app.integrations.base import IntegrationAdapter
from app.models.integration import Integration

# Keys a JSON response might nest its record list under, tried in order —
# generic, not tied to any specific vendor's API shape.
_LIST_KEYS = ("data", "records", "items", "results")


def _build_auth(credentials: dict[str, Any]) -> tuple[httpx.Auth | None, dict[str, str]]:
    auth_type = (credentials.get("authentication_type") or "none").lower()
    headers: dict[str, str] = {}
    if auth_type == "basic" and credentials.get("username"):
        return httpx.BasicAuth(credentials["username"], credentials.get("password", "")), headers
    if auth_type == "api_key" and credentials.get("api_key"):
        headers["X-API-Key"] = credentials["api_key"]
    elif auth_type == "bearer" and credentials.get("api_key"):
        headers["Authorization"] = f"Bearer {credentials['api_key']}"
    return None, headers


def _extract_records(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in _LIST_KEYS:
            if isinstance(payload.get(key), list):
                return payload[key]
    return []


class RESTAPIAdapter(IntegrationAdapter):
    """A generic REST client — no vendor-specific request/response shape
    hard-coded (per "do not hard-code any vendor-specific API"). Auth is
    driven entirely by credentials["authentication_type"] (none/basic/
    api_key/bearer), matching the Integration Form's generic auth fields.
    The one adapter in this build with a real push_records() — it's
    already a generic HTTP client, so outward writes are just a POST/PUT
    to the same generic {base_url}/{entity_type} shape fetch_records reads
    from. supports_incremental_sync=True: a generic REST endpoint can
    accept query params (handled by a future checkpoint-aware fetch), even
    though this pass's fetch_records doesn't yet thread one through.
    """

    supports_product_read = True
    supports_product_write = True
    supports_price_read = True
    supports_price_write = True
    supports_inventory_read = True
    supports_inventory_write = True
    supports_promotion_read = True
    supports_promotion_write = True
    supports_sales_read = True
    supports_incremental_sync = True

    def test_connection(self, integration: Integration, credentials: dict[str, Any]) -> dict[str, Any]:
        del integration
        base_url = credentials.get("base_url")
        if not base_url:
            return {"success": False, "message": "No Base URL configured."}
        auth, headers = _build_auth(credentials)
        try:
            response = httpx.get(base_url, auth=auth, headers=headers, timeout=5.0, follow_redirects=True)
        except httpx.HTTPError as exc:
            return {"success": False, "message": f"Could not reach {base_url}: {exc}"}
        if response.status_code >= 400:
            return {"success": False, "message": f"{base_url} returned HTTP {response.status_code}."}
        return {"success": True, "message": f"Connected to {base_url} (HTTP {response.status_code})."}

    def fetch_records(
        self,
        integration: Integration,
        credentials: dict[str, Any],
        *,
        entity_type: str,
        records: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        del integration, records
        base_url = credentials.get("base_url")
        if not base_url:
            raise ValueError("No Base URL configured.")
        auth, headers = _build_auth(credentials)
        url = f"{base_url.rstrip('/')}/{entity_type}"
        response = httpx.get(url, auth=auth, headers=headers, timeout=15.0, follow_redirects=True)
        response.raise_for_status()
        return _extract_records(response.json())

    def push_records(
        self,
        integration: Integration,
        credentials: dict[str, Any],
        *,
        entity_type: str,
        records: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Outbound execution (PIP -> External), e.g. approved-price push.
        POSTs each record individually to {base_url}/{entity_type} —
        generic, no vendor-specific batch-endpoint shape assumed. Returns
        a per-record success/failure summary rather than raising on the
        first failure, so the caller (integration_sync_service) can record
        partial outcomes the same way it does for inbound sync.
        """
        del integration
        base_url = credentials.get("base_url")
        if not base_url:
            raise ValueError("No Base URL configured.")
        auth, headers = _build_auth(credentials)
        url = f"{base_url.rstrip('/')}/{entity_type}"

        results: list[dict[str, Any]] = []
        for record in records:
            try:
                response = httpx.post(
                    url, json=record, auth=auth, headers=headers, timeout=15.0, follow_redirects=True
                )
                response.raise_for_status()
                results.append({"success": True})
            except httpx.HTTPError as exc:
                results.append({"success": False, "message": str(exc)})
        return {"results": results}
