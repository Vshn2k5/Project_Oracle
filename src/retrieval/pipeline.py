"""
Hybrid Retrieval Pipeline for Project Oracle.
"""

import logging

from src.config.settings import Settings
from src.embeddings.embedder import create_embedder
from src.knowledge_graph.connection import Neo4jConnection
from src.models.retrieval import RetrievedContext

from .context_builder import ContextBuilder
from .fusion import ResultFusionEngine
from .graph_retriever import GraphRetriever
from .keyword_retriever import KeywordRetriever
from .query_analyzer import QueryAnalyzer
from .vector_retriever import VectorRetriever

logger = logging.getLogger(__name__)


class RetrievalPipeline:
    """
    Orchestrates the entire Hybrid Retrieval and GraphRAG Context Construction.
    """

    def __init__(self, connection: Neo4jConnection, settings: Settings):
        self._connection = connection
        self._settings = settings
        
        # Initialize sub-components
        # We don't have known_entities loaded globally yet, so we pass empty set.
        # In a production system, this could be cached and updated.
        self._analyzer = QueryAnalyzer()
        
        embedder = create_embedder(settings)
        self._vector_retriever = VectorRetriever(connection, embedder)
        self._keyword_retriever = KeywordRetriever(connection)
        self._graph_retriever = GraphRetriever(connection)
        
        self._fusion = ResultFusionEngine(
            vector_weight=settings.vector_weight,
            keyword_weight=settings.keyword_weight,
            graph_weight=settings.graph_weight,
        )
        
        self._context_builder = ContextBuilder(connection)

    def retrieve(self, query: str, top_k: int = 10) -> RetrievedContext:
        """
        Executes the hybrid retrieval pipeline.
        """
        logger.info("Starting retrieval for query: '%s'", query)
        
        # 1. Analyze
        analysis = self._analyzer.analyze(query)
        logger.debug("Query analysis: %s", analysis)
        
        # 2. Independent Retrievals
        # We fetch slightly more candidates than final top_k to allow fusion to rank them
        candidate_k = top_k * 2
        
        vector_results = self._vector_retriever.retrieve(analysis, top_k=candidate_k)
        keyword_results = self._keyword_retriever.retrieve(analysis, top_k=candidate_k)
        graph_results = self._graph_retriever.retrieve(analysis, top_k=candidate_k)
        
        # 3. Fusion
        fused_chunks = self._fusion.fuse(
            vector_results=vector_results,
            keyword_results=keyword_results,
            graph_results=graph_results,
            top_k=top_k,
        )
        
        # Handle empty retrieval
        if not fused_chunks:
            logger.info("No relevant chunks found for query.")
            return RetrievedContext(
                query=query,
                chunks=tuple(),
                entities=tuple(),
                relationships=tuple(),
                claims=tuple(),
                evidence=tuple(),
                sources=tuple(),
                retrieval_status="no_relevant_context",
            )
            
        # 4. Context Expansion
        graph_context = self._context_builder.build_context(fused_chunks)
        
        # 5. Build Final RetrievedContext
        return RetrievedContext(
            query=query,
            chunks=tuple(fused_chunks),
            entities=tuple(graph_context["entities"]),
            relationships=tuple(graph_context["relationships"]),
            claims=tuple(graph_context["claims"]),
            evidence=tuple(graph_context["evidence"]),
            sources=tuple(graph_context["sources"]),
            retrieval_status="success",
        )
