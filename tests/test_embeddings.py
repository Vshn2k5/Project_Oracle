"""
Unit tests for the embedding abstraction.
"""

import pytest
from src.embeddings.embedder import (
    EmbeddingError,
    EmbeddingModel,
    SentenceTransformerEmbedder,
)
from src.models.document import DocumentChunk


class TestEmbeddingModelUnit:
    def test_sentence_transformer_initialization_dimension_mismatch(self):
        # We expect 384, but if we mistakenly assert 128, it should fail
        with pytest.raises(ValueError, match="Configured embedding dimension"):
            SentenceTransformerEmbedder(
                model_name="all-MiniLM-L6-v2", expected_dimension=128
            )

    def test_sentence_transformer_embed_text(self):
        embedder = SentenceTransformerEmbedder("all-MiniLM-L6-v2", 384)
        emb = embedder.embed_text("Test sentence")
        assert len(emb) == 384
        assert isinstance(emb, list)
        assert isinstance(emb[0], float)

    def test_sentence_transformer_embed_batch(self):
        embedder = SentenceTransformerEmbedder("all-MiniLM-L6-v2", 384)
        embs = embedder.embed_batch(["Test 1", "Test 2", "Test 3"])
        assert len(embs) == 3
        for e in embs:
            assert len(e) == 384

    def test_embed_chunks(self):
        embedder = SentenceTransformerEmbedder("all-MiniLM-L6-v2", 384)
        chunks = [
            DocumentChunk("C1", "Text 1", 1, 0, "path", "D1"),
            DocumentChunk("C2", "Text 2", 1, 1, "path", "D1"),
        ]
        
        embedded_chunks = embedder.embed_chunks(chunks)
        assert len(embedded_chunks) == 2
        assert embedded_chunks[0].chunk.chunk_id == "C1"
        assert len(embedded_chunks[0].embedding) == 384
