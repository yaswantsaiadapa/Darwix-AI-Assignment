"""
Universal Multi-Format Document Parser for Question 2 Knowledge Base
Dispatches parsing to dedicated engines (PDF, HTML, CSV, TXT, MD, JSON),
handles extraction failures, and produces uniform structured content for chunking.
"""

from pathlib import Path
from typing import Dict, Any
from backend.app.q2_knowledge_base.parsers.pdf_parser import PDFParser
from backend.app.q2_knowledge_base.parsers.html_parser import HTMLParser
from backend.app.q2_knowledge_base.parsers.csv_table_parser import CSVTableParser


class UniversalDocumentParser:
    """
    Unified entry point for ingesting any heterogeneous business document.
    """

    SUPPORTED_EXTENSIONS = {".pdf", ".html", ".htm", ".csv", ".tsv", ".txt", ".md", ".json"}

    @classmethod
    def parse_file(cls, file_path: Path) -> Dict[str, Any]:
        """
        Parses any supported file format and returns a normalized dictionary.
        """
        if not file_path.exists():
            return {
                "success": False,
                "file_type": "unknown",
                "filename": file_path.name,
                "content": "",
                "error": f"File does not exist: {file_path}",
            }

        suffix = file_path.suffix.lower()

        if suffix == ".pdf":
            return PDFParser.parse_pdf(file_path)

        elif suffix in {".html", ".htm"}:
            return HTMLParser.parse_html(file_path)

        elif suffix in {".csv", ".tsv"}:
            return CSVTableParser.parse_csv(file_path)

        elif suffix in {".txt", ".md"}:
            try:
                raw_text = file_path.read_text(encoding="utf-8", errors="ignore")
                title = file_path.stem.replace("_", " ").title()
                return {
                    "success": True,
                    "file_type": suffix.strip("."),
                    "filename": file_path.name,
                    "title": title,
                    "content": raw_text,
                    "error": None,
                }
            except Exception as e:
                return {
                    "success": False,
                    "file_type": suffix.strip("."),
                    "filename": file_path.name,
                    "content": "",
                    "error": f"Text reading error: {str(e)}",
                }

        elif suffix == ".json":
            try:
                raw_text = file_path.read_text(encoding="utf-8", errors="ignore")
                title = file_path.stem.replace("_", " ").title()
                return {
                    "success": True,
                    "file_type": "json",
                    "filename": file_path.name,
                    "title": title,
                    "content": f"# {title} (Structured JSON Export)\n\n```json\n{raw_text}\n```",
                    "error": None,
                }
            except Exception as e:
                return {
                    "success": False,
                    "file_type": "json",
                    "filename": file_path.name,
                    "content": "",
                    "error": f"JSON reading error: {str(e)}",
                }

        else:
            return {
                "success": False,
                "file_type": suffix,
                "filename": file_path.name,
                "content": "",
                "error": f"Unsupported file extension: {suffix}. Supported: {cls.SUPPORTED_EXTENSIONS}",
            }
