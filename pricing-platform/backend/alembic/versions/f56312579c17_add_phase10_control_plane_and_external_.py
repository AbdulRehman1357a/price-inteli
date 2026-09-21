"""add phase10 control plane tables

Revision ID: f56312579c17
Revises: a7f5c9e2b8d4
Create Date: 2026-09-15 17:43:12.623796

Part 1 of 2 for the Phase 10 (Enterprise Integration Hub) production
upgrade — control-plane tables (onboarding/config/audit) plus new columns
on the existing `integrations` table. Part 2
(<next revision>_add_phase10_external_staging_tables.py) adds the
external-ID-mapping staging tables and the additive columns on
integration_sync_jobs/integration_mappings. Split purely for
reviewability; both are safe to run back-to-back.

Hand-pruned from an autogenerate pass: the raw diff also proposed
dropping/recreating several composite indexes on unrelated tables
(ai_pricing_recommendations, analytics_snapshots, device_sync_logs,
inventory_adjustments, price_history) — pre-existing drift between those
models and the reflected schema, unrelated to this change — so those
operations are intentionally omitted here.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f56312579c17'
down_revision: Union[str, None] = 'a7f5c9e2b8d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('integration_locations',
    sa.Column('integration_id', sa.Uuid(native_uuid=False), nullable=False),
    sa.Column('store_id', sa.Uuid(native_uuid=False), nullable=True),
    sa.Column('external_location_id', sa.String(length=255), nullable=False),
    sa.Column('external_location_name', sa.String(length=255), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('discovered_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('linked_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', sa.Uuid(native_uuid=False), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['integration_id'], ['integrations.id'], ),
    sa.ForeignKeyConstraint(['store_id'], ['stores.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('integration_id', 'external_location_id', name='uq_integration_locations_integration_external')
    )
    op.create_index(op.f('ix_integration_locations_integration_id'), 'integration_locations', ['integration_id'], unique=False)
    op.create_index(op.f('ix_integration_locations_store_id'), 'integration_locations', ['store_id'], unique=False)

    op.create_table('integration_authorities',
    sa.Column('integration_id', sa.Uuid(native_uuid=False), nullable=False),
    sa.Column('entity_type', sa.Enum('PRODUCT', 'PRICE', 'INVENTORY', 'PROMOTION', 'STORE', 'ORDER', name='canonicalentitytype', native_enum=False, length=20), nullable=False),
    sa.Column('field_name', sa.String(length=100), nullable=False),
    sa.Column('authority', sa.Enum('PIP', 'EXTERNAL', name='authoritysource', native_enum=False, length=10), nullable=False),
    sa.Column('allow_override', sa.Boolean(), nullable=False),
    sa.Column('id', sa.Uuid(native_uuid=False), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['integration_id'], ['integrations.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('integration_id', 'entity_type', 'field_name', name='uq_integration_authorities_integration_entity_field')
    )
    op.create_index(op.f('ix_integration_authorities_integration_id'), 'integration_authorities', ['integration_id'], unique=False)

    op.create_table('integration_checkpoints',
    sa.Column('integration_id', sa.Uuid(native_uuid=False), nullable=False),
    sa.Column('entity_type', sa.Enum('PRODUCT', 'PRICE', 'INVENTORY', 'PROMOTION', 'STORE', 'ORDER', name='canonicalentitytype', native_enum=False, length=20), nullable=False),
    sa.Column('cursor_value', sa.String(length=500), nullable=True),
    sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', sa.Uuid(native_uuid=False), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['integration_id'], ['integrations.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('integration_id', 'entity_type', name='uq_integration_checkpoints_integration_entity')
    )
    op.create_index(op.f('ix_integration_checkpoints_integration_id'), 'integration_checkpoints', ['integration_id'], unique=False)

    op.create_table('integration_sync_schedules',
    sa.Column('integration_id', sa.Uuid(native_uuid=False), nullable=False),
    sa.Column('entity_type', sa.Enum('PRODUCT', 'PRICE', 'INVENTORY', 'PROMOTION', 'STORE', 'ORDER', name='canonicalentitytype', native_enum=False, length=20), nullable=False),
    sa.Column('job_type', sa.Enum('FULL_SYNC', 'INCREMENTAL_SYNC', name='integrationsyncjobtype', native_enum=False, length=20), nullable=False),
    sa.Column('interval_minutes', sa.Integer(), nullable=False),
    sa.Column('is_enabled', sa.Boolean(), nullable=False),
    sa.Column('next_run_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('last_dispatched_job_id', sa.Uuid(native_uuid=False), nullable=True),
    sa.Column('id', sa.Uuid(native_uuid=False), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['integration_id'], ['integrations.id'], ),
    sa.ForeignKeyConstraint(['last_dispatched_job_id'], ['integration_sync_jobs.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('integration_id', 'entity_type', name='uq_integration_sync_schedules_integration_entity')
    )
    op.create_index(op.f('ix_integration_sync_schedules_integration_id'), 'integration_sync_schedules', ['integration_id'], unique=False)

    op.create_table('integration_webhook_events',
    sa.Column('integration_id', sa.Uuid(native_uuid=False), nullable=False),
    sa.Column('provider_event_id', sa.String(length=255), nullable=False),
    sa.Column('entity_type', sa.Enum('PRODUCT', 'PRICE', 'INVENTORY', 'PROMOTION', 'STORE', 'ORDER', name='canonicalentitytype', native_enum=False, length=20), nullable=True),
    sa.Column('payload', sa.JSON(), nullable=False),
    sa.Column('signature_valid', sa.Boolean(), nullable=False),
    sa.Column('status', sa.Enum('RECEIVED', 'PROCESSING', 'PROCESSED', 'FAILED', 'DUPLICATE', name='integrationwebhookeventstatus', native_enum=False, length=20), nullable=False),
    sa.Column('sync_job_id', sa.Uuid(native_uuid=False), nullable=True),
    sa.Column('received_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('id', sa.Uuid(native_uuid=False), nullable=False),
    sa.ForeignKeyConstraint(['integration_id'], ['integrations.id'], ),
    sa.ForeignKeyConstraint(['sync_job_id'], ['integration_sync_jobs.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('integration_id', 'provider_event_id', name='uq_integration_webhook_events_integration_event')
    )
    op.create_index(op.f('ix_integration_webhook_events_integration_id'), 'integration_webhook_events', ['integration_id'], unique=False)

    op.create_table('integration_errors',
    sa.Column('integration_id', sa.Uuid(native_uuid=False), nullable=False),
    sa.Column('sync_job_id', sa.Uuid(native_uuid=False), nullable=True),
    sa.Column('error_type', sa.String(length=50), nullable=False),
    sa.Column('severity', sa.Enum('WARNING', 'ERROR', 'CRITICAL', name='integrationerrorseverity', native_enum=False, length=10), nullable=False),
    sa.Column('message', sa.Text(), nullable=False),
    sa.Column('context', sa.JSON(), nullable=True),
    sa.Column('is_resolved', sa.Boolean(), nullable=False),
    sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('resolved_by', sa.Uuid(native_uuid=False), nullable=True),
    sa.Column('id', sa.Uuid(native_uuid=False), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['integration_id'], ['integrations.id'], ),
    sa.ForeignKeyConstraint(['sync_job_id'], ['integration_sync_jobs.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_integration_errors_integration_id'), 'integration_errors', ['integration_id'], unique=False)
    op.create_index(op.f('ix_integration_errors_sync_job_id'), 'integration_errors', ['sync_job_id'], unique=False)

    op.create_table('integration_reconciliation',
    sa.Column('integration_id', sa.Uuid(native_uuid=False), nullable=False),
    sa.Column('entity_type', sa.Enum('PRODUCT', 'PRICE', 'INVENTORY', 'PROMOTION', 'STORE', 'ORDER', name='canonicalentitytype', native_enum=False, length=20), nullable=False),
    sa.Column('external_id', sa.String(length=255), nullable=False),
    sa.Column('field_name', sa.String(length=100), nullable=False),
    sa.Column('pip_value', sa.String(length=500), nullable=True),
    sa.Column('external_value', sa.String(length=500), nullable=True),
    sa.Column('authority_at_detection', sa.Enum('PIP', 'EXTERNAL', name='authoritysource', native_enum=False, length=10), nullable=False),
    sa.Column('status', sa.Enum('OPEN', 'RESOLVED_PIP_KEPT', 'RESOLVED_EXTERNAL_APPLIED', 'IGNORED', name='integrationreconciliationstatus', native_enum=False, length=30), nullable=False),
    sa.Column('detected_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('resolved_by', sa.Uuid(native_uuid=False), nullable=True),
    sa.Column('id', sa.Uuid(native_uuid=False), nullable=False),
    sa.ForeignKeyConstraint(['integration_id'], ['integrations.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_integration_reconciliation_integration_id'), 'integration_reconciliation', ['integration_id'], unique=False)

    op.add_column('integrations', sa.Column('provider_version', sa.String(length=50), nullable=True))
    op.add_column('integrations', sa.Column('environment', sa.Enum('SANDBOX', 'PRODUCTION', name='integrationenvironment', native_enum=False, length=20), server_default='PRODUCTION', nullable=False))
    op.add_column('integrations', sa.Column('base_url_display', sa.String(length=500), nullable=True))
    op.add_column('integrations', sa.Column('auth_type', sa.String(length=50), nullable=True))
    op.add_column('integrations', sa.Column('last_successful_connection_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('integrations', sa.Column('last_failed_connection_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('integrations', sa.Column('last_connection_error', sa.Text(), nullable=True))
    op.add_column('integrations', sa.Column('token_expires_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('integrations', sa.Column('webhook_secret_encrypted', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('integrations', 'webhook_secret_encrypted')
    op.drop_column('integrations', 'token_expires_at')
    op.drop_column('integrations', 'last_connection_error')
    op.drop_column('integrations', 'last_failed_connection_at')
    op.drop_column('integrations', 'last_successful_connection_at')
    op.drop_column('integrations', 'auth_type')
    op.drop_column('integrations', 'base_url_display')
    op.drop_column('integrations', 'environment')
    op.drop_column('integrations', 'provider_version')

    # MySQL/InnoDB refuses to drop an index still backing a foreign key
    # constraint, so tables (and their indexes) are dropped outright rather
    # than via individual drop_index calls, same precedent as d1a85ca1e66f.
    op.drop_table('integration_reconciliation')
    op.drop_table('integration_errors')
    op.drop_table('integration_webhook_events')
    op.drop_table('integration_sync_schedules')
    op.drop_table('integration_checkpoints')
    op.drop_table('integration_authorities')
    op.drop_table('integration_locations')
