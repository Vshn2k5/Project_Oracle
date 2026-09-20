"""Tests for the shared domain models."""

import pytest

from src.models.document import (
    CleanedDocument,
    CleanedPage,
    DocumentChunk,
    EmbeddedChunk,
    ExtractedDocument,
    ExtractedPage,
)
from src.models.knowledge_graph import (
    Claim,
    Entity,
    Evidence,
    ExtractedRelationship,
)
from src.models.retrieval import (
    GraphContext,
    RetrievedChunk,
    RetrievedContext,
)
from src.models.agent import AgentResult, Recommendation
from src.models.verification import VerificationResult


class TestDocumentModels:
    """Document-layer models are frozen and well-typed."""

    def test_embedded_chunk(self) -> None:
        chunk = DocumentChunk(
            chunk_id="C-001",
            document_id="DOC-abc",
            source_path="/tmp/test.pdf",
            page_number=1,
            chunk_index=0,
            text="sample",
        )
        embedded = EmbeddedChunk(
            chunk=chunk,
            embedding=(0.1, 0.2, 0.3),
        )
        assert embedded.chunk.chunk_id == "C-001"
        assert len(embedded.embedding) == 3

    def test_embedded_chunk_is_frozen(self) -> None:
        chunk = DocumentChunk(
            chunk_id="C-001",
            document_id="DOC-abc",
            source_path="/tmp/test.pdf",
            page_number=1,
            chunk_index=0,
            text="sample",
        )
        embedded = EmbeddedChunk(chunk=chunk, embedding=(0.1,))
        with pytest.raises(AttributeError):
            embedded.embedding = (0.9,)  # type: ignore[misc]


class TestKnowledgeGraphModels:
    """Knowledge-graph layer models."""

    def test_entity(self) -> None:
        entity = Entity(
            entity_id="ENT-001",
            label="Zone",
            name="Kochi",
            entity_type="city",
            description="Coastal city in Kerala",
            source_chunk_id="C-001",
        )
        assert entity.label == "Zone"
        assert entity.entity_id == "ENT-001"

    def test_extracted_relationship(self) -> None:
        rel = ExtractedRelationship(
            source_entity_id="ENT-001",
            target_entity_id="ENT-002",
            relationship_type="HAS_RISK",
            description="Zone has flood risk",
            source_chunk_id="C-001",
        )
        assert rel.relationship_type == "HAS_RISK"

    def test_claim(self) -> None:
        claim = Claim(
            claim_id="CLM-001",
            statement="Kochi experiences annual flooding.",
            subject_entity_id="ENT-001",
            source_chunk_id="C-001",
            confidence=0.85,
        )
        assert claim.confidence == 0.85

    def test_evidence(self) -> None:
        evidence = Evidence(
            evidence_id="EV-001",
            claim_id="CLM-001",
            chunk_id="C-001",
            text="Kochi floods occur every monsoon season.",
            supports=True,
        )
        assert evidence.supports is True

    def test_entity_is_frozen(self) -> None:
        entity = Entity(
            entity_id="ENT-001",
            label="Zone",
            name="Test",
            entity_type="test",
            description="",
            source_chunk_id="C-001",
        )
        with pytest.raises(AttributeError):
            entity.name = "Changed"  # type: ignore[misc]


class TestRetrievalModels:
    """Retrieval-layer models."""

    def test_retrieved_context(self) -> None:
        chunk = RetrievedChunk(
            chunk_id="C-001",
            text="sample",
            page_number=1,
            document_id="DOC-abc",
            document_title="Floods Report",
            score=0.92,
        )
        context = RetrievedContext(
            query="flood risk",
            chunks=(chunk,),
            graph_context=GraphContext(entities=(), relationships=()),
        )
        assert context.query == "flood risk"
        assert len(context.chunks) == 1


class TestAgentModels:
    """Agent-layer models."""

    def test_agent_result(self) -> None:
        rec = Recommendation(
            recommendation_id="REC-001",
            title="Build flood barriers",
            description="Install concrete barriers along the coast.",
            priority="high",
            supporting_claim_ids=("CLM-001",),
        )
        result = AgentResult(
            agent_name="risk_analysis",
            analysis="Flood risk is critical in Zone A.",
            recommendations=(rec,),
            confidence=0.88,
            claim_ids=("CLM-001",),
            evidence_chunk_ids=("C-001",),
        )
        assert result.agent_name == "risk_analysis"
        assert len(result.recommendations) == 1


class TestVerificationModels:
    """Verification-layer models."""

    def test_verification_result(self) -> None:
        vr = VerificationResult(
            claim_id="CLM-001",
            verdict="verified",
            explanation="Claim supported by 3 evidence nodes.",
            supporting_node_ids=("EV-001", "EV-002", "EV-003"),
            supporting_relationship_types=("SUPPORTED_BY",),
        )
        assert vr.verdict == "verified"
        assert len(vr.supporting_node_ids) == 3


class TestModelImports:
    """Verify models can be imported from the package root."""

    def test_imports_from_package(self) -> None:
        from src.models import (
            AgentResult,
            Claim,
            CleanedDocument,
            CleanedPage,
            DocumentChunk,
            EmbeddedChunk,
            Entity,
            Evidence,
            ExtractedDocument,
            ExtractedPage,
            ExtractedRelationship,
            GraphContext,
            Recommendation,
            RetrievedChunk,
            RetrievedContext,
            VerificationResult,
        )
        # Smoke test — just verify they are importable
        assert Entity is not None
        assert VerificationResult is not None
