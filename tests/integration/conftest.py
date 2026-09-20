"""
Integration test fixtures for Neo4j.

All tests in this directory require a running Neo4j instance and are
marked with ``@pytest.mark.integration``.
"""

import pytest

from src.config.settings import Settings
from src.knowledge_graph.connection import Neo4jConnection, create_neo4j_connection


@pytest.fixture(scope="session")
def neo4j_settings() -> Settings:
    """Load real Neo4j settings from environment variables."""
    try:
        return Settings.from_environment()
    except Exception as exc:
        pytest.skip(f"Neo4j settings not available: {exc}")


@pytest.fixture(scope="session")
def neo4j_connection(neo4j_settings: Settings) -> Neo4jConnection:
    """Create a verified Neo4j connection for the test session."""
    try:
        connection = create_neo4j_connection(neo4j_settings)
    except Exception as exc:
        pytest.skip(f"Cannot connect to Neo4j: {exc}")

    yield connection  # type: ignore[misc]
    connection.close()
