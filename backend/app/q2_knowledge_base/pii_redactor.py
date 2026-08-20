"""
PII Redaction & Sanitization Engine (Relaxed & Context-Aware)
Scans and redacts strict personal identifiers (Aadhaar, PAN, SSN, Credit Cards, Bank Accounts, Personal Mobile)
while protecting institutional terms (Bank Names, Customer Service, Grievance Cell, Toll-Free numbers, Support Emails).
"""

import re
from typing import Tuple, List, Dict


class PIIRedactor:
    """
    Relaxed, context-aware PII scrubber for enterprise financial documents.
    Safely redacts PAN, Aadhaar, SSN, credit cards, bank accounts, and individual customer phone numbers,
    while preserving institutional helpline directories, bank names, branch offices, and support emails.
    """

    STRICT_PATTERNS = {
        "AADHAAR": re.compile(r"\b[2-9]\d{3}[-\s]?\d{4}[-\s]?\d{4}\b"),
        "PAN": re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b"),
        "SSN": re.compile(r"\b(?!000|666|9\d{2})\d{3}-(?!00)\d{2}-(?!0000)\d{4}\b"),
        "TAX_ID": re.compile(r"\b\d{2}-\d{7}\b"),
        "CREDIT_CARD": re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"),
        "BANK_ACCOUNT": re.compile(r"(?:A/c|Account\s+No|Account\s+Number|Bank\s+Acc)[:\s]+(\d{9,18})\b", re.IGNORECASE),
        "PERSONAL_PHONE": re.compile(r"(?:Mobile|Cell|Personal\s+Phone|Applicant\s+Phone)[:\s]+(?:\+91[-\s]?|0)?[6-9]\d{9}\b", re.IGNORECASE),
        "PERSONAL_EMAIL": re.compile(r"\b[A-Za-z0-9._%+-]+@(?!sbi\.co\.in|hdfcbank\.com|icicibank\.com|axisbank\.com|bank\.com)[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", re.IGNORECASE),
    }

    # Protected terms that should NEVER be redacted as person names or noise
    INSTITUTIONAL_WHITELIST = {
        "customer service", "customer care", "help line", "grievance cell", "grievance redressal",
        "head office", "local head office", "department", "state bank of india", "sbi", "hdfc",
        "icici", "commercial bank", "branch manager", "nodal officer", "appellate authority",
        "personal loan", "business loan", "loan against property", "express credit",
    }

    @classmethod
    def redact(cls, text: str) -> Tuple[str, bool, List[str]]:
        """
        Scans input text for sensitive personal identifiers and redacts them.
        
        Returns:
            Tuple[sanitized_text, has_pii_flag, list_of_redacted_types]
        """
        sanitized = text
        detected_types: List[str] = []

        # 1. Redact Indian Aadhaar Numbers
        if cls.STRICT_PATTERNS["AADHAAR"].search(sanitized):
            sanitized = cls.STRICT_PATTERNS["AADHAAR"].sub("[REDACTED_AADHAAR]", sanitized)
            detected_types.append("AADHAAR")

        # 2. Redact Indian PAN Card Numbers
        if cls.STRICT_PATTERNS["PAN"].search(sanitized):
            sanitized = cls.STRICT_PATTERNS["PAN"].sub("[REDACTED_PAN]", sanitized)
            detected_types.append("PAN")

        # 3. Redact SSNs
        if cls.STRICT_PATTERNS["SSN"].search(sanitized):
            sanitized = cls.STRICT_PATTERNS["SSN"].sub("[REDACTED_SSN]", sanitized)
            detected_types.append("SSN")

        # 4. Redact Tax IDs / EINs
        if cls.STRICT_PATTERNS["TAX_ID"].search(sanitized):
            sanitized = cls.STRICT_PATTERNS["TAX_ID"].sub("[REDACTED_TAX_ID]", sanitized)
            detected_types.append("TAX_ID")

        # 5. Redact Bank Account Numbers
        if cls.STRICT_PATTERNS["BANK_ACCOUNT"].search(sanitized):
            sanitized = cls.STRICT_PATTERNS["BANK_ACCOUNT"].sub(r"Account Number: [REDACTED_BANK_ACCOUNT]", sanitized)
            detected_types.append("BANK_ACCOUNT")

        # 6. Redact Credit Card Numbers
        if cls.STRICT_PATTERNS["CREDIT_CARD"].search(sanitized):
            sanitized = cls.STRICT_PATTERNS["CREDIT_CARD"].sub("[REDACTED_CARD]", sanitized)
            detected_types.append("CREDIT_CARD")

        # 7. Redact Explicit Personal Mobile Numbers
        if cls.STRICT_PATTERNS["PERSONAL_PHONE"].search(sanitized):
            sanitized = cls.STRICT_PATTERNS["PERSONAL_PHONE"].sub(r"Phone: [REDACTED_PHONE]", sanitized)
            detected_types.append("PERSONAL_PHONE")

        # 8. Redact Personal Customer Emails (excluding bank support/care domains)
        if cls.STRICT_PATTERNS["PERSONAL_EMAIL"].search(sanitized):
            # Check if it is a personal email, not support@ / info@ / customercare@
            def _replace_email(match):
                email = match.group(0)
                prefix = email.split("@")[0].lower()
                if any(k in prefix for k in ["support", "care", "customercare", "help", "info", "grievance"]):
                    return email
                detected_types.append("PERSONAL_EMAIL")
                return "[REDACTED_EMAIL]"

            sanitized = cls.STRICT_PATTERNS["PERSONAL_EMAIL"].sub(_replace_email, sanitized)

        # 9. Targeted Applicant Name Redaction (Strict: Only when preceded by explicit applicant/borrower tag)
        applicant_name_regex = re.compile(r"\b(?:Applicant|Borrower|Director|Guarantor)\s+Name[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b")
        for match in applicant_name_regex.finditer(sanitized):
            candidate_name = match.group(1).strip()
            if candidate_name.lower() not in cls.INSTITUTIONAL_WHITELIST:
                sanitized = sanitized.replace(candidate_name, "[REDACTED_PERSON_NAME]")
                detected_types.append("PERSON_NAME")

        has_pii = len(detected_types) > 0
        return sanitized, has_pii, sorted(list(set(detected_types)))
