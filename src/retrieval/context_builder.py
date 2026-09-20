"""
GraphRAG Context Builder for Project Oracle.
"""

import logging
from typing import Any

from src.knowledge_graph.connection import Neo4jConnection
from src.models.retrieval import RetrievedChunk

logger = logging.getLogger(__name__)


class ContextBuilder:
    """
    Expands the graph context for a set of retrieved chunks.
    Retrieves entities, relationships, claims, and evidence
    while strictly preserving provenance.
    """

    def __init__(self, connection: Neo4jConnection):
        self._connection = connection

    def build_context(self, chunks: list[RetrievedChunk]) -> dict[str, Any]:
        """
        Takes high-ranked chunks and expands their local graph context.
        Returns a dict containing entities, relationships, claims, evidence, and sources.
        """
        if not chunks:
            return {
                "entities": [],
                "relationships": [],
                "claims": [],
                "evidence": [],
                "sources": [],
            }

        chunk_ids = [c.chunk_id for c in chunks]

        # We execute a batched cypher query to fetch the local neighborhood.
        # 1. Fetch Entities mentioned in these chunks.
        # 2. Fetch Relationships between these Entities.
        # 3. Fetch Claims supported by Evidence derived from these Chunks.
        cypher = """
        UNWIND $chunk_ids AS chunk_id
        MATCH (c:Chunk {id: chunk_id})
        
        // 1. Entities & Sources
        OPTIONAL MATCH (c)-[:MENTIONS]->(entity)
        OPTIONAL MATCH (c)-[:CONTAINS]-(doc:Document)
        
        // 2. Claims & Evidence (strict provenance)
        OPTIONAL MATCH (c)<-[:DERIVED_FROM]-(evidence:Evidence)<-[:SUPPORTED_BY]-(claim:Claim)
        
        WITH collect(DISTINCT entity) AS entities,
             collect(DISTINCT claim) AS claims,
             collect(DISTINCT evidence) AS evidences,
             collect(DISTINCT doc) AS sources
             
        // 3. Relationships between those specific entities
        OPTIONAL MATCH (e1)-[r]->(e2)
        WHERE e1 IN entities AND e2 IN entities 
          AND type(r) <> 'MENTIONS' AND type(r) <> 'ABOUT'
          
        RETURN 
            [e IN entities | e{.*, labels: labels(e)}] AS entities,
            [rel IN collect(DISTINCT r) | rel{.*, type: type(rel), source_id: startNode(rel).id, target_id: endNode(rel).id}] AS relationships,
            [cl IN claims | cl{.*}] AS claims,
            [ev IN evidences | ev{.*}] AS evidence,
            [s IN sources | s{.*}] AS sources
        """
        
        try:
            with self._connection.session() as session:
                result = session.execute_read(
                    lambda tx: tx.run(cypher, chunk_ids=chunk_ids).single()
                )
        except Exception as exc:
            logger.error("Context expansion query failed: %s", exc)
            return {
                "entities": [],
                "relationships": [],
                "claims": [],
                "evidence": [],
                "sources": [],
            }

        if not result:
            return {
                "entities": [],
                "relationships": [],
                "claims": [],
                "evidence": [],
                "sources": [],
            }

        return {
            "entities": result["entities"] or [],
            "relationships": result["relationships"] or [],
            "claims": result["claims"] or [],
            "evidence": result["evidence"] or [],
            "sources": result["sources"] or [],
        }
