"""
Embedding Abstraction.

Provides a unified interface for embedding generation, allowing the
backend model to be swapped without changing ingestion code.
"""

import abc
import logging
from typing import Sequence

from src.config.settings import Settings
from src.models.document import DocumentChunk, EmbeddedChunk

logger = logging.getLogger(__name__)


class EmbeddingError(RuntimeError):
    """Raised when embedding generation fails."""


class EmbeddingModel(abc.ABC):
    """Abstract interface for text embedding."""

    @property
    @abc.abstractmethod
    def dimension(self) -> int:
        """The output dimension of the embeddings."""
        pass

    @abc.abstractmethod
    def embed_text(self, text: str) -> list[float]:
        """Embed a single string."""
        pass

    @abc.abstractmethod
    def embed_batch(self, texts: Sequence[str]) -> list[list[float]]:
        """Embed a batch of strings."""
        pass

    def embed_chunks(self, chunks: Sequence[DocumentChunk]) -> list[EmbeddedChunk]:
        """Convenience method to embed a batch of DocumentChunks."""
        if not chunks:
            return []

        texts = [c.text for c in chunks]
        embeddings = self.embed_batch(texts)

        return [
            EmbeddedChunk(chunk=chunk, embedding=tuple(emb))
            for chunk, emb in zip(chunks, embeddings)
        ]


class SentenceTransformerEmbedder(EmbeddingModel):
    """Local embedding implementation using sentence-transformers."""

    def __init__(self, model_name: str, expected_dimension: int) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "sentence-transformers is required. "
                "Install it with `pip install sentence-transformers`."
            ) from exc

        logger.info("Loading embedding model: %s", model_name)
        self._model = SentenceTransformer(model_name)
        
        actual_dim = self._model.get_sentence_embedding_dimension()
        if actual_dim != expected_dimension:
            raise ValueError(
                f"Configured embedding dimension ({expected_dimension}) does not "
                f"match the actual model dimension ({actual_dim})."
            )
            
        self._dimension = expected_dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_text(self, text: str) -> list[float]:
        try:
            # encode returns a numpy array, convert to float list
            embedding = self._model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as exc:
            logger.error("Failed to embed text: %s", exc)
            raise EmbeddingError("Embedding generation failed.") from exc

    def embed_batch(self, texts: Sequence[str]) -> list[list[float]]:
        try:
            embeddings = self._model.encode(
                list(texts),
                batch_size=32,
                convert_to_numpy=True,
                show_progress_bar=False,
            )
            return [emb.tolist() for emb in embeddings]
        except Exception as exc:
            logger.error("Failed to embed batch of %d texts: %s", len(texts), exc)
            raise EmbeddingError("Batch embedding generation failed.") from exc


def create_embedder(settings: Settings) -> EmbeddingModel:
    """Factory to create the configured embedding model."""
    # For now, we only support sentence-transformers locally.
    # The provider could be specified in settings if we add more (e.g. OpenAI).
    
    return SentenceTransformerEmbedder(
        model_name=settings.embedding_model,
        expected_dimension=settings.embedding_dimension,
    )
