import uuid
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401  # registers every model with Base.metadata
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.device_model import DeviceModel
from app.models.device_vendor import DeviceVendor
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission

# Mirrors alembic/versions/eaa27d8a5e16_seed_rbac_permissions_and_system_roles.py,
# alembic/versions/83921e864ba5_seed_categories_permissions.py,
# alembic/versions/e849cf59dc1f_seed_inventory_permissions.py,
# alembic/versions/3dcfb4ae03c1_seed_imports_permissions.py,
# alembic/versions/a1f3c9d2b6e4_seed_ai_recommendations_permissions.py, and
# alembic/versions/e6a94367f581_seed_analytics_permissions.py. Kept as a
# separate, deliberately-duplicated copy rather than a shared import: those
# migrations are pinned to their literal values on purpose (migrations must
# stay stable even if application code changes later), so tests seed the
# same fixture data independently rather than depending on Alembic running
# against a throwaway SQLite DB.
_PERMISSIONS: list[tuple[str, str, str]] = [
    ("organizations.read", "View organization", "organizations"),
    ("organizations.update", "Update organization", "organizations"),
    ("categories.read", "View categories", "categories"),
    ("categories.create", "Create categories", "categories"),
    ("categories.update", "Update categories", "categories"),
    ("categories.delete", "Delete categories", "categories"),
    ("inventory.read", "View inventory", "inventory"),
    ("inventory.create", "Register inventory tracking for a store/product", "inventory"),
    ("inventory.update", "Update inventory settings", "inventory"),
    ("inventory.adjust", "Adjust on-hand stock quantities", "inventory"),
    ("imports.read", "View import jobs and their errors", "imports"),
    ("imports.create", "Upload and run bulk imports", "imports"),
    ("users.read", "View users", "users"),
    ("users.create", "Create users", "users"),
    ("users.update", "Update users", "users"),
    ("users.delete", "Delete users", "users"),
    ("stores.read", "View stores", "stores"),
    ("stores.create", "Create stores", "stores"),
    ("stores.update", "Update stores", "stores"),
    ("stores.delete", "Delete stores", "stores"),
    ("products.read", "View products", "products"),
    ("products.create", "Create products", "products"),
    ("products.update", "Update products", "products"),
    ("products.delete", "Delete products", "products"),
    ("pricing.read", "View pricing", "pricing"),
    ("pricing.create", "Create pricing", "pricing"),
    ("pricing.update", "Update pricing", "pricing"),
    ("pricing.approve", "Approve pricing changes", "pricing"),
    ("devices.read", "View ESL devices", "devices"),
    ("devices.create", "Register ESL devices", "devices"),
    ("devices.update", "Update ESL devices", "devices"),
    ("devices.manage", "Manage ESL devices (push updates)", "devices"),
    ("integrations.read", "View integrations", "integrations"),
    ("integrations.create", "Create integrations", "integrations"),
    ("integrations.update", "Update integrations", "integrations"),
    (
        "integrations.manage",
        "Manage integration locations, authority config, webhook secrets, and schedules",
        "integrations",
    ),
    ("integrations.reconcile", "Trigger and resolve integration reconciliation", "integrations"),
    ("outputs.read", "View output channels and jobs", "outputs"),
    ("outputs.create", "Create output channels", "outputs"),
    ("outputs.update", "Update output channels", "outputs"),
    ("outputs.manage", "Dispatch and retry output jobs", "outputs"),
    ("ai_recommendations.read", "View AI pricing recommendations", "ai_recommendations"),
    ("ai_recommendations.create", "Generate AI pricing recommendations", "ai_recommendations"),
    (
        "ai_recommendations.review",
        "Approve, reject, or modify AI pricing recommendations",
        "ai_recommendations",
    ),
    (
        "ai_recommendations.apply",
        "Apply an approved AI pricing recommendation as a real price",
        "ai_recommendations",
    ),
    ("analytics.read", "View pricing analytics dashboards", "analytics"),
]
_ALL_CODES = [code for code, _, _ in _PERMISSIONS]
_READ_ONLY_CODES = [code for code in _ALL_CODES if code.endswith(".read")]
_ROLES: dict[str, list[str]] = {
    "Super Admin": _ALL_CODES,
    "Organization Admin": _ALL_CODES,
    "Store Manager": [
        "stores.read",
        "stores.create",
        "stores.update",
        "stores.delete",
        "products.read",
        "products.update",
        "pricing.read",
        "categories.read",
        "inventory.read",
        "inventory.adjust",
        "imports.read",
        "imports.create",
        "outputs.read",
        "outputs.manage",
        "devices.read",
        "devices.manage",
        "analytics.read",
    ],
    "Pricing Manager": [
        "pricing.read",
        "pricing.create",
        "pricing.update",
        "pricing.approve",
        "products.read",
        "categories.read",
        "inventory.read",
        "imports.read",
        "outputs.read",
        "ai_recommendations.read",
        "ai_recommendations.create",
        "ai_recommendations.review",
        "ai_recommendations.apply",
        "analytics.read",
    ],
    "Inventory Manager": [
        "products.read",
        "products.update",
        "stores.read",
        "categories.read",
        "inventory.read",
        "inventory.create",
        "inventory.update",
        "inventory.adjust",
        "imports.read",
        "imports.create",
        "devices.read",
        "analytics.read",
    ],
    "Viewer": _READ_ONLY_CODES,
}


