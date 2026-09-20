"""Integration tests for the knowledge-graph repository."""

import pytest

from src.knowledge_graph.connection import Neo4jConnection
from src.knowledge_graph.repository import KnowledgeGraphRepository


@pytest.mark.integration
class TestRepositoryWrite:
    """Write operations against a live Neo4j instance."""

    def test_upsert_risk_and_infrastructure(
        self, neo4j_connection: Neo4jConnection,
    ) -> None:
        repo = KnowledgeGraphRepository(neo4j_connection)

        risk = repo.upsert_risk(
            node_id="RISK-INT-001",
            risk_type="urban_flood",
            severity="high",
            description="Integration test risk.",
        )
        assert risk.node_id == "RISK-INT-001"
        assert risk.label == "Risk"

        infra = repo.upsert_infrastructure(
            node_id="INF-INT-001",
            name="Test Hospital",
            infrastructure_type="hospital",
            description="Integration test infrastructure.",
        )
        assert infra.node_id == "INF-INT-001"

        rel = repo.link_risk_to_infrastructure(
            risk_id=risk.node_id,
            infrastructure_id=infra.node_id,
        )
        assert rel.relationship_type == "AFFECTS"


@pytest.mark.integration
class TestRepositoryRead:
    """Read operations against a live Neo4j instance."""

    def test_get_document_not_found(
        self, neo4j_connection: Neo4jConnection,
    ) -> None:
        repo = KnowledgeGraphRepository(neo4j_connection)
        result = repo.get_document("NONEXISTENT-DOC")
        assert result is None

    def test_write_then_read_document(
        self, neo4j_connection: Neo4jConnection,
    ) -> None:
        repo = KnowledgeGraphRepository(neo4j_connection)

        repo.upsert_document(
            node_id="DOC-INT-READ-001",
            title="Integration Test Document",
            source="/tmp/test.pdf",
            document_type="report",
            publication_date="2026-01-01",
        )

        doc = repo.get_document("DOC-INT-READ-001")
        assert doc is not None
        assert doc["id"] == "DOC-INT-READ-001"
        assert doc["title"] == "Integration Test Document"

    def test_find_entities_by_label(
        self, neo4j_connection: Neo4jConnection,
    ) -> None:
        repo = KnowledgeGraphRepository(neo4j_connection)

        repo.upsert_zone(
            node_id="ZONE-INT-001",
            name="Test Zone",
            description="Integration test zone.",
        )

        zones = repo.find_entities_by_label("Zone")
        assert any(z.get("id") == "ZONE-INT-001" for z in zones)

    def test_find_entity_by_id(
        self, neo4j_connection: Neo4jConnection,
    ) -> None:
        repo = KnowledgeGraphRepository(neo4j_connection)

        repo.upsert_zone(
            node_id="ZONE-INT-002",
            name="Find Test",
            description="Entity find test.",
        )

        result = repo.find_entity("ZONE-INT-002")
        assert result is not None
        assert "Zone" in result["labels"]

    def test_find_relationships(
        self, neo4j_connection: Neo4jConnection,
    ) -> None:
        repo = KnowledgeGraphRepository(neo4j_connection)

        repo.upsert_zone(
            node_id="ZONE-INT-REL-001",
            name="Rel Test Zone",
            description="Zone for relationship test.",
        )
        repo.upsert_risk(
            node_id="RISK-INT-REL-001",
            risk_type="flood",
            severity="medium",
            description="Risk for relationship test.",
        )
        repo.link_zone_to_risk(
            zone_id="ZONE-INT-REL-001",
            risk_id="RISK-INT-REL-001",
        )

        rels = repo.find_relationships("ZONE-INT-REL-001", "HAS_RISK")
        assert len(rels) >= 1
        assert rels[0]["relationship_type"] == "HAS_RISK"

    def test_execute_read_query(
        self, neo4j_connection: Neo4jConnection,
    ) -> None:
        repo = KnowledgeGraphRepository(neo4j_connection)
        records = repo.execute_read_query(
            "RETURN $value AS val",
            {"value": 42},
        )
        assert records[0]["val"] == 42

    def test_invalid_label_raises(
        self, neo4j_connection: Neo4jConnection,
    ) -> None:
        repo = KnowledgeGraphRepository(neo4j_connection)
        with pytest.raises(ValueError, match="not a recognized"):
            repo.find_entities_by_label("FakeLabel")


@pytest.mark.integration
class TestRepositoryBatch:
    """Batch operations against a live Neo4j instance."""

    def test_batch_upsert_chunks(
        self, neo4j_connection: Neo4jConnection,
    ) -> None:
        repo = KnowledgeGraphRepository(neo4j_connection)

        chunks = [
            {
                "id": f"CHUNK-BATCH-{i:03d}",
                "text": f"Batch test chunk {i}.",
                "page": 1,
                "chunk_index": i,
                "source_path": "/tmp/test.pdf",
                "document_id": "DOC-BATCH-001",
            }
            for i in range(5)
        ]
        count = repo.batch_upsert_chunks(chunks)
        assert count == 5

    def test_batch_empty_is_noop(
        self, neo4j_connection: Neo4jConnection,
    ) -> None:
        repo = KnowledgeGraphRepository(neo4j_connection)
        count = repo.batch_upsert_chunks([])
        assert count == 0

    def test_batch_link_document_chunks(
        self, neo4j_connection: Neo4jConnection,
    ) -> None:
        repo = KnowledgeGraphRepository(neo4j_connection)

        # Create document and chunks first
        repo.upsert_document(
            node_id="DOC-BATCH-LINK-001",
            title="Batch Link Test",
            source="/tmp/test.pdf",
            document_type="report",
            publication_date=None,
        )

        chunks = [
            {
                "id": f"CHUNK-BLINK-{i:03d}",
                "text": f"Chunk {i}.",
                "page": 1,
                "chunk_index": i,
                "source_path": "/tmp/test.pdf",
                "document_id": "DOC-BATCH-LINK-001",
            }
            for i in range(3)
        ]
        repo.batch_upsert_chunks(chunks)

        links = [
            {"document_id": "DOC-BATCH-LINK-001", "chunk_id": c["id"]}
            for c in chunks
        ]
        count = repo.batch_link_document_chunks(links)
        assert count == 3
