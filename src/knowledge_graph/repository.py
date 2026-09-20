"""
Knowledge-graph repository for Project Oracle.

Provides controlled write, read, batch, and query operations against the
Neo4j knowledge graph.  All Cypher is parameterized.  The repository
receives its connection explicitly — it does not access global state.
"""

import logging
from dataclasses import dataclass
from typing import Any, Final

from neo4j import Transaction
from neo4j.exceptions import Neo4jError

from src.config.settings import Settings
from src.knowledge_graph.connection import (
    Neo4jConnection,
    create_neo4j_connection,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class NodeWriteResult:
    """Result returned after creating or updating a graph node."""

    node_id: str
    label: str


@dataclass(frozen=True, slots=True)
class RelationshipWriteResult:
    """Result returned after creating or confirming a graph relationship."""

    relationship_type: str


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class KnowledgeGraphRepositoryError(RuntimeError):
    """Raised when a knowledge-graph repository operation fails."""


class DatabaseWriteError(KnowledgeGraphRepositoryError):
    """Raised when a write operation fails."""


class DatabaseReadError(KnowledgeGraphRepositoryError):
    """Raised when a read operation fails."""


# ---------------------------------------------------------------------------
# Cypher statements — Node MERGE (write)
# ---------------------------------------------------------------------------

MERGE_DOCUMENT: Final[str] = """
MERGE (n:Document {id: $id})
SET
    n.title = $title,
    n.source = $source,
    n.document_type = $document_type,
    n.publication_date = $publication_date
RETURN n.id AS node_id
"""


MERGE_CHUNK: Final[str] = """
MERGE (n:Chunk {id: $id})
SET
    n.text = $text,
    n.page = $page,
    n.chunk_index = $chunk_index,
    n.source_path = $source_path,
    n.document_id = $document_id
RETURN n.id AS node_id
"""


MERGE_ZONE: Final[str] = """
MERGE (n:Zone {id: $id})
SET
    n.name = $name,
    n.description = $description
RETURN n.id AS node_id
"""


MERGE_RISK: Final[str] = """
MERGE (n:Risk {id: $id})
SET
    n.type = $risk_type,
    n.severity = $severity,
    n.description = $description
RETURN n.id AS node_id
"""


MERGE_INFRASTRUCTURE: Final[str] = """
MERGE (n:Infrastructure {id: $id})
SET
    n.name = $name,
    n.type = $infrastructure_type,
    n.description = $description
RETURN n.id AS node_id
"""


MERGE_MITIGATION: Final[str] = """
MERGE (n:Mitigation {id: $id})
SET
    n.name = $name,
    n.type = $mitigation_type,
    n.description = $description
RETURN n.id AS node_id
"""


MERGE_BUDGET: Final[str] = """
MERGE (n:Budget {id: $id})
SET
    n.amount = $amount,
    n.currency = $currency,
    n.fiscal_year = $fiscal_year
RETURN n.id AS node_id
"""


MERGE_POLICY: Final[str] = """
MERGE (n:Policy {id: $id})
SET
    n.title = $title,
    n.policy_type = $policy_type,
    n.description = $description
RETURN n.id AS node_id
"""


MERGE_CLAIM: Final[str] = """
MERGE (n:Claim {id: $id})
SET
    n.statement = $statement,
    n.subject_entity_id = $subject_entity_id,
    n.source_chunk_id = $source_chunk_id,
    n.confidence = $confidence
RETURN n.id AS node_id
"""


MERGE_EVIDENCE: Final[str] = """
MERGE (n:Evidence {id: $id})
SET
    n.claim_id = $claim_id,
    n.chunk_id = $chunk_id,
    n.text = $text,
    n.supports = $supports
RETURN n.id AS node_id
"""


MERGE_PROJECT: Final[str] = """
MERGE (n:Project {id: $id})
SET
    n.name = $name,
    n.description = $description,
    n.status = $status
RETURN n.id AS node_id
"""


# ---------------------------------------------------------------------------
# Cypher statements — Relationship MERGE (write)
# ---------------------------------------------------------------------------

LINK_DOCUMENT_CHUNK: Final[str] = """
MATCH (document:Document {id: $source_id})
MATCH (chunk:Chunk {id: $target_id})
MERGE (document)-[relationship:CONTAINS]->(chunk)
RETURN type(relationship) AS relationship_type
"""

LINK_CHUNK_ZONE: Final[str] = """
MATCH (chunk:Chunk {id: $source_id})
MATCH (zone:Zone {id: $target_id})
MERGE (chunk)-[relationship:MENTIONS]->(zone)
RETURN type(relationship) AS relationship_type
"""

LINK_CHUNK_RISK: Final[str] = """
MATCH (chunk:Chunk {id: $source_id})
MATCH (risk:Risk {id: $target_id})
MERGE (chunk)-[relationship:MENTIONS]->(risk)
RETURN type(relationship) AS relationship_type
"""

LINK_CHUNK_INFRASTRUCTURE: Final[str] = """
MATCH (chunk:Chunk {id: $source_id})
MATCH (infrastructure:Infrastructure {id: $target_id})
MERGE (chunk)-[relationship:MENTIONS]->(infrastructure)
RETURN type(relationship) AS relationship_type
"""

LINK_CHUNK_MITIGATION: Final[str] = """
MATCH (chunk:Chunk {id: $source_id})
MATCH (mitigation:Mitigation {id: $target_id})
MERGE (chunk)-[relationship:MENTIONS]->(mitigation)
RETURN type(relationship) AS relationship_type
"""

LINK_ZONE_RISK: Final[str] = """
MATCH (zone:Zone {id: $source_id})
MATCH (risk:Risk {id: $target_id})
MERGE (zone)-[relationship:HAS_RISK]->(risk)
RETURN type(relationship) AS relationship_type
"""

LINK_RISK_INFRASTRUCTURE: Final[str] = """
MATCH (risk:Risk {id: $source_id})
MATCH (infrastructure:Infrastructure {id: $target_id})
MERGE (risk)-[relationship:AFFECTS]->(infrastructure)
RETURN type(relationship) AS relationship_type
"""

LINK_INFRASTRUCTURE_MITIGATION: Final[str] = """
MATCH (infrastructure:Infrastructure {id: $source_id})
MATCH (mitigation:Mitigation {id: $target_id})
MERGE (infrastructure)-[relationship:REQUIRES]->(mitigation)
RETURN type(relationship) AS relationship_type
"""

LINK_BUDGET_MITIGATION: Final[str] = """
MATCH (budget:Budget {id: $source_id})
MATCH (mitigation:Mitigation {id: $target_id})
MERGE (budget)-[relationship:FUNDS]->(mitigation)
RETURN type(relationship) AS relationship_type
"""

LINK_POLICY_INFRASTRUCTURE: Final[str] = """
MATCH (policy:Policy {id: $source_id})
MATCH (infrastructure:Infrastructure {id: $target_id})
MERGE (policy)-[relationship:REGULATES]->(infrastructure)
RETURN type(relationship) AS relationship_type
"""

LINK_POLICY_MITIGATION: Final[str] = """
MATCH (policy:Policy {id: $source_id})
MATCH (mitigation:Mitigation {id: $target_id})
MERGE (policy)-[relationship:REQUIRES]->(mitigation)
RETURN type(relationship) AS relationship_type
"""

# Provenance / reasoning relationships
LINK_CLAIM_EVIDENCE: Final[str] = """
MATCH (claim:Claim {id: $source_id})
MATCH (evidence:Evidence {id: $target_id})
MERGE (claim)-[relationship:SUPPORTED_BY]->(evidence)
RETURN type(relationship) AS relationship_type
"""

LINK_EVIDENCE_CHUNK: Final[str] = """
MATCH (evidence:Evidence {id: $source_id})
MATCH (chunk:Chunk {id: $target_id})
MERGE (evidence)-[relationship:DERIVED_FROM]->(chunk)
RETURN type(relationship) AS relationship_type
"""

LINK_CLAIM_ENTITY: Final[str] = """
MATCH (claim:Claim {id: $source_id})
MATCH (entity {id: $target_id})
MERGE (claim)-[relationship:ABOUT]->(entity)
RETURN type(relationship) AS relationship_type
"""

LINK_PROJECT_ZONE: Final[str] = """
MATCH (project:Project {id: $source_id})
MATCH (zone:Zone {id: $target_id})
MERGE (project)-[relationship:LOCATED_IN]->(zone)
RETURN type(relationship) AS relationship_type
"""

LINK_PROJECT_RISK: Final[str] = """
MATCH (project:Project {id: $source_id})
MATCH (risk:Risk {id: $target_id})
MERGE (project)-[relationship:ADDRESSES]->(risk)
RETURN type(relationship) AS relationship_type
"""

LINK_BUDGET_PROJECT: Final[str] = """
MATCH (budget:Budget {id: $source_id})
MATCH (project:Project {id: $target_id})
MERGE (budget)-[relationship:ALLOCATES]->(project)
RETURN type(relationship) AS relationship_type
"""

LINK_POLICY_PROJECT: Final[str] = """
MATCH (policy:Policy {id: $source_id})
MATCH (project:Project {id: $target_id})
MERGE (policy)-[relationship:APPLIES_TO]->(project)
RETURN type(relationship) AS relationship_type
"""


# ---------------------------------------------------------------------------
# Cypher statements — READ queries
# ---------------------------------------------------------------------------

GET_DOCUMENT: Final[str] = """
MATCH (n:Document {id: $id})
RETURN n {.*} AS document
"""

GET_CHUNK: Final[str] = """
MATCH (n:Chunk {id: $id})
RETURN n {.*} AS chunk
"""

GET_CHUNKS_FOR_DOCUMENT: Final[str] = """
MATCH (d:Document {id: $document_id})-[:CONTAINS]->(c:Chunk)
RETURN c {.*} AS chunk
ORDER BY c.chunk_index
"""

FIND_ENTITIES_BY_LABEL: Final[str] = """
MATCH (n:{label})
RETURN n {{.*}} AS entity
"""

FIND_ENTITY: Final[str] = """
MATCH (n {{id: $id}})
RETURN n {{.*}} AS entity, labels(n) AS labels
"""

FIND_RELATIONSHIPS: Final[str] = """
MATCH (source {id: $source_id})-[r]->(target)
RETURN
    source.id AS source_id,
    type(r) AS relationship_type,
    target.id AS target_id,
    labels(target) AS target_labels,
    target {.*} AS target_properties
"""

FIND_RELATIONSHIPS_TYPED: Final[str] = """
MATCH (source {{id: $source_id}})-[r:{relationship_type}]->(target)
RETURN
    source.id AS source_id,
    type(r) AS relationship_type,
    target.id AS target_id,
    labels(target) AS target_labels,
    target {{.*}} AS target_properties
"""

GET_GRAPH_CONTEXT: Final[str] = """
MATCH (c:Chunk)
WHERE c.id IN $chunk_ids
OPTIONAL MATCH (c)-[r1:MENTIONS]->(entity)
OPTIONAL MATCH (entity)-[r2]->(related)
RETURN
    collect(DISTINCT entity {.*, labels: labels(entity)}) AS entities,
    collect(DISTINCT {
        source_id: entity.id,
        relationship_type: type(r2),
        target_id: related.id,
        target_labels: labels(related)
    }) AS relationships
"""


# ---------------------------------------------------------------------------
# Cypher statements — BATCH write
# ---------------------------------------------------------------------------

BATCH_MERGE_CHUNKS: Final[str] = """
UNWIND $items AS item
MERGE (n:Chunk {id: item.id})
SET
    n.text = item.text,
    n.page = item.page,
    n.chunk_index = item.chunk_index,
    n.source_path = item.source_path,
    n.document_id = item.document_id
WITH n, item
CALL {
    WITH n, item
    WITH n, item WHERE item.embedding IS NOT NULL
    SET n.embedding = item.embedding
    RETURN count(*) AS c1
}
RETURN n.id AS node_id
"""

BATCH_MERGE_ENTITIES: Final[str] = """
UNWIND $items AS item
CALL {
    WITH item
    // Entities are dynamically labelled at application level, but in Cypher we can't parameterize labels in MERGE easily.
    // The preferred way in APOC is apoc.merge.node, but to stay dependency-free we will MERGE on a generic pattern
    // and then add the specific label using a small trick, or just require batching by label.
    // To keep it simple and compliant with the requirement: "Neo4j should use domain-specific labels".
    // We will batch by label in the Python method and inject the label into the query.
}
RETURN node_id
"""

BATCH_LINK_DOCUMENT_CHUNKS: Final[str] = """
UNWIND $items AS item
MATCH (d:Document {id: item.document_id})
MATCH (c:Chunk {id: item.chunk_id})
MERGE (d)-[r:CONTAINS]->(c)
RETURN type(r) AS relationship_type
"""


# ---------------------------------------------------------------------------
# Repository
# ---------------------------------------------------------------------------

class KnowledgeGraphRepository:
    """
    Provides controlled database operations for Project Oracle's
    knowledge graph.

    The repository uses the Neo4jConnection abstraction supplied by the
    application. A repository created by ``create_repository`` owns its
    connection and must be closed when it is no longer needed.
    """

    def __init__(
        self,
        connection: Neo4jConnection,
        *,
        owns_connection: bool = False,
    ) -> None:
        self._connection = connection
        self._owns_connection = owns_connection
        self._closed = False

    def close(self) -> None:
        """Close the underlying connection when this repository owns it."""
        if self._closed:
            return

        if self._owns_connection:
            self._connection.close()

        self._closed = True

    def __enter__(self) -> "KnowledgeGraphRepository":
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        self.close()

    # -----------------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------------

    def _ensure_open(self) -> None:
        """Ensure the repository has not been closed."""
        if self._closed:
            raise KnowledgeGraphRepositoryError(
                "Knowledge graph repository is closed."
            )

    @staticmethod
    def _validate_id(node_id: str) -> str:
        """
        Validate and normalize a graph node identifier.
        """
        if not isinstance(node_id, str):
            raise TypeError("Node id must be a string.")

        normalized_id = node_id.strip()

        if not normalized_id:
            raise ValueError("Node id cannot be empty.")

        return normalized_id

    def _merge_node(
        self,
        *,
        label: str,
        cypher: str,
        parameters: dict[str, Any],
    ) -> NodeWriteResult:
        """
        Create or update one graph node using its stable identifier.
        """
        self._ensure_open()

        try:
            with self._connection.session() as session:
                record = session.execute_write(
                    self._execute_merge,
                    cypher,
                    parameters,
                )

        except Neo4jError as exc:
            logger.error("Failed to write %s node: %s", label, exc)
            raise DatabaseWriteError(
                f"Failed to write {label} node."
            ) from exc

        if record is None:
            raise DatabaseWriteError(
                f"Neo4j did not return the id of the {label} node."
            )

        try:
            node_id = record["node_id"]
        except (KeyError, TypeError) as exc:
            raise DatabaseWriteError(
                f"Neo4j returned an invalid response for the {label} node."
            ) from exc

        if not isinstance(node_id, str) or not node_id:
            raise DatabaseWriteError(
                f"Neo4j returned an invalid id for the {label} node."
            )

        logger.debug("Upserted %s node: %s", label, node_id)

        return NodeWriteResult(
            node_id=node_id,
            label=label,
        )

    @staticmethod
    def _execute_merge(
        transaction: Transaction,
        cypher: str,
        parameters: dict[str, Any],
    ):
        """
        Execute a single parameterized MERGE operation inside a transaction.
        """
        return transaction.run(cypher, parameters).single()

    def _merge_relationship(
        self,
        *,
        relationship_type: str,
        cypher: str,
        source_id: str,
        target_id: str,
    ) -> RelationshipWriteResult:
        """Create or confirm one relationship between existing nodes."""
        self._ensure_open()

        parameters = {
            "source_id": self._validate_id(source_id),
            "target_id": self._validate_id(target_id),
        }

        try:
            with self._connection.session() as session:
                record = session.execute_write(
                    self._execute_merge,
                    cypher,
                    parameters,
                )
        except Neo4jError as exc:
            logger.error(
                "Failed to write %s relationship: %s",
                relationship_type,
                exc,
            )
            raise DatabaseWriteError(
                f"Failed to write {relationship_type} relationship."
            ) from exc

        if record is None:
            raise DatabaseWriteError(
                f"Cannot create {relationship_type} relationship: "
                "one or both endpoint nodes do not exist."
            )

        try:
            returned_type = record["relationship_type"]
        except (KeyError, TypeError) as exc:
            raise DatabaseWriteError(
                f"Neo4j returned an invalid response for the "
                f"{relationship_type} relationship."
            ) from exc

        if returned_type != relationship_type:
            raise DatabaseWriteError(
                f"Neo4j returned unexpected relationship type "
                f"'{returned_type}' for {relationship_type}."
            )

        logger.debug(
            "Upserted %s relationship: %s -> %s",
            relationship_type,
            source_id,
            target_id,
        )

        return RelationshipWriteResult(relationship_type=returned_type)

    # -----------------------------------------------------------------------
    # Internal read helper
    # -----------------------------------------------------------------------

    @staticmethod
    def _execute_read(
        transaction: Transaction,
        cypher: str,
        parameters: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Execute a parameterized read query inside a transaction."""
        result = transaction.run(cypher, parameters)
        return [dict(record) for record in result]

    # -----------------------------------------------------------------------
    # Document — write
    # -----------------------------------------------------------------------

    def upsert_document(
        self,
        *,
        node_id: str,
        title: str,
        source: str,
        document_type: str,
        publication_date: str | None,
    ) -> NodeWriteResult:
        """Create or update a Document node."""
        return self._merge_node(
            label="Document",
            cypher=MERGE_DOCUMENT,
            parameters={
                "id": self._validate_id(node_id),
                "title": title,
                "source": source,
                "document_type": document_type,
                "publication_date": publication_date,
            },
        )

    # -----------------------------------------------------------------------
    # Chunk — write
    # -----------------------------------------------------------------------

    def upsert_chunk(
        self,
        *,
        node_id: str,
        text: str,
        page: int,
        chunk_index: int,
        source_path: str = "",
        document_id: str = "",
    ) -> NodeWriteResult:
        """Create or update a Chunk node with provenance metadata."""
        return self._merge_node(
            label="Chunk",
            cypher=MERGE_CHUNK,
            parameters={
                "id": self._validate_id(node_id),
                "text": text,
                "page": page,
                "chunk_index": chunk_index,
                "source_path": source_path,
                "document_id": document_id,
            },
        )

    # -----------------------------------------------------------------------
    # Zone — write
    # -----------------------------------------------------------------------

    def upsert_zone(
        self,
        *,
        node_id: str,
        name: str,
        description: str,
    ) -> NodeWriteResult:
        """Create or update a Zone node."""
        return self._merge_node(
            label="Zone",
            cypher=MERGE_ZONE,
            parameters={
                "id": self._validate_id(node_id),
                "name": name,
                "description": description,
            },
        )

    # -----------------------------------------------------------------------
    # Risk — write
    # -----------------------------------------------------------------------

    def upsert_risk(
        self,
        *,
        node_id: str,
        risk_type: str,
        severity: str,
        description: str,
    ) -> NodeWriteResult:
        """Create or update a Risk node."""
        return self._merge_node(
            label="Risk",
            cypher=MERGE_RISK,
            parameters={
                "id": self._validate_id(node_id),
                "risk_type": risk_type,
                "severity": severity,
                "description": description,
            },
        )

    # -----------------------------------------------------------------------
    # Infrastructure — write
    # -----------------------------------------------------------------------

    def upsert_infrastructure(
        self,
        *,
        node_id: str,
        name: str,
        infrastructure_type: str,
        description: str,
    ) -> NodeWriteResult:
        """Create or update an Infrastructure node."""
        return self._merge_node(
            label="Infrastructure",
            cypher=MERGE_INFRASTRUCTURE,
            parameters={
                "id": self._validate_id(node_id),
                "name": name,
                "infrastructure_type": infrastructure_type,
                "description": description,
            },
        )

    # -----------------------------------------------------------------------
    # Mitigation — write
    # -----------------------------------------------------------------------

    def upsert_mitigation(
        self,
        *,
        node_id: str,
        name: str,
        mitigation_type: str,
        description: str,
    ) -> NodeWriteResult:
        """Create or update a Mitigation node."""
        return self._merge_node(
            label="Mitigation",
            cypher=MERGE_MITIGATION,
            parameters={
                "id": self._validate_id(node_id),
                "name": name,
                "mitigation_type": mitigation_type,
                "description": description,
            },
        )

    # -----------------------------------------------------------------------
    # Budget — write
    # -----------------------------------------------------------------------

    def upsert_budget(
        self,
        *,
        node_id: str,
        amount: float,
        currency: str,
        fiscal_year: str,
    ) -> NodeWriteResult:
        """Create or update a Budget node."""
        return self._merge_node(
            label="Budget",
            cypher=MERGE_BUDGET,
            parameters={
                "id": self._validate_id(node_id),
                "amount": amount,
                "currency": currency,
                "fiscal_year": fiscal_year,
            },
        )

    # -----------------------------------------------------------------------
    # Policy — write
    # -----------------------------------------------------------------------

    def upsert_policy(
        self,
        *,
        node_id: str,
        title: str,
        policy_type: str,
        description: str,
    ) -> NodeWriteResult:
        """Create or update a Policy node."""
        return self._merge_node(
            label="Policy",
            cypher=MERGE_POLICY,
            parameters={
                "id": self._validate_id(node_id),
                "title": title,
                "policy_type": policy_type,
                "description": description,
            },
        )

    # -----------------------------------------------------------------------
    # Claim — write
    # -----------------------------------------------------------------------

    def upsert_claim(
        self,
        *,
        node_id: str,
        statement: str,
        subject_entity_id: str,
        source_chunk_id: str,
        confidence: float,
    ) -> NodeWriteResult:
        """Create or update a Claim node."""
        return self._merge_node(
            label="Claim",
            cypher=MERGE_CLAIM,
            parameters={
                "id": self._validate_id(node_id),
                "statement": statement,
                "subject_entity_id": subject_entity_id,
                "source_chunk_id": source_chunk_id,
                "confidence": confidence,
            },
        )

    # -----------------------------------------------------------------------
    # Evidence — write
    # -----------------------------------------------------------------------

    def upsert_evidence(
        self,
        *,
        node_id: str,
        claim_id: str,
        chunk_id: str,
        text: str,
        supports: bool,
    ) -> NodeWriteResult:
        """Create or update an Evidence node."""
        return self._merge_node(
            label="Evidence",
            cypher=MERGE_EVIDENCE,
            parameters={
                "id": self._validate_id(node_id),
                "claim_id": claim_id,
                "chunk_id": chunk_id,
                "text": text,
                "supports": supports,
            },
        )

    # -----------------------------------------------------------------------
    # Project — write
    # -----------------------------------------------------------------------

    def upsert_project(
        self,
        *,
        node_id: str,
        name: str,
        description: str,
        status: str = "planned",
    ) -> NodeWriteResult:
        """Create or update a Project node."""
        return self._merge_node(
            label="Project",
            cypher=MERGE_PROJECT,
            parameters={
                "id": self._validate_id(node_id),
                "name": name,
                "description": description,
                "status": status,
            },
        )

    # -----------------------------------------------------------------------
    # Relationships — write
    # -----------------------------------------------------------------------

    def link_document_to_chunk(
        self,
        *,
        document_id: str,
        chunk_id: str,
    ) -> RelationshipWriteResult:
        """Link a document to one of its chunks."""
        return self._merge_relationship(
            relationship_type="CONTAINS",
            cypher=LINK_DOCUMENT_CHUNK,
            source_id=document_id,
            target_id=chunk_id,
        )

    def link_chunk_to_zone(
        self,
        *,
        chunk_id: str,
        zone_id: str,
    ) -> RelationshipWriteResult:
        """Record that a chunk mentions a zone."""
        return self._merge_relationship(
            relationship_type="MENTIONS",
            cypher=LINK_CHUNK_ZONE,
            source_id=chunk_id,
            target_id=zone_id,
        )

    def link_chunk_to_risk(
        self,
        *,
        chunk_id: str,
        risk_id: str,
    ) -> RelationshipWriteResult:
        """Record that a chunk mentions a risk."""
        return self._merge_relationship(
            relationship_type="MENTIONS",
            cypher=LINK_CHUNK_RISK,
            source_id=chunk_id,
            target_id=risk_id,
        )

    def link_chunk_to_infrastructure(
        self,
        *,
        chunk_id: str,
        infrastructure_id: str,
    ) -> RelationshipWriteResult:
        """Record that a chunk mentions infrastructure."""
        return self._merge_relationship(
            relationship_type="MENTIONS",
            cypher=LINK_CHUNK_INFRASTRUCTURE,
            source_id=chunk_id,
            target_id=infrastructure_id,
        )

    def link_chunk_to_mitigation(
        self,
        *,
        chunk_id: str,
        mitigation_id: str,
    ) -> RelationshipWriteResult:
        """Record that a chunk mentions a mitigation."""
        return self._merge_relationship(
            relationship_type="MENTIONS",
            cypher=LINK_CHUNK_MITIGATION,
            source_id=chunk_id,
            target_id=mitigation_id,
        )

    def link_zone_to_risk(
        self,
        *,
        zone_id: str,
        risk_id: str,
    ) -> RelationshipWriteResult:
        """Link a zone to a risk affecting it."""
        return self._merge_relationship(
            relationship_type="HAS_RISK",
            cypher=LINK_ZONE_RISK,
            source_id=zone_id,
            target_id=risk_id,
        )

    def link_risk_to_infrastructure(
        self,
        *,
        risk_id: str,
        infrastructure_id: str,
    ) -> RelationshipWriteResult:
        """Link a risk to affected infrastructure."""
        return self._merge_relationship(
            relationship_type="AFFECTS",
            cypher=LINK_RISK_INFRASTRUCTURE,
            source_id=risk_id,
            target_id=infrastructure_id,
        )

    def link_infrastructure_to_mitigation(
        self,
        *,
        infrastructure_id: str,
        mitigation_id: str,
    ) -> RelationshipWriteResult:
        """Link infrastructure to a required mitigation."""
        return self._merge_relationship(
            relationship_type="REQUIRES",
            cypher=LINK_INFRASTRUCTURE_MITIGATION,
            source_id=infrastructure_id,
            target_id=mitigation_id,
        )

    def link_budget_to_mitigation(
        self,
        *,
        budget_id: str,
        mitigation_id: str,
    ) -> RelationshipWriteResult:
        """Link funding to a mitigation."""
        return self._merge_relationship(
            relationship_type="FUNDS",
            cypher=LINK_BUDGET_MITIGATION,
            source_id=budget_id,
            target_id=mitigation_id,
        )

    def link_policy_to_infrastructure(
        self,
        *,
        policy_id: str,
        infrastructure_id: str,
    ) -> RelationshipWriteResult:
        """Link a policy to infrastructure it regulates."""
        return self._merge_relationship(
            relationship_type="REGULATES",
            cypher=LINK_POLICY_INFRASTRUCTURE,
            source_id=policy_id,
            target_id=infrastructure_id,
        )

    def link_policy_to_mitigation(
        self,
        *,
        policy_id: str,
        mitigation_id: str,
    ) -> RelationshipWriteResult:
        """Link a policy to a required mitigation."""
        return self._merge_relationship(
            relationship_type="REQUIRES",
            cypher=LINK_POLICY_MITIGATION,
            source_id=policy_id,
            target_id=mitigation_id,
        )

    # Provenance / reasoning relationships

    def link_claim_to_evidence(
        self,
        *,
        claim_id: str,
        evidence_id: str,
    ) -> RelationshipWriteResult:
        """Link a claim to supporting or contradicting evidence."""
        return self._merge_relationship(
            relationship_type="SUPPORTED_BY",
            cypher=LINK_CLAIM_EVIDENCE,
            source_id=claim_id,
            target_id=evidence_id,
        )

    def link_evidence_to_chunk(
        self,
        *,
        evidence_id: str,
        chunk_id: str,
    ) -> RelationshipWriteResult:
        """Link evidence to the chunk it derives from."""
        return self._merge_relationship(
            relationship_type="DERIVED_FROM",
            cypher=LINK_EVIDENCE_CHUNK,
            source_id=evidence_id,
            target_id=chunk_id,
        )

    def link_claim_to_entity(
        self,
        *,
        claim_id: str,
        entity_id: str,
    ) -> RelationshipWriteResult:
        """Link a claim to the entity it is about."""
        return self._merge_relationship(
            relationship_type="ABOUT",
            cypher=LINK_CLAIM_ENTITY,
            source_id=claim_id,
            target_id=entity_id,
        )

    def link_project_to_zone(
        self,
        *,
        project_id: str,
        zone_id: str,
    ) -> RelationshipWriteResult:
        """Link a project to its zone."""
        return self._merge_relationship(
            relationship_type="LOCATED_IN",
            cypher=LINK_PROJECT_ZONE,
            source_id=project_id,
            target_id=zone_id,
        )

    def link_project_to_risk(
        self,
        *,
        project_id: str,
        risk_id: str,
    ) -> RelationshipWriteResult:
        """Link a project to a risk it addresses."""
        return self._merge_relationship(
            relationship_type="ADDRESSES",
            cypher=LINK_PROJECT_RISK,
            source_id=project_id,
            target_id=risk_id,
        )

    def link_budget_to_project(
        self,
        *,
        budget_id: str,
        project_id: str,
    ) -> RelationshipWriteResult:
        """Link a budget allocation to a project."""
        return self._merge_relationship(
            relationship_type="ALLOCATES",
            cypher=LINK_BUDGET_PROJECT,
            source_id=budget_id,
            target_id=project_id,
        )

    def link_policy_to_project(
        self,
        *,
        policy_id: str,
        project_id: str,
    ) -> RelationshipWriteResult:
        """Link a policy to a project it applies to."""
        return self._merge_relationship(
            relationship_type="APPLIES_TO",
            cypher=LINK_POLICY_PROJECT,
            source_id=policy_id,
            target_id=project_id,
        )

    # -----------------------------------------------------------------------
    # READ operations
    # -----------------------------------------------------------------------

    def get_document(self, document_id: str) -> dict[str, Any] | None:
        """
        Retrieve a single Document node by its identifier.

        Returns:
            A dictionary of node properties, or ``None`` if not found.
        """
        self._ensure_open()

        try:
            with self._connection.read_session() as session:
                records = session.execute_read(
                    self._execute_read,
                    GET_DOCUMENT,
                    {"id": self._validate_id(document_id)},
                )
        except Neo4jError as exc:
            logger.error("Failed to read Document %s: %s", document_id, exc)
            raise DatabaseReadError(
                f"Failed to read Document '{document_id}'."
            ) from exc

        if not records:
            return None

        return records[0].get("document")

    def get_chunk(self, chunk_id: str) -> dict[str, Any] | None:
        """
        Retrieve a single Chunk node by its identifier.

        Returns:
            A dictionary of node properties, or ``None`` if not found.
        """
        self._ensure_open()

        try:
            with self._connection.read_session() as session:
                records = session.execute_read(
                    self._execute_read,
                    GET_CHUNK,
                    {"id": self._validate_id(chunk_id)},
                )
        except Neo4jError as exc:
            logger.error("Failed to read Chunk %s: %s", chunk_id, exc)
            raise DatabaseReadError(
                f"Failed to read Chunk '{chunk_id}'."
            ) from exc

        if not records:
            return None

        return records[0].get("chunk")

    def get_chunks_for_document(
        self, document_id: str,
    ) -> list[dict[str, Any]]:
        """
        Retrieve all Chunk nodes belonging to a Document, ordered by index.
        """
        self._ensure_open()

        try:
            with self._connection.read_session() as session:
                records = session.execute_read(
                    self._execute_read,
                    GET_CHUNKS_FOR_DOCUMENT,
                    {"document_id": self._validate_id(document_id)},
                )
        except Neo4jError as exc:
            logger.error(
                "Failed to read chunks for Document %s: %s",
                document_id,
                exc,
            )
            raise DatabaseReadError(
                f"Failed to read chunks for Document '{document_id}'."
            ) from exc

        return [r["chunk"] for r in records if r.get("chunk")]

    def find_entities_by_label(
        self, label: str,
    ) -> list[dict[str, Any]]:
        """
        Find all nodes with the given Neo4j label.

        Args:
            label: A Neo4j node label (e.g. ``Zone``, ``Risk``).

        Returns:
            A list of node property dictionaries.
        """
        self._ensure_open()

        # Label is injected into the query template because Neo4j does not
        # support parameterized labels.  We whitelist to prevent injection.
        allowed_labels = {
            "Document", "Chunk", "Zone", "Risk", "Infrastructure",
            "Mitigation", "Budget", "Policy", "Claim", "Evidence", "Project",
        }
        if label not in allowed_labels:
            raise ValueError(
                f"Label '{label}' is not a recognized node type."
            )

        cypher = f"MATCH (n:{label}) RETURN n {{.*}} AS entity"

        try:
            with self._connection.read_session() as session:
                records = session.execute_read(
                    self._execute_read,
                    cypher,
                    {},
                )
        except Neo4jError as exc:
            logger.error("Failed to find %s entities: %s", label, exc)
            raise DatabaseReadError(
                f"Failed to find entities with label '{label}'."
            ) from exc

        return [r["entity"] for r in records if r.get("entity")]

    def find_entity(self, entity_id: str) -> dict[str, Any] | None:
        """
        Find a single node by its ``id`` property regardless of label.

        Returns:
            A dictionary with ``entity`` (properties) and ``labels``,
            or ``None`` if not found.
        """
        self._ensure_open()

        cypher = (
            "MATCH (n {id: $id}) "
            "RETURN n {.*} AS entity, labels(n) AS labels"
        )

        try:
            with self._connection.read_session() as session:
                records = session.execute_read(
                    self._execute_read,
                    cypher,
                    {"id": self._validate_id(entity_id)},
                )
        except Neo4jError as exc:
            logger.error("Failed to find entity %s: %s", entity_id, exc)
            raise DatabaseReadError(
                f"Failed to find entity '{entity_id}'."
            ) from exc

        if not records:
            return None

        return {
            "entity": records[0].get("entity"),
            "labels": records[0].get("labels"),
        }

    def find_relationships(
        self,
        source_id: str,
        relationship_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Find outgoing relationships from a node.

        Args:
            source_id: The ``id`` of the source node.
            relationship_type: Optional filter for a specific relationship
                type.  When omitted, all outgoing relationships are returned.
        """
        self._ensure_open()

        if relationship_type is not None:
            # Whitelist relationship types to prevent injection.
            allowed_types = {
                "CONTAINS", "MENTIONS", "HAS_RISK", "AFFECTS", "REQUIRES",
                "FUNDS", "REGULATES", "SUPPORTED_BY", "DERIVED_FROM",
                "ABOUT", "LOCATED_IN", "ADDRESSES", "ALLOCATES", "APPLIES_TO",
            }
            if relationship_type not in allowed_types:
                raise ValueError(
                    f"Relationship type '{relationship_type}' is not "
                    f"recognized."
                )
            cypher = (
                f"MATCH (source {{id: $source_id}})"
                f"-[r:{relationship_type}]->(target) "
                f"RETURN source.id AS source_id, "
                f"type(r) AS relationship_type, "
                f"target.id AS target_id, "
                f"labels(target) AS target_labels, "
                f"target {{.*}} AS target_properties"
            )
        else:
            cypher = FIND_RELATIONSHIPS

        try:
            with self._connection.read_session() as session:
                records = session.execute_read(
                    self._execute_read,
                    cypher,
                    {"source_id": self._validate_id(source_id)},
                )
        except Neo4jError as exc:
            logger.error(
                "Failed to find relationships for %s: %s", source_id, exc,
            )
            raise DatabaseReadError(
                f"Failed to find relationships for '{source_id}'."
            ) from exc

        return records

    def get_graph_context(
        self, chunk_ids: list[str],
    ) -> dict[str, Any]:
        """
        Retrieve the graph neighbourhood for a set of chunks.

        Returns entities mentioned by the chunks and the relationships
        between those entities.  This is the primary context provider
        for future GraphRAG retrieval.
        """
        self._ensure_open()

        if not chunk_ids:
            return {"entities": [], "relationships": []}

        try:
            with self._connection.read_session() as session:
                records = session.execute_read(
                    self._execute_read,
                    GET_GRAPH_CONTEXT,
                    {"chunk_ids": chunk_ids},
                )
        except Neo4jError as exc:
            logger.error(
                "Failed to get graph context for %d chunks: %s",
                len(chunk_ids),
                exc,
            )
            raise DatabaseReadError(
                "Failed to retrieve graph context."
            ) from exc

        if not records:
            return {"entities": [], "relationships": []}

        row = records[0]
        return {
            "entities": row.get("entities", []),
            "relationships": [
                rel for rel in row.get("relationships", [])
                if rel.get("relationship_type") is not None
            ],
        }

    def execute_read_query(
        self,
        cypher: str,
        parameters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Execute an arbitrary parameterized Cypher read query.

        This is an escape hatch for future retrieval queries that do not
        yet have dedicated repository methods.

        Args:
            cypher: A parameterized Cypher query string.
            parameters: Query parameters.

        Returns:
            A list of record dictionaries.
        """
        self._ensure_open()

        try:
            with self._connection.read_session() as session:
                records = session.execute_read(
                    self._execute_read,
                    cypher,
                    parameters or {},
                )
        except Neo4jError as exc:
            logger.error("Read query failed: %s", exc)
            raise DatabaseReadError("Read query failed.") from exc

        return records

    # -----------------------------------------------------------------------
    # BATCH operations
    # -----------------------------------------------------------------------

    def batch_upsert_chunks(
        self,
        chunks: list[dict[str, Any]],
    ) -> int:
        """
        Upsert multiple Chunk nodes in a single transaction.

        Each item in ``chunks`` must contain keys:
        ``id``, ``text``, ``page``, ``chunk_index``, ``source_path``,
        ``document_id``. Optional key: ``embedding`` (list of floats).

        Returns:
            The number of chunks upserted.
        """
        self._ensure_open()

        if not chunks:
            return 0

        logger.info("Batch upserting %d chunks.", len(chunks))

        try:
            with self._connection.session() as session:
                records = session.execute_write(
                    self._execute_read,
                    BATCH_MERGE_CHUNKS,
                    {"items": chunks},
                )
        except Neo4jError as exc:
            logger.error("Batch chunk upsert failed: %s", exc)
            raise DatabaseWriteError(
                f"Batch chunk upsert failed for {len(chunks)} chunks."
            ) from exc

        count = len(records)
        logger.info("Batch upserted %d chunks.", count)
        return count

    def batch_link_document_chunks(
        self,
        links: list[dict[str, str]],
    ) -> int:
        """
        Create CONTAINS relationships between a document and chunks in
        a single transaction.

        Each item in ``links`` must contain keys:
        ``document_id``, ``chunk_id``.

        Returns:
            The number of relationships created.
        """
        self._ensure_open()

        if not links:
            return 0

        logger.info("Batch linking %d document-chunk relationships.", len(links))

        try:
            with self._connection.session() as session:
                records = session.execute_write(
                    self._execute_read,
                    BATCH_LINK_DOCUMENT_CHUNKS,
                    {"items": links},
                )
        except Neo4jError as exc:
            logger.error("Batch document-chunk linking failed: %s", exc)
            raise DatabaseWriteError(
                f"Batch document-chunk linking failed for {len(links)} links."
            ) from exc

        count = len(records)
        logger.info("Batch linked %d document-chunk relationships.", count)
        return count

    def batch_upsert_entities(
        self,
        label: str,
        entities: list[dict[str, Any]],
    ) -> int:
        """
        Batch upsert entities of a specific label.

        Each item in ``entities`` must contain keys:
        ``id``, ``name``, ``entity_type``, ``description``, ``source_chunk_id``.
        """
        self._ensure_open()

        if not entities:
            return 0

        # Validate label to prevent injection
        allowed_labels = {
            "Zone", "Risk", "Infrastructure", "Mitigation", "Budget",
            "Policy", "Project", "Claim", "Evidence", "Entity"
        }
        if label not in allowed_labels:
            raise ValueError(f"Label '{label}' is not a recognized node type.")

        cypher = f"""
        UNWIND $items AS item
        MERGE (n:{label} {{id: item.id}})
        SET
            n.name = item.name,
            n.entity_type = item.entity_type,
            n.description = item.description,
            n.source_chunk_id = item.source_chunk_id
        RETURN n.id AS node_id
        """

        try:
            with self._connection.session() as session:
                records = session.execute_write(
                    self._execute_read, cypher, {"items": entities},
                )
        except Neo4jError as exc:
            logger.error("Batch %s upsert failed: %s", label, exc)
            raise DatabaseWriteError(f"Batch {label} upsert failed.") from exc

        return len(records)

    def batch_link_relationships(
        self,
        relationship_type: str,
        links: list[dict[str, str]],
    ) -> int:
        """
        Batch create relationships of a specific type.

        Each item in ``links`` must contain keys:
        ``source_id``, ``target_id``, ``description``, ``source_chunk_id``.
        """
        self._ensure_open()
        if not links:
            return 0

        allowed_types = {
            "CONTAINS", "MENTIONS", "HAS_RISK", "AFFECTS", "REQUIRES",
            "FUNDS", "REGULATES", "SUPPORTED_BY", "DERIVED_FROM",
            "ABOUT", "LOCATED_IN", "ADDRESSES", "ALLOCATES", "APPLIES_TO"
        }
        if relationship_type not in allowed_types:
            raise ValueError(f"Relationship type '{relationship_type}' is not recognized.")

        cypher = f"""
        UNWIND $items AS item
        MATCH (source {{id: item.source_id}})
        MATCH (target {{id: item.target_id}})
        MERGE (source)-[r:{relationship_type}]->(target)
        SET
            r.description = item.description,
            r.source_chunk_id = item.source_chunk_id
        RETURN type(r) AS relationship_type
        """
        try:
            with self._connection.session() as session:
                records = session.execute_write(
                    self._execute_read, cypher, {"items": links},
                )
        except Neo4jError as exc:
            logger.error("Batch relationship linking failed: %s", exc)
            raise DatabaseWriteError("Batch relationship linking failed.") from exc

        return len(records)

    def batch_upsert_claims(self, claims: list[dict[str, Any]]) -> int:
        """Batch upsert Claim nodes."""
        self._ensure_open()
        if not claims:
            return 0
        
        cypher = """
        UNWIND $items AS item
        MERGE (n:Claim {id: item.id})
        SET
            n.statement = item.statement,
            n.subject_entity_id = item.subject_entity_id,
            n.source_chunk_id = item.source_chunk_id,
            n.confidence = item.confidence
        RETURN n.id AS node_id
        """
        try:
            with self._connection.session() as session:
                records = session.execute_write(
                    self._execute_read, cypher, {"items": claims},
                )
        except Neo4jError as exc:
            logger.error("Batch Claim upsert failed: %s", exc)
            raise DatabaseWriteError("Batch Claim upsert failed.") from exc

        return len(records)

    def batch_upsert_evidence(self, evidence: list[dict[str, Any]]) -> int:
        """Batch upsert Evidence nodes."""
        self._ensure_open()
        if not evidence:
            return 0
        
        cypher = """
        UNWIND $items AS item
        MERGE (n:Evidence {id: item.id})
        SET
            n.claim_id = item.claim_id,
            n.chunk_id = item.chunk_id,
            n.text = item.text,
            n.supports = item.supports
        RETURN n.id AS node_id
        """
        try:
            with self._connection.session() as session:
                records = session.execute_write(
                    self._execute_read, cypher, {"items": evidence},
                )
        except Neo4jError as exc:
            logger.error("Batch Evidence upsert failed: %s", exc)
            raise DatabaseWriteError("Batch Evidence upsert failed.") from exc

        return len(records)


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def create_repository(settings: Settings) -> KnowledgeGraphRepository:
    """
    Create a Project Oracle knowledge-graph repository
    with a verified Neo4j connection.

    Args:
        settings: Application configuration containing Neo4j credentials.
    """
    connection = create_neo4j_connection(settings)
    return KnowledgeGraphRepository(connection, owns_connection=True)