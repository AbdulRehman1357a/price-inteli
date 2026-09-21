import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.repositories.price_repository import PriceRepository
from app.repositories.product_repository import ProductRepository
from app.services import output_job_service, output_router_service
from tests.helpers import (
    auth_headers,
    category_payload,
    output_channel_payload,
    output_job_payload,
    output_routing_rule_payload,
    price_payload,
    product_payload,
    register,
)


def _run_worker(db_session: Session, job_id: str) -> None:
    output_job_service.process_output_job(uuid.UUID(job_id), db=db_session)


def _setup_product(client: TestClient, tokens: dict, **overrides) -> dict:
    category = client.post(
        "/api/v1/categories", json=category_payload(), headers=auth_headers(tokens)
    ).json()["data"]
    return client.post(
        "/api/v1/products",
        json=product_payload(category_id=category["id"], **overrides),
        headers=auth_headers(tokens),
    ).json()["data"]


def _setup_channel(client: TestClient, tokens: dict, **overrides) -> dict:
    return client.post(
        "/api/v1/outputs/channels", json=output_channel_payload(**overrides), headers=auth_headers(tokens)
    ).json()["data"]


def _create_rule(client: TestClient, tokens: dict, **overrides) -> dict:
    response = client.post(
        "/api/v1/outputs/routing-rules",
        json=output_routing_rule_payload(**overrides),
        headers=auth_headers(tokens),
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]


def test_create_routing_rule_success(client: TestClient) -> None:
    tokens = register(client)

    response = client.post(
        "/api/v1/outputs/routing-rules", json=output_routing_rule_payload(), headers=auth_headers(tokens)
    )

    assert response.status_code == 201, response.text
    data = response.json()["data"]
    assert data["target_outputs_json"] == ["esl_simulator", "qr_code"]
    assert data["status"] == "active"


def test_price_change_matching_rule_creates_output_jobs(client: TestClient, db_session: Session) -> None:
    tokens = register(client)
    product = _setup_product(client, tokens)
    esl = _setup_channel(client, tokens, name="ESL", output_type="esl_simulator")
    qr = _setup_channel(client, tokens, name="QR", output_type="qr_code")
    _create_rule(client, tokens, target_outputs_json=["esl_simulator", "qr_code"])

    response = client.post(
        "/api/v1/pricing", json=price_payload(product_id=product["id"]), headers=auth_headers(tokens)
    )
    assert response.status_code == 201, response.text

    jobs = client.get("/api/v1/outputs/jobs", headers=auth_headers(tokens)).json()["data"]
    channel_ids = {j["output_channel_id"] for j in jobs}
    assert channel_ids == {esl["id"], qr["id"]}
    for job in jobs:
        assert job["idempotency_key"] is not None
        assert job["source_price_id"] is not None
        assert job["routing_rule_id"] is not None


def test_price_change_not_matching_rule_creates_no_jobs(client: TestClient) -> None:
    tokens = register(client)
    product = _setup_product(client, tokens)
    _setup_channel(client, tokens, name="ESL", output_type="esl_simulator")
    other_category = client.post(
        "/api/v1/categories", json=category_payload(name="Other"), headers=auth_headers(tokens)
    ).json()["data"]
    _create_rule(client, tokens, conditions_json={"category_ids": [other_category["id"]]})

    client.post(
        "/api/v1/pricing", json=price_payload(product_id=product["id"]), headers=auth_headers(tokens)
    )

    jobs = client.get("/api/v1/outputs/jobs", headers=auth_headers(tokens)).json()["data"]
    assert jobs == []


