import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.helpers import add_user_with_role, auth_headers, category_payload, product_payload, register


def _create_category(client: TestClient, tokens: dict, **overrides) -> dict:
    response = client.post(
        "/api/v1/categories", json=category_payload(**overrides), headers=auth_headers(tokens)
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]


def _create_product(client: TestClient, tokens: dict, category_id: str, **overrides) -> dict:
    response = client.post(
        "/api/v1/products",
        json=product_payload(category_id=category_id, **overrides),
        headers=auth_headers(tokens),
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]


def test_create_product_success(client: TestClient) -> None:
    tokens = register(client)
    category = _create_category(client, tokens)

    product = _create_product(client, tokens, category["id"])

    assert product["sku"] == "SKU-001"
    assert product["status"] == "active"
    assert product["category_id"] == category["id"]
    assert product["selling_price"] == "19.9900"


def test_create_product_unknown_category_returns_404(client: TestClient) -> None:
    tokens = register(client)

    response = client.post(
        "/api/v1/products",
        json=product_payload(category_id="00000000-0000-0000-0000-000000000000"),
        headers=auth_headers(tokens),
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "category_not_found"


def test_create_product_duplicate_sku_in_same_org_conflicts(client: TestClient) -> None:
    tokens = register(client)
    category = _create_category(client, tokens)
    _create_product(client, tokens, category["id"])

    response = client.post(
        "/api/v1/products",
        json=product_payload(category_id=category["id"]),
        headers=auth_headers(tokens),
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "sku_taken"


def test_get_product_by_id(client: TestClient) -> None:
    tokens = register(client)
    category = _create_category(client, tokens)
    created = _create_product(client, tokens, category["id"])

    response = client.get(f"/api/v1/products/{created['id']}", headers=auth_headers(tokens))

    assert response.status_code == 200
    assert response.json()["data"]["sku"] == "SKU-001"


def test_get_unknown_product_returns_404(client: TestClient) -> None:
    tokens = register(client)

    response = client.get(
        "/api/v1/products/00000000-0000-0000-0000-000000000000", headers=auth_headers(tokens)
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "product_not_found"


def test_update_product_partial(client: TestClient) -> None:
    tokens = register(client)
    category = _create_category(client, tokens)
    created = _create_product(client, tokens, category["id"])

    response = client.put(
        f"/api/v1/products/{created['id']}",
        json={"product_name": "Ergonomic Mouse", "status": "discontinued"},
        headers=auth_headers(tokens),
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["product_name"] == "Ergonomic Mouse"
    assert data["status"] == "discontinued"
    assert data["sku"] == "SKU-001"


def test_update_product_to_duplicate_sku_conflicts(client: TestClient) -> None:
    tokens = register(client)
    category = _create_category(client, tokens)
    _create_product(client, tokens, category["id"], sku="A")
    second = _create_product(client, tokens, category["id"], sku="B")

    response = client.put(
        f"/api/v1/products/{second['id']}", json={"sku": "A"}, headers=auth_headers(tokens)
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "sku_taken"


def test_update_product_to_unknown_category_returns_404(client: TestClient) -> None:
    tokens = register(client)
    category = _create_category(client, tokens)
    created = _create_product(client, tokens, category["id"])

    response = client.put(
        f"/api/v1/products/{created['id']}",
        json={"category_id": "00000000-0000-0000-0000-000000000000"},
        headers=auth_headers(tokens),
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "category_not_found"


def test_delete_product_soft_deletes(client: TestClient) -> None:
    tokens = register(client)
    category = _create_category(client, tokens)
    created = _create_product(client, tokens, category["id"])

    delete_response = client.delete(f"/api/v1/products/{created['id']}", headers=auth_headers(tokens))
    assert delete_response.status_code == 200

    get_response = client.get(f"/api/v1/products/{created['id']}", headers=auth_headers(tokens))
    assert get_response.status_code == 404

    list_response = client.get("/api/v1/products", headers=auth_headers(tokens))
    assert created["id"] not in [p["id"] for p in list_response.json()["data"]]


def test_list_products_pagination(client: TestClient) -> None:
    tokens = register(client)
    category = _create_category(client, tokens)
    for i in range(5):
        _create_product(client, tokens, category["id"], sku=f"SKU-{i}")

    response = client.get("/api/v1/products?page=1&page_size=2", headers=auth_headers(tokens))

    body = response.json()
    assert len(body["data"]) == 2
    assert body["meta"]["total"] == 5
    assert body["meta"]["total_pages"] == 3


def test_list_products_search_matches_sku_barcode_or_name(client: TestClient) -> None:
    tokens = register(client)
    category = _create_category(client, tokens)
    _create_product(client, tokens, category["id"], sku="A-1", product_name="Blue Widget")
    _create_product(client, tokens, category["id"], sku="B-1", product_name="Red Gadget")

    response = client.get("/api/v1/products?search=widget", headers=auth_headers(tokens))

    assert [p["sku"] for p in response.json()["data"]] == ["A-1"]


def test_list_products_category_filter(client: TestClient) -> None:
    tokens = register(client)
    electronics = _create_category(client, tokens, name="Electronics")
    apparel = _create_category(client, tokens, name="Apparel")
    _create_product(client, tokens, electronics["id"], sku="E-1")
    _create_product(client, tokens, apparel["id"], sku="A-1")

    response = client.get(f"/api/v1/products?category_id={electronics['id']}", headers=auth_headers(tokens))

    assert [p["sku"] for p in response.json()["data"]] == ["E-1"]


def test_list_products_status_filter(client: TestClient) -> None:
    tokens = register(client)
    category = _create_category(client, tokens)
    _create_product(client, tokens, category["id"], sku="A", status="active")
    _create_product(client, tokens, category["id"], sku="B", status="discontinued")

    response = client.get("/api/v1/products?status=discontinued", headers=auth_headers(tokens))

    assert [p["sku"] for p in response.json()["data"]] == ["B"]


def test_list_products_sort_by_selling_price(client: TestClient) -> None:
    tokens = register(client)
    category = _create_category(client, tokens)
    _create_product(client, tokens, category["id"], sku="EXPENSIVE", selling_price="99.99")
    _create_product(client, tokens, category["id"], sku="CHEAP", selling_price="1.99")

    response = client.get("/api/v1/products?sort=selling_price", headers=auth_headers(tokens))

    assert [p["sku"] for p in response.json()["data"]] == ["CHEAP", "EXPENSIVE"]


def test_role_without_products_create_permission_is_denied(
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
    category = _create_category(client, admin_tokens)

    response = client.post(
        "/api/v1/products",
        json=product_payload(category_id=category["id"]),
        headers=auth_headers(viewer_tokens),
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "permission_denied"
