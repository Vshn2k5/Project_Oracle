from contextlib import contextmanager
from collections.abc import Generator
from types import TracebackType

from neo4j import Driver, GraphDatabase, Session

from src.config.settings import settings


class Neo4jConnection:
    """
    Manages the connection between Project Oracle and Neo4j.

    The class owns a single Neo4j driver and provides sessions
    for database operations.
    """

    def __init__(self) -> None:
        self._driver: Driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(
                settings.neo4j_username,
                settings.neo4j_password,
            ),
        )
        self._closed = False

    def verify_connectivity(self) -> None:
        """
        Verify that Neo4j is reachable using the configured credentials.

        Raises:
            RuntimeError: If this connection has already been closed.
            Exception: If Neo4j cannot be reached or authentication fails.
        """
        self._ensure_open()
        self._driver.verify_connectivity()

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        """
        Provide a Neo4j session for database operations.
        """
        self._ensure_open()
        with self._driver.session(
            database=settings.neo4j_database
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


def create_neo4j_connection() -> Neo4jConnection:
    """
    Create and verify a Neo4j connection for Project Oracle.

    Returns:
        A verified Neo4jConnection instance.
    """
    connection = Neo4jConnection()
    try:
        connection.verify_connectivity()
    except Exception:
        connection.close()
        raise

    return connection