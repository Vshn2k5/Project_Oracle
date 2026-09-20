"""
Keyword Retriever for Project Oracle.
"""

import logging
from typing import Any

from src.knowledge_graph.connection import Neo4jConnection
from src.models.retrieval import QueryAnalysis

logger = logging.getLogger(__name__)


class KeywordRetriever:
    """
    Retrieves chunks using Neo4j's native full-text index.
    """

    def __init__(self, connection: Neo4jConnection):
        self._connection = connection

    def retrieve(self, query: QueryAnalysis, top_k: int = 10) -> list[dict[str, Any]]:
        """
        Query the full-text index using the extracted keywords.
        """
        if not query.keywords:
            # If no keywords, fallback to trying to search the whole normalized string
            search_term = query.normalized_query
        else:
            # Join keywords with OR for broad recall
            search_term = " OR ".join(query.keywords)

        if not search_term.strip():
            return []

        cypher = """
        CALL db.index.fulltext.queryNodes('chunk_text_index', $search_term)
        YIELD node, score
        RETURN 
            node.id AS chunk_id,
            node.text AS text,
            node.page AS page_number,
            node.document_id AS document_id,
            node.source_path AS source_path,
            score
        LIMIT $top_k
        """
        
        try:
            with self._connection.session() as session:
                records = session.execute_read(
                    lambda tx: list(tx.run(cypher, search_term=search_term, top_k=top_k))
                )
        except Exception as exc:
            logger.error("Keyword retrieval query failed: %s", exc)
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
            
        logger.debug("Keyword retrieval returned %d results", len(results))
        return results
