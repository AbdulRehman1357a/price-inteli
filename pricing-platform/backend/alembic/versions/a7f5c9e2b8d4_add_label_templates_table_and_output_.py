"""add label_templates table and output_channels label_template_id

Revision ID: a7f5c9e2b8d4
Revises: 790934a4508d
Create Date: 2026-09-07 10:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a7f5c9e2b8d4'
down_revision: Union[str, None] = '790934a4508d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'label_templates',
        sa.Column('organization_id', sa.Uuid(native_uuid=False), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('colors', sa.JSON(), nullable=True),
        sa.Column('background_image_url', sa.String(length=500), nullable=True),
        sa.Column('id', sa.Uuid(native_uuid=False), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_label_templates_organization_id'), 'label_templates', ['organization_id'], unique=False)
    op.add_column(
        'output_channels',
        sa.Column(
            'label_template_id',
            sa.Uuid(native_uuid=False),
            sa.ForeignKey('label_templates.id', ondelete='SET NULL'),
            nullable=True,
        ),
    )
    op.create_index(op.f('ix_output_channels_label_template_id'), 'output_channels', ['label_template_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_output_channels_label_template_id'), table_name='output_channels')
    op.drop_column('output_channels', 'label_template_id')
    op.drop_table('label_templates')