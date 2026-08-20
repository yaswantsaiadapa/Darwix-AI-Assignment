"""
Underwriting & Loan Eligibility Rules Engine
Calculates preliminary qualification tiers and evaluates SBA loan program fit.
"""

from typing import Dict, Any, Tuple


class LoanRulesEngine:
    """
    Evaluates applicant business parameters against SBA 7(a), 504, and Microloan standards.
    """

    @classmethod
    def evaluate_eligibility(
        cls,
        business_name: str,
        years_in_business: float,
        annual_revenue: float,
        requested_amount: float,
        purpose: str,
        credit_score: int = 680,
    ) -> Dict[str, Any]:
        """
        Computes preliminary qualification score, recommended program, and max approved amount.
        """
        flags = []
        is_qualified = True
        recommended_program = "SBA 7(a) Standard Loan"
        max_approved = 0.0
        tier = "Tier 2 (Standard)"

        # 1. Operational Track Record Check (Commercial lending standard: 2-3 years vintage)
        if years_in_business < 1.0:
            is_qualified = False
            flags.append("Standard commercial lending requires at least 2-3 years in current business (minimum 1 year under special MSME credit schemes).")
        elif years_in_business < 3.0:
            if requested_amount <= 50000000:
                recommended_program = "CGTMSE MSME Credit Facility"
                flags.append("Eligible under CGTMSE government credit guarantee scheme (1-3 years operating vintage).")
            else:
                flags.append("Operating vintage under 3 years requires additional promoter co-guarantor.")

        # 2. Revenue & Requested Amount Ratio Check (Standard min turnover benchmark)
        if annual_revenue < 4000000 and requested_amount > 1000000:
            flags.append("Annual turnover below ₹40 Lakhs benchmark. Evaluated under Micro MSME / CGTMSE slab.")
            recommended_program = "CGTMSE Micro MSME Scheme"

        if requested_amount <= 5000000:  # Up to ₹50 Lakhs
            recommended_program = "Unsecured Business Growth Loan (Up to ₹50 Lakhs)"
        elif requested_amount <= 50000000:  # Up to ₹5 Crore
            recommended_program = "CGTMSE Collateral-Free MSME Credit (Up to ₹5 Crore)"
        else:  # Exceeding ₹5 Crore
            recommended_program = "Commercial Loan Against Property (LAP)"

        # 3. Purpose Check
        purpose_lower = purpose.lower()
        if "crypto" in purpose_lower or "bitcoin" in purpose_lower or "speculat" in purpose_lower or "gambl" in purpose_lower:
            return {
                "is_qualified": False,
                "tier": "Ineligible",
                "recommended_program": "None (Prohibited Industry/Use Case)",
                "max_approved_amount": 0,
                "monthly_payment_estimate": 0,
                "underwriting_flags": ["Prohibited use case: Speculative trading and cryptocurrency investments are strictly ineligible under official commercial underwriting rules."],
                "escalation_required": True,
            }

        if "property" in purpose_lower or "real estate" in purpose_lower or "land" in purpose_lower or "building" in purpose_lower:
            recommended_program = "Commercial Loan Against Property (LAP)"

        # 4. Credit Score & Max Amount Calculation
        if credit_score >= 720:
            tier = "Tier 1 (Prime Preferred)"
            max_multiplier = 0.40  # Up to 40% of annual revenue
        elif credit_score >= 660:
            tier = "Tier 2 (Standard MSME)"
            max_multiplier = 0.25
        else:
            tier = "Tier 3 (Subprime / Caution)"
            max_multiplier = 0.15
            flags.append("Credit score below 660 requires senior credit manager manual review.")

        calculated_max = annual_revenue * max_multiplier
        # Ensure minimum approved limit for micro loans
        if requested_amount <= 500000 and annual_revenue > 0:
            calculated_max = max(calculated_max, requested_amount)

        max_approved = min(requested_amount, calculated_max)
        if max_approved < (requested_amount * 0.5) and is_qualified:
            flags.append(f"Requested amount exceeds prudent debt service ratio. Capped at preliminary sanction.")

        # 5. Monthly Payment Calculation (Estimated 9.5% p.a. over 5-year tenor)
        annual_interest_rate = 0.095
        tenor_months = 60
        monthly_rate = annual_interest_rate / 12
        if max_approved > 0:
            monthly_payment = (
                max_approved * (monthly_rate * (1 + monthly_rate) ** tenor_months)
                / (((1 + monthly_rate) ** tenor_months) - 1)
            )
        else:
            monthly_payment = 0.0

        return {
            "is_qualified": is_qualified,
            "tier": tier,
            "recommended_program": recommended_program,
            "preliminary_max_approved": round(max_approved, 2),
            "max_approved_amount": round(max_approved, 2),
            "monthly_payment_estimate": round(monthly_payment, 2),
            "interest_rate_estimate_pct": round(annual_interest_rate * 100, 2),
            "tenor_months": tenor_months,
            "underwriting_flags": flags,
            "escalation_required": not is_qualified or ("manual review" in " ".join(flags).lower()),
        }
