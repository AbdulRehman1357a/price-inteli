import hashlib
import hmac
import json
import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.services import integration_sync_service, integration_webhook_service
from tests.helpers import (
    add_user_with_role,
    auth_headers,
    integration_authority_payload,
    integration_mapping_payload,
    integration_payload,
    integration_sync_schedule_payload,
    register,
)


def _run_worker(db_session: Session, job_id: str) -> None:
    integration_sync_service.process_sync_job(uuid.UUID(job_id), db=db_session)


def _create_integration(client: TestClient, tokens: dict, **overrides) -> dict:
    payload = integration_payload(
        provider="webhook", credentials={"webhook_url": "https://example.com/hook"}, **overrides
    )
    return client.post("/api/v1/integrations", json=payload, headers=auth_headers(tokens)).json()["data"]


def _setup_product_mapping(client: TestClient, tokens: dict, integration_id: str) -> None:
    client.post(
        f"/api/v1/integrations/{integration_id}/mappings",
        json=integration_mapping_payload(source_field="SKU", canonical_field="sku"),
        headers=auth_headers(tokens),
    )
    client.post(
        f"/api/v1/integrations/{integration_id}/mappings",
        json=integration_mapping_payload(source_field="Name", canonical_field="product_name"),
        headers=auth_headers(tokens),
    )
    client.post(
        f"/api/v1/integrations/{integration_id}/mappings",
        json=integration_mapping_payload(source_field="Category", canonical_field="category"),
        headers=auth_headers(tokens),
    )
    client.post(
        f"/api/v1/integrations/{integration_id}/mappings",
        json=integration_mapping_payload(
            source_field="Price", canonical_field="selling_price", transformation_rule="direct"
        ),
        headers=auth_headers(tokens),
    )


def _setup_price_mapping(client: TestClient, tokens: dict, integration_id: str) -> None:
    client.post(
        f"/api/v1/integrations/{integration_id}/mappings",
        json=integration_mapping_payload(entity_type="price", source_field="SKU", canonical_field="sku"),
        headers=auth_headers(tokens),
    )
    client.post(
        f"/api/v1/integrations/{integration_id}/mappings",
        json=integration_mapping_payload(
            entity_type="price", source_field="Price", canonical_field="selling_price"
        ),
        headers=auth_headers(tokens),
    )


# --- Connection / capabilities ---


def test_capabilities_reported_on_integration_out(client: TestClient) -> None:
    tokens = register(client)
    integration = client.post(
        "/api/v1/integrations",
        json=integration_payload(provider="rest_api", credentials={"base_url": "https://example.com/api"}),
        headers=auth_headers(tokens),
    ).json()["data"]

    assert integration["capabilities"]["supports_price_write"] is True
    assert integration["capabilities"]["supports_incremental_sync"] is True

    csv_integration = client.post(
        "/api/v1/integrations", json=integration_payload(provider="csv"), headers=auth_headers(tokens)
    ).json()["data"]
    assert csv_integration["capabilities"]["supports_price_write"] is False
    assert csv_integration["capabilities"]["supports_price_read"] is True


def test_test_connection_updates_last_successful_connection_at(client: TestClient) -> None:
    tokens = register(client)
    integration = _create_integration(client, tokens)

    client.post(f"/api/v1/integrations/{integration['id']}/test", headers=auth_headers(tokens))
    refreshed = client.get(
        f"/api/v1/integrations/{integration['id']}", headers=auth_headers(tokens)
    ).json()["data"]

    assert refreshed["last_successful_connection_at"] is not None
    assert refreshed["last_connection_error"] is None


def test_test_connection_failure_updates_last_failed_connection_at(client: TestClient) -> None:
    tokens = register(client)
    integration = client.post(
        "/api/v1/integrations", json=integration_payload(provider="webhook"), headers=auth_headers(tokens)
    ).json()["data"]

    client.post(f"/api/v1/integrations/{integration['id']}/test", headers=auth_headers(tokens))
    refreshed = client.get(
        f"/api/v1/integrations/{integration['id']}", headers=auth_headers(tokens)
    ).json()["data"]

    assert refreshed["last_failed_connection_at"] is not None
    assert refreshed["last_connection_error"] is not None


