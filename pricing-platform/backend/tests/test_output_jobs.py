import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.services import output_job_service
from tests.helpers import (
    auth_headers,
    category_payload,
    output_channel_payload,
    output_job_payload,
    product_payload,
    register,
)


def _run_worker(db_session: Session, job_id: str) -> None:
    """Simulates the Celery worker synchronously, in the same test DB —
    no Redis/Celery worker needed to exercise the real processing logic.
    """
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


def test_create_job_starts_pending(client: TestClient) -> None:
    tokens = register(client)
    product = _setup_product(client, tokens)
    channel = _setup_channel(client, tokens)

    response = client.post(
        "/api/v1/outputs/jobs",
        json=output_job_payload(output_channel_id=channel["id"], product_id=product["id"]),
        headers=auth_headers(tokens),
    )

    assert response.status_code == 201, response.text
    data = response.json()["data"]
    assert data["status"] == "pending"
    assert data["attempts"] == 0


def test_create_job_rejects_inactive_channel(client: TestClient) -> None:
    tokens = register(client)
    product = _setup_product(client, tokens)
    channel = _setup_channel(client, tokens)
    client.put(
        f"/api/v1/outputs/channels/{channel['id']}", json={"status": "inactive"}, headers=auth_headers(tokens)
    )

    response = client.post(
        "/api/v1/outputs/jobs",
        json=output_job_payload(output_channel_id=channel["id"], product_id=product["id"]),
        headers=auth_headers(tokens),
    )

    assert response.status_code == 409


def test_esl_simulator_job_completes_with_rendered_payload(client: TestClient, db_session: Session) -> None:
    tokens = register(client)
    product = _setup_product(client, tokens, selling_price="49.9900")
    channel = _setup_channel(client, tokens, output_type="esl_simulator")

    job = client.post(
        "/api/v1/outputs/jobs",
        json=output_job_payload(output_channel_id=channel["id"], product_id=product["id"]),
        headers=auth_headers(tokens),
    ).json()["data"]
    _run_worker(db_session, job["id"])

    response = client.get(f"/api/v1/outputs/jobs/{job['id']}", headers=auth_headers(tokens))
    data = response.json()["data"]
    assert data["status"] == "completed"
    assert data["attempts"] == 1
    assert data["payload"]["product_name"] == "Wireless Mouse"
    assert data["payload"]["price"] == "49.9900"
    assert data["completed_at"] is not None


def test_qr_code_job_generates_image(client: TestClient, db_session: Session) -> None:
    tokens = register(client)
    product = _setup_product(client, tokens)
    channel = _setup_channel(client, tokens, name="QR", output_type="qr_code")

    job = client.post(
        "/api/v1/outputs/jobs",
        json=output_job_payload(output_channel_id=channel["id"], product_id=product["id"]),
        headers=auth_headers(tokens),
    ).json()["data"]
    _run_worker(db_session, job["id"])

    data = client.get(f"/api/v1/outputs/jobs/{job['id']}", headers=auth_headers(tokens)).json()["data"]
    assert data["status"] == "completed"
    assert data["payload"]["qr_image_mime"] == "image/png"
    assert len(data["payload"]["qr_image_base64"]) > 100
    # The QR encodes the product's product_url when set; the test product has none, so it's empty.
    assert data["payload"]["qr_text"] == ""


def test_pdf_label_job_generates_pdf(client: TestClient, db_session: Session) -> None:
    """Default config: QR right, banner bottom, unit price shown."""
    tokens = register(client)
    product = _setup_product(
        client, tokens, selling_price="49.9900", shelf_id="39", product_url="https://example.com/item/1"
    )
    channel = _setup_channel(client, tokens, name="PDF", output_type="pdf_label")

    job = client.post(
        "/api/v1/outputs/jobs",
        json=output_job_payload(output_channel_id=channel["id"], product_id=product["id"]),
        headers=auth_headers(tokens),
    ).json()["data"]
    _run_worker(db_session, job["id"])

    data = client.get(f"/api/v1/outputs/jobs/{job['id']}", headers=auth_headers(tokens)).json()["data"]
    assert data["status"] == "completed"
    payload = data["payload"]
    assert payload["pdf_mime"] == "application/pdf"
    assert len(payload["pdf_base64"]) > 100
    assert payload["product_name"] == "Wireless Mouse"
    assert payload["sku"] == product["sku"]
    assert payload["price"] == "49.99"
    assert payload["shelf_id"] == "39"
    assert payload["unit_suffix"] == "PER EA"

    # A valid QR PNG was embedded and drawn without error
    assert len(payload["pdf_base64"]) > 0


