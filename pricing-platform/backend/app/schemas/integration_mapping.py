import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.integration_mapping import CanonicalEntityType


class IntegrationMappingCreate(BaseModel):
    entity_type: CanonicalEntityType
    source_field: str = Field(min_length=1, max_length=255)
    canonical_field: str = Field(min_length=1, max_length=255)
    transformation_rule: str | None = Field(default=None, max_length=255)
    # --- Phase 10 upgrade: Field Mapping Engine table columns ---
    data_type: str | None = Field(default=None, max_length=30)
    required: bool = False
    default_value: str | None = Field(default=None, max_length=255)
    validation_rule: str | None = Field(default=None, max_length=255)


class IntegrationMappingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    integration_id: uuid.UUID
    entity_type: CanonicalEntityType
    source_field: str
    canonical_field: str
    transformation_rule: str | None
    data_type: str | None
    required: bool
    default_value: str | None
    validation_rule: str | None
    created_at: datetime
