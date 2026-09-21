import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.models.integration_authority import AuthoritySource
from app.models.integration_mapping import CanonicalEntityType
from app.models.integration_reconciliation import IntegrationReconciliationStatus
from app.schemas.common import PaginationParams


class IntegrationReconciliationListParams(PaginationParams):
    status: IntegrationReconciliationStatus | None = None


class IntegrationReconciliationRunRequest(BaseModel):
    entity_type: CanonicalEntityType


class IntegrationReconciliationResolveRequest(BaseModel):
    resolution: Literal["keep_pip", "apply_external"]


class IntegrationReconciliationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    integration_id: uuid.UUID
    entity_type: CanonicalEntityType
    external_id: str
    field_name: str
    pip_value: str | None
    external_value: str | None
    authority_at_detection: AuthoritySource
    status: IntegrationReconciliationStatus
    detected_at: datetime
    resolved_at: datetime | None
    resolved_by: uuid.UUID | None
