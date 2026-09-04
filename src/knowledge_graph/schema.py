from dataclasses import dataclass
from typing import Final

from neo4j.exceptions import Neo4jError

from src.knowledge_graph.connection import Neo4jConnection, create_neo4j_connection


# ---------------------------------------------------------------------------
# Node identity constraints
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


SCHEMA_STATEMENTS: Final[tuple[SchemaStatement, ...]] = (
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
)


def apply_schema(connection: Neo4jConnection | None = None) -> SchemaApplyResult:
    """
    Apply the Project Oracle Phase-I schema to Neo4j.

    The operation is idempotent: existing constraints are not recreated.

    Args:
        connection: Optional connection supplied by a caller or test. When
            omitted, a verified connection is created and closed here.

    Returns:
        The names of the statements successfully applied.
    """
    owns_connection = connection is None
    active_connection = (
        connection if connection is not None else create_neo4j_connection()
    )
    applied: list[str] = []

    try:
        with active_connection.session() as session:
            for statement in SCHEMA_STATEMENTS:
                try:
                    session.run(statement.cypher).consume()
                except Neo4jError as exc:
                    raise SchemaApplicationError(statement.name) from exc
                applied.append(statement.name)
    finally:
        if owns_connection:
            active_connection.close()

    return SchemaApplyResult(applied=tuple(applied))


def main() -> None:
    """Apply the Neo4j schema."""
    result = apply_schema()
    print(f"Project Oracle Neo4j schema applied successfully ({len(result.applied)} statements).")


if __name__ == "__main__":
    main()