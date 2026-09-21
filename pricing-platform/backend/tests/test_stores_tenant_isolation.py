from fastapi.testclient import TestClient

from tests.helpers import auth_headers, register, store_payload


def _create_store(client: TestClient, tokens: dict, **overrides) -> dict:
    response = client.post(
        "/api/v1/stores", json=store_payload(**overrides), headers=auth_headers(tokens)
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]


def test_store_list_never_crosses_organizations(client: TestClient) -> None:
    org_a = register(client, organization_name="Org A", email="admin-a@acme.com")
    org_b = register(client, organization_name="Org B", email="admin-b@acme.com")

    store_a = _create_store(client, org_a, store_code="A-STORE")
    store_b = _create_store(client, org_b, store_code="B-STORE")

    list_a = client.get("/api/v1/stores", headers=auth_headers(org_a)).json()["data"]
    list_b = client.get("/api/v1/stores", headers=auth_headers(org_b)).json()["data"]

    assert [s["id"] for s in list_a] == [store_a["id"]]
    assert [s["id"] for s in list_b] == [store_b["id"]]


def test_cannot_get_another_organizations_store(client: TestClient) -> None:
    org_a = register(client, organization_name="Org A", email="admin-a@acme.com")
    org_b = register(client, organization_name="Org B", email="admin-b@acme.com")
    store_b = _create_store(client, org_b, store_code="B-STORE")

    response = client.get(f"/api/v1/stores/{store_b['id']}", headers=auth_headers(org_a))

    # 404, not 403 — existence of another org's store must not leak.
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "store_not_found"


def test_cannot_update_another_organizations_store(client: TestClient) -> None:
    org_a = register(client, organization_name="Org A", email="admin-a@acme.com")
    org_b = register(client, organization_name="Org B", email="admin-b@acme.com")
    store_b = _create_store(client, org_b, store_code="B-STORE")

    response = client.put(
        f"/api/v1/stores/{store_b['id']}", json={"name": "Hijacked"}, headers=auth_headers(org_a)
    )

    assert response.status_code == 404


def test_cannot_delete_another_organizations_store(client: TestClient) -> None:
    org_a = register(client, organization_name="Org A", email="admin-a@acme.com")
    org_b = register(client, organization_name="Org B", email="admin-b@acme.com")
    store_b = _create_store(client, org_b, store_code="B-STORE")

    response = client.delete(f"/api/v1/stores/{store_b['id']}", headers=auth_headers(org_a))

    assert response.status_code == 404

    # And it must still exist, untouched, for its real owner.
    still_there = client.get(f"/api/v1/stores/{store_b['id']}", headers=auth_headers(org_b))
    assert still_there.status_code == 200


def test_client_supplied_organization_id_is_ignored(client: TestClient) -> None:
    org_a = register(client, organization_name="Org A", email="admin-a@acme.com")
    org_b = register(client, organization_name="Org B", email="admin-b@acme.com")
    org_b_id = client.get("/api/v1/auth/me", headers=auth_headers(org_b)).json()["data"]["organization"][
        "id"
    ]

    # A malicious or buggy client tries to plant the store in another org by
    # sending organization_id in the body. The API schema has no such field,
    # so it's silently dropped — the store must land in the caller's own org.
    response = client.post(
        "/api/v1/stores",
        json={**store_payload(), "organization_id": org_b_id},
        headers=auth_headers(org_a),
    )

    assert response.status_code == 201
    created = response.json()["data"]
    assert created["organization_id"] != org_b_id

    me_a = client.get("/api/v1/auth/me", headers=auth_headers(org_a)).json()["data"]
    assert created["organization_id"] == me_a["organization"]["id"]
