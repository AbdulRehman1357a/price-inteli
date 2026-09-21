import uuid

from pydantic import BaseModel, Field


class IntegrationPricePushRequest(BaseModel):
    price_ids: list[uuid.UUID] = Field(min_length=1)
