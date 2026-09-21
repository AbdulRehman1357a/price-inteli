from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

# The Enterprise Integration Hub's canonical retail data model. External
# systems (via CSV/REST/Webhook adapters) never map directly onto our
# Product/Price/Inventory/Store tables — a source record is first
# transformed (app/services/integration_mapping_engine.py, driven by each
# integration's IntegrationMapping rows) into one of these normalized
# shapes, then reconciled into the real tables
# (app/services/integration_apply_service.py). This decoupling is the
# whole point: adding a new source system means adding mapping rows and,
# if needed, an adapter — never touching the domain tables' shape.
#
# extra="forbid" on every model below is deliberate: a mapping row whose
# canonical_field is misspelled should surface as a clear per-record sync
# error, not silently vanish (Pydantic's default is to drop unknown fields).
#
# Phase 10 upgrade: every model below also carries an optional external_id
# (and, where a variant concept applies, external_variant_id) field,
# embedded directly rather than through a separate CanonicalExternalReference
# sub-object — extra="forbid" plus the mapping engine's flat
# source_field->canonical_field model doesn't support nested sub-objects
# without special-casing, and a flat optional field is exactly what
# app.services.integration_apply_service needs to upsert the external_*
# staging tables (the general External ID Mapping mechanism).


class CanonicalProduct(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sku: str
    product_name: str
    category: str | None = None
    barcode: str | None = None
    cost_price: Decimal | None = None
    selling_price: Decimal | None = None
    currency: str | None = None
    external_id: str | None = None
    external_variant_id: str | None = None


class CanonicalPrice(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sku: str
    store_code: str | None = None
    selling_price: Decimal
    currency: str = "USD"
    effective_from: datetime | None = None
    external_id: str | None = None


class CanonicalInventory(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sku: str
    store_code: str
    quantity_on_hand: Decimal
    external_id: str | None = None


class CanonicalPromotion(BaseModel):
    """The platform has no persisted, pricing-engine-integrated Promotion
    entity (pricing_rules.rule_type="promotion" is a categorization label,
    not a dedicated table; see Phase 6). A CanonicalPromotion record is
    staged into app.models.external_promotion.ExternalPromotion — synced
    end-to-end and queryable — but does not create/drive a live
    pricing_rules row. See app.services.integration_apply_service.apply_promotion.
    external_id is required in practice (not just optional) for promotions:
    it's the only stable dedup key the staging upsert has, since name
    alone isn't unique.
    """

    model_config = ConfigDict(extra="forbid")

    name: str
    sku: str | None = None
    discount_percentage: Decimal | None = None
    discount_amount: Decimal | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    external_id: str | None = None


class CanonicalStore(BaseModel):
    model_config = ConfigDict(extra="forbid")

    store_code: str
    name: str
    city: str | None = None
    country: str | None = None
    address_line_1: str | None = None
    timezone: str | None = None
    currency: str | None = None
    external_id: str | None = None


class CanonicalOrderLine(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sku: str
    external_variant_id: str | None = None
    quantity: Decimal
    unit_price: Decimal
    line_total: Decimal | None = None


class CanonicalOrder(BaseModel):
    """Sales/order sync (Phase 10 upgrade) — staged into
    app.models.external_order.ExternalOrder rather than a persisted domain
    Order entity, same "queryable but not domain-integrated" pattern as
    CanonicalPromotion. `lines` is populated by a single mapping row
    (source_field="line_items" -> canonical_field="lines",
    transformation_rule=None/"direct") since the existing passthrough
    already returns a value unchanged regardless of type — Pydantic
    validates the nested list on construction, no mapping-engine change
    needed. external_id here is the order id itself (not a "reference to
    something else"), so it's required rather than optional.
    """

    model_config = ConfigDict(extra="forbid")

    external_id: str
    store_code: str | None = None
    order_date: datetime | None = None
    status: str | None = None
    currency: str = "USD"
    subtotal: Decimal | None = None
    tax_total: Decimal | None = None
    total: Decimal | None = None
    lines: list[CanonicalOrderLine] = Field(default_factory=list)
