from app.db.session import SessionLocal
from app.models.product import Product
from app.models.category import Category
from app.models.price import Price
from app.models.store import Store
from app.models.inventory import Inventory
from app.models.organization import Organization
import uuid
from decimal import Decimal

db = SessionLocal()

CATEGORIES_DATA = [
    ('Electronics', None),
    ('Smartphones', 'Electronics'),
    ('Laptops', 'Electronics'),
    ('Accessories', 'Electronics'),
    ('Clothing', None),
    ('Mens Wear', 'Clothing'),
    ('Womens Wear', 'Clothing'),
    ('Home & Garden', None),
    ('Kitchen', 'Home & Garden'),
    ('Decor', 'Home & Garden'),
]

PRODUCTS_DATA = [
    ('IPHONE-15', 'iPhone 15', 'Smartphones', '999.99'),
    ('IPHONE-15P', 'iPhone 15 Pro', 'Smartphones', '1199.99'),
    ('SAMSUNG-S24', 'Samsung Galaxy S24', 'Smartphones', '899.99'),
    ('MACBOOK-AIR', 'MacBook Air M3', 'Laptops', '1299.99'),
    ('MACBOOK-PRO', 'MacBook Pro M3', 'Laptops', '1999.99'),
    ('DELL-XPS', 'Dell XPS 13', 'Laptops', '1099.99'),
    ('AIRPODS-PRO', 'AirPods Pro 2', 'Accessories', '249.99'),
    ('MAGSAFE-CHRG', 'MagSafe Charger', 'Accessories', '39.99'),
    ('USB-C-HUB', 'USB-C Hub 7-in-1', 'Accessories', '79.99'),
    ('TSHIRT-BLK', 'Black T-Shirt', 'Mens Wear', '29.99'),
    ('JEANS-BLU', 'Blue Jeans', 'Mens Wear', '79.99'),
    ('DRESS-RED', 'Red Summer Dress', 'Womens Wear', '89.99'),
    ('COFFEE-MKR', 'Coffee Maker', 'Kitchen', '129.99'),
    ('BLENDER', 'High-Speed Blender', 'Kitchen', '149.99'),
    ('VASE-CERAMIC', 'Ceramic Vase', 'Decor', '49.99'),
    ('CANDLE-SET', 'Scented Candle Set', 'Decor', '34.99'),
]


def ensure_category(org_id, name, parent_id):
    existing = db.query(Category).filter_by(name=name, organization_id=org_id).first()
    if existing:
        return existing.id, False
    cat = Category(
        id=uuid.uuid4(),
        organization_id=org_id,
        name=name,
        parent_id=parent_id,
    )
    db.add(cat)
    db.flush()
    return cat.id, True


def seed_org(org):
    print(f'\n=== Seeding org: {org.name} ({org.id}) ===')

    # Ensure at least one store exists for the org
    store = db.query(Store).filter_by(organization_id=org.id).first()
    if not store:
        store = Store(
            id=uuid.uuid4(),
            organization_id=org.id,
            store_code='MAIN',
            name=f'{org.name} Main Store',
            country='US',
            city='New York',
            address_line_1='1 Main St',
            timezone='UTC',
            currency=org.currency if hasattr(org, 'currency') and org.currency else 'USD',
        )
        db.add(store)
        db.flush()
        print(f'  Created store: {store.name}')
    else:
        print(f'  Store exists: {store.name}')

    # Categories (in order so parents resolve before children)
    cat_map = {}
    for name, parent_name in CATEGORIES_DATA:
        parent_id = cat_map.get(parent_name)
        cat_id, created = ensure_category(org.id, name, parent_id)
        cat_map[name] = cat_id
        if created:
            print(f'  + Category: {name}')
    db.flush()

    # Products + prices + inventory
    for sku, name, cat_name, price in PRODUCTS_DATA:
        existing = db.query(Product).filter_by(sku=sku, organization_id=org.id).first()
        if existing:
            print(f'  = Product exists: {name}')
            continue
        prod = Product(
            id=uuid.uuid4(),
            organization_id=org.id,
            sku=sku,
            product_name=name,
            category_id=cat_map[cat_name],
            selling_price=Decimal(price),
            currency='USD',
        )
        db.add(prod)
        db.flush()

        price_rec = Price(
            id=uuid.uuid4(),
            organization_id=org.id,
            product_id=prod.id,
            base_price=Decimal(price),
            selling_price=Decimal(price),
            currency='USD',
        )
        db.add(price_rec)

        inv = Inventory(
            id=uuid.uuid4(),
            organization_id=org.id,
            product_id=prod.id,
            store_id=store.id,
            quantity_on_hand=100,
            reorder_point=10,
        )
        db.add(inv)
        print(f'  + Product: {name} (${price})')

    db.commit()
    count = db.query(Product).filter_by(organization_id=org.id).count()
    cat_count = db.query(Category).filter_by(organization_id=org.id).count()
    print(f'  => Org now has {cat_count} categories, {count} products')


try:
    orgs = db.query(Organization).all()
    for org in orgs:
        seed_org(org)
    print('\nDone seeding all orgs.')
finally:
    db.close()