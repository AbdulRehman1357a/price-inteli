from fastapi.testclient import TestClient

from tests.helpers import auth_headers, category_payload, product_payload, register


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


def _two_orgs(client: TestClient) -> tuple[dict, dict]:
    org_a = register(client, organization_name="Org A", email="admin-a@acme.com")
    org_b = register(client, organization_name="Org B", email="admin-b@acme.com")
    return org_a, org_b


def test_category_list_never_crosses_organizations(client: TestClient) -> None:
    org_a, org_b = _two_orgs(client)
    cat_a = _create_category(client, org_a, name="Org A Category")
    cat_b = _create_category(client, org_b, name="Org B Category")

    list_a = client.get("/api/v1/categories", headers=auth_headers(org_a)).json()["data"]
    list_b = client.get("/api/v1/categories", headers=auth_headers(org_b)).json()["data"]

    assert [c["id"] for c in list_a] == [cat_a["id"]]
    assert [c["id"] for c in list_b] == [cat_b["id"]]


def test_cannot_get_another_organizations_category(client: TestClient) -> None:
    org_a, org_b = _two_orgs(client)
    cat_b = _create_category(client, org_b)

    response = client.get(f"/api/v1/categories/{cat_b['id']}", headers=auth_headers(org_a))

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "category_not_found"


def test_cannot_update_or_delete_another_organizations_category(client: TestClient) -> None:
    org_a, org_b = _two_orgs(client)
    cat_b = _create_category(client, org_b)

    update_response = client.put(
        f"/api/v1/categories/{cat_b['id']}", json={"name": "Hijacked"}, headers=auth_headers(org_a)
    )
    delete_response = client.delete(f"/api/v1/categories/{cat_b['id']}", headers=auth_headers(org_a))

    assert update_response.status_code == 404
    assert delete_response.status_code == 404


def test_client_supplied_organization_id_is_ignored_for_category(client: TestClient) -> None:
    org_a, org_b = _two_orgs(client)
    org_b_id = client.get("/api/v1/auth/me", headers=auth_headers(org_b)).json()["data"]["organization"][
        "id"
    ]

    response = client.post(
        "/api/v1/categories",
        json={**category_payload(), "organization_id": org_b_id},
        headers=auth_headers(org_a),
    )

    assert response.status_code == 201
    me_a = client.get("/api/v1/auth/me", headers=auth_headers(org_a)).json()["data"]
    assert response.json()["data"]["organization_id"] == me_a["organization"]["id"]
    assert response.json()["data"]["organization_id"] != org_b_id


def test_product_list_never_crosses_organizations(client: TestClient) -> None:
    org_a, org_b = _two_orgs(client)
    cat_a = _create_category(client, org_a)
    cat_b = _create_category(client, org_b)
    product_a = _create_product(client, org_a, cat_a["id"])
    product_b = _create_product(client, org_b, cat_b["id"])

    list_a = client.get("/api/v1/products", headers=auth_headers(org_a)).json()["data"]
    list_b = client.get("/api/v1/products", headers=auth_headers(org_b)).json()["data"]

    assert [p["id"] for p in list_a] == [product_a["id"]]
    assert [p["id"] for p in list_b] == [product_b["id"]]


def test_cannot_get_update_or_delete_another_organizations_product(client: TestClient) -> None:
    org_a, org_b = _two_orgs(client)
    cat_b = _create_category(client, org_b)
    product_b = _create_product(client, org_b, cat_b["id"])

    get_response = client.get(f"/api/v1/products/{product_b['id']}", headers=auth_headers(org_a))
    update_response = client.put(
        f"/api/v1/products/{product_b['id']}", json={"product_name": "Hijacked"}, headers=auth_headers(org_a)
    )
    delete_response = client.delete(f"/api/v1/products/{product_b['id']}", headers=auth_headers(org_a))

    assert get_response.status_code == 404
    assert update_response.status_code == 404
    assert delete_response.status_code == 404


def test_cannot_assign_product_to_another_organizations_category(client: TestClient) -> None:
    org_a, org_b = _two_orgs(client)
    cat_b = _create_category(client, org_b)

    response = client.post(
        "/api/v1/products",
        json=product_payload(category_id=cat_b["id"]),
        headers=auth_headers(org_a),
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "category_not_found"


def test_client_supplied_organization_id_is_ignored_for_product(client: TestClient) -> None:
    org_a, org_b = _two_orgs(client)
    cat_a = _create_category(client, org_a)
    org_b_id = client.get("/api/v1/auth/me", headers=auth_headers(org_b)).json()["data"]["organization"][
        "id"
    ]

    response = client.post(
        "/api/v1/products",
        json={**product_payload(category_id=cat_a["id"]), "organization_id": org_b_id},
        headers=auth_headers(org_a),
    )

    assert response.status_code == 201
    me_a = client.get("/api/v1/auth/me", headers=auth_headers(org_a)).json()["data"]
    assert response.json()["data"]["organization_id"] == me_a["organization"]["id"]
    assert response.json()["data"]["organization_id"] != org_b_id