def test_routing_is_idempotent_for_the_same_price(client: TestClient, db_session: Session) -> None:
    tokens = register(client)
    product = _setup_product(client, tokens)
    _setup_channel(client, tokens, name="ESL", output_type="esl_simulator")
    _create_rule(client, tokens, target_outputs_json=["esl_simulator"])

    price = client.post(
        "/api/v1/pricing", json=price_payload(product_id=product["id"]), headers=auth_headers(tokens)
    ).json()["data"]

    jobs_after_create = client.get("/api/v1/outputs/jobs", headers=auth_headers(tokens)).json()["data"]
    assert len(jobs_after_create) == 1

    price_row = PriceRepository(db_session).get_by_id(uuid.UUID(price["id"]))
    product_row = ProductRepository(db_session).get_by_id(uuid.UUID(product["id"]))
    created_again = output_router_service.route_price_change(
        db_session,
        organization_id=price_row.organization_id,
        product=product_row,
        store_id=price_row.store_id,
        price=price_row,
    )

    assert created_again == []
    jobs_after_replay = client.get("/api/v1/outputs/jobs", headers=auth_headers(tokens)).json()["data"]
    assert len(jobs_after_replay) == 1


def test_pos_ecommerce_signage_jobs_complete(client: TestClient, db_session: Session) -> None:
    tokens = register(client)
    product = _setup_product(client, tokens)

    for name, output_type in (
        ("POS", "pos_integration"),
        ("Ecom", "ecommerce_integration"),
        ("Signage", "digital_signage"),
    ):
        channel = _setup_channel(client, tokens, name=name, output_type=output_type)
        job = client.post(
            "/api/v1/outputs/jobs",
            json=output_job_payload(output_channel_id=channel["id"], product_id=product["id"]),
            headers=auth_headers(tokens),
        ).json()["data"]
        _run_worker(db_session, job["id"])

        data = client.get(f"/api/v1/outputs/jobs/{job['id']}", headers=auth_headers(tokens)).json()["data"]
        assert data["status"] == "completed", data
        assert data["payload"]["product_name"] == "Wireless Mouse"


def test_cancel_only_allowed_from_pending(client: TestClient, db_session: Session) -> None:
    tokens = register(client)
    product = _setup_product(client, tokens)
    channel = _setup_channel(client, tokens)
    job = client.post(
        "/api/v1/outputs/jobs",
        json=output_job_payload(output_channel_id=channel["id"], product_id=product["id"]),
        headers=auth_headers(tokens),
    ).json()["data"]

    response = client.post(f"/api/v1/outputs/jobs/{job['id']}/cancel", headers=auth_headers(tokens))
    assert response.status_code == 200, response.text
    assert response.json()["data"]["status"] == "cancelled"

    second_attempt = client.post(f"/api/v1/outputs/jobs/{job['id']}/cancel", headers=auth_headers(tokens))
    assert second_attempt.status_code == 409


def test_dashboard_summary_counts(client: TestClient, db_session: Session) -> None:
    tokens = register(client)
    product = _setup_product(client, tokens)
    channel = _setup_channel(client, tokens)

    completed_job = client.post(
        "/api/v1/outputs/jobs",
        json=output_job_payload(output_channel_id=channel["id"], product_id=product["id"]),
        headers=auth_headers(tokens),
    ).json()["data"]
    _run_worker(db_session, completed_job["id"])

    pending_job = client.post(
        "/api/v1/outputs/jobs",
        json=output_job_payload(output_channel_id=channel["id"], product_id=product["id"]),
        headers=auth_headers(tokens),
    ).json()["data"]

    response = client.get("/api/v1/outputs/jobs/summary", headers=auth_headers(tokens))
    assert response.status_code == 200, response.text
    summary = response.json()["data"]
    assert summary["total"] == 2
    assert summary["successful"] == 1
    assert summary["pending"] == 1
    assert summary["failed"] == 0
    del pending_job


def test_routing_rules_are_tenant_isolated(client: TestClient) -> None:
    tokens_a = register(client, organization_name="Org A", email="a@example.com")
    tokens_b = register(client, organization_name="Org B", email="b@example.com")
    rule = _create_rule(client, tokens_a)

    response = client.get(f"/api/v1/outputs/routing-rules/{rule['id']}", headers=auth_headers(tokens_b))

    assert response.status_code == 404
