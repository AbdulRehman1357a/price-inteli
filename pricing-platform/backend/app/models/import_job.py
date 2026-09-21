import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import CreatedAtMixin, UUIDPrimaryKeyMixin


class ImportFileType(enum.StrEnum):
    CSV = "csv"
    XLSX = "xlsx"


class ImportEntityType(enum.StrEnum):
    PRODUCTS = "products"
    INVENTORY = "inventory"
    USERS = "users"


class ImportStatus(enum.StrEnum):
    UPLOADED = "uploaded"  # file stored, columns detected, waiting for column mapping
    QUEUED = "queued"  # mapping submitted, dispatched to the background worker
    PROCESSING = "processing"
    COMPLETED = "completed"
    COMPLETED_WITH_ERRORS = "completed_with_errors"
    FAILED = "failed"  # couldn't even be parsed/processed (not row-level errors)


class ImportJob(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """A bulk import of products or inventory from an uploaded CSV/XLSX file.

    detected_columns and column_mapping are not in the Phase 5 DB spec, but
    are required for the wizard to function: detected_columns is the parsed
    header row (Step 2's "preview detected columns"), and column_mapping is
    where Step 3's "map columns" submission is persisted so the background
    worker — which may run in a separate process, possibly after a restart
    — knows how to interpret each row.
    """

    __tablename__ = "import_jobs"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("organizations.id"), nullable=False, index=True
    )
    store_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("stores.id"), nullable=True
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[ImportFileType] = mapped_column(
        Enum(ImportFileType, native_enum=False, length=10), nullable=False
    )
    file_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    entity_type: Mapped[ImportEntityType] = mapped_column(
        Enum(ImportEntityType, native_enum=False, length=20), nullable=False
    )
    status: Mapped[ImportStatus] = mapped_column(
        Enum(ImportStatus, native_enum=False, length=30), nullable=False, default=ImportStatus.UPLOADED
    )
    total_rows: Mapped[int | None] = mapped_column(Integer, nullable=True)
    success_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("users.id"), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    detected_columns: Mapped[list | None] = mapped_column(JSON, nullable=True)
    column_mapping: Mapped[dict | None] = mapped_column(JSON, nullable=True)
