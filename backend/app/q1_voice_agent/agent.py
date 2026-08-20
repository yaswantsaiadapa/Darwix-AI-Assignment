"""
Main Voice Agent Coordinator for Question 1
Integrates Unified LLM Intent & Slot Routing, Hybrid RAG Retriever, Grounding Gate, TTS, and CRM Webhooks.
"""

import base64
from pathlib import Path
from typing import Dict, Any, List, Optional
from backend.app.q1_voice_agent.state_machine import ConversationStateMachine, DialogueState
from backend.app.q1_voice_agent.rules_engine import LoanRulesEngine
from backend.app.q1_voice_agent.crm_webhook import CRMWebhookHandler
from backend.app.q1_voice_agent.groq_service import GroqService
from backend.app.q1_voice_agent.tts_engine import TTSEngine
from backend.app.q2_knowledge_base.retriever import HybridRetriever
from backend.app.q2_knowledge_base.indexer import KnowledgeIndexer


class VoiceAgent:
    """
    Production-ready knowledge-grounded voice agent for business loan qualification.
    """

    def __init__(self, retriever: Optional[HybridRetriever] = None, groq_service: Optional[GroqService] = None):
        self.state_machine = ConversationStateMachine()
        self.groq_service = groq_service or GroqService()
        self.transcript: List[Dict[str, str]] = []
        self.citations_history: List[Dict[str, Any]] = []
        self.crm_lead_result: Optional[Dict[str, Any]] = None

        if retriever is not None:
            self.retriever = retriever
        else:
            project_root = Path(__file__).resolve().parent.parent.parent.parent
            vector_dir = project_root / "data" / "vector_db"
            indexer = KnowledgeIndexer()
            try:
                indexer.load_indices(vector_dir)
                self.retriever = HybridRetriever(indexer, dense_weight=0.70, confidence_threshold=0.55)
            except Exception as e:
                print(f"[VoiceAgent Warning] Could not load vector index ({e}). RAG retriever uninitialized.")
                self.retriever = None

    def reset_session(self):
        """Resets agent conversation state."""
        self.state_machine = ConversationStateMachine()
        self.transcript = []
        self.citations_history = []
        self.crm_lead_result = None

    def get_greeting(self) -> Dict[str, Any]:
        """Returns the initial agent opening greeting."""
        greeting_text = (
            "Hello! Thank you for calling Darwix AI commercial lending. My name is Alex. "
            "I can help check your eligibility for commercial business growth loans, collateral-free MSME credit, and working capital lines. "
            "May I know the legal name of your business?"
        )
        self.state_machine.state = DialogueState.DISCOVERY_BUSINESS_NAME
        self.transcript.append({"role": "assistant", "content": greeting_text})
        audio_bytes = TTSEngine.synthesize_to_bytes(greeting_text)
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8") if audio_bytes else ""

        return {
            "agent_response": greeting_text,
            "dialogue_state": DialogueState.DISCOVERY_BUSINESS_NAME.value,
            "audio_base64": audio_b64,
            "citations": [],
            "crm_lead": None,
            "is_grounded": True,
        }

    def interact(self, user_message: str) -> Dict[str, Any]:
        """
        Processes a single conversational turn using Unified LLM Function/Intent Routing.
        """
        user_message_clean = user_message.strip()
        self.transcript.append({"role": "user", "content": user_message_clean})

        # 1. Unified Single-Turn LLM Intent & Slot Decision
        decision = self.groq_service.route_and_extract(
            user_message=user_message_clean,
            current_slots=self.state_machine.slots,
            conversation_history=self.transcript,
        )

        action = decision.get("action", "CONVERSE")
        search_query = decision.get("search_query")
        extracted_slots = decision.get("slots", {}) or {}
        is_human_escalation = decision.get("is_human_escalation", False)

        citations_this_turn: List[Dict[str, Any]] = []
        is_grounded = True
        agent_reply = ""
        current_dialogue_state = "CONVERSATIONAL"

        # Update slots with any valid extracted entity
        for key, val in extracted_slots.items():
            if val is not None and key in self.state_machine.slots:
                self.state_machine.slots[key] = val

        # 1. Handle Explicit Human Escalation
        if is_human_escalation or action == "ESCALATE":
            current_dialogue_state = DialogueState.HUMAN_ESCALATION.value
            agent_reply = (
                "I completely understand. I am transferring your call directly to a senior commercial "
                "lending specialist right now. They will review your application immediately."
            )
            # Create escalation lead
            eligibility = LoanRulesEngine.evaluate_eligibility(
                business_name=self.state_machine.slots.get("business_name") or "Inquiring Business",
                years_in_business=float(self.state_machine.slots.get("years_in_business") or 2.0),
                annual_revenue=float(self.state_machine.slots.get("annual_revenue") or 200000.0),
                requested_amount=float(self.state_machine.slots.get("requested_amount") or 100000.0),
                purpose=str(self.state_machine.slots.get("purpose") or "General Inquiry"),
            )
            eligibility["escalation_required"] = True
            self.crm_lead_result = CRMWebhookHandler.create_lead(
                business_name=self.state_machine.slots.get("business_name") or "Inquiring Business",
                applicant_name="Phone Applicant",
                phone="Voice Channel",
                years_in_business=float(self.state_machine.slots.get("years_in_business") or 2.0),
                annual_revenue=float(self.state_machine.slots.get("annual_revenue") or 200000.0),
                requested_amount=float(self.state_machine.slots.get("requested_amount") or 100000.0),
                purpose=str(self.state_machine.slots.get("purpose") or "General Inquiry"),
                eligibility_result=eligibility,
                transcript=self.transcript,
                citations_used=self.citations_history,
                call_summary="Customer requested direct transfer to a human specialist.",
            )

        # 2. Handle Knowledge / Policy / Customer Service / Objection Query via Hybrid RAG
        elif action == "SEARCH_KB" or search_query:
            current_dialogue_state = DialogueState.POLICY_FAQ_OR_OBJECTION.value
            query_to_search = search_query if search_query else user_message_clean
            if self.retriever:
                # Sub-query decomposition for multi-part compound queries
                import re
                delimiters = [r"\?", r"\band\b", r"\balso\b", r"\bwhat is\b", r"\bwhat are\b", r"\bhow about\b", r"\bhow much\b"]
                pattern = "|".join(delimiters)
                raw_parts = re.split(pattern, user_message_clean, flags=re.IGNORECASE)
                sub_queries = [p.strip() for p in raw_parts if len(p.strip()) > 8]
                if not sub_queries:
                    sub_queries = [query_to_search]

                all_results = []
                seen_chunk_ids = set()
                is_any_supported = False

                for sq in sub_queries:
                    is_sup, sq_res, _ = self.retriever.grounded_retrieval(sq, top_k=2)
                    if is_sup:
                        is_any_supported = True
                    for r in sq_res:
                        if r.record.record_id not in seen_chunk_ids:
                            seen_chunk_ids.add(r.record.record_id)
                            all_results.append(r)

                # Fallback to direct search if sub-queries yielded nothing
                if not all_results:
                    is_sup, all_results, _ = self.retriever.grounded_retrieval(query_to_search, top_k=5)
                    is_any_supported = is_sup

                if is_any_supported and all_results:
                    retrieved_context = "\n\n".join([f"[{r.record.record_id}] {r.record.title}:\n{r.record.content}" for r in all_results[:8]])
                    citations_this_turn = [r.citation.model_dump() for r in all_results[:8]]
                    self.citations_history.extend(citations_this_turn)
                    agent_reply = self.groq_service.generate_grounded_response(
                        user_message=user_message_clean,
                        retrieved_context=retrieved_context,
                        conversation_history=self.transcript,
                        dialogue_state="POLICY_FAQ_OR_OBJECTION",
                        is_supported=True,
                    )
                else:
                    is_grounded = False
                    agent_reply = (
                        "I do not have verified policy guidelines regarding that in our official underwriting guidelines. "
                        "We specialize in commercial business growth loans, working capital facilities, and collateral-free credit. "
                        "Would you like to proceed with checking your business loan eligibility?"
                    )
            else:
                agent_reply = "I apologize, our knowledge base is currently being updated. Let's continue with your loan application details."

        # 3. Check if all required slots are filled for Qualification Calculation
        elif all(self.state_machine.slots.get(k) is not None for k in ["business_name", "years_in_business", "annual_revenue", "requested_amount", "purpose"]):
            current_dialogue_state = DialogueState.QUALIFICATION_ASSESSMENT.value
            eligibility = LoanRulesEngine.evaluate_eligibility(
                business_name=str(self.state_machine.slots.get("business_name") or "Your Enterprise"),
                years_in_business=float(self.state_machine.slots.get("years_in_business") or 2.0),
                annual_revenue=float(self.state_machine.slots.get("annual_revenue") or 250000.0),
                requested_amount=float(self.state_machine.slots.get("requested_amount") or 100000.0),
                purpose=str(self.state_machine.slots.get("purpose") or "Working Capital"),
            )
            
            # Check if user gave confirmation to submit ("yes", "submit", "please", "proceed")
            user_low = user_message_clean.lower()
            if any(conf in user_low for conf in ["submit", "yes", "proceed", "sure", "please do", "confirm"]):
                current_dialogue_state = DialogueState.CLOSING.value
                self.crm_lead_result = CRMWebhookHandler.create_lead(
                    business_name=str(self.state_machine.slots.get("business_name") or "Applicant Business"),
                    applicant_name="Phone Applicant",
                    phone="Voice Channel",
                    years_in_business=float(self.state_machine.slots.get("years_in_business") or 2.0),
                    annual_revenue=float(self.state_machine.slots.get("annual_revenue") or 250000.0),
                    requested_amount=float(self.state_machine.slots.get("requested_amount") or 100000.0),
                    purpose=str(self.state_machine.slots.get("purpose") or "Working Capital"),
                    eligibility_result=eligibility,
                    transcript=self.transcript,
                    citations_used=self.citations_history,
                    call_summary="Customer completed voice qualification. Lead generated in CRM.",
                )
                agent_reply = (
                    f"Wonderful! I have generated your pre-approval file {self.crm_lead_result['lead_id']}. "
                    "Our commercial lending team will contact you within 24 hours to finalize documents. Thank you for choosing Darwix AI!"
                )
            else:
                if eligibility["is_qualified"]:
                    agent_reply = (
                        f"Great news! Based on your {self.state_machine.slots.get('years_in_business')} years in operation and "
                        f"Rs. {float(self.state_machine.slots.get('annual_revenue') or 0):,.0f} annual turnover, your business qualifies under our "
                        f"{eligibility['recommended_program']} for up to Rs. {eligibility.get('max_approved_amount', 0):,.0f}. "
                        f"Estimated monthly EMI starts around Rs. {eligibility.get('monthly_payment_estimate', 0):,.0f}/month. "
                        "Shall I submit your preliminary pre-approval application to underwriting?"
                    )
                else:
                    flag_text = " ".join(eligibility["underwriting_flags"])
                    agent_reply = (
                        f"Based on our underwriting criteria: {flag_text} "
                        "We can still review your application manually with a senior underwriter. Would you like me to submit your file for review?"
                    )

        # 4. Prompt for next missing qualification slot
        else:
            current_dialogue_state = "DISCOVERY"
            # Find what is missing next in order: business_name -> years_in_business -> annual_revenue -> requested_amount -> purpose
            if not self.state_machine.slots.get("business_name"):
                prompt_hint = "Acknowledge what the user said warmly, and politely ask for the legal name of their business."
            elif self.state_machine.slots.get("years_in_business") is None:
                prompt_hint = f"Acknowledge {self.state_machine.slots.get('business_name')} and ask how many continuous years they have been in active business."
            elif self.state_machine.slots.get("annual_revenue") is None:
                prompt_hint = "Ask approximately what their gross annual revenue / turnover was over the past 12 months."
            elif self.state_machine.slots.get("requested_amount") is None:
                prompt_hint = "Ask how much commercial funding or loan amount they are looking to borrow."
            else:
                prompt_hint = "Ask what the primary purpose of the loan will be (for example, working capital, inventory, or equipment purchase)."

            agent_reply = self.groq_service.generate_conversational_response(
                user_message=user_message_clean,
                dialogue_state=current_dialogue_state,
                prompt_instruction=prompt_hint,
                conversation_history=self.transcript,
                slots=self.state_machine.slots,
            )

        self.transcript.append({"role": "assistant", "content": agent_reply})

        # Synthesize Voice Audio
        audio_bytes = TTSEngine.synthesize_to_bytes(agent_reply)
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8") if audio_bytes else ""

        return {
            "agent_response": agent_reply,
            "dialogue_state": current_dialogue_state,
            "audio_base64": audio_b64,
            "citations": citations_this_turn,
            "crm_lead": self.crm_lead_result,
            "is_grounded": is_grounded,
        }
