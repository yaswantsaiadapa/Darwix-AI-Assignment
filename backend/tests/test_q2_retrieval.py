"""
Question 2 — Formal Multi-Format Retrieval Benchmark Suite
Evaluates the Knowledge Base on:
1. Multi-Format Ingestion (PDF, HTML, CSV, TXT) & PII Redaction
2. 5 Required Query Classes:
   - Product query
   - Policy query
   - Qualification query
   - FAQ & Limitation query
   - Unsupported / Out-of-Scope query (safely rejected)
"""

import json
from pathlib import Path
import pytest
from backend.app.q2_knowledge_base.chunker import MarkdownChunker
from backend.app.q2_knowledge_base.indexer import KnowledgeIndexer
from backend.app.q2_knowledge_base.retriever import HybridRetriever
from backend.app.q2_knowledge_base.schema import RetrievalQueryEvaluation


@pytest.fixture(scope="module")
def project_dirs():
    project_root = Path(__file__).resolve().parent.parent.parent
    return {
        "root": project_root,
        "vector_dir": project_root / "data" / "vector_db",
        "hdfc_dir": project_root / "test_data_banks" / "hdfc",
        "sbi_dir": project_root / "test_data_banks" / "sbi",
        "default_dir": project_root / "data" / "default_knowledge",
    }


def test_multi_format_parsing_and_pii(project_dirs):
    """Validates that PDF, HTML, CSV, and TXT files parse cleanly and scrub PII."""
    chunker = MarkdownChunker()
    
    # Ingest HDFC dataset (PDF, CSV, HTML, TXT)
    records_hdfc = chunker.process_directory(project_dirs["hdfc_dir"])
    assert len(records_hdfc) > 0
    assert any(r.source.endswith(".pdf") for r in records_hdfc)
    assert any(r.source.endswith(".csv") for r in records_hdfc)
    assert any(r.source.endswith(".html") for r in records_hdfc)
    assert any(r.source.endswith(".txt") for r in records_hdfc)

    # Ingest SBI dataset (PDF, CSV, HTML, TXT)
    records_sbi = chunker.process_directory(project_dirs["sbi_dir"])
    assert len(records_sbi) > 0
    assert any(r.source.endswith(".pdf") for r in records_sbi)
    assert any(r.source.endswith(".csv") for r in records_sbi)

    # Verify PII was redacted from txt application forms
    pii_records = [r for r in records_hdfc + records_sbi if r.has_pii]
    assert len(pii_records) > 0
    for r in pii_records:
        assert len(r.pii_types_redacted) > 0
        assert "[REDACTED_" in r.content
        assert not any(ph in r.content for ph in ["9876543210", "9811223344"])  # Raw phone numbers redacted
    print(f"\n[Multi-Format Parser Test] -> PASSED ({len(records_hdfc)} HDFC chunks, {len(records_sbi)} SBI chunks, {len(pii_records)} PII scrubbed)")


def test_q2_retrieval_benchmarks(project_dirs):
    """
    Executes the 5 evaluation benchmark queries and validates verdicts and confidence scores.
    """
    # Index HDFC dataset for benchmark testing
    chunker = MarkdownChunker()
    records = chunker.process_directory(project_dirs["hdfc_dir"])
    indexer = KnowledgeIndexer()
    indexer.build_indices(records)
    indexer.save_indices(project_dirs["vector_dir"])
    retriever = HybridRetriever(indexer, dense_weight=0.70, confidence_threshold=0.55)

    test_queries = [
        {
            "query_id": "eval_q2_001",
            "type": "product",
            "question": "What is the maximum loan quantum and repayment tenure for HDFC Unsecured Business Growth Loans?",
            "expected_keywords": ["50", "lakh", "unsecured", "months"],
            "should_be_supported": True,
        },
        {
            "query_id": "eval_q2_002",
            "type": "policy",
            "question": "What is the maximum sanction limit and guarantee coverage under HDFC CGTMSE collateral-free loan scheme?",
            "expected_keywords": ["5 crore", "500", "guarantee", "cgtmse"],
            "should_be_supported": True,
        },
        {
            "query_id": "eval_q2_003",
            "type": "qualification",
            "question": "What are the eligibility criteria, minimum annual turnover, and business vintage required for HDFC business loans?",
            "expected_keywords": ["3 years", "40 lakh", "vintage", "turnover"],
            "should_be_supported": True,
        },
        {
            "query_id": "eval_q2_004",
            "type": "faq_and_objection",
            "question": "Can HDFC Cash Credit and Loan Against Property be used for purchasing raw materials and long-term commercial factory construction?",
            "expected_keywords": ["cash credit", "property", "commercial", "working capital"],
            "should_be_supported": True,
        },
        {
            "query_id": "eval_q2_005",
            "type": "unsupported_out_of_scope",
            "question": "Can I get a loan for personal online gaming tournament bets and lottery jackpots?",
            "expected_keywords": [],
            "should_be_supported": False,
        },
    ]

    evaluation_report = []

    for test_case in test_queries:
        q = test_case["question"]
        is_supported, results, explanation = retriever.grounded_retrieval(q, top_k=3)

        top_match = results[0] if results else None
        top_score = top_match.score if top_match else 0.0
        record_id = top_match.record.record_id if top_match else "N/A"
        source_ref = top_match.record.source if top_match else "N/A"
        content_snippet = top_match.record.content[:200] + "..." if top_match else "N/A"

        # Determine verdict
        if not test_case["should_be_supported"]:
            if not is_supported or top_score < 0.55:
                verdict = "safely_rejected"
            else:
                verdict = "incorrect (failed to reject out-of-scope query)"
        else:
            if is_supported:
                matched = any(kw.lower() in top_match.record.content.lower() for kw in test_case["expected_keywords"])
                verdict = "correct" if matched else "partially_correct"
            else:
                verdict = "incorrect (valid query falsely rejected)"

        eval_item = RetrievalQueryEvaluation(
            query_id=test_case["query_id"],
            question=q,
            query_type=test_case["type"],
            retrieved_chunk=content_snippet,
            source_reference=source_ref,
            record_id=record_id,
            similarity_score=top_score,
            relevance_explanation=explanation,
            verdict=verdict,
        )
        evaluation_report.append(eval_item.model_dump())

        print(f"\n[Query {test_case['query_id']} - {test_case['type'].upper()}]")
        print(f"  Q: {q}")
        print(f"  Top Record: {record_id} | Score: {top_score:.3f}")
        print(f"  Verdict: {verdict.upper()}")

        if test_case["should_be_supported"]:
            assert is_supported is True
            assert verdict in ["correct", "partially_correct"]
        else:
            assert verdict == "safely_rejected"

    # Save formal evaluation results to evaluation/q2_retrieval_report.json
    eval_dir = project_dirs["root"] / "evaluation"
    eval_dir.mkdir(parents=True, exist_ok=True)
    report_file = eval_dir / "q2_retrieval_report.json"

    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(evaluation_report, f, indent=2)

    print(f"\n[OK] Formal Q2 Evaluation Report saved to: {report_file}")
