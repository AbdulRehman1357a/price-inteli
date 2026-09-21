import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.helpers import add_user_with_role, auth_headers, register


def _role_id(client: TestClient, tokens: dict, name: str) -> str:
    response = client.get("/api/v1/roles", headers=auth_headers(tokens))
    assert response.status_code == 200, response.text
    role = next(r for r in response.json()["data"] if r["name"] == name)
    return role["id"]


def test_list_roles_includes_seeded_system_roles_with_permissions(client: TestClient) -> None:
    tokens = register(client)
    response = client.get("/api/v1/roles", headers=auth_headers(tokens))
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    names = {r["name"] for r in data}
    assert {"Super Admin", "Organization Admin", "Store Manager", "Viewer"} <= names
    admin_role = next(r for r in data if r["name"] == "Organization Admin")
    assert any(p["code"] == "users.create" for p in admin_role["permissions"])


def test_list_permissions_returns_seeded_catalog(client: TestClient) -> None:
    tokens = register(client)
    response = client.get("/api/v1/permissions", headers=auth_headers(tokens))
    assert response.status_code == 200, response.text
    codes = {p["code"] for p in response.json()["data"]}
    assert "users.create" in codes
    assert "stores.read" in codes


def test_create_user_assigns_role_and_is_immediately_loginable(client: TestClient) -> None:
    tokens = register(client)
    role_id = _role_id(client, tokens, "Store Manager")

    response = client.post(
        "/api/v1/users",
        json={
            "first_name": "Nia",
            "last_name": "Store",
            "email": "nia.store@acme.com",
            "password": "SuperSecret1",
            "role_ids": [role_id],
        },
        headers=auth_headers(tokens),
    )

    assert response.status_code == 201, response.text
    data = response.json()["data"]
    assert data["email"] == "nia.store@acme.com"
    assert [r["name"] for r in data["roles"]] == ["Store Manager"]

    login = client.post(
        "/api/v1/auth/login", json={"email": "nia.store@acme.com", "password": "SuperSecret1"}
    )
    assert login.status_code == 200, login.text


def test_create_user_rejects_duplicate_email(client: TestClient) -> None:
    tokens = register(client, email="dup@acme.com")
    role_id = _role_id(client, tokens, "Viewer")

    response = client.post(
        "/api/v1/users",
        json={
            "first_name": "Dup",
            "last_name": "User",
            "email": "dup@acme.com",
            "password": "SuperSecret1",
            "role_ids": [role_id],
        },
        headers=auth_headers(tokens),
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "email_taken"


def test_create_user_rejects_unknown_role_id(client: TestClient) -> None:
    tokens = register(client)

    response = client.post(
        "/api/v1/users",
        json={
            "first_name": "Bad",
            "last_name": "Role",
            "email": "badrole@acme.com",
            "password": "SuperSecret1",
            "role_ids": [str(uuid.uuid4())],
        },
        headers=auth_headers(tokens),
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "role_not_found"


def test_list_users_includes_roles_and_supports_search(client: TestClient) -> None:
    tokens = register(client, email="owner@acme.com")
    role_id = _role_id(client, tokens, "Viewer")
    client.post(
        "/api/v1/users",
        json={
            "first_name": "Searchable",
            "last_name": "Person",
            "email": "searchable@acme.com",
            "password": "SuperSecret1",
            "role_ids": [role_id],
        },
        headers=auth_headers(tokens),
    )

    response = client.get("/api/v1/users?search=Searchable", headers=auth_headers(tokens))
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["email"] == "searchable@acme.com"
    assert data[0]["roles"][0]["name"] == "Viewer"


def test_update_user_changes_fields_status_and_roles(client: TestClient) -> None:
    tokens = register(client)
    viewer_role_id = _role_id(client, tokens, "Viewer")
    pricing_role_id = _role_id(client, tokens, "Pricing Manager")

    created = client.post(
        "/api/v1/users",
        json={
            "first_name": "Before",
            "last_name": "Edit",
            "email": "beforeedit@acme.com",
            "password": "SuperSecret1",
            "role_ids": [viewer_role_id],
        },
        headers=auth_headers(tokens),
    ).json()["data"]

    response = client.put(
        f"/api/v1/users/{created['id']}",
        json={"first_name": "After", "status": "inactive", "role_ids": [pricing_role_id]},
        headers=auth_headers(tokens),
    )

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["first_name"] == "After"
    assert data["status"] == "inactive"
    assert [r["name"] for r in data["roles"]] == ["Pricing Manager"]


def test_delete_user_soft_deletes(client: TestClient) -> None:
    tokens = register(client)
    role_id = _role_id(client, tokens, "Viewer")
    created = client.post(
        "/api/v1/users",
        json={
            "first_name": "To",
            "last_name": "Delete",
            "email": "todelete@acme.com",
            "password": "SuperSecret1",
            "role_ids": [role_id],
        },
        headers=auth_headers(tokens),
    ).json()["data"]

    response = client.delete(f"/api/v1/users/{created['id']}", headers=auth_headers(tokens))
    assert response.status_code == 200, response.text

    follow_up = client.get(f"/api/v1/users/{created['id']}", headers=auth_headers(tokens))
    assert follow_up.status_code == 404


def test_admin_cannot_update_own_account_via_admin_endpoint(client: TestClient) -> None:
    tokens = register(client)
    me = client.get("/api/v1/auth/me", headers=auth_headers(tokens)).json()["data"]

    response = client.put(
        f"/api/v1/users/{me['user']['id']}",
        json={"first_name": "Self"},
        headers=auth_headers(tokens),
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "cannot_self_administer"


def test_admin_cannot_delete_own_account(client: TestClient) -> None:
    tokens = register(client)
    me = client.get("/api/v1/auth/me", headers=auth_headers(tokens)).json()["data"]

    response = client.delete(f"/api/v1/users/{me['user']['id']}", headers=auth_headers(tokens))

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "cannot_self_administer"


def test_users_from_another_organization_are_not_visible(client: TestClient) -> None:
    tokens_a = register(client, organization_name="Org A", email="admina@a.com")
    role_id = _role_id(client, tokens_a, "Viewer")
    created_in_a = client.post(
        "/api/v1/users",
        json={
            "first_name": "Isolated",
            "last_name": "User",
            "email": "isolated@a.com",
            "password": "SuperSecret1",
            "role_ids": [role_id],
        },
        headers=auth_headers(tokens_a),
    ).json()["data"]

    tokens_b = register(client, organization_name="Org B", email="adminb@b.com")

    response = client.get(f"/api/v1/users/{created_in_a['id']}", headers=auth_headers(tokens_b))
    assert response.status_code == 404


def test_user_management_requires_permission(client: TestClient, db_session: Session) -> None:
    tokens = register(client)
    me = client.get("/api/v1/auth/me", headers=auth_headers(tokens)).json()["data"]
    organization_id = uuid.UUID(me["organization"]["id"])
    role_id = _role_id(client, tokens, "Viewer")

    add_user_with_role(
        db_session, organization_id=organization_id, email="viewer3@acme.com", role_name="Viewer"
    )
    viewer_tokens = client.post(
        "/api/v1/auth/login", json={"email": "viewer3@acme.com", "password": "SuperSecret1"}
    ).json()["data"]

    response = client.post(
        "/api/v1/users",
        json={
            "first_name": "Nope",
            "last_name": "User",
            "email": "nope@acme.com",
            "password": "SuperSecret1",
            "role_ids": [role_id],
        },
        headers=auth_headers(viewer_tokens),
    )

    assert response.status_code == 403
