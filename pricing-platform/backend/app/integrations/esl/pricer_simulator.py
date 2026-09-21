from __future__ import annotations

import argparse
import copy
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

# ---------------------------------------------------------------------------
# Fake state (in-memory)
# ---------------------------------------------------------------------------

_FAKE_STORES: list[dict[str, Any]] = [
    {
        "storeId": "store-1",
        "name": "Pricer Test Store",
        "address": {"street": "123 Main St", "city": "Stockholm", "country": "SE"},
        "timeZone": "Europe/Stockholm",
        "size": "small",
    },
    {
        "storeId": "store-2",
        "name": "Pricer Demo Location",
        "address": {"street": "456 Oak Ave", "city": "Malmö", "country": "SE"},
        "timeZone": "Europe/Stockholm",
        "size": "medium",
    },
]

_DEFAULT_DEVICES: dict[str, list[dict[str, Any]]] = {
    "store-1": [
        {
            "deviceId": "PRX-001",
            "modelName": "PricerXT",
            "modelType": "shelf_label",
            "hardwareRevision": "2.1",
            "firmwareVersion": "3.4.2",
            "status": "linked",
            "batteryState": "ok",
            "batteryStateChanged": "2026-09-01T10:00:00Z",
            "batteryStateLastConfirmed": "2026-09-13T08:00:00Z",
            "lastOkUpdate": "2026-09-13T08:15:00Z",
            "lastUpdate": "2026-09-13T08:15:00Z",
            "lastDisplayUpdate": "2026-09-13T08:14:30Z",
            "positions": [{"x": 1, "y": 2, "floor": 1}],
            "link": {
                "design": "default-price",
                "linkDepartment": "grocery",
                "items": [{"itemId": "SKU-001", "displayPosition": 0, "facings": "1"}],
            },
        },
        {
            "deviceId": "PRX-002",
            "modelName": "PricerXT",
            "modelType": "shelf_label",
            "hardwareRevision": "2.1",
            "firmwareVersion": "3.4.2",
            "status": "linked",
            "batteryState": "ok",
            "batteryStateChanged": "2026-08-15T12:00:00Z",
            "batteryStateLastConfirmed": "2026-09-13T07:30:00Z",
            "lastOkUpdate": "2026-09-13T07:45:00Z",
            "lastUpdate": "2026-09-13T07:45:00Z",
            "lastDisplayUpdate": "2026-09-13T07:44:00Z",
            "positions": [{"x": 1, "y": 4, "floor": 1}],
            "link": {
                "design": "default-price",
                "linkDepartment": "grocery",
                "items": [],
            },
        },
        {
            "deviceId": "PRX-003",
            "modelName": "PricerS",
            "modelType": "shelf_label",
            "hardwareRevision": "1.3",
            "firmwareVersion": "2.8.0",
            "status": "roaming",
            "batteryState": "low",
            "batteryStateChanged": "2026-09-12T18:00:00Z",
            "batteryStateLastConfirmed": "2026-09-13T06:00:00Z",
            "lastOkUpdate": "2026-09-12T18:00:00Z",
            "lastUpdate": "2026-09-13T06:00:00Z",
            "lastDisplayUpdate": "2026-09-12T17:55:00Z",
            "positions": [],
            "link": {"design": None, "linkDepartment": None, "items": []},
        },
    ],
    "store-2": [],
}

_FAKE_DEVICES: dict[str, list[dict[str, Any]]] = copy.deepcopy(_DEFAULT_DEVICES)

_FAKE_OPERATIONS: dict[str, dict[str, Any]] = {}

_SIM_VALID_CLIENTS: dict[str, str] = {
    "test-client": "test-secret",
    "demo-client": "demo-secret",
}

SIM_REQUIRE_AUTH = False


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(title="Pricer Plaza API Simulator", version="1.0.0")


@app.post("/v2/oauth/token")
async def oauth_token(request: Request) -> JSONResponse:
    """OAuth2 client_credentials token endpoint."""
    content_type = request.headers.get("content-type", "")

    if "application/x-www-form-urlencoded" in content_type:
        form = await request.form()
        client_id = form.get("client_id")
        client_secret = form.get("client_secret")
        grant_type = form.get("grant_type")
    else:
        body = await request.json()
        client_id = body.get("client_id")
        client_secret = body.get("client_secret")
        grant_type = body.get("grant_type")

    if grant_type != "client_credentials":
        raise HTTPException(status_code=400, detail={"error": "unsupported_grant_type"})

    if client_id not in _SIM_VALID_CLIENTS or _SIM_VALID_CLIENTS[client_id] != client_secret:
        raise HTTPException(status_code=401, detail={"error": "invalid_client"})

    token = f"sim-token-{uuid.uuid4().hex}"
    return JSONResponse(
        {"access_token": token, "token_type": "Bearer", "expires_in": 259200}
    )


