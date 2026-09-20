"""
Document-level models for Project Oracle.

Existing ingestion models (``ExtractedPage``, ``ExtractedDocument``,
``CleanedPage``, ``CleanedDocument``, ``DocumentChunk``) are defined in
their respective ingestion modules and re-exported here for convenience.

This module adds the ``EmbeddedChunk`` model which pairs a chunk with
its vector embedding without modifying the core chunking pipeline.
"""

from dataclasses import dataclass

# Re-export existing ingestion models so consumers can import from one place.
from src.ingestion.pdf_reader import ExtractedPage, ExtractedDocument
from src.ingestion.text_cleaner import CleanedPage, CleanedDocument
from src.ingestion.chunker import DocumentChunk

__all__ = [
    "ExtractedPage",
    "ExtractedDocument",
    "CleanedPage",
    "CleanedDocument",
    "DocumentChunk",
    "EmbeddedChunk",
]


@dataclass(frozen=True, slots=True)
class EmbeddedChunk:
    """
    A document chunk paired with its vector embedding.

    Keeps the embedding concern separate from the chunking pipeline so
    that ingestion and chunking remain independent of the embedding model.
    """

    chunk: DocumentChunk
    embedding: tuple[float, ...]
