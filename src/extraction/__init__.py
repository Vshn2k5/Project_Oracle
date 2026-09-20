"""
Extraction layer for Project Oracle.
Converts unstructured text chunks into structured knowledge-graph elements.
"""

from src.extraction.llm import (
    LLMProvider,
    LLMProviderError,
    create_llm_provider,
)
from src.extraction.pipeline import ExtractionPipeline
from src.extraction.schemas import (
    DocumentExtractionSchema,
    ExtractedClaimSchema,
    ExtractedEntitySchema,
    ExtractedRelationshipSchema,
)

__all__ = [
    "LLMProvider",
    "LLMProviderError",
    "create_llm_provider",
    "ExtractionPipeline",
    "DocumentExtractionSchema",
    "ExtractedEntitySchema",
    "ExtractedRelationshipSchema",
    "ExtractedClaimSchema",
]
