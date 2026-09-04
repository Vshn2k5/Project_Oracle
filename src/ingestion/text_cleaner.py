import re
from dataclasses import dataclass
from pathlib import Path

from src.ingestion.pdf_reader import ExtractedDocument, ExtractedPage


@dataclass(frozen=True, slots=True)
class CleanedPage:
    """
    Represents cleaned text for one PDF page.
    """

    page_number: int
    text: str


@dataclass(frozen=True, slots=True)
class CleanedDocument:
    """
    Represents a complete document after text normalization.
    """

    source_path: Path
    pages: tuple[CleanedPage, ...]

    @property
    def page_count(self) -> int:
        """Return the number of pages in the cleaned document."""
        return len(self.pages)

    @property
    def text(self) -> str:
        """Return the complete cleaned document text."""
        return "\n\n".join(
            page.text
            for page in self.pages
            if page.text
        )


class TextCleaner:
    """
    Cleans PDF-extracted text while preserving meaningful content and
    page boundaries.
    """

    _HYPHENATED_LINE_BREAK = re.compile(r"(?<=\w)-[ \t]*\n[ \t]*(?=\w)")
    _TRAILING_WHITESPACE = re.compile(r"[ \t]+$", re.MULTILINE)
    _EXCESSIVE_BLANK_LINES = re.compile(r"\n{3,}")

    def clean_text(self, text: str) -> str:
        """
        Normalize extracted PDF text.

        The cleaning process:
        1. Normalizes line endings.
        2. Repairs words split across line boundaries.
        3. Removes trailing whitespace.
        4. Normalizes excessive blank lines.
        5. Removes surrounding whitespace.
        """
        if not isinstance(text, str):
            raise TypeError("Text to clean must be a string.")

        if not text:
            return ""

        cleaned = text.replace("\r\n", "\n").replace("\r", "\n")

        cleaned = self._HYPHENATED_LINE_BREAK.sub("", cleaned)

        cleaned = self._TRAILING_WHITESPACE.sub("", cleaned)

        cleaned = self._EXCESSIVE_BLANK_LINES.sub("\n\n", cleaned)

        return cleaned.strip()

    def clean_page(self, page: ExtractedPage) -> CleanedPage:
        """Clean the text belonging to one extracted page."""
        return CleanedPage(
            page_number=page.page_number,
            text=self.clean_text(page.text),
        )

    def clean_document(
        self,
        document: ExtractedDocument,
    ) -> CleanedDocument:
        """Clean every page in an extracted document."""
        pages = tuple(
            self.clean_page(page)
            for page in document.pages
        )

        return CleanedDocument(
            source_path=document.source_path,
            pages=pages,
        )


def create_text_cleaner() -> TextCleaner:
    """Create a text cleaner for Project Oracle."""
    return TextCleaner()