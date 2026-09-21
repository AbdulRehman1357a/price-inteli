import uuid
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.analytics_snapshot import AnalyticsSnapshot
from app.models.device_sync_log import DeviceSyncLog, DeviceSyncStatus
from app.models.mixins import utcnow
from app.services import analytics_service
from tests.conftest import DEVICE_MODEL_ID, DEVICE_VENDOR_ID
from tests.helpers import (
    adjustment_item,
    auth_headers,
    category_payload,
    device_assignment_payload,
    device_payload,
    price_payload,
    product_payload,
    register,
    store_payload,
)

_DEFAULT_PRICES = {"selling_price": "100.0000", "cost_price": "50.0000"}


def _setup(
    client: TestClient,
    tokens: dict,
    sku: str,
    *,
    on_hand: str,
    decrease: str | None = None,
    store_code: str | None = None,
    **overrides,
) -> dict:
    headers = auth_headers(tokens)
    category = client.post("/api/v1/categories", json=category_payload(), headers=headers).json()["data"]
    store_kwargs = {"store_code": store_code} if store_code else {}
    store = client.post(
        "/api/v1/stores", json=store_payload(**store_kwargs), headers=headers
    ).json()["data"]
    payload = product_payload(category_id=category["id"], sku=sku, **{**_DEFAULT_PRICES, **overrides})
    product = client.post("/api/v1/products", json=payload, headers=headers).json()["data"]

    inv_payload = {"store_id": store["id"], "product_id": product["id"], "quantity_on_hand": on_hand}
    inv = client.post("/api/v1/inventory", json=inv_payload, headers=headers)
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

    return {"category": category, "store": store, "product": product, "inventory": inv.json()["data"]}


def _dashboard(client: TestClient, tokens: dict, **params) -> dict:
    response = client.get("/api/v1/analytics/dashboard", params=params, headers=auth_headers(tokens))
    assert response.status_code == 200, response.text
    return response.json()["data"]


def test_dashboard_requires_auth(client: TestClient) -> None:
    response = client.get("/api/v1/analytics/dashboard")
    assert response.status_code == 401


def test_dashboard_default_range_empty_org_returns_zeros(client: TestClient) -> None:
    tokens = register(client)

    data = _dashboard(client, tokens)

    assert Decimal(data["revenue"]) == 0
    assert Decimal(data["gross_margin_amount"]) == 0
    assert data["gross_margin_pct"] is None
    assert data["price_changes_count"] == 0
    assert data["average_price_change"] is None
    assert data["ai_recommendations_count"] == 0
    assert data["ai_approval_rate_pct"] is None
    assert data["low_stock_count"] == 0
    assert data["overstock_count"] == 0
    assert data["failed_device_updates_count"] == 0
    assert data["device_uptime_pct"] is None
    assert data["is_partial"] is False


def test_price_change_count_and_average(client: TestClient) -> None:
    tokens = register(client)
    ctx = _setup(client, tokens, "PRICE-1", on_hand="10")

    price_response = client.post(
        "/api/v1/pricing", json=price_payload(product_id=ctx["product"]["id"]), headers=auth_headers(tokens)
    )
    assert price_response.status_code == 201, price_response.text
    price = price_response.json()["data"]

    # Creation writes a PriceHistory row with old_price=NULL — not counted
    # as a "change" (see PriceHistoryRepository._HAS_PRIOR_PRICE).
    data = _dashboard(client, tokens)
    assert data["price_changes_count"] == 0

    update = client.put(
        f"/api/v1/pricing/{price['id']}",
        json={"selling_price": "89.0000", "reason": "Markdown"},
        headers=auth_headers(tokens),
    )
    assert update.status_code == 200, update.text

    data = _dashboard(client, tokens)
    assert data["price_changes_count"] == 1
    assert Decimal(data["average_price_change"]) == Decimal("-11.0000")


def test_revenue_and_gross_margin_from_stock_decrease(client: TestClient) -> None:
    tokens = register(client)
    _setup(client, tokens, "REV-1", on_hand="100", decrease="10")

    data = _dashboard(client, tokens)

    assert Decimal(data["revenue"]) == Decimal("1000.0000")
    assert Decimal(data["gross_margin_amount"]) == Decimal("500.0000")
    assert Decimal(data["gross_margin_pct"]) == Decimal("50.00")


