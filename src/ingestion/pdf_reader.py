from dataclasses import dataclass
from pathlib import Path

import pymupdf


@dataclass(frozen=True, slots=True)
class ExtractedPage:
    """
    Represents the extracted text and metadata for one PDF page.
    """

    page_number: int
    text: str


@dataclass(frozen=True, slots=True)
class ExtractedDocument:
    """
    Represents the extracted content of a complete PDF document.
    """

    source_path: Path
    pages: tuple[ExtractedPage, ...]

    @property
    def page_count(self) -> int:
        """Return the number of pages successfully extracted."""
        return len(self.pages)

    @property
    def text(self) -> str:
        """
        Return the complete document text with page boundaries preserved.
        """
        return "\n\n".join(
            page.text
            for page in self.pages
            if page.text
        )


class PDFReaderError(RuntimeError):
    """Raised when a PDF cannot be read or processed."""


class PDFReader:
    """
    Extracts text from PDF documents while preserving page boundaries.
    """

    def read(self, file_path: str | Path) -> ExtractedDocument:
        """
        Extract text from a PDF document.

        Args:
            file_path: Path to the PDF document.

        Returns:
            ExtractedDocument containing page-wise extracted text.

        Raises:
            PDFReaderError: If the file does not exist, is not a PDF,
                or cannot be processed.
        """
        try:
            path = Path(file_path)
        except TypeError as exc:
            raise PDFReaderError(
                "PDF path must be a string or pathlib.Path."
            ) from exc

        if not path.exists():
            raise PDFReaderError(
                f"PDF file does not exist: {path}"
            )

        if not path.is_file():
            raise PDFReaderError(
                f"PDF path is not a file: {path}"
            )

        if path.suffix.lower() != ".pdf":
            raise PDFReaderError(
                f"Expected a PDF file, received: {path.suffix or 'no extension'}"
            )

        try:
            with pymupdf.open(path) as document:
                pages = tuple(
                    ExtractedPage(
                        page_number=page_index + 1,
                        text=page.get_text("text").strip(),
                    )
                    for page_index, page in enumerate(document)
                )

        except (pymupdf.FileDataError, OSError, RuntimeError) as exc:
            raise PDFReaderError(
                f"Failed to read PDF document: {path}"
            ) from exc

        return ExtractedDocument(
            source_path=path,
            pages=pages,
        )


def create_pdf_reader() -> PDFReader:
    """Create a PDF reader for Project Oracle."""
    return PDFReader()