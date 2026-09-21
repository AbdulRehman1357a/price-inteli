import uuid
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.services import import_service
from tests.helpers import (
    add_user_with_role,
    auth_headers,
    build_csv,
    category_payload,
    register,
    store_payload,
    upload_import,
)


def _run_worker(db_session: Session, job_id: str) -> None:
    """Simulates the Celery worker synchronously, in the same test DB —
    no Redis/Celery worker needed to exercise the real processing logic.
    """
    import_service.process_import_job(uuid.UUID(job_id), db=db_session)


def test_upload_detects_columns(client: TestClient) -> None:
    tokens = register(client)
    content = build_csv([{"SKU Code": "A-1", "Name": "Widget", "Cat": "Electronics", "Price": "9.99"}])

    job = upload_import(client, tokens, content=content)

    assert job["status"] == "uploaded"
    assert job["file_type"] == "csv"
    assert job["detected_columns"] == ["SKU Code", "Name", "Cat", "Price"]
    assert job["entity_type"] == "products"


def test_upload_rejects_unsupported_file_type(client: TestClient) -> None:
    tokens = register(client)

    response = client.post(
        "/api/v1/imports",
        files={"file": ("products.txt", b"whatever", "text/plain")},
        data={"entity_type": "products"},
        headers=auth_headers(tokens),
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_start_import_rejects_unmapped_column(client: TestClient) -> None:
    tokens = register(client)
    content = build_csv([{"SKU Code": "A-1", "Name": "Widget", "Cat": "Electronics", "Price": "9.99"}])
    job = upload_import(client, tokens, content=content)

    response = client.post(
        f"/api/v1/imports/{job['id']}/start",
        json={"mapping": {"sku": "Does Not Exist"}},
        headers=auth_headers(tokens),
    )

    assert response.status_code == 422


def test_start_import_rejects_missing_required_mapping(client: TestClient) -> None:
    tokens = register(client)
    content = build_csv([{"SKU Code": "A-1", "Name": "Widget", "Cat": "Electronics", "Price": "9.99"}])
    job = upload_import(client, tokens, content=content)

    response = client.post(
        f"/api/v1/imports/{job['id']}/start",
        json={"mapping": {"sku": "SKU Code"}},  # missing product_name/category/selling_price
        headers=auth_headers(tokens),
    )

    assert response.status_code == 422


def test_start_import_twice_conflicts(client: TestClient) -> None:
    tokens = register(client)
    content = build_csv([{"SKU Code": "A-1", "Name": "Widget", "Cat": "Electronics", "Price": "9.99"}])
    job = upload_import(client, tokens, content=content)
    mapping = {
        "mapping": {
            "sku": "SKU Code",
            "product_name": "Name",
            "category": "Cat",
            "selling_price": "Price",
        }
    }
    first = client.post(f"/api/v1/imports/{job['id']}/start", json=mapping, headers=auth_headers(tokens))
    assert first.status_code == 200

    second = client.post(f"/api/v1/imports/{job['id']}/start", json=mapping, headers=auth_headers(tokens))

    assert second.status_code == 409
    assert second.json()["error"]["code"] == "import_already_started"


def test_products_import_creates_and_updates_products(client: TestClient, db_session: Session) -> None:
    tokens = register(client)
    client.post("/api/v1/categories", json=category_payload(name="Electronics"), headers=auth_headers(tokens))
    client.post("/api/v1/categories", json=category_payload(name="Books"), headers=auth_headers(tokens))

    content = build_csv(
        [
            {"SKU Code": "A-1", "Name": "Widget", "Cat": "Electronics", "Price": "9.99"},
            {"SKU Code": "B-1", "Name": "Novel", "Cat": "Books", "Price": "14.50"},
        ]
    )
    job = upload_import(client, tokens, content=content)
    client.post(
        f"/api/v1/imports/{job['id']}/start",
        json={
            "mapping": {
                "sku": "SKU Code",
                "product_name": "Name",
                "category": "Cat",
                "selling_price": "Price",
            }
        },
        headers=auth_headers(tokens),
    )

    _run_worker(db_session, job["id"])

    result = client.get(f"/api/v1/imports/{job['id']}", headers=auth_headers(tokens)).json()["data"]
    assert result["status"] == "completed"
    assert result["success_rows"] == 2
    assert result["failed_rows"] == 0
    assert result["total_rows"] == 2

    products = client.get("/api/v1/products", headers=auth_headers(tokens)).json()["data"]
    assert {p["sku"] for p in products} == {"A-1", "B-1"}


def test_products_import_reports_row_errors(client: TestClient, db_session: Session) -> None:
    tokens = register(client)
    client.post("/api/v1/categories", json=category_payload(name="Electronics"), headers=auth_headers(tokens))

    content = build_csv(
        [
            {"SKU Code": "A-1", "Name": "Widget", "Cat": "Electronics", "Price": "9.99"},  # valid
            {"SKU Code": "", "Name": "No SKU", "Cat": "Electronics", "Price": "5.00"},  # missing SKU
            {"SKU Code": "A-1", "Name": "Dup", "Cat": "Electronics", "Price": "5.00"},  # duplicate SKU
            {"SKU Code": "C-1", "Name": "Bad Cat", "Cat": "Nonexistent", "Price": "5.00"},  # unknown category
            {"SKU Code": "D-1", "Name": "Bad Price", "Cat": "Electronics", "Price": "abc"},  # invalid number
        ]
    )
    job = upload_import(client, tokens, content=content)
    client.post(
        f"/api/v1/imports/{job['id']}/start",
        json={
            "mapping": {
                "sku": "SKU Code",
                "product_name": "Name",
                "category": "Cat",
                "selling_price": "Price",
            }
        },
        headers=auth_headers(tokens),
    )

    _run_worker(db_session, job["id"])

    result = client.get(f"/api/v1/imports/{job['id']}", headers=auth_headers(tokens)).json()["data"]
    assert result["status"] == "completed_with_errors"
    assert result["success_rows"] == 1
    assert result["failed_rows"] == 4

    errors = client.get(f"/api/v1/imports/{job['id']}/errors", headers=auth_headers(tokens)).json()["data"]
    messages = {(e["row_number"], e["field_name"]) for e in errors}
    assert (3, "sku") in messages  # missing SKU -> row 3 (header=1, then 4 data rows starting row 2)
    assert (4, "sku") in messages  # duplicate
    assert (5, "category") in messages  # unknown category
    assert (6, "selling_price") in messages  # invalid number
    for e in errors:
        assert e["raw_data"]  # raw row payload preserved


def test_inventory_import_with_job_level_store(client: TestClient, db_session: Session) -> None:
    tokens = register(client)
    store = client.post("/api/v1/stores", json=store_payload(), headers=auth_headers(tokens)).json()["data"]
    category = client.post(
        "/api/v1/categories", json=category_payload(), headers=auth_headers(tokens)
    ).json()["data"]
    client.post(
        "/api/v1/products",
        json={"category_id": category["id"], "sku": "A-1", "product_name": "Widget", "selling_price": "9.99"},
        headers=auth_headers(tokens),
    )

    content = build_csv([{"SKU": "A-1", "Qty": "50", "Reorder": "10"}])
    job = upload_import(
        client, tokens, content=content, entity_type="inventory", store_id=store["id"], filename="inv.csv"
    )
    client.post(
        f"/api/v1/imports/{job['id']}/start",
        json={"mapping": {"sku": "SKU", "quantity": "Qty", "reorder_point": "Reorder"}},
        headers=auth_headers(tokens),
    )

    _run_worker(db_session, job["id"])

    result = client.get(f"/api/v1/imports/{job['id']}", headers=auth_headers(tokens)).json()["data"]
    assert result["success_rows"] == 1

    inventory = client.get("/api/v1/inventory", headers=auth_headers(tokens)).json()["data"]
    assert len(inventory) == 1
    assert Decimal(inventory[0]["quantity_on_hand"]) == 50
    assert Decimal(inventory[0]["reorder_point"]) == 10


def test_inventory_import_unknown_sku_reported(client: TestClient, db_session: Session) -> None:
    tokens = register(client)
    store = client.post("/api/v1/stores", json=store_payload(), headers=auth_headers(tokens)).json()["data"]

    content = build_csv([{"SKU": "GHOST", "Qty": "5"}])
    job = upload_import(
        client, tokens, content=content, entity_type="inventory", store_id=store["id"], filename="inv.csv"
    )
    client.post(
        f"/api/v1/imports/{job['id']}/start",
        json={"mapping": {"sku": "SKU", "quantity": "Qty"}},
        headers=auth_headers(tokens),
    )

    _run_worker(db_session, job["id"])

    result = client.get(f"/api/v1/imports/{job['id']}", headers=auth_headers(tokens)).json()["data"]
    assert result["failed_rows"] == 1
    errors = client.get(f"/api/v1/imports/{job['id']}/errors", headers=auth_headers(tokens)).json()["data"]
    assert errors[0]["field_name"] == "sku"
    assert "GHOST" in errors[0]["error_message"]


def test_cannot_upload_against_another_orgs_store(client: TestClient) -> None:
    org_a = register(client, organization_name="Org A", email="admin-a@acme.com")
    org_b = register(client, organization_name="Org B", email="admin-b@acme.com")
    store_b = client.post(
        "/api/v1/stores", json=store_payload(), headers=auth_headers(org_b)
    ).json()["data"]

    response = client.post(
        "/api/v1/imports",
        files={"file": ("inv.csv", build_csv([{"SKU": "A", "Qty": "1"}]), "text/csv")},
        data={"entity_type": "inventory", "store_id": store_b["id"]},
        headers=auth_headers(org_a),
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "store_not_found"


def test_cannot_get_another_orgs_import_job(client: TestClient) -> None:
    org_a = register(client, organization_name="Org A", email="admin-a@acme.com")
    org_b = register(client, organization_name="Org B", email="admin-b@acme.com")
    content = build_csv([{"SKU Code": "A-1", "Name": "Widget", "Cat": "Electronics", "Price": "9.99"}])
    job_b = upload_import(client, org_b, content=content)

    response = client.get(f"/api/v1/imports/{job_b['id']}", headers=auth_headers(org_a))

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "import_job_not_found"


def test_role_without_imports_create_permission_is_denied(client: TestClient, db_session: Session) -> None:
    admin_tokens = register(client)
    organization_id = client.get("/api/v1/auth/me", headers=auth_headers(admin_tokens)).json()["data"][
        "user"
    ]["organization_id"]

    add_user_with_role(
        db_session,
        organization_id=uuid.UUID(organization_id),
        email="viewer@acme.com",
        role_name="Viewer",
    )
    login = client.post("/api/v1/auth/login", json={"email": "viewer@acme.com", "password": "SuperSecret1"})
    viewer_tokens = login.json()["data"]

    content = build_csv([{"SKU": "A", "Name": "X", "Cat": "Y", "Price": "1"}])
    response = client.post(
        "/api/v1/imports",
        files={"file": ("products.csv", content, "text/csv")},
        data={"entity_type": "products"},
        headers=auth_headers(viewer_tokens),
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "permission_denied"
