"""
Universal Adaptive Recursive Hierarchical Chunker & Schema Formatter
Converts multi-format business documents (PDF, HTML, CSV, TXT, MD, Tables)
into structured, traceable, PII-scrubbed KnowledgeRecord objects conforming to the Q2 schema.
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Any, Union, Optional
from backend.app.q2_knowledge_base.schema import KnowledgeRecord
from backend.app.q2_knowledge_base.pii_redactor import PIIRedactor
from backend.app.q2_knowledge_base.cleaner import DocumentCleaner
from backend.app.q2_knowledge_base.parsers.universal_parser import UniversalDocumentParser


class MarkdownChunker:
    """
    Splits multi-format documents using Universal Recursive Hierarchical Chunking (300-500 chars, 50 char overlap)
    with natural header preservation and metadata attachment.
    """

    def __init__(self, target_chunk_size: int = 450, overlap: int = 50):
        self.target_chunk_size = target_chunk_size
        self.overlap = overlap

    @staticmethod
    def extract_document_title(raw_text: str, default_name: str = "Commercial Banking Policy") -> str:
        """Extracts the top-level # title or defaults to filename."""
        match = re.search(r"^#\s+(.+)$", raw_text, re.MULTILINE)
        return match.group(1).strip() if match else default_name

    @staticmethod
    def infer_category(title: str, content: str) -> str:
        """Categorizes chunk based on domain taxonomy and terminology."""
        text = (title + " " + content).lower()
        if "customercare" in text or "customer service" in text or "helpline" in text or "grievance" in text:
            return "customer_service_and_support"
        elif "eligib" in text or "requirement" in text or "qualif" in text or "vintage" in text or "turnover" in text:
            return "qualification_rules"
        elif "rate" in text or "fee" in text or "apr" in text or "eblr" in text or "spread" in text or "pricing" in text or "penal" in text:
            return "pricing_and_fees"
        elif "cgtmse" in text or "guarantee" in text or "collateral" in text or "security" in text or "hypothecation" in text:
            return "collateral_and_guarantee"
        elif "lap" in text or "property" in text or "machinery" in text or "equipment" in text:
            return "secured_assets_and_lap"
        elif "growth loan" in text or "unsecured" in text or "mudra" in text or "working capital" in text or "cash credit" in text or "personal loan" in text:
            return "commercial_loan_products"
        elif "apply" in text or "document" in text or "kyc" in text or "itr" in text or "gst" in text or "timeline" in text:
            return "application_and_kyc"
        elif "prohibit" in text or "crypto" in text or "speculat" in text or "lottery" in text or "ineligible" in text:
            return "prohibitions_and_exceptions"
        elif "pay back" in text or "repay" in text or "prepay" in text or "tenor" in text or "tenure" in text:
            return "repayment_and_servicing"
        return "general_policy"

    def recursive_split_text(self, text: str) -> List[str]:
        """
        Recursive Hierarchical Separator Fallback (Industry Standard):
        Level 1: Double newlines \n\n or markdown headings (#, ##, ###)
        Level 2: Titled clauses & section headers (e.g. '14. TIMELINE...', 'Customer Service:', 'Eligibility:')
        Level 3: Sentence boundaries (. , ? , ! , • )
        Level 4: Word spaces
        """
        # Step 1: Initial coarse split on major sections and titled headers
        # Matches: ## Headings, 1. NUMBERED HEADINGS:, or Title Case Headings with colon (e.g. Customer Service:)
        header_split_regex = re.compile(
            r"(?=(?:^|\n)(?:#{1,3}\s+|[0-9]{1,2}[\.\)]\s+[A-Z\s]{2,}:?|[A-Z][A-Za-z\s]{2,30}:\s*(?:\n|$)))",
            re.MULTILINE,
        )
        coarse_sections = [s.strip() for s in header_split_regex.split(text) if s.strip()]

        final_chunks: List[str] = []

        for sec in coarse_sections:
            if len(sec) <= self.target_chunk_size:
                if len(sec) > 20:  # Skip trivial fragments
                    final_chunks.append(sec)
                continue

            # Step 2: Split large sections by paragraphs
            paragraphs = [p.strip() for p in sec.split("\n\n") if p.strip()]
            buffer = ""
            for p in paragraphs:
                if len(buffer) + len(p) <= self.target_chunk_size:
                    buffer += ("\n\n" if buffer else "") + p
                else:
                    if buffer:
                        final_chunks.append(buffer)
                    # If paragraph itself exceeds target size, split by sentences/bullets
                    if len(p) > self.target_chunk_size:
                        sentences = re.split(r"(?<=[.?!•])\s+", p)
                        s_buf = ""
                        for s in sentences:
                            if len(s_buf) + len(s) <= self.target_chunk_size:
                                s_buf += (" " if s_buf else "") + s
                            else:
                                if s_buf:
                                    final_chunks.append(s_buf)
                                s_buf = s
                        buffer = s_buf
                    else:
                        buffer = p
            if buffer and len(buffer) > 20:
                final_chunks.append(buffer)

        return final_chunks

    def chunk_parsed_content(
        self,
        content_text: str,
        source_filename: str,
        version: str = "1.0",
        doc_metadata: Dict[str, Any] = None,
    ) -> List[KnowledgeRecord]:
        """
        Takes raw extracted text from any document parser, cleans it, splits it via
        Universal Recursive Hierarchical Chunking, scrubs PII, and returns standardized KnowledgeRecord objects.
        """
        cleaned_text = DocumentCleaner.clean_text(content_text)
        doc_title = self.extract_document_title(cleaned_text, default_name=Path(source_filename).stem.replace("_", " ").title())

        # Split into semantic adaptive chunks
        raw_chunks = self.recursive_split_text(cleaned_text)

        # Deduplicate near-duplicate sections
        unique_sections = DocumentCleaner.deduplicate_chunks(raw_chunks, similarity_threshold=0.85)

        records: List[KnowledgeRecord] = []
        doc_prefix = Path(source_filename).stem.replace("-", "_").replace(" ", "_").lower()

        for idx, sec in enumerate(unique_sections):
            # Extract clean title from header line
            first_line = sec.split("\n")[0].strip("# ").strip()
            title = first_line if first_line and len(first_line) < 100 else f"{doc_title} - Part {idx + 1}"

            # Run Relaxed, Context-Aware PII Redaction
            sanitized_content, has_pii, pii_types = PIIRedactor.redact(sec)
            category = self.infer_category(title, sanitized_content)

            record_id = f"kb_{doc_prefix}_{idx+1:03d}"

            meta = {
                "doc_title": doc_title,
                "source_file": source_filename,
                "char_count": len(sanitized_content),
                "section_index": idx + 1,
            }
            if doc_metadata:
                meta.update(doc_metadata)

            record = KnowledgeRecord(
                record_id=record_id,
                title=title,
                content=sanitized_content,
                category=category,
                source=source_filename,
                version=version,
                has_pii=has_pii,
                pii_types_redacted=pii_types,
                chunk_index=idx + 1,
                parent_doc=source_filename,
                metadata=meta,
            )
            records.append(record)

        return records

    def process_file(self, file_path: Path, version: str = "1.0") -> List[KnowledgeRecord]:
        """
        End-to-end ingestion pipeline: Parses file of any format (PDF, HTML, CSV, TXT, MD),
        cleans noise, splits hierarchically, and returns Q2 KnowledgeRecords.
        """
        parsed_doc = UniversalDocumentParser.parse_file(file_path)
        return self.chunk_parsed_content(
            content_text=parsed_doc.get("content", ""),
            source_filename=parsed_doc.get("filename", file_path.name),
            version=version,
            doc_metadata=parsed_doc,
        )

    def process_directory(
        self,
        directory_path: Union[str, Path],
        output_json: Optional[Union[str, Path]] = None,
        version: str = "1.0",
    ) -> List[KnowledgeRecord]:
        """Processes all documents in a directory and saves cleaned knowledge records to JSON."""
        dir_p = Path(directory_path)
        all_records: List[KnowledgeRecord] = []
        for file_path in dir_p.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in [".pdf", ".html", ".htm", ".csv", ".tsv", ".txt", ".md", ".json"]:
                try:
                    recs = self.process_file(file_path, version=version)
                    all_records.extend(recs)
                except Exception as e:
                    print(f"[MarkdownChunker Warning] Failed to process {file_path.name}: {e}")

        if output_json:
            out_p = Path(output_json)
            out_p.parent.mkdir(parents=True, exist_ok=True)
            with open(out_p, "w", encoding="utf-8") as f:
                json.dump([r.model_dump() for r in all_records], f, indent=2, ensure_ascii=False)

        return all_records
