import csv
import io
import uuid

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.role import Role
from app.models.user import User, UserStatus
from app.models.user_role import UserRole


def register(
    client: TestClient,
    *,
    organization_name: str = "Acme Retail",
    first_name: str = "Ada",
    last_name: str = "Lovelace",
    email: str = "ada@acme.com",
    password: str = "SuperSecret1",
) -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "organization_name": organization_name,
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "password": password,
            "confirm_password": password,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]


def auth_headers(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def store_payload(**overrides) -> dict:
    payload = {
        "store_code": "NYC-001",
        "name": "Fifth Avenue Flagship",
        "store_type": "flagship",
        "country": "United States",
        "city": "New York",
        "address_line_1": "123 Fifth Avenue",
        "timezone": "America/New_York",
        "currency": "USD",
    }
    payload.update(overrides)
    return payload


def category_payload(**overrides) -> dict:
    payload = {"name": "Electronics"}
    payload.update(overrides)
    return payload


def product_payload(*, category_id: str, **overrides) -> dict:
    payload = {
        "category_id": category_id,
        "sku": "SKU-001",
        "product_name": "Wireless Mouse",
        "selling_price": "19.9900",
    }
    payload.update(overrides)
    return payload


def inventory_payload(*, store_id: str, product_id: str, **overrides) -> dict:
    payload = {"store_id": store_id, "product_id": product_id}
    payload.update(overrides)
    return payload


def adjustment_item(*, store_id: str, product_id: str, **overrides) -> dict:
    payload = {
        "store_id": store_id,
        "product_id": product_id,
        "adjustment_type": "increase",
        "adjustment_quantity": "10",
        "reason": "Received shipment",
    }
    payload.update(overrides)
    return payload


def build_csv(rows: list[dict[str, str]], columns: list[str] | None = None) -> bytes:
    fieldnames = columns or list(rows[0].keys())
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8")


def upload_import(
    client: TestClient,
    tokens: dict,
    *,
    filename: str = "products.csv",
    content: bytes,
    entity_type: str = "products",
    store_id: str | None = None,
) -> dict:
    data = {"entity_type": entity_type}
    if store_id:
        data["store_id"] = store_id
    response = client.post(
        "/api/v1/imports",
        files={"file": (filename, content, "text/csv")},
        data=data,
        headers=auth_headers(tokens),
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]


def price_payload(*, product_id: str, **overrides) -> dict:
    payload = {
        "product_id": product_id,
        "base_price": "100.0000",
        "selling_price": "100.0000",
        "currency": "USD",
    }
    payload.update(overrides)
    return payload


def pricing_rule_payload(**overrides) -> dict:
    payload = {
        "name": "10% Off Electronics",
        "rule_type": "percentage_discount",
        "priority": 100,
        "actions_json": {"kind": "percentage_discount", "value": "10"},
        "status": "active",
    }
    payload.update(overrides)
    return payload


def device_payload(*, store_id: str, vendor_id: str, device_model_id: str, **overrides) -> dict:
    payload = {
        "store_id": store_id,
        "vendor_id": vendor_id,
        "device_model_id": device_model_id,
        "device_identifier": "SIM-0001",
        "device_name": "Aisle 1 Shelf Tag",
    }
    payload.update(overrides)
    return payload


def device_assignment_payload(*, device_id: str, store_id: str, product_id: str, **overrides) -> dict:
    payload = {"device_id": device_id, "store_id": store_id, "product_id": product_id}
    payload.update(overrides)
    return payload


def esl_integration_payload(*, vendor_id: str, store_id: str, **overrides) -> dict:
    payload = {
        "vendor_id": vendor_id,
        "name": "Mock Integration",
        "integration_type": "mock",
        "store_id": store_id,
        "credentials": {"api_key": "test-key"},
    }
    payload.update(overrides)
    return payload


def integration_payload(**overrides) -> dict:
    payload = {
        "name": "CSV Product Feed",
        "integration_category": "erp",
        "provider": "csv",
        "credentials": {},
    }
    payload.update(overrides)
    return payload


def integration_authority_payload(**overrides) -> dict:
    payload = {
        "entity_type": "price",
        "field_name": "selling_price",
        "authority": "pip",
        "allow_override": False,
    }
    payload.update(overrides)
    return payload


def integration_sync_schedule_payload(**overrides) -> dict:
    payload = {"entity_type": "product", "job_type": "incremental_sync", "interval_minutes": 15}
    payload.update(overrides)
    return payload


def integration_mapping_payload(**overrides) -> dict:
    payload = {
        "entity_type": "product",
        "source_field": "SKU",
        "canonical_field": "sku",
        "transformation_rule": "direct",
    }
    payload.update(overrides)
    return payload


def output_channel_payload(**overrides) -> dict:
    payload = {"name": "Front Window ESL", "output_type": "esl_simulator"}
    payload.update(overrides)
    return payload


def output_job_payload(*, output_channel_id: str, product_id: str, **overrides) -> dict:
    payload = {"output_channel_id": output_channel_id, "product_id": product_id}
    payload.update(overrides)
    return payload


def output_routing_rule_payload(**overrides) -> dict:
    payload = {
        "name": "Grocery -> ESL/QR/POS",
        "priority": 100,
        "conditions_json": None,
        "target_outputs_json": ["esl_simulator", "qr_code"],
        "status": "active",
    }
    payload.update(overrides)
    return payload


def add_user_with_role(
    db_session: Session,
    *,
    organization_id: uuid.UUID,
    email: str,
    role_name: str,
    password: str = "SuperSecret1",
) -> User:
    """Create a user directly (bypassing /auth/register) and assign an
    existing seeded system role by name. Used to test RBAC denial for roles
    other than the auto-assigned Organization Admin.
    """
    role = db_session.execute(select(Role).where(Role.name == role_name)).scalar_one()
    user = User(
        id=uuid.uuid4(),
        organization_id=organization_id,
        first_name="Test",
        last_name="User",
        email=email,
        password_hash=hash_password(password),
        status=UserStatus.ACTIVE,
    )
    db_session.add(user)
    db_session.flush()
    db_session.add(UserRole(id=uuid.uuid4(), user_id=user.id, role_id=role.id))
    db_session.commit()
    return user