def _seed_rbac(session: Session) -> None:
    now = datetime.now(UTC)
    permission_ids = {code: uuid.uuid4() for code in _ALL_CODES}
    session.add_all(
        Permission(id=permission_ids[code], code=code, name=name, module=module)
        for code, name, module in _PERMISSIONS
    )
    role_ids = {name: uuid.uuid4() for name in _ROLES}
    session.add_all(
        Role(
            id=role_ids[name],
            organization_id=None,
            name=name,
            is_system_role=True,
            created_at=now,
            updated_at=now,
        )
        for name in _ROLES
    )
    session.flush()
    session.add_all(
        RolePermission(
            id=uuid.uuid4(),
            role_id=role_ids[role_name],
            permission_id=permission_ids[code],
            created_at=now,
        )
        for role_name, codes in _ROLES.items()
        for code in codes
    )
    session.commit()


# Mirrors alembic/versions/9c4e2a6f8d1b_seed_esl_simulator_vendor_and_model.py
# and 5e8b1f4a2c7d/7b3d9f2e5a1c (Phase 9's Mock Vendor catalog entry) —
# device_vendors/device_models are global catalog data with no seed
# migration equivalent run against the throwaway SQLite test DB, so tests
# need this fixture data to exercise device/integration creation at all.
DEVICE_VENDOR_ID = uuid.uuid4()
DEVICE_MODEL_ID = uuid.uuid4()
MOCK_VENDOR_ID = uuid.uuid4()
MOCK_MODEL_ID = uuid.uuid4()
# Phase 9 stub vendors (app/integrations/esl/vendor_stubs.py) — code -> id,
# so tests can look one up without a live DB query.
STUB_VENDOR_IDS: dict[str, uuid.UUID] = {
    code: uuid.uuid4() for code in ("vusion", "hanshow", "solum", "pricer", "zkong")
}


def _seed_device_catalog(session: Session) -> None:
    session.add(DeviceVendor(id=DEVICE_VENDOR_ID, name="ESL Simulator", code="esl_simulator"))
    session.add(DeviceVendor(id=MOCK_VENDOR_ID, name="Mock Vendor (Testing)", code="mock"))
    for code, vendor_id in STUB_VENDOR_IDS.items():
        session.add(DeviceVendor(id=vendor_id, name=code.capitalize(), code=code))
    session.flush()
    session.add(
        DeviceModel(
            id=DEVICE_MODEL_ID,
            vendor_id=DEVICE_VENDOR_ID,
            name="Generic Simulator Display",
            model_code="SIM-1",
            screen_size="2.9in",
            resolution="296x128",
            color_capabilities={"colors": ["black", "white", "red"]},
            battery_type="CR2450",
            communication_type="mqtt",
        )
    )
    session.add(
        DeviceModel(
            id=MOCK_MODEL_ID,
            vendor_id=MOCK_VENDOR_ID,
            name="Generic Placeholder Display",
            model_code="PLACEHOLDER-1",
            communication_type="mock",
        )
    )
    session.commit()


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    session = TestingSessionLocal()
    _seed_rbac(session)
    _seed_device_catalog(session)
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture()
def client(db_session: Session) -> TestClient:
    def _override_get_db():
        # Mirrors app.db.session.get_db's one-transaction-per-request
        # behavior (commit on success, rollback on exception) using a
        # SAVEPOINT per request instead of a whole new session, so requests
        # within one test still share — and see — each other's committed
        # data, while a failed request's partial writes still roll back.
        db_session.begin_nested()
        try:
            yield db_session
            db_session.commit()
        except Exception:
            db_session.rollback()
            raise

    app.dependency_overrides[get_db] = _override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_db, None)
