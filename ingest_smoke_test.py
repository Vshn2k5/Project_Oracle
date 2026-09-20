"""
Smoke test script for Project Oracle extraction and population pipeline.
Runs ingestion on only the first 3 chunks of Floods.pdf to verify the entire flow.
"""

import logging
from pathlib import Path

from src.config.settings import Settings
from src.embeddings.embedder import create_embedder
from src.extraction.llm import create_llm_provider
from src.ingestion.orchestrator import IngestionOrchestrator
from src.knowledge_graph.connection import Neo4jConnection
from src.knowledge_graph.repository import KnowledgeGraphRepository
from src.knowledge_graph.schema import apply_schema

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main() -> None:
    settings = Settings.from_environment()

    pdf_path = Path("data/raw/Floods.pdf")
    if not pdf_path.exists():
        logger.error("Could not find %s. Are you running from project root?", pdf_path)
        return

    # 1. Connect and ensure schema
    logger.info("Connecting to Neo4j...")
    connection = Neo4jConnection(settings)
    
    logger.info("Applying schema (including vector index)...")
    apply_schema(connection, settings)

    # 2. Initialize components
    logger.info("Initializing components...")
    repository = KnowledgeGraphRepository(connection)
    embedder = create_embedder(settings)
    llm = create_llm_provider(settings)
    
    orchestrator = IngestionOrchestrator(repository, embedder, llm)

    # 3. Process limited chunks
    logger.info("Running smoke test (max 3 chunks)...")
    success = orchestrator.process_document(pdf_path, max_chunks=3)
    
    if success:
        logger.info("Smoke test completed successfully!")
        logger.info("Please verify the graph manually via Neo4j Browser.")
    else:
        logger.error("Smoke test failed. Check logs for details.")

    connection.close()


if __name__ == "__main__":
    main()
