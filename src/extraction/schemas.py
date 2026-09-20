"""
Extraction schemas for Project Oracle.

These Pydantic models represent the structured output expected from the LLM.
They are validated before being converted into the core domain models.
"""

from typing import Literal

from pydantic import BaseModel, Field


class ExtractedEntitySchema(BaseModel):
    """An entity extracted from text."""

    name: str = Field(
        description="The normalized name of the entity.",
    )
    entity_type: Literal[
        "Zone",
        "Risk",
        "Infrastructure",
        "Mitigation",
        "Budget",
        "Policy",
        "Project",
    ] = Field(
        description="The domain type of the entity.",
    )
    properties: dict[str, str] = Field(
        default_factory=dict,
        description="Additional properties, such as 'type', 'severity', or 'description'.",
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score between 0.0 and 1.0.",
    )


class ExtractedRelationshipSchema(BaseModel):
    """A relationship between two entities."""

    source_entity: str = Field(
        description="The exact name of the source entity.",
    )
    relationship_type: Literal[
        "HAS_RISK",
        "AFFECTS",
        "REQUIRES",
        "FUNDS",
        "LOCATED_IN",
        "ADDRESSES",
        "REGULATES",
        "APPLIES_TO",
    ] = Field(
        description="The type of relationship.",
    )
    target_entity: str = Field(
        description="The exact name of the target entity.",
    )
    evidence_quote: str = Field(
        description="Exact quote from the text supporting this relationship.",
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score between 0.0 and 1.0.",
    )


class ExtractedClaimSchema(BaseModel):
    """A factual assertion extracted from text."""

    claim_text: str = Field(
        description="The standalone factual assertion (e.g., 'Zone X has high flood exposure.').",
    )
    subject_entity: str = Field(
        description="The primary entity this claim is about.",
    )
    evidence_quote: str = Field(
        description="Exact quote from the text supporting this claim.",
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score between 0.0 and 1.0.",
    )


class DocumentExtractionSchema(BaseModel):
    """The complete extraction result for a single chunk."""

    entities: list[ExtractedEntitySchema] = Field(
        default_factory=list,
        description="All relevant domain entities found in the text.",
    )
    relationships: list[ExtractedRelationshipSchema] = Field(
        default_factory=list,
        description="All supported relationships between the extracted entities.",
    )
    claims: list[ExtractedClaimSchema] = Field(
        default_factory=list,
        description="All verifiable claims asserted in the text.",
    )
