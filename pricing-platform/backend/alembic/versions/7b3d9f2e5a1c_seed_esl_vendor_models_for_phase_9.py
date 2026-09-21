"""seed esl vendor models for phase 9

Revision ID: 7b3d9f2e5a1c
Revises: 5e8b1f4a2c7d
Create Date: 2026-08-25 17:46:00.000000

Data-only migration. Adds one placeholder DeviceModel per vendor seeded in
5e8b1f4a2c7d, so the Integration Setup Wizard's "Import Devices" step
(which requires picking a device_model_id) has something to select
regardless of which vendor was chosen in Step 1 — these are generic
placeholders, not real vendor hardware specs, since no partner catalog
data is available for the five stub vendors (see vendor_stubs.py).
"""
import uuid
from datetime import UTC, datetime
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '7b3d9f2e5a1c'
down_revision: Union[str, None] = '5e8b1f4a2c7d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

VENDOR_CODES = ["mock", "vusion", "hanshow", "solum", "pricer", "zkong"]

device_vendors_table = sa.table(
    "device_vendors",
    sa.column("id", sa.Uuid(native_uuid=False)),
    sa.column("code", sa.String(length=50)),
)

device_models_table = sa.table(
    "device_models",
    sa.column("id", sa.Uuid(native_uuid=False)),
    sa.column("vendor_id", sa.Uuid(native_uuid=False)),
    sa.column("name", sa.String(length=255)),
    sa.column("model_code", sa.String(length=100)),
    sa.column("screen_size", sa.String(length=50)),
    sa.column("resolution", sa.String(length=50)),
    sa.column("color_capabilities", sa.JSON()),
    sa.column("battery_type", sa.String(length=50)),
    sa.column("communication_type", sa.String(length=50)),
    sa.column("status", sa.String(length=20)),
    sa.column("created_at", sa.DateTime(timezone=True)),
    sa.column("updated_at", sa.DateTime(timezone=True)),
)


def upgrade() -> None:
    bind = op.get_bind()
    now = datetime.now(UTC)

    vendor_ids = {
        row[1]: row[0]
        for row in bind.execute(
            sa.select(device_vendors_table.c.id, device_vendors_table.c.code).where(
                device_vendors_table.c.code.in_(VENDOR_CODES)
            )
        )
    }

    op.bulk_insert(
        device_models_table,
        [
            {
                "id": uuid.uuid4(),
                "vendor_id": vendor_ids[code],
                "name": "Generic Placeholder Display",
                "model_code": "PLACEHOLDER-1",
                "screen_size": None,
                "resolution": None,
                "color_capabilities": None,
                "battery_type": None,
                "communication_type": "mock" if code == "mock" else "api",
                "status": "ACTIVE",
                "created_at": now,
                "updated_at": now,
            }
            for code in VENDOR_CODES
        ],
    )


def downgrade() -> None:
    bind = op.get_bind()
    vendor_ids = [
        row[0]
        for row in bind.execute(
            sa.select(device_vendors_table.c.id).where(device_vendors_table.c.code.in_(VENDOR_CODES))
        )
    ]
    op.execute(device_models_table.delete().where(device_models_table.c.vendor_id.in_(vendor_ids)))
