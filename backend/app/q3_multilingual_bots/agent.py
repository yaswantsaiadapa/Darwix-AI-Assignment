"""
Multilingual Voice Agent Engine for Question 3 (Philippines & Indonesia)
Handles Market Routing, Language-Tuned ASR, Culturally Grounded LLM Reasoning & In-Language Fallbacks.
"""

import io
import re
import json
from typing import Dict, Any, List, Optional
from groq import Groq
from backend.app.config import GROQ_API_KEY, GROQ_LLM_MODEL, GROQ_WHISPER_MODEL
from backend.app.q3_multilingual_bots.models import (
    MarketCode,
    PersonaConfig,
    MultilingualChatResponse,
)
from backend.app.q3_multilingual_bots.personas import (
    MARKET_PERSONAS,
    PHILIPPINES_SYSTEM_PROMPT,
    INDONESIA_SYSTEM_PROMPT,
)
from backend.app.q3_multilingual_bots.knowledge import LOCALIZED_KNOWLEDGE


def clean_think_tags(text: str) -> str:
    """Strips internal reasoning scratchpad tokens from LLM output."""
    if not text:
        return ""
    cleaned = re.sub(r"<think>[\s\S]*?</think>", "", text, flags=re.IGNORECASE)
    cleaned = re.sub(r"<thought>[\s\S]*?</thought>", "", cleaned, flags=re.IGNORECASE)
    if "<think>" in cleaned.lower():
        cleaned = re.sub(r"<think>[\s\S]*$", "", cleaned, flags=re.IGNORECASE)
    if "<thought>" in cleaned.lower():
        cleaned = re.sub(r"<thought>[\s\S]*$", "", cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


class MultilingualVoiceAgent:
    """
    Native-language conversational agent for Philippines (Taglish) and Indonesia (Bahasa Indonesia).
    """

    def __init__(self, api_key: str = None):
        self.api_key = api_key or GROQ_API_KEY
        self.client = None
        if self.api_key and self.api_key != "your_groq_api_key_here":
            try:
                self.client = Groq(api_key=self.api_key)
            except Exception as e:
                print(f"[MultilingualVoiceAgent Warning] Groq init failed: {e}")
                self.client = None

    def transcribe_audio(self, audio_bytes: bytes, market_code: MarketCode, filename: str = "audio.wav") -> str:
        """
        Performs speech transcription with language-specific context prompts to optimize code-switching accuracy.
        """
        if not self.client:
            return "Simulated multilingual transcription"

        # Domain-tuned initial prompts to prime Whisper for code-switching and financial terminology
        initial_prompts = {
            MarketCode.PHILIPPINES: "Magandang araw po. Life insurance policy, premium, beneficiary, rider, lapse, coverage, grace period po.",
            MarketCode.INDONESIA: "Selamat pagi Bapak Ibu. Angsuran cicilan, tenor, denda keterlambatan, jatuh tempo, pembiayaan OJK, nggih nuwun sewu.",
        }
        lang_codes = {
            MarketCode.PHILIPPINES: "tl",
            MarketCode.INDONESIA: "id",
        }

        try:
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = filename

            transcription = self.client.audio.transcriptions.create(
                file=(filename, audio_bytes),
                model=GROQ_WHISPER_MODEL,
                language=lang_codes.get(market_code, "en"),
                prompt=initial_prompts.get(market_code, ""),
                temperature=0.0,
                response_format="json",
            )
            return transcription.text.strip()
        except Exception as e:
            print(f"[MultilingualVoiceAgent Error] Whisper transcription failed: {e}")
            return ""

    def process_turn(
        self,
        market_code: MarketCode,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        customer_context: Optional[Dict[str, Any]] = None,
    ) -> MultilingualChatResponse:
        """
        Generates a culturally grounded, sector-accurate conversational response.
        Enforces in-language fallback and authentic register.
        """
        persona = MARKET_PERSONAS.get(market_code, MARKET_PERSONAS[MarketCode.PHILIPPINES])
        knowledge = LOCALIZED_KNOWLEDGE.get(market_code, {})

        # System prompt with localized knowledge base
        base_prompt = PHILIPPINES_SYSTEM_PROMPT if market_code == MarketCode.PHILIPPINES else INDONESIA_SYSTEM_PROMPT
        knowledge_context = "\n".join([f"- {p['topic']}: {p['rules']}" for p in knowledge.get("policies", [])])

        full_system_prompt = (
            f"{base_prompt}\n\n"
            f"LOCALIZED REGULATORY & POLICY RULES:\n{knowledge_context}\n\n"
            f"CUSTOMER CONTEXT:\n{json.dumps(customer_context or {}, indent=2)}\n"
        )

        messages = [{"role": "system", "content": full_system_prompt}]
        for turn in conversation_history[-6:]:
            messages.append({"role": turn["role"], "content": turn["content"]})
        messages.append({"role": "user", "content": user_message})

        reply_text = ""
        is_escalation = any(k in user_message.lower() for k in ["transfer", "manager", "supervisor", "tao po", "petugas", "staf cabang"])

        if self.client:
            models_to_try = [GROQ_LLM_MODEL, "openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.6-27b"]
            for model_cand in models_to_try:
                try:
                    resp = self.client.chat.completions.create(
                        model=model_cand,
                        messages=messages,
                        temperature=0.3,
                        max_tokens=600,
                    )
                    raw_text = resp.choices[0].message.content.strip()
                    reply_text = clean_think_tags(raw_text)
                    if reply_text:
                        break
                except Exception:
                    continue

        if not reply_text:
            reply_text = self._offline_fallback_response(market_code, user_message)

        # Detect identified finance terms
        identified_terms = [t for t in persona.key_terminology if t.lower() in user_message.lower() or t.lower() in reply_text.lower()]

        return MultilingualChatResponse(
            market_code=market_code,
            bot_name=persona.bot_name,
            reply_text=reply_text,
            detected_intent="INQUIRY_OR_SERVICE",
            cultural_register_used="Taglish / Conversational" if market_code == MarketCode.PHILIPPINES else "Bahasa Indonesia / Santun",
            finance_terms_identified=identified_terms,
            is_escalation=is_escalation,
            suggested_action="BRANCH_FOLLOW_UP" if is_escalation else "RESOLVE_IN_CALL",
        )

    def _offline_fallback_response(self, market_code: MarketCode, user_message: str) -> str:
        """Deterministic, culturally polite offline fallback."""
        if market_code == MarketCode.PHILIPPINES:
            return (
                "Maraming salamat po sa inyong inquiry. Naiintindihan ko po ang inyong concern. "
                "Para po sa inyong life policy at premium payments, may 31-day grace period po tayo mula sa inyong due date. "
                "May maitutulong pa po ba ako sa inyong coverage?"
            )
        else:
            return (
                "Terima kasih Bapak/Ibu atas pertanyaannya. Kami sangat memahami kebutuhan Bapak/Ibu. "
                "Terkait angsuran pembiayaan dan jatuh tempo, kami siap membantu simulasi perpanjangan tenor atau komitmen pembayaran. "
                "Ada yang bisa kami bantu jelaskan kembali, Pak/Bu?"
            )
