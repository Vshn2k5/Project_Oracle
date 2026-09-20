"""
Extraction pipeline for Project Oracle.

Validates and converts raw LLM outputs into core knowledge-graph domain models.
Includes lightweight deterministic entity resolution.
"""

import hashlib
import logging
import re
from typing import Any

from src.extraction.llm import LLMProvider, LLMProviderError
from src.extraction.schemas import DocumentExtractionSchema
from src.models.document import DocumentChunk
from src.models.knowledge_graph import (
    Claim,
    Entity,
    Evidence,
    ExtractedRelationship,
)

logger = logging.getLogger(__name__)


class ExtractionPipeline:
    """
    Coordinates extraction of knowledge from document chunks.
    """

    def __init__(self, llm_provider: LLMProvider) -> None:
        self._llm = llm_provider

    def _generate_id(self, prefix: str, content: str) -> str:
        """Generate a deterministic ID based on content."""
        hash_digest = hashlib.sha256(content.encode("utf-8")).hexdigest()[:12]
        return f"{prefix}-{hash_digest}"

    def _normalize_entity_name(self, name: str) -> str:
        """
        Lightweight deterministic entity resolution.
        - Lowercase
        - Strip leading/trailing whitespace
        - Replace multiple spaces with a single space
        """
        name = name.lower().strip()
        name = re.sub(r"\s+", " ", name)
        return name

    def extract_from_chunk(
        self,
        chunk: DocumentChunk,
    ) -> dict[str, list[Any]]:
        """
        Process a single chunk through the LLM and validate the output.

        Returns:
            A dictionary containing lists of validated domain models:
            'entities', 'relationships', 'claims', 'evidence'.
        """
        try:
            raw_extraction = self._llm.extract_structured_data(
                text=chunk.text,
                schema=DocumentExtractionSchema,
            )
        except LLMProviderError as exc:
            logger.warning(
                "Extraction failed for chunk %s: %s",
                chunk.chunk_id,
                exc,
            )
            # Return empty lists on failure to allow pipeline to continue safely
            return {
                "entities": [],
                "relationships": [],
                "claims": [],
                "evidence": [],
            }

        entities: list[Entity] = []
        relationships: list[ExtractedRelationship] = []
        claims: list[Claim] = []
        evidence: list[Evidence] = []

        # 1. Process Entities
        entity_map: dict[str, str] = {}  # Maps normalized name to entity ID

        for raw_ent in raw_extraction.entities:
            if not raw_ent.name.strip():
                continue

            normalized_name = self._normalize_entity_name(raw_ent.name)
            entity_id = self._generate_id(
                prefix="ENT",
                content=f"{raw_ent.entity_type}:{normalized_name}",
            )

            # Prevent duplicate entities within the same chunk
            if normalized_name not in entity_map:
                entity_map[normalized_name] = entity_id
                
                # Format properties into a single description string for now
                description = raw_ent.properties.get("description", "")
                if not description:
                    description = ", ".join(
                        f"{k}: {v}" for k, v in raw_ent.properties.items()
                    )

                entities.append(
                    Entity(
                        entity_id=entity_id,
                        label=raw_ent.entity_type,
                        name=normalized_name,
                        entity_type=raw_ent.properties.get("type", "generic"),
                        description=description,
                        source_chunk_id=chunk.chunk_id,
                    )
                )

        # 2. Process Relationships
        for raw_rel in raw_extraction.relationships:
            norm_source = self._normalize_entity_name(raw_rel.source_entity)
            norm_target = self._normalize_entity_name(raw_rel.target_entity)

            # Validate that both endpoints exist in our entity map
            if norm_source not in entity_map or norm_target not in entity_map:
                logger.debug(
                    "Skipping relationship %s->%s: missing endpoints",
                    norm_source,
                    norm_target,
                )
                continue

            # Check if evidence actually exists in chunk text
            if raw_rel.evidence_quote and raw_rel.evidence_quote not in chunk.text:
                 logger.debug("Relationship evidence quote not exactly found in text (ignoring evidence field).")

            relationships.append(
                ExtractedRelationship(
                    source_entity_id=entity_map[norm_source],
                    target_entity_id=entity_map[norm_target],
                    relationship_type=raw_rel.relationship_type,
                    description=raw_rel.evidence_quote,
                    source_chunk_id=chunk.chunk_id,
                )
            )

        # 3. Process Claims & Evidence
        for raw_claim in raw_extraction.claims:
            norm_subject = self._normalize_entity_name(raw_claim.subject_entity)
            
            # Claims must be about a known entity
            if norm_subject not in entity_map:
                logger.debug(
                    "Skipping claim: subject '%s' not found",
                    norm_subject,
                )
                continue
            
            if not raw_claim.claim_text.strip():
                continue

            claim_id = self._generate_id("CLM", raw_claim.claim_text)
            
            claims.append(
                Claim(
                    claim_id=claim_id,
                    statement=raw_claim.claim_text,
                    subject_entity_id=entity_map[norm_subject],
                    source_chunk_id=chunk.chunk_id,
                    confidence=raw_claim.confidence,
                )
            )

            # Create corresponding Evidence
            evidence_id = self._generate_id("EVD", claim_id + chunk.chunk_id)
            evidence.append(
                Evidence(
                    evidence_id=evidence_id,
                    claim_id=claim_id,
                    chunk_id=chunk.chunk_id,
                    text=raw_claim.evidence_quote,
                    supports=True,
                )
            )

        logger.debug(
            "Extracted %d entities, %d relationships, %d claims from chunk %s",
            len(entities),
            len(relationships),
            len(claims),
            chunk.chunk_id,
        )

        return {
            "entities": entities,
            "relationships": relationships,
            "claims": claims,
            "evidence": evidence,
        }
