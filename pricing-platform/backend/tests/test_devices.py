from fastapi.testclient import TestClient

from tests.conftest import DEVICE_MODEL_ID, DEVICE_VENDOR_ID
from tests.helpers import add_user_with_role, auth_headers, device_payload, register, store_payload


def _setup_store(client: TestClient, tokens: dict, **overrides) -> dict:
    response = client.post(
        "/api/v1/stores", json=store_payload(**overrides), headers=auth_headers(tokens)
    )
    return response.json()["data"]


def test_list_vendors_and_models(client: TestClient) -> None:
    tokens = register(client)

    vendors = client.get("/api/v1/devices/vendors", headers=auth_headers(tokens))
    models = client.get("/api/v1/devices/models", headers=auth_headers(tokens))

    assert vendors.status_code == 200
    assert any(v["code"] == "esl_simulator" for v in vendors.json()["data"])
    assert models.status_code == 200
    assert any(m["model_code"] == "SIM-1" for m in models.json()["data"])


def test_models_filtered_by_vendor(client: TestClient) -> None:
    tokens = register(client)

    response = client.get(
        "/api/v1/devices/models", params={"vendor_id": str(DEVICE_VENDOR_ID)}, headers=auth_headers(tokens)
    )

    assert response.status_code == 200
    assert all(m["vendor_id"] == str(DEVICE_VENDOR_ID) for m in response.json()["data"])


def test_create_device_success(client: TestClient) -> None:
    tokens = register(client)
    store = _setup_store(client, tokens)

    response = client.post(
        "/api/v1/devices",
        json=device_payload(
            store_id=store["id"], vendor_id=str(DEVICE_VENDOR_ID), device_model_id=str(DEVICE_MODEL_ID)
        ),
        headers=auth_headers(tokens),
    )

    assert response.status_code == 201, response.text
    data = response.json()["data"]
    assert data["device_name"] == "Aisle 1 Shelf Tag"
    assert data["status"] == "active"
    assert data["battery_level"] == 100
    assert data["signal_strength"] == 95
    assert data["firmware_version"] == "1.0.0-sim"


def test_create_device_rejects_duplicate_identifier(client: TestClient) -> None:
    tokens = register(client)
    store = _setup_store(client, tokens)
    payload = device_payload(
        store_id=store["id"], vendor_id=str(DEVICE_VENDOR_ID), device_model_id=str(DEVICE_MODEL_ID)
    )
    client.post("/api/v1/devices", json=payload, headers=auth_headers(tokens))

    response = client.post("/api/v1/devices", json=payload, headers=auth_headers(tokens))

    assert response.status_code == 409


def test_create_device_rejects_unknown_vendor(client: TestClient) -> None:
    tokens = register(client)
    store = _setup_store(client, tokens)

    response = client.post(
        "/api/v1/devices",
        json=device_payload(
            store_id=store["id"],
            vendor_id="00000000-0000-0000-0000-000000000000",
            device_model_id=str(DEVICE_MODEL_ID),
        ),
        headers=auth_headers(tokens),
    )

    assert response.status_code == 404


def test_list_devices_filters_by_store(client: TestClient) -> None:
    tokens = register(client)
    store_a = _setup_store(client, tokens, store_code="A-1")
    store_b = _setup_store(client, tokens, store_code="B-1")
    client.post(
        "/api/v1/devices",
        json=device_payload(
            store_id=store_a["id"],
            vendor_id=str(DEVICE_VENDOR_ID),
            device_model_id=str(DEVICE_MODEL_ID),
            device_identifier="SIM-A",
        ),
        headers=auth_headers(tokens),
    )
    client.post(
        "/api/v1/devices",
        json=device_payload(
            store_id=store_b["id"],
            vendor_id=str(DEVICE_VENDOR_ID),
            device_model_id=str(DEVICE_MODEL_ID),
            device_identifier="SIM-B",
        ),
        headers=auth_headers(tokens),
    )

    response = client.get("/api/v1/devices", params={"store_id": store_a["id"]}, headers=auth_headers(tokens))

    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["device_identifier"] == "SIM-A"


def test_update_device(client: TestClient) -> None:
    tokens = register(client)
    store = _setup_store(client, tokens)
    device = client.post(
        "/api/v1/devices",
        json=device_payload(
            store_id=store["id"], vendor_id=str(DEVICE_VENDOR_ID), device_model_id=str(DEVICE_MODEL_ID)
        ),
        headers=auth_headers(tokens),
    ).json()["data"]

    response = client.put(
        f"/api/v1/devices/{device['id']}",
        json={"device_name": "Renamed Tag", "status": "maintenance"},
        headers=auth_headers(tokens),
    )

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["device_name"] == "Renamed Tag"
    assert data["status"] == "maintenance"


