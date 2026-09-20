"""Integration tests for Neo4j connection."""

import pytest

from src.knowledge_graph.connection import Neo4jConnection


@pytest.mark.integration
class TestNeo4jConnection:
    """Tests that require a live Neo4j instance."""

    def test_session_returns_data(
        self, neo4j_connection: Neo4jConnection,
    ) -> None:
        with neo4j_connection.session() as session:
            result = session.run("RETURN 1 AS test")
            record = result.single()

        assert record is not None
        assert record["test"] == 1

    def test_read_session_returns_data(
        self, neo4j_connection: Neo4jConnection,
    ) -> None:
        with neo4j_connection.read_session() as session:
            result = session.run("RETURN 42 AS answer")
            record = result.single()

        assert record is not None
        assert record["answer"] == 42