def test_pdf_label_custom_format(client: TestClient, db_session: Session) -> None:
    """Non-default config: QR left, banner top, smaller QR; weight-derived unit price."""
    tokens = register(client)
    product = _setup_product(
        client,
        tokens,
        selling_price="6.4800",
        shelf_id="12",
        product_url="https://example.com/juice",
        weight="2.0000",
        weight_unit="qt",
    )
    channel = _setup_channel(
        client,
        tokens,
        name="PDF Custom",
        output_type="pdf_label",
        configuration={
            "show_qr": True,
            "qr_position": "left",
            "qr_size_mm": 16,
            "show_unit_price": True,
            "banner_position": "top",
            "label_width_mm": 90,
            "label_height_mm": 60,
        },
    )

    job = client.post(
        "/api/v1/outputs/jobs",
        json=output_job_payload(output_channel_id=channel["id"], product_id=product["id"]),
        headers=auth_headers(tokens),
    ).json()["data"]
    _run_worker(db_session, job["id"])

    data = client.get(f"/api/v1/outputs/jobs/{job['id']}", headers=auth_headers(tokens)).json()["data"]
    assert data["status"] == "completed"
    payload = data["payload"]
    assert payload["pdf_mime"] == "application/pdf"
    assert len(payload["pdf_base64"]) > 100
    # 6.48 / 2 qt = 3.24 per qt
    assert payload["unit_price"] == "3.24"
    assert payload["unit_suffix"] == "PER QT"
    assert payload["shelf_id"] == "12"


def test_pdf_label_without_qr_or_unit_price(client: TestClient, db_session: Session) -> None:
    """Both optional elements disabled — text-only label still renders."""
    tokens = register(client)
    product = _setup_product(client, tokens)
    channel = _setup_channel(
        client,
        tokens,
        name="PDF Text",
        output_type="pdf_label",
        configuration={"show_qr": False, "show_unit_price": False},
    )

    job = client.post(
        "/api/v1/outputs/jobs",
        json=output_job_payload(output_channel_id=channel["id"], product_id=product["id"]),
        headers=auth_headers(tokens),
    ).json()["data"]
    _run_worker(db_session, job["id"])

    data = client.get(f"/api/v1/outputs/jobs/{job['id']}", headers=auth_headers(tokens)).json()["data"]
    assert data["status"] == "completed"
    assert data["payload"]["pdf_mime"] == "application/pdf"
    assert len(data["payload"]["pdf_base64"]) > 100


def test_web_display_job_completes(client: TestClient, db_session: Session) -> None:
    tokens = register(client)
    product = _setup_product(client, tokens)
    channel = _setup_channel(client, tokens, name="Web", output_type="web_display")

    job = client.post(
        "/api/v1/outputs/jobs",
        json=output_job_payload(output_channel_id=channel["id"], product_id=product["id"]),
        headers=auth_headers(tokens),
    ).json()["data"]
    _run_worker(db_session, job["id"])

    data = client.get(f"/api/v1/outputs/jobs/{job['id']}", headers=auth_headers(tokens)).json()["data"]
    assert data["status"] == "completed"
    assert data["payload"]["published"] is True


def test_job_fails_when_product_deleted_before_processing(client: TestClient, db_session: Session) -> None:
    tokens = register(client)
    product = _setup_product(client, tokens)
    channel = _setup_channel(client, tokens)
    job = client.post(
        "/api/v1/outputs/jobs",
        json=output_job_payload(output_channel_id=channel["id"], product_id=product["id"]),
        headers=auth_headers(tokens),
    ).json()["data"]

    client.delete(f"/api/v1/products/{product['id']}", headers=auth_headers(tokens))
    _run_worker(db_session, job["id"])

    data = client.get(f"/api/v1/outputs/jobs/{job['id']}", headers=auth_headers(tokens)).json()["data"]
    assert data["status"] == "failed"
    assert data["last_error"]


def test_retry_reprocesses_failed_job(client: TestClient, db_session: Session) -> None:
    tokens = register(client)
    product = _setup_product(client, tokens)
    channel = _setup_channel(client, tokens)
    job = client.post(
        "/api/v1/outputs/jobs",
        json=output_job_payload(output_channel_id=channel["id"], product_id=product["id"]),
        headers=auth_headers(tokens),
    ).json()["data"]
    client.delete(f"/api/v1/products/{product['id']}", headers=auth_headers(tokens))
    _run_worker(db_session, job["id"])
    assert client.get(f"/api/v1/outputs/jobs/{job['id']}", headers=auth_headers(tokens)).json()["data"][
        "status"
    ] == "failed"

    # Recreate isn't possible (product stays deleted); retry should still
    # transition back to pending and fail again cleanly rather than error.
    retry_response = client.post(
        f"/api/v1/outputs/jobs/{job['id']}/retry", headers=auth_headers(tokens)
    )
    assert retry_response.status_code == 200
    assert retry_response.json()["data"]["status"] == "pending"
    assert retry_response.json()["data"]["last_error"] is None

    _run_worker(db_session, job["id"])
    data = client.get(f"/api/v1/outputs/jobs/{job['id']}", headers=auth_headers(tokens)).json()["data"]
    assert data["status"] == "failed"
    assert data["attempts"] == 2


