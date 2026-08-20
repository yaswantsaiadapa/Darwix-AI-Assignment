"""
Data Cleaner, Terminology Standardizer & Deduplication Engine
Removes HTML/Markdown noise, headers, footers, normalizes disparate banking terminology,
standardizes dates, and deduplicates repeated policy clauses.
"""

import re
from typing import List, Set


class DocumentCleaner:
    """
    Cleans raw web scrapes, PDFs, and policy manuals by eliminating navigation noise,
    standardizing terminology/dates, normalizing whitespace, and filtering near-duplicate clauses.
    """

    NOISE_PATTERNS = [
        re.compile(r"<!--.*?-->", re.DOTALL),  # HTML Comments
        re.compile(r"BREADCRUMB:.*?\n", re.IGNORECASE),
        re.compile(r"BANNER AD:.*?\n", re.IGNORECASE),
        re.compile(r"NAVIGATION (?:MENU|LINKS):.*?\n", re.IGNORECASE),
        re.compile(r"WEBSITE (?:HEADER|FOOTER) START:.*?\n", re.IGNORECASE),
        re.compile(r"COOKIE (?:CONSENT|BANNER):.*?\n", re.IGNORECASE),
        re.compile(r"FOOTER NOISE:.*?\n", re.IGNORECASE),
        re.compile(r"^\s*[-=_*]{3,}\s*$", re.MULTILINE),  # Excessive horizontal rules
    ]

    # Terminology standardization mapping
    TERMINOLOGY_MAP = [
        (re.compile(r"\btenor\b", re.IGNORECASE), "tenure"),
        (re.compile(r"\bRoI\b", re.IGNORECASE), "interest rate"),
        (re.compile(r"\bRate of Int\.?\b", re.IGNORECASE), "interest rate"),
        (re.compile(r"\bLoan Quantum\b", re.IGNORECASE), "loan amount"),
        (re.compile(r"\bSanction Quantum\b", re.IGNORECASE), "sanctioned amount"),
        (re.compile(r"\bRepayment Periodicity\b", re.IGNORECASE), "repayment frequency"),
        (re.compile(r"\bA/C\b", re.IGNORECASE), "Account"),
        (re.compile(r"\bRs\.?\s*(\d+)", re.IGNORECASE), r"₹\1"),
        (re.compile(r"\bINR\s*(\d+)", re.IGNORECASE), r"₹\1"),
    ]

    @classmethod
    def standardize_terminology(cls, text: str) -> str:
        """Standardizes banking terms, currency symbols, and abbreviations."""
        standardized = text
        for pattern, replacement in cls.TERMINOLOGY_MAP:
            standardized = pattern.sub(replacement, standardized)
        return standardized

    @classmethod
    def clean_text(cls, text: str) -> str:
        """
        Strips boilerplate, applies terminology standardization, and standardizes line breaks.
        """
        cleaned = text
        for pattern in cls.NOISE_PATTERNS:
            cleaned = pattern.sub("\n", cleaned)

        # Standardize terms & currency
        cleaned = cls.standardize_terminology(cleaned)

        # Normalize multiple blank lines to a maximum of two
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned.strip()

    @staticmethod
    def compute_jaccard_similarity(text1: str, text2: str) -> float:
        """
        Calculates word-level Jaccard similarity between two candidate text blocks.
        """
        tokens1: Set[str] = set(re.findall(r"\w+", text1.lower()))
        tokens2: Set[str] = set(re.findall(r"\w+", text2.lower()))

        if not tokens1 or not tokens2:
            return 0.0

        intersection = len(tokens1.intersection(tokens2))
        union = len(tokens1.union(tokens2))
        return intersection / union if union > 0 else 0.0

    @classmethod
    def deduplicate_chunks(cls, chunks: List[str], similarity_threshold: float = 0.82) -> List[str]:
        """
        Filters out near-duplicate chunks based on Jaccard lexical overlap.
        Preserves the first occurrence.
        """
        unique_chunks: List[str] = []

        for candidate in chunks:
            if not candidate.strip():
                continue

            is_duplicate = False
            for existing in unique_chunks:
                sim = cls.compute_jaccard_similarity(candidate, existing)
                if sim >= similarity_threshold:
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique_chunks.append(candidate)

        return unique_chunks