def test_low_stock_and_overstock_counts(client: TestClient) -> None:
    tokens = register(client)
    headers = auth_headers(tokens)
    category = client.post("/api/v1/categories", json=category_payload(), headers=headers).json()["data"]
    store = client.post("/api/v1/stores", json=store_payload(), headers=headers).json()["data"]

    low_product = client.post(
        "/api/v1/products",
        json=product_payload(category_id=category["id"], sku="LOW-1", **_DEFAULT_PRICES),
        headers=headers,
    ).json()["data"]
    client.post(
        "/api/v1/inventory",
        json={
            "store_id": store["id"],
            "product_id": low_product["id"],
            "quantity_on_hand": "5",
            "reorder_point": "10",
        },
        headers=headers,
    )

    over_product = client.post(
        "/api/v1/products",
        json=product_payload(category_id=category["id"], sku="OVER-1", **_DEFAULT_PRICES),
        headers=headers,
    ).json()["data"]
    client.post(
        "/api/v1/inventory",
        json={
            "store_id": store["id"],
            "product_id": over_product["id"],
            "quantity_on_hand": "100",
            "reorder_point": "10",
        },
        headers=headers,
    )

    data = _dashboard(client, tokens)
    assert data["low_stock_count"] == 1
    assert data["overstock_count"] == 1


def test_ai_recommendations_count_and_approval_rate(client: TestClient) -> None:
    tokens = register(client)
    headers = auth_headers(tokens)
    ctx1 = _setup(client, tokens, "AI-1", on_hand="1000", decrease="950", store_code="AI-STORE-1")
    ctx2 = _setup(client, tokens, "AI-2", on_hand="1000", decrease="950", store_code="AI-STORE-2")

    rec1 = client.post(
        "/api/v1/ai-recommendations/generate",
        json={"product_id": ctx1["product"]["id"], "store_id": ctx1["store"]["id"]},
        headers=headers,
    )
    assert rec1.status_code == 201, rec1.text
    rec2 = client.post(
        "/api/v1/ai-recommendations/generate",
        json={"product_id": ctx2["product"]["id"], "store_id": ctx2["store"]["id"]},
        headers=headers,
    )
    assert rec2.status_code == 201, rec2.text

    approve = client.post(
        f"/api/v1/ai-recommendations/{rec1.json()['data']['id']}/approve", headers=headers
    )
    assert approve.status_code == 200, approve.text

    data = _dashboard(client, tokens)
    assert data["ai_recommendations_count"] == 2
    assert Decimal(data["ai_approval_rate_pct"]) == Decimal("50.00")


def test_failed_device_updates_and_device_uptime(client: TestClient, db_session: Session) -> None:
    tokens = register(client)
    headers = auth_headers(tokens)
    store = client.post("/api/v1/stores", json=store_payload(), headers=headers).json()["data"]
    category = client.post("/api/v1/categories", json=category_payload(), headers=headers).json()["data"]
    product = client.post(
        "/api/v1/products",
        json=product_payload(category_id=category["id"], **_DEFAULT_PRICES),
        headers=headers,
    ).json()["data"]
    device = client.post(
        "/api/v1/devices",
        json=device_payload(
            store_id=store["id"], vendor_id=str(DEVICE_VENDOR_ID), device_model_id=str(DEVICE_MODEL_ID)
        ),
        headers=headers,
    ).json()["data"]

    # Assigning a product to a device triggers one successful sync (see
    # test_device_assignments_and_sync.py).
    assign = client.post(
        "/api/v1/devices/assignments",
        json=device_assignment_payload(
            device_id=device["id"], store_id=store["id"], product_id=product["id"]
        ),
        headers=headers,
    )
    assert assign.status_code == 201, assign.text

    # No API path produces a failed sync (the ESL simulator always
    # succeeds) — inserted directly, same as any other test seeding data
    # outside what the app's own endpoints can trigger.
    db_session.add(
        DeviceSyncLog(
            id=uuid.uuid4(),
            device_id=uuid.UUID(device["id"]),
            product_id=uuid.UUID(product["id"]),
            status=DeviceSyncStatus.FAILED,
            error_message="simulated failure",
            attempted_at=utcnow(),
        )
    )
    db_session.commit()

    data = _dashboard(client, tokens)
    assert data["failed_device_updates_count"] == 1
    assert Decimal(data["device_uptime_pct"]) == Decimal("50.00")


