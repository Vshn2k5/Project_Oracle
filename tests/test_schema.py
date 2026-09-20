"""
Unit tests for the Neo4j schema module.

These tests validate the schema statement definitions and the
SchemaApplicationError exception without requiring a live Neo4j instance.
"""

import pytest

from src.knowledge_graph.schema import (
    SCHEMA_STATEMENTS,
    SchemaApplicationError,
    SchemaApplyResult,
    SchemaStatement,
)


class TestSchemaStatements:
    """Validate the schema statement definitions."""

    def test_all_statements_have_names(self) -> None:
        for statement in SCHEMA_STATEMENTS:
            assert statement.name, f"Statement has no name: {statement}"

    def test_all_statements_have_cypher(self) -> None:
        for statement in SCHEMA_STATEMENTS:
            assert statement.cypher.strip(), (
                f"Statement '{statement.name}' has no Cypher."
            )

    def test_statement_names_unique(self) -> None:
        names = [s.name for s in SCHEMA_STATEMENTS]
        assert len(names) == len(set(names)), "Duplicate statement names found."

    def test_expected_constraints_present(self) -> None:
        names = {s.name for s in SCHEMA_STATEMENTS}
        expected = {
            "document_id_unique",
            "chunk_id_unique",
            "zone_id_unique",
            "risk_id_unique",
            "infrastructure_id_unique",
            "mitigation_id_unique",
            "budget_id_unique",
            "policy_id_unique",
            "claim_id_unique",
            "evidence_id_unique",
            "project_id_unique",
        }
        assert expected.issubset(names), (
            f"Missing constraints: {expected - names}"
        )

    def test_indexes_present(self) -> None:
        names = {s.name for s in SCHEMA_STATEMENTS}
        assert "chunk_document_id_index" in names
        assert "chunk_page_index" in names

    def test_all_use_if_not_exists(self) -> None:
        for statement in SCHEMA_STATEMENTS:
            assert "IF NOT EXISTS" in statement.cypher, (
                f"Statement '{statement.name}' is not idempotent."
            )

    def test_total_count(self) -> None:
        # 8 original constraints + 3 new constraints + 2 indexes = 13
        assert len(SCHEMA_STATEMENTS) == 13


class TestSchemaExceptions:
    """Schema exception behavior."""

    def test_application_error_message(self) -> None:
        error = SchemaApplicationError("test_constraint")
        assert "test_constraint" in str(error)
        assert error.statement_name == "test_constraint"

    def test_application_error_is_runtime_error(self) -> None:
        assert issubclass(SchemaApplicationError, RuntimeError)


class TestSchemaApplyResult:
    """Schema result dataclass."""

    def test_apply_result(self) -> None:
        result = SchemaApplyResult(applied=("a", "b", "c"))
        assert len(result.applied) == 3
