"""seed inventory permissions

Revision ID: e849cf59dc1f
Revises: 29e0d36e7acf
Create Date: 2026-08-25 12:41:52.000000

Data-only migration, same pattern as 83921e864ba5 (categories permissions):
Phase 1 didn't seed inventory.* since the resource didn't exist yet. Grants
full access to Super Admin / Organization Admin / Inventory Manager (whose
whole purpose is this), read + adjust to Store Manager (day-to-day stock
counts at their own store, but not reconfiguring reorder/safety-stock
settings or registering new store/product tracking), and read-only to
Pricing Manager and Viewer.

Hardcodes literal strings rather than importing app.core.rbac so the
migration stays stable if that module changes later.
"""
import uuid
from datetime import UTC, datetime
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'e849cf59dc1f'
down_revision: Union[str, None] = '29e0d36e7acf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

PERMISSIONS: list[tuple[str, str, str]] = [
    ("inventory.read", "View inventory", "inventory"),
    ("inventory.create", "Register inventory tracking for a store/product", "inventory"),
    ("inventory.update", "Update inventory settings (reorder point, safety stock)", "inventory"),
    ("inventory.adjust", "Adjust on-hand stock quantities", "inventory"),
]
ALL_CODES = [code for code, _, _ in PERMISSIONS]

ROLE_GRANTS: dict[str, list[str]] = {
    "Super Admin": ALL_CODES,
    "Organization Admin": ALL_CODES,
    "Inventory Manager": ALL_CODES,
    "Store Manager": ["inventory.read", "inventory.adjust"],
    "Pricing Manager": ["inventory.read"],
    "Viewer": ["inventory.read"],
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
    sa.column("name", sa.String(length=100)),
    sa.column("organization_id", sa.Uuid(native_uuid=False)),
    sa.column("is_system_role", sa.Boolean()),
)

role_permissions_table = sa.table(
    "role_permissions",
    sa.column("id", sa.Uuid(native_uuid=False)),
    sa.column("role_id", sa.Uuid(native_uuid=False)),
    sa.column("permission_id", sa.Uuid(native_uuid=False)),
    sa.column("created_at", sa.DateTime(timezone=True)),
)


def upgrade() -> None:
    bind = op.get_bind()
    now = datetime.now(UTC)

    permission_ids = {code: uuid.uuid4() for code in ALL_CODES}
    op.bulk_insert(
        permissions_table,
        [
            {"id": permission_ids[code], "code": code, "name": name, "module": module}
            for code, name, module in PERMISSIONS
        ],
    )

    role_ids: dict[str, uuid.UUID] = {}
    for role_name in ROLE_GRANTS:
        role_id = bind.execute(
            sa.select(roles_table.c.id).where(
                roles_table.c.name == role_name,
                roles_table.c.organization_id.is_(None),
                roles_table.c.is_system_role.is_(True),
            )
        ).scalar_one()
        role_ids[role_name] = role_id

    op.bulk_insert(
        role_permissions_table,
        [
            {
                "id": uuid.uuid4(),
                "role_id": role_ids[role_name],
                "permission_id": permission_ids[code],
                "created_at": now,
            }
            for role_name, codes in ROLE_GRANTS.items()
            for code in codes
        ],
    )


def downgrade() -> None:
    bind = op.get_bind()
    permission_ids = [
        row[0]
        for row in bind.execute(
            sa.select(permissions_table.c.id).where(permissions_table.c.code.in_(ALL_CODES))
        )
    ]
    op.execute(
        role_permissions_table.delete().where(role_permissions_table.c.permission_id.in_(permission_ids))
    )
    op.execute(permissions_table.delete().where(permissions_table.c.code.in_(ALL_CODES)))
