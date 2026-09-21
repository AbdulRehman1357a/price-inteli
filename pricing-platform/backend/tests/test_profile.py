from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.helpers import add_user_with_role, auth_headers, register


def test_update_me_updates_editable_fields(client: TestClient) -> None:
    tokens = register(client)

    response = client.put(
        "/api/v1/auth/me",
        json={"first_name": "Grace", "last_name": "Hopper", "phone": "+1-555-0100"},
        headers=auth_headers(tokens),
    )

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["first_name"] == "Grace"
    assert data["last_name"] == "Hopper"
    assert data["phone"] == "+1-555-0100"


def test_update_me_partial_update_leaves_other_fields_untouched(client: TestClient) -> None:
    tokens = register(client, first_name="Ada", last_name="Lovelace")

    response = client.put("/api/v1/auth/me", json={"phone": "+1-555-0199"}, headers=auth_headers(tokens))

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["first_name"] == "Ada"
    assert data["last_name"] == "Lovelace"
    assert data["phone"] == "+1-555-0199"


def test_update_me_rejects_unauthenticated(client: TestClient) -> None:
    response = client.put("/api/v1/auth/me", json={"first_name": "Nope"})
    assert response.status_code == 401


def test_update_me_does_not_accept_email_change(client: TestClient) -> None:
    tokens = register(client, email="original@acme.com")

    response = client.put(
        "/api/v1/auth/me", json={"email": "changed@acme.com"}, headers=auth_headers(tokens)
    )

    assert response.status_code == 200, response.text
    me = client.get("/api/v1/auth/me", headers=auth_headers(tokens))
    assert me.json()["data"]["user"]["email"] == "original@acme.com"


def test_update_organization_updates_company_details(client: TestClient) -> None:
    tokens = register(client)

    response = client.put(
        "/api/v1/organizations/me",
        json={"legal_name": "Acme Retail Holdings LLC", "website": "https://acme.example.com"},
        headers=auth_headers(tokens),
    )

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["legal_name"] == "Acme Retail Holdings LLC"
    assert data["website"] == "https://acme.example.com"


def test_update_organization_requires_permission(client: TestClient, db_session: Session) -> None:
    tokens = register(client)

    # Fetch the current org id via /auth/me, then create a Viewer in the same org.
    me = client.get("/api/v1/auth/me", headers=auth_headers(tokens)).json()["data"]
    org_id = me["organization"]["id"]

    from uuid import UUID

    add_user_with_role(db_session, organization_id=UUID(org_id), email="viewer2@acme.com", role_name="Viewer")
    viewer_tokens = client.post(
        "/api/v1/auth/login", json={"email": "viewer2@acme.com", "password": "SuperSecret1"}
    ).json()["data"]

    response = client.put(
        "/api/v1/organizations/me", json={"legal_name": "Should Fail"}, headers=auth_headers(viewer_tokens)
    )

    assert response.status_code == 403


def test_update_organization_rejects_unauthenticated(client: TestClient) -> None:
    response = client.put("/api/v1/organizations/me", json={"legal_name": "Nope"})
    assert response.status_code == 401
