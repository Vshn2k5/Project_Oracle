"""
Retrieval testing script for Project Oracle.
"""

import argparse
import json
import logging
import os
from dataclasses import asdict

from src.config.settings import Settings
from src.knowledge_graph.connection import Neo4jConnection
from src.retrieval.pipeline import RetrievalPipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Test Stage 3 Retrieval Pipeline.")
    parser.add_argument(
        "--query",
        type=str,
        required=True,
        help="Natural language query to test.",
    )
    args = parser.parse_args()

    settings = Settings.from_environment()

    logger.info("Connecting to Neo4j...")
    connection = Neo4jConnection(settings)
    
    logger.info("Initializing Retrieval Pipeline...")
    pipeline = RetrievalPipeline(connection, settings)

    logger.info("Retrieving context for query: '%s'", args.query)
    context = pipeline.retrieve(args.query, top_k=5)
    
    print("\n--- RETRIEVAL RESULT ---")
    print(f"Status: {context.retrieval_status}")
    print(f"Fused Chunks Found: {len(context.chunks)}")
    print(f"Graph Expansion - Entities: {len(context.entities)}")
    print(f"Graph Expansion - Relationships: {len(context.relationships)}")
    print(f"Graph Expansion - Claims: {len(context.claims)}")
    print(f"Graph Expansion - Evidence: {len(context.evidence)}")
    print(f"Graph Expansion - Sources: {len(context.sources)}")
    
    if context.chunks:
        print("\nTop Chunk:")
        top_chunk = context.chunks[0]
        print(f"  ID: {top_chunk.chunk_id}")
        print(f"  Final Score: {top_chunk.final_score:.4f}")
        print(f"  Sources: {top_chunk.retrieval_sources}")
        print(f"  Text: {top_chunk.text[:200]}...")
    
    connection.close()


if __name__ == "__main__":
    main()
