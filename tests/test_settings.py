"""Tests for the Project Oracle configuration system."""

import os

import pytest

from src.config.settings import ConfigurationError, Settings


class TestSettingsDirectConstruction:
    """Settings can be created directly for testing and DI."""

    def test_create_with_all_fields(self) -> None:
        settings = Settings(
            neo4j_uri="bolt://localhost:7687",
            neo4j_username="neo4j",
            neo4j_password="secret",
            neo4j_database="testdb",
        )
        assert settings.neo4j_uri == "bolt://localhost:7687"
        assert settings.neo4j_username == "neo4j"
        assert settings.neo4j_password == "secret"
        assert settings.neo4j_database == "testdb"

    def test_default_database(self) -> None:
        settings = Settings(
            neo4j_uri="bolt://localhost:7687",
            neo4j_username="neo4j",
            neo4j_password="secret",
        )
        assert settings.neo4j_database == "neo4j"

    def test_settings_are_frozen(self) -> None:
        settings = Settings(
            neo4j_uri="bolt://localhost:7687",
            neo4j_username="neo4j",
            neo4j_password="secret",
        )
        with pytest.raises(AttributeError):
            settings.neo4j_uri = "bolt://other:7687"  # type: ignore[misc]

    def test_password_not_in_repr(self) -> None:
        settings = Settings(
            neo4j_uri="bolt://localhost:7687",
            neo4j_username="neo4j",
            neo4j_password="super-secret",
        )
        representation = repr(settings)
        assert "super-secret" not in representation


class TestSettingsFromEnvironment:
    """Settings.from_environment() reads env vars correctly."""

    @pytest.fixture(autouse=True)
    def mock_load_dotenv(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Prevent tests from reading the real .env file."""
        monkeypatch.setattr("dotenv.load_dotenv", lambda **kwargs: True)
        # Also clean up the environment so tests start fresh
        monkeypatch.delenv("NEO4J_URI", raising=False)
        monkeypatch.delenv("NEO4J_USERNAME", raising=False)
        monkeypatch.delenv("NEO4J_PASSWORD", raising=False)
        monkeypatch.delenv("NEO4J_DATABASE", raising=False)

    def test_loads_from_environment(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("NEO4J_URI", "bolt://testhost:7687")
        monkeypatch.setenv("NEO4J_USERNAME", "testuser")
        monkeypatch.setenv("NEO4J_PASSWORD", "testpass")
        monkeypatch.setenv("NEO4J_DATABASE", "testdb")

        settings = Settings.from_environment()

        assert settings.neo4j_uri == "bolt://testhost:7687"
        assert settings.neo4j_username == "testuser"
        assert settings.neo4j_password == "testpass"
        assert settings.neo4j_database == "testdb"

    def test_missing_uri_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("NEO4J_URI", raising=False)
        monkeypatch.setenv("NEO4J_USERNAME", "neo4j")
        monkeypatch.setenv("NEO4J_PASSWORD", "pass")

        with pytest.raises(ConfigurationError, match="NEO4J_URI"):
            Settings.from_environment()

    def test_missing_password_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("NEO4J_URI", "bolt://localhost:7687")
        monkeypatch.setenv("NEO4J_USERNAME", "neo4j")
        monkeypatch.delenv("NEO4J_PASSWORD", raising=False)

        with pytest.raises(ConfigurationError, match="NEO4J_PASSWORD"):
            Settings.from_environment()

    def test_empty_uri_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("NEO4J_URI", "   ")
        monkeypatch.setenv("NEO4J_USERNAME", "neo4j")
        monkeypatch.setenv("NEO4J_PASSWORD", "pass")

        with pytest.raises(ConfigurationError, match="NEO4J_URI"):
            Settings.from_environment()

    def test_default_database_from_environment(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("NEO4J_URI", "bolt://localhost:7687")
        monkeypatch.setenv("NEO4J_USERNAME", "neo4j")
        monkeypatch.setenv("NEO4J_PASSWORD", "pass")
        monkeypatch.delenv("NEO4J_DATABASE", raising=False)

        settings = Settings.from_environment()
        assert settings.neo4j_database == "neo4j"
