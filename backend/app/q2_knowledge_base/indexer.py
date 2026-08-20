"""
FAISS Dense & BM25 Sparse Indexer
Builds and persists hybrid search indices from structured KnowledgeRecord objects.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Tuple
import numpy as np
import faiss
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
from backend.app.q2_knowledge_base.schema import KnowledgeRecord


class KnowledgeIndexer:
    """
    Manages vector embeddings (SentenceTransformers with resilient TF-IDF dense fallback) and sparse BM25 indexing.
    Provides persistence and fast in-memory hybrid search.
    """

    MODEL_NAME = "all-MiniLM-L6-v2"

    def __init__(self, embedding_model=None):
        self.model = None
        self.use_fallback = False
        self.fallback_vectorizer = None

        if embedding_model is not None:
            self.model = embedding_model
        else:
            try:
                print(f"[KnowledgeIndexer] Loading SentenceTransformer model: {self.MODEL_NAME}...", flush=True)
                self.model = SentenceTransformer(self.MODEL_NAME)
                print("[KnowledgeIndexer] SentenceTransformer loaded successfully.", flush=True)
            except Exception as e:
                print(f"[KnowledgeIndexer Warning] Could not load SentenceTransformer ({e}). Using dense TF-IDF vectorizer fallback.", flush=True)
                from sklearn.feature_extraction.text import TfidfVectorizer
                self.use_fallback = True
                self.fallback_vectorizer = TfidfVectorizer(max_features=384, stop_words="english")

        self.records: List[KnowledgeRecord] = []
        self.faiss_index: faiss.IndexFlatIP = None
        self.bm25_index: BM25Okapi = None
        self.tokenized_corpus: List[List[str]] = []

    def encode_texts(self, texts: List[str], is_fitting: bool = False) -> np.ndarray:
        """Encodes texts into normalized dense vectors."""
        if not self.use_fallback and self.model is not None:
            try:
                embeddings = self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
                return np.array(embeddings, dtype=np.float32)
            except Exception as e:
                print(f"[KnowledgeIndexer Warning] SentenceTransformer inference failed ({e}). Falling back to TF-IDF vectorizer.", flush=True)
                self.use_fallback = True

        from sklearn.feature_extraction.text import TfidfVectorizer
        if self.fallback_vectorizer is None or is_fitting:
            self.fallback_vectorizer = TfidfVectorizer(max_features=384, stop_words="english")
            matrix = self.fallback_vectorizer.fit_transform(texts).toarray()
        else:
            try:
                matrix = self.fallback_vectorizer.transform(texts).toarray()
            except Exception:
                matrix = self.fallback_vectorizer.fit_transform(texts).toarray()
        
        # L2 normalize vectors
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        normalized = matrix / norms
        # Pad if dimension < 384
        if normalized.shape[1] < 384:
            padding = np.zeros((normalized.shape[0], 384 - normalized.shape[1]), dtype=np.float32)
            normalized = np.hstack([normalized, padding])
        return normalized.astype(np.float32)

    def build_indices(self, records: List[KnowledgeRecord]):
        """
        Builds FAISS dense index and BM25 sparse index over knowledge records.
        """
        if not records:
            raise ValueError("No knowledge records provided to index.")

        self.records = records
        texts = [f"{rec.title}\n{rec.content}" for rec in records]

        # 1. Dense FAISS Embedding Index
        print(f"[KnowledgeIndexer] Computing embeddings for {len(records)} chunks...", flush=True)
        embeddings_np = self.encode_texts(texts, is_fitting=True)

        dimension = embeddings_np.shape[1]
        self.faiss_index = faiss.IndexFlatIP(dimension)
        self.faiss_index.add(embeddings_np)

        # 2. Sparse BM25 Keyword Index
        print("[KnowledgeIndexer] Building BM25 keyword index...", flush=True)
        self.tokenized_corpus = [rec.content.lower().split() for rec in records]
        self.bm25_index = BM25Okapi(self.tokenized_corpus)
        print(f"[KnowledgeIndexer] Hybrid index built successfully ({len(records)} records).", flush=True)

    def save_indices(self, output_dir: Path):
        """
        Serializes the FAISS index, records, and metadata to disk.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS
        faiss_file = output_dir / "faiss_index.bin"
        faiss.write_index(self.faiss_index, str(faiss_file))

        # Save records metadata
        records_file = output_dir / "kb_records.json"
        with open(records_file, "w", encoding="utf-8") as f:
            json.dump([rec.model_dump() for rec in self.records], f, indent=2)

        print(f"[KnowledgeIndexer] Indices saved to: {output_dir}")

    def load_indices(self, index_dir: Path):
        """
        Loads pre-built FAISS index and records from disk.
        """
        faiss_file = index_dir / "faiss_index.bin"
        records_file = index_dir / "kb_records.json"

        if not faiss_file.exists() or not records_file.exists():
            raise FileNotFoundError(f"Index files not found in {index_dir}")

        self.faiss_index = faiss.read_index(str(faiss_file))

        with open(records_file, "r", encoding="utf-8") as f:
            records_data = json.load(f)
            self.records = [KnowledgeRecord(**item) for item in records_data]

        # Rebuild BM25 in memory (instant)
        self.tokenized_corpus = [rec.content.lower().split() for rec in self.records]
        self.bm25_index = BM25Okapi(self.tokenized_corpus)
        print(f"[KnowledgeIndexer] Loaded {len(self.records)} records from {index_dir}")
