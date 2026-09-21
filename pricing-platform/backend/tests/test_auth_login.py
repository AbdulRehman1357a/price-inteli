from fastapi.testclient import TestClient

from tests.helpers import register


def test_login_success_returns_tokens(client: TestClient) -> None:
    register(client, email="ada@acme.com", password="SuperSecret1")

    response = client.post(
        "/api/v1/auth/login", json={"email": "ada@acme.com", "password": "SuperSecret1"}
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["access_token"]
    assert data["refresh_token"]
    assert data["token_type"] == "bearer"


def test_login_wrong_password_returns_401(client: TestClient) -> None:
    register(client, email="ada@acme.com", password="SuperSecret1")

    response = client.post(
        "/api/v1/auth/login", json={"email": "ada@acme.com", "password": "WrongPassword1"}
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_credentials"


def test_login_unknown_email_returns_401(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login", json={"email": "nobody@acme.com", "password": "SuperSecret1"}
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_credentials"
