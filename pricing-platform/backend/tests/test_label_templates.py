import uuid
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.services import output_job_service
from app.storage.local import LocalFilesystemStorageAdapter
from tests.helpers import (
    auth_headers,
    category_payload,
    output_channel_payload,
    output_job_payload,
    product_payload,
    register,
)

_DEFAULT_COLORS = {
    "background": "#FFFFFF",
    "border": "#111111",
    "text": "#111111",
    "banner": "#111111",
    "unit_border": "#111111",
    "sublabel": "#666666",
    "placeholder": "#AAAAAA",
}


def _register_second_org(client: TestClient) -> dict:
    """Register a second organization and return its tokens."""
    return register(
        client,
        organization_name="Other Retail",
        first_name="Bob",
        last_name="Smith",
        email="bob@other.com",
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


def _setup_channel(client: TestClient, tokens: dict, **overrides) -> dict:
    return client.post(
        "/api/v1/outputs/channels",
        json=output_channel_payload(**overrides),
        headers=auth_headers(tokens),
    ).json()["data"]


def _create_template(client: TestClient, tokens: dict, **overrides) -> dict:
    payload = {"name": "Store Template", **overrides}
    response = client.post(
        "/api/v1/outputs/label-templates",
        json=payload,
        headers=auth_headers(tokens),
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]


def _run_worker(db_session: Session, job_id: str) -> None:
    output_job_service.process_output_job(uuid.UUID(job_id), db=db_session)


# ─────────────────────────────────────────────────────────────
# CRUD
# ─────────────────────────────────────────────────────────────


def test_template_crud(client: TestClient) -> None:
    tokens = register(client)

    # Create
    tpl = _create_template(
        client,
        tokens,
        name="Red Banner",
        colors={"banner": "#FF0000", "text": "#000000"},
    )
    assert tpl["name"] == "Red Banner"
    assert tpl["colors"]["banner"] == "#FF0000"
    assert tpl["background_image_url"] is None

    # Read
    get_resp = client.get(
        f"/api/v1/outputs/label-templates/{tpl['id']}", headers=auth_headers(tokens)
    )
    assert get_resp.status_code == 200, get_resp.text
    assert get_resp.json()["data"]["name"] == "Red Banner"

    # List
    list_resp = client.get("/api/v1/outputs/label-templates", headers=auth_headers(tokens))
    assert list_resp.status_code == 200, list_resp.text
    assert len(list_resp.json()["data"]) == 1

    # Update
    update_resp = client.put(
        f"/api/v1/outputs/label-templates/{tpl['id']}",
        json={"name": "Blue Banner", "colors": {"background": "#0000FF"}},
        headers=auth_headers(tokens),
    )
    assert update_resp.status_code == 200, update_resp.text
    updated = update_resp.json()["data"]
    assert updated["name"] == "Blue Banner"
    assert updated["colors"]["background"] == "#0000FF"
    # banner key is gone (replaced entirely)
    assert "banner" not in updated["colors"]

    # Delete
    del_resp = client.delete(
        f"/api/v1/outputs/label-templates/{tpl['id']}", headers=auth_headers(tokens)
    )
    assert del_resp.status_code == 204

    # Verify gone
    gone_resp = client.get(
        f"/api/v1/outputs/label-templates/{tpl['id']}", headers=auth_headers(tokens)
    )
    assert gone_resp.status_code == 404


# ─────────────────────────────────────────────────────────────
# Tenant isolation
# ─────────────────────────────────────────────────────────────


def test_template_tenant_isolation(client: TestClient) -> None:
    tokens_a = register(client)
    tpl = _create_template(client, tokens_a, name="Org A template")

    tokens_b = _register_second_org(client)

    # Org B can't see Org A's template
    get_resp = client.get(
        f"/api/v1/outputs/label-templates/{tpl['id']}", headers=auth_headers(tokens_b)
    )
    assert get_resp.status_code == 404, get_resp.text

    # Org B's list is empty
    list_resp = client.get("/api/v1/outputs/label-templates", headers=auth_headers(tokens_b))
    assert len(list_resp.json()["data"]) == 0


# ─────────────────────────────────────────────────────────────
# Validation: bad hex
# ─────────────────────────────────────────────────────────────


def test_template_bad_hex_rejected(client: TestClient) -> None:
    tokens = register(client)

    response = client.post(
        "/api/v1/outputs/label-templates",
        json={"name": "Bad", "colors": {"banner": "not-a-color"}},
        headers=auth_headers(tokens),
    )
    assert response.status_code == 422, response.text

    # Unknown color key also rejected
    response = client.post(
        "/api/v1/outputs/label-templates",
        json={"name": "Unknown key", "colors": {"nonexistent": "#000000"}},
        headers=auth_headers(tokens),
    )
    assert response.status_code == 422, response.text


# ─────────────────────────────────────────────────────────────
# Channel rejects unknown/other-org template
# ─────────────────────────────────────────────────────────────


def test_channel_rejects_unknown_or_other_org_template(client: TestClient) -> None:
    tokens = register(client)
    tokens_b = _register_second_org(client)

    # Unknown template id
    resp = client.post(
        "/api/v1/outputs/channels",
        json={
            "name": "PDF Bad",
            "output_type": "pdf_label",
            "label_template_id": str(uuid.uuid4()),
        },
        headers=auth_headers(tokens),
    )
    assert resp.status_code == 404, resp.text

    # Create a template under Org A, try to assign from Org B
    tpl = _create_template(client, tokens, name="Org A only")
    resp = client.put(
        "/api/v1/outputs/channels",
        json={"label_template_id": tpl["id"]},
        headers=auth_headers(tokens_b),
    )
    # Org B has no channels — so this is really about channel creation under B
    resp = client.post(
        "/api/v1/outputs/channels",
        json={
            "name": "PDF Stolen",
            "output_type": "pdf_label",
            "label_template_id": tpl["id"],
        },
        headers=auth_headers(tokens_b),
    )
    assert resp.status_code == 404, resp.text


# ─────────────────────────────────────────────────────────────
# Delete template detaches channel (FK SET NULL)
# ─────────────────────────────────────────────────────────────


def test_delete_template_does_not_break_jobs(client: TestClient, db_session: Session) -> None:
    """Deleting a template that a channel references doesn't crash jobs —
    the render path falls back to built-in defaults (get_by_id returns
    None, so template_colors stays None).

    Note: ON DELETE SET NULL is a MySQL/PostgreSQL guarantee. SQLite
    doesn't enforce FK actions without PRAGMA foreign_keys = ON, so we
    don't assert the FK bookkeeping here — we assert the user-facing
    contract: the job still completes.
    """
    tokens = register(client)
    tpl = _create_template(client, tokens, name="Temporary template")
    channel = _setup_channel(
        client,
        tokens,
        name="PDF with template",
        output_type="pdf_label",
        label_template_id=tpl["id"],
    )
    assert channel["label_template_id"] == tpl["id"]

    # Delete the template
    del_resp = client.delete(
        f"/api/v1/outputs/label-templates/{tpl['id']}", headers=auth_headers(tokens)
    )
    assert del_resp.status_code == 204

    # Job still completes (template is gone → get_by_id returns None → defaults)
    product = _setup_product(client, tokens)
    job = client.post(
        "/api/v1/outputs/jobs",
        json=output_job_payload(output_channel_id=channel["id"], product_id=product["id"]),
        headers=auth_headers(tokens),
    ).json()["data"]
    _run_worker(db_session, job["id"])
    final = client.get(f"/api/v1/outputs/jobs/{job['id']}", headers=auth_headers(tokens)).json()["data"]
    assert final["status"] == "completed"
    assert final["payload"]["pdf_base64"]


# ─────────────────────────────────────────────────────────────
# PDF job with template
# ─────────────────────────────────────────────────────────────


def test_pdf_job_with_template_renders(client: TestClient, db_session: Session) -> None:
    """A PDF label job on a channel with a template assigned completes and
    produces a valid PDF. The render path merges template colors over the
    defaults (here we use all defaults to exercise the resolution path).
    """
    tokens = register(client)
    product = _setup_product(client, tokens, selling_price="39.9900")
    tpl = _create_template(
        client,
        tokens,
        name="Custom Label",
        colors=_DEFAULT_COLORS,
    )
    channel = _setup_channel(
        client,
        tokens,
        name="PDF Store A",
        output_type="pdf_label",
        label_template_id=tpl["id"],
    )
    assert channel["label_template_id"] == tpl["id"]

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
    assert payload["price"] == "39.99"


def test_pdf_job_with_background_image(
    client: TestClient, db_session: Session, tmp_path: Path, monkeypatch
) -> None:
    """A PDF job with a template that has a background image completes —
    the image is drawn behind text/QR if it can be downloaded; any failure
    falls back to the plain color background without crashing.
    """
    tokens = register(client)
    product = _setup_product(client, tokens, selling_price="29.9900")

    # Use a temp directory for storage so we don't pollute the project
    monkeypatch.setattr(
        "app.services.label_template_service.get_storage_adapter",
        lambda: LocalFilesystemStorageAdapter(tmp_path / "storage"),
    )

    # Upload a small PNG (1×1 red pixel)
    def _png_bytes() -> bytes:
        import struct
        import zlib

        def chunk(tag: bytes, data: bytes) -> bytes:
            c = struct.pack(">I", len(data)) + tag + data
            c += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
            return c

        ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
        raw = b"\x00\xff\x00\x00"
        return (
            b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(raw))
            + chunk(b"IEND", b"")
        )

    # Create a template with a background image via direct API call
    tpl_payload = {"name": "Image Template", "colors": _DEFAULT_COLORS}
    tpl_resp = client.post(
        "/api/v1/outputs/label-templates",
        json=tpl_payload,
        headers=auth_headers(tokens),
    )
    assert tpl_resp.status_code == 201, tpl_resp.text
    tpl_id = tpl_resp.json()["data"]["id"]

    # Upload background image
    upload_resp = client.post(
        f"/api/v1/outputs/label-templates/{tpl_id}/background-image",
        files={"file": ("bg.png", _png_bytes(), "image/png")},
        headers=auth_headers(tokens),
    )
    assert upload_resp.status_code == 200, upload_resp.text
    assert upload_resp.json()["data"]["background_image_url"] is not None

    # Channel with the template
    channel = _setup_channel(
        client,
        tokens,
        name="PDF Image",
        output_type="pdf_label",
        label_template_id=tpl_id,
    )

    # Run a job — the adapter downloads the image, draws it behind text/QR
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


def test_unsupported_image_type_rejected(client: TestClient) -> None:
    tokens = register(client)
    tpl = _create_template(client, tokens, name="Will fail upload")

    response = client.post(
        f"/api/v1/outputs/label-templates/{tpl['id']}/background-image",
        files={"file": ("bad.bmp", b"not-an-image", "image/bmp")},
        headers=auth_headers(tokens),
    )
    assert response.status_code == 422, response.text
