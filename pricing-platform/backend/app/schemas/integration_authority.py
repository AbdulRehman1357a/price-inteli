import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.integration_authority import AuthoritySource
from app.models.integration_mapping import CanonicalEntityType


class IntegrationAuthorityCreate(BaseModel):
    entity_type: CanonicalEntityType
    field_name: str = Field(min_length=1, max_length=100)
    authority: AuthoritySource
    allow_override: bool = False


class IntegrationAuthorityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    integration_id: uuid.UUID
    entity_type: CanonicalEntityType
    field_name: str
    authority: AuthoritySource
    allow_override: bool
    created_at: datetime
