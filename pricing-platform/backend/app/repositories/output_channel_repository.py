import uuid

from sqlalchemy import func, or_, select

from app.models.output_channel import OutputChannel, OutputChannelStatus, OutputType
from app.repositories.base import BaseRepository


class OutputChannelRepository(BaseRepository[OutputChannel]):
    model = OutputChannel

    def get_by_id_for_organization(
        self, channel_id: uuid.UUID, organization_id: uuid.UUID
    ) -> OutputChannel | None:
        stmt = select(OutputChannel).where(
            OutputChannel.id == channel_id, OutputChannel.organization_id == organization_id
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_active_by_type(
        self, organization_id: uuid.UUID, *, output_type: OutputType, store_id: uuid.UUID | None
    ) -> list[OutputChannel]:
        """Active channels of this type that a given store's price change can
        target: organization-wide channels (store_id IS NULL) plus any
        channel scoped to this exact store.
        """
        conditions = [
            OutputChannel.organization_id == organization_id,
            OutputChannel.output_type == output_type,
            OutputChannel.status == OutputChannelStatus.ACTIVE,
        ]
        if store_id is not None:
            conditions.append(or_(OutputChannel.store_id.is_(None), OutputChannel.store_id == store_id))
        else:
            conditions.append(OutputChannel.store_id.is_(None))
        stmt = select(OutputChannel).where(*conditions)
        return list(self.db.execute(stmt).scalars().all())

    def search(
        self,
        organization_id: uuid.UUID,
        *,
        output_type: OutputType | None = None,
        store_id: uuid.UUID | None = None,
        status: OutputChannelStatus | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[OutputChannel], int]:
        conditions = [OutputChannel.organization_id == organization_id]
        if output_type is not None:
            conditions.append(OutputChannel.output_type == output_type)
        if store_id is not None:
            conditions.append(OutputChannel.store_id == store_id)
        if status is not None:
            conditions.append(OutputChannel.status == status)

        base_stmt = select(OutputChannel).where(*conditions)
        total = self.db.execute(select(func.count()).select_from(base_stmt.subquery())).scalar_one()
        items = list(
            self.db.execute(
                base_stmt.order_by(OutputChannel.created_at.desc()).offset(offset).limit(limit)
            )
            .scalars()
            .all()
        )
        return items, total