# --- Mapping engine: required / validation_rule ---


def test_mapping_required_enforced(client: TestClient, db_session: Session) -> None:
    tokens = register(client)
    integration = _create_integration(client, tokens)
    client.post(
        f"/api/v1/integrations/{integration['id']}/mappings",
        json=integration_mapping_payload(source_field="SKU", canonical_field="sku"),
        headers=auth_headers(tokens),
    )
    client.post(
        f"/api/v1/integrations/{integration['id']}/mappings",
        json=integration_mapping_payload(
            source_field="Name", canonical_field="product_name", required=True
        ),
        headers=auth_headers(tokens),
    )

    job = client.post(
        f"/api/v1/integrations/{integration['id']}/sync",
        json={"entity_type": "product", "records": [{"SKU": "REQ-1"}]},
        headers=auth_headers(tokens),
    ).json()["data"]
    _run_worker(db_session, job["id"])

    updated = client.get(
        f"/api/v1/integrations/{integration['id']}/jobs", headers=auth_headers(tokens)
    ).json()["data"][0]
    assert updated["records_failed"] == 1
    assert "required" in updated["error_details"][0]["message"]


def test_mapping_validation_rule_regex_rejects_bad_value(client: TestClient, db_session: Session) -> None:
    tokens = register(client)
    integration = _create_integration(client, tokens)
    client.post(
        f"/api/v1/integrations/{integration['id']}/mappings",
        json=integration_mapping_payload(
            source_field="SKU", canonical_field="sku", validation_rule="regex:^[A-Z0-9-]+$"
        ),
        headers=auth_headers(tokens),
    )
    client.post(
        f"/api/v1/integrations/{integration['id']}/mappings",
        json=integration_mapping_payload(source_field="Name", canonical_field="product_name"),
        headers=auth_headers(tokens),
    )

    job = client.post(
        f"/api/v1/integrations/{integration['id']}/sync",
        json={"entity_type": "product", "records": [{"SKU": "bad sku!", "Name": "Widget"}]},
        headers=auth_headers(tokens),
    ).json()["data"]
    _run_worker(db_session, job["id"])

    updated = client.get(
        f"/api/v1/integrations/{integration['id']}/jobs", headers=auth_headers(tokens)
    ).json()["data"][0]
    assert updated["records_failed"] == 1


# --- Sync / external ID mapping / new entity types ---


def test_order_sync_maps_line_items_via_direct_passthrough(client: TestClient, db_session: Session) -> None:
    tokens = register(client)
    integration = _create_integration(client, tokens)
    client.post(
        f"/api/v1/integrations/{integration['id']}/mappings",
        json=integration_mapping_payload(
            entity_type="order", source_field="order_id", canonical_field="external_id"
        ),
        headers=auth_headers(tokens),
    )
    client.post(
        f"/api/v1/integrations/{integration['id']}/mappings",
        json=integration_mapping_payload(
            entity_type="order", source_field="line_items", canonical_field="lines"
        ),
        headers=auth_headers(tokens),
    )

    job = client.post(
        f"/api/v1/integrations/{integration['id']}/sync",
        json={
            "entity_type": "order",
            "records": [
                {
                    "order_id": "ORD-1",
                    "line_items": [{"sku": "SKU-1", "quantity": "2", "unit_price": "9.99"}],
                }
            ],
        },
        headers=auth_headers(tokens),
    ).json()["data"]
    _run_worker(db_session, job["id"])

    updated = client.get(
        f"/api/v1/integrations/{integration['id']}/jobs", headers=auth_headers(tokens)
    ).json()["data"][0]
    assert updated["status"] == "completed"
    assert updated["records_created"] == 1


