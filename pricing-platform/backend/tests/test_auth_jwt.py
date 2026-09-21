from fastapi.testclient import TestClient

from tests.helpers import auth_headers, register


def test_me_without_token_returns_401(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "not_authenticated"


def test_me_with_garbage_token_returns_401(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_access_token"


def test_me_with_valid_token_returns_200(client: TestClient) -> None:
    tokens = register(client)
    response = client.get("/api/v1/auth/me", headers=auth_headers(tokens))
    assert response.status_code == 200


def test_refresh_issues_new_access_token(client: TestClient) -> None:
    tokens = register(client)

    response = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})

    assert response.status_code == 200
    new_access_token = response.json()["data"]["access_token"]
    assert new_access_token
    # The new access token itself must work against a protected endpoint.
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {new_access_token}"})
    assert me.status_code == 200


def test_refresh_rejects_an_access_token(client: TestClient) -> None:
    tokens = register(client)

    response = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["access_token"]})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_refresh_token"


def test_access_token_rejected_on_refresh_type_but_me_rejects_refresh_token(client: TestClient) -> None:
    tokens = register(client)
    # A refresh token must not work as an access token on a protected route.
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['refresh_token']}"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_access_token"
