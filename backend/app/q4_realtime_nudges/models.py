"""
Data Contracts and Pydantic Models for Question 4: Real-Time Call Intelligence & Nudges
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import time


class Speaker(str, Enum):
    AGENT = "Agent"
    CUSTOMER = "Customer"
    UNKNOWN = "Unknown"


class SignalType(str, Enum):
    COMPLIANCE_GAP = "COMPLIANCE_GAP"
    MISSED_CROSS_SELL = "MISSED_CROSS_SELL"
    RISING_FRUSTRATION = "RISING_FRUSTRATION"
    PAYMENT_DIFFICULTY = "PAYMENT_DIFFICULTY"
    CALLBACK_NEED = "CALLBACK_NEED"
    GENERAL_ADVISORY = "GENERAL_ADVISORY"


class PriorityLevel(str, Enum):
    CRITICAL = "CRITICAL"  # Statutory compliance breach, legal violations
    HIGH = "HIGH"          # Severe customer frustration, payment hardship
    MEDIUM = "MEDIUM"      # Missed cross-sell opportunities, upsell
    LOW = "LOW"            # General conversational tips


class TranscriptSegment(BaseModel):
    segment_id: str
    speaker: Speaker
    text: str
    start_time: float
    end_time: float
    confidence: float = 1.0


class DetectedSignal(BaseModel):
    signal_id: str
    signal_type: SignalType
    priority: PriorityLevel
    headline: str
    actionable_recommendation: str
    trigger_excerpt: str
    confidence: float = Field(ge=0.0, le=1.0)
    speaker_origin: Speaker
    timestamp: float = Field(default_factory=time.time)


class Nudge(BaseModel):
    nudge_id: str
    signal_type: SignalType
    priority: PriorityLevel
    headline: str
    actionable_recommendation: str
    trigger_excerpt: str
    suggested_script: Optional[str] = None
    confidence: float
    created_at: float = Field(default_factory=time.time)
    expires_in_seconds: int = 25
    is_preempted: bool = False
    is_dismissed: bool = False


class LatencyRecord(BaseModel):
    chunk_index: int
    audio_received_time: float
    asr_latency_ms: float
    signal_extraction_latency_ms: float
    governor_latency_ms: float
    delivery_latency_ms: float
    total_end_to_end_ms: float


class TelemetryReport(BaseModel):
    total_chunks_processed: int
    total_nudges_generated: int
    total_nudges_suppressed: int
    p50_total_latency_ms: float
    p95_total_latency_ms: float
    p50_asr_latency_ms: float
    p95_asr_latency_ms: float
    p50_signal_latency_ms: float
    p95_signal_latency_ms: float
    suppression_reasons: Dict[str, int]
    compliance_violations_prevented: int
    cross_sell_opportunities_detected: int


class ScenarioInfo(BaseModel):
    scenario_id: str
    name: str
    description: str
    expected_signals: List[str]
    expected_nudge_priority: str
    duration_seconds: float
    audio_file_url: str
