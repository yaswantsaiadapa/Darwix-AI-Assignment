"""
Question 2 Parsers Package
Provides multi-format document extractors for PDF, HTML, CSV, and Text.
"""

from backend.app.q2_knowledge_base.parsers.universal_parser import UniversalDocumentParser
from backend.app.q2_knowledge_base.parsers.pdf_parser import PDFParser
from backend.app.q2_knowledge_base.parsers.html_parser import HTMLParser
from backend.app.q2_knowledge_base.parsers.csv_table_parser import CSVTableParser

__all__ = [
    "UniversalDocumentParser",
    "PDFParser",
    "HTMLParser",
    "CSVTableParser",
]
