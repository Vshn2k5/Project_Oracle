from src.ingestion.pdf_reader import PDFReaderError, create_pdf_reader


def main() -> None:
    reader = create_pdf_reader()

    document = reader.read(
        "data/raw/Floods.pdf"
    )

    print(f"Document: {document.source_path}")
    print(f"Pages: {document.page_count}")

    for page in document.pages[:3]:
        print(f"\n--- Page {page.page_number} ---")
        print(page.text[:500])

    assert document.page_count == 16
    assert document.pages[0].page_number == 1
    assert document.pages[-1].page_number == 16

    try:
        reader.read(123)  # type: ignore[arg-type]
    except PDFReaderError as exc:
        assert str(exc) == "PDF path must be a string or pathlib.Path."
    else:
        raise AssertionError("Invalid PDF path was accepted")

    print("PDF reader assertions passed.")


if __name__ == "__main__":
    main()