from fastapi.testclient import TestClient

from tests.conftest import MOCK_MODEL_ID, MOCK_VENDOR_ID, STUB_VENDOR_IDS
from tests.helpers import (
    auth_headers,
    category_payload,
    device_assignment_payload,
    esl_integration_payload,
    product_payload,
    register,
    store_payload,
)


def _setup_store_and_product(client: TestClient, tokens: dict, **product_overrides) -> tuple[dict, dict]:
    store = client.post("/api/v1/stores", json=store_payload(), headers=auth_headers(tokens)).json()["data"]
    category = client.post(
        "/api/v1/categories", json=category_payload(), headers=auth_headers(tokens)
    ).json()["data"]
    product = client.post(
        "/api/v1/products",
        json=product_payload(category_id=category["id"], **product_overrides),
        headers=auth_headers(tokens),
    ).json()["data"]
    return store, product


def test_create_integration_starts_pending_and_hides_credentials(client: TestClient) -> None:
    tokens = register(client)
    store = client.post("/api/v1/stores", json=store_payload(), headers=auth_headers(tokens)).json()["data"]

    response = client.post(
        "/api/v1/esl-integrations",
        json=esl_integration_payload(vendor_id=str(MOCK_VENDOR_ID), store_id=store["id"]),
        headers=auth_headers(tokens),
    )

    assert response.status_code == 201, response.text
    data = response.json()["data"]
    assert data["status"] == "pending"
    assert data["name"] == "Mock Integration"
    assert "credentials" not in data
    assert "configuration_encrypted" not in data


def test_test_connection_succeeds_for_mock_vendor(client: TestClient) -> None:
    tokens = register(client)
    store = client.post("/api/v1/stores", json=store_payload(), headers=auth_headers(tokens)).json()["data"]
    integration = client.post(
        "/api/v1/esl-integrations",
        json=esl_integration_payload(vendor_id=str(MOCK_VENDOR_ID), store_id=store["id"]),
        headers=auth_headers(tokens),
    ).json()["data"]

    response = client.post(
        f"/api/v1/esl-integrations/{integration['id']}/test-connection", headers=auth_headers(tokens)
    )

    assert response.status_code == 200, response.text
    assert response.json()["data"]["success"] is True

    refreshed = client.get(f"/api/v1/esl-integrations/{integration['id']}", headers=auth_headers(tokens))
    assert refreshed.json()["data"]["status"] == "active"


def test_test_connection_fails_gracefully_for_stub_vendor(client: TestClient) -> None:
    tokens = register(client)
    store = client.post("/api/v1/stores", json=store_payload(), headers=auth_headers(tokens)).json()["data"]

    integration = client.post(
        "/api/v1/esl-integrations",
        json=esl_integration_payload(
            vendor_id=str(STUB_VENDOR_IDS["vusion"]),
            store_id=store["id"],
            name="Vusion Test",
            integration_type="api",
        ),
        headers=auth_headers(tokens),
    ).json()["data"]

    response = client.post(
        f"/api/v1/esl-integrations/{integration['id']}/test-connection", headers=auth_headers(tokens)
    )

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["success"] is False
    assert "Vusion" in data["message"]
    assert "not available" in data["message"]

    refreshed = client.get(f"/api/v1/esl-integrations/{integration['id']}", headers=auth_headers(tokens))
    assert refreshed.json()["data"]["status"] == "error"


def test_discover_devices_returns_mock_devices(client: TestClient) -> None:
    tokens = register(client)
    store = client.post("/api/v1/stores", json=store_payload(), headers=auth_headers(tokens)).json()["data"]
    integration = client.post(
        "/api/v1/esl-integrations",
        json=esl_integration_payload(vendor_id=str(MOCK_VENDOR_ID), store_id=store["id"]),
        headers=auth_headers(tokens),
    ).json()["data"]

    response = client.post(
        f"/api/v1/esl-integrations/{integration['id']}/discover-devices", headers=auth_headers(tokens)
    )

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["success"] is True
    assert len(data["devices"]) == 3
    assert data["devices"][0]["device_identifier"] == "MOCK-001"


def test_import_devices_creates_devices_linked_to_integration(client: TestClient) -> None:
    tokens = register(client)
    store, _ = _setup_store_and_product(client, tokens)
    integration = client.post(
        "/api/v1/esl-integrations",
        json=esl_integration_payload(vendor_id=str(MOCK_VENDOR_ID), store_id=store["id"]),
        headers=auth_headers(tokens),
    ).json()["data"]

    response = client.post(
        f"/api/v1/esl-integrations/{integration['id']}/import-devices",
        json={
            "device_model_id": str(MOCK_MODEL_ID),
            "devices": [
                {"device_identifier": "MOCK-001", "device_name": "Imported Tag 1"},
                {"device_identifier": "MOCK-002", "device_name": "Imported Tag 2"},
            ],
        },
        headers=auth_headers(tokens),
    )

    assert response.status_code == 201, response.text
    created = response.json()["data"]
    assert len(created) == 2
    assert created[0]["device_identifier"] == "MOCK-001"
    assert created[0]["vendor_id"] == str(MOCK_VENDOR_ID)

    device_detail = client.get(f"/api/v1/devices/{created[0]['id']}", headers=auth_headers(tokens)).json()[
        "data"
    ]
    assert device_detail["store_id"] == store["id"]