@app.get("/v1/stores")
async def list_stores() -> list[dict[str, Any]]:
    """List all stores."""
    return _FAKE_STORES


@app.get("/v1/stores/{store_id}")
async def get_store(store_id: str) -> dict[str, Any]:
    """Get a single store."""
    for s in _FAKE_STORES:
        if s["storeId"] == store_id:
            return s
    raise HTTPException(status_code=404, detail="Store not found")


@app.get("/v1/stores/{store_id}/devices")
async def list_devices(
    store_id: str,
    status: str | None = None,
    modelName: str | None = None,
    deviceId: str | None = None,
) -> list[dict[str, Any]]:
    """List devices for a store with optional filters."""
    if store_id not in _FAKE_DEVICES:
        raise HTTPException(status_code=404, detail="Store not found")

    devices = _FAKE_DEVICES[store_id]

    if status:
        devices = [d for d in devices if d["status"] == status]
    if modelName:
        devices = [d for d in devices if d["modelName"] == modelName]
    if deviceId:
        devices = [d for d in devices if d["deviceId"] == deviceId]

    return devices


@app.get("/v1/stores/{store_id}/devices/{device_id}")
async def get_device(store_id: str, device_id: str) -> dict[str, Any]:
    """Get a single device."""
    if store_id not in _FAKE_DEVICES:
        raise HTTPException(status_code=404, detail="Store not found")

    for d in _FAKE_DEVICES[store_id]:
        if d["deviceId"] == device_id:
            return d
    raise HTTPException(status_code=404, detail="Device not found")


@app.patch("/v1/stores/{store_id}/devices/{device_id}/link")
async def link_device(store_id: str, device_id: str, request: Request) -> dict[str, Any]:
    """Link products to an ESL device (price update + template).

    Stores the operation and marks it as completed immediately.
    """
    if store_id not in _FAKE_DEVICES:
        raise HTTPException(status_code=404, detail="Store not found")

    device = None
    for d in _FAKE_DEVICES[store_id]:
        if d["deviceId"] == device_id:
            device = d
            break
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")

    body = await request.json()

    # Update device link state (simulating a successful push)
    if body.get("design"):
        device["link"]["design"] = body["design"]
    if body.get("linkDepartment"):
        device["link"]["linkDepartment"] = body["linkDepartment"]
    if body.get("items"):
        device["link"]["items"] = body["items"]
        device["status"] = "linked"
    device["lastUpdate"] = datetime.now(UTC).isoformat()
    device["lastDisplayUpdate"] = datetime.now(UTC).isoformat()
    device["lastOkUpdate"] = datetime.now(UTC).isoformat()

    op_id = f"op-{uuid.uuid4().hex[:12]}"
    _FAKE_OPERATIONS[op_id] = {
        "operationId": op_id,
        "status": "completed",
        "processedCount": len(body.get("items", [])),
        "failureCount": 0,
        "completedAt": datetime.now(UTC).isoformat(),
    }

    return {"operationId": op_id, "status": "accepted"}


@app.get("/v1/stores/{store_id}/devices/link/status/{operation_id}")
async def get_operation_status(store_id: str, operation_id: str) -> dict[str, Any]:
    """Check the status of an async link/unlink operation."""
    op = _FAKE_OPERATIONS.get(operation_id)
    if op is None:
        raise HTTPException(status_code=404, detail="Operation not found")
    return op


# ---------------------------------------------------------------------------
# Simulated test device state management (for testing against the simulator)
# ---------------------------------------------------------------------------

@app.post("/_sim/reset")
async def sim_reset() -> dict[str, str]:
    """Reset all simulator state to defaults. Test-only endpoint."""
    global _FAKE_DEVICES, _FAKE_OPERATIONS  # noqa: PLW0603
    _FAKE_DEVICES = copy.deepcopy(_DEFAULT_DEVICES)
    _FAKE_OPERATIONS = {}
    return {"status": "reset"}


if __name__ == "__main__":
    import uvicorn

    parser = argparse.ArgumentParser(description="Pricer Plaza API Simulator")
    parser.add_argument("--port", type=int, default=8090, help="Port to listen on (default: 8090)")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")
    args = parser.parse_args()

    print(f"Pricer Plaza API Simulator starting on http://{args.host}:{args.port}")
    print("Default credentials: test-client / test-secret, store_id: store-1")
    uvicorn.run(app, host=args.host, port=args.port)