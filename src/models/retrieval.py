"""
Retrieval models for Project Oracle.

These models define the contracts that the hybrid retrieval system
produces for downstream consumers (agents, verification engine).
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RetrievedChunk:
    """
    A single chunk returned by the retrieval system with provenance.

    Attributes:
        chunk_id: Graph identifier of the chunk.
        text: The chunk text content.
        page_number: Source page number.
        document_id: Identifier of the source document.
        document_title: Human-readable document title.
        score: Relevance score assigned by the retriever.
    """

    chunk_id: str
    text: str
    page_number: int
    document_id: str
    document_title: str
    score: float


@dataclass(frozen=True, slots=True)
class GraphContext:
    """
    A snapshot of graph neighbourhood returned alongside retrieved chunks.

    Attributes:
        entities: Entities related to the retrieved chunks.
        relationships: Relationships connecting those entities.
    """

    entities: tuple[dict[str, object], ...]
    relationships: tuple[dict[str, object], ...]


@dataclass(frozen=True, slots=True)
class RetrievedContext:
    """
    The complete evidence package delivered to an agent.

    Attributes:
        query: The original user query.
        chunks: Ranked chunks from hybrid retrieval.
        graph_context: Relevant graph neighbourhood.
    """

    query: str
    chunks: tuple[RetrievedChunk, ...]
    graph_context: GraphContext
