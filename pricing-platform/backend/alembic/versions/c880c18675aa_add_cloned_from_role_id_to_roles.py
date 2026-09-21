"""add cloned_from_role_id to roles

Revision ID: c880c18675aa
Revises: 543415371808
Create Date: 2026-08-25 23:22:30.571080

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c880c18675aa'
down_revision: Union[str, None] = '543415371808'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('roles', sa.Column('cloned_from_role_id', sa.Uuid(native_uuid=False), nullable=True))
    op.create_index(op.f('ix_roles_cloned_from_role_id'), 'roles', ['cloned_from_role_id'], unique=False)
    op.create_foreign_key(
        'fk_roles_cloned_from_role_id', 'roles', 'roles', ['cloned_from_role_id'], ['id']
    )


def downgrade() -> None:
    op.drop_constraint('fk_roles_cloned_from_role_id', 'roles', type_='foreignkey')
    op.drop_index(op.f('ix_roles_cloned_from_role_id'), table_name='roles')
    op.drop_column('roles', 'cloned_from_role_id')
