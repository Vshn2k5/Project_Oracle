from src.ingestion.pdf_reader import create_pdf_reader
from src.ingestion.text_cleaner import TextCleaner, create_text_cleaner


def main() -> None:
    reader = create_pdf_reader()
    cleaner = create_text_cleaner()

    document = reader.read("data/raw/Floods.pdf")
    cleaned_document = cleaner.clean_document(document)

    print(f"Document: {cleaned_document.source_path}")
    print(f"Pages: {cleaned_document.page_count}")

    for page in cleaned_document.pages[:3]:
        print(f"\n--- Cleaned Page {page.page_number} ---")
        print(page.text[:700])

    cleaner = TextCleaner()
    assert cleaner.clean_text("com-\nmunities") == "communities"
    assert cleaner.clean_text("first\n\n\nsecond") == "first\n\nsecond"
    assert cleaner.clean_text("first-\n\nsecond") == "first-\n\nsecond"
    assert cleaner.clean_text("\r\n  text  \t\r\n") == "text"
    print("Text normalization assertions passed.")


if __name__ == "__main__":
    main()
