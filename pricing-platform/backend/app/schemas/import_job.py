import enum
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.import_job import ImportEntityType, ImportFileType, ImportStatus


class ImportField(enum.StrEnum):
    """The 9 supported column mappings from the Phase 5 wizard spec, plus
    the 6 added for bulk user import (additive, not in the literal spec —
    same precedent as every other admin-requested field beyond a phase's
    literal list).
    """

    SKU = "sku"
    BARCODE = "barcode"
    PRODUCT_NAME = "product_name"
    CATEGORY = "category"
    COST_PRICE = "cost_price"
    SELLING_PRICE = "selling_price"
    QUANTITY = "quantity"
    REORDER_POINT = "reorder_point"
    STORE = "store"

    FIRST_NAME = "first_name"
    LAST_NAME = "last_name"
    EMAIL = "email"
    PASSWORD = "password"
    PHONE = "phone"
    ROLE = "role"


class ImportJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    store_id: uuid.UUID | None
    file_name: str
    file_type: ImportFileType
    entity_type: ImportEntityType
    status: ImportStatus
    total_rows: int | None
    success_rows: int
    failed_rows: int
    error_summary: str | None
    created_by: uuid.UUID | None
    created_at: datetime
    completed_at: datetime | None
    detected_columns: list[str] | None
    column_mapping: dict[str, str] | None


class ImportMappingRequest(BaseModel):
    """Step 3's submission: which detected file column feeds which
    supported field. Only SKU is universally required — the rest of the
    required-ness depends on entity_type (see ImportService.start_import).
    """

    mapping: dict[ImportField, str] = Field(min_length=1)


class ImportRowErrorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    import_job_id: uuid.UUID
    row_number: int
    field_name: str | None
    error_message: str
    raw_data: dict
    created_at: datetime


class ImportRowErrorListParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)


class ImportTemplateOut(BaseModel):
    """A generated .xlsx template for a given entity_type, base64-encoded.

    Returned inside the standard APIResponse envelope rather than as a raw
    file response — this codebase has no generic binary file-serving
    endpoint (see Phase 7's QR/PDF payloads), so the frontend decodes this
    into a data: URL and triggers the download itself, same pattern as the
    Output Job PDF/QR download links.
    """

    filename: str
    content_type: str
    content_base64: str
