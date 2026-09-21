import uuid
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.price_history import PriceHistory
from tests.helpers import (
    add_user_with_role,
    auth_headers,
    category_payload,
    price_payload,
    product_payload,
    register,
)


def _setup_product(client: TestClient, tokens: dict, **overrides) -> dict:
    category = client.post(
        "/api/v1/categories", json=category_payload(), headers=auth_headers(tokens)
    ).json()["data"]
    return client.post(
        "/api/v1/products",
        json=product_payload(category_id=category["id"], **overrides),
        headers=auth_headers(tokens),
    ).json()["data"]


def test_create_price_success(client: TestClient) -> None:
    tokens = register(client)
    product = _setup_product(client, tokens)

    response = client.post(
        "/api/v1/pricing", json=price_payload(product_id=product["id"]), headers=auth_headers(tokens)
    )

    assert response.status_code == 201, response.text
    data = response.json()["data"]
    assert Decimal(data["selling_price"]) == 100
    assert data["status"] == "active"


def test_create_price_unknown_product_returns_404(client: TestClient) -> None:
    tokens = register(client)

    response = client.post(
        "/api/v1/pricing",
        json=price_payload(product_id="00000000-0000-0000-0000-000000000000"),
        headers=auth_headers(tokens),
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "product_not_found"


def test_create_price_writes_history(client: TestClient, db_session: Session) -> None:
    tokens = register(client)
    product = _setup_product(client, tokens)

    created = client.post(
        "/api/v1/pricing",
        json=price_payload(product_id=product["id"], reason="Initial price"),
        headers=auth_headers(tokens),
    ).json()["data"]

    history = (
        db_session.query(PriceHistory).filter_by(product_id=uuid.UUID(product["id"])).one()
    )
    assert history.old_price is None
    assert history.new_price == Decimal("100.0000")
    assert history.change_type == "created"
    assert history.source == "manual"
    assert history.reason == "Initial price"
    assert str(history.product_id) == product["id"]
    assert created["id"]


def test_get_price_by_id(client: TestClient) -> None:
    tokens = register(client)
    product = _setup_product(client, tokens)
    created = client.post(
        "/api/v1/pricing", json=price_payload(product_id=product["id"]), headers=auth_headers(tokens)
    ).json()["data"]

    response = client.get(f"/api/v1/pricing/{created['id']}", headers=auth_headers(tokens))

    assert response.status_code == 200
    assert response.json()["data"]["id"] == created["id"]


def test_get_unknown_price_returns_404(client: TestClient) -> None:
    tokens = register(client)

    response = client.get(
        "/api/v1/pricing/00000000-0000-0000-0000-000000000000", headers=auth_headers(tokens)
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "price_not_found"


def test_update_price_selling_price_writes_history(client: TestClient, db_session: Session) -> None:
    tokens = register(client)
    product = _setup_product(client, tokens)
    created = client.post(
        "/api/v1/pricing", json=price_payload(product_id=product["id"]), headers=auth_headers(tokens)
    ).json()["data"]

    response = client.put(
        f"/api/v1/pricing/{created['id']}",
        json={"selling_price": "89.9900", "reason": "Markdown", "source": "manual"},
        headers=auth_headers(tokens),
    )

    assert response.status_code == 200
    assert Decimal(response.json()["data"]["selling_price"]) == Decimal("89.99")

    entries = (
        db_session.query(PriceHistory).filter_by(product_id=uuid.UUID(product["id"])).order_by(PriceHistory.created_at).all()
    )
    assert len(entries) == 2  # created + updated
    assert entries[1].change_type == "updated"
    assert entries[1].old_price == Decimal("100.0000")
    assert entries[1].new_price == Decimal("89.9900")


def test_update_price_without_selling_price_change_writes_no_extra_history(
    client: TestClient, db_session: Session
) -> None:
    tokens = register(client)
    product = _setup_product(client, tokens)
    created = client.post(
        "/api/v1/pricing", json=price_payload(product_id=product["id"]), headers=auth_headers(tokens)
    ).json()["data"]

    client.put(
        f"/api/v1/pricing/{created['id']}", json={"status": "inactive"}, headers=auth_headers(tokens)
    )

    count = db_session.query(PriceHistory).filter_by(product_id=uuid.UUID(product["id"])).count()
    assert count == 1  # just the original "created" entry


def test_list_prices_filters_by_status(client: TestClient) -> None:
    tokens = register(client)
    product = _setup_product(client, tokens)
    client.post(
        "/api/v1/pricing",
        json=price_payload(product_id=product["id"], status="inactive"),
        headers=auth_headers(tokens),
    )
    client.post(
        "/api/v1/pricing", json=price_payload(product_id=product["id"]), headers=auth_headers(tokens)
    )

    response = client.get("/api/v1/pricing?status=inactive", headers=auth_headers(tokens))

    assert response.status_code == 200
    assert len(response.json()["data"]) == 1
    assert response.json()["data"][0]["status"] == "inactive"


def test_price_status_computed_as_scheduled_for_future_effective_from(client: TestClient) -> None:
    tokens = register(client)
    product = _setup_product(client, tokens)

    created = client.post(
        "/api/v1/pricing",
        json=price_payload(product_id=product["id"], effective_from="2099-01-01T00:00:00Z"),
        headers=auth_headers(tokens),
    ).json()["data"]

    assert created["status"] == "scheduled"


def test_price_status_computed_as_expired_for_past_effective_to(client: TestClient) -> None:
    tokens = register(client)
    product = _setup_product(client, tokens)

    created = client.post(
        "/api/v1/pricing",
        json=price_payload(
            product_id=product["id"],
            effective_from="2020-01-01T00:00:00Z",
            effective_to="2020-06-01T00:00:00Z",
        ),
        headers=auth_headers(tokens),
    ).json()["data"]

    assert created["status"] == "expired"


def test_role_without_pricing_create_permission_is_denied(client: TestClient, db_session: Session) -> None:
    admin_tokens = register(client)
    product = _setup_product(client, admin_tokens)
    organization_id = client.get("/api/v1/auth/me", headers=auth_headers(admin_tokens)).json()["data"][
        "user"
    ]["organization_id"]

    add_user_with_role(
        db_session,
        organization_id=uuid.UUID(organization_id),
        email="viewer@acme.com",
        role_name="Viewer",
    )
    login = client.post(
        "/api/v1/auth/login", json={"email": "viewer@acme.com", "password": "SuperSecret1"}
    )
    viewer_tokens = login.json()["data"]

    response = client.post(
        "/api/v1/pricing", json=price_payload(product_id=product["id"]), headers=auth_headers(viewer_tokens)
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "permission_denied"
