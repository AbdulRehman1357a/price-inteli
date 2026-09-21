import uuid
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.inventory_adjustment import InventoryAdjustment
from tests.helpers import (
    add_user_with_role,
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


def test_create_inventory_defaults_to_zero_and_out_of_stock(client: TestClient) -> None:
    tokens = register(client)
    store_id, product_id = _setup_store_and_product(client, tokens)

    item = _create_inventory(client, tokens, store_id, product_id)

    assert Decimal(item["quantity_on_hand"]) == 0
    assert Decimal(item["quantity_available"]) == 0
    assert item["status"] == "out_of_stock"


def test_create_inventory_with_initial_stock(client: TestClient) -> None:
    tokens = register(client)
    store_id, product_id = _setup_store_and_product(client, tokens)

    # reorder_point=50 keeps this out of both low_stock (on_hand > reorder_point)
    # and overstock (on_hand <= reorder_point * OVERSTOCK_MULTIPLIER == 150).
    item = _create_inventory(
        client, tokens, store_id, product_id, quantity_on_hand="100", reorder_point="50"
    )

    assert Decimal(item["quantity_on_hand"]) == 100
    assert Decimal(item["quantity_available"]) == 100
    assert item["status"] == "in_stock"


def test_create_duplicate_inventory_conflicts(client: TestClient) -> None:
    tokens = register(client)
    store_id, product_id = _setup_store_and_product(client, tokens)
    _create_inventory(client, tokens, store_id, product_id)

    response = client.post(
        "/api/v1/inventory",
        json=inventory_payload(store_id=store_id, product_id=product_id),
        headers=auth_headers(tokens),
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "inventory_exists"


def test_create_inventory_unknown_store_returns_404(client: TestClient) -> None:
    tokens = register(client)
    _, product_id = _setup_store_and_product(client, tokens)

    response = client.post(
        "/api/v1/inventory",
        json=inventory_payload(
            store_id="00000000-0000-0000-0000-000000000000", product_id=product_id
        ),
        headers=auth_headers(tokens),
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "store_not_found"


def test_get_inventory_by_id(client: TestClient) -> None:
    tokens = register(client)
    store_id, product_id = _setup_store_and_product(client, tokens)
    created = _create_inventory(client, tokens, store_id, product_id)

    response = client.get(f"/api/v1/inventory/{created['id']}", headers=auth_headers(tokens))

    assert response.status_code == 200
    assert response.json()["data"]["id"] == created["id"]


def test_get_unknown_inventory_returns_404(client: TestClient) -> None:
    tokens = register(client)

    response = client.get(
        "/api/v1/inventory/00000000-0000-0000-0000-000000000000", headers=auth_headers(tokens)
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "inventory_not_found"


def test_update_inventory_settings_recomputes_available(client: TestClient) -> None:
    tokens = register(client)
    store_id, product_id = _setup_store_and_product(client, tokens)
    created = _create_inventory(client, tokens, store_id, product_id, quantity_on_hand="50")

    response = client.put(
        f"/api/v1/inventory/{created['id']}",
        json={"quantity_reserved": "10", "reorder_point": "5", "safety_stock": "2"},
        headers=auth_headers(tokens),
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert Decimal(data["quantity_reserved"]) == 10
    assert Decimal(data["quantity_available"]) == 40
    assert Decimal(data["reorder_point"]) == 5


def test_update_inventory_ignores_client_supplied_quantity_on_hand(client: TestClient) -> None:
    tokens = register(client)
    store_id, product_id = _setup_store_and_product(client, tokens)
    created = _create_inventory(client, tokens, store_id, product_id, quantity_on_hand="50")

    response = client.put(
        f"/api/v1/inventory/{created['id']}",
        json={"quantity_on_hand": "999999"},
        headers=auth_headers(tokens),
    )

    assert response.status_code == 200
    # PUT has no quantity_on_hand field at all — the extra key is silently
    # ignored, on_hand stays exactly what it was.
    assert Decimal(response.json()["data"]["quantity_on_hand"]) == 50


def test_list_inventory_filters(client: TestClient) -> None:
    tokens = register(client)
    store_id, product_id = _setup_store_and_product(client, tokens)
    low = _create_inventory(
        client, tokens, store_id, product_id, quantity_on_hand="5", reorder_point="10"
    )

    category2 = client.post(
        "/api/v1/categories", json=category_payload(name="Apparel"), headers=auth_headers(tokens)
    ).json()["data"]
    product2 = client.post(
        "/api/v1/products",
        json=product_payload(category_id=category2["id"], sku="SKU-2", product_name="T-Shirt"),
        headers=auth_headers(tokens),
    ).json()["data"]
    zero = _create_inventory(client, tokens, store_id, product2["id"], quantity_on_hand="0")

    low_stock = client.get("/api/v1/inventory?low_stock=true", headers=auth_headers(tokens)).json()[
        "data"
    ]
    assert [i["id"] for i in low_stock] == [low["id"]]

    out_of_stock = client.get(
        "/api/v1/inventory?out_of_stock=true", headers=auth_headers(tokens)
    ).json()["data"]
    assert [i["id"] for i in out_of_stock] == [zero["id"]]

    by_product = client.get(
        f"/api/v1/inventory?product_id={product2['id']}", headers=auth_headers(tokens)
    ).json()["data"]
    assert [i["id"] for i in by_product] == [zero["id"]]

    by_category = client.get(
        f"/api/v1/inventory?category_id={category2['id']}", headers=auth_headers(tokens)
    ).json()["data"]
    assert [i["id"] for i in by_category] == [zero["id"]]


def test_inventory_summary_counts(client: TestClient) -> None:
    tokens = register(client)
    store_id, product_id = _setup_store_and_product(client, tokens)
    _create_inventory(client, tokens, store_id, product_id, quantity_on_hand="0")

    category2 = client.post(
        "/api/v1/categories", json=category_payload(name="Apparel"), headers=auth_headers(tokens)
    ).json()["data"]
    product2 = client.post(
        "/api/v1/products",
        json=product_payload(category_id=category2["id"], sku="SKU-2"),
        headers=auth_headers(tokens),
    ).json()["data"]
    _create_inventory(
        client, tokens, store_id, product2["id"], quantity_on_hand="500", reorder_point="10"
    )

    response = client.get("/api/v1/inventory/summary", headers=auth_headers(tokens))

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total_products"] == 2
    assert data["out_of_stock"] == 1
    assert data["overstock"] == 1
    assert data["low_stock"] == 0


def test_bulk_update_increase(client: TestClient) -> None:
    tokens = register(client)
    store_id, product_id = _setup_store_and_product(client, tokens)
    created = _create_inventory(client, tokens, store_id, product_id, quantity_on_hand="10")

    response = client.post(
        "/api/v1/inventory/bulk-update",
        json={"items": [adjustment_item(store_id=store_id, product_id=product_id, adjustment_quantity="5")]},
        headers=auth_headers(tokens),
    )

    assert response.status_code == 200, response.text
    data = response.json()["data"][0]
    assert Decimal(data["quantity_on_hand"]) == 15
    assert data["id"] == created["id"]


def test_bulk_update_decrease(client: TestClient) -> None:
    tokens = register(client)
    store_id, product_id = _setup_store_and_product(client, tokens)
    _create_inventory(client, tokens, store_id, product_id, quantity_on_hand="10")

    response = client.post(
        "/api/v1/inventory/bulk-update",
        json={
            "items": [
                adjustment_item(
                    store_id=store_id,
                    product_id=product_id,
                    adjustment_type="decrease",
                    adjustment_quantity="4",
                    reason="Damaged goods",
                )
            ]
        },
        headers=auth_headers(tokens),
    )

    assert response.status_code == 200
    assert Decimal(response.json()["data"][0]["quantity_on_hand"]) == 6


def test_bulk_update_correction_sets_absolute_value(client: TestClient) -> None:
    tokens = register(client)
    store_id, product_id = _setup_store_and_product(client, tokens)
    _create_inventory(client, tokens, store_id, product_id, quantity_on_hand="10")

    response = client.post(
        "/api/v1/inventory/bulk-update",
        json={
            "items": [
                adjustment_item(
                    store_id=store_id,
                    product_id=product_id,
                    adjustment_type="correction",
                    adjustment_quantity="42",
                    reason="Cycle count",
                )
            ]
        },
        headers=auth_headers(tokens),
    )

    assert response.status_code == 200
    assert Decimal(response.json()["data"][0]["quantity_on_hand"]) == 42


def test_bulk_update_rejects_negative_result_by_default(client: TestClient) -> None:
    tokens = register(client)
    store_id, product_id = _setup_store_and_product(client, tokens)
    _create_inventory(client, tokens, store_id, product_id, quantity_on_hand="5")

    response = client.post(
        "/api/v1/inventory/bulk-update",
        json={
            "items": [
                adjustment_item(
                    store_id=store_id,
                    product_id=product_id,
                    adjustment_type="decrease",
                    adjustment_quantity="10",
                )
            ]
        },
        headers=auth_headers(tokens),
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "negative_inventory_not_allowed"


def test_bulk_update_allows_negative_when_explicitly_flagged(client: TestClient) -> None:
    tokens = register(client)
    store_id, product_id = _setup_store_and_product(client, tokens)
    _create_inventory(client, tokens, store_id, product_id, quantity_on_hand="5")

    response = client.post(
        "/api/v1/inventory/bulk-update",
        json={
            "items": [
                adjustment_item(
                    store_id=store_id,
                    product_id=product_id,
                    adjustment_type="decrease",
                    adjustment_quantity="10",
                    allow_negative=True,
                )
            ]
        },
        headers=auth_headers(tokens),
    )

    assert response.status_code == 200
    assert Decimal(response.json()["data"][0]["quantity_on_hand"]) == -5


def test_bulk_update_unknown_inventory_returns_404(client: TestClient) -> None:
    tokens = register(client)
    store_id, product_id = _setup_store_and_product(client, tokens)
    # No inventory row created for this store/product.

    response = client.post(
        "/api/v1/inventory/bulk-update",
        json={"items": [adjustment_item(store_id=store_id, product_id=product_id)]},
        headers=auth_headers(tokens),
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "inventory_not_found"


def test_bulk_update_is_atomic_across_items(client: TestClient) -> None:
    tokens = register(client)
    store_id, product_id = _setup_store_and_product(client, tokens)
    first = _create_inventory(client, tokens, store_id, product_id, quantity_on_hand="10")

    category2 = client.post(
        "/api/v1/categories", json=category_payload(name="Apparel"), headers=auth_headers(tokens)
    ).json()["data"]
    product2 = client.post(
        "/api/v1/products",
        json=product_payload(category_id=category2["id"], sku="SKU-2"),
        headers=auth_headers(tokens),
    ).json()["data"]
    # No inventory row for product2 — this item will fail with 404, and
    # since both items share one transaction, the first item's increase
    # must not be persisted either.

    response = client.post(
        "/api/v1/inventory/bulk-update",
        json={
            "items": [
                adjustment_item(store_id=store_id, product_id=product_id, adjustment_quantity="100"),
                adjustment_item(store_id=store_id, product_id=product2["id"]),
            ]
        },
        headers=auth_headers(tokens),
    )

    assert response.status_code == 404

    unchanged = client.get(f"/api/v1/inventory/{first['id']}", headers=auth_headers(tokens)).json()[
        "data"
    ]
    assert Decimal(unchanged["quantity_on_hand"]) == 10


def test_bulk_update_records_audit_trail(client: TestClient, db_session: Session) -> None:
    tokens = register(client)
    store_id, product_id = _setup_store_and_product(client, tokens)
    created = _create_inventory(client, tokens, store_id, product_id, quantity_on_hand="10")

    client.post(
        "/api/v1/inventory/bulk-update",
        json={
            "items": [
                adjustment_item(
                    store_id=store_id,
                    product_id=product_id,
                    adjustment_quantity="5",
                    reason="Received shipment",
                    notes="PO #123",
                )
            ]
        },
        headers=auth_headers(tokens),
    )

    adjustment = db_session.query(InventoryAdjustment).filter_by(inventory_id=uuid.UUID(created["id"])).one()
    assert adjustment.quantity_before == 10
    assert adjustment.quantity_after == 15
    assert adjustment.reason == "Received shipment"
    assert adjustment.notes == "PO #123"
    assert adjustment.created_by_user_id is not None


def test_role_without_adjust_permission_is_denied(client: TestClient, db_session: Session) -> None:
    admin_tokens = register(client)
    store_id, product_id = _setup_store_and_product(client, admin_tokens)
    _create_inventory(client, admin_tokens, store_id, product_id)
    organization_id = client.get("/api/v1/auth/me", headers=auth_headers(admin_tokens)).json()["data"][
        "user"
    ]["organization_id"]

    add_user_with_role(
        db_session,
        organization_id=uuid.UUID(organization_id),
        email="pricingmgr@acme.com",
        role_name="Pricing Manager",
    )
    login = client.post(
        "/api/v1/auth/login", json={"email": "pricingmgr@acme.com", "password": "SuperSecret1"}
    )
    pricing_tokens = login.json()["data"]

    response = client.post(
        "/api/v1/inventory/bulk-update",
        json={"items": [adjustment_item(store_id=store_id, product_id=product_id)]},
        headers=auth_headers(pricing_tokens),
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "permission_denied"
