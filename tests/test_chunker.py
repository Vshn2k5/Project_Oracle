"""Tests for the document chunker."""

from pathlib import Path

import pytest

from src.ingestion.chunker import (
    ChunkingError,
    DocumentChunk,
    DocumentChunker,
    create_document_chunker,
)
from src.ingestion.text_cleaner import CleanedDocument, CleanedPage
from tests.conftest import FLOODS_PDF, requires_floods_pdf
from src.ingestion.pdf_reader import create_pdf_reader
from src.ingestion.text_cleaner import create_text_cleaner


class TestDocumentChunkerValidation:
    """Constructor validation — no files needed."""

    def test_zero_max_characters_raises(self) -> None:
        with pytest.raises(ValueError, match="greater than zero"):
            DocumentChunker(max_characters=0)

    def test_negative_overlap_raises(self) -> None:
        with pytest.raises(ValueError, match="cannot be negative"):
            DocumentChunker(max_characters=100, overlap_characters=-1)

    def test_overlap_equals_max_raises(self) -> None:
        with pytest.raises(ValueError, match="smaller than max"):
            DocumentChunker(max_characters=100, overlap_characters=100)

    def test_overlap_exceeds_max_raises(self) -> None:
        with pytest.raises(ValueError, match="smaller than max"):
            DocumentChunker(max_characters=100, overlap_characters=200)


class TestDocumentChunkerUnit:
    """Unit tests using synthetic documents."""

    def _make_document(
        self,
        pages: list[tuple[int, str]],
        source_path: Path | None = None,
    ) -> CleanedDocument:
        """Build a CleanedDocument from (page_number, text) pairs."""
        path = source_path or FLOODS_PDF
        return CleanedDocument(
            source_path=path,
            pages=tuple(
                CleanedPage(page_number=num, text=text)
                for num, text in pages
            ),
        )

    @requires_floods_pdf
    def test_basic_chunking(self) -> None:
        doc = self._make_document(
            [(1, "This is a short paragraph on page one.")],
        )
        chunker = DocumentChunker(max_characters=200, overlap_characters=0)
        chunks = chunker.chunk_document(doc)

        assert len(chunks) >= 1
        assert all(isinstance(c, DocumentChunk) for c in chunks)

    @requires_floods_pdf
    def test_chunk_size_respected(self) -> None:
        text = "Word " * 300  # ~1500 chars
        doc = self._make_document([(1, text)])
        chunker = DocumentChunker(max_characters=200, overlap_characters=50)
        chunks = chunker.chunk_document(doc)

        for chunk in chunks:
            assert len(chunk.text) <= 200

    @requires_floods_pdf
    def test_page_provenance(self) -> None:
        doc = self._make_document([
            (1, "Page one content here."),
            (2, "Page two content here."),
        ])
        chunker = DocumentChunker(max_characters=500, overlap_characters=0)
        chunks = chunker.chunk_document(doc)

        page_numbers = {c.page_number for c in chunks}
        assert 1 in page_numbers
        assert 2 in page_numbers

    @requires_floods_pdf
    def test_chunk_ids_unique(self) -> None:
        doc = self._make_document([
            (1, "First page with enough text to produce chunks."),
            (2, "Second page with more text content."),
        ])
        chunker = DocumentChunker(max_characters=50, overlap_characters=10)
        chunks = chunker.chunk_document(doc)

        ids = [c.chunk_id for c in chunks]
        assert len(ids) == len(set(ids))

    @requires_floods_pdf
    def test_document_id_deterministic(self) -> None:
        doc = self._make_document([(1, "Content.")])
        chunker = create_document_chunker()
        chunks_a = chunker.chunk_document(doc)
        chunks_b = chunker.chunk_document(doc)

        assert chunks_a[0].document_id == chunks_b[0].document_id

    @requires_floods_pdf
    def test_source_path_preserved(self) -> None:
        doc = self._make_document([(1, "Content.")])
        chunker = create_document_chunker()
        chunks = chunker.chunk_document(doc)

        assert chunks[0].source_path == str(FLOODS_PDF)

    @requires_floods_pdf
    def test_empty_page_produces_no_chunks(self) -> None:
        doc = self._make_document([
            (1, ""),
            (2, "Has content."),
        ])
        chunker = DocumentChunker(max_characters=500, overlap_characters=0)
        chunks = chunker.chunk_document(doc)

        # No chunk should be from page 1 (empty)
        assert all(c.page_number != 1 for c in chunks)

    @requires_floods_pdf
    def test_chunk_index_monotonic(self) -> None:
        doc = self._make_document([
            (1, "Short text."),
            (2, "Another short text."),
        ])
        chunker = DocumentChunker(max_characters=500, overlap_characters=0)
        chunks = chunker.chunk_document(doc)

        indices = [c.chunk_index for c in chunks]
        assert indices == sorted(indices)

    def test_missing_source_raises(self, tmp_path: Path) -> None:
        missing = tmp_path / "nonexistent.pdf"
        doc = CleanedDocument(
            source_path=missing,
            pages=(CleanedPage(page_number=1, text="text"),),
        )
        chunker = create_document_chunker()
        with pytest.raises(ChunkingError, match="does not exist"):
            chunker.chunk_document(doc)

    @requires_floods_pdf
    def test_boundary_chunks_respect_limit(self) -> None:
        """Boundary test: chunks near the max size boundary."""
        bounded_chunker = DocumentChunker(
            max_characters=120, overlap_characters=40,
        )
        doc = self._make_document([
            (1, ("A" * 100) + "\n\n" + ("B" * 110)),
        ])
        chunks = bounded_chunker.chunk_document(doc)
        assert all(len(c.text) <= 120 for c in chunks)


@requires_floods_pdf
class TestDocumentChunkerWithData:
    """Full pipeline test with Floods.pdf."""

    def test_full_pipeline(self) -> None:
        reader = create_pdf_reader()
        cleaner = create_text_cleaner()
        chunker = create_document_chunker()

        doc = reader.read(FLOODS_PDF)
        cleaned = cleaner.clean_document(doc)
        chunks = chunker.chunk_document(cleaned)

        assert len(chunks) > 0
        assert all(chunk.document_id for chunk in chunks)
        assert all(chunk.chunk_id for chunk in chunks)
        assert all(chunk.text for chunk in chunks)
        assert all(chunk.page_number >= 1 for chunk in chunks)
        assert all(len(chunk.text) <= 1200 for chunk in chunks)