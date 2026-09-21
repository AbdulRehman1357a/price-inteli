import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.helpers import (
    add_user_with_role,
    adjustment_item,
    auth_headers,
    category_payload,
    product_payload,
    register,
    store_payload,
)

_DEFAULT_PRICES = {"selling_price": "100.0000", "cost_price": "50.0000"}


def _setup(
    client: TestClient, tokens: dict, sku: str, *, on_hand: str, decrease: str | None = None, **overrides
) -> dict:
    """Creates a category/store/product (with the given sku), an inventory
    row, and optionally a stock decrease (a sales-velocity proxy) — the
    common fixture every recommendation test needs.
    """
    headers = auth_headers(tokens)
    category = client.post("/api/v1/categories", json=category_payload(), headers=headers).json()["data"]
    store = client.post("/api/v1/stores", json=store_payload(), headers=headers).json()["data"]
    payload = product_payload(category_id=category["id"], sku=sku, **{**_DEFAULT_PRICES, **overrides})
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


def _generate(client: TestClient, tokens: dict, ctx: dict) -> dict:
    payload = {"product_id": ctx["product"]["id"], "store_id": ctx["store"]["id"]}
    response = client.post("/api/v1/ai-recommendations/generate", json=payload, headers=auth_headers(tokens))
    assert response.status_code == 201, response.text
    return response.json()["data"]


def test_scarcity_signal_recommends_price_increase(client: TestClient) -> None:
    tokens = register(client)
    ctx = _setup(client, tokens, "SCARCE-1", on_hand="1000", decrease="950")

    data = _generate(client, tokens, ctx)

    assert data["status"] == "pending"
    assert data["created_by_agent"] == "heuristic-v1"
    assert float(data["recommended_price"]) > float(data["current_price"])
    assert 0 <= float(data["confidence_score"]) <= 1
    assert "days of supply" in data["recommendation_reason"]
    assert float(data["input_snapshot"]["sales_history"]["units_sold"]) == 950


def test_overstock_signal_recommends_discount(client: TestClient) -> None:
    tokens = register(client)
    ctx = _setup(client, tokens, "OVERSTOCK-1", on_hand="10000", decrease="30")

    data = _generate(client, tokens, ctx)

    assert float(data["recommended_price"]) < float(data["current_price"])
    assert "discount" in data["recommendation_reason"].lower()
    assert data["input_snapshot"]["guardrail"]["passed"] is True


def test_no_signal_no_cost_recommends_no_change(client: TestClient) -> None:
    tokens = register(client)
    ctx = _setup(client, tokens, "NOSIGNAL-1", on_hand="100", selling_price="42.0000", cost_price=None)

    data = _generate(client, tokens, ctx)

    assert data["recommended_price"] == data["current_price"]
    assert float(data["confidence_score"]) <= 0.55
    assert "No cost price" in data["recommendation_reason"]


def test_guardrail_floors_a_below_cost_modification(client: TestClient) -> None:
    tokens = register(client)
    ctx = _setup(client, tokens, "FLOOR-1", on_hand="1000", decrease="950")
    data = _generate(client, tokens, ctx)

    response = client.put(
        f"/api/v1/ai-recommendations/{data['id']}/modify",
        json={"recommended_price": "10.0000"},
        headers=auth_headers(tokens),
    )

    assert response.status_code == 200, response.text
    modified = response.json()["data"]
    assert float(modified["recommended_price"]) == 50.5  # cost 50 * 1.01 floor
    assert modified["status"] == "pending"


def test_approve_then_apply_writes_a_real_price(client: TestClient) -> None:
    tokens = register(client)
    ctx = _setup(client, tokens, "APPLY-1", on_hand="1000", decrease="950")
    data = _generate(client, tokens, ctx)
    headers = auth_headers(tokens)

    approve = client.post(f"/api/v1/ai-recommendations/{data['id']}/approve", headers=headers)
    assert approve.status_code == 200, approve.text
    assert approve.json()["data"]["status"] == "approved"
    assert approve.json()["data"]["reviewed_by"] is not None

    apply_response = client.post(f"/api/v1/ai-recommendations/{data['id']}/apply", headers=headers)
    assert apply_response.status_code == 200, apply_response.text
    applied = apply_response.json()["data"]
    assert applied["status"] == "applied"

    product_id = ctx["product"]["id"]
    prices = client.get(f"/api/v1/pricing?product_id={product_id}", headers=headers).json()["data"]
    assert any(
        abs(float(p["selling_price"]) - float(applied["recommended_price"])) < 0.0001
        and p["store_id"] == ctx["store"]["id"]
        for p in prices
    )


