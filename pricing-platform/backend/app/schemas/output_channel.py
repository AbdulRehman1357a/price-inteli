import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.output_channel import OutputChannelStatus, OutputType
from app.schemas.common import PaginationParams


class OutputChannelBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    output_type: OutputType
    store_id: uuid.UUID | None = None
    label_template_id: uuid.UUID | None = None
    configuration: dict[str, Any] | None = None
    status: OutputChannelStatus = OutputChannelStatus.ACTIVE


class OutputChannelCreate(OutputChannelBase):
    pass


class OutputChannelUpdate(BaseModel):
    """output_type is deliberately not updatable — it determines which
    adapter/configuration schema applies, so changing it is really creating
    a different channel, not editing this one.
    """

    name: str | None = Field(default=None, min_length=1, max_length=255)
    store_id: uuid.UUID | None = None
    label_template_id: uuid.UUID | None = None
    configuration: dict[str, Any] | None = None
    status: OutputChannelStatus | None = None


class OutputChannelOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    store_id: uuid.UUID | None
    label_template_id: uuid.UUID | None
    name: str
    output_type: OutputType
    configuration: dict[str, Any] | None
    status: OutputChannelStatus
    created_at: datetime
    updated_at: datetime


class OutputChannelListParams(PaginationParams):
    output_type: OutputType | None = None
    store_id: uuid.UUID | None = None
    status: OutputChannelStatus | None = None
