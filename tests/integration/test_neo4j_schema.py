"""Integration tests for the Neo4j schema module."""

import pytest

from src.knowledge_graph.connection import Neo4jConnection
from src.knowledge_graph.schema import SCHEMA_STATEMENTS, apply_schema


@pytest.mark.integration
class TestSchemaApplication:
    """Apply schema to a live Neo4j instance."""

    def test_apply_schema_idempotent(
        self, neo4j_connection: Neo4jConnection,
    ) -> None:
        result_a = apply_schema(neo4j_connection)
        result_b = apply_schema(neo4j_connection)

        assert len(result_a.applied) == len(SCHEMA_STATEMENTS)
        assert result_a.applied == result_b.applied

    def test_all_statements_applied(
        self, neo4j_connection: Neo4jConnection,
    ) -> None:
        result = apply_schema(neo4j_connection)
        assert len(result.applied) == len(SCHEMA_STATEMENTS)

        expected_names = {s.name for s in SCHEMA_STATEMENTS}
        applied_names = set(result.applied)
        assert expected_names == applied_names
