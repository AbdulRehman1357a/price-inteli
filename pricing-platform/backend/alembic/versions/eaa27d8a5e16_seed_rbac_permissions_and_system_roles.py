"""seed rbac permissions and system roles

Revision ID: eaa27d8a5e16
Revises: 78c1a8124f99
Create Date: 2026-08-25 11:31:07.762958

Data-only migration. Seeds the 24 Phase 1 permission codes and the six
built-in system roles (organization_id=NULL, is_system_role=True), plus the
role -> permission grants below.

This file intentionally hardcodes literal strings rather than importing
app.core.rbac: migrations must stay stable even if application code changes
later. app.core.rbac.SystemRoleName / PermissionCode are the source of
truth these values were copied from at the time this migration was written.

Role -> permission mapping is a starting point, not a spec handed down by
the product: there are no inventory.* permission codes in the Phase 1 list,
so "Inventory Manager" is granted the closest available product/store
permissions below. Adjust via a future migration once inventory
permissions exist.
"""
import uuid
from datetime import UTC, datetime
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'eaa27d8a5e16'
down_revision: Union[str, None] = '78c1a8124f99'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

PERMISSIONS: list[tuple[str, str, str]] = [
    # (code, name, module)
    ("organizations.read", "View organization", "organizations"),
    ("organizations.update", "Update organization", "organizations"),
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
]

ALL_CODES = [code for code, _, _ in PERMISSIONS]
READ_ONLY_CODES = [code for code in ALL_CODES if code.endswith(".read")]

ROLES: dict[str, list[str]] = {
    "Super Admin": ALL_CODES,
    "Organization Admin": ALL_CODES,
    "Store Manager": [
        "stores.read",
        "stores.create",
        "stores.update",
        "stores.delete",
        "products.read",
        "products.update",
        "pricing.read",
    ],
    "Pricing Manager": [
        "pricing.read",
        "pricing.create",
        "pricing.update",
        "pricing.approve",
        "products.read",
    ],
    "Inventory Manager": [
        "products.read",
        "products.update",
        "stores.read",
    ],
    "Viewer": READ_ONLY_CODES,
}

permissions_table = sa.table(
    "permissions",
    sa.column("id", sa.Uuid(native_uuid=False)),
    sa.column("code", sa.String(length=150)),
    sa.column("name", sa.String(length=150)),
    sa.column("module", sa.String(length=100)),
)

roles_table = sa.table(
    "roles",
    sa.column("id", sa.Uuid(native_uuid=False)),
    sa.column("organization_id", sa.Uuid(native_uuid=False)),
    sa.column("name", sa.String(length=100)),
    sa.column("is_system_role", sa.Boolean()),
    sa.column("created_at", sa.DateTime(timezone=True)),
    sa.column("updated_at", sa.DateTime(timezone=True)),
)

role_permissions_table = sa.table(
    "role_permissions",
    sa.column("id", sa.Uuid(native_uuid=False)),
    sa.column("role_id", sa.Uuid(native_uuid=False)),
    sa.column("permission_id", sa.Uuid(native_uuid=False)),
    sa.column("created_at", sa.DateTime(timezone=True)),
)


def upgrade() -> None:
    now = datetime.now(UTC)

    permission_ids = {code: uuid.uuid4() for code in ALL_CODES}
    op.bulk_insert(
        permissions_table,
        [
            {"id": permission_ids[code], "code": code, "name": name, "module": module}
            for code, name, module in PERMISSIONS
        ],
    )

    role_ids = {name: uuid.uuid4() for name in ROLES}
    op.bulk_insert(
        roles_table,
        [
            {
                "id": role_ids[name],
                "organization_id": None,
                "name": name,
                "is_system_role": True,
                "created_at": now,
                "updated_at": now,
            }
            for name in ROLES
        ],
    )

    op.bulk_insert(
        role_permissions_table,
        [
            {
                "id": uuid.uuid4(),
                "role_id": role_ids[role_name],
                "permission_id": permission_ids[code],
                "created_at": now,
            }
            for role_name, codes in ROLES.items()
            for code in codes
        ],
    )


def downgrade() -> None:
    op.execute(role_permissions_table.delete())
    op.execute(roles_table.delete().where(roles_table.c.is_system_role.is_(True)))
    op.execute(permissions_table.delete())
