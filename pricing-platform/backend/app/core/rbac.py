from enum import StrEnum


class SystemRoleName(StrEnum):
    """The six built-in role templates seeded by the Phase 1 data migration.

    Stored as Role rows with organization_id=NULL, is_system_role=True —
    shared by every tenant rather than duplicated per organization.
    """

    SUPER_ADMIN = "Super Admin"
    ORGANIZATION_ADMIN = "Organization Admin"
    STORE_MANAGER = "Store Manager"
    PRICING_MANAGER = "Pricing Manager"
    INVENTORY_MANAGER = "Inventory Manager"
    VIEWER = "Viewer"


class PermissionCode(StrEnum):
    """Every permission code seeded by the Phase 1 data migration.

    Pass one of these (or its .value) to the require_permission() dependency.
    """

    ORGANIZATIONS_READ = "organizations.read"
    ORGANIZATIONS_UPDATE = "organizations.update"

    USERS_READ = "users.read"
    USERS_CREATE = "users.create"
    USERS_UPDATE = "users.update"
    USERS_DELETE = "users.delete"

    STORES_READ = "stores.read"
    STORES_CREATE = "stores.create"
    STORES_UPDATE = "stores.update"
    STORES_DELETE = "stores.delete"

    CATEGORIES_READ = "categories.read"
    CATEGORIES_CREATE = "categories.create"
    CATEGORIES_UPDATE = "categories.update"
    CATEGORIES_DELETE = "categories.delete"

    PRODUCTS_READ = "products.read"
    PRODUCTS_CREATE = "products.create"
    PRODUCTS_UPDATE = "products.update"
    PRODUCTS_DELETE = "products.delete"

    INVENTORY_READ = "inventory.read"
    INVENTORY_CREATE = "inventory.create"
    INVENTORY_UPDATE = "inventory.update"
    INVENTORY_ADJUST = "inventory.adjust"

    IMPORTS_READ = "imports.read"
    IMPORTS_CREATE = "imports.create"

    PRICING_READ = "pricing.read"
    PRICING_CREATE = "pricing.create"
    PRICING_UPDATE = "pricing.update"
    PRICING_APPROVE = "pricing.approve"

    DEVICES_READ = "devices.read"
    DEVICES_CREATE = "devices.create"
    DEVICES_UPDATE = "devices.update"
    DEVICES_MANAGE = "devices.manage"

    INTEGRATIONS_READ = "integrations.read"
    INTEGRATIONS_CREATE = "integrations.create"
    INTEGRATIONS_UPDATE = "integrations.update"
    INTEGRATIONS_MANAGE = "integrations.manage"
    INTEGRATIONS_RECONCILE = "integrations.reconcile"

    OUTPUTS_READ = "outputs.read"
    OUTPUTS_CREATE = "outputs.create"
    OUTPUTS_UPDATE = "outputs.update"
    OUTPUTS_MANAGE = "outputs.manage"

    AI_RECOMMENDATIONS_READ = "ai_recommendations.read"
    AI_RECOMMENDATIONS_CREATE = "ai_recommendations.create"
    AI_RECOMMENDATIONS_REVIEW = "ai_recommendations.review"
    AI_RECOMMENDATIONS_APPLY = "ai_recommendations.apply"

    ANALYTICS_READ = "analytics.read"
