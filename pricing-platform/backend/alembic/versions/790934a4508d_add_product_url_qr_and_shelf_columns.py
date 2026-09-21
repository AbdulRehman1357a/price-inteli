"""add product url qr and shelf columns

Revision ID: 790934a4508d
Revises: e6a94367f581
Create Date: 2026-09-07 00:59:41.582683

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '790934a4508d'
down_revision: Union[str, None] = 'e6a94367f581'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("products", sa.Column("product_url", sa.String(500), nullable=True))
    op.add_column("products", sa.Column("qr_id", sa.String(150), nullable=True))
    op.add_column("products", sa.Column("shelf_id", sa.String(150), nullable=True))


def downgrade() -> None:
    op.drop_column("products", "shelf_id")
    op.drop_column("products", "qr_id")
    op.drop_column("products", "product_url")
