"""
Shared fixtures for Project Oracle unit tests.
"""

import os
from pathlib import Path

import pytest

from src.config.settings import Settings


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
FLOODS_PDF = DATA_DIR / "Floods.pdf"


def floods_pdf_available() -> bool:
    """Return True if the sample Floods.pdf is present on disk."""
    return FLOODS_PDF.is_file()


requires_floods_pdf = pytest.mark.skipif(
    not floods_pdf_available(),
    reason="data/raw/Floods.pdf not available in this environment.",
)


# ---------------------------------------------------------------------------
# Settings fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def test_settings() -> Settings:
    """Return a Settings instance with dummy credentials for unit tests."""
    return Settings(
        neo4j_uri="bolt://localhost:7687",
        neo4j_username="neo4j",
        neo4j_password="test-password",
        neo4j_database="neo4j",
    )
