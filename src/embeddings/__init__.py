"""
Embeddings layer for Project Oracle.
"""

from src.embeddings.embedder import (
    EmbeddingError,
    EmbeddingModel,
    SentenceTransformerEmbedder,
    create_embedder,
)

__all__ = [
    "EmbeddingError",
    "EmbeddingModel",
    "SentenceTransformerEmbedder",
    "create_embedder",
]
