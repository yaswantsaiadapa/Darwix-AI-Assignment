"""
Groq API Service for Question 1 & Question 4
Provides ultra-low-latency Speech-to-Text (Whisper Large v3) and Grounded Reasoning (OpenAI GPT-OSS / Qwen on Groq).
Includes Unified Single-Turn LLM Intent & Slot Extraction with strict output cleaning and multi-question RAG support.
"""

import io
import json
import re
from typing import List, Dict, Any, Optional
import httpx
from groq import Groq
from backend.app.config import GROQ_API_KEY, GROQ_LLM_MODEL, GROQ_WHISPER_MODEL


def clean_llm_response(text: str) -> str:
    """Strips internal <think>...</think> chain-of-thought tokens and raw markdown symbols."""
    if not text:
        return ""
    cleaned = re.sub(r"<think>[\s\S]*?</think>", "", text, flags=re.IGNORECASE)
    cleaned = re.sub(r"<thought>[\s\S]*?</thought>", "", cleaned, flags=re.IGNORECASE)
    # Strip unclosed thinking block if token ceiling was hit mid-thought
    if "<think>" in cleaned.lower():
        cleaned = re.sub(r"<think>[\s\S]*$", "", cleaned, flags=re.IGNORECASE)
    if "<thought>" in cleaned.lower():
        cleaned = re.sub(r"<thought>[\s\S]*$", "", cleaned, flags=re.IGNORECASE)

    # Strip inline bracket citations
    cleaned = re.sub(r"【[^】]+】", "", cleaned)
    cleaned = re.sub(r"\[kb_[^\]]+\]", "", cleaned)

    # Strip markdown symbols so speech synthesis never reads asterisks or hashtags
    cleaned = re.sub(r"\*\*([^*]+)\*\*", r"\1", cleaned)
    cleaned = re.sub(r"\*([^*]+)\*", r"\1", cleaned)
    cleaned = re.sub(r"^#+\s*", "", cleaned, flags=re.MULTILINE)

    return cleaned.strip()


