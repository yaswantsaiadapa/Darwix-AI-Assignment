"""
PDF Document Parser for Question 2 Knowledge Base
Extracts text page-by-page from PDF documents using pypdf, preserves section structure,
and handles extraction errors gracefully.
"""

from pathlib import Path
from typing import Dict, Any, List
import pypdf


class PDFParser:
    """
    Parses PDF policy manuals, circulars, and product sheets into structured text.
    """

    @staticmethod
    def parse_pdf(file_path: Path) -> Dict[str, Any]:
        """
        Reads a PDF file and extracts text per page with header metadata.
        
        Returns:
            Dict containing raw_text, page_count, pages (list), and metadata.
        """
        try:
            reader = pypdf.PdfReader(str(file_path))
            page_count = len(reader.pages)
            extracted_pages: List[Dict[str, Any]] = []
            full_text_parts: List[str] = []

            for idx, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                # Clean up null bytes or weird encoding
                clean_page_text = page_text.replace("\x00", "").strip()
                if clean_page_text:
                    extracted_pages.append({
                        "page_number": idx + 1,
                        "content": clean_page_text,
                    })
                    full_text_parts.append(f"<!-- Page {idx + 1} -->\n" + clean_page_text)

            combined_text = "\n\n".join(full_text_parts)
            return {
                "success": True,
                "file_type": "pdf",
                "filename": file_path.name,
                "page_count": page_count,
                "pages": extracted_pages,
                "content": combined_text,
                "error": None,
            }
        except Exception as e:
            return {
                "success": False,
                "file_type": "pdf",
                "filename": file_path.name,
                "page_count": 0,
                "pages": [],
                "content": "",
                "error": f"PDF parsing error: {str(e)}",
            }
