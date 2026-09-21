"""seed esl vendor catalog for phase 9

Revision ID: 5e8b1f4a2c7d
Revises: 63501503a51e
Create Date: 2026-08-25 17:42:00.000000

Data-only migration. device_vendors is global platform catalog data
(no organization_id — see 9c4e2a6f8d1b). Adds a "Mock Vendor" entry (so the
Integration Setup Wizard is fully exercisable end-to-end without a real
vendor account or MQTT broker — app/integrations/esl/mock_adapter.py) and
one catalog entry per vendor Phase 9 says the plugin framework must be
"ready for": Vusion, Hanshow, SOLUM, Pricer, ZKong. Each currently
resolves to a stub adapter (app/integrations/esl/vendor_stubs.py) that
fails every call with an explicit "not available" message — selecting one
of these vendors is not a claim of real integration, per the Phase 9 spec:
"Do not claim integration with a vendor unless an actual supported
API/SDK/partner integration is available."
"""
import uuid
from datetime import UTC, datetime
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '5e8b1f4a2c7d'
down_revision: Union[str, None] = '63501503a51e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

VENDORS: list[tuple[str, str, str | None]] = [
    ("Mock Vendor (Testing)", "mock", None),
    ("Vusion", "vusion", "https://www.vusion.com"),
    ("Hanshow", "hanshow", "https://www.hanshow.com"),
    ("SOLUM", "solum", "https://www.solumesl.com"),
    ("Pricer", "pricer", "https://www.pricer.com"),
    ("ZKong", "zkong", "https://www.zkong.com"),
]

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


def upgrade() -> None:
    now = datetime.now(UTC)
    op.bulk_insert(
        device_vendors_table,
        [
            {
                "id": uuid.uuid4(),
                "name": name,
                "code": code,
                "website": website,
                "status": "ACTIVE",
                "created_at": now,
                "updated_at": now,
            }
            for name, code, website in VENDORS
        ],
    )


def downgrade() -> None:
    codes = [code for _, code, _ in VENDORS]
    op.execute(device_vendors_table.delete().where(device_vendors_table.c.code.in_(codes)))
