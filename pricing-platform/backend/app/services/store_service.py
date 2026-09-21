import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.store import Store
from app.repositories.store_repository import StoreRepository
from app.schemas.store import StoreCreate, StoreListParams, StoreUpdate


def create_store(db: Session, *, organization_id: uuid.UUID, payload: StoreCreate) -> Store:
    repo = StoreRepository(db)
    if repo.get_by_code(organization_id, payload.store_code) is not None:
        raise ConflictError("A store with this store_code already exists.", code="store_code_taken")

    store = Store(id=uuid.uuid4(), organization_id=organization_id, **payload.model_dump())
    return repo.add(store)


def get_store(db: Session, *, organization_id: uuid.UUID, store_id: uuid.UUID) -> Store:
    store = StoreRepository(db).get_by_id_for_organization(store_id, organization_id)
    if store is None:
        raise NotFoundError("Store not found.", code="store_not_found")
    return store


def list_stores(
    db: Session, *, organization_id: uuid.UUID, params: StoreListParams
) -> tuple[list[Store], int]:
    repo = StoreRepository(db)
    offset = (params.page - 1) * params.page_size
    return repo.search(
        organization_id,
        search=params.search,
        status=params.status,
        store_type=params.store_type,
        offset=offset,
        limit=params.page_size,
    )


def update_store(
    db: Session, *, organization_id: uuid.UUID, store_id: uuid.UUID, payload: StoreUpdate
) -> Store:
    store = get_store(db, organization_id=organization_id, store_id=store_id)

    updates = payload.model_dump(exclude_unset=True)
    new_code = updates.get("store_code")
    if new_code and new_code != store.store_code:
        existing = StoreRepository(db).get_by_code(organization_id, new_code)
        if existing is not None and existing.id != store.id:
            raise ConflictError("A store with this store_code already exists.", code="store_code_taken")

    for field, value in updates.items():
        setattr(store, field, value)

    return StoreRepository(db).add(store)


def delete_store(db: Session, *, organization_id: uuid.UUID, store_id: uuid.UUID) -> None:
    store = get_store(db, organization_id=organization_id, store_id=store_id)
    StoreRepository(db).soft_delete(store)
