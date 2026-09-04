from dataclasses import dataclass
from typing import Any, Final

from neo4j import Transaction
from neo4j.exceptions import Neo4jError

from src.knowledge_graph.connection import (
    Neo4jConnection,
    create_neo4j_connection,
)


@dataclass(frozen=True, slots=True)
class NodeWriteResult:
    """Result returned after creating or updating a graph node."""

    node_id: str
    label: str


@dataclass(frozen=True, slots=True)
class RelationshipWriteResult:
    """Result returned after creating or confirming a graph relationship."""

    relationship_type: str


class KnowledgeGraphRepositoryError(RuntimeError):
    """Raised when a knowledge-graph repository operation fails."""


# ---------------------------------------------------------------------------
# Cypher statements
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
    n.chunk_index = $chunk_index
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


class KnowledgeGraphRepository:
    """
    Provides controlled database operations for Project Oracle's
    knowledge graph.

    The repository uses the Neo4jConnection abstraction supplied by the
    application. A repository created by create_repository owns its
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
            raise KnowledgeGraphRepositoryError(
                f"Failed to write {label} node."
            ) from exc

        if record is None:
            raise KnowledgeGraphRepositoryError(
                f"Neo4j did not return the id of the {label} node."
            )

        try:
            node_id = record["node_id"]
        except (KeyError, TypeError) as exc:
            raise KnowledgeGraphRepositoryError(
                f"Neo4j returned an invalid response for the {label} node."
            ) from exc

        if not isinstance(node_id, str) or not node_id:
            raise KnowledgeGraphRepositoryError(
                f"Neo4j returned an invalid id for the {label} node."
            )

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
            raise KnowledgeGraphRepositoryError(
                f"Failed to write {relationship_type} relationship."
            ) from exc

        if record is None:
            raise KnowledgeGraphRepositoryError(
                f"Cannot create {relationship_type} relationship: "
                "one or both endpoint nodes do not exist."
            )

        try:
            returned_type = record["relationship_type"]
        except (KeyError, TypeError) as exc:
            raise KnowledgeGraphRepositoryError(
                f"Neo4j returned an invalid response for the "
                f"{relationship_type} relationship."
            ) from exc

        if returned_type != relationship_type:
            raise KnowledgeGraphRepositoryError(
                f"Neo4j returned unexpected relationship type "
                f"'{returned_type}' for {relationship_type}."
            )

        return RelationshipWriteResult(relationship_type=returned_type)

    # -----------------------------------------------------------------------
    # Document
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
    # Chunk
    # -----------------------------------------------------------------------

    def upsert_chunk(
        self,
        *,
        node_id: str,
        text: str,
        page: int,
        chunk_index: int,
    ) -> NodeWriteResult:
        """Create or update a Chunk node."""
        return self._merge_node(
            label="Chunk",
            cypher=MERGE_CHUNK,
            parameters={
                "id": self._validate_id(node_id),
                "text": text,
                "page": page,
                "chunk_index": chunk_index,
            },
        )

    # -----------------------------------------------------------------------
    # Zone
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
    # Risk
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
    # Infrastructure
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
    # Mitigation
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
    # Budget
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
    # Policy
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
    # Relationships
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


def create_repository() -> KnowledgeGraphRepository:
    """
    Create a Project Oracle knowledge-graph repository
    with a verified Neo4j connection.
    """
    connection = create_neo4j_connection()
    return KnowledgeGraphRepository(connection, owns_connection=True)