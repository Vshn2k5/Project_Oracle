"""
Ingestion Orchestrator.

Coordinates the pipeline: PDF -> Chunks -> Embeddings -> Extraction -> Neo4j.
"""

import logging
from collections import defaultdict
from pathlib import Path

from src.embeddings.embedder import EmbeddingModel
from src.extraction.llm import LLMProvider
from src.extraction.pipeline import ExtractionPipeline
from src.ingestion.chunker import DocumentChunker
from src.ingestion.pdf_reader import PDFReader
from src.ingestion.text_cleaner import TextCleaner
from src.knowledge_graph.repository import KnowledgeGraphRepository

logger = logging.getLogger(__name__)


class IngestionOrchestrator:
    """Coordinates full document ingestion into the Knowledge Graph."""

    def __init__(
        self,
        repository: KnowledgeGraphRepository,
        embedder: EmbeddingModel,
        llm_provider: LLMProvider,
    ) -> None:
        self.repository = repository
        self.embedder = embedder
        self.extractor = ExtractionPipeline(llm_provider)

        # Basic text processing components
        self.reader = PDFReader()
        self.cleaner = TextCleaner()
        self.chunker = DocumentChunker()

    def process_document(self, file_path: Path | str, max_chunks: int | None = None) -> bool:
        """
        Process a document end-to-end.
        
        Args:
            file_path: Path to the PDF file.
            max_chunks: Optional limit on chunks to process (for smoke testing).
            
        Returns:
            True if the document was processed successfully.
        """
        file_path = Path(file_path)
        if not file_path.exists():
            logger.error("File not found: %s", file_path)
            return False

        logger.info("Starting ingestion for %s", file_path)
        
        # 1. Read & Clean
        raw_doc = self.reader.read_pdf(file_path)
        clean_doc = self.cleaner.clean_document(raw_doc)
        
        # 2. Chunk
        chunks = self.chunker.chunk_document(clean_doc)
        if not chunks:
            logger.warning("No text extracted from %s", file_path)
            return False
            
        if max_chunks:
            logger.info("Limiting ingestion to first %d chunks for testing.", max_chunks)
            chunks = chunks[:max_chunks]

        # 3. Embed
        logger.info("Generating embeddings for %d chunks...", len(chunks))
        embedded_chunks = self.embedder.embed_chunks(chunks)

        # 4. Extract
        logger.info("Extracting structured knowledge...")
        all_entities = []
        all_relationships = []
        all_claims = []
        all_evidence = []
        
        for e_chunk in embedded_chunks:
            extracted = self.extractor.extract_from_chunk(e_chunk.chunk)
            all_entities.extend(extracted["entities"])
            all_relationships.extend(extracted["relationships"])
            all_claims.extend(extracted["claims"])
            all_evidence.extend(extracted["evidence"])

        # 5. Write to Neo4j
        logger.info("Writing to Neo4j...")
        try:
            self._write_to_neo4j(
                document=clean_doc,
                embedded_chunks=embedded_chunks,
                entities=all_entities,
                relationships=all_relationships,
                claims=all_claims,
                evidence=all_evidence,
            )
            logger.info("Successfully ingested %s", file_path)
            return True
        except Exception as exc:
            logger.error("Failed to write document to Neo4j: %s", exc)
            return False

    def _write_to_neo4j(
        self,
        document,
        embedded_chunks,
        entities,
        relationships,
        claims,
        evidence,
    ) -> None:
        """Batch write all extracted components to Neo4j."""
        
        # Write Document
        self.repository.save_document(document)
        
        # Write Chunks & Embeddings
        chunk_dicts = []
        for e_chunk in embedded_chunks:
            c = e_chunk.chunk
            chunk_dicts.append({
                "id": c.chunk_id,
                "text": c.text,
                "page": c.page_number,
                "chunk_index": c.chunk_index,
                "source_path": str(c.source_path),
                "document_id": c.document_id,
                "embedding": list(e_chunk.embedding),
            })
        self.repository.batch_upsert_chunks(chunk_dicts)
        
        # Link Document -> Chunks
        doc_chunk_links = [
            {"document_id": document.document_id, "chunk_id": c.chunk.chunk_id}
            for c in embedded_chunks
        ]
        self.repository.batch_link_document_chunks(doc_chunk_links)
        
        # Group entities by label
        entities_by_label = defaultdict(list)
        for e in entities:
            entities_by_label[e.label].append({
                "id": e.entity_id,
                "name": e.name,
                "entity_type": e.entity_type,
                "description": e.description,
                "source_chunk_id": e.source_chunk_id,
            })
            
        for label, group in entities_by_label.items():
            self.repository.batch_upsert_entities(label, group)
            
        # Group relationships by type
        rels_by_type = defaultdict(list)
        for r in relationships:
            rels_by_type[r.relationship_type].append({
                "source_id": r.source_entity_id,
                "target_id": r.target_entity_id,
                "description": r.description,
                "source_chunk_id": r.source_chunk_id,
            })
            
        for r_type, group in rels_by_type.items():
            self.repository.batch_link_relationships(r_type, group)
            
        # Claims
        claim_dicts = [
            {
                "id": c.claim_id,
                "statement": c.statement,
                "subject_entity_id": c.subject_entity_id,
                "source_chunk_id": c.source_chunk_id,
                "confidence": c.confidence,
            }
            for c in claims
        ]
        self.repository.batch_upsert_claims(claim_dicts)
        
        # Evidence
        evidence_dicts = [
            {
                "id": e.evidence_id,
                "claim_id": e.claim_id,
                "chunk_id": e.chunk_id,
                "text": e.text,
                "supports": e.supports,
            }
            for e in evidence
        ]
        self.repository.batch_upsert_evidence(evidence_dicts)
        
        # Provenance Relationships
        # (Claim)-[:SUPPORTED_BY]->(Evidence)
        supp_links = [
            {
                "source_id": e.claim_id,
                "target_id": e.evidence_id,
                "description": "Supports claim",
                "source_chunk_id": e.chunk_id,
            }
            for e in evidence
        ]
        self.repository.batch_link_relationships("SUPPORTED_BY", supp_links)
        
        # (Evidence)-[:DERIVED_FROM]->(Chunk)
        derived_links = [
            {
                "source_id": e.evidence_id,
                "target_id": e.chunk_id,
                "description": "Derived from chunk",
                "source_chunk_id": e.chunk_id,
            }
            for e in evidence
        ]
        self.repository.batch_link_relationships("DERIVED_FROM", derived_links)
        
        # (Claim)-[:ABOUT]->(Entity)
        about_links = [
            {
                "source_id": c.claim_id,
                "target_id": c.subject_entity_id,
                "description": "Claim is about entity",
                "source_chunk_id": c.source_chunk_id,
            }
            for c in claims
        ]
        self.repository.batch_link_relationships("ABOUT", about_links)
        
        # (Chunk)-[:MENTIONS]->(Entity)
        mentions_links = [
            {
                "source_id": e.source_chunk_id,
                "target_id": e.entity_id,
                "description": "Entity found in chunk",
                "source_chunk_id": e.source_chunk_id,
            }
            for e in entities
        ]
        self.repository.batch_link_relationships("MENTIONS", mentions_links)
