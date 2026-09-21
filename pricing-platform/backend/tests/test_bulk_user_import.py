import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.services import import_service
from tests.helpers import auth_headers, build_csv, register, upload_import


def _run_worker(db_session: Session, job_id: str) -> None:
    import_service.process_import_job(uuid.UUID(job_id), db=db_session)


def _start(client: TestClient, tokens: dict, job_id: str, mapping: dict) -> dict:
    response = client.post(
        f"/api/v1/imports/{job_id}/start", json={"mapping": mapping}, headers=auth_headers(tokens)
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]


def test_bulk_user_upload_creates_users_with_roles(client: TestClient, db_session: Session) -> None:
    tokens = register(client)
    content = build_csv(
        [
            {
                "First": "Nia",
                "Last": "Store",
                "Email": "bulk1@acme.com",
                "Pass": "SuperSecret1",
                "Role": "Store Manager",
            },
            {
                "First": "Vik",
                "Last": "View",
                "Email": "bulk2@acme.com",
                "Pass": "SuperSecret1",
                "Role": "Viewer",
            },
        ],
        columns=["First", "Last", "Email", "Pass", "Role"],
    )
    job = upload_import(client, tokens, content=content, entity_type="users")

    started = _start(
        client,
        tokens,
        job["id"],
        {
            "first_name": "First",
            "last_name": "Last",
            "email": "Email",
            "password": "Pass",
            "role": "Role",
        },
    )
    _run_worker(db_session, started["id"])

    result = client.get(f"/api/v1/imports/{job['id']}", headers=auth_headers(tokens)).json()["data"]
    assert result["status"] == "completed"
    assert result["success_rows"] == 2
    assert result["failed_rows"] == 0

    users = client.get("/api/v1/users?search=bulk", headers=auth_headers(tokens)).json()["data"]
    emails_to_roles = {u["email"]: [r["name"] for r in u["roles"]] for u in users}
    assert emails_to_roles["bulk1@acme.com"] == ["Store Manager"]
    assert emails_to_roles["bulk2@acme.com"] == ["Viewer"]

    login = client.post(
        "/api/v1/auth/login", json={"email": "bulk1@acme.com", "password": "SuperSecret1"}
    )
    assert login.status_code == 200


def test_bulk_user_upload_reports_row_errors(client: TestClient, db_session: Session) -> None:
    tokens = register(client, email="bulkadmin@acme.com")
    content = build_csv(
        [
            {
                "First": "Ok",
                "Last": "User",
                "Email": "bulkok@acme.com",
                "Pass": "SuperSecret1",
                "Role": "Viewer",
            },
            {
                "First": "Bad",
                "Last": "Role",
                "Email": "bulkbad@acme.com",
                "Pass": "SuperSecret1",
                "Role": "Nonexistent",
            },
            {
                "First": "Short",
                "Last": "Pw",
                "Email": "bulkshort@acme.com",
                "Pass": "short",
                "Role": "Viewer",
            },
            {
                "First": "Dup",
                "Last": "Email",
                "Email": "bulkadmin@acme.com",
                "Pass": "SuperSecret1",
                "Role": "Viewer",
            },
        ],
        columns=["First", "Last", "Email", "Pass", "Role"],
    )
    job = upload_import(client, tokens, content=content, entity_type="users")

    started = _start(
        client,
        tokens,
        job["id"],
        {
            "first_name": "First",
            "last_name": "Last",
            "email": "Email",
            "password": "Pass",
            "role": "Role",
        },
    )
    _run_worker(db_session, started["id"])

    result = client.get(f"/api/v1/imports/{job['id']}", headers=auth_headers(tokens)).json()["data"]
    assert result["status"] == "completed_with_errors"
    assert result["success_rows"] == 1
    assert result["failed_rows"] == 3

    errors = client.get(f"/api/v1/imports/{job['id']}/errors", headers=auth_headers(tokens)).json()["data"]
    fields = {e["field_name"] for e in errors}
    assert fields == {"role", "password", "email"}


def test_start_import_rejects_missing_required_users_mapping(client: TestClient) -> None:
    tokens = register(client)
    content = build_csv([{"First": "A", "Last": "B", "Email": "x@acme.com"}])
    job = upload_import(client, tokens, content=content, entity_type="users")

    response = client.post(
        f"/api/v1/imports/{job['id']}/start",
        json={"mapping": {"first_name": "First"}},
        headers=auth_headers(tokens),
    )

    assert response.status_code == 422
