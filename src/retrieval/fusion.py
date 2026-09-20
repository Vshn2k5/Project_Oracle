"""
Result Fusion Engine for Project Oracle.
"""

import logging
from collections import defaultdict
from typing import Any

from src.models.retrieval import RetrievedChunk

logger = logging.getLogger(__name__)


class ResultFusionEngine:
    """
    Normalizes scores from different retrievers and fuses them.
    """

    def __init__(self, vector_weight: float, keyword_weight: float, graph_weight: float):
        self.weights = {
            "vector": vector_weight,
            "keyword": keyword_weight,
            "graph": graph_weight,
        }

    def _normalize_scores(self, results: list[dict[str, Any]], score_key: str) -> None:
        """
        Robust min-max normalization in-place.
        Adds 'normalized_score' to each result.
        If all scores are identical, falls back to rank-based or constant score.
        """
        if not results:
            return

        scores = [r[score_key] for r in results]
        min_score = min(scores)
        max_score = max(scores)

        if max_score == min_score:
            # Fallback: all results have the same score.
            # Assign a sensible constant (e.g. 1.0 if score > 0 else 0.0)
            fallback = 1.0 if max_score > 0 else 0.0
            for r in results:
                r["normalized_score"] = fallback
            return

        # Min-max normalization
        for r in results:
            r["normalized_score"] = (r[score_key] - min_score) / (max_score - min_score)

    def fuse(
        self,
        vector_results: list[dict[str, Any]],
        keyword_results: list[dict[str, Any]],
        graph_results: list[dict[str, Any]],
        top_k: int = 10,
    ) -> list[RetrievedChunk]:
        """
        Normalize, fuse, and deduplicate results.
        """
        self._normalize_scores(vector_results, "raw_score")
        self._normalize_scores(keyword_results, "raw_score")
        self._normalize_scores(graph_results, "raw_score")

        # Deduplicate chunks
        # Map: chunk_id -> dict of properties
        fused_map: dict[str, dict[str, Any]] = defaultdict(lambda: {
            "vector_score_raw": 0.0,
            "keyword_score_raw": 0.0,
            "graph_score_raw": 0.0,
            "vector_score_normalized": 0.0,
            "keyword_score_normalized": 0.0,
            "graph_score_normalized": 0.0,
            "retrieval_sources": set(),
        })

        def _merge_results(results_list: list[dict[str, Any]], source: str):
            for r in results_list:
                cid = r["chunk_id"]
                fm = fused_map[cid]
                # Preserve metadata from first encounter
                if "text" not in fm:
                    fm["text"] = r["text"]
                    fm["page_number"] = r["page_number"]
                    fm["document_id"] = r["document_id"]
                    fm["source_path"] = r["source_path"]

                fm[f"{source}_score_raw"] = r["raw_score"]
                fm[f"{source}_score_normalized"] = r["normalized_score"]
                fm["retrieval_sources"].add(source)

        _merge_results(vector_results, "vector")
        _merge_results(keyword_results, "keyword")
        _merge_results(graph_results, "graph")

        # Compute final scores and build models
        final_chunks = []
        for cid, fm in fused_map.items():
            final_score = (
                (fm["vector_score_normalized"] * self.weights["vector"]) +
                (fm["keyword_score_normalized"] * self.weights["keyword"]) +
                (fm["graph_score_normalized"] * self.weights["graph"])
            )
            
            final_chunks.append(
                RetrievedChunk(
                    chunk_id=cid,
                    text=fm["text"],
                    page_number=fm["page_number"],
                    document_id=fm["document_id"],
                    source_path=fm["source_path"],
                    vector_score_raw=fm["vector_score_raw"],
                    keyword_score_raw=fm["keyword_score_raw"],
                    graph_score_raw=fm["graph_score_raw"],
                    vector_score_normalized=fm["vector_score_normalized"],
                    keyword_score_normalized=fm["keyword_score_normalized"],
                    graph_score_normalized=fm["graph_score_normalized"],
                    final_score=final_score,
                    retrieval_sources=tuple(sorted(fm["retrieval_sources"])),
                )
            )

        # Sort by final score descending
        final_chunks.sort(key=lambda c: c.final_score, reverse=True)
        return final_chunks[:top_k]