def test_device_not_visible_across_organizations(client: TestClient) -> None:
    tokens_a = register(client, organization_name="Org A", email="a@example.com")
    store = _setup_store(client, tokens_a)
    device = client.post(
        "/api/v1/devices",
        json=device_payload(
            store_id=store["id"], vendor_id=str(DEVICE_VENDOR_ID), device_model_id=str(DEVICE_MODEL_ID)
        ),
        headers=auth_headers(tokens_a),
    ).json()["data"]

    tokens_b = register(client, organization_name="Org B", email="b@example.com")
    response = client.get(f"/api/v1/devices/{device['id']}", headers=auth_headers(tokens_b))

    assert response.status_code == 404


def test_viewer_cannot_create_device(client: TestClient, db_session) -> None:
    tokens = register(client)
    me = client.get("/api/v1/auth/me", headers=auth_headers(tokens)).json()["data"]
    store = _setup_store(client, tokens)
    import uuid as uuid_module

    viewer = add_user_with_role(
        db_session,
        organization_id=uuid_module.UUID(me["organization"]["id"]),
        email="viewer@example.com",
        role_name="Viewer",
    )
    viewer_tokens = client.post(
        "/api/v1/auth/login", json={"email": viewer.email, "password": "SuperSecret1"}
    ).json()["data"]

    response = client.post(
        "/api/v1/devices",
        json=device_payload(
            store_id=store["id"], vendor_id=str(DEVICE_VENDOR_ID), device_model_id=str(DEVICE_MODEL_ID)
        ),
        headers=auth_headers(viewer_tokens),
    )

    assert response.status_code == 403


def test_delete_device_removes_it_with_its_assignments_and_sync_logs(client: TestClient) -> None:
    from tests.helpers import category_payload, device_assignment_payload, product_payload

    tokens = register(client)
    store = _setup_store(client, tokens)
    category = client.post(
        "/api/v1/categories", json=category_payload(), headers=auth_headers(tokens)
    ).json()["data"]
    product = client.post(
        "/api/v1/products",
        json=product_payload(category_id=category["id"]),
        headers=auth_headers(tokens),
    ).json()["data"]
    device = client.post(
        "/api/v1/devices",
        json=device_payload(
            store_id=store["id"], vendor_id=str(DEVICE_VENDOR_ID), device_model_id=str(DEVICE_MODEL_ID)
        ),
        headers=auth_headers(tokens),
    ).json()["data"]
    # Creates an active assignment and (via the immediate sync) a sync log.
    client.post(
        "/api/v1/devices/assignments",
        json=device_assignment_payload(
            device_id=device["id"], store_id=store["id"], product_id=product["id"]
        ),
        headers=auth_headers(tokens),
    )

    response = client.delete(f"/api/v1/devices/{device['id']}", headers=auth_headers(tokens))

    assert response.status_code == 200, response.text
    assert response.json()["data"] == {"deleted": True}
    assert client.get(f"/api/v1/devices/{device['id']}", headers=auth_headers(tokens)).status_code == 404


def test_delete_device_not_allowed_across_organizations(client: TestClient) -> None:
    tokens_a = register(client, organization_name="Org A", email="a@example.com")
    store = _setup_store(client, tokens_a)
    device = client.post(
        "/api/v1/devices",
        json=device_payload(
            store_id=store["id"], vendor_id=str(DEVICE_VENDOR_ID), device_model_id=str(DEVICE_MODEL_ID)
        ),
        headers=auth_headers(tokens_a),
    ).json()["data"]

    tokens_b = register(client, organization_name="Org B", email="b@example.com")
    response = client.delete(f"/api/v1/devices/{device['id']}", headers=auth_headers(tokens_b))

    assert response.status_code == 404
    assert client.get(f"/api/v1/devices/{device['id']}", headers=auth_headers(tokens_a)).status_code == 200


def test_viewer_cannot_delete_device(client: TestClient, db_session) -> None:
    import uuid as uuid_module

    tokens = register(client)
    me = client.get("/api/v1/auth/me", headers=auth_headers(tokens)).json()["data"]
    store = _setup_store(client, tokens)
    device = client.post(
        "/api/v1/devices",
        json=device_payload(
            store_id=store["id"], vendor_id=str(DEVICE_VENDOR_ID), device_model_id=str(DEVICE_MODEL_ID)
        ),
        headers=auth_headers(tokens),
    ).json()["data"]
    viewer = add_user_with_role(
        db_session,
        organization_id=uuid_module.UUID(me["organization"]["id"]),
        email="viewer@example.com",
        role_name="Viewer",
    )
    viewer_tokens = client.post(
        "/api/v1/auth/login", json={"email": viewer.email, "password": "SuperSecret1"}
    ).json()["data"]

    response = client.delete(f"/api/v1/devices/{device['id']}", headers=auth_headers(viewer_tokens))

    assert response.status_code == 403
