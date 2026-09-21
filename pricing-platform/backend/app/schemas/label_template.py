import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

# The color keys the pdf_label adapter knows how to apply. Keeping the
# allow-list here (and mirroring it in the service) means a template can
# never smuggle in an unknown key the adapter would silently ignore.
LABEL_COLOR_KEYS = frozenset(
    {"background", "border", "text", "banner", "unit_border", "sublabel", "placeholder"}
)

_HEX_RE = r"^#[0-9a-fA-F]{6}$"


class LabelTemplateBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    colors: dict[str, str] | None = None
    background_image_url: str | None = Field(default=None, max_length=500)

    @field_validator("colors")
    @classmethod
    def _validate_colors(cls, value: dict[str, str] | None) -> dict[str, str] | None:
        if not value:
            return value
        unknown = set(value) - LABEL_COLOR_KEYS
        if unknown:
            raise ValueError(f"Unknown label color key(s): {', '.join(sorted(unknown))}.")
        for key, hex_value in value.items():
            import re

            if not re.match(_HEX_RE, hex_value):
                raise ValueError(f"colors.{key} must be a 6-digit hex color (e.g. #FFFFFF).")
        return value


class LabelTemplateCreate(LabelTemplateBase):
    pass


class LabelTemplateUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    colors: dict[str, str] | None = None
    background_image_url: str | None = Field(default=None, max_length=500)

    @field_validator("colors")
    @classmethod
    def _validate_colors(cls, value: dict[str, str] | None) -> dict[str, str] | None:
        return LabelTemplateBase._validate_colors(value)


class LabelTemplateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    colors: dict[str, str] | None
    background_image_url: str | None
    created_at: datetime
    updated_at: datetime


class LabelTemplateListOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    colors: dict[str, str] | None
    background_image_url: str | None
    updated_at: datetime
