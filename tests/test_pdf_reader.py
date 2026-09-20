"""Tests for the PDF reader."""

from pathlib import Path

import pytest

from src.ingestion.pdf_reader import (
    ExtractedDocument,
    ExtractedPage,
    PDFReader,
    PDFReaderError,
    create_pdf_reader,
)
from tests.conftest import FLOODS_PDF, requires_floods_pdf


class TestPDFReaderValidation:
    """Input validation — no PDF file required."""

    def test_invalid_path_type_raises(self) -> None:
        reader = create_pdf_reader()
        with pytest.raises(PDFReaderError, match="string or pathlib.Path"):
            reader.read(123)  # type: ignore[arg-type]

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        reader = create_pdf_reader()
        with pytest.raises(PDFReaderError, match="does not exist"):
            reader.read(tmp_path / "missing.pdf")

    def test_directory_raises(self, tmp_path: Path) -> None:
        reader = create_pdf_reader()
        with pytest.raises(PDFReaderError, match="not a file"):
            reader.read(tmp_path)

    def test_wrong_extension_raises(self, tmp_path: Path) -> None:
        text_file = tmp_path / "document.txt"
        text_file.write_text("hello")
        reader = create_pdf_reader()
        with pytest.raises(PDFReaderError, match="Expected a PDF"):
            reader.read(text_file)


@requires_floods_pdf
class TestPDFReaderWithData:
    """Tests that require the Floods.pdf data file."""

    def test_extract_document(self) -> None:
        reader = create_pdf_reader()
        document = reader.read(FLOODS_PDF)

        assert isinstance(document, ExtractedDocument)
        assert document.page_count == 16
        assert document.pages[0].page_number == 1
        assert document.pages[-1].page_number == 16

    def test_pages_have_text(self) -> None:
        reader = create_pdf_reader()
        document = reader.read(FLOODS_PDF)

        for page in document.pages:
            assert isinstance(page, ExtractedPage)
            assert isinstance(page.text, str)

    def test_source_path_preserved(self) -> None:
        reader = create_pdf_reader()
        document = reader.read(FLOODS_PDF)

        assert document.source_path == FLOODS_PDF

    def test_full_text_is_nonempty(self) -> None:
        reader = create_pdf_reader()
        document = reader.read(FLOODS_PDF)

        assert len(document.text) > 0