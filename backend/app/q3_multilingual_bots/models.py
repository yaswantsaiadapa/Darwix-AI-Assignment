"""
Pydantic Data Contracts for Question 3: Native-Language Voice Bots (Philippines & Indonesia)
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class MarketCode(str, Enum):
    PHILIPPINES = "PH"
    INDONESIA = "ID"


class SectorType(str, Enum):
    BANCASSURANCE = "BANCASSURANCE"
    MULTIFINANCE = "MULTIFINANCE"


class DialogueRole(str, Enum):
    AGENT = "Agent"
    CUSTOMER = "Customer"
    SYSTEM = "System"


class PersonaConfig(BaseModel):
    market_code: MarketCode
    market_name: str
    flag_emoji: str
    sector: SectorType
    bot_name: str
    target_languages: List[str]
    tts_voice: str
    key_terminology: List[str]
    politeness_particles: List[str]
    currency_symbol: str
    currency_code: str
    description: str


class DialogueTurn(BaseModel):
    role: DialogueRole
    speaker_name: str
    text: str
    audio_timestamp_start: float = 0.0
    audio_timestamp_end: float = 0.0
    detected_language_mix: Optional[str] = None
    cultural_markers: List[str] = Field(default_factory=list)


class ScenarioRecord(BaseModel):
    scenario_id: str
    market_code: MarketCode
    title: str
    description: str
    test_category: str  # cooperative, objection, regional_accent, colloquial_slang, human_escalation
    expected_outcome: str
    timeline: List[DialogueTurn]
    adaptation_highlights: List[str] = Field(default_factory=list)


class MultilingualChatRequest(BaseModel):
    market_code: MarketCode
    message: str
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)
    customer_context: Optional[Dict[str, Any]] = None


class MultilingualChatResponse(BaseModel):
    market_code: MarketCode
    bot_name: str
    reply_text: str
    detected_intent: str
    cultural_register_used: str
    finance_terms_identified: List[str] = Field(default_factory=list)
    is_escalation: bool = False
    suggested_action: Optional[str] = None


class MarketEvaluationReport(BaseModel):
    market_code: MarketCode
    asr_provider: str
    asr_model: str
    code_switching_accuracy_pct: float
    regional_accent_intelligibility_pct: float
    observed_asr_errors: List[str]
    tts_voice: str
    tts_quality_score: float
    adaptation_examples: List[Dict[str, str]]
    compliance_guidelines: List[str]
    native_speaker_nuances: List[str]
