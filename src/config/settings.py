"""
Configuration management for Project Oracle.

Settings are created explicitly by the application rather than at import
time.  This allows tests and future API entry points to supply their own
configuration without environment-variable side effects.
"""

from dataclasses import dataclass, field
import logging
import os

logger = logging.getLogger(__name__)


class ConfigurationError(RuntimeError):
    """Raised when required configuration is missing or invalid."""


def _get_required_env(name: str) -> str:
    """
    Read a required environment variable.

    Raises:
        ConfigurationError: If the variable is missing or empty.
    """
    value = os.getenv(name)

    if value is None or not value.strip():
        raise ConfigurationError(
            f"Required environment variable '{name}' is not configured."
        )

    return value.strip()


@dataclass(frozen=True, slots=True)
class Settings:
    """
    Central configuration for Project Oracle.

    Create with ``Settings.from_environment()`` to load values from
    environment variables, or construct directly for testing.
    """

    neo4j_uri: str
    neo4j_username: str
    neo4j_password: str = field(repr=False)
    neo4j_database: str = "neo4j"

    @classmethod
    def from_environment(cls) -> "Settings":
        """
        Build the application configuration from environment variables.

        Calls ``load_dotenv()`` to pick up a ``.env`` file if present.

        Raises:
            ConfigurationError: If a required variable is missing.
        """
        from dotenv import load_dotenv

        load_dotenv()

        logger.info("Loading Project Oracle configuration from environment.")

        return cls(
            neo4j_uri=_get_required_env("NEO4J_URI"),
            neo4j_username=_get_required_env("NEO4J_USERNAME"),
            neo4j_password=_get_required_env("NEO4J_PASSWORD"),
            neo4j_database=os.getenv("NEO4J_DATABASE", "neo4j").strip(),
        )