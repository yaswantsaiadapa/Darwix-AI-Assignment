"""
ETL Multi-Format Knowledge Base Pipeline Script
Processes multi-format documents (PDF, HTML, CSV, TXT, MD), performs PII redaction and deduplication,
chunks into structured records, and builds the FAISS & BM25 hybrid vector database.
"""

import sys
import argparse
from pathlib import Path

# Configure utf-8 stdout for Windows
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.q2_knowledge_base.chunker import MarkdownChunker
from backend.app.q2_knowledge_base.indexer import KnowledgeIndexer


def main():
    parser = argparse.ArgumentParser(description="Multi-Format Knowledge Base Ingestion Pipeline")
    parser.add_argument("--preset", choices=["default", "hdfc", "sbi", "all"], default="default", help="Dataset preset to ingest")
    parser.add_argument("--input-dir", type=str, default=None, help="Custom input directory with mixed documents")
    args = parser.parse_args()

    print("================================================================")
    print(f"[START] MULTI-FORMAT KNOWLEDGE BASE PIPELINE (Preset: {args.preset})")
    print("================================================================")

    if args.input_dir:
        input_dir = Path(args.input_dir)
    elif args.preset == "hdfc":
        input_dir = PROJECT_ROOT / "test_data_banks" / "hdfc"
    elif args.preset == "sbi":
        input_dir = PROJECT_ROOT / "test_data_banks" / "sbi"
    elif args.preset == "all":
        input_dir = PROJECT_ROOT / "data" / "default_knowledge"
    else:
        input_dir = PROJECT_ROOT / "data" / "default_knowledge"

    cleaned_json = PROJECT_ROOT / "data" / "cleaned_kb" / "knowledge_records.json"
    vector_dir = PROJECT_ROOT / "data" / "vector_db"

    print(f"\n[Step 1/2] Ingesting multi-format documents from: {input_dir}")
    chunker = MarkdownChunker()
    records = chunker.process_directory(input_dir, output_json=cleaned_json)
    print(f"  -> Generated {len(records)} structured knowledge records from {input_dir.name}.")
    print(f"  -> Clean records saved to: {cleaned_json}")

    # 2. Dense & Sparse Vector Indexing
    print("\n[Step 2/2] Generating embeddings and building FAISS + BM25 indices...")
    indexer = KnowledgeIndexer()
    indexer.build_indices(records)
    indexer.save_indices(vector_dir)

    print("\n[DONE] KNOWLEDGE BASE BUILT SUCCESSFULLY!")
    print(f"Total Chunks: {len(records)}")
    
    # Print sample taxonomy distribution
    categories = {}
    pii_counts = 0
    for r in records:
        categories[r.category] = categories.get(r.category, 0) + 1
        if r.has_pii:
            pii_counts += 1
    
    print("\nTaxonomy Breakdown:")
    for cat, count in categories.items():
        print(f"  - {cat}: {count} records")
    print(f"\nPII Redacted Chunks: {pii_counts}/{len(records)}")


if __name__ == "__main__":
    main()
