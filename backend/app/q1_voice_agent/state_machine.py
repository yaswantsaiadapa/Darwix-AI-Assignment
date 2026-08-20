"""
Conversation State Machine for Question 1 Voice Agent
Manages dialogue progression, intent tracking, slot filling, and RAG routing.
"""

import re
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple


class DialogueState(str, Enum):
    GREETING = "GREETING"
    DISCOVERY_BUSINESS_NAME = "DISCOVERY_BUSINESS_NAME"
    DISCOVERY_YEARS_ACTIVE = "DISCOVERY_YEARS_ACTIVE"
    DISCOVERY_ANNUAL_REVENUE = "DISCOVERY_ANNUAL_REVENUE"
    DISCOVERY_LOAN_AMOUNT = "DISCOVERY_LOAN_AMOUNT"
    DISCOVERY_PURPOSE = "DISCOVERY_PURPOSE"
    QUALIFICATION_ASSESSMENT = "QUALIFICATION_ASSESSMENT"
    POLICY_FAQ_OR_OBJECTION = "POLICY_FAQ_OR_OBJECTION"
    HUMAN_ESCALATION = "HUMAN_ESCALATION"
    CLOSING = "CLOSING"


class ConversationStateMachine:
    """
    State machine that handles conversational slot filling and policy query interception.
    """

    def __init__(self):
        self.state: DialogueState = DialogueState.GREETING
        self.slots: Dict[str, Any] = {
            "business_name": None,
            "years_in_business": None,
            "annual_revenue": None,
            "requested_amount": None,
            "purpose": None,
            "applicant_name": None,
            "phone": None,
        }
        self.escalation_requested: bool = False
        self.citations_used: List[Dict[str, Any]] = []

    def extract_numbers(self, text: str) -> List[float]:
        """Extracts currency/numbers from conversational strings (USD & INR Lakhs/Crores)."""
        clean_text = text.replace("$", "").replace("₹", "").replace("rs.", "").replace("rs", "").replace("inr", "").replace(",", "").lower()
        
        # Look for e.g. "50 lakhs", "2 crore", "1.5 cr", "150k", "2 million", "3.5m"
        multipliers = {
            r"(\d+(?:\.\d+)?)\s*(?:crores?|cr|crs)\b": 10000000,
            r"(\d+(?:\.\d+)?)\s*(?:lakhs?|lacs?|lac|l)\b": 100000,
            r"(\d+(?:\.\d+)?)\s*k\b": 1000,
            r"(\d+(?:\.\d+)?)\s*m\b": 1000000,
            r"(\d+(?:\.\d+)?)\s*million": 1000000,
            r"(\d+(?:\.\d+)?)\s*thousand": 1000,
        }
        for pattern, mult in multipliers.items():
            match = re.search(pattern, clean_text)
            if match:
                return [float(match.group(1)) * mult]

        # Standard numbers
        raw_nums = re.findall(r"\b\d+(?:\.\d+)?\b", clean_text)
        return [float(n) for n in raw_nums]

    def is_policy_question_or_objection(self, text: str) -> bool:
        """Detects if the user is asking a policy, terms, rate, or objection question."""
        text_lower = text.lower()
        keywords = [
            "what is", "how much", "what are", "interest rate", "rate", "fee", "apr",
            "collateral", "guarantee", "terms", "how long", "can i use", "do you offer",
            "crypto", "bitcoin", "mortgage", "penalty", "prepayment", "504", "7(a)", "microloan"
        ]
        return any(kw in text_lower for kw in keywords) or "?" in text

    def is_human_escalation_request(self, text: str) -> bool:
        """Detects if the user explicitly asks for a human or specialist."""
        text_lower = text.lower()
        escalation_triggers = [
            "human", "representative", "agent", "specialist", "speak to someone",
            "real person", "manager", "operator", "transfer me", "supervisor"
        ]
        return any(trig in text_lower for trig in escalation_triggers)

    def process_turn(self, user_text: str) -> Tuple[DialogueState, Optional[str]]:
        """
        Advances dialogue state and extracts applicant slot information.
        Returns:
            Tuple[next_state, prompt_instruction]
        """
        user_lower = user_text.lower()

        # Check for explicit human escalation request
        if self.is_human_escalation_request(user_text):
            self.state = DialogueState.HUMAN_ESCALATION
            self.escalation_requested = True
            return self.state, "Acknowledge the request and transfer to human loan specialist."

        # If user asks a policy/objection question during the flow
        if self.is_policy_question_or_objection(user_text) and self.state != DialogueState.CLOSING:
            # We don't advance the discovery state, we answer the question via RAG and re-prompt
            return DialogueState.POLICY_FAQ_OR_OBJECTION, "Answer user question with grounded RAG context, then guide back."

        # Progression based on current state
        if self.state == DialogueState.GREETING:
            self.state = DialogueState.DISCOVERY_BUSINESS_NAME
            return self.state, "Ask for the name of their business."

        elif self.state == DialogueState.DISCOVERY_BUSINESS_NAME:
            user_lower = user_text.lower().strip()
            if any(term in user_lower for term in ["no business", "don't have a business", "don't possess a business", "salaried", "employee", "individual"]):
                return DialogueState.POLICY_FAQ_OR_OBJECTION, "Clarify that commercial facilities require a registered business entity."

            # Ignore generic conversational filler or polite phrases
            polite_phrases = ["thank you", "thanks", "thank u", "hello", "hi", "hey", "good morning", "good afternoon", "ok", "okay", "sure", "cool", "yes", "alright", "great"]
            if user_lower in polite_phrases or any(user_lower == p for p in polite_phrases):
                return self.state, "Acknowledge politely and ask for the legal name of their business to check loan eligibility."

            # Clean up filler words e.g. "We are Apex Logistics LLC."
            clean_name = re.sub(r"^(?:we are|i am with|our company is|the business is|my company is|it is|it's)\s+", "", user_text.strip(), flags=re.IGNORECASE)
            clean_name = clean_name.rstrip(".")
            if len(clean_name) < 2 or any(err in clean_name.lower() for err in ["error", "transcription", "undefined", "null"]):
                return self.state, "I didn't quite catch that. Could you please state the legal name of your business?"

            self.slots["business_name"] = clean_name
            self.state = DialogueState.DISCOVERY_YEARS_ACTIVE
            return self.state, f"Acknowledge {self.slots['business_name']} and ask how many continuous years they have been in active operation."

        elif self.state == DialogueState.DISCOVERY_YEARS_ACTIVE:
            nums = self.extract_numbers(user_text)
            self.slots["years_in_business"] = nums[0] if nums else 2.0
            self.state = DialogueState.DISCOVERY_ANNUAL_REVENUE
            return self.state, "Ask for their approximate annual gross revenue over the last 12 months."

        elif self.state == DialogueState.DISCOVERY_ANNUAL_REVENUE:
            nums = self.extract_numbers(user_text)
            self.slots["annual_revenue"] = nums[0] if nums else 250000.0
            self.state = DialogueState.DISCOVERY_LOAN_AMOUNT
            return self.state, "Ask how much funding they are looking to secure."

        elif self.state == DialogueState.DISCOVERY_LOAN_AMOUNT:
            nums = self.extract_numbers(user_text)
            self.slots["requested_amount"] = nums[0] if nums else 100000.0
            self.state = DialogueState.DISCOVERY_PURPOSE
            return self.state, "Ask what the primary use of funds will be (working capital, equipment, debt refinance, etc.)."

        elif self.state == DialogueState.DISCOVERY_PURPOSE:
            self.slots["purpose"] = user_text.strip()
            self.state = DialogueState.QUALIFICATION_ASSESSMENT
            return self.state, "Provide preliminary underwriting assessment based on business rules."

        elif self.state == DialogueState.QUALIFICATION_ASSESSMENT:
            self.state = DialogueState.CLOSING
            return self.state, "Summarize the application, confirm contact details, and conclude the call."

        elif self.state == DialogueState.CLOSING:
            return self.state, "Thank the user and finish the call."

        return self.state, "Continue dialogue."
