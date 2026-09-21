import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.helpers import add_user_with_role, auth_headers, category_payload, register


def _create(client: TestClient, tokens: dict, **overrides) -> dict:
    response = client.post(
        "/api/v1/categories", json=category_payload(**overrides), headers=auth_headers(tokens)
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]


def test_create_category_success(client: TestClient) -> None:
    tokens = register(client)

    response = client.post(
        "/api/v1/categories", json=category_payload(), headers=auth_headers(tokens)
    )

    assert response.status_code == 201, response.text
    data = response.json()["data"]
    assert data["name"] == "Electronics"
    assert data["parent_id"] is None
    assert data["status"] == "active"


def test_create_category_with_parent(client: TestClient) -> None:
    tokens = register(client)
    parent = _create(client, tokens, name="Electronics")

    child = _create(client, tokens, name="Laptops", parent_id=parent["id"])

    assert child["parent_id"] == parent["id"]


def test_create_category_with_unknown_parent_returns_404(client: TestClient) -> None:
    tokens = register(client)

    response = client.post(
        "/api/v1/categories",
        json=category_payload(parent_id="00000000-0000-0000-0000-000000000000"),
        headers=auth_headers(tokens),
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "parent_category_not_found"


def test_get_category_by_id(client: TestClient) -> None:
    tokens = register(client)
    created = _create(client, tokens)

    response = client.get(f"/api/v1/categories/{created['id']}", headers=auth_headers(tokens))

    assert response.status_code == 200
    assert response.json()["data"]["name"] == "Electronics"


def test_get_unknown_category_returns_404(client: TestClient) -> None:
    tokens = register(client)

    response = client.get(
        "/api/v1/categories/00000000-0000-0000-0000-000000000000", headers=auth_headers(tokens)
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "category_not_found"


def test_update_category_partial(client: TestClient) -> None:
    tokens = register(client)
    created = _create(client, tokens)

    response = client.put(
        f"/api/v1/categories/{created['id']}",
        json={"name": "Consumer Electronics", "status": "inactive"},
        headers=auth_headers(tokens),
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["name"] == "Consumer Electronics"
    assert data["status"] == "inactive"


def test_cannot_move_category_under_itself(client: TestClient) -> None:
    tokens = register(client)
    created = _create(client, tokens)

    response = client.put(
        f"/api/v1/categories/{created['id']}",
        json={"parent_id": created["id"]},
        headers=auth_headers(tokens),
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "category_cycle"


def test_cannot_move_category_under_its_own_child(client: TestClient) -> None:
    tokens = register(client)
    parent = _create(client, tokens, name="Electronics")
    child = _create(client, tokens, name="Laptops", parent_id=parent["id"])

    response = client.put(
        f"/api/v1/categories/{parent['id']}",
        json={"parent_id": child["id"]},
        headers=auth_headers(tokens),
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "category_cycle"


def test_delete_category_with_children_conflicts(client: TestClient) -> None:
    tokens = register(client)
    parent = _create(client, tokens, name="Electronics")
    _create(client, tokens, name="Laptops", parent_id=parent["id"])

    response = client.delete(f"/api/v1/categories/{parent['id']}", headers=auth_headers(tokens))

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "category_has_children"


def test_delete_category_with_products_conflicts(client: TestClient) -> None:
    tokens = register(client)
    category = _create(client, tokens)
    client.post(
        "/api/v1/products",
        json={
            "category_id": category["id"],
            "sku": "SKU-1",
            "product_name": "Mouse",
            "selling_price": "9.99",
        },
        headers=auth_headers(tokens),
    )

    response = client.delete(f"/api/v1/categories/{category['id']}", headers=auth_headers(tokens))

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "category_has_products"


def test_delete_empty_category_succeeds(client: TestClient) -> None:
    tokens = register(client)
    created = _create(client, tokens)

    response = client.delete(f"/api/v1/categories/{created['id']}", headers=auth_headers(tokens))
    assert response.status_code == 200

    get_response = client.get(f"/api/v1/categories/{created['id']}", headers=auth_headers(tokens))
    assert get_response.status_code == 404


def test_list_categories_search_and_status_filter(client: TestClient) -> None:
    tokens = register(client)
    _create(client, tokens, name="Electronics", status="active")
    _create(client, tokens, name="Discontinued Line", status="inactive")

    search = client.get("/api/v1/categories?search=electronics", headers=auth_headers(tokens)).json()[
        "data"
    ]
    assert [c["name"] for c in search] == ["Electronics"]

    inactive = client.get("/api/v1/categories?status=inactive", headers=auth_headers(tokens)).json()[
        "data"
    ]
    assert [c["name"] for c in inactive] == ["Discontinued Line"]


def test_list_categories_sort_by_name(client: TestClient) -> None:
    tokens = register(client)
    _create(client, tokens, name="Zebra")
    _create(client, tokens, name="Apple")

    response = client.get("/api/v1/categories?sort=name", headers=auth_headers(tokens))

    assert [c["name"] for c in response.json()["data"]] == ["Apple", "Zebra"]


def test_role_without_categories_create_permission_is_denied(
    client: TestClient, db_session: Session
) -> None:
    admin_tokens = register(client)
    organization_id = client.get("/api/v1/auth/me", headers=auth_headers(admin_tokens)).json()["data"][
        "user"
    ]["organization_id"]

    add_user_with_role(
        db_session,
        organization_id=uuid.UUID(organization_id),
        email="viewer@acme.com",
        role_name="Viewer",
    )
    login = client.post("/api/v1/auth/login", json={"email": "viewer@acme.com", "password": "SuperSecret1"})
    viewer_tokens = login.json()["data"]

    response = client.post(
        "/api/v1/categories", json=category_payload(), headers=auth_headers(viewer_tokens)
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "permission_denied"
