"""
Mock CRM & Escalation Webhook Handler for Question 1
Generates structured CRM lead payloads, formats transcripts, and triggers human escalation tickets.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
import uuid


class CRMWebhookHandler:
    """
    Handles business actions: Lead creation, underwriting summary, and human escalation tickets.
    """

    @classmethod
    def create_lead(
        cls,
        business_name: str,
        applicant_name: str,
        phone: str,
        years_in_business: float,
        annual_revenue: float,
        requested_amount: float,
        purpose: str,
        eligibility_result: Dict[str, Any],
        transcript: List[Dict[str, str]],
        citations_used: List[Dict[str, Any]],
        call_summary: str,
    ) -> Dict[str, Any]:
        """
        Creates and persists a structured CRM Lead & Qualification Record.
        """
        lead_id = f"LEAD-SBA-{uuid.uuid4().hex[:8].upper()}"
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%SZ")

        payload = {
            "lead_id": lead_id,
            "created_at": timestamp,
            "status": "QUALIFIED" if eligibility_result.get("is_qualified") else "NEEDS_REVIEW",
            "business_profile": {
                "business_name": business_name or "Commercial Applicant",
                "applicant_name": applicant_name or "Authorized Officer",
                "phone": phone or "Captured via Voice Channel",
                "years_in_business": years_in_business,
                "annual_revenue": annual_revenue,
                "requested_loan_amount": requested_amount,
                "stated_loan_purpose": purpose,
            },
            "underwriting_assessment": {
                "eligibility_tier": eligibility_result.get("tier", "Unknown"),
                "recommended_program": eligibility_result.get("recommended_program", "SBA 7(a)"),
                "preliminary_max_approved": eligibility_result.get("max_approved_amount", 0.0),
                "monthly_payment_estimate": eligibility_result.get("monthly_payment_estimate", 0.0),
                "underwriting_flags": eligibility_result.get("underwriting_flags", []),
                "escalation_required": eligibility_result.get("escalation_required", False),
            },
            "call_metadata": {
                "total_turns": len(transcript),
                "call_summary": call_summary,
                "citations_consulted": citations_used,
            },
            "full_transcript": transcript,
        }

        # Persist lead locally in recordings_and_transcripts/crm_leads.json
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        output_dir = project_root / "recordings_and_transcripts"
        output_dir.mkdir(parents=True, exist_ok=True)
        leads_file = output_dir / "crm_leads.json"

        existing_leads = []
        if leads_file.exists():
            try:
                with open(leads_file, "r", encoding="utf-8") as f:
                    existing_leads = json.load(f)
            except Exception:
                existing_leads = []

        existing_leads.append(payload)
        with open(leads_file, "w", encoding="utf-8") as f:
            json.dump(existing_leads, f, indent=2)

        print(f"[CRM Webhook] Generated Lead {lead_id} -> Saved to {leads_file.name}")
        return payload
