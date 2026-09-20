"""Tests for the text cleaner."""

import pytest

from src.ingestion.pdf_reader import ExtractedDocument, ExtractedPage
from src.ingestion.text_cleaner import (
    CleanedDocument,
    CleanedPage,
    TextCleaner,
    create_text_cleaner,
)
from tests.conftest import FLOODS_PDF, requires_floods_pdf
from src.ingestion.pdf_reader import create_pdf_reader


class TestTextCleanerUnit:
    """Unit tests for text cleaning — no external files needed."""

    def test_hyphenated_line_break(self) -> None:
        cleaner = TextCleaner()
        assert cleaner.clean_text("com-\nmunities") == "communities"

    def test_excessive_blank_lines(self) -> None:
        cleaner = TextCleaner()
        assert cleaner.clean_text("first\n\n\nsecond") == "first\n\nsecond"

    def test_hyphen_across_paragraph_boundary_preserved(self) -> None:
        cleaner = TextCleaner()
        assert cleaner.clean_text("first-\n\nsecond") == "first-\n\nsecond"

    def test_trailing_whitespace_removed(self) -> None:
        cleaner = TextCleaner()
        assert cleaner.clean_text("\r\n  text  \t\r\n") == "text"

    def test_empty_string(self) -> None:
        cleaner = TextCleaner()
        assert cleaner.clean_text("") == ""

    def test_non_string_raises(self) -> None:
        cleaner = TextCleaner()
        with pytest.raises(TypeError, match="string"):
            cleaner.clean_text(42)  # type: ignore[arg-type]

    def test_clean_page(self) -> None:
        cleaner = TextCleaner()
        page = ExtractedPage(page_number=1, text="com-\nmunities  ")
        cleaned = cleaner.clean_page(page)

        assert isinstance(cleaned, CleanedPage)
        assert cleaned.page_number == 1
        assert cleaned.text == "communities"

    def test_clean_document(self) -> None:
        cleaner = TextCleaner()
        document = ExtractedDocument(
            source_path=__file__,  # type: ignore[arg-type]
            pages=(
                ExtractedPage(page_number=1, text="hello  "),
                ExtractedPage(page_number=2, text="  world"),
            ),
        )
        cleaned = cleaner.clean_document(document)

        assert isinstance(cleaned, CleanedDocument)
        assert cleaned.page_count == 2
        assert cleaned.pages[0].text == "hello"
        assert cleaned.pages[1].text == "world"

    def test_windows_line_endings(self) -> None:
        cleaner = TextCleaner()
        result = cleaner.clean_text("line1\r\nline2\r\nline3")
        assert "\r" not in result
        assert "line1\nline2\nline3" == result


@requires_floods_pdf
class TestTextCleanerWithData:
    """Tests that exercise cleaning against real PDF output."""

    def test_cleaned_document_preserves_pages(self) -> None:
        reader = create_pdf_reader()
        cleaner = create_text_cleaner()

        document = reader.read(FLOODS_PDF)
        cleaned = cleaner.clean_document(document)

        assert cleaned.page_count == document.page_count
        assert cleaned.source_path == document.source_path
