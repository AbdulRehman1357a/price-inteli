import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.product import Product
from app.repositories.category_repository import CategoryRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.product import ProductCreate, ProductListParams, ProductUpdate


def _validate_category(db: Session, *, organization_id: uuid.UUID, category_id: uuid.UUID) -> None:
    if CategoryRepository(db).get_by_id_for_organization(category_id, organization_id) is None:
        raise NotFoundError("Category not found.", code="category_not_found")


def create_product(db: Session, *, organization_id: uuid.UUID, payload: ProductCreate) -> Product:
    repo = ProductRepository(db)
    if repo.get_by_sku(organization_id, payload.sku) is not None:
        raise ConflictError("A product with this SKU already exists.", code="sku_taken")
    _validate_category(db, organization_id=organization_id, category_id=payload.category_id)

    product = Product(id=uuid.uuid4(), organization_id=organization_id, **payload.model_dump())
    return repo.add(product)


def get_product(db: Session, *, organization_id: uuid.UUID, product_id: uuid.UUID) -> Product:
    product = ProductRepository(db).get_by_id_for_organization(product_id, organization_id)
    if product is None:
        raise NotFoundError("Product not found.", code="product_not_found")
    return product


def list_products(
    db: Session, *, organization_id: uuid.UUID, params: ProductListParams
) -> tuple[list[Product], int]:
    repo = ProductRepository(db)
    offset = (params.page - 1) * params.page_size
    return repo.search(
        organization_id,
        search=params.search,
        category_id=params.category_id,
        status=params.status,
        sort=params.sort,
        offset=offset,
        limit=params.page_size,
    )


def update_product(
    db: Session, *, organization_id: uuid.UUID, product_id: uuid.UUID, payload: ProductUpdate
) -> Product:
    product = get_product(db, organization_id=organization_id, product_id=product_id)
    repo = ProductRepository(db)

    updates = payload.model_dump(exclude_unset=True)

    new_sku = updates.get("sku")
    if new_sku and new_sku != product.sku:
        existing = repo.get_by_sku(organization_id, new_sku)
        if existing is not None and existing.id != product.id:
            raise ConflictError("A product with this SKU already exists.", code="sku_taken")

    new_category_id = updates.get("category_id")
    if new_category_id and new_category_id != product.category_id:
        _validate_category(db, organization_id=organization_id, category_id=new_category_id)

    for field, value in updates.items():
        setattr(product, field, value)

    return repo.add(product)


def delete_product(db: Session, *, organization_id: uuid.UUID, product_id: uuid.UUID) -> None:
    product = get_product(db, organization_id=organization_id, product_id=product_id)
    ProductRepository(db).soft_delete(product)
