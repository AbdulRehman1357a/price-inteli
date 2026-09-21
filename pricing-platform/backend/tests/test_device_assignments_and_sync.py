from fastapi.testclient import TestClient

from tests.conftest import DEVICE_MODEL_ID, DEVICE_VENDOR_ID
from tests.helpers import (
    auth_headers,
    category_payload,
    device_assignment_payload,
    device_payload,
    product_payload,
    register,
    store_payload,
)


def _setup(client: TestClient, tokens: dict, **product_overrides) -> tuple[dict, dict]:
    store = client.post("/api/v1/stores", json=store_payload(), headers=auth_headers(tokens)).json()["data"]
    category = client.post(
        "/api/v1/categories", json=category_payload(), headers=auth_headers(tokens)
    ).json()["data"]
    product = client.post(
        "/api/v1/products",
        json=product_payload(category_id=category["id"], **product_overrides),
        headers=auth_headers(tokens),
    ).json()["data"]
    device = client.post(
        "/api/v1/devices",
        json=device_payload(
            store_id=store["id"], vendor_id=str(DEVICE_VENDOR_ID), device_model_id=str(DEVICE_MODEL_ID)
        ),
        headers=auth_headers(tokens),
    ).json()["data"]
    return store, {"product": product, "device": device}


def test_assign_product_success_and_triggers_sync(client: TestClient) -> None:
    tokens = register(client)
    store, ctx = _setup(client, tokens, selling_price="49.9900")

    response = client.post(
        "/api/v1/devices/assignments",
        json=device_assignment_payload(
            device_id=ctx["device"]["id"], store_id=store["id"], product_id=ctx["product"]["id"]
        ),
        headers=auth_headers(tokens),
    )

    assert response.status_code == 201, response.text
    assert response.json()["data"]["status"] == "active"

    device = client.get(f"/api/v1/devices/{ctx['device']['id']}", headers=auth_headers(tokens)).json()["data"]
    assert device["last_sync_at"] is not None

    logs = client.get(
        f"/api/v1/devices/{ctx['device']['id']}/sync-logs", headers=auth_headers(tokens)
    ).json()["data"]
    assert len(logs) == 1
    assert logs[0]["status"] == "success"


def test_assign_product_rejects_store_mismatch(client: TestClient) -> None:
    tokens = register(client)
    store, ctx = _setup(client, tokens)
    other_store = client.post(
        "/api/v1/stores", json=store_payload(store_code="OTHER-1"), headers=auth_headers(tokens)
    ).json()["data"]

    response = client.post(
        "/api/v1/devices/assignments",
        json=device_assignment_payload(
            device_id=ctx["device"]["id"], store_id=other_store["id"], product_id=ctx["product"]["id"]
        ),
        headers=auth_headers(tokens),
    )

    assert response.status_code == 409


def test_new_assignment_ends_previous_one(client: TestClient) -> None:
    tokens = register(client)
    store, ctx = _setup(client, tokens)
    category = client.get("/api/v1/categories", headers=auth_headers(tokens)).json()["data"][0]
    second_product = client.post(
        "/api/v1/products",
        json=product_payload(category_id=category["id"], sku="SKU-002", product_name="Second Product"),
        headers=auth_headers(tokens),
    ).json()["data"]

    first = client.post(
        "/api/v1/devices/assignments",
        json=device_assignment_payload(
            device_id=ctx["device"]["id"], store_id=store["id"], product_id=ctx["product"]["id"]
        ),
        headers=auth_headers(tokens),
    ).json()["data"]

    second = client.post(
        "/api/v1/devices/assignments",
        json=device_assignment_payload(
            device_id=ctx["device"]["id"], store_id=store["id"], product_id=second_product["id"]
        ),
        headers=auth_headers(tokens),
    ).json()["data"]

    assert second["status"] == "active"
    active = client.get(
        f"/api/v1/devices/{ctx['device']['id']}/assignment", headers=auth_headers(tokens)
    ).json()["data"]
    assert active["id"] == second["id"]
    assert active["product_id"] == second_product["id"]

    logs = client.get(
        f"/api/v1/devices/{ctx['device']['id']}/sync-logs", headers=auth_headers(tokens)
    ).json()["data"]
    assert len(logs) == 2
    assert first["id"] != second["id"]


def test_unassign_ends_assignment(client: TestClient) -> None:
    tokens = register(client)
    store, ctx = _setup(client, tokens)
    assignment = client.post(
        "/api/v1/devices/assignments",
        json=device_assignment_payload(
            device_id=ctx["device"]["id"], store_id=store["id"], product_id=ctx["product"]["id"]
        ),
        headers=auth_headers(tokens),
    ).json()["data"]

    response = client.post(
        f"/api/v1/devices/assignments/{assignment['id']}/unassign", headers=auth_headers(tokens)
    )

    assert response.status_code == 200, response.text
    assert response.json()["data"]["status"] == "ended"
    assert response.json()["data"]["unassigned_at"] is not None

    active = client.get(
        f"/api/v1/devices/{ctx['device']['id']}/assignment", headers=auth_headers(tokens)
    ).json()["data"]
    assert active is None


def test_unassign_twice_conflicts(client: TestClient) -> None:
    tokens = register(client)
    store, ctx = _setup(client, tokens)
    assignment = client.post(
        "/api/v1/devices/assignments",
        json=device_assignment_payload(
            device_id=ctx["device"]["id"], store_id=store["id"], product_id=ctx["product"]["id"]
        ),
        headers=auth_headers(tokens),
    ).json()["data"]
    client.post(f"/api/v1/devices/assignments/{assignment['id']}/unassign", headers=auth_headers(tokens))

    response = client.post(
        f"/api/v1/devices/assignments/{assignment['id']}/unassign", headers=auth_headers(tokens)
    )

    assert response.status_code == 409


def test_manual_resync_uses_active_assignment(client: TestClient) -> None:
    tokens = register(client)
    store, ctx = _setup(client, tokens, selling_price="19.9900")
    client.post(
        "/api/v1/devices/assignments",
        json=device_assignment_payload(
            device_id=ctx["device"]["id"], store_id=store["id"], product_id=ctx["product"]["id"]
        ),
        headers=auth_headers(tokens),
    )

    response = client.post(f"/api/v1/devices/{ctx['device']['id']}/sync", headers=auth_headers(tokens))

    assert response.status_code == 200, response.text
    assert response.json()["data"]["status"] == "success"


def test_resync_without_assignment_conflicts(client: TestClient) -> None:
    tokens = register(client)
    store, ctx = _setup(client, tokens)

    response = client.post(f"/api/v1/devices/{ctx['device']['id']}/sync", headers=auth_headers(tokens))

    assert response.status_code == 409


def test_device_health_reflects_simulated_telemetry(client: TestClient) -> None:
    tokens = register(client)
    store, ctx = _setup(client, tokens)
    client.post(
        "/api/v1/devices/assignments",
        json=device_assignment_payload(
            device_id=ctx["device"]["id"], store_id=store["id"], product_id=ctx["product"]["id"]
        ),
        headers=auth_headers(tokens),
    )

    response = client.get(f"/api/v1/devices/{ctx['device']['id']}/health", headers=auth_headers(tokens))

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["connectivity"] == "online"
    assert 0 <= data["battery_level"] <= 100
    assert data["last_seen_at"] is not None
