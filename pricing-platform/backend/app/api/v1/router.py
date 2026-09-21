from fastapi import APIRouter

from app.api.v1 import (
    ai_agent_runs,
    ai_agents,
    ai_policies,
    ai_pricing,
    analytics,
    auth,
    categories,
    competitors,
    devices,
    esl_integrations,
    health,
    imports,
    integration_webhooks,
    integrations,
    inventory,
    label_templates,
    organizations,
    outputs,
    permissions,
    pricing,
    products,
    public,
    roles,
    stores,
    users,
)

api_v1_router = APIRouter()

api_v1_router.include_router(health.router)
api_v1_router.include_router(auth.router)
api_v1_router.include_router(users.router)
api_v1_router.include_router(roles.router)
api_v1_router.include_router(permissions.router)
api_v1_router.include_router(organizations.router)
api_v1_router.include_router(stores.router)
api_v1_router.include_router(categories.router)
api_v1_router.include_router(products.router)
api_v1_router.include_router(inventory.router)
api_v1_router.include_router(imports.router)
api_v1_router.include_router(label_templates.router)
api_v1_router.include_router(pricing.router)
api_v1_router.include_router(outputs.router)
api_v1_router.include_router(public.router)
api_v1_router.include_router(devices.router)
api_v1_router.include_router(esl_integrations.router)
api_v1_router.include_router(integrations.router)
api_v1_router.include_router(integration_webhooks.router)
api_v1_router.include_router(ai_pricing.router)
api_v1_router.include_router(ai_agents.router)
api_v1_router.include_router(ai_agent_runs.router)
api_v1_router.include_router(ai_policies.router)
api_v1_router.include_router(competitors.router)
api_v1_router.include_router(analytics.router)
