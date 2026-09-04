import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

from src.ingestion.text_cleaner import CleanedDocument, CleanedPage


@dataclass(frozen=True, slots=True)
class DocumentChunk:
    """
    Represents one retrieval-ready chunk of a source document.
    """

    chunk_id: str
    document_id: str
    page_number: int
    chunk_index: int
    text: str


class ChunkingError(RuntimeError):
    """Raised when a document cannot be chunked safely."""


class DocumentChunker:
    """
    Splits cleaned document pages into deterministic, context-preserving
    chunks suitable for retrieval and downstream knowledge extraction.
    """

    def __init__(
        self,
        max_characters: int = 1200,
        overlap_characters: int = 200,
    ) -> None:
        if max_characters <= 0:
            raise ValueError("max_characters must be greater than zero.")

        if overlap_characters < 0:
            raise ValueError("overlap_characters cannot be negative.")

        if overlap_characters >= max_characters:
            raise ValueError(
                "overlap_characters must be smaller than max_characters."
            )

        self._max_characters = max_characters
        self._overlap_characters = overlap_characters

    def create_document_id(self, source_path: Path) -> str:
        """
        Create a deterministic document identifier from file contents.

        The same file contents always produce the same identifier.
        """
        try:
            digest = hashlib.sha256()

            with source_path.open("rb") as file:
                for block in iter(lambda: file.read(1024 * 1024), b""):
                    digest.update(block)

        except OSError as exc:
            raise ChunkingError(
                f"Unable to calculate document ID for: {source_path}"
            ) from exc

        return f"DOC-{digest.hexdigest()[:16]}"

    def chunk_document(
        self,
        document: CleanedDocument,
    ) -> tuple[DocumentChunk, ...]:
        """
        Split a cleaned document into page-aware chunks.

        Page boundaries are preserved so every chunk retains source
        provenance.
        """
        if not document.source_path.exists():
            raise ChunkingError(
                f"Source document does not exist: {document.source_path}"
            )

        document_id = self.create_document_id(document.source_path)

        chunks: list[DocumentChunk] = []
        chunk_index = 0

        for page in document.pages:
            page_chunks = self._chunk_page(page)

            for text in page_chunks:
                chunks.append(
                    DocumentChunk(
                        chunk_id=(
                            f"{document_id}-"
                            f"P{page.page_number:02d}-"
                            f"C{chunk_index:04d}"
                        ),
                        document_id=document_id,
                        page_number=page.page_number,
                        chunk_index=chunk_index,
                        text=text,
                    )
                )

                chunk_index += 1

        return tuple(chunks)

    def _chunk_page(self, page: CleanedPage) -> tuple[str, ...]:
        """Split one page while preserving paragraph boundaries."""
        if not page.text:
            return ()

        paragraphs = self._split_paragraphs(page.text)

        chunks: list[str] = []
        current_parts: list[str] = []
        current_length = 0

        for paragraph in paragraphs:
            paragraph = paragraph.strip()

            if not paragraph:
                continue

            if len(paragraph) > self._max_characters:
                if current_parts:
                    chunks.append("\n\n".join(current_parts))
                    current_parts = []
                    current_length = 0

                chunks.extend(self._split_long_paragraph(paragraph))
                continue

            separator_length = 2 if current_parts else 0
            proposed_length = (
                current_length
                + separator_length
                + len(paragraph)
            )

            if proposed_length <= self._max_characters:
                current_parts.append(paragraph)
                current_length = proposed_length
                continue

            chunks.append("\n\n".join(current_parts))

            overlap = self._build_overlap(
                current_parts,
                max_length=self._max_characters - len(paragraph) - 2,
            )

            current_parts = [overlap, paragraph] if overlap else [paragraph]
            current_length = sum(len(part) for part in current_parts) + (
                2 if overlap else 0
            )

        if current_parts:
            chunks.append("\n\n".join(current_parts))

        return tuple(chunks)

    @staticmethod
    def _split_paragraphs(text: str) -> tuple[str, ...]:
        """Split text using blank lines as paragraph boundaries."""
        return tuple(
            paragraph.strip()
            for paragraph in re.split(r"\n\s*\n", text)
            if paragraph.strip()
        )

    def _split_long_paragraph(self, paragraph: str) -> tuple[str, ...]:
        """
        Split a paragraph that exceeds the maximum size.

        Sentences are preferred as boundaries. If an individual sentence is
        still too long, it is split by character length.
        """
        sentences = tuple(
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])\s+", paragraph)
            if sentence.strip()
        )

        if len(sentences) <= 1:
            return self._split_by_length(paragraph)

        chunks: list[str] = []
        current = ""

        for sentence in sentences:
            proposed = (
                sentence
                if not current
                else f"{current} {sentence}"
            )

            if len(proposed) <= self._max_characters:
                current = proposed
                continue

            if current:
                chunks.append(current)

            if len(sentence) <= self._max_characters:
                current = sentence
            else:
                chunks.extend(self._split_by_length(sentence))
                current = ""

        if current:
            chunks.append(current)

        return tuple(chunks)

    def _split_by_length(self, text: str) -> tuple[str, ...]:
        """Split exceptionally long text using word boundaries."""
        chunks: list[str] = []
        start = 0

        while start < len(text):
            end = min(
                start + self._max_characters,
                len(text),
            )

            if end < len(text):
                boundary = text.rfind(" ", start, end)

                if boundary > start:
                    end = boundary

            chunk = text[start:end].strip()

            if chunk:
                chunks.append(chunk)

            if end >= len(text):
                break

            next_start = max(
                end - self._overlap_characters,
                start + 1,
            )

            start = next_start

        return tuple(chunks)

    def _build_overlap(
        self,
        current_parts: list[str],
        *,
        max_length: int | None = None,
    ) -> str:
        """Build a bounded overlap from the end of the previous chunk."""
        if self._overlap_characters == 0:
            return ""

        text = "\n\n".join(current_parts)
        overlap_limit = self._overlap_characters

        if max_length is not None:
            overlap_limit = min(overlap_limit, max_length)

        if overlap_limit <= 0:
            return ""

        if len(text) <= overlap_limit:
            return text

        overlap = text[-overlap_limit:]

        # Avoid starting the overlap in the middle of a word.
        first_space = overlap.find(" ")

        if first_space > 0:
            overlap = overlap[first_space + 1 :]

        return overlap.strip()


def create_document_chunker() -> DocumentChunker:
    """Create the default Project Oracle document chunker."""
    return DocumentChunker(
        max_characters=1200,
        overlap_characters=200,
    )