def test_promotion_sync_writes_external_promotion_not_pricing_rule(
    client: TestClient, db_session: Session
) -> None:
    tokens = register(client)
    integration = _create_integration(client, tokens)
    client.post(
        f"/api/v1/integrations/{integration['id']}/mappings",
        json=integration_mapping_payload(
            entity_type="promotion", source_field="promo_id", canonical_field="external_id"
        ),
        headers=auth_headers(tokens),
    )
    client.post(
        f"/api/v1/integrations/{integration['id']}/mappings",
        json=integration_mapping_payload(
            entity_type="promotion", source_field="name", canonical_field="name"
        ),
        headers=auth_headers(tokens),
    )

    pricing_rules_before = client.get("/api/v1/pricing/rules", headers=auth_headers(tokens)).json()["data"]

    job = client.post(
        f"/api/v1/integrations/{integration['id']}/sync",
        json={
            "entity_type": "promotion",
            "records": [{"promo_id": "PROMO-1", "name": "10% off"}],
        },
        headers=auth_headers(tokens),
    ).json()["data"]
    _run_worker(db_session, job["id"])

    updated = client.get(
        f"/api/v1/integrations/{integration['id']}/jobs", headers=auth_headers(tokens)
    ).json()["data"][0]
    assert updated["status"] == "completed"
    assert updated["records_created"] == 1

    pricing_rules_after = client.get("/api/v1/pricing/rules", headers=auth_headers(tokens)).json()["data"]
    assert len(pricing_rules_after) == len(pricing_rules_before)


# --- Idempotency / loop prevention ---


def test_apply_price_skips_when_value_unchanged(client: TestClient, db_session: Session) -> None:
    tokens = register(client)
    integration = _create_integration(client, tokens)
    _setup_product_mapping(client, tokens, integration["id"])
    _setup_price_mapping(client, tokens, integration["id"])

    job1 = client.post(
        f"/api/v1/integrations/{integration['id']}/sync",
        json={
            "entity_type": "product",
            "records": [{"SKU": "SKIP-1", "Name": "Widget", "Category": "Gadgets", "Price": "10.00"}],
        },
        headers=auth_headers(tokens),
    ).json()["data"]
    _run_worker(db_session, job1["id"])

    job2 = client.post(
        f"/api/v1/integrations/{integration['id']}/sync",
        json={"entity_type": "price", "records": [{"SKU": "SKIP-1", "Price": "10.00"}]},
        headers=auth_headers(tokens),
    ).json()["data"]
    _run_worker(db_session, job2["id"])

    job3 = client.post(
        f"/api/v1/integrations/{integration['id']}/sync",
        json={"entity_type": "price", "records": [{"SKU": "SKIP-1", "Price": "10.00"}]},
        headers=auth_headers(tokens),
    ).json()["data"]
    _run_worker(db_session, job3["id"])

    jobs = client.get(f"/api/v1/integrations/{integration['id']}/jobs", headers=auth_headers(tokens)).json()[
        "data"
    ]
    last_price_job = next(j for j in jobs if j["id"] == job3["id"])
    assert last_price_job["records_skipped"] == 1
    assert last_price_job["records_created"] == 0


# --- Authority / source-of-truth ---


def test_default_authority_is_external_when_unconfigured(client: TestClient, db_session: Session) -> None:
    tokens = register(client)
    integration = _create_integration(client, tokens)
    _setup_product_mapping(client, tokens, integration["id"])

    job = client.post(
        f"/api/v1/integrations/{integration['id']}/sync",
        json={
            "entity_type": "product",
            "records": [{"SKU": "AUTH-1", "Name": "Widget", "Category": "Gadgets", "Price": "5.00"}],
        },
        headers=auth_headers(tokens),
    ).json()["data"]
    _run_worker(db_session, job["id"])

    updated = client.get(
        f"/api/v1/integrations/{integration['id']}/jobs", headers=auth_headers(tokens)
    ).json()["data"][0]
    assert updated["status"] == "completed"


