"""
Shared domain models for Project Oracle.

This package provides the data contracts used across layers of the
application.  Models are organised into submodules by concern:

- ``document``       — source data (documents, pages, chunks, embeddings)
- ``knowledge_graph`` — extracted knowledge (entities, relationships, claims)
- ``retrieval``      — retrieval results and query analysis
- ``agent``          — agent reasoning outputs
- ``verification``   — fact-checking results
"""

from src.models.document import (
    CleanedDocument,
    CleanedPage,
    DocumentChunk,
    EmbeddedChunk,
    ExtractedDocument,
    ExtractedPage,
)
from src.models.knowledge_graph import (
    Claim,
    Entity,
    Evidence,
    ExtractedRelationship,
)
from src.models.retrieval import (
    QueryAnalysis,
    RetrievedChunk,
    RetrievedContext,
)
from src.models.agent import (
    AgentResult,
    Recommendation,
)
from src.models.verification import VerificationResult

__all__ = [
    # document
    "ExtractedPage",
    "ExtractedDocument",
    "CleanedPage",
    "CleanedDocument",
    "DocumentChunk",
    "EmbeddedChunk",
    # knowledge graph
    "Entity",
    "ExtractedRelationship",
    "Claim",
    "Evidence",
    # retrieval
    "RetrievedChunk",
    "GraphContext",
    "RetrievedContext",
    # agent
    "Recommendation",
    "AgentResult",
    # verification
    "VerificationResult",
]
