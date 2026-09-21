import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.category import Category
from app.repositories.category_repository import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryListParams, CategoryUpdate


def _validate_parent(
    repo: CategoryRepository, *, organization_id: uuid.UUID, parent_id: uuid.UUID | None
) -> None:
    if parent_id is None:
        return
    if repo.get_by_id_for_organization(parent_id, organization_id) is None:
        raise NotFoundError("Parent category not found.", code="parent_category_not_found")


def create_category(db: Session, *, organization_id: uuid.UUID, payload: CategoryCreate) -> Category:
    repo = CategoryRepository(db)
    _validate_parent(repo, organization_id=organization_id, parent_id=payload.parent_id)

    category = Category(id=uuid.uuid4(), organization_id=organization_id, **payload.model_dump())
    return repo.add(category)


def get_category(db: Session, *, organization_id: uuid.UUID, category_id: uuid.UUID) -> Category:
    category = CategoryRepository(db).get_by_id_for_organization(category_id, organization_id)
    if category is None:
        raise NotFoundError("Category not found.", code="category_not_found")
    return category


def list_categories(
    db: Session, *, organization_id: uuid.UUID, params: CategoryListParams
) -> tuple[list[Category], int]:
    repo = CategoryRepository(db)
    offset = (params.page - 1) * params.page_size
    return repo.search(
        organization_id,
        search=params.search,
        status=params.status,
        sort=params.sort,
        offset=offset,
        limit=params.page_size,
    )


def update_category(
    db: Session, *, organization_id: uuid.UUID, category_id: uuid.UUID, payload: CategoryUpdate
) -> Category:
    category = get_category(db, organization_id=organization_id, category_id=category_id)
    repo = CategoryRepository(db)

    updates = payload.model_dump(exclude_unset=True)
    if "parent_id" in updates:
        new_parent_id = updates["parent_id"]
        _validate_parent(repo, organization_id=organization_id, parent_id=new_parent_id)
        if new_parent_id is not None and repo.would_create_cycle(
            category_id=category.id, new_parent_id=new_parent_id, organization_id=organization_id
        ):
            raise ConflictError(
                "A category cannot be moved under itself or one of its own subcategories.",
                code="category_cycle",
            )

    for field, value in updates.items():
        setattr(category, field, value)

    return repo.add(category)


def delete_category(db: Session, *, organization_id: uuid.UUID, category_id: uuid.UUID) -> None:
    category = get_category(db, organization_id=organization_id, category_id=category_id)
    repo = CategoryRepository(db)

    if repo.has_children(category.id):
        raise ConflictError(
            "This category has subcategories — move or delete them first.", code="category_has_children"
        )
    if repo.has_products(category.id):
        raise ConflictError(
            "This category has products assigned to it — reassign them first.",
            code="category_has_products",
        )

    db.delete(category)
    db.flush()
