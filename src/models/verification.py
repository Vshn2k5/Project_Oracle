"""
Verification models for Project Oracle.

These models represent the output of the symbolic verification engine
that checks agent claims against the knowledge graph.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class VerificationResult:
    """
    The outcome of verifying a single claim against the knowledge graph.

    Attributes:
        claim_id: ID of the claim that was verified.
        verdict: One of ``verified``, ``contradicted``, ``unsupported``.
        explanation: Human-readable explanation of the verdict.
        supporting_node_ids: Graph node IDs used as evidence.
        supporting_relationship_types: Relationship types traversed.
    """

    claim_id: str
    verdict: str
    explanation: str
    supporting_node_ids: tuple[str, ...]
    supporting_relationship_types: tuple[str, ...]
