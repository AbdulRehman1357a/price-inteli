from app.ai.agents.base import Agent
from app.ai.agents.pricing_optimization_agent import PricingOptimizationAgent
from app.core.exceptions import ValidationError
from app.models.ai_agent import AgentType

# Only Pricing Optimization is implemented in this phase ("Implement one
# agent at a time. Start with Pricing Optimization Agent"). The other 4
# agent_type catalog values are valid to create an AIAgent with — same
# honesty pattern as Phase 9's ESL vendor stubs and Phase 10's SAP/Oracle
# catalog entries — but running one raises a clear error rather than
# pretending to do something.
_AGENTS: dict[AgentType, Agent] = {
    AgentType.PRICING_OPTIMIZATION: PricingOptimizationAgent(),
}


def get_agent(agent_type: AgentType) -> Agent:
    agent = _AGENTS.get(agent_type)
    if agent is None:
        raise ValidationError(
            f"The {agent_type.value} agent is not implemented yet — only "
            f"{AgentType.PRICING_OPTIMIZATION.value} is available in this phase."
        )
    return agent
