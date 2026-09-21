from fastapi.testclient import TestClient

from tests.helpers import (
    adjustment_item,
    auth_headers,
    category_payload,
    product_payload,
    register,
    store_payload,
)


def _setup(
    client: TestClient, tokens: dict, sku: str, *, on_hand: str, decrease: str | None = None, **overrides
) -> dict:
    headers = auth_headers(tokens)
    category = client.post("/api/v1/categories", json=category_payload(), headers=headers).json()["data"]
    store = client.post("/api/v1/stores", json=store_payload(), headers=headers).json()["data"]
    defaults = {"selling_price": "100.0000", "cost_price": "50.0000"}
    payload = product_payload(category_id=category["id"], sku=sku, **{**defaults, **overrides})
    product = client.post("/api/v1/products", json=payload, headers=headers).json()["data"]

    inv = client.post(
        "/api/v1/inventory",
        json={"store_id": store["id"], "product_id": product["id"], "quantity_on_hand": on_hand},
        headers=headers,
    )
    assert inv.status_code == 201, inv.text

    if decrease is not None:
        item = adjustment_item(
            store_id=store["id"],
            product_id=product["id"],
            adjustment_type="decrease",
            adjustment_quantity=decrease,
            reason="Sold",
        )
        bulk = client.post("/api/v1/inventory/bulk-update", json={"items": [item]}, headers=headers)
        assert bulk.status_code == 200, bulk.text

    return {"category": category, "store": store, "product": product}


def _simulate(client: TestClient, tokens: dict, payload: dict) -> dict:
    response = client.post("/api/v1/pricing/simulations", json=payload, headers=auth_headers(tokens))
    assert response.status_code == 200, response.text
    return response.json()["data"]


def test_price_increase_reduces_units_under_default_elasticity(client: TestClient) -> None:
    tokens = register(client)
    ctx = _setup(client, tokens, "SIM-1", on_hand="1000", decrease="300")

    data = _simulate(
        client,
        tokens,
        {"product_id": ctx["product"]["id"], "store_id": ctx["store"]["id"], "proposed_price": "120.0000"},
    )

    assert data["assumptions"]["demand_change_defaulted"] is True
    assert float(data["proposed_scenario"]["estimated_unit_sales"]) < float(
        data["current_scenario"]["estimated_unit_sales"]
    )
    assert data["current_scenario"]["price"] == "100.0000"
    assert data["proposed_scenario"]["price"] == "120.0000"
    assert data["current_scenario"]["gross_margin_percent"] == "50.00"


def test_explicit_demand_change_overrides_default_elasticity(client: TestClient) -> None:
    tokens = register(client)
    ctx = _setup(client, tokens, "SIM-2", on_hand="1000", decrease="300")

    data = _simulate(
        client,
        tokens,
        {
            "product_id": ctx["product"]["id"],
            "store_id": ctx["store"]["id"],
            "proposed_price": "110.0000",
            "expected_demand_change_percent": "-5",
        },
    )

    assert data["assumptions"]["demand_change_defaulted"] is False
    assert data["assumptions"]["demand_change_percent"] == "-5.00"
    current_units = float(data["current_scenario"]["estimated_unit_sales"])
    proposed_units = float(data["proposed_scenario"]["estimated_unit_sales"])
    assert abs(proposed_units - current_units * 0.95) < 0.5


def test_no_cost_price_leaves_margin_fields_null(client: TestClient) -> None:
    tokens = register(client)
    ctx = _setup(client, tokens, "SIM-3", on_hand="1000", decrease="300", cost_price=None)

    data = _simulate(
        client,
        tokens,
        {"product_id": ctx["product"]["id"], "store_id": ctx["store"]["id"], "proposed_price": "110.0000"},
    )

    assert data["current_scenario"]["gross_margin"] is None
    assert data["current_scenario"]["gross_margin_percent"] is None
    assert data["margin_change"] is None
    assert data["assumptions"]["cost_known"] is False


def test_large_price_increase_with_low_inventory_days_is_high_risk(client: TestClient) -> None:
    tokens = register(client)
    # Fast-moving stock (velocity high relative to remaining inventory) plus
    # a huge price swing should push the risk score into "high".
    ctx = _setup(client, tokens, "SIM-4", on_hand="1000", decrease="950")

    data = _simulate(
        client,
        tokens,
        {
            "product_id": ctx["product"]["id"],
            "store_id": ctx["store"]["id"],
            "proposed_price": "300.0000",
            "expected_demand_change_percent": "-10",
        },
    )

    assert data["risk_level"] in ("medium", "high")
    assert float(data["risk_score"]) > 0


def test_revenue_and_margin_change_are_consistent(client: TestClient) -> None:
    tokens = register(client)
    ctx = _setup(client, tokens, "SIM-5", on_hand="1000", decrease="300")

    data = _simulate(
        client,
        tokens,
        {
            "product_id": ctx["product"]["id"],
            "store_id": ctx["store"]["id"],
            "proposed_price": "100.0000",
            "expected_demand_change_percent": "0",
        },
    )

    # No price change, no demand change -> both scenarios identical.
    assert data["revenue_change"] == "0.0000"
    assert data["margin_change"] == "0.0000"
    assert data["recommendation"]


def test_simulation_requires_pricing_read_permission(client: TestClient) -> None:
    tokens = register(client)
    ctx = _setup(client, tokens, "SIM-6", on_hand="100")

    response = client.post(
        "/api/v1/pricing/simulations",
        json={"product_id": ctx["product"]["id"], "proposed_price": "110.0000"},
        headers={"Authorization": "Bearer invalid"},
    )

    assert response.status_code == 401


def test_simulation_is_tenant_isolated(client: TestClient) -> None:
    tokens_a = register(client, organization_name="Sim Org A", email="sima@a.com")
    ctx = _setup(client, tokens_a, "SIM-7", on_hand="100")

    tokens_b = register(client, organization_name="Sim Org B", email="simb@b.com")
    response = client.post(
        "/api/v1/pricing/simulations",
        json={"product_id": ctx["product"]["id"], "proposed_price": "110.0000"},
        headers=auth_headers(tokens_b),
    )

    assert response.status_code == 404
