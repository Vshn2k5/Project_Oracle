"""
Unit tests for retrieval modules.
"""

from src.retrieval.fusion import ResultFusionEngine
from src.retrieval.query_analyzer import QueryAnalyzer


class TestQueryAnalyzer:
    def test_normalize_and_keywords(self):
        analyzer = QueryAnalyzer()
        analysis = analyzer.analyze("What infrastructure is vulnerable to flooding in Zone A?")
        
        assert analysis.original_query == "What infrastructure is vulnerable to flooding in Zone A?"
        assert analysis.normalized_query == "what infrastructure is vulnerable to flooding in zone a"
        
        # 'what', 'is', 'to', 'in', 'a' are stopwords or < 3 chars
        assert "infrastructure" in analysis.keywords
        assert "vulnerable" in analysis.keywords
        assert "flooding" in analysis.keywords
        assert "zone" in analysis.keywords

    def test_intent_matching(self):
        analyzer = QueryAnalyzer()
        analysis1 = analyzer.analyze("What infrastructure is vulnerable?")
        assert analysis1.retrieval_intent in ["infrastructure", "risk"]
        
        analysis2 = analyzer.analyze("Show me the budget for mitigation.")
        # 'budget' and 'mitigation' are both intents. Depending on order/count, it will pick one.
        assert analysis2.retrieval_intent in ["budget", "mitigation"]
        
        analysis3 = analyzer.analyze("Unknown intent completely.")
        assert analysis3.retrieval_intent == "general"

    def test_entity_extraction(self):
        analyzer = QueryAnalyzer(known_entities={"Zone A", "Pump Station"})
        analysis = analyzer.analyze("Is Zone A safe?")
        assert "zone a" in analysis.entities


class TestFusionEngine:
    def test_min_max_normalization_standard(self):
        engine = ResultFusionEngine(0.5, 0.2, 0.3)
        results = [
            {"chunk_id": "C1", "raw_score": 0.5},
            {"chunk_id": "C2", "raw_score": 1.0},
            {"chunk_id": "C3", "raw_score": 0.0},
        ]
        
        engine._normalize_scores(results, "raw_score")
        
        # C1 -> (0.5 - 0) / (1 - 0) = 0.5
        assert results[0]["normalized_score"] == 0.5
        # C2 -> (1.0 - 0) / (1 - 0) = 1.0
        assert results[1]["normalized_score"] == 1.0
        # C3 -> (0.0 - 0) / (1 - 0) = 0.0
        assert results[2]["normalized_score"] == 0.0

    def test_min_max_normalization_fallback_zero_variance(self):
        engine = ResultFusionEngine(0.5, 0.2, 0.3)
        results = [
            {"chunk_id": "C1", "raw_score": 0.8},
            {"chunk_id": "C2", "raw_score": 0.8},
        ]
        
        engine._normalize_scores(results, "raw_score")
        
        # Since max == min, it should fallback to 1.0
        assert results[0]["normalized_score"] == 1.0
        assert results[1]["normalized_score"] == 1.0

    def test_fuse_deduplication_and_weighting(self):
        engine = ResultFusionEngine(vector_weight=0.5, keyword_weight=0.2, graph_weight=0.3)
        
        vector_results = [
            {"chunk_id": "C1", "raw_score": 0.8, "text": "T1", "page_number": 1, "document_id": "D1", "source_path": "P1"},
        ]
        keyword_results = [
            {"chunk_id": "C1", "raw_score": 0.5, "text": "T1", "page_number": 1, "document_id": "D1", "source_path": "P1"},
            {"chunk_id": "C2", "raw_score": 0.9, "text": "T2", "page_number": 2, "document_id": "D1", "source_path": "P1"},
        ]
        graph_results = [
            {"chunk_id": "C1", "raw_score": 1.0, "text": "T1", "page_number": 1, "document_id": "D1", "source_path": "P1"},
        ]
        
        fused = engine.fuse(vector_results, keyword_results, graph_results, top_k=5)
        
        assert len(fused) == 2
        
        # Find C1
        c1 = next(c for c in fused if c.chunk_id == "C1")
        assert "vector" in c1.retrieval_sources
        assert "keyword" in c1.retrieval_sources
        assert "graph" in c1.retrieval_sources
        
        # Check normalization
        assert c1.vector_score_normalized == 1.0  # Zero variance fallback
        assert c1.graph_score_normalized == 1.0   # Zero variance fallback
        # Keyword normalization for C1: (0.5 - 0.5)/(0.9-0.5) = 0.0
        assert c1.keyword_score_normalized == 0.0
        
        # Final score C1 = (1.0 * 0.5) + (0.0 * 0.2) + (1.0 * 0.3) = 0.8
        assert c1.final_score == 0.8
        
        # Find C2
        c2 = next(c for c in fused if c.chunk_id == "C2")
        assert "keyword" in c2.retrieval_sources
        assert "vector" not in c2.retrieval_sources
        assert c2.vector_score_normalized == 0.0
        assert c2.keyword_score_normalized == 1.0
        assert c2.final_score == (1.0 * 0.2) == 0.2
        
        # Sorting
        assert fused[0].chunk_id == "C1"
        assert fused[1].chunk_id == "C2"
