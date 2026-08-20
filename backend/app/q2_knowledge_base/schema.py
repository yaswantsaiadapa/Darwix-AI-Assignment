"""
Q2 Knowledge Base Schema Definitions
Defines structured data contracts for knowledge ingestion, PII auditing, vector indexing, and grounded retrieval.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class KnowledgeRecord(BaseModel):
    """
    Standardized Knowledge Base Record Contract.
    Conforms to enterprise RAG & audit requirements.
    """
    record_id: str = Field(..., description="Unique deterministic identifier (e.g. kb_sme_underwriting_001)")
    title: str = Field(..., description="Canonical section title")
    content: str = Field(..., description="Sanitized, chunked textual content")
    category: str = Field(..., description="Taxonomy classification (e.g. policy, product, qualification, objection, faq)")
    source: str = Field(..., description="Provenance document path or web URL")
    version: str = Field(default="1.0", description="Semantic policy version")
    has_pii: bool = Field(default=False, description="Flag indicating if source originally contained PII")
    pii_types_redacted: List[str] = Field(default_factory=list, description="List of redacted PII categories (e.g. SSN, Phone, Email)")
    chunk_index: int = Field(default=0, description="Sequential chunk offset within the source document")
    parent_doc: str = Field(default="", description="Original source document name")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional domain metadata (e.g. min_credit_score, max_loan_limit)")
    last_updated: str = Field(default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%d %H:%M:%SZ"))


class Citation(BaseModel):
    """
    Structured provenance citation returned with grounded answers.
    """
    record_id: str
    title: str
    category: str
    source: str
    version: str
    confidence_score: float


class RetrievalResult(BaseModel):
    """
    Hybrid Search Retrieval Result with confidence metrics and citation.
    """
    record: KnowledgeRecord
    score: float = Field(..., description="Normalized hybrid similarity score [0.0 - 1.0]")
    dense_score: float = Field(default=0.0, description="FAISS cosine similarity score")
    sparse_score: float = Field(default=0.0, description="BM25 normalized keyword score")
    citation: Citation


class RetrievalQueryEvaluation(BaseModel):
    """
    Evaluation benchmark record for retrieval testing.
    """
    query_id: str
    question: str
    query_type: str = Field(..., description="product | policy | qualification | objection | out_of_scope")
    retrieved_chunk: Optional[str] = None
    source_reference: Optional[str] = None
    record_id: Optional[str] = None
    similarity_score: float = 0.0
    relevance_explanation: str
    verdict: str = Field(..., description="correct | partially_correct | incorrect | safely_rejected")
