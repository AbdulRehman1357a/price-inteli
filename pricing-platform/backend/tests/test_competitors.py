from decimal import Decimal

from fastapi.testclient import TestClient

from app.integrations.competitors.base import RawCompetitorPriceObservation
from tests.helpers import auth_headers, category_payload, product_payload, register, store_payload


def _setup_product(client: TestClient, tokens: dict, sku: str, **overrides) -> dict:
    headers = auth_headers(tokens)
    category = client.post("/api/v1/categories", json=category_payload(), headers=headers).json()["data"]
    client.post("/api/v1/stores", json=store_payload(), headers=headers)
    payload = product_payload(category_id=category["id"], sku=sku, selling_price="100.0000", **overrides)
    return client.post("/api/v1/products", json=payload, headers=headers).json()["data"]


def _create_competitor(client: TestClient, tokens: dict, **overrides) -> dict:
    payload = {"name": "Rival Retail"}
    payload.update(overrides)
    response = client.post("/api/v1/competitors", json=payload, headers=auth_headers(tokens))
    assert response.status_code == 201, response.text
    return response.json()["data"]


def _track_product(
    client: TestClient, tokens: dict, competitor_id: str, product_id: str, **overrides
) -> dict:
    payload = {"product_id": product_id}
    payload.update(overrides)
    response = client.post(
        f"/api/v1/competitors/{competitor_id}/products", json=payload, headers=auth_headers(tokens)
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]


def test_create_competitor_and_track_a_product(client: TestClient) -> None:
    tokens = register(client)
    product = _setup_product(client, tokens, "COMP-1")
    competitor = _create_competitor(client, tokens)

    tracked = _track_product(
        client, tokens, competitor["id"], product["id"], external_product_url="https://rival.example.com/api/x"
    )

    assert tracked["product_name"] == product["product_name"]
    assert tracked["sku"] == "COMP-1"
    assert tracked["latest_price"] is None


def test_record_manual_price_updates_latest_price(client: TestClient) -> None:
    tokens = register(client)
    product = _setup_product(client, tokens, "COMP-2")
    competitor = _create_competitor(client, tokens)
    tracked = _track_product(client, tokens, competitor["id"], product["id"])

    response = client.post(
        f"/api/v1/competitors/products/{tracked['id']}/prices",
        json={"price": "95.0000", "currency": "USD", "availability": "in_stock"},
        headers=auth_headers(tokens),
    )
    assert response.status_code == 201, response.text
    assert response.json()["data"]["source"] == "manual"

    prices = client.get(
        f"/api/v1/competitors/products/{tracked['id']}/prices", headers=auth_headers(tokens)
    ).json()["data"]
    assert len(prices) == 1
    assert prices[0]["price"] == "95.0000"

    listing = client.get(
        f"/api/v1/competitors/{competitor['id']}/products", headers=auth_headers(tokens)
    ).json()["data"]
    assert listing[0]["latest_price"] == "95.0000"


def test_sync_price_from_api_uses_the_configured_provider(client: TestClient, monkeypatch) -> None:
    tokens = register(client)
    product = _setup_product(client, tokens, "COMP-3")
    competitor = _create_competitor(client, tokens)
    tracked = _track_product(
        client, tokens, competitor["id"], product["id"], external_product_url="https://rival.example.com/api/x"
    )

    def fake_fetch_price(self, external_product_url):
        assert external_product_url == "https://rival.example.com/api/x"
        return RawCompetitorPriceObservation(
            price=Decimal("88.5000"), currency="USD", availability="in_stock"
        )

    monkeypatch.setattr(
        "app.integrations.competitors.api_provider.APICompetitorPriceProvider.fetch_price", fake_fetch_price
    )

    response = client.post(
        f"/api/v1/competitors/products/{tracked['id']}/prices/sync", headers=auth_headers(tokens)
    )

    assert response.status_code == 201, response.text
    data = response.json()["data"]
    assert data["source"] == "api"
    assert data["price"] == "88.5000"


def test_sync_price_without_url_fails_clearly(client: TestClient) -> None:
    tokens = register(client)
    product = _setup_product(client, tokens, "COMP-4")
    competitor = _create_competitor(client, tokens)
    tracked = _track_product(client, tokens, competitor["id"], product["id"])

    response = client.post(
        f"/api/v1/competitors/products/{tracked['id']}/prices/sync", headers=auth_headers(tokens)
    )

    assert response.status_code == 422


def test_dashboard_shows_price_gap_and_position(client: TestClient) -> None:
    tokens = register(client)
    product = _setup_product(client, tokens, "COMP-5")  # our selling_price = 100
    competitor = _create_competitor(client, tokens)
    tracked = _track_product(client, tokens, competitor["id"], product["id"])
    client.post(
        f"/api/v1/competitors/products/{tracked['id']}/prices",
        json={"price": "90.0000", "currency": "USD"},
        headers=auth_headers(tokens),
    )

    dashboard = client.get("/api/v1/competitors/dashboard", headers=auth_headers(tokens)).json()["data"]

    assert len(dashboard) == 1
    row = dashboard[0]
    assert row["competitor_price"] == "90.0000"
    assert row["position"] == "more_expensive"  # we're at 100, they're at 90
    assert float(row["price_gap"]) == 10.0


def test_delete_competitor_blocked_with_tracked_products(client: TestClient) -> None:
    tokens = register(client)
    product = _setup_product(client, tokens, "COMP-6")
    competitor = _create_competitor(client, tokens)
    _track_product(client, tokens, competitor["id"], product["id"])

    response = client.delete(f"/api/v1/competitors/{competitor['id']}", headers=auth_headers(tokens))

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "competitor_has_products"


def test_delete_competitor_product_blocked_with_price_history(client: TestClient) -> None:
    tokens = register(client)
    product = _setup_product(client, tokens, "COMP-7")
    competitor = _create_competitor(client, tokens)
    tracked = _track_product(client, tokens, competitor["id"], product["id"])
    client.post(
        f"/api/v1/competitors/products/{tracked['id']}/prices",
        json={"price": "50.0000"},
        headers=auth_headers(tokens),
    )

    response = client.delete(f"/api/v1/competitors/products/{tracked['id']}", headers=auth_headers(tokens))

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "competitor_product_has_prices"


def test_competitors_are_tenant_isolated(client: TestClient) -> None:
    tokens_a = register(client, organization_name="Comp Org A", email="compa@a.com")
    competitor = _create_competitor(client, tokens_a)

    tokens_b = register(client, organization_name="Comp Org B", email="compb@b.com")
    response = client.get(f"/api/v1/competitors/{competitor['id']}", headers=auth_headers(tokens_b))

    assert response.status_code == 404
