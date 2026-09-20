"""
Graph Retriever for Project Oracle.
"""

import logging
from typing import Any

from src.knowledge_graph.connection import Neo4jConnection
from src.models.retrieval import QueryAnalysis

logger = logging.getLogger(__name__)


class GraphRetriever:
    """
    Retrieves chunks based on graph traversal from query entities.
    """

    def __init__(self, connection: Neo4jConnection):
        self._connection = connection

    def retrieve(self, query: QueryAnalysis, top_k: int = 10) -> list[dict[str, Any]]:
        """
        Query the graph using extracted entities.
        Finds chunks that directly mention the entities or mention 1-hop related entities.
        """
        if not query.entities:
            logger.debug("No entities in query. Skipping graph retrieval.")
            return []

        cypher = """
        // Match exact or case-insensitive entity names
        UNWIND $entity_names AS entity_name
        MATCH (e)
        WHERE (e:Zone OR e:Risk OR e:Infrastructure OR e:Mitigation OR e:Budget OR e:Policy OR e:Project)
          AND toLower(e.name) = toLower(entity_name)
        
        // 1. Direct mentions
        OPTIONAL MATCH (chunk1:Chunk)-[:MENTIONS]->(e)
        
        // 2. 1-hop related entities
        OPTIONAL MATCH (e)-[r]-(e2)
        WHERE type(r) <> 'MENTIONS' AND type(r) <> 'ABOUT'
        OPTIONAL MATCH (chunk2:Chunk)-[:MENTIONS]->(e2)
        
        // Collect candidate chunks
        WITH 
            collect(chunk1) AS direct_chunks,
            collect(chunk2) AS related_chunks
            
        UNWIND (direct_chunks + related_chunks) AS chunk
        WITH chunk, 
             CASE WHEN chunk IN direct_chunks THEN 1.0 ELSE 0.7 END AS score
        WHERE chunk IS NOT NULL
        
        RETURN 
            chunk.id AS chunk_id,
            chunk.text AS text,
            chunk.page AS page_number,
            chunk.document_id AS document_id,
            chunk.source_path AS source_path,
            max(score) AS raw_score
        ORDER BY raw_score DESC
        LIMIT $top_k
        """
        
        try:
            with self._connection.session() as session:
                records = session.execute_read(
                    lambda tx: list(tx.run(cypher, entity_names=list(query.entities), top_k=top_k))
                )
        except Exception as exc:
            logger.error("Graph retrieval query failed: %s", exc)
            return []

        results = []
        for r in records:
            results.append({
                "chunk_id": r["chunk_id"],
                "text": r["text"],
                "page_number": r["page_number"],
                "document_id": r["document_id"],
                "source_path": r["source_path"],
                "raw_score": float(r["raw_score"]),
            })
            
        logger.debug("Graph retrieval returned %d results", len(results))
        return results
