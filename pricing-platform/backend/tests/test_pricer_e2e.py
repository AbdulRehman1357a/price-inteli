"""End-to-end tests for the Pricer Plaza adapter running against the local simulator.

These tests perform real HTTP round-trips (no mocking) against the in-process
Pricer Plaza simulator (app.integrations.esl.pricer_simulator).
"""
from __future__ import annotations

import threading
from typing import Any

import httpx
import pytest
import uvicorn

from app.integrations.esl.pricer_adapter import PricerAdapter, PricerClient
from app.integrations.esl.pricer_simulator import app as simulator_app

# ---------------------------------------------------------------------------
# Fixture: start the simulator on a free port
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def sim_server() -> str:
    """Start the Pricer simulator on a free port in a background thread.

    Yields the base URL (e.g. http://127.0.0.1:8091) for use in tests.
    """
    port = 8091  # avoid conflicts with 8090 default
    config = uvicorn.Config(app=simulator_app, host="127.0.0.1", port=port, log_level="error")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    import time
    for _ in range(50):
        if server.started:
            break
        time.sleep(0.1)

    yield f"http://127.0.0.1:{port}"
    server.should_exit = True
    thread.join(timeout=3)


def _integration(base_url: str) -> Any:
    """Create a mock ESLIntegration with the given base_url."""

    class _Integration:
        def __init__(self) -> None:
            self.id = "00000000-0000-0000-0000-000000000001"
            self.base_url = base_url
            self.organization_id = "00000000-0000-0000-0000-000000000099"
            self.last_sync_at = None

    return _Integration()


