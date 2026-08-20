"""
CSV & Tabular Document Parser for Question 2 Knowledge Base
Converts tabular CSV / TSV datasets (interest rate cards, eligibility slabs, fee schedules)
into structured Markdown tables AND semantic row-level contextual text blocks.
"""

import csv
from pathlib import Path
from typing import Dict, Any, List


class CSVTableParser:
    """
    Parses CSV/TSV spreadsheets and converts them into semantically rich knowledge text.
    """

    @staticmethod
    def parse_csv(file_path: Path) -> Dict[str, Any]:
        """
        Reads a CSV or TSV file, infers columns, and produces structured markdown and row sentences.
        """
        try:
            content_str = file_path.read_text(encoding="utf-8", errors="ignore")
            dialect = csv.Sniffer().sniff(content_str[:2048]) if len(content_str) > 10 else csv.excel
        except Exception:
            dialect = csv.excel

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                reader = csv.reader(f, dialect=dialect)
                rows = [row for row in reader if any(cell.strip() for cell in row)]

            if not rows:
                return {
                    "success": False,
                    "file_type": "csv",
                    "filename": file_path.name,
                    "content": "",
                    "error": "Empty CSV file.",
                }

            headers = [h.strip() for h in rows[0]]
            data_rows = rows[1:]

            # 1. Build Markdown Table
            md_table_lines = [
                "| " + " | ".join(headers) + " |",
                "| " + " | ".join(["---"] * len(headers)) + " |",
            ]
            for r in data_rows:
                # Pad short rows
                padded = (r + [""] * len(headers))[:len(headers)]
                clean_cells = [c.strip().replace("\n", " ") for c in padded]
                md_table_lines.append("| " + " | ".join(clean_cells) + " |")

            md_table = "\n".join(md_table_lines)

            # 2. Build Semantic Row-Level Sentences for Vector Embeddings
            row_sentences: List[str] = []
            table_title = file_path.stem.replace("_", " ").title()

            for idx, r in enumerate(data_rows):
                padded = (r + [""] * len(headers))[:len(headers)]
                pairs = [f"{headers[i]}: {padded[i].strip()}" for i in range(len(headers)) if padded[i].strip()]
                sentence = f"Record {idx + 1} ({table_title}): " + ", ".join(pairs) + "."
                row_sentences.append(sentence)

            semantic_block = "\n".join([f"- {s}" for s in row_sentences])

            final_content = (
                f"# {table_title} (Tabular Reference)\n\n"
                f"## 1. Structured Rate & Criteria Matrix\n\n{md_table}\n\n"
                f"## 2. Policy Specifications by Row\n\n{semantic_block}\n"
            )

            return {
                "success": True,
                "file_type": "csv",
                "filename": file_path.name,
                "title": table_title,
                "row_count": len(data_rows),
                "headers": headers,
                "content": final_content,
                "error": None,
            }
        except Exception as e:
            return {
                "success": False,
                "file_type": "csv",
                "filename": file_path.name,
                "content": "",
                "error": f"CSV parsing error: {str(e)}",
            }
