import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.services import integration_sync_service
from tests.helpers import (
    add_user_with_role,
    auth_headers,
    integration_mapping_payload,
    integration_payload,
    register,
)


def _run_worker(db_session: Session, job_id: str) -> None:
    """Simulates the Celery worker synchronously, in the same test DB — no
    Redis/Celery worker needed to exercise the real processing logic.
    """
    integration_sync_service.process_sync_job(uuid.UUID(job_id), db=db_session)


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


def test_create_integration_starts_pending_and_hides_credentials(client: TestClient) -> None:
    tokens = register(client)

    response = client.post(
        "/api/v1/integrations",
        json=integration_payload(provider="webhook", credentials={"webhook_url": "https://example.com/hook"}),
        headers=auth_headers(tokens),
    )

    assert response.status_code == 201, response.text
    data = response.json()["data"]
    assert data["status"] == "pending"
    assert "credentials" not in data
    assert "configuration_encrypted" not in data


def test_test_connection_for_webhook(client: TestClient) -> None:
    tokens = register(client)
    integration = client.post(
        "/api/v1/integrations",
        json=integration_payload(provider="webhook", credentials={"webhook_url": "https://example.com/hook"}),
        headers=auth_headers(tokens),
    ).json()["data"]

    response = client.post(f"/api/v1/integrations/{integration['id']}/test", headers=auth_headers(tokens))

    assert response.status_code == 200, response.text
    assert response.json()["data"]["success"] is True
    refreshed = client.get(f"/api/v1/integrations/{integration['id']}", headers=auth_headers(tokens))
    assert refreshed.json()["data"]["status"] == "active"


def test_test_connection_fails_without_webhook_url(client: TestClient) -> None:
    tokens = register(client)
    integration = client.post(
        "/api/v1/integrations",
        json=integration_payload(provider="webhook"),
        headers=auth_headers(tokens),
    ).json()["data"]

    response = client.post(f"/api/v1/integrations/{integration['id']}/test", headers=auth_headers(tokens))

    assert response.json()["data"]["success"] is False
    refreshed = client.get(f"/api/v1/integrations/{integration['id']}", headers=auth_headers(tokens))
    assert refreshed.json()["data"]["status"] == "error"


def test_full_sync_creates_product_via_canonical_mapping(client: TestClient, db_session: Session) -> None:
    tokens = register(client)
    integration = client.post(
        "/api/v1/integrations",
        json=integration_payload(provider="webhook", credentials={"webhook_url": "https://example.com/hook"}),
        headers=auth_headers(tokens),
    ).json()["data"]
    _setup_product_mapping(client, tokens, integration["id"])

    job = client.post(
        f"/api/v1/integrations/{integration['id']}/sync",
        json={
            "entity_type": "product",
            "job_type": "full_sync",
            "records": [
                {"SKU": "EXT-001", "Name": "External Widget", "Category": "Gadgets", "Price": "29.99"}
            ],
        },
        headers=auth_headers(tokens),
    ).json()["data"]
    assert job["status"] == "pending"

    _run_worker(db_session, job["id"])

    updated_job = client.get(
        f"/api/v1/integrations/{integration['id']}/jobs", headers=auth_headers(tokens)
    ).json()["data"][0]
    assert updated_job["status"] == "completed"
    assert updated_job["records_processed"] == 1
    assert updated_job["records_failed"] == 0

    product = client.get(
        "/api/v1/products", params={"search": "EXT-001"}, headers=auth_headers(tokens)
    ).json()["data"]
    assert len(product) == 1
    assert product[0]["product_name"] == "External Widget"

    integration_after = client.get(f"/api/v1/integrations/{integration['id']}", headers=auth_headers(tokens))
    assert integration_after.json()["data"]["last_sync_at"] is not None


def test_sync_records_partial_failures(client: TestClient, db_session: Session) -> None:
    tokens = register(client)
    integration = client.post(
        "/api/v1/integrations",
        json=integration_payload(provider="webhook", credentials={"webhook_url": "https://example.com/hook"}),
        headers=auth_headers(tokens),
    ).json()["data"]
    _setup_product_mapping(client, tokens, integration["id"])

    job = client.post(
        f"/api/v1/integrations/{integration['id']}/sync",
        json={
            "entity_type": "product",
            "records": [
                {"SKU": "OK-001", "Name": "Good Widget", "Category": "Gadgets", "Price": "10.00"},
                {"SKU": "BAD-001", "Name": "No Category Widget", "Category": "", "Price": "10.00"},
            ],
        },
        headers=auth_headers(tokens),
    ).json()["data"]

    _run_worker(db_session, job["id"])

    jobs = client.get(
        f"/api/v1/integrations/{integration['id']}/jobs", headers=auth_headers(tokens)
    ).json()["data"]
    assert jobs[0]["status"] == "completed_with_errors"
    assert jobs[0]["records_processed"] == 1
    assert jobs[0]["records_failed"] == 1
    assert len(jobs[0]["error_details"]) == 1


