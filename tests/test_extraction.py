"""
Unit tests for the extraction pipeline.
"""

from typing import Type

from src.extraction.llm import LLMProvider
from src.extraction.pipeline import ExtractionPipeline
from src.extraction.schemas import (
    DocumentExtractionSchema,
    ExtractedClaimSchema,
    ExtractedEntitySchema,
    ExtractedRelationshipSchema,
)
from src.models.document import DocumentChunk


class DummyLLMProvider(LLMProvider):
    def __init__(self, mock_response: DocumentExtractionSchema):
        self.mock_response = mock_response

    def extract_structured_data(self, text: str, schema: Type) -> DocumentExtractionSchema:
        return self.mock_response


class TestExtractionPipelineUnit:
    def test_entity_resolution_and_validation(self):
        mock_response = DocumentExtractionSchema(
            entities=[
                ExtractedEntitySchema(
                    name="  Ernakulam  ",
                    entity_type="Zone",
                    properties={"type": "District"},
                    confidence=0.9
                ),
                ExtractedEntitySchema(
                    name="ERNAKULAM",
                    entity_type="Zone",
                    properties={"type": "District"},
                    confidence=0.9
                ),
            ],
            relationships=[],
            claims=[],
        )
        llm = DummyLLMProvider(mock_response)
        pipeline = ExtractionPipeline(llm)
        chunk = DocumentChunk("C1", "Ernakulam is a district.", 1, 0, "path", "D1")
        
        result = pipeline.extract_from_chunk(chunk)
        
        # Should deduplicate Ernakulam
        assert len(result["entities"]) == 1
        assert result["entities"][0].name == "ernakulam"
        assert result["entities"][0].label == "Zone"

    def test_relationship_validation_missing_endpoint(self):
        mock_response = DocumentExtractionSchema(
            entities=[
                ExtractedEntitySchema(
                    name="Zone A",
                    entity_type="Zone",
                    properties={},
                    confidence=0.9
                ),
            ],
            relationships=[
                ExtractedRelationshipSchema(
                    source_entity="Zone A",
                    relationship_type="HAS_RISK",
                    target_entity="Missing Risk",
                    evidence_quote="High risk",
                    confidence=0.9
                )
            ],
            claims=[],
        )
        llm = DummyLLMProvider(mock_response)
        pipeline = ExtractionPipeline(llm)
        chunk = DocumentChunk("C1", "Zone A has High risk.", 1, 0, "path", "D1")
        
        result = pipeline.extract_from_chunk(chunk)
        
        assert len(result["entities"]) == 1
        # Relationship should be dropped because target is missing
        assert len(result["relationships"]) == 0

    def test_claim_evidence_creation(self):
        mock_response = DocumentExtractionSchema(
            entities=[
                ExtractedEntitySchema(
                    name="Zone A",
                    entity_type="Zone",
                    properties={},
                    confidence=0.9
                ),
            ],
            relationships=[],
            claims=[
                ExtractedClaimSchema(
                    claim_text="Zone A is exposed to flood.",
                    subject_entity="Zone A",
                    evidence_quote="Zone A is exposed to flood.",
                    confidence=0.9
                )
            ],
        )
        llm = DummyLLMProvider(mock_response)
        pipeline = ExtractionPipeline(llm)
        chunk = DocumentChunk("C1", "Zone A is exposed to flood.", 1, 0, "path", "D1")
        
        result = pipeline.extract_from_chunk(chunk)
        
        assert len(result["claims"]) == 1
        assert len(result["evidence"]) == 1
        assert result["claims"][0].subject_entity_id == result["entities"][0].entity_id
        assert result["evidence"][0].claim_id == result["claims"][0].claim_id
        assert result["evidence"][0].chunk_id == "C1"
