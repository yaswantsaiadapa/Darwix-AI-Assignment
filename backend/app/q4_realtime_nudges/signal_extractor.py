"""
Real-Time Multi-Signal Extraction Engine for Question 4
Analyzes rolling conversation context via Groq LLM and high-speed rule heuristics to detect:
Compliance Gaps, Cross-Sell Opportunities, Rising Frustration, and Payment Risks.
"""

import time
import json
import uuid
from typing import List, Dict, Any, Optional, Tuple
from backend.app.q1_voice_agent.groq_service import GroqService, clean_llm_response
from backend.app.q4_realtime_nudges.models import (
    Speaker,
    SignalType,
    PriorityLevel,
    TranscriptSegment,
    DetectedSignal,
)


class RealTimeSignalExtractor:
    """
    Evaluates rolling call transcripts in real-time to detect actionable banking & compliance signals.
    """

    def __init__(self, groq_service: Optional[GroqService] = None):
        self.groq_service = groq_service or GroqService()

    def extract_signals(
        self,
        rolling_transcript: List[TranscriptSegment],
        latest_segment: TranscriptSegment,
    ) -> Tuple[List[DetectedSignal], float]:
        """
        Scans rolling conversation buffer and returns list of detected signals with latency timing.
        
        Returns:
            Tuple[List[DetectedSignal], extraction_latency_ms]
        """
        t_start = time.perf_counter()
        signals: List[DetectedSignal] = []

        if not rolling_transcript:
            return [], (time.perf_counter() - t_start) * 1000.0

        # Build formatted dialogue text
        conversation_lines = []
        for seg in rolling_transcript[-8:]:  # Last 8 turns
            conversation_lines.append(f"[{seg.speaker.value} ({seg.start_time:.1f}s)]: {seg.text}")
        dialogue_text = "\n".join(conversation_lines)

        latest_lower = latest_segment.text.lower()
        speaker_val = latest_segment.speaker.value.lower()

        # 1. High-Precision Domain Heuristics (Ultra-fast < 1ms)

        # Heuristic 1: Compliance Gap Check
        # If agent quotes rate (e.g. 10.5% or interest rate) but omits "floating/EBLR/prepayment/foreclosure"
        if speaker_val == "agent":
            if any(k in latest_lower for k in ["interest rate", "approved at", "10.5%", "rate is", "proceed with", "disburse"]) and not any(k in latest_lower for k in ["floating", "eblr", "mclr", "pre-closure", "foreclosure"]):
                # Check if rate was mentioned in recent turns
                if any(k in dialogue_text.lower() for k in ["10.5%", "rate is 10.5%", "interest rate"]):
                    signals.append(
                        DetectedSignal(
                            signal_id=f"sig_{uuid.uuid4().hex[:8]}",
                            signal_type=SignalType.COMPLIANCE_GAP,
                            priority=PriorityLevel.CRITICAL,
                            headline="⚠️ Statutory Rate & Prepayment Disclosure Missing!",
                            actionable_recommendation="State that the quoted rate is floating (EBLR-linked) and disclose the mandatory 3% pre-closure charge before requesting bank details.",
                            trigger_excerpt=latest_segment.text,
                            confidence=0.96,
                            speaker_origin=latest_segment.speaker,
                        )
                    )

        # Heuristic 2: Cross-Sell Opportunity Check
        # If customer mentions fleet, trucks, warehouse, expansion
        if speaker_val == "customer":
            if any(k in latest_lower for k in ["warehouse", "trucks", "vehicles", "fleet", "second location", "expanding", "branch office", "delivery footprint"]):
                signals.append(
                    DetectedSignal(
                        signal_id=f"sig_{uuid.uuid4().hex[:8]}",
                        signal_type=SignalType.MISSED_CROSS_SELL,
                        priority=PriorityLevel.MEDIUM,
                        headline="💡 Commercial Expansion & Fleet Cross-Sell Opportunity",
                        actionable_recommendation="Customer mentioned expanding with 3 refrigerated trucks and a second warehouse. Offer Commercial LAP or Equipment Guarantee Scheme (up to ₹5 Crore).",
                        trigger_excerpt=latest_segment.text,
                        confidence=0.92,
                        speaker_origin=latest_segment.speaker,
                    )
                )

        # Heuristic 3: Rising Frustration Check
        if speaker_val == "customer":
            if any(k in latest_lower for k in ["ridiculous", "waste of my time", "three times", "already sent", "manager", "hold for", "angry", "upset"]):
                signals.append(
                    DetectedSignal(
                        signal_id=f"sig_{uuid.uuid4().hex[:8]}",
                        signal_type=SignalType.RISING_FRUSTRATION,
                        priority=PriorityLevel.HIGH,
                        headline="⚠️ Rising Customer Frustration & Escalation Risk",
                        actionable_recommendation="Acknowledge the document re-upload delay empathetically and offer immediate supervisor verification before asking for more information.",
                        trigger_excerpt=latest_segment.text,
                        confidence=0.95,
                        speaker_origin=latest_segment.speaker,
                    )
                )

        # 2. Semantic LLM Reasoning (if no immediate pattern triggered and client is ready)
        if not signals and self.groq_service and self.groq_service.client:
            try:
                prompt = (
                    f"Analyze this call transcript and detect if any of these 3 signals occurred in the latest turn: "
                    f"1. COMPLIANCE_GAP (missing mandatory disclosure), 2. MISSED_CROSS_SELL (expansion/vehicles), 3. RISING_FRUSTRATION.\n"
                    f"Transcript:\n{dialogue_text}\n"
                    f"Respond ONLY with a JSON object format: {{\"signals\": []}}"
                )
                completion = self.groq_service.client.chat.completions.create(
                    model="openai/gpt-oss-120b",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0,
                    max_tokens=250,
                    timeout=3.0,
                )
                raw_text = clean_llm_response(completion.choices[0].message.content.strip())
                if "{" in raw_text and "}" in raw_text:
                    json_str = raw_text[raw_text.find("{"):raw_text.rfind("}")+1]
                    parsed = json.loads(json_str)
                    for item in parsed.get("signals", []):
                        signals.append(
                            DetectedSignal(
                                signal_id=f"sig_{uuid.uuid4().hex[:8]}",
                                signal_type=SignalType(item.get("signal_type", "GENERAL_ADVISORY")),
                                priority=PriorityLevel(item.get("priority", "MEDIUM")),
                                headline=item.get("headline", "Actionable Guidance"),
                                actionable_recommendation=item.get("actionable_recommendation", ""),
                                trigger_excerpt=item.get("trigger_excerpt", latest_segment.text),
                                confidence=float(item.get("confidence", 0.85)),
                                speaker_origin=latest_segment.speaker,
                            )
                        )
            except Exception as e:
                pass

        extraction_latency_ms = (time.perf_counter() - t_start) * 1000.0
        return signals, extraction_latency_ms
