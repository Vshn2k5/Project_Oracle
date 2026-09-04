from dataclasses import dataclass, field
import os

from dotenv import load_dotenv


# Load variables from the project's .env file.
load_dotenv()


def _get_required_env(name: str) -> str:
    """
    Read a required environment variable.

    Raises:
        RuntimeError: If the variable is missing or empty.
    """
    value = os.getenv(name)

    if value is None or not value.strip():
        raise RuntimeError(
            f"Required environment variable '{name}' is not configured."
        )

    return value.strip()


@dataclass(frozen=True, slots=True)
class Settings:
    """
    Central configuration for Project Oracle.
    """

    neo4j_uri: str
    neo4j_username: str
    neo4j_password: str = field(repr=False)
    neo4j_database: str

    @classmethod
    def from_environment(cls) -> "Settings":
        """
        Build the application configuration from environment variables.
        """
        return cls(
            neo4j_uri=_get_required_env("NEO4J_URI"),
            neo4j_username=_get_required_env("NEO4J_USERNAME"),
            neo4j_password=_get_required_env("NEO4J_PASSWORD"),
            neo4j_database=os.getenv("NEO4J_DATABASE", "neo4j").strip(),
        )


settings = Settings.from_environment()