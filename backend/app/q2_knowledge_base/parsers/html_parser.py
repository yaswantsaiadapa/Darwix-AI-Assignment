"""
HTML & Web Page Document Parser for Question 2 Knowledge Base
Strips navigation menus, header bars, footer noise, tracking scripts, and converts
HTML tables and form inputs into clean, structured Markdown.
"""

from pathlib import Path
from typing import Dict, Any
from bs4 import BeautifulSoup, Comment


class HTMLParser:
    """
    Parses web pages and HTML exports, stripping boilerplate and extracting clean content.
    """

    NOISE_TAGS = [
        "script", "style", "nav", "header", "footer", "aside", "noscript",
        "iframe", "svg", "button", "input", "select"
    ]

    NOISE_CLASSES_OR_IDS = [
        "navbar", "navigation", "nav-menu", "site-header", "site-footer",
        "cookie-banner", "advertisement", "ad-banner", "sidebar", "breadcrumb",
        "social-share", "popup", "modal", "footer-links"
    ]

    @classmethod
    def parse_html(cls, file_path: Path) -> Dict[str, Any]:
        """
        Reads an HTML file and returns clean Markdown-compatible structured text.
        """
        try:
            raw_html = file_path.read_text(encoding="utf-8", errors="ignore")
            soup = BeautifulSoup(raw_html, "html.parser")

            # 1. Remove HTML Comments
            for comment in soup.find_all(text=lambda text: isinstance(text, Comment)):
                comment.extract()

            # 2. Remove noise tags
            for tag_name in cls.NOISE_TAGS:
                for tag in soup.find_all(tag_name):
                    tag.decompose()

            # 3. Remove noise classes/ids
            for selector in cls.NOISE_CLASSES_OR_IDS:
                for match in soup.find_all(attrs={"class": lambda c: c and selector in c.lower()}):
                    match.decompose()
                for match in soup.find_all(attrs={"id": lambda i: i and selector in i.lower()}):
                    match.decompose()

            # 4. Convert HTML Tables to Markdown Tables
            for table in soup.find_all("table"):
                md_table = cls._table_to_markdown(table)
                table.replace_with(soup.new_string("\n\n" + md_table + "\n\n"))

            # 5. Extract structured text
            page_title = soup.title.string.strip() if soup.title and soup.title.string else file_path.stem.replace("_", " ").title()
            
            # Extract main content container if present, else entire body
            main_container = soup.find("main") or soup.find("article") or soup.find("body") or soup
            
            text_lines = []
            for elem in main_container.find_all(["h1", "h2", "h3", "h4", "p", "li", "div"]):
                text = elem.get_text(separator=" ", strip=True)
                if not text:
                    continue
                tag = elem.name
                if tag == "h1":
                    text_lines.append(f"\n# {text}\n")
                elif tag == "h2":
                    text_lines.append(f"\n## {text}\n")
                elif tag == "h3":
                    text_lines.append(f"\n### {text}\n")
                elif tag == "h4":
                    text_lines.append(f"\n#### {text}\n")
                elif tag == "li":
                    text_lines.append(f"- {text}")
                else:
                    # Avoid duplicated parent-child text
                    if len(text) > 20 and not any(text in existing for existing in text_lines[-3:]):
                        text_lines.append(text)

            cleaned_content = "\n\n".join(text_lines).strip()
            if not cleaned_content:
                cleaned_content = soup.get_text(separator="\n", strip=True)

            return {
                "success": True,
                "file_type": "html",
                "filename": file_path.name,
                "title": page_title,
                "content": f"# {page_title}\n\n{cleaned_content}",
                "error": None,
            }
        except Exception as e:
            return {
                "success": False,
                "file_type": "html",
                "filename": file_path.name,
                "title": file_path.name,
                "content": "",
                "error": f"HTML parsing error: {str(e)}",
            }

    @staticmethod
    def _table_to_markdown(table_tag) -> str:
        """Converts a BeautifulSoup <table> tag into a GitHub Markdown table."""
        rows = table_tag.find_all("tr")
        if not rows:
            return ""

        md_rows = []
        header_parsed = False

        for row in rows:
            headers = row.find_all("th")
            cells = row.find_all("td")
            
            if headers:
                cols = [h.get_text(strip=True).replace("\n", " ") for h in headers]
                md_rows.append("| " + " | ".join(cols) + " |")
                md_rows.append("| " + " | ".join(["---"] * len(cols)) + " |")
                header_parsed = True
            elif cells:
                cols = [c.get_text(strip=True).replace("\n", " ") for c in cells]
                if not header_parsed and len(md_rows) == 0:
                    # Treat first row as header if no <th>
                    md_rows.append("| " + " | ".join(cols) + " |")
                    md_rows.append("| " + " | ".join(["---"] * len(cols)) + " |")
                    header_parsed = True
                else:
                    md_rows.append("| " + " | ".join(cols) + " |")

        return "\n".join(md_rows)