class GroqService:
    """
    Handles Whisper STT transcription and fast LLaMA / GPT-OSS grounded reasoning with strict guardrails.
    """

    def __init__(self, api_key: str = None):
        self.api_key = api_key or GROQ_API_KEY
        self.client = None
        self.models_to_try = [
            GROQ_LLM_MODEL,
            "openai/gpt-oss-120b",
            "openai/gpt-oss-20b",
            "qwen/qwen3.6-27b",
            "groq/compound",
        ]
        if self.api_key and self.api_key != "your_groq_api_key_here":
            try:
                self.client = Groq(api_key=self.api_key)
                print(f"[GroqService] Initialized Groq Client (STT: {GROQ_WHISPER_MODEL}, LLM: {GROQ_LLM_MODEL})")
            except Exception as e:
                print(f"[GroqService Warning] Failed to initialize Groq client: {e}")
                self.client = None
        else:
            print("[GroqService Info] Operating in Resilient Offline Engine mode.")

    def transcribe_audio(self, audio_bytes: bytes, filename: str = "audio.wav") -> str:
        """
        Transcribes voice audio using Groq Whisper API (whisper-large-v3).
        """
        if not self.client:
            return "Simulated transcription: customer spoke audio input."

        try:
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = filename

            transcription = self.client.audio.transcriptions.create(
                file=(filename, audio_bytes),
                model=GROQ_WHISPER_MODEL,
                temperature=0.0,
                response_format="json",
            )
            return transcription.text.strip()
        except Exception as e:
            print(f"[GroqService Error] Whisper transcription failed: {e}")
            return ""

    def route_and_extract(
        self,
        user_message: str,
        current_slots: Dict[str, Any],
        conversation_history: List[Dict[str, str]],
    ) -> Dict[str, Any]:
        """
        Unified Single-Turn Intent Classification & Slot Extraction via LLM.
        Accurately distinguishes between policy/customer service inquiries vs applicant data.
        """
        if not self.client:
            return {
                "action": "CONVERSE",
                "search_query": None,
                "slots": {},
                "is_human_escalation": False,
            }

        system_prompt = (
            "You are an intelligent intent router and entity extractor for a commercial lending voice agent.\n"
            "Analyze the user message in context of the conversation and output a JSON object with:\n"
            "- 'action': 'SEARCH_KB' (if user asks any question about policies, customer service, terms, timelines, fees, objections, rates, eligibility rules, permitted/prohibited loan purposes like crypto/trading, or general inquiries starting with 'can I', 'do you', 'what is', 'how much', etc.), "
            "'UPDATE_SLOTS' (if user is directly providing their own qualification information like business name, years in business, annual turnover, requested amount, or purpose), "
            "'ESCALATE' (if requesting a human specialist/manager/agent), or 'CONVERSE' (greetings, pleasantries, small talk).\n"
            "- 'search_query': string or null (clean semantic search query preserving all key inquiry topics if action is SEARCH_KB)\n"
            "- 'slots': object with extracted keys: business_name (string|null), years_in_business (float|null), annual_revenue (float|null), requested_amount (float|null), purpose (string|null)\n"
            "- 'is_human_escalation': boolean\n"
            f"CURRENT KNOWN APPLICANT SLOTS: {current_slots}"
        )

        messages = [{"role": "system", "content": system_prompt}]
        for turn in conversation_history[-4:]:
            messages.append({"role": turn["role"], "content": turn["content"]})
        messages.append({"role": "user", "content": user_message})

        for model_candidate in self.models_to_try:
            try:
                resp = self.client.chat.completions.create(
                    model=model_candidate,
                    messages=messages,
                    response_format={"type": "json_object"},
                    temperature=0.0,
                    max_tokens=350,
                )
                raw_text = clean_llm_response(resp.choices[0].message.content.strip())
                data = json.loads(raw_text)
                return data
            except Exception:
                continue

        return {"action": "CONVERSE", "search_query": None, "slots": {}, "is_human_escalation": False}

    def generate_conversational_response(
        self,
        user_message: str,
        dialogue_state: str,
        prompt_instruction: str,
        conversation_history: List[Dict[str, str]],
        slots: Dict[str, Any] = None,
    ) -> str:
        """
        Generates conversational discovery and qualification responses.
        """
        if not self.client:
            return prompt_instruction

        system_prompt = (
            "You are Alex, an experienced, friendly, and professional commercial lending advisor at Darwix Commercial Lending speaking over the phone with a business loan applicant.\n"
            f"GOAL / INSTRUCTION: {prompt_instruction}\n"
            f"CURRENT QUALIFICATION SLOTS COLLECTED: {slots or {}}\n"
            "RULES:\n"
            "1. Speak naturally, warmly, and concisely as if speaking over a phone call.\n"
            "2. Keep your response brief (1-2 sentences) so the borrower can easily reply.\n"
            "3. Do NOT output internal thinking or reasoning tags.\n"
        )

        messages = [{"role": "system", "content": system_prompt}]
        for turn in conversation_history[-4:]:
            messages.append({"role": turn["role"], "content": turn["content"]})
        messages.append({"role": "user", "content": user_message})

        for model_candidate in self.models_to_try:
            try:
                completion = self.client.chat.completions.create(
                    model=model_candidate,
                    messages=messages,
                    temperature=0.2,
                    max_tokens=150,
                )
                raw_out = completion.choices[0].message.content.strip()
                res_text = clean_llm_response(raw_out)
                if res_text:
                    return res_text
            except Exception:
                continue

        return prompt_instruction

    def generate_grounded_response(
        self,
        user_message: str,
        retrieved_context: str,
        conversation_history: List[Dict[str, str]],
        dialogue_state: str,
        is_supported: bool = True,
    ) -> str:
        """
        Generates grounded conversational response covering single or multi-part questions.
        Enforces zero hallucination guardrail.
        """
        if not is_supported or not retrieved_context.strip():
            return (
                "I apologize, but I do not have verified policy guidelines regarding that in our official "
                "underwriting guidelines. Let me make a note and connect you with a senior commercial loan officer."
            )

        if not self.client:
            return self._generate_offline_grounded_response(user_message, retrieved_context, dialogue_state)

        system_prompt = (
            "You are Alex, an experienced human commercial loan officer at Darwix Commercial Lending talking over the phone with a customer.\n\n"
            "CRITICAL SPOKEN PHONE CONVERSATION RULES (ACT LIKE A REAL HUMAN AGENT):\n"
            "1. You are a live human agent talking on a phone call. Answer like a real person having a verbal phone conversation.\n"
            "2. NEVER output markdown symbols (like **, __, #, -, *), asterisks, bullet dashes, or section headers (like Section 4.1). NEVER read brackets or section codes aloud.\n"
            "3. Speak in complete, natural conversational sentences. Explain the policy like you are explaining it verbally to a person over the phone.\n"
            "4. NEVER read out bullet lists or say 'bullet point'. Connect ideas naturally with spoken phrases like 'First, ...', 'Also, ...', 'Regarding the fees, ...', and 'In addition to that, ...'.\n"
            "5. Maintain 100% factual accuracy on loan caps, interest rates, and fees from the RETRIEVED CONTEXT below, but explain what they mean conversationally.\n"
            "6. If a specific figure is not in the context, politely let the customer know in conversational words that it is outside our standard manual and offer to connect them with a senior specialist.\n"
            "7. Do NOT output internal reasoning tags or thinking steps.\n\n"
            f"CURRENT DIALOGUE STATE: {dialogue_state}\n"
            f"RETRIEVED CONTEXT:\n{retrieved_context}\n"
        )

        messages = [{"role": "system", "content": system_prompt}]
        for turn in conversation_history[-4:]:
            messages.append({"role": turn["role"], "content": turn["content"]})
        messages.append({"role": "user", "content": user_message})

        for model_candidate in self.models_to_try:
            try:
                completion = self.client.chat.completions.create(
                    model=model_candidate,
                    messages=messages,
                    temperature=0.1,
                    max_tokens=900,
                )
                raw_out = completion.choices[0].message.content.strip()
                res_text = clean_llm_response(raw_out)
                if res_text:
                    return res_text
            except Exception:
                continue

        return self._generate_offline_grounded_response(user_message, retrieved_context, dialogue_state)

    def _generate_offline_grounded_response(self, query: str, context: str, state: str) -> str:
        """Heuristic offline grounded response fallback."""
        lines = [line.strip() for line in context.split("\n") if line.strip() and not line.startswith("[")]
        summary_snippet = " ".join(lines[:4])
        return f"Based on our official underwriting guidelines: {summary_snippet}"
