"""
Agent output models for Project Oracle.

These models define the contracts produced by domain specialist agents
and the Decision Mediator.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Recommendation:
    """
    A single actionable recommendation produced by an agent.

    Attributes:
        recommendation_id: Stable identifier.
        title: Short summary of the recommendation.
        description: Detailed explanation.
        priority: Priority level (``critical``, ``high``, ``medium``, ``low``).
        supporting_claim_ids: IDs of claims that support this recommendation.
    """

    recommendation_id: str
    title: str
    description: str
    priority: str
    supporting_claim_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AgentResult:
    """
    The output produced by a single domain specialist agent.

    Attributes:
        agent_name: Identifier of the agent that produced this result.
        analysis: Free-text analysis narrative.
        recommendations: Actionable recommendations.
        confidence: Overall confidence (0.0–1.0).
        claim_ids: IDs of claims made during analysis.
        evidence_chunk_ids: IDs of evidence chunks consulted.
    """

    agent_name: str
    analysis: str
    recommendations: tuple[Recommendation, ...]
    confidence: float
    claim_ids: tuple[str, ...]
    evidence_chunk_ids: tuple[str, ...]
