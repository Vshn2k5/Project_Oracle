"""
Unit tests for the knowledge-graph repository.

These tests exercise validation, error handling, and structural logic
WITHOUT requiring a live Neo4j instance.
"""

import pytest

from src.knowledge_graph.repository import (
    DatabaseReadError,
    DatabaseWriteError,
    KnowledgeGraphRepository,
    KnowledgeGraphRepositoryError,
    NodeWriteResult,
    RelationshipWriteResult,
)


class TestRepositoryValidation:
    """ID validation and lifecycle checks."""

    def test_validate_id_strips_whitespace(self) -> None:
        result = KnowledgeGraphRepository._validate_id("  DOC-001  ")
        assert result == "DOC-001"

    def test_validate_id_empty_raises(self) -> None:
        with pytest.raises(ValueError, match="cannot be empty"):
            KnowledgeGraphRepository._validate_id("   ")

    def test_validate_id_non_string_raises(self) -> None:
        with pytest.raises(TypeError, match="must be a string"):
            KnowledgeGraphRepository._validate_id(42)  # type: ignore[arg-type]


class TestResultTypes:
    """Write result dataclasses are correct."""

    def test_node_write_result(self) -> None:
        result = NodeWriteResult(node_id="DOC-001", label="Document")
        assert result.node_id == "DOC-001"
        assert result.label == "Document"

    def test_relationship_write_result(self) -> None:
        result = RelationshipWriteResult(relationship_type="CONTAINS")
        assert result.relationship_type == "CONTAINS"

    def test_node_write_result_frozen(self) -> None:
        result = NodeWriteResult(node_id="DOC-001", label="Document")
        with pytest.raises(AttributeError):
            result.node_id = "DOC-002"  # type: ignore[misc]


class TestExceptionHierarchy:
    """Exception hierarchy is correct."""

    def test_write_error_is_repo_error(self) -> None:
        assert issubclass(DatabaseWriteError, KnowledgeGraphRepositoryError)

    def test_read_error_is_repo_error(self) -> None:
        assert issubclass(DatabaseReadError, KnowledgeGraphRepositoryError)

    def test_repo_error_is_runtime_error(self) -> None:
        assert issubclass(KnowledgeGraphRepositoryError, RuntimeError)
