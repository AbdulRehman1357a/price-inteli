import uuid

from fastapi.testclient import TestClient

from tests.helpers import auth_headers, register


def _role(client: TestClient, tokens: dict, name: str) -> dict:
    response = client.get("/api/v1/roles", headers=auth_headers(tokens))
    assert response.status_code == 200, response.text
    return next(r for r in response.json()["data"] if r["name"] == name)


def _all_permission_ids(client: TestClient, tokens: dict) -> list[str]:
    response = client.get("/api/v1/permissions", headers=auth_headers(tokens))
    assert response.status_code == 200, response.text
    return [p["id"] for p in response.json()["data"]]


def _permission_ids_by_code(client: TestClient, tokens: dict, codes: list[str]) -> list[str]:
    response = client.get("/api/v1/permissions", headers=auth_headers(tokens))
    assert response.status_code == 200, response.text
    by_code = {p["code"]: p["id"] for p in response.json()["data"]}
    return [by_code[c] for c in codes]


def test_editing_a_system_role_forks_it_into_an_org_scoped_copy(client: TestClient) -> None:
    tokens = register(client)
    store_manager = _role(client, tokens, "Store Manager")
    assert store_manager["is_system_role"] is True

    new_permission_ids = _permission_ids_by_code(client, tokens, ["stores.read", "products.read"])
    response = client.put(
        f"/api/v1/roles/{store_manager['id']}/permissions",
        json={"permission_ids": new_permission_ids},
        headers=auth_headers(tokens),
    )

    assert response.status_code == 200, response.text
    forked = response.json()["data"]
    assert forked["id"] != store_manager["id"]
    assert forked["name"] == "Store Manager"
    assert forked["is_system_role"] is False
    assert {p["code"] for p in forked["permissions"]} == {"stores.read", "products.read"}


def test_forked_role_replaces_the_original_in_the_org_role_list(client: TestClient) -> None:
    tokens = register(client)
    store_manager = _role(client, tokens, "Store Manager")
    new_ids = _permission_ids_by_code(client, tokens, ["stores.read"])
    client.put(
        f"/api/v1/roles/{store_manager['id']}/permissions",
        json={"permission_ids": new_ids},
        headers=auth_headers(tokens),
    )

    response = client.get("/api/v1/roles", headers=auth_headers(tokens))
    store_manager_entries = [r for r in response.json()["data"] if r["name"] == "Store Manager"]
    assert len(store_manager_entries) == 1
    assert store_manager_entries[0]["id"] != store_manager["id"]
    assert store_manager_entries[0]["is_system_role"] is False


def test_editing_an_already_forked_role_updates_it_in_place(client: TestClient) -> None:
    tokens = register(client)
    store_manager = _role(client, tokens, "Store Manager")
    first_ids = _permission_ids_by_code(client, tokens, ["stores.read"])
    first_response = client.put(
        f"/api/v1/roles/{store_manager['id']}/permissions",
        json={"permission_ids": first_ids},
        headers=auth_headers(tokens),
    ).json()["data"]

    second_ids = _permission_ids_by_code(client, tokens, ["stores.read", "products.read"])
    second_response = client.put(
        f"/api/v1/roles/{first_response['id']}/permissions",
        json={"permission_ids": second_ids},
        headers=auth_headers(tokens),
    )

    assert second_response.status_code == 200, second_response.text
    data = second_response.json()["data"]
    assert data["id"] == first_response["id"]
    assert {p["code"] for p in data["permissions"]} == {"stores.read", "products.read"}


def test_forking_reassigns_existing_org_users_to_the_fork(client: TestClient) -> None:
    tokens = register(client)
    store_manager = _role(client, tokens, "Store Manager")

    created = client.post(
        "/api/v1/users",
        json={
            "first_name": "Store",
            "last_name": "Mgr",
            "email": "storemgr2@acme.com",
            "password": "SuperSecret1",
            "role_ids": [store_manager["id"]],
        },
        headers=auth_headers(tokens),
    ).json()["data"]
    assert created["roles"][0]["id"] == store_manager["id"]

    new_ids = _permission_ids_by_code(client, tokens, ["stores.read"])
    forked = client.put(
        f"/api/v1/roles/{store_manager['id']}/permissions",
        json={"permission_ids": new_ids},
        headers=auth_headers(tokens),
    ).json()["data"]

    refreshed = client.get(f"/api/v1/users/{created['id']}", headers=auth_headers(tokens)).json()["data"]
    assert refreshed["roles"][0]["id"] == forked["id"]


def test_update_role_permissions_rejects_unknown_permission_id(client: TestClient) -> None:
    tokens = register(client)
    store_manager = _role(client, tokens, "Store Manager")

    response = client.put(
        f"/api/v1/roles/{store_manager['id']}/permissions",
        json={"permission_ids": [str(uuid.uuid4())]},
        headers=auth_headers(tokens),
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "permission_not_found"


def test_cannot_strip_own_users_update_permission(client: TestClient) -> None:
    tokens = register(client)
    admin_role = _role(client, tokens, "Organization Admin")
    ids_without_users_update = [
        p["id"] for p in admin_role["permissions"] if p["code"] != "users.update"
    ]

    response = client.put(
        f"/api/v1/roles/{admin_role['id']}/permissions",
        json={"permission_ids": ids_without_users_update},
        headers=auth_headers(tokens),
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "cannot_remove_own_role_management"


def test_another_organization_cannot_edit_a_forked_role(client: TestClient) -> None:
    tokens_a = register(client, organization_name="Org A", email="admina2@a.com")
    store_manager = _role(client, tokens_a, "Store Manager")
    ids = _permission_ids_by_code(client, tokens_a, ["stores.read"])
    forked = client.put(
        f"/api/v1/roles/{store_manager['id']}/permissions",
        json={"permission_ids": ids},
        headers=auth_headers(tokens_a),
    ).json()["data"]

    tokens_b = register(client, organization_name="Org B", email="adminb2@b.com")
    response = client.put(
        f"/api/v1/roles/{forked['id']}/permissions",
        json={"permission_ids": ids},
        headers=auth_headers(tokens_b),
    )

    assert response.status_code == 404


def test_role_permission_edit_requires_permission(client: TestClient) -> None:
    tokens = register(client)
    viewer = _role(client, tokens, "Viewer")

    client.post(
        "/api/v1/users",
        json={
            "first_name": "Just",
            "last_name": "Viewer",
            "email": "justviewer2@acme.com",
            "password": "SuperSecret1",
            "role_ids": [viewer["id"]],
        },
        headers=auth_headers(tokens),
    )
    login = client.post(
        "/api/v1/auth/login", json={"email": "justviewer2@acme.com", "password": "SuperSecret1"}
    ).json()["data"]

    ids = _permission_ids_by_code(client, tokens, ["stores.read"])
    response = client.put(
        f"/api/v1/roles/{viewer['id']}/permissions",
        json={"permission_ids": ids},
        headers=auth_headers(login),
    )

    assert response.status_code == 403
