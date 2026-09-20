"""
Full ingestion script for Project Oracle.
"""

import argparse
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
    parser = argparse.ArgumentParser(description="Ingest a document into Project Oracle.")
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to the PDF document to ingest.",
    )
    args = parser.parse_args()

    input_path: Path = args.input
    if not input_path.exists():
        logger.error("Input file not found: %s", input_path)
        return

    settings = Settings.from_environment()

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

    # 3. Process document
    logger.info("Starting full ingestion of %s", input_path.name)
    success = orchestrator.process_document(input_path)
    
    if success:
        logger.info("Ingestion completed successfully!")
    else:
        logger.error("Ingestion failed. Check logs for details.")

    connection.close()


if __name__ == "__main__":
    main()
