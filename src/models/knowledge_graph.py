"""
Knowledge-graph domain models for Project Oracle.

These models represent information *extracted* from source documents —
entities, relationships, claims, and evidence — before they are written
to Neo4j.  They serve as the contract between the extraction layer and
the knowledge-graph layer.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Entity:
    """
    An entity extracted from document text.

    Attributes:
        entity_id: Stable identifier for this entity.
        label: Neo4j node label (e.g. ``Zone``, ``Risk``, ``Infrastructure``).
        name: Human-readable name of the entity.
        entity_type: Subtype within the label (e.g. ``urban_flood`` for Risk).
        description: Free-text description extracted from the source.
        source_chunk_id: ID of the chunk the entity was extracted from.
    """

    entity_id: str
    label: str
    name: str
    entity_type: str
    description: str
    source_chunk_id: str


@dataclass(frozen=True, slots=True)
class ExtractedRelationship:
    """
    A relationship extracted between two entities.

    Attributes:
        source_entity_id: ID of the source entity.
        target_entity_id: ID of the target entity.
        relationship_type: Neo4j relationship type (e.g. ``HAS_RISK``).
        description: Optional description of the relationship.
        source_chunk_id: ID of the chunk the relationship was extracted from.
    """

    source_entity_id: str
    target_entity_id: str
    relationship_type: str
    description: str
    source_chunk_id: str


@dataclass(frozen=True, slots=True)
class Claim:
    """
    A factual assertion extracted from a source document.

    Claims are the atomic units that the verification engine checks
    against the knowledge graph.

    Attributes:
        claim_id: Stable identifier for this claim.
        statement: The natural-language claim text.
        subject_entity_id: ID of the entity the claim is about.
        source_chunk_id: ID of the chunk the claim originates from.
        confidence: Extraction confidence score (0.0–1.0).
    """

    claim_id: str
    statement: str
    subject_entity_id: str
    source_chunk_id: str
    confidence: float


@dataclass(frozen=True, slots=True)
class Evidence:
    """
    Supporting or contradicting evidence for a claim.

    Attributes:
        evidence_id: Stable identifier for this evidence record.
        claim_id: ID of the claim this evidence supports or contradicts.
        chunk_id: ID of the source chunk the evidence derives from.
        text: The relevant text excerpt.
        supports: ``True`` if the evidence supports the claim.
    """

    evidence_id: str
    claim_id: str
    chunk_id: str
    text: str
    supports: bool
