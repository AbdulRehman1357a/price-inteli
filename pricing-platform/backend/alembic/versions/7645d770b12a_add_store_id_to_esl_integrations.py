"""add store_id to esl_integrations

Revision ID: 7645d770b12a
Revises: c94e7a2d5f19
Create Date: 2026-09-17 17:25:17.360302

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '7645d770b12a'
down_revision: Union[str, None] = 'c94e7a2d5f19'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('esl_integrations', sa.Column('store_id', sa.Uuid(native_uuid=False), nullable=True))
    op.create_index(op.f('ix_esl_integrations_store_id'), 'esl_integrations', ['store_id'], unique=False)
    op.create_foreign_key(
        'fk_esl_integrations_store_id', 'esl_integrations', 'stores', ['store_id'], ['id']
    )


def downgrade() -> None:
    # MySQL requires an explicit constraint name to drop a foreign key, and
    # refuses to drop a column still backing one — the FK is dropped first,
    # same precedent as 63501503a51e.
    op.drop_constraint('fk_esl_integrations_store_id', 'esl_integrations', type_='foreignkey')
    op.drop_index(op.f('ix_esl_integrations_store_id'), table_name='esl_integrations')
    op.drop_column('esl_integrations', 'store_id')
