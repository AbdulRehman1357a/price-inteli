"""add phase10 external staging tables

Revision ID: b3a9d4e71f28
Revises: f56312579c17
Create Date: 2026-09-15 17:45:00.000000

Part 2 of 2 for the Phase 10 (Enterprise Integration Hub) production
upgrade — the six external-ID-mapping staging tables
(external_products/stores/inventory/prices/orders/promotions), plus the
additive columns on integration_sync_jobs (direction, records_created/
updated/skipped, retry_count, correlation_id, error_type) and
integration_mappings (data_type, required, default_value,
validation_rule). See f56312579c17 for part 1 (control-plane tables).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b3a9d4e71f28'
down_revision: Union[str, None] = 'f56312579c17'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('external_products',
    sa.Column('integration_id', sa.Uuid(native_uuid=False), nullable=False),
    sa.Column('external_id', sa.String(length=255), nullable=False),
    sa.Column('external_variant_id', sa.String(length=255), nullable=True),
    sa.Column('sku', sa.String(length=100), nullable=False),
    sa.Column('product_id', sa.Uuid(native_uuid=False), nullable=True),
    sa.Column('raw_payload', sa.JSON(), nullable=True),
    sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('id', sa.Uuid(native_uuid=False), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['integration_id'], ['integrations.id'], ),
    sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('integration_id', 'external_id', name='uq_external_products_integration_external')
    )
    op.create_index(op.f('ix_external_products_integration_id'), 'external_products', ['integration_id'], unique=False)
    op.create_index(op.f('ix_external_products_product_id'), 'external_products', ['product_id'], unique=False)
    op.create_index(op.f('ix_external_products_sku'), 'external_products', ['sku'], unique=False)

    op.create_table('external_stores',
    sa.Column('integration_id', sa.Uuid(native_uuid=False), nullable=False),
    sa.Column('external_id', sa.String(length=255), nullable=False),
    sa.Column('store_id', sa.Uuid(native_uuid=False), nullable=True),
    sa.Column('store_code', sa.String(length=100), nullable=False),
    sa.Column('raw_payload', sa.JSON(), nullable=True),
    sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('id', sa.Uuid(native_uuid=False), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['integration_id'], ['integrations.id'], ),
    sa.ForeignKeyConstraint(['store_id'], ['stores.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('integration_id', 'external_id', name='uq_external_stores_integration_external')
    )
    op.create_index(op.f('ix_external_stores_integration_id'), 'external_stores', ['integration_id'], unique=False)
    op.create_index(op.f('ix_external_stores_store_code'), 'external_stores', ['store_code'], unique=False)
    op.create_index(op.f('ix_external_stores_store_id'), 'external_stores', ['store_id'], unique=False)

    op.create_table('external_inventory',
    sa.Column('integration_id', sa.Uuid(native_uuid=False), nullable=False),
    sa.Column('external_id', sa.String(length=255), nullable=True),
    sa.Column('sku', sa.String(length=100), nullable=False),
    sa.Column('store_code', sa.String(length=100), nullable=False),
    sa.Column('inventory_id', sa.Uuid(native_uuid=False), nullable=True),
    sa.Column('quantity_on_hand', sa.Numeric(precision=14, scale=4), nullable=True),
    sa.Column('raw_payload', sa.JSON(), nullable=True),
    sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('id', sa.Uuid(native_uuid=False), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['integration_id'], ['integrations.id'], ),
    sa.ForeignKeyConstraint(['inventory_id'], ['inventory.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('integration_id', 'sku', 'store_code', name='uq_external_inventory_integration_sku_store')
    )
    op.create_index(op.f('ix_external_inventory_integration_id'), 'external_inventory', ['integration_id'], unique=False)
    op.create_index(op.f('ix_external_inventory_inventory_id'), 'external_inventory', ['inventory_id'], unique=False)
    op.create_index(op.f('ix_external_inventory_sku'), 'external_inventory', ['sku'], unique=False)
    op.create_index(op.f('ix_external_inventory_store_code'), 'external_inventory', ['store_code'], unique=False)

    op.create_table('external_prices',
    sa.Column('integration_id', sa.Uuid(native_uuid=False), nullable=False),
    sa.Column('sku', sa.String(length=100), nullable=False),
    sa.Column('store_code', sa.String(length=100), nullable=True),
    sa.Column('price_id', sa.Uuid(native_uuid=False), nullable=True),
    sa.Column('external_selling_price', sa.Numeric(precision=14, scale=4), nullable=True),
    sa.Column('currency', sa.String(length=10), nullable=True),
    sa.Column('direction', sa.Enum('INBOUND', 'OUTBOUND', name='integrationsyncdirection', native_enum=False, length=10), nullable=False),
    sa.Column('raw_payload', sa.JSON(), nullable=True),
    sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('id', sa.Uuid(native_uuid=False), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['integration_id'], ['integrations.id'], ),
    sa.ForeignKeyConstraint(['price_id'], ['prices.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('integration_id', 'sku', 'store_code', name='uq_external_prices_integration_sku_store')
    )
    op.create_index(op.f('ix_external_prices_integration_id'), 'external_prices', ['integration_id'], unique=False)
    op.create_index(op.f('ix_external_prices_price_id'), 'external_prices', ['price_id'], unique=False)
    op.create_index(op.f('ix_external_prices_sku'), 'external_prices', ['sku'], unique=False)
    op.create_index(op.f('ix_external_prices_store_code'), 'external_prices', ['store_code'], unique=False)

    op.create_table('external_orders',
    sa.Column('integration_id', sa.Uuid(native_uuid=False), nullable=False),
    sa.Column('external_order_id', sa.String(length=255), nullable=False),
    sa.Column('store_code', sa.String(length=100), nullable=True),
    sa.Column('order_date', sa.DateTime(timezone=True), nullable=True),
    sa.Column('status', sa.String(length=50), nullable=True),
    sa.Column('currency', sa.String(length=10), nullable=True),
    sa.Column('subtotal', sa.Numeric(precision=14, scale=4), nullable=True),
    sa.Column('tax_total', sa.Numeric(precision=14, scale=4), nullable=True),
    sa.Column('total', sa.Numeric(precision=14, scale=4), nullable=True),
    sa.Column('line_items', sa.JSON(), nullable=False),
    sa.Column('raw_payload', sa.JSON(), nullable=True),
    sa.Column('synced_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('id', sa.Uuid(native_uuid=False), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['integration_id'], ['integrations.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('integration_id', 'external_order_id', name='uq_external_orders_integration_external_order')
    )
    op.create_index(op.f('ix_external_orders_integration_id'), 'external_orders', ['integration_id'], unique=False)

    op.create_table('external_promotions',
    sa.Column('integration_id', sa.Uuid(native_uuid=False), nullable=False),
    sa.Column('external_promotion_id', sa.String(length=255), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('sku', sa.String(length=100), nullable=True),
    sa.Column('discount_percentage', sa.Numeric(precision=6, scale=3), nullable=True),
    sa.Column('discount_amount', sa.Numeric(precision=14, scale=4), nullable=True),
    sa.Column('start_date', sa.DateTime(timezone=True), nullable=True),
    sa.Column('end_date', sa.DateTime(timezone=True), nullable=True),
    sa.Column('status', sa.Enum('PENDING', 'ACTIVE', 'EXPIRED', 'CANCELLED', name='externalpromotionstatus', native_enum=False, length=20), nullable=False),
    sa.Column('raw_payload', sa.JSON(), nullable=True),
    sa.Column('synced_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('id', sa.Uuid(native_uuid=False), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['integration_id'], ['integrations.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('integration_id', 'external_promotion_id', name='uq_external_promotions_integration_external_promo')
    )
    op.create_index(op.f('ix_external_promotions_integration_id'), 'external_promotions', ['integration_id'], unique=False)

    op.add_column('integration_sync_jobs', sa.Column('direction', sa.Enum('INBOUND', 'OUTBOUND', name='integrationsyncdirection', native_enum=False, length=10), server_default='INBOUND', nullable=False))
    op.add_column('integration_sync_jobs', sa.Column('records_created', sa.Integer(), server_default='0', nullable=False))
    op.add_column('integration_sync_jobs', sa.Column('records_updated', sa.Integer(), server_default='0', nullable=False))
    op.add_column('integration_sync_jobs', sa.Column('records_skipped', sa.Integer(), server_default='0', nullable=False))
    op.add_column('integration_sync_jobs', sa.Column('retry_count', sa.Integer(), server_default='0', nullable=False))
    op.add_column('integration_sync_jobs', sa.Column('correlation_id', sa.Uuid(native_uuid=False), nullable=True))
    op.add_column('integration_sync_jobs', sa.Column('error_type', sa.String(length=50), nullable=True))
    op.create_index(op.f('ix_integration_sync_jobs_correlation_id'), 'integration_sync_jobs', ['correlation_id'], unique=False)

    op.add_column('integration_mappings', sa.Column('data_type', sa.String(length=30), nullable=True))
    op.add_column('integration_mappings', sa.Column('required', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    op.add_column('integration_mappings', sa.Column('default_value', sa.String(length=255), nullable=True))
    op.add_column('integration_mappings', sa.Column('validation_rule', sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column('integration_mappings', 'validation_rule')
    op.drop_column('integration_mappings', 'default_value')
    op.drop_column('integration_mappings', 'required')
    op.drop_column('integration_mappings', 'data_type')

    op.drop_index(op.f('ix_integration_sync_jobs_correlation_id'), table_name='integration_sync_jobs')
    op.drop_column('integration_sync_jobs', 'error_type')
    op.drop_column('integration_sync_jobs', 'correlation_id')
    op.drop_column('integration_sync_jobs', 'retry_count')
    op.drop_column('integration_sync_jobs', 'records_skipped')
    op.drop_column('integration_sync_jobs', 'records_updated')
    op.drop_column('integration_sync_jobs', 'records_created')
    op.drop_column('integration_sync_jobs', 'direction')

    # MySQL/InnoDB refuses to drop an index still backing a foreign key
    # constraint, so tables are dropped outright, same precedent as
    # d1a85ca1e66f and f56312579c17.
    op.drop_table('external_promotions')
    op.drop_table('external_orders')
    op.drop_table('external_prices')
    op.drop_table('external_inventory')
    op.drop_table('external_stores')
    op.drop_table('external_products')
