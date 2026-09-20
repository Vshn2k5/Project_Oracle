"""
Deterministic Query Analyzer for Project Oracle.
"""

import re
from typing import Set

from src.models.retrieval import QueryAnalysis


class QueryAnalyzer:
    """
    Parses a user query deterministically to extract keywords,
    identify intents, and recognize known entities.
    """

    # Basic English stopwords for naive keyword extraction
    STOPWORDS = {
        "what", "which", "where", "how", "who", "when", "why",
        "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did",
        "a", "an", "the", "and", "or", "but", "if", "because",
        "in", "on", "at", "to", "from", "by", "for", "with",
        "about", "against", "between", "into", "through",
        "during", "before", "after", "above", "below", "to",
        "of", "that", "this", "these", "those", "it", "its",
        "they", "them", "their", "he", "him", "his", "she", "her",
        "can", "could", "should", "would", "may", "might", "must",
        "i", "you", "we", "my", "your", "our",
    }

    # Intent heuristics mapped to Oracle Query Workload v1
    INTENT_KEYWORDS = {
        "risk": {"risk", "exposed", "exposure", "hazard", "vulnerable", "severity"},
        "infrastructure": {"infrastructure", "asset", "pump", "drainage", "canal", "road", "bridge", "station"},
        "mitigation": {"mitigation", "measure", "reduce", "prevent", "improve", "improvement"},
        "budget": {"budget", "funding", "fund", "cost", "allocation", "approved"},
        "policy": {"policy", "regulate", "requirement", "rule", "law", "compliance"},
        "provenance": {"evidence", "support", "recommendation", "originate", "source", "document", "where"},
    }

    def __init__(self, known_entities: Set[str] | None = None):
        """
        Args:
            known_entities: A set of exact normalized entity names from the graph,
                            used for naive entity recognition.
        """
        self.known_entities = {e.lower() for e in (known_entities or [])}

    def analyze(self, query: str) -> QueryAnalysis:
        """
        Analyze the query and return structured QueryAnalysis.
        """
        normalized_query = self._normalize(query)
        keywords = self._extract_keywords(normalized_query)
        entities = self._extract_entities(normalized_query)
        intent = self._determine_intent(keywords)

        return QueryAnalysis(
            original_query=query,
            normalized_query=normalized_query,
            query_type="natural_language",
            entities=tuple(entities),
            keywords=tuple(keywords),
            retrieval_intent=intent,
        )

    def _normalize(self, text: str) -> str:
        text = text.lower()
        # Remove punctuation except alphanumeric and spaces
        text = re.sub(r"[^\w\s]", "", text)
        return re.sub(r"\s+", " ", text).strip()

    def _extract_keywords(self, normalized_query: str) -> list[str]:
        words = normalized_query.split()
        keywords = [w for w in words if w not in self.STOPWORDS and len(w) > 2]
        return keywords

    def _extract_entities(self, normalized_query: str) -> list[str]:
        # Naive substring matching against known entities.
        # This will be sufficient for Stage 3 deterministic matching.
        found = set()
        if self.known_entities:
            for entity in self.known_entities:
                if entity in normalized_query:
                    found.add(entity)
        
        # If no known_entities provided, we might try to guess based on capitalized words in the original query,
        # but the safest approach is to return an empty list and rely on keyword search.
        return list(found)

    def _determine_intent(self, keywords: list[str]) -> str:
        intent_scores = {intent: 0 for intent in self.INTENT_KEYWORDS}
        
        for word in keywords:
            for intent, intent_words in self.INTENT_KEYWORDS.items():
                if word in intent_words:
                    intent_scores[intent] += 1
                    
        # Find max score
        max_intent = max(intent_scores, key=intent_scores.get)
        
        if intent_scores[max_intent] > 0:
            return max_intent
            
        return "general"