def test_category_and_product_filters_use_live_path(client: TestClient) -> None:
    tokens = register(client)
    ctx_a = _setup(client, tokens, "CATA-1", on_hand="100", decrease="10")
    headers = auth_headers(tokens)
    other_category = client.post(
        "/api/v1/categories", json=category_payload(name="Other"), headers=headers
    ).json()["data"]
    product_b = client.post(
        "/api/v1/products",
        json=product_payload(category_id=other_category["id"], sku="CATB-1", **_DEFAULT_PRICES),
        headers=headers,
    ).json()["data"]
    client.post(
        "/api/v1/inventory",
        json={"store_id": ctx_a["store"]["id"], "product_id": product_b["id"], "quantity_on_hand": "100"},
        headers=headers,
    )
    item = adjustment_item(
        store_id=ctx_a["store"]["id"],
        product_id=product_b["id"],
        adjustment_type="decrease",
        adjustment_quantity="5",
        reason="Sold",
    )
    client.post("/api/v1/inventory/bulk-update", json={"items": [item]}, headers=headers)

    all_data = _dashboard(client, tokens)
    assert Decimal(all_data["revenue"]) == Decimal("1500.0000")  # 10*100 + 5*100

    category_scoped = _dashboard(client, tokens, category_id=ctx_a["category"]["id"])
    assert Decimal(category_scoped["revenue"]) == Decimal("1000.0000")
    assert category_scoped["category_id"] == ctx_a["category"]["id"]

    product_scoped = _dashboard(client, tokens, product_id=product_b["id"])
    assert Decimal(product_scoped["revenue"]) == Decimal("500.0000")


def test_store_filter_scopes_revenue(client: TestClient) -> None:
    tokens = register(client)
    headers = auth_headers(tokens)
    ctx_a = _setup(client, tokens, "STOREA-1", on_hand="100", decrease="10")

    store_b = client.post(
        "/api/v1/stores", json=store_payload(store_code="STORE-B"), headers=headers
    ).json()["data"]
    client.post(
        "/api/v1/inventory",
        json={"store_id": store_b["id"], "product_id": ctx_a["product"]["id"], "quantity_on_hand": "100"},
        headers=headers,
    )
    item = adjustment_item(
        store_id=store_b["id"],
        product_id=ctx_a["product"]["id"],
        adjustment_type="decrease",
        adjustment_quantity="20",
        reason="Sold",
    )
    client.post("/api/v1/inventory/bulk-update", json={"items": [item]}, headers=headers)

    store_a_data = _dashboard(client, tokens, store_id=ctx_a["store"]["id"])
    store_b_data = _dashboard(client, tokens, store_id=store_b["id"])
    all_data = _dashboard(client, tokens)

    assert Decimal(store_a_data["revenue"]) == Decimal("1000.0000")
    assert Decimal(store_b_data["revenue"]) == Decimal("2000.0000")
    assert Decimal(all_data["revenue"]) == Decimal("3000.0000")


def test_snapshot_rows_created_after_dashboard_request(client: TestClient, db_session: Session) -> None:
    tokens = register(client)
    _setup(client, tokens, "SNAP-1", on_hand="100", decrease="10")

    _dashboard(client, tokens)

    today = utcnow().date()
    rows = db_session.query(AnalyticsSnapshot).filter_by(snapshot_date=today).all()
    assert len(rows) >= 2  # at least the org-wide (store_id=NULL) row + one per-store row
    assert any(row.store_id is None for row in rows)
    assert any(row.store_id is not None for row in rows)


def test_recompute_range_is_idempotent(client: TestClient, db_session: Session) -> None:
    tokens = register(client)
    ctx = _setup(client, tokens, "IDEMP-1", on_hand="100", decrease="10")
    organization_id = uuid.UUID(ctx["product"]["organization_id"])
    today = utcnow().date()

    analytics_service.recompute_range(organization_id, start_date=today, end_date=today, db=db_session)
    first_count = db_session.query(AnalyticsSnapshot).filter_by(organization_id=organization_id).count()

    analytics_service.recompute_range(organization_id, start_date=today, end_date=today, db=db_session)
    second_count = db_session.query(AnalyticsSnapshot).filter_by(organization_id=organization_id).count()

    assert first_count == second_count
    data = _dashboard(client, tokens)
    assert Decimal(data["revenue"]) == Decimal("1000.0000")


def test_tenant_isolation(client: TestClient) -> None:
    tokens_a = register(client, organization_name="Org A", email="analytics-a@example.com")
    tokens_b = register(client, organization_name="Org B", email="analytics-b@example.com")
    _setup(client, tokens_a, "ISO-1", on_hand="100", decrease="10")

    data_a = _dashboard(client, tokens_a)
    data_b = _dashboard(client, tokens_b)

    assert Decimal(data_a["revenue"]) == Decimal("1000.0000")
    assert Decimal(data_b["revenue"]) == Decimal("0")