def test_retry_reprocesses_failed_job(client: TestClient, db_session: Session) -> None:
    tokens = register(client)
    integration = client.post(
        "/api/v1/integrations",
        json=integration_payload(provider="webhook", credentials={"webhook_url": "https://example.com/hook"}),
        headers=auth_headers(tokens),
    ).json()["data"]
    # No mappings configured at all -> every record fails.
    job = client.post(
        f"/api/v1/integrations/{integration['id']}/sync",
        json={"entity_type": "product", "records": [{"SKU": "X-1", "Name": "Widget"}]},
        headers=auth_headers(tokens),
    ).json()["data"]
    _run_worker(db_session, job["id"])
    failed = client.get(
        f"/api/v1/integrations/{integration['id']}/jobs", headers=auth_headers(tokens)
    ).json()["data"][0]
    assert failed["status"] == "completed_with_errors"

    retry_response = client.post(
        f"/api/v1/integrations/{integration['id']}/jobs/{job['id']}/retry",
        headers=auth_headers(tokens),
    )
    assert retry_response.status_code == 200, retry_response.text
    assert retry_response.json()["data"]["status"] == "pending"
    assert retry_response.json()["data"]["records_failed"] == 0


def test_retry_rejects_pending_job(client: TestClient) -> None:
    tokens = register(client)
    integration = client.post(
        "/api/v1/integrations",
        json=integration_payload(provider="webhook"),
        headers=auth_headers(tokens),
    ).json()["data"]
    job = client.post(
        f"/api/v1/integrations/{integration['id']}/sync",
        json={"entity_type": "product", "records": []},
        headers=auth_headers(tokens),
    ).json()["data"]

    response = client.post(
        f"/api/v1/integrations/{integration['id']}/jobs/{job['id']}/retry", headers=auth_headers(tokens)
    )

    assert response.status_code == 409


def test_sap_stub_fails_honestly(client: TestClient) -> None:
    tokens = register(client)
    integration = client.post(
        "/api/v1/integrations",
        json=integration_payload(provider="sap", integration_category="erp"),
        headers=auth_headers(tokens),
    ).json()["data"]

    response = client.post(f"/api/v1/integrations/{integration['id']}/test", headers=auth_headers(tokens))

    data = response.json()["data"]
    assert data["success"] is False
    assert "SAP" in data["message"]
    assert "not available" in data["message"]


def test_delete_mapping(client: TestClient) -> None:
    tokens = register(client)
    integration = client.post(
        "/api/v1/integrations",
        json=integration_payload(provider="webhook"),
        headers=auth_headers(tokens),
    ).json()["data"]
    mapping = client.post(
        f"/api/v1/integrations/{integration['id']}/mappings",
        json=integration_mapping_payload(),
        headers=auth_headers(tokens),
    ).json()["data"]

    response = client.delete(
        f"/api/v1/integrations/{integration['id']}/mappings/{mapping['id']}", headers=auth_headers(tokens)
    )
    assert response.status_code == 200, response.text

    remaining = client.get(
        f"/api/v1/integrations/{integration['id']}/mappings", headers=auth_headers(tokens)
    ).json()["data"]
    assert remaining == []


def test_integration_not_visible_across_organizations(client: TestClient) -> None:
    tokens_a = register(client, organization_name="Org A", email="a@example.com")
    integration = client.post(
        "/api/v1/integrations",
        json=integration_payload(provider="webhook"),
        headers=auth_headers(tokens_a),
    ).json()["data"]

    tokens_b = register(client, organization_name="Org B", email="b@example.com")
    response = client.get(f"/api/v1/integrations/{integration['id']}", headers=auth_headers(tokens_b))

    assert response.status_code == 404


def test_csv_adapter_reads_real_file(client: TestClient, db_session: Session, tmp_path) -> None:
    csv_file = tmp_path / "products.csv"
    csv_file.write_text("SKU,Name,Category,Price\nCSV-001,CSV Widget,Gadgets,15.50\n", encoding="utf-8")

    tokens = register(client)
    integration = client.post(
        "/api/v1/integrations",
        json=integration_payload(provider="csv", credentials={"base_url": str(csv_file)}),
        headers=auth_headers(tokens),
    ).json()["data"]
    _setup_product_mapping(client, tokens, integration["id"])

    test_response = client.post(
        f"/api/v1/integrations/{integration['id']}/test", headers=auth_headers(tokens)
    )
    assert test_response.json()["data"]["success"] is True

    job = client.post(
        f"/api/v1/integrations/{integration['id']}/sync",
        json={"entity_type": "product"},
        headers=auth_headers(tokens),
    ).json()["data"]
    _run_worker(db_session, job["id"])

    jobs = client.get(
        f"/api/v1/integrations/{integration['id']}/jobs", headers=auth_headers(tokens)
    ).json()["data"]
    assert jobs[0]["status"] == "completed"
    assert jobs[0]["records_processed"] == 1

    product = client.get(
        "/api/v1/products", params={"search": "CSV-001"}, headers=auth_headers(tokens)
    ).json()["data"]
    assert product[0]["product_name"] == "CSV Widget"


def test_viewer_cannot_create_integration(client: TestClient, db_session) -> None:
    tokens = register(client)
    me = client.get("/api/v1/auth/me", headers=auth_headers(tokens)).json()["data"]
    viewer = add_user_with_role(
        db_session,
        organization_id=uuid.UUID(me["organization"]["id"]),
        email="viewer@example.com",
        role_name="Viewer",
    )
    viewer_tokens = client.post(
        "/api/v1/auth/login", json={"email": viewer.email, "password": "SuperSecret1"}
    ).json()["data"]

    response = client.post(
        "/api/v1/integrations",
        json=integration_payload(provider="webhook"),
        headers=auth_headers(viewer_tokens),
    )

    assert response.status_code == 403
