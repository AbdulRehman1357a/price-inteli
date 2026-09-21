"""seed esl simulator vendor and model

Revision ID: 9c4e2a6f8d1b
Revises: 3a5f7c1e9b2d
Create Date: 2026-08-25 16:42:00.000000

Data-only migration. device_vendors/device_models are global platform
catalog data (no organization_id) — seeds the one vendor Phase 8 actually
implements an adapter for (app/integrations/esl_simulator/adapter.py),
selected via DeviceVendor.code, so the Device Form's Vendor/Model dropdowns
have something to select in a fresh database. Real hardware vendors are
out of scope for this phase ("Do not integrate physical hardware yet").
"""
import uuid
from datetime import UTC, datetime
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '9c4e2a6f8d1b'
down_revision: Union[str, None] = '3a5f7c1e9b2d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

VENDOR_ID = uuid.uuid4()
MODEL_ID = uuid.uuid4()

device_vendors_table = sa.table(
    "device_vendors",
    sa.column("id", sa.Uuid(native_uuid=False)),
    sa.column("name", sa.String(length=255)),
    sa.column("code", sa.String(length=50)),
    sa.column("website", sa.String(length=500)),
    sa.column("status", sa.String(length=20)),
    sa.column("created_at", sa.DateTime(timezone=True)),
    sa.column("updated_at", sa.DateTime(timezone=True)),
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
    now = datetime.now(UTC)
    op.bulk_insert(
        device_vendors_table,
        [
            {
                "id": VENDOR_ID,
                "name": "ESL Simulator",
                "code": "esl_simulator",
                "website": None,
                "status": "ACTIVE",
                "created_at": now,
                "updated_at": now,
            }
        ],
    )
    op.bulk_insert(
        device_models_table,
        [
            {
                "id": MODEL_ID,
                "vendor_id": VENDOR_ID,
                "name": "Generic Simulator Display",
                "model_code": "SIM-1",
                "screen_size": "2.9in",
                "resolution": "296x128",
                "color_capabilities": {"colors": ["black", "white", "red"]},
                "battery_type": "CR2450",
                "communication_type": "mqtt",
                "status": "ACTIVE",
                "created_at": now,
                "updated_at": now,
            }
        ],
    )


def downgrade() -> None:
    op.execute(device_models_table.delete().where(device_models_table.c.id == MODEL_ID))
    op.execute(device_vendors_table.delete().where(device_vendors_table.c.id == VENDOR_ID))
