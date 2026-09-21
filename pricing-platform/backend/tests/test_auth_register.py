from fastapi.testclient import TestClient

from tests.helpers import auth_headers, register


def test_register_creates_organization_admin_and_first_user(client: TestClient) -> None:
    tokens = register(client)
    assert "access_token" in tokens
    assert "refresh_token" in tokens

    me = client.get("/api/v1/auth/me", headers=auth_headers(tokens))
    assert me.status_code == 200
    data = me.json()["data"]
    assert data["organization"]["name"] == "Acme Retail"
    assert data["user"]["email"] == "ada@acme.com"
    assert data["roles"] == ["Organization Admin"]
    assert "users.create" in data["permissions"]
    assert "password" not in data["user"]
    assert "password_hash" not in data["user"]


def test_register_duplicate_email_is_rejected(client: TestClient) -> None:
    register(client, email="dup@acme.com")

    response = client.post(
        "/api/v1/auth/register",
        json={
            "organization_name": "Second Org",
            "first_name": "Bea",
            "last_name": "Smith",
            "email": "dup@acme.com",
            "password": "AnotherSecret1",
            "confirm_password": "AnotherSecret1",
        },
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "email_taken"


def test_register_password_mismatch_returns_422(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "organization_name": "Acme Retail",
            "first_name": "Ada",
            "last_name": "Lovelace",
            "email": "ada@acme.com",
            "password": "SuperSecret1",
            "confirm_password": "Different1",
        },
    )
    assert response.status_code == 422


def test_register_short_password_returns_422(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "organization_name": "Acme Retail",
            "first_name": "Ada",
            "last_name": "Lovelace",
            "email": "ada@acme.com",
            "password": "short1",
            "confirm_password": "short1",
        },
    )
    assert response.status_code == 422


def test_register_invalid_email_returns_422(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "organization_name": "Acme Retail",
            "first_name": "Ada",
            "last_name": "Lovelace",
            "email": "not-an-email",
            "password": "SuperSecret1",
            "confirm_password": "SuperSecret1",
        },
    )
    assert response.status_code == 422