def test_retry_rejects_pending_job(client: TestClient) -> None:
    tokens = register(client)
    product = _setup_product(client, tokens)
    channel = _setup_channel(client, tokens)
    job = client.post(
        "/api/v1/outputs/jobs",
        json=output_job_payload(output_channel_id=channel["id"], product_id=product["id"]),
        headers=auth_headers(tokens),
    ).json()["data"]

    response = client.post(f"/api/v1/outputs/jobs/{job['id']}/retry", headers=auth_headers(tokens))

    assert response.status_code == 409


def test_create_jobs_bulk_single_product(client: TestClient, db_session: Session) -> None:
    """Creating one job per product in a bulk request works the same as single."""
    tokens = register(client)
    product1 = _setup_product(client, tokens)
    channel = _setup_channel(client, tokens)

    response = client.post(
        "/api/v1/outputs/jobs/bulk",
        json={"output_channel_id": channel["id"], "product_ids": [product1["id"]]},
        headers=auth_headers(tokens),
    )

    assert response.status_code == 201, response.text
    data = response.json()["data"]
    assert len(data) == 1
    job = data[0]
    assert job["status"] == "pending"
    assert job["product_id"] == product1["id"]
    _run_worker(db_session, job["id"])
    completed = client.get(f"/api/v1/outputs/jobs/{job['id']}", headers=auth_headers(tokens)).json()["data"]
    assert completed["status"] == "completed"


def test_create_jobs_bulk_multiple_products(client: TestClient, db_session: Session) -> None:
    """Creating multiple jobs in one bulk request produces one job per product."""
    tokens = register(client)
    product1 = _setup_product(client, tokens)
    product2 = _setup_product(client, tokens, selling_price="19.9900")
    channel = _setup_channel(client, tokens)

    response = client.post(
        "/api/v1/outputs/jobs/bulk",
        json={"output_channel_id": channel["id"], "product_ids": [product1["id"], product2["id"]]},
        headers=auth_headers(tokens),
    )

    assert response.status_code == 201, response.text
    data = response.json()["data"]
    assert len(data) == 2
    job_ids = {j["product_id"] for j in data}
    assert product1["id"] in job_ids
    assert product2["id"] in job_ids

    # Run both workers synchronously
    for job_data in data:
        _run_worker(db_session, job_data["id"])
    completed = client.get(f"/api/v1/outputs/jobs/{data[0]['id']}", headers=auth_headers(tokens)).json()["data"]
    assert completed["status"] == "completed"
    completed2 = client.get(f"/api/v1/outputs/jobs/{data[1]['id']}", headers=auth_headers(tokens)).json()["data"]
    assert completed2["status"] == "completed"
    assert completed["product_name"] == completed2["product_name"]


def test_create_jobs_bulk_rejects_missing_product(client: TestClient) -> None:
    """Bulk create rejects with 404 if any product_id is invalid."""
    tokens = register(client)
    product = _setup_product(client, tokens)
    channel = _setup_channel(client, tokens)

    response = client.post(
        "/api/v1/outputs/jobs/bulk",
        json={"output_channel_id": channel["id"], "product_ids": [product["id"], uuid.uuid4()]},
        headers=auth_headers(tokens),
    )

    assert response.status_code == 404, response.text


def test_list_jobs_filters_by_status(client: TestClient, db_session: Session) -> None:
    tokens = register(client)
    product = _setup_product(client, tokens)
    channel = _setup_channel(client, tokens)
    job = client.post(
        "/api/v1/outputs/jobs",
        json=output_job_payload(output_channel_id=channel["id"], product_id=product["id"]),
        headers=auth_headers(tokens),
    ).json()["data"]
    _run_worker(db_session, job["id"])

    response = client.get(
        "/api/v1/outputs/jobs", params={"status": "completed"}, headers=auth_headers(tokens)
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["id"] == job["id"]


def test_public_price_display(client: TestClient) -> None:
    tokens = register(client)
    product = _setup_product(client, tokens, selling_price="29.9900")

    response = client.get(f"/api/v1/public/price/{product['id']}")

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["product_name"] == "Wireless Mouse"
    assert data["sku"] == product["sku"]
    assert data["price"] == "29.9900"


def test_public_price_display_unknown_product_404s(client: TestClient) -> None:
    response = client.get(f"/api/v1/public/price/{uuid.uuid4()}")

    assert response.status_code == 404
