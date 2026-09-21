from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class AIActionAuditRecord:
    """Rule: every AI action must be auditable. Every AI recommendation or
    action writes one of these before it can take effect.
    """

    action_type: str
    input_payload: dict[str, Any]
    output_payload: dict[str, Any]
    model_name: str
    passed_guardrails: bool


class PricingGuardrail(ABC):
    """Rule: AI must not bypass deterministic pricing guardrails. Every AI
    pricing recommendation is validated against guardrails like this
    (min margin, max discount, price bounds) before it can be applied —
    the guardrail check is deterministic code, never another AI call.
    """

    @abstractmethod
    def validate(self, proposed_price: float, context: dict[str, Any]) -> bool: ...


class AIAction(ABC):
    """Base for any AI-driven action (e.g. pricing recommendations). Concrete
    implementations must run proposed changes through a PricingGuardrail and
    produce an AIActionAuditRecord before the result is used.
    """

    @abstractmethod
    def run(self, context: dict[str, Any]) -> AIActionAuditRecord: ...
