from src.ingestion.chunker import DocumentChunker, create_document_chunker
from src.ingestion.pdf_reader import create_pdf_reader
from src.ingestion.text_cleaner import (
    CleanedDocument,
    CleanedPage,
    create_text_cleaner,
)


def main() -> None:
    reader = create_pdf_reader()
    cleaner = create_text_cleaner()
    chunker = create_document_chunker()

    extracted_document = reader.read("data/raw/Floods.pdf")
    cleaned_document = cleaner.clean_document(extracted_document)
    chunks = chunker.chunk_document(cleaned_document)

    print(f"Document: {cleaned_document.source_path}")
    print(f"Pages: {cleaned_document.page_count}")
    print(f"Chunks: {len(chunks)}")

    for chunk in chunks[:5]:
        print("\n--- Chunk ---")
        print(f"ID: {chunk.chunk_id}")
        print(f"Document ID: {chunk.document_id}")
        print(f"Page: {chunk.page_number}")
        print(f"Index: {chunk.chunk_index}")
        print(f"Characters: {len(chunk.text)}")
        print(chunk.text[:500])

    print("\n=== Page 6 Chunks ===")

    for chunk in chunks:
        if chunk.page_number == 6:
            print("\n--- Chunk ---")
            print(f"ID: {chunk.chunk_id}")
            print(f"Characters: {len(chunk.text)}")
            print(chunk.text)

    assert chunks
    assert all(chunk.document_id for chunk in chunks)
    assert all(chunk.chunk_id for chunk in chunks)
    assert all(chunk.text for chunk in chunks)
    assert all(chunk.page_number >= 1 for chunk in chunks)
    assert all(len(chunk.text) <= 1200 for chunk in chunks)

    bounded_chunker = DocumentChunker(max_characters=120, overlap_characters=40)
    boundary_document = CleanedDocument(
        source_path=cleaned_document.source_path,
        pages=(
            CleanedPage(
                page_number=1,
                text=("A" * 100) + "\n\n" + ("B" * 110),
            ),
        ),
    )
    boundary_chunks = bounded_chunker.chunk_document(boundary_document)
    assert all(len(chunk.text) <= 120 for chunk in boundary_chunks)

    print("\nChunking assertions passed.")


if __name__ == "__main__":
    main()