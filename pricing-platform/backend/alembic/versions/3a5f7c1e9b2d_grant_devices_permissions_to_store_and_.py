"""grant devices permissions to store and inventory managers

Revision ID: 3a5f7c1e9b2d
Revises: 84c22ab0df4a
Create Date: 2026-08-25 16:40:00.000000

Data-only migration. devices.read/devices.create/devices.update/
devices.manage were already seeded in eaa27d8a5e16 (Phase 1) but only
granted to Super Admin/Organization Admin (full) and Viewer (read-only,
via the ".read"-suffix convention). Phase 8 makes the devices module real,
so Store Manager (operates the store's physical/simulated devices) gains
read+manage, and Inventory Manager gains read-only visibility — same
pattern as 7f2a4c9d1e3b granting Store Manager outputs.read/outputs.manage.
No new Permission rows here, only new RolePermission grants.
"""
import uuid
from datetime import UTC, datetime
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '3a5f7c1e9b2d'
down_revision: Union[str, None] = '84c22ab0df4a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

GRANTS: dict[str, list[str]] = {
    "Store Manager": ["devices.read", "devices.manage"],
    "Inventory Manager": ["devices.read"],
}

permissions_table = sa.table(
    "permissions",
    sa.column("id", sa.Uuid(native_uuid=False)),
    sa.column("code", sa.String(length=150)),
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

    all_codes = sorted({code for codes in GRANTS.values() for code in codes})
    permission_ids: dict[str, uuid.UUID] = {
        row[1]: row[0]
        for row in bind.execute(
            sa.select(permissions_table.c.id, permissions_table.c.code).where(
                permissions_table.c.code.in_(all_codes)
            )
        )
    }

    role_ids: dict[str, uuid.UUID] = {}
    for role_name in GRANTS:
        role_ids[role_name] = bind.execute(
            sa.select(roles_table.c.id).where(
                roles_table.c.name == role_name,
                roles_table.c.organization_id.is_(None),
                roles_table.c.is_system_role.is_(True),
            )
        ).scalar_one()

    op.bulk_insert(
        role_permissions_table,
        [
            {
                "id": uuid.uuid4(),
                "role_id": role_ids[role_name],
                "permission_id": permission_ids[code],
                "created_at": now,
            }
            for role_name, codes in GRANTS.items()
            for code in codes
        ],
    )


def downgrade() -> None:
    bind = op.get_bind()
    all_codes = sorted({code for codes in GRANTS.values() for code in codes})
    permission_ids = [
        row[0]
        for row in bind.execute(
            sa.select(permissions_table.c.id).where(permissions_table.c.code.in_(all_codes))
        )
    ]
    role_ids = [
        row[0]
        for row in bind.execute(
            sa.select(roles_table.c.id).where(roles_table.c.name.in_(list(GRANTS)))
        )
    ]
    op.execute(
        role_permissions_table.delete().where(
            role_permissions_table.c.permission_id.in_(permission_ids),
            role_permissions_table.c.role_id.in_(role_ids),
        )
    )
