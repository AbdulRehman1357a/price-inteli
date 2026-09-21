import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.helpers import add_user_with_role, auth_headers, register


def test_organization_admin_can_list_users(client: TestClient) -> None:
    tokens = register(client)
    response = client.get("/api/v1/users", headers=auth_headers(tokens))
    assert response.status_code == 200


def test_role_without_users_read_permission_is_denied(client: TestClient, db_session: Session) -> None:
    admin_tokens = register(client)
    me = client.get("/api/v1/auth/me", headers=auth_headers(admin_tokens)).json()["data"]
    organization_id = uuid.UUID(me["user"]["organization_id"])

    # Store Manager is a seeded role with no users.* permissions at all.
    add_user_with_role(
        db_session,
        organization_id=organization_id,
        email="storemgr@acme.com",
        role_name="Store Manager",
    )
    login = client.post(
        "/api/v1/auth/login", json={"email": "storemgr@acme.com", "password": "SuperSecret1"}
    )
    assert login.status_code == 200
    store_manager_tokens = login.json()["data"]

    response = client.get("/api/v1/users", headers=auth_headers(store_manager_tokens))

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "permission_denied"
