"""
Vector Retriever for Project Oracle.
"""

import logging
from typing import Any

from src.embeddings.embedder import EmbeddingModel
from src.knowledge_graph.connection import Neo4jConnection
from src.models.retrieval import QueryAnalysis

logger = logging.getLogger(__name__)


class VectorRetriever:
    """
    Retrieves chunks using Neo4j's native vector index.
    """

    def __init__(self, connection: Neo4jConnection, embedder: EmbeddingModel):
        self._connection = connection
        self._embedder = embedder

    def retrieve(self, query: QueryAnalysis, top_k: int = 10) -> list[dict[str, Any]]:
        """
        Query the vector index.
        
        Returns a list of raw result dicts containing chunk metadata and score.
        These will be normalized and fused by the Fusion engine.
        """
        try:
            query_vector = self._embedder.embed_text(query.original_query)
        except Exception as exc:
            logger.error("Failed to embed query for vector retrieval: %s", exc)
            return []

        cypher = """
        CALL db.index.vector.queryNodes('chunk_embedding', $top_k, $query_vector)
        YIELD node, score
        RETURN 
            node.id AS chunk_id,
            node.text AS text,
            node.page AS page_number,
            node.document_id AS document_id,
            node.source_path AS source_path,
            score
        """
        
        try:
            with self._connection.session() as session:
                records = session.execute_read(
                    lambda tx: list(tx.run(cypher, top_k=top_k, query_vector=query_vector))
                )
        except Exception as exc:
            logger.error("Vector retrieval query failed: %s", exc)
            return []

        results = []
        for r in records:
            results.append({
                "chunk_id": r["chunk_id"],
                "text": r["text"],
                "page_number": r["page_number"],
                "document_id": r["document_id"],
                "source_path": r["source_path"],
                "raw_score": float(r["score"]),
            })
            
        logger.debug("Vector retrieval returned %d results", len(results))
        return results
