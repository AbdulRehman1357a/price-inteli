from app.ai.providers.base import AIPricingProvider
from app.ai.providers.heuristic_provider import HeuristicPricingProvider

_PROVIDERS: dict[str, AIPricingProvider] = {
    "heuristic": HeuristicPricingProvider(),
}
_DEFAULT_PROVIDER = "heuristic"


def get_ai_provider(name: str | None = None) -> AIPricingProvider:
    """Resolves a provider by name, defaulting to the deterministic
    heuristic one. A future real-LLM provider (e.g. "openai") registers
    here the same way every other adapter registry in this codebase works
    (app/outputs/registry.py, app/integrations/registry.py,
    app/integrations/hub/registry.py) — callers never depend on a concrete
    provider class.
    """
    return _PROVIDERS.get(name or _DEFAULT_PROVIDER, _PROVIDERS[_DEFAULT_PROVIDER])


def list_provider_names() -> list[str]:
    return list(_PROVIDERS)
