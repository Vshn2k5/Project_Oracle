"""
Retrieval models for Project Oracle.

These models define the contracts that the hybrid retrieval system
produces for downstream consumers (agents, verification engine).
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class QueryAnalysis:
    """
    Structured representation of a parsed user query.
    """
    original_query: str
    normalized_query: str
    query_type: str
    entities: tuple[str, ...]
    keywords: tuple[str, ...]
    retrieval_intent: str


@dataclass(frozen=True, slots=True)
class RetrievedChunk:
    """
    A single chunk returned by the retrieval system with provenance and ranking signals.
    """
    chunk_id: str
    text: str
    page_number: int
    document_id: str
    source_path: str
    
    # Raw scores
    vector_score_raw: float
    keyword_score_raw: float
    graph_score_raw: float
    
    # Normalized scores
    vector_score_normalized: float
    keyword_score_normalized: float
    graph_score_normalized: float
    
    # Final fused score
    final_score: float
    
    # Explanation
    retrieval_sources: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RetrievedContext:
    """
    The complete evidence package delivered to an agent.
    """
    query: str
    chunks: tuple[RetrievedChunk, ...]
    entities: tuple[dict[str, object], ...]
    relationships: tuple[dict[str, object], ...]
    claims: tuple[dict[str, object], ...]
    evidence: tuple[dict[str, object], ...]
    sources: tuple[dict[str, object], ...]
    retrieval_status: str

