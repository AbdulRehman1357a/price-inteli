from __future__ import annotations

import time
import uuid
from typing import Any

import httpx

from app.integrations.esl.base import ESLIntegrationAdapter
from app.models.esl_integration import ESLIntegration


def _http_error_message(exc: httpx.HTTPStatusError) -> str:
    return f"HTTP {exc.response.status_code}: {exc.response.text}"


_NETWORK_ERROR_MESSAGE = "Could not reach Pricer Plaza API (network error)"


class PricerClient:
    """Async HTTP client for the Pricer Plaza API.

    Handles OAuth2 client_credentials flow with token caching and automatic
    refresh on 401. Attaches required headers (Authorization, X-Pricer-Client-Id,
    X-Pricer-Transaction-Id) on every request.
    """

    def __init__(
        self,
        base_url: str,
        client_id: str,
        client_secret: str,
        timeout: float = 15.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.client_id = client_id
        self.client_secret = client_secret
        self._timeout = timeout
        self._token: str | None = None
        self._token_expires_at: float = 0.0
        self._client: httpx.AsyncClient | None = None

    async def _ensure_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self._timeout)
        return self._client

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def _request(
        self,
        method: str,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        client = await self._ensure_client()

        # Ensure we have a valid token
        if not self._token or time.time() >= self._token_expires_at - 60:  # refresh 60s early
            await self.authenticate()

        request_headers = {
            "Authorization": f"Bearer {self._token}",
            "X-Pricer-Client-Id": self.client_id,
            "X-Pricer-Transaction-Id": uuid.uuid4().hex,
        }
        if headers:
            request_headers.update(headers)

        url = f"{self.base_url}{path}"
        response = await client.request(method, url, headers=request_headers, **kwargs)

        # Auto-refresh on 401 (token expired or invalid)
        if response.status_code == 401:
            self._token = None
            self._token_expires_at = 0.0
            await self.authenticate()
            request_headers["Authorization"] = f"Bearer {self._token}"
            response = await client.request(method, url, headers=request_headers, **kwargs)

        return response

    async def authenticate(self) -> dict[str, Any]:
        """Obtain an OAuth2 bearer token via client_credentials grant."""
        client = await self._ensure_client()
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
        }
        response = await client.post(
            f"{self.base_url}/v2/oauth/token",
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()
        payload = response.json()
        self._token = payload["access_token"]
        self._token_expires_at = time.time() + payload.get("expires_in", 259200)
        return payload

    async def get_stores(self) -> list[dict[str, Any]]:
        """List all stores (GET /v1/stores)."""
        response = await self._request("GET", "/v1/stores")
        response.raise_for_status()
        return response.json()

    async def get_store(self, store_id: str) -> dict[str, Any]:
        """Get a single store (GET /v1/stores/{storeId})."""
        response = await self._request("GET", f"/v1/stores/{store_id}")
        response.raise_for_status()
        return response.json()

    async def get_devices(
        self,
        store_id: str,
        *,
        status: str | None = None,
        model_name: str | None = None,
        device_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """List devices (GET /v1/stores/{storeId}/devices).

        Optional filters: status (linked|roaming|not_found), modelName, deviceId.
        """
        params: dict[str, str] = {}
        if status:
            params["status"] = status
        if model_name:
            params["modelName"] = model_name
        if device_id:
            params["deviceId"] = device_id

        response = await self._request("GET", f"/v1/stores/{store_id}/devices", params=params)
        response.raise_for_status()
        return response.json()

    async def get_device(self, store_id: str, device_id: str) -> dict[str, Any]:
        """Get single device detail (GET /v1/stores/{storeId}/devices/{deviceId})."""
        response = await self._request("GET", f"/v1/stores/{store_id}/devices/{device_id}")
        response.raise_for_status()
        return response.json()

    async def link_device(
        self,
        store_id: str,
        device_id: str,
        items: list[dict[str, Any]],
        design: str | None = None,
        link_department: str | None = None,
    ) -> dict[str, Any]:
        """Link products to an ESL device (PATCH /v1/stores/{storeId}/devices/{deviceId}/link).

        Returns operation info with operationId and status.
        """
        payload: dict[str, Any] = {"items": items}
        if design:
            payload["design"] = design
        if link_department:
            payload["linkDepartment"] = link_department

        response = await self._request(
            "PATCH",
            f"/v1/stores/{store_id}/devices/{device_id}/link",
            json=payload,
        )
        response.raise_for_status()
        return response.json()

    async def get_operation_status(self, store_id: str, operation_id: str) -> dict[str, Any]:
        """Check async operation status (GET /v1/stores/{storeId}/devices/link/status/{operationId})."""
        response = await self._request("GET", f"/v1/stores/{store_id}/devices/link/status/{operation_id}")
        response.raise_for_status()
        return response.json()


class PricerAdapter(ESLIntegrationAdapter):
    """ESLIntegrationAdapter implementation for Pricer Plaza.

    Reads configuration from the ESLIntegration row:
    - integration.base_url (defaults to https://api.pricer-plaza.com)
    - credentials["client_id"] (required)
    - credentials["client_secret"] (required)
    - credentials["store_id"] (required — the Plaza store ID to operate against)
    """

    def _build_client(self, integration: ESLIntegration, credentials: dict[str, Any]) -> PricerClient:
        base_url = integration.base_url or "https://api.pricer-plaza.com"
        client_id = credentials.get("client_id")
        client_secret = credentials.get("client_secret")
        if not client_id or not client_secret:
            raise ValueError("Pricer credentials require client_id and client_secret")
        return PricerClient(base_url=base_url, client_id=client_id, client_secret=client_secret)

    def _get_store_id(self, credentials: dict[str, Any]) -> str:
        store_id = credentials.get("store_id")
        if not store_id:
            raise ValueError("Pricer credentials require store_id (Pricer Plaza Store ID)")
        return store_id

    async def test_connection(
        self, integration: ESLIntegration, credentials: dict[str, Any]
    ) -> dict[str, Any]:
        """Verifies credentials by obtaining an OAuth2 token."""
        try:
            client = self._build_client(integration, credentials)
            auth_result = await client.authenticate()
            await client.close()
            return {
                "success": True,
                "message": f"Token obtained, expires in {auth_result.get('expires_in', 259200)}s",
            }
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 401:
                return {"success": False, "message": "Invalid client_id or client_secret"}
            return {"success": False, "message": _http_error_message(exc)}
        except httpx.ConnectError:
            return {"success": False, "message": _NETWORK_ERROR_MESSAGE}
        except Exception as exc:
            return {"success": False, "message": str(exc)}

    async def discover_devices(
        self, integration: ESLIntegration, credentials: dict[str, Any]
    ) -> dict[str, Any]:
        """Lists devices in the configured store."""
        try:
            client = self._build_client(integration, credentials)
            store_id = self._get_store_id(credentials)
            devices = await client.get_devices(store_id)
            await client.close()

            mapped = [
                {
                    "device_identifier": d.get("deviceId") or d.get("id") or "",
                    "device_name": d.get("name") or d.get("modelName") or "Pricer Device",
                    "model_hint": d.get("modelName") or d.get("modelType"),
                    "status": d.get("status") or "unknown",
                }
                for d in devices
            ]
            return {"success": True, "message": None, "devices": mapped}
        except httpx.HTTPStatusError as exc:
            return {"success": False, "message": _http_error_message(exc), "devices": []}
        except httpx.ConnectError:
            return {"success": False, "message": _NETWORK_ERROR_MESSAGE, "devices": []}
        except Exception as exc:
            return {"success": False, "message": str(exc), "devices": []}

    async def push_price(
        self,
        integration: ESLIntegration,
        credentials: dict[str, Any],
        *,
        device_identifier: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Pushes a price update by linking the product SKU to the device.

        The payload from the wizard contains:
        - product_name, sku, price, currency, store_id
        We use the SKU as the itemId (Pricer's item identifier).
        """
        try:
            client = self._build_client(integration, credentials)
            store_id = self._get_store_id(credentials)

            sku = payload.get("sku") or ""
            if not sku:
                await client.close()
                return {"success": False, "message": "Product SKU is required for Pricer price push"}

            items = [
                {
                    "itemId": sku,
                    "displayPosition": 0,
                    "facings": "1",
                }
            ]

            op = await client.link_device(store_id, device_identifier, items=items)
            await client.close()

            return {
                "success": True,
                "message": f"Price push accepted (operation {op.get('operationId')})",
                "operation_id": op.get("operationId"),
            }
        except httpx.HTTPStatusError as exc:
            return {"success": False, "message": _http_error_message(exc)}
        except httpx.ConnectError:
            return {"success": False, "message": _NETWORK_ERROR_MESSAGE}
        except Exception as exc:
            return {"success": False, "message": str(exc)}

    async def push_template(
        self,
        integration: ESLIntegration,
        credentials: dict[str, Any],
        *,
        device_identifier: str,
        template: dict[str, Any],
    ) -> dict[str, Any]:
        """Pushes a display template/design change to the device.

        The template dict from the wizard is expected to have a 'design' field
        (the Pricer design/template ID). We call the same link endpoint with
        the design field populated.
        """
        try:
            client = self._build_client(integration, credentials)
            store_id = self._get_store_id(credentials)

            design = template.get("design") if isinstance(template, dict) else None
            if not design:
                await client.close()
                return {
                    "success": False,
                    "message": "Template must include a 'design' field (Pricer template ID)",
                }

            items = [{"itemId": "", "displayPosition": 0, "facings": "1"}]
            op = await client.link_device(store_id, device_identifier, items=items, design=design)
            await client.close()

            return {
                "success": True,
                "message": f"Template push accepted (operation {op.get('operationId')})",
                "operation_id": op.get("operationId"),
            }
        except httpx.HTTPStatusError as exc:
            return {"success": False, "message": _http_error_message(exc)}
        except httpx.ConnectError:
            return {"success": False, "message": _NETWORK_ERROR_MESSAGE}
        except Exception as exc:
            return {"success": False, "message": str(exc)}

    async def get_device_status(
        self, integration: ESLIntegration, credentials: dict[str, Any], *, device_identifier: str
    ) -> dict[str, Any]:
        """Gets live status for a single device (battery, signal, connectivity)."""
        try:
            client = self._build_client(integration, credentials)
            store_id = self._get_store_id(credentials)
            device = await client.get_device(store_id, device_identifier)
            await client.close()

            # Map Plaza fields to our expected shape
            battery_state = device.get("batteryState", "unknown")
            battery_level = 100 if battery_state == "ok" else (20 if battery_state == "low" else None)

            status_val = device.get("status", "unknown")
            if status_val == "linked":
                connectivity = "online"
            elif status_val == "roaming":
                connectivity = "degraded"
            else:
                connectivity = "offline"

            return {
                "success": True,
                "message": None,
                "device_identifier": device_identifier,
                "battery_level": battery_level,
                "battery_state": battery_state,
                "signal_strength": None,  # Plaza uses lastOkUpdate timestamps, not RSSI
                "connectivity": connectivity,
                "last_ok_update": device.get("lastOkUpdate"),
                "last_update": device.get("lastUpdate"),
                "last_display_update": device.get("lastDisplayUpdate"),
                "model_name": device.get("modelName"),
                "firmware_version": device.get("firmwareVersion"),
            }
        except httpx.HTTPStatusError as exc:
            return {"success": False, "message": _http_error_message(exc)}
        except httpx.ConnectError:
            return {"success": False, "message": _NETWORK_ERROR_MESSAGE}
        except Exception as exc:
            return {"success": False, "message": str(exc)}

    async def get_sync_status(
        self, integration: ESLIntegration, credentials: dict[str, Any]
    ) -> dict[str, Any]:
        """Aggregates sync health for the whole integration (store)."""
        try:
            client = self._build_client(integration, credentials)
            store_id = self._get_store_id(credentials)
            devices = await client.get_devices(store_id)
            await client.close()

            linked = sum(1 for d in devices if d.get("status") == "linked")
            roaming = sum(1 for d in devices if d.get("status") == "roaming")
            not_found = sum(1 for d in devices if d.get("status") == "not_found")
            total = len(devices)

            # Find the most recent successful update across all devices
            last_ok_updates = [
                d.get("lastOkUpdate") for d in devices if d.get("lastOkUpdate")
            ]
            last_sync = max(last_ok_updates) if last_ok_updates else None

            return {
                "success": True,
                "message": None,
                "integration_id": str(integration.id),
                "linked_count": linked,
                "roaming_count": roaming,
                "offline_count": not_found,
                "total_devices": total,
                "last_sync": last_sync,
                "status": "healthy"
                if not_found == 0 and roaming == 0
                else ("degraded" if roaming > 0 else "critical"),
            }
        except httpx.HTTPStatusError as exc:
            return {"success": False, "message": _http_error_message(exc)}
        except httpx.ConnectError:
            return {"success": False, "message": _NETWORK_ERROR_MESSAGE}
        except Exception as exc:
            return {"success": False, "message": str(exc)}