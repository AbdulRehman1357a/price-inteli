from pydantic import BaseModel


class PublicPriceDisplay(BaseModel):
    """Deliberately minimal — this is served with no authentication (it's
    the QR/web output target), so only customer-facing fields belong here.
    """

    product_name: str
    sku: str
    price: str
    currency: str
    store_name: str | None
