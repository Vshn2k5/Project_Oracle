"""
Neo4j schema management for Project Oracle.

Defines the graph constraints and indexes, and provides an idempotent
``apply_schema`` function that can be called at startup.
"""

import logging
from dataclasses import dataclass
from typing import Final

from neo4j.exceptions import Neo4jError

from src.config.settings import Settings
from src.knowledge_graph.connection import Neo4jConnection

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Schema abstractions
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class SchemaStatement:
    """A named, executable unit of Neo4j schema definition."""

    name: str
    cypher: str


@dataclass(frozen=True, slots=True)
class SchemaApplyResult:
    """Summary of the schema statements applied during one operation."""

    applied: tuple[str, ...]


class SchemaApplicationError(RuntimeError):
    """Raised when Neo4j rejects a schema statement."""

    def __init__(self, statement_name: str) -> None:
        super().__init__(f"Failed to apply Neo4j schema statement '{statement_name}'.")
        self.statement_name = statement_name


# ---------------------------------------------------------------------------
# Schema statements — uniqueness constraints
# ---------------------------------------------------------------------------

SCHEMA_STATEMENTS: Final[tuple[SchemaStatement, ...]] = (
    # --- Existing node types ---
    SchemaStatement(
        "document_id_unique",
        """
        CREATE CONSTRAINT document_id_unique IF NOT EXISTS
        FOR (n:Document)
        REQUIRE n.id IS UNIQUE
        """,
    ),
    SchemaStatement(
        "chunk_id_unique",
        """
        CREATE CONSTRAINT chunk_id_unique IF NOT EXISTS
        FOR (n:Chunk)
        REQUIRE n.id IS UNIQUE
        """,
    ),
    SchemaStatement(
        "zone_id_unique",
        """
        CREATE CONSTRAINT zone_id_unique IF NOT EXISTS
        FOR (n:Zone)
        REQUIRE n.id IS UNIQUE
        """,
    ),
    SchemaStatement(
        "risk_id_unique",
        """
        CREATE CONSTRAINT risk_id_unique IF NOT EXISTS
        FOR (n:Risk)
        REQUIRE n.id IS UNIQUE
        """,
    ),
    SchemaStatement(
        "infrastructure_id_unique",
        """
        CREATE CONSTRAINT infrastructure_id_unique IF NOT EXISTS
        FOR (n:Infrastructure)
        REQUIRE n.id IS UNIQUE
        """,
    ),
    SchemaStatement(
        "mitigation_id_unique",
        """
        CREATE CONSTRAINT mitigation_id_unique IF NOT EXISTS
        FOR (n:Mitigation)
        REQUIRE n.id IS UNIQUE
        """,
    ),
    SchemaStatement(
        "budget_id_unique",
        """
        CREATE CONSTRAINT budget_id_unique IF NOT EXISTS
        FOR (n:Budget)
        REQUIRE n.id IS UNIQUE
        """,
    ),
    SchemaStatement(
        "policy_id_unique",
        """
        CREATE CONSTRAINT policy_id_unique IF NOT EXISTS
        FOR (n:Policy)
        REQUIRE n.id IS UNIQUE
        """,
    ),
    # --- New node types for provenance / reasoning ---
    SchemaStatement(
        "claim_id_unique",
        """
        CREATE CONSTRAINT claim_id_unique IF NOT EXISTS
        FOR (n:Claim)
        REQUIRE n.id IS UNIQUE
        """,
    ),
    SchemaStatement(
        "evidence_id_unique",
        """
        CREATE CONSTRAINT evidence_id_unique IF NOT EXISTS
        FOR (n:Evidence)
        REQUIRE n.id IS UNIQUE
        """,
    ),
    SchemaStatement(
        "project_id_unique",
        """
        CREATE CONSTRAINT project_id_unique IF NOT EXISTS
        FOR (n:Project)
        REQUIRE n.id IS UNIQUE
        """,
    ),
    # --- Indexes for common query patterns ---
    SchemaStatement(
        "chunk_document_id_index",
        """
        CREATE INDEX chunk_document_id_index IF NOT EXISTS
        FOR (n:Chunk)
        ON (n.document_id)
        """,
    ),
    SchemaStatement(
        "chunk_page_index",
        """
        CREATE INDEX chunk_page_index IF NOT EXISTS
        FOR (n:Chunk)
        ON (n.page)
        """,
    ),
    # --- Full-text index for future keyword search ---
    SchemaStatement(
        "chunk_text_index",
        """
        CREATE FULLTEXT INDEX chunk_text_index IF NOT EXISTS
        FOR (n:Chunk)
        ON EACH [n.text]
        """,
    ),
)


def apply_schema(connection: Neo4jConnection, settings: Settings | None = None) -> SchemaApplyResult:
    """
    Apply the Project Oracle schema to Neo4j.

    The operation is idempotent: existing constraints and indexes are not
    recreated.

    Args:
        connection: An open Neo4j connection.
        settings: Application settings to configure the vector index dimension.

    Returns:
        The names of the statements successfully applied.

    Raises:
        SchemaApplicationError: If a statement is rejected by Neo4j.
    """
    applied: list[str] = []

    # Inject the vector index statement dynamically based on settings
    statements = list(SCHEMA_STATEMENTS)
    if settings:
        dim = settings.embedding_dimension
        vector_index_statement = SchemaStatement(
            "chunk_embedding_vector_index",
            f"""
            CREATE VECTOR INDEX chunk_embedding IF NOT EXISTS
            FOR (c:Chunk) ON (c.embedding)
            OPTIONS {{
                indexConfig: {{
                    `vector.dimensions`: {dim},
                    `vector.similarity_function`: 'cosine'
                }}
            }}
            """,
        )
        statements.append(vector_index_statement)
    else:
        logger.warning("No Settings provided to apply_schema. Vector index will NOT be created.")

    logger.info(
        "Applying Project Oracle schema (%d statements).",
        len(statements),
    )

    with connection.session() as session:
        for statement in statements:
            try:
                session.run(statement.cypher).consume()
            except Neo4jError as exc:
                logger.error(
                    "Schema statement '%s' failed: %s",
                    statement.name,
                    exc,
                )
                raise SchemaApplicationError(statement.name) from exc

            logger.debug("Applied schema statement '%s'.", statement.name)
            applied.append(statement.name)

    logger.info(
        "Project Oracle schema applied successfully (%d statements).",
        len(applied),
    )

    return SchemaApplyResult(applied=tuple(applied))