def test_full_wizard_flow_including_test_price_update(client: TestClient) -> None:
    tokens = register(client)
    store, product = _setup_store_and_product(client, tokens, selling_price="39.9900")
    integration = client.post(
        "/api/v1/esl-integrations",
        json=esl_integration_payload(vendor_id=str(MOCK_VENDOR_ID), store_id=store["id"]),
        headers=auth_headers(tokens),
    ).json()["data"]
    client.post(f"/api/v1/esl-integrations/{integration['id']}/test-connection", headers=auth_headers(tokens))

    imported = client.post(
        f"/api/v1/esl-integrations/{integration['id']}/import-devices",
        json={
            "device_model_id": str(MOCK_MODEL_ID),
            "devices": [{"device_identifier": "MOCK-001", "device_name": "Imported Tag 1"}],
        },
        headers=auth_headers(tokens),
    ).json()["data"]
    device = imported[0]

    client.post(
        "/api/v1/devices/assignments",
        json=device_assignment_payload(
            device_id=device["id"], store_id=store["id"], product_id=product["id"]
        ),
        headers=auth_headers(tokens),
    )

    response = client.post(
        f"/api/v1/esl-integrations/{integration['id']}/test-price-update",
        json={"device_id": device["id"]},
        headers=auth_headers(tokens),
    )

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["success"] is True

    logs = client.get(
        f"/api/v1/devices/{device['id']}/sync-logs", headers=auth_headers(tokens)
    ).json()["data"]
    assert len(logs) >= 1
    assert logs[0]["status"] == "success"


def test_test_price_update_without_assignment_conflicts(client: TestClient) -> None:
    tokens = register(client)
    store, _ = _setup_store_and_product(client, tokens)
    integration = client.post(
        "/api/v1/esl-integrations",
        json=esl_integration_payload(vendor_id=str(MOCK_VENDOR_ID), store_id=store["id"]),
        headers=auth_headers(tokens),
    ).json()["data"]
    imported = client.post(
        f"/api/v1/esl-integrations/{integration['id']}/import-devices",
        json={
            "device_model_id": str(MOCK_MODEL_ID),
            "devices": [{"device_identifier": "MOCK-001", "device_name": "Imported Tag 1"}],
        },
        headers=auth_headers(tokens),
    ).json()["data"]

    response = client.post(
        f"/api/v1/esl-integrations/{integration['id']}/test-price-update",
        json={"device_id": imported[0]["id"]},
        headers=auth_headers(tokens),
    )

    assert response.status_code == 409


def test_update_integration_rotates_credentials(client: TestClient) -> None:
    tokens = register(client)
    store = client.post("/api/v1/stores", json=store_payload(), headers=auth_headers(tokens)).json()["data"]
    integration = client.post(
        "/api/v1/esl-integrations",
        json=esl_integration_payload(vendor_id=str(MOCK_VENDOR_ID), store_id=store["id"]),
        headers=auth_headers(tokens),
    ).json()["data"]

    response = client.put(
        f"/api/v1/esl-integrations/{integration['id']}",
        json={"credentials": {"api_key": "rotated-key"}, "name": "Renamed Integration"},
        headers=auth_headers(tokens),
    )

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["name"] == "Renamed Integration"
    assert "credentials" not in data


def test_integration_not_visible_across_organizations(client: TestClient) -> None:
    tokens_a = register(client, organization_name="Org A", email="a@example.com")
    store_a = client.post(
        "/api/v1/stores", json=store_payload(), headers=auth_headers(tokens_a)
    ).json()["data"]
    integration = client.post(
        "/api/v1/esl-integrations",
        json=esl_integration_payload(vendor_id=str(MOCK_VENDOR_ID), store_id=store_a["id"]),
        headers=auth_headers(tokens_a),
    ).json()["data"]

    tokens_b = register(client, organization_name="Org B", email="b@example.com")
    response = client.get(f"/api/v1/esl-integrations/{integration['id']}", headers=auth_headers(tokens_b))

    assert response.status_code == 404


def test_viewer_cannot_create_integration(client: TestClient, db_session) -> None:
    import uuid as uuid_module

    from tests.helpers import add_user_with_role

    tokens = register(client)
    store = client.post("/api/v1/stores", json=store_payload(), headers=auth_headers(tokens)).json()["data"]
    me = client.get("/api/v1/auth/me", headers=auth_headers(tokens)).json()["data"]
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
        "/api/v1/esl-integrations",
        json=esl_integration_payload(vendor_id=str(MOCK_VENDOR_ID), store_id=store["id"]),
        headers=auth_headers(viewer_tokens),
    )

    assert response.status_code == 403
