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

    # LLM Configuration
    llm_provider: str = "google-genai"
    llm_model: str = "gemini-2.5-flash"
    llm_api_key: str | None = field(default=None, repr=False)

    # Embedding Configuration
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimension: int = 384

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
            llm_provider=os.getenv("LLM_PROVIDER", "google-genai").strip(),
            llm_model=os.getenv("LLM_MODEL", "gemini-2.5-flash").strip(),
            llm_api_key=os.getenv("LLM_API_KEY", "").strip() or None,
            embedding_model=os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2").strip(),
            embedding_dimension=int(os.getenv("EMBEDDING_DIMENSION", "384").strip()),
        )