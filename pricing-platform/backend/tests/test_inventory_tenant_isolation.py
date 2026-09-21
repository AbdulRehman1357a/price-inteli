from fastapi.testclient import TestClient

from tests.helpers import (
    adjustment_item,
    auth_headers,
    category_payload,
    inventory_payload,
    product_payload,
    register,
    store_payload,
)


def _setup_store_and_product(client: TestClient, tokens: dict) -> tuple[str, str]:
    store = client.post("/api/v1/stores", json=store_payload(), headers=auth_headers(tokens)).json()[
        "data"
    ]
    category = client.post(
        "/api/v1/categories", json=category_payload(), headers=auth_headers(tokens)
    ).json()["data"]
    product = client.post(
        "/api/v1/products",
        json=product_payload(category_id=category["id"]),
        headers=auth_headers(tokens),
    ).json()["data"]
    return store["id"], product["id"]


def _create_inventory(client: TestClient, tokens: dict, store_id: str, product_id: str, **overrides) -> dict:
    response = client.post(
        "/api/v1/inventory",
        json=inventory_payload(store_id=store_id, product_id=product_id, **overrides),
        headers=auth_headers(tokens),
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]


def _two_orgs(client: TestClient) -> tuple[dict, dict]:
    org_a = register(client, organization_name="Org A", email="admin-a@acme.com")
    org_b = register(client, organization_name="Org B", email="admin-b@acme.com")
    return org_a, org_b


def test_inventory_list_never_crosses_organizations(client: TestClient) -> None:
    org_a, org_b = _two_orgs(client)
    store_a, product_a = _setup_store_and_product(client, org_a)
    store_b, product_b = _setup_store_and_product(client, org_b)
    item_a = _create_inventory(client, org_a, store_a, product_a)
    item_b = _create_inventory(client, org_b, store_b, product_b)

    list_a = client.get("/api/v1/inventory", headers=auth_headers(org_a)).json()["data"]
    list_b = client.get("/api/v1/inventory", headers=auth_headers(org_b)).json()["data"]

    assert [i["id"] for i in list_a] == [item_a["id"]]
    assert [i["id"] for i in list_b] == [item_b["id"]]


def test_cannot_get_or_update_another_organizations_inventory(client: TestClient) -> None:
    org_a, org_b = _two_orgs(client)
    store_b, product_b = _setup_store_and_product(client, org_b)
    item_b = _create_inventory(client, org_b, store_b, product_b)

    get_response = client.get(f"/api/v1/inventory/{item_b['id']}", headers=auth_headers(org_a))
    update_response = client.put(
        f"/api/v1/inventory/{item_b['id']}", json={"reorder_point": "1"}, headers=auth_headers(org_a)
    )

    assert get_response.status_code == 404
    assert update_response.status_code == 404


def test_cannot_create_inventory_against_another_orgs_store(client: TestClient) -> None:
    org_a, org_b = _two_orgs(client)
    store_b, _ = _setup_store_and_product(client, org_b)
    _, product_a = _setup_store_and_product(client, org_a)

    response = client.post(
        "/api/v1/inventory",
        json=inventory_payload(store_id=store_b, product_id=product_a),
        headers=auth_headers(org_a),
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "store_not_found"


def test_cannot_create_inventory_against_another_orgs_product(client: TestClient) -> None:
    org_a, org_b = _two_orgs(client)
    store_a, _ = _setup_store_and_product(client, org_a)
    _, product_b = _setup_store_and_product(client, org_b)

    response = client.post(
        "/api/v1/inventory",
        json=inventory_payload(store_id=store_a, product_id=product_b),
        headers=auth_headers(org_a),
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "product_not_found"


def test_cannot_bulk_adjust_another_organizations_inventory(client: TestClient) -> None:
    org_a, org_b = _two_orgs(client)
    store_b, product_b = _setup_store_and_product(client, org_b)
    _create_inventory(client, org_b, store_b, product_b)

    response = client.post(
        "/api/v1/inventory/bulk-update",
        json={"items": [adjustment_item(store_id=store_b, product_id=product_b)]},
        headers=auth_headers(org_a),
    )

    # org A has no inventory row for org B's store/product — 404, not a
    # cross-tenant mutation.
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "inventory_not_found"


def test_summary_never_counts_another_organizations_inventory(client: TestClient) -> None:
    org_a, org_b = _two_orgs(client)
    store_a, product_a = _setup_store_and_product(client, org_a)
    store_b, product_b = _setup_store_and_product(client, org_b)
    _create_inventory(client, org_a, store_a, product_a, quantity_on_hand="0")
    _create_inventory(client, org_b, store_b, product_b, quantity_on_hand="0")

    summary_a = client.get("/api/v1/inventory/summary", headers=auth_headers(org_a)).json()["data"]

    assert summary_a["total_products"] == 1
    assert summary_a["out_of_stock"] == 1


def test_client_supplied_organization_id_is_ignored(client: TestClient) -> None:
    org_a, org_b = _two_orgs(client)
    store_a, product_a = _setup_store_and_product(client, org_a)
    org_b_id = client.get("/api/v1/auth/me", headers=auth_headers(org_b)).json()["data"]["organization"][
        "id"
    ]

    response = client.post(
        "/api/v1/inventory",
        json={**inventory_payload(store_id=store_a, product_id=product_a), "organization_id": org_b_id},
        headers=auth_headers(org_a),
    )

    assert response.status_code == 201
    me_a = client.get("/api/v1/auth/me", headers=auth_headers(org_a)).json()["data"]
    assert response.json()["data"]["organization_id"] == me_a["organization"]["id"]
    assert response.json()["data"]["organization_id"] != org_b_id
