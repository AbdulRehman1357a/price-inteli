import uuid

from sqlalchemy import func, or_, select

from app.models.category import Category, CategoryStatus
from app.models.product import Product
from app.repositories.base import BaseRepository

_SORTABLE_COLUMNS = {
    "name": Category.name,
    "created_at": Category.created_at,
}
_DEFAULT_SORT = Category.created_at.desc()


def _resolve_sort(sort: str | None):
    if not sort:
        return _DEFAULT_SORT
    descending = sort.startswith("-")
    key = sort[1:] if descending else sort
    column = _SORTABLE_COLUMNS.get(key)
    if column is None:
        return _DEFAULT_SORT
    return column.desc() if descending else column.asc()


class CategoryRepository(BaseRepository[Category]):
    model = Category

    def get_by_id_for_organization(
        self, category_id: uuid.UUID, organization_id: uuid.UUID
    ) -> Category | None:
        stmt = select(Category).where(
            Category.id == category_id, Category.organization_id == organization_id
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_name(self, organization_id: uuid.UUID, name: str) -> Category | None:
        stmt = select(Category).where(
            Category.organization_id == organization_id, func.lower(Category.name) == name.strip().lower()
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_for_organization(self, organization_id: uuid.UUID) -> list[Category]:
        """All categories for an org, unpaginated — used to build the full
        hierarchy (e.g. for cycle checks and the frontend's category tree).
        """
        stmt = select(Category).where(Category.organization_id == organization_id)
        return list(self.db.execute(stmt).scalars().all())

    def search(
        self,
        organization_id: uuid.UUID,
        *,
        search: str | None = None,
        status: CategoryStatus | None = None,
        sort: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Category], int]:
        conditions = [Category.organization_id == organization_id]
        if status is not None:
            conditions.append(Category.status == status)
        if search:
            pattern = f"%{search.strip()}%"
            conditions.append(or_(Category.name.ilike(pattern), Category.code.ilike(pattern)))

        base_stmt = select(Category).where(*conditions)

        total = self.db.execute(
            select(func.count()).select_from(base_stmt.subquery())
        ).scalar_one()

        items = list(
            self.db.execute(base_stmt.order_by(_resolve_sort(sort)).offset(offset).limit(limit))
            .scalars()
            .all()
        )
        return items, total

    def has_children(self, category_id: uuid.UUID) -> bool:
        stmt = select(func.count()).select_from(Category).where(Category.parent_id == category_id)
        return self.db.execute(stmt).scalar_one() > 0

    def has_products(self, category_id: uuid.UUID) -> bool:
        stmt = (
            select(func.count())
            .select_from(Product)
            .where(Product.category_id == category_id, Product.deleted_at.is_(None))
        )
        return self.db.execute(stmt).scalar_one() > 0

    def would_create_cycle(
        self, *, category_id: uuid.UUID, new_parent_id: uuid.UUID, organization_id: uuid.UUID
    ) -> bool:
        """True if re-parenting category_id under new_parent_id would create
        a cycle — i.e. new_parent_id is category_id itself, or anywhere in
        category_id's current subtree. Walks the org's categories in memory
        (a tenant's category tree is small) rather than a recursive CTE.
        """
        if new_parent_id == category_id:
            return True

        children_by_parent: dict[uuid.UUID, list[uuid.UUID]] = {}
        for c in self.list_for_organization(organization_id):
            if c.parent_id is not None:
                children_by_parent.setdefault(c.parent_id, []).append(c.id)

        stack = list(children_by_parent.get(category_id, []))
        while stack:
            current = stack.pop()
            if current == new_parent_id:
                return True
            stack.extend(children_by_parent.get(current, []))
        return False
