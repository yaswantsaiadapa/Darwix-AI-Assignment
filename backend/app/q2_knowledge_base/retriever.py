"""
Hybrid Retriever & Dual-Confidence Grounding Gate for Question 2 & Question 1
Executes dense vector (FAISS) + sparse keyword (BM25) search with blended scoring and anti-hallucination verification.
"""

from typing import List, Tuple, Optional
import numpy as np
from backend.app.q2_knowledge_base.indexer import KnowledgeIndexer
from backend.app.q2_knowledge_base.schema import KnowledgeRecord, RetrievalResult, Citation


class HybridRetriever:
    """
    Combines dense FAISS search (semantic similarity) and BM25 search (exact keyword match)
    with a dual-confidence grounding gate to prevent hallucinations while accurately accepting exact keyword matches.
    """

    def __init__(self, indexer: KnowledgeIndexer, dense_weight: float = 0.70, confidence_threshold: float = 0.50):
        self.indexer = indexer
        self.dense_weight = dense_weight
        self.sparse_weight = 1.0 - dense_weight
        self.confidence_threshold = confidence_threshold

    def search(self, query: str, top_k: int = 3) -> List[RetrievalResult]:
        """
        Executes hybrid retrieval over the knowledge base.
        """
        if not self.indexer.records or self.indexer.faiss_index is None:
            return []

        # 1. Dense Semantic Search (FAISS)
        query_np = self.indexer.encode_texts([query])

        dense_scores, dense_indices = self.indexer.faiss_index.search(query_np, min(top_k * 2, len(self.indexer.records)))
        
        dense_score_map = {}
        for idx, score in zip(dense_indices[0], dense_scores[0]):
            if idx >= 0:
                dense_score_map[idx] = float(score)

        # 2. Sparse Keyword Search (BM25)
        tokenized_query = query.lower().split()
        bm25_scores = self.indexer.bm25_index.get_scores(tokenized_query)
        max_bm25 = max(bm25_scores) if len(bm25_scores) > 0 and max(bm25_scores) > 0 else 1.0

        # 3. Hybrid Fusion & Normalization
        candidate_indices = set(dense_score_map.keys())
        top_bm25_indices = np.argsort(bm25_scores)[::-1][:top_k * 2]
        candidate_indices.update(top_bm25_indices)

        scored_results: List[RetrievalResult] = []

        for idx in candidate_indices:
            rec = self.indexer.records[idx]
            d_score = max(0.0, dense_score_map.get(idx, 0.0))
            raw_bm25 = max(0.0, float(bm25_scores[idx]))
            s_score = raw_bm25 / float(max_bm25) if max_bm25 > 0 else 0.0

            hybrid_score = (self.dense_weight * d_score) + (self.sparse_weight * s_score)

            citation = Citation(
                record_id=rec.record_id,
                title=rec.title,
                category=rec.category,
                source=rec.source,
                version=rec.version,
                confidence_score=round(hybrid_score, 4),
            )

            scored_results.append(
                RetrievalResult(
                    record=rec,
                    score=round(hybrid_score, 4),
                    dense_score=round(d_score, 4),
                    sparse_score=round(s_score, 4),
                    citation=citation,
                )
            )

        # Sort descending by hybrid score
        scored_results.sort(key=lambda x: x.score, reverse=True)
        return scored_results[:top_k]

    def grounded_retrieval(self, query: str, top_k: int = 3) -> Tuple[bool, List[RetrievalResult], str]:
        """
        Dual-Confidence Grounding Gate (Industry Standard):
        Evaluates whether the query is verified in the knowledge base using dual conditions:
        1. Strong Semantic Match: dense_score >= 0.50
        2. Strong Keyword Match with semantic grounding: sparse_score >= 0.75 and dense_score >= 0.20
        3. Solid Blended Hybrid Score: hybrid_score >= 0.48
        
        Returns:
            Tuple[is_supported (bool), results (List[RetrievalResult]), explanation (str)]
        """
        results = self.search(query, top_k=top_k)

        if not results:
            return False, [], "No knowledge chunks found in the active database."

        top_match = results[0]

        # Dual-Confidence Verification Gate
        is_supported = (
            (top_match.dense_score >= 0.50)
            or (top_match.sparse_score >= 0.75 and top_match.dense_score >= 0.20)
            or (top_match.score >= 0.48)
        )

        if not is_supported:
            return (
                False,
                results,
                f"Top similarity score ({top_match.score:.3f} | Dense: {top_match.dense_score:.3f}, BM25: {top_match.sparse_score:.3f}) is below threshold. Query is out-of-scope or unverified.",
            )

        return (
            True,
            results,
            f"Supported by {top_match.record.record_id} with confidence {top_match.score:.3f}.",
        )