def _creds(
    client_id: str = "test-client",
    client_secret: str = "test-secret",
    store_id: str = "store-1",
) -> dict[str, str]:
    return {"client_id": client_id, "client_secret": client_secret, "store_id": store_id}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestPricerE2E:
    """Live HTTP E2E tests against the simulator."""

    def test_authenticate_success(self, sim_server: str) -> None:
        """Valid credentials → token obtained."""
        client = PricerClient(
            base_url=sim_server,
            client_id="test-client",
            client_secret="test-secret",
        )
        import asyncio
        result = asyncio.get_event_loop().run_until_complete(client.authenticate())
        assert "access_token" in result
        assert result["token_type"] == "Bearer"
        assert result["expires_in"] == 259200

    def test_authenticate_invalid_credentials(self, sim_server: str) -> None:
        """Wrong credentials → 401."""
        client = PricerClient(base_url=sim_server, client_id="bad", client_secret="creds")
        import asyncio
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            asyncio.get_event_loop().run_until_complete(client.authenticate())
        assert exc_info.value.response.status_code == 401

    def test_list_stores(self, sim_server: str) -> None:
        """GET /v1/stores → 2 fake stores."""
        client = PricerClient(
            base_url=sim_server,
            client_id="test-client",
            client_secret="test-secret",
        )
        import asyncio
        asyncio.get_event_loop().run_until_complete(client.authenticate())
        stores = asyncio.get_event_loop().run_until_complete(client.get_stores())
        assert len(stores) == 2
        assert stores[0]["storeId"] == "store-1"

    def test_list_devices(self, sim_server: str) -> None:
        """GET /v1/stores/{storeId}/devices → 3 devices for store-1."""
        client = PricerClient(
            base_url=sim_server,
            client_id="test-client",
            client_secret="test-secret",
        )
        import asyncio
        asyncio.get_event_loop().run_until_complete(client.authenticate())
        devices = asyncio.get_event_loop().run_until_complete(client.get_devices("store-1"))
        assert len(devices) == 3
        ids = [d["deviceId"] for d in devices]
        assert "PRX-001" in ids
        assert "PRX-003" in ids

    def test_get_single_device(self, sim_server: str) -> None:
        """GET /v1/stores/{storeId}/devices/{deviceId} → device detail."""
        client = PricerClient(
            base_url=sim_server,
            client_id="test-client",
            client_secret="test-secret",
        )
        import asyncio
        asyncio.get_event_loop().run_until_complete(client.authenticate())
        device = asyncio.get_event_loop().run_until_complete(client.get_device("store-1", "PRX-001"))
        assert device["deviceId"] == "PRX-001"
        assert device["batteryState"] == "ok"
        assert device["status"] == "linked"

    def test_link_device_pushes_price(self, sim_server: str) -> None:
        """PATCH /devices/{deviceId}/link → operation accepted, device updated."""
        client = PricerClient(
            base_url=sim_server,
            client_id="test-client",
            client_secret="test-secret",
        )
        import asyncio
        asyncio.get_event_loop().run_until_complete(client.authenticate())

        items = [{"itemId": "NEW-SKU", "displayPosition": 0, "facings": "1"}]
        op = asyncio.get_event_loop().run_until_complete(
            client.link_device("store-1", "PRX-002", items=items)
        )
        assert "operationId" in op
        assert op["status"] == "accepted"

        # Verify the device was updated
        device = asyncio.get_event_loop().run_until_complete(client.get_device("store-1", "PRX-002"))
        assert device["status"] == "linked"
        assert device["link"]["items"][0]["itemId"] == "NEW-SKU"

    def test_operation_status(self, sim_server: str) -> None:
        """GET /devices/link/status/{operationId} → completed."""
        client = PricerClient(
            base_url=sim_server,
            client_id="test-client",
            client_secret="test-secret",
        )
        import asyncio
        asyncio.get_event_loop().run_until_complete(client.authenticate())

        items = [{"itemId": "SKU-X", "displayPosition": 0, "facings": "1"}]
        op = asyncio.get_event_loop().run_until_complete(
            client.link_device("store-1", "PRX-001", items=items)
        )
        status = asyncio.get_event_loop().run_until_complete(
            client.get_operation_status("store-1", op["operationId"])
        )
        assert status["status"] == "completed"
        assert status["processedCount"] == 1

    def test_adapter_test_connection(self, sim_server: str) -> None:
        """PricerAdapter.test_connection against the simulator."""
        adapter = PricerAdapter()
        integration = _integration(sim_server)
        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            adapter.test_connection(integration, _creds())
        )
        assert result["success"] is True
        assert "expires in" in result["message"]

    def test_adapter_test_connection_bad_creds(self, sim_server: str) -> None:
        """PricerAdapter.test_connection with wrong creds → graceful failure."""
        adapter = PricerAdapter()
        integration = _integration(sim_server)
        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            adapter.test_connection(integration, _creds(client_id="wrong", client_secret="creds"))
        )
        assert result["success"] is False
        assert "Invalid" in result["message"] or "401" in result["message"]

    def test_adapter_discover_devices(self, sim_server: str) -> None:
        """PricerAdapter.discover_devices against the simulator."""
        adapter = PricerAdapter()
        integration = _integration(sim_server)
        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            adapter.discover_devices(integration, _creds())
        )
        assert result["success"] is True
        assert len(result["devices"]) == 3
        assert result["devices"][0]["device_identifier"] == "PRX-001"

    def test_adapter_push_price(self, sim_server: str) -> None:
        """PricerAdapter.push_price against the simulator."""
        adapter = PricerAdapter()
        integration = _integration(sim_server)
        import asyncio
        payload = {
                "product_name": "Milk 1L",
                "sku": "SKU-MILK-001",
                "price": "3.99",
                "currency": "SEK",
            }
        result = asyncio.get_event_loop().run_until_complete(
            adapter.push_price(
                integration,
                _creds(),
                device_identifier="PRX-001",
                payload=payload,
            )
        )
        assert result["success"] is True
        assert "operation_id" in result

    def test_adapter_get_device_status(self, sim_server: str) -> None:
        """PricerAdapter.get_device_status against the simulator."""
        adapter = PricerAdapter()
        integration = _integration(sim_server)
        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            adapter.get_device_status(integration, _creds(), device_identifier="PRX-001")
        )
        assert result["success"] is True
        assert result["battery_state"] == "ok"
        assert result["connectivity"] == "online"

    def test_adapter_get_sync_status(self, sim_server: str) -> None:
        """PricerAdapter.get_sync_status against the simulator."""
        adapter = PricerAdapter()
        integration = _integration(sim_server)
        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            adapter.get_sync_status(integration, _creds())
        )
        assert result["success"] is True
        assert result["linked_count"] == 2
        assert result["roaming_count"] == 1
        assert result["total_devices"] == 3

    def test_adapter_device_not_found(self, sim_server: str) -> None:
        """PricerAdapter.get_device_status for non-existent device → 404 → failure."""
        adapter = PricerAdapter()
        integration = _integration(sim_server)
        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            adapter.get_device_status(integration, _creds(), device_identifier="NON-EXISTENT")
        )
        assert result["success"] is False
        assert "404" in result["message"]

    def test_adapter_missing_credentials(self, sim_server: str) -> None:
        """PricerAdapter with missing credentials → graceful ValueError."""
        adapter = PricerAdapter()
        integration = _integration(sim_server)
        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            adapter.test_connection(integration, {})
        )
        assert result["success"] is False
        assert "client_id" in result["message"] or "credentials" in result["message"].lower()