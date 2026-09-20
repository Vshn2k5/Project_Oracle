"""
Neo4j connection management for Project Oracle.

The connection is created with explicit ``Settings`` — it does not read
global state.  Both write and read sessions are supported.
"""

import logging
from contextlib import contextmanager
from collections.abc import Generator
from types import TracebackType

from neo4j import Driver, GraphDatabase, Session

from src.config.settings import Settings

logger = logging.getLogger(__name__)


class Neo4jConnection:
    """
    Manages the connection between Project Oracle and Neo4j.

    The class owns a single Neo4j driver and provides sessions
    for database operations.

    Args:
        settings: Application configuration containing Neo4j credentials.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._driver: Driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(
                settings.neo4j_username,
                settings.neo4j_password,
            ),
        )
        self._closed = False
        logger.info("Neo4j driver created for %s.", settings.neo4j_uri)

    def verify_connectivity(self) -> None:
        """
        Verify that Neo4j is reachable using the configured credentials.

        Raises:
            RuntimeError: If this connection has already been closed.
            Exception: If Neo4j cannot be reached or authentication fails.
        """
        self._ensure_open()
        self._driver.verify_connectivity()
        logger.info("Neo4j connectivity verified.")

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        """
        Provide a Neo4j session for database operations.
        """
        self._ensure_open()
        with self._driver.session(
            database=self._settings.neo4j_database
        ) as session:
            yield session

    def _ensure_open(self) -> None:
        """Ensure the connection has not been closed."""
        if self._closed:
            raise RuntimeError("Neo4j connection is closed.")

    def close(self) -> None:
        """
        Close the Neo4j driver and release its resources.
        """
        if self._closed:
            return

        self._driver.close()
        self._closed = True
        logger.info("Neo4j connection closed.")

    def __enter__(self) -> "Neo4jConnection":
        self._ensure_open()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()


def create_neo4j_connection(settings: Settings) -> Neo4jConnection:
    """
    Create and verify a Neo4j connection for Project Oracle.

    Args:
        settings: Application configuration containing Neo4j credentials.

    Returns:
        A verified Neo4jConnection instance.
    """
    connection = Neo4jConnection(settings)
    try:
        connection.verify_connectivity()
    except Exception:
        connection.close()
        raise

    return connection