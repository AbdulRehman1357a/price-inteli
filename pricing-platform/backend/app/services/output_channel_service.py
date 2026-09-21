import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.output_channel import OutputChannel
from app.outputs.registry import get_output_adapter
from app.repositories.label_template_repository import LabelTemplateRepository
from app.repositories.output_channel_repository import OutputChannelRepository
from app.repositories.store_repository import StoreRepository
from app.schemas.output_channel import OutputChannelCreate, OutputChannelListParams, OutputChannelUpdate


def _validate_store(db: Session, *, organization_id: uuid.UUID, store_id: uuid.UUID | None) -> None:
    if store_id is None:
        return
    if StoreRepository(db).get_by_id_for_organization(store_id, organization_id) is None:
        raise NotFoundError("Store not found.", code="store_not_found")


def _validate_label_template(
    db: Session, *, organization_id: uuid.UUID, label_template_id: uuid.UUID | None
) -> None:
    if label_template_id is None:
        return
    if LabelTemplateRepository(db).get_by_id_for_organization(label_template_id, organization_id) is None:
        raise NotFoundError("Label template not found.", code="label_template_not_found")


def create_channel(db: Session, *, organization_id: uuid.UUID, payload: OutputChannelCreate) -> OutputChannel:
    _validate_store(db, organization_id=organization_id, store_id=payload.store_id)
    _validate_label_template(
        db, organization_id=organization_id, label_template_id=payload.label_template_id
    )
    adapter = get_output_adapter(payload.output_type)
    adapter.validate_configuration(payload.configuration or {})

    channel = OutputChannel(
        id=uuid.uuid4(),
        organization_id=organization_id,
        store_id=payload.store_id,
        label_template_id=payload.label_template_id,
        name=payload.name,
        output_type=payload.output_type,
        configuration=payload.configuration,
        status=payload.status,
    )
    return OutputChannelRepository(db).add(channel)


def get_channel(db: Session, *, organization_id: uuid.UUID, channel_id: uuid.UUID) -> OutputChannel:
    channel = OutputChannelRepository(db).get_by_id_for_organization(channel_id, organization_id)
    if channel is None:
        raise NotFoundError("Output channel not found.", code="output_channel_not_found")
    return channel


def list_channels(
    db: Session, *, organization_id: uuid.UUID, params: OutputChannelListParams
) -> tuple[list[OutputChannel], int]:
    offset = (params.page - 1) * params.page_size
    return OutputChannelRepository(db).search(
        organization_id,
        output_type=params.output_type,
        store_id=params.store_id,
        status=params.status,
        offset=offset,
        limit=params.page_size,
    )


def update_channel(
    db: Session, *, organization_id: uuid.UUID, channel_id: uuid.UUID, payload: OutputChannelUpdate
) -> OutputChannel:
    channel = get_channel(db, organization_id=organization_id, channel_id=channel_id)
    data = payload.model_dump(exclude_unset=True)

    if "store_id" in data:
        _validate_store(db, organization_id=organization_id, store_id=data["store_id"])
        channel.store_id = data["store_id"]
    if "label_template_id" in data:
        _validate_label_template(
            db, organization_id=organization_id, label_template_id=data["label_template_id"]
        )
        channel.label_template_id = data["label_template_id"]
    if "configuration" in data:
        adapter = get_output_adapter(channel.output_type)
        adapter.validate_configuration(data["configuration"] or {})
        channel.configuration = data["configuration"]
    if "name" in data:
        channel.name = data["name"]
    if "status" in data:
        channel.status = data["status"]

    return OutputChannelRepository(db).add(channel)