def test_apply_price_blocked_when_pip_is_authoritative(client: TestClient, db_session: Session) -> None:
    tokens = register(client)
    integration = _create_integration(client, tokens)
    _setup_product_mapping(client, tokens, integration["id"])
    _setup_price_mapping(client, tokens, integration["id"])

    # Seed the product first (price authority doesn't block products).
    seed_job = client.post(
        f"/api/v1/integrations/{integration['id']}/sync",
        json={
            "entity_type": "product",
            "records": [{"SKU": "BLOCK-1", "Name": "Widget", "Category": "Gadgets", "Price": "20.00"}],
        },
        headers=auth_headers(tokens),
    ).json()["data"]
    _run_worker(db_session, seed_job["id"])

    authority_response = client.post(
        f"/api/v1/integrations/{integration['id']}/authorities",
        json=integration_authority_payload(),
        headers=auth_headers(tokens),
    )
    assert authority_response.status_code == 201, authority_response.text

    job = client.post(
        f"/api/v1/integrations/{integration['id']}/sync",
        json={"entity_type": "price", "records": [{"SKU": "BLOCK-1", "Price": "1.00"}]},
        headers=auth_headers(tokens),
    ).json()["data"]
    _run_worker(db_session, job["id"])

    updated = client.get(
        f"/api/v1/integrations/{integration['id']}/jobs", headers=auth_headers(tokens)
    ).json()["data"][0]
    assert updated["records_failed"] == 1
    assert "authority" in updated["error_details"][0]["message"].lower()


def test_apply_price_allowed_with_override_logs_reconciliation(
    client: TestClient, db_session: Session
) -> None:
    tokens = register(client)
    integration = _create_integration(client, tokens)
    _setup_product_mapping(client, tokens, integration["id"])
    _setup_price_mapping(client, tokens, integration["id"])

    seed_job = client.post(
        f"/api/v1/integrations/{integration['id']}/sync",
        json={
            "entity_type": "product",
            "records": [{"SKU": "OVR-1", "Name": "Widget", "Category": "Gadgets", "Price": "20.00"}],
        },
        headers=auth_headers(tokens),
    ).json()["data"]
    _run_worker(db_session, seed_job["id"])

    client.post(
        f"/api/v1/integrations/{integration['id']}/authorities",
        json=integration_authority_payload(allow_override=True),
        headers=auth_headers(tokens),
    )

    job = client.post(
        f"/api/v1/integrations/{integration['id']}/sync",
        json={"entity_type": "price", "records": [{"SKU": "OVR-1", "Price": "1.00"}]},
        headers=auth_headers(tokens),
    ).json()["data"]
    _run_worker(db_session, job["id"])

    updated = client.get(
        f"/api/v1/integrations/{integration['id']}/jobs", headers=auth_headers(tokens)
    ).json()["data"][0]
    assert updated["records_failed"] == 0
    assert updated["records_created"] == 1

    reconciliation = client.get(
        f"/api/v1/integrations/{integration['id']}/reconciliation", headers=auth_headers(tokens)
    ).json()["data"]
    assert len(reconciliation) == 1
    assert reconciliation[0]["status"] == "open"


# --- Reconciliation ---


def test_run_reconciliation_detects_mismatch(client: TestClient, db_session: Session) -> None:
    tokens = register(client)
    integration = _create_integration(client, tokens)
    _setup_product_mapping(client, tokens, integration["id"])
    _setup_price_mapping(client, tokens, integration["id"])

    seed_job = client.post(
        f"/api/v1/integrations/{integration['id']}/sync",
        json={
            "entity_type": "product",
            "records": [{"SKU": "RECON-1", "Name": "Widget", "Category": "Gadgets", "Price": "20.00"}],
        },
        headers=auth_headers(tokens),
    ).json()["data"]
    _run_worker(db_session, seed_job["id"])
    price_job = client.post(
        f"/api/v1/integrations/{integration['id']}/sync",
        json={"entity_type": "price", "records": [{"SKU": "RECON-1", "Price": "20.00"}]},
        headers=auth_headers(tokens),
    ).json()["data"]
    _run_worker(db_session, price_job["id"])

    # PIP's price then diverges from what the integration last synced.
    products_response = client.get(
        "/api/v1/products", params={"search": "RECON-1"}, headers=auth_headers(tokens)
    )
    product = products_response.json()["data"][0]
    client.put(
        f"/api/v1/products/{product['id']}", json={"selling_price": "99.99"}, headers=auth_headers(tokens)
    )
    client.post(
        "/api/v1/pricing",
        json={
            "product_id": product["id"],
            "base_price": "99.99",
            "selling_price": "99.99",
            "currency": "USD",
        },
        headers=auth_headers(tokens),
    )

    response = client.post(
        f"/api/v1/integrations/{integration['id']}/reconcile",
        json={"entity_type": "price"},
        headers=auth_headers(tokens),
    )
    assert response.status_code == 200, response.text
    mismatches = response.json()["data"]
    assert len(mismatches) == 1
    assert mismatches[0]["pip_value"] == "99.9900"
    assert mismatches[0]["external_value"] == "20.0000"