def test_apply_requires_prior_approval(client: TestClient) -> None:
    tokens = register(client)
    ctx = _setup(client, tokens, "NOAPPROVE-1", on_hand="100")
    data = _generate(client, tokens, ctx)

    response = client.post(f"/api/v1/ai-recommendations/{data['id']}/apply", headers=auth_headers(tokens))

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "recommendation_not_approved"


def test_reject_then_cannot_approve_or_apply(client: TestClient) -> None:
    tokens = register(client)
    ctx = _setup(client, tokens, "REJECT-1", on_hand="100")
    data = _generate(client, tokens, ctx)
    headers = auth_headers(tokens)

    reject = client.post(f"/api/v1/ai-recommendations/{data['id']}/reject", headers=headers)
    assert reject.status_code == 200, reject.text
    assert reject.json()["data"]["status"] == "rejected"

    approve_after_reject = client.post(f"/api/v1/ai-recommendations/{data['id']}/approve", headers=headers)
    assert approve_after_reject.status_code == 409
    assert approve_after_reject.json()["error"]["code"] == "recommendation_not_pending"


def test_dashboard_summary_counts_and_impact(client: TestClient) -> None:
    tokens = register(client)
    ctx = _setup(client, tokens, "SUMMARY-1", on_hand="1000", decrease="950")
    _generate(client, tokens, ctx)

    summary = client.get("/api/v1/ai-recommendations/summary", headers=auth_headers(tokens)).json()["data"]

    assert summary["pending_count"] >= 1
    assert summary["approved_count"] == 0


def test_list_recommendations_includes_product_and_store_names(client: TestClient) -> None:
    tokens = register(client)
    ctx = _setup(client, tokens, "LIST-1", on_hand="100")
    _generate(client, tokens, ctx)

    listing = client.get("/api/v1/ai-recommendations", headers=auth_headers(tokens)).json()["data"]

    assert len(listing) == 1
    assert listing[0]["sku"] == "LIST-1"
    assert listing[0]["store_name"] == ctx["store"]["name"]


def test_viewer_can_read_but_not_generate_or_approve(client: TestClient, db_session: Session) -> None:
    tokens = register(client)
    ctx = _setup(client, tokens, "VIEWER-1", on_hand="100")
    me = client.get("/api/v1/auth/me", headers=auth_headers(tokens)).json()["data"]
    organization_id = uuid.UUID(me["organization"]["id"])

    add_user_with_role(
        db_session, organization_id=organization_id, email="aiviewer@acme.com", role_name="Viewer"
    )
    viewer_tokens = client.post(
        "/api/v1/auth/login", json={"email": "aiviewer@acme.com", "password": "SuperSecret1"}
    ).json()["data"]

    read = client.get("/api/v1/ai-recommendations", headers=auth_headers(viewer_tokens))
    assert read.status_code == 200

    generate = client.post(
        "/api/v1/ai-recommendations/generate",
        json={"product_id": ctx["product"]["id"]},
        headers=auth_headers(viewer_tokens),
    )
    assert generate.status_code == 403


def test_recommendations_are_tenant_isolated(client: TestClient) -> None:
    tokens_a = register(client, organization_name="AI Org A", email="aiadmina@a.com")
    ctx = _setup(client, tokens_a, "ISO-1", on_hand="100")
    data = _generate(client, tokens_a, ctx)

    tokens_b = register(client, organization_name="AI Org B", email="aiadminb@b.com")
    response = client.get(f"/api/v1/ai-recommendations/{data['id']}", headers=auth_headers(tokens_b))

    assert response.status_code == 404