# --- Webhooks ---


def _rotate_secret_url(integration_id: str) -> str:
    return f"/api/v1/integrations/{integration_id}/webhook-secret/rotate"


def test_webhook_receiver_rejects_bad_signature(client: TestClient) -> None:
    tokens = register(client)
    integration = _create_integration(client, tokens)
    client.post(_rotate_secret_url(integration["id"]), headers=auth_headers(tokens))

    response = client.post(
        f"/api/v1/integration-webhooks/{integration['id']}/product",
        content=json.dumps({"id": "evt-1", "sku": "X"}),
        headers={"X-Webhook-Signature": "sha256=deadbeef", "Content-Type": "application/json"},
    )
    assert response.status_code == 401


def test_webhook_receiver_accepts_valid_signature_and_enqueues_job(
    client: TestClient, db_session: Session
) -> None:
    tokens = register(client)
    integration = _create_integration(client, tokens)
    secret = client.post(
        f"/api/v1/integrations/{integration['id']}/webhook-secret/rotate", headers=auth_headers(tokens)
    ).json()["data"]["webhook_secret"]

    body = json.dumps({"id": "evt-100", "SKU": "WH-1", "Name": "Widget"}).encode()
    signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

    response = client.post(
        f"/api/v1/integration-webhooks/{integration['id']}/product",
        content=body,
        headers={"X-Webhook-Signature": signature, "Content-Type": "application/json"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["data"]["status"] == "received"

    events = client.get(
        f"/api/v1/integrations/{integration['id']}/webhook-events", headers=auth_headers(tokens)
    ).json()["data"]
    assert len(events) == 1
    assert events[0]["signature_valid"] is True

    integration_webhook_service.process_webhook_event(uuid.UUID(events[0]["id"]), db=db_session)
    processed = client.get(
        f"/api/v1/integrations/{integration['id']}/webhook-events", headers=auth_headers(tokens)
    ).json()["data"][0]
    assert processed["sync_job_id"] is not None


def test_webhook_duplicate_event_id_is_deduped(client: TestClient) -> None:
    tokens = register(client)
    integration = _create_integration(client, tokens)
    secret = client.post(
        f"/api/v1/integrations/{integration['id']}/webhook-secret/rotate", headers=auth_headers(tokens)
    ).json()["data"]["webhook_secret"]

    body = json.dumps({"id": "evt-dup", "SKU": "WH-2"}).encode()
    signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    headers = {"X-Webhook-Signature": signature, "Content-Type": "application/json"}

    url = f"/api/v1/integration-webhooks/{integration['id']}/product"
    first = client.post(url, content=body, headers=headers)
    second = client.post(url, content=body, headers=headers)

    assert first.json()["data"]["status"] == "received"
    assert second.json()["data"]["status"] == "duplicate"

    events = client.get(
        f"/api/v1/integrations/{integration['id']}/webhook-events", headers=auth_headers(tokens)
    ).json()["data"]
    assert len(events) == 1


# --- Price execution (outbound) ---


def test_push_price_rejected_when_adapter_lacks_write_capability(client: TestClient) -> None:
    tokens = register(client)
    integration = client.post(
        "/api/v1/integrations", json=integration_payload(provider="csv"), headers=auth_headers(tokens)
    ).json()["data"]

    response = client.post(
        f"/api/v1/integrations/{integration['id']}/push",
        json={"price_ids": [str(uuid.uuid4())]},
        headers=auth_headers(tokens),
    )
    assert response.status_code == 422, response.text


def test_push_price_creates_outbound_job_when_adapter_supports_write(client: TestClient) -> None:
    tokens = register(client)
    integration = client.post(
        "/api/v1/integrations",
        json=integration_payload(provider="rest_api", credentials={"base_url": "https://example.com/api"}),
        headers=auth_headers(tokens),
    ).json()["data"]

    response = client.post(
        f"/api/v1/integrations/{integration['id']}/push",
        json={"price_ids": [str(uuid.uuid4())]},
        headers=auth_headers(tokens),
    )
    assert response.status_code == 201, response.text
    assert response.json()["data"]["direction"] == "outbound"
    assert response.json()["data"]["status"] == "pending"


# --- Scheduled sync ---


def test_create_and_update_sync_schedule(client: TestClient) -> None:
    tokens = register(client)
    integration = _create_integration(client, tokens)

    created = client.post(
        f"/api/v1/integrations/{integration['id']}/schedules",
        json=integration_sync_schedule_payload(),
        headers=auth_headers(tokens),
    )
    assert created.status_code == 201, created.text
    schedule = created.json()["data"]
    assert schedule["is_enabled"] is True

    updated = client.put(
        f"/api/v1/integrations/{integration['id']}/schedules/{schedule['id']}",
        json={"is_enabled": False},
        headers=auth_headers(tokens),
    )
    assert updated.json()["data"]["is_enabled"] is False


# --- Tenant isolation ---


def test_locations_not_visible_across_organizations(client: TestClient) -> None:
    tokens_a = register(client, organization_name="Org A", email="a-phase10@example.com")
    integration = _create_integration(client, tokens_a)

    tokens_b = register(client, organization_name="Org B", email="b-phase10@example.com")
    response = client.get(
        f"/api/v1/integrations/{integration['id']}/locations", headers=auth_headers(tokens_b)
    )

    assert response.status_code == 404


def test_reconciliation_not_visible_across_organizations(client: TestClient) -> None:
    tokens_a = register(client, organization_name="Org A2", email="a2-phase10@example.com")
    integration = _create_integration(client, tokens_a)

    tokens_b = register(client, organization_name="Org B2", email="b2-phase10@example.com")
    response = client.post(
        f"/api/v1/integrations/{integration['id']}/reconcile",
        json={"entity_type": "price"},
        headers=auth_headers(tokens_b),
    )

    assert response.status_code == 404


# --- RBAC ---


def test_viewer_cannot_rotate_webhook_secret(client: TestClient, db_session: Session) -> None:
    tokens = register(client)
    integration = _create_integration(client, tokens)
    me = client.get("/api/v1/auth/me", headers=auth_headers(tokens)).json()["data"]
    viewer = add_user_with_role(
        db_session,
        organization_id=uuid.UUID(me["organization"]["id"]),
        email="viewer-phase10@example.com",
        role_name="Viewer",
    )
    viewer_tokens = client.post(
        "/api/v1/auth/login", json={"email": viewer.email, "password": "SuperSecret1"}
    ).json()["data"]

    response = client.post(
        f"/api/v1/integrations/{integration['id']}/webhook-secret/rotate", headers=auth_headers(viewer_tokens)
    )
    assert response.status_code == 403


# --- Stub honesty ---


def test_shopify_stub_fails_honestly_but_reports_webhook_capability(client: TestClient) -> None:
    tokens = register(client)
    integration = client.post(
        "/api/v1/integrations",
        json=integration_payload(provider="shopify", integration_category="ecommerce"),
        headers=auth_headers(tokens),
    ).json()["data"]

    assert integration["capabilities"]["supports_webhooks"] is True
    assert integration["capabilities"]["supports_product_write"] is True

    response = client.post(f"/api/v1/integrations/{integration['id']}/test", headers=auth_headers(tokens))
    data = response.json()["data"]
    assert data["success"] is False
    assert "Shopify" in data["message"]
    assert "not available" in data["message"]
