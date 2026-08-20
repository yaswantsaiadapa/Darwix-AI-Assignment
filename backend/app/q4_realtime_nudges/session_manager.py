"""
Real-Time Call Session Manager & Telemetry Profiler for Question 4
Manages continuous chunk streams, rolling context buffers, and computes P50/P95 latency percentiles.
"""

import time
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from backend.app.q4_realtime_nudges.models import (
    Speaker,
    TranscriptSegment,
    DetectedSignal,
    Nudge,
    LatencyRecord,
    TelemetryReport,
)
from backend.app.q4_realtime_nudges.asr_streamer import StreamingASR
from backend.app.q4_realtime_nudges.signal_extractor import RealTimeSignalExtractor
from backend.app.q4_realtime_nudges.nudge_governor import NudgeGovernor


class RealTimeCallSession:
    """
    Coordinates an active streaming call session, rolling transcript buffer,
    signal extraction, nudge generation, and latency profiling.
    """

    def __init__(self, session_id: str, scenario_id: Optional[str] = None):
        self.session_id = session_id
        self.scenario_id = scenario_id
        self.created_at = time.time()
        self.is_active = True

        # Pipeline Sub-Components
        self.asr = StreamingASR()
        self.extractor = RealTimeSignalExtractor()
        self.governor = NudgeGovernor()

        # Session Buffers
        self.transcript_segments: List[TranscriptSegment] = []
        self.detected_signals: List[DetectedSignal] = []
        self.nudges: List[Nudge] = []
        self.latency_records: List[LatencyRecord] = []

        # Real-time state
        self.current_simulated_time = 0.0
        self.compliance_violations_prevented = 0
        self.cross_sells_detected = 0

    def process_audio_chunk(
        self,
        chunk_bytes: bytes,
        chunk_index: int,
        start_time: float,
        end_time: float,
        inferred_speaker: Speaker = Speaker.UNKNOWN,
        fallback_text: Optional[str] = None,
        is_noisy: bool = False,
    ) -> Dict[str, Any]:
        """
        Executes the end-to-end real-time processing loop for one audio chunk:
        Audio Chunk -> ASR -> Context Buffer -> Signal Extractor -> Governor -> Latency Profiler
        
        Returns:
            Dictionary with new segment, approved nudges, and latency metrics.
        """
        t_audio_in = time.perf_counter()

        # Step 1: Streaming ASR
        segment, asr_ms = self.asr.transcribe_chunk(
            audio_bytes=chunk_bytes,
            chunk_index=chunk_index,
            start_time=start_time,
            end_time=end_time,
            inferred_speaker=inferred_speaker,
            fallback_text=fallback_text,
        )
        self.transcript_segments.append(segment)
        self.current_simulated_time = end_time

        # Step 2: Signal Extraction over Rolling Context
        signals, signal_ms = self.extractor.extract_signals(
            rolling_transcript=self.transcript_segments,
            latest_segment=segment,
        )
        self.detected_signals.extend(signals)

        # Step 3: Nudge Governor Filtering
        approved_nudges, gov_ms = self.governor.process_signals(
            signals=signals,
            current_time=self.current_simulated_time,
            is_noisy_chunk=is_noisy,
        )
        self.nudges.extend(approved_nudges)

        for n in approved_nudges:
            if n.signal_type.value == "COMPLIANCE_GAP":
                self.compliance_violations_prevented += 1
            elif n.signal_type.value == "MISSED_CROSS_SELL":
                self.cross_sells_detected += 1

        # Step 4: Latency Profiling
        t_total_end = time.perf_counter()
        delivery_ms = 18.0  # WebSocket transport estimate
        total_end_to_end_ms = ((t_total_end - t_audio_in) * 1000.0) + delivery_ms

        rec = LatencyRecord(
            chunk_index=chunk_index,
            audio_received_time=start_time,
            asr_latency_ms=round(asr_ms, 2),
            signal_extraction_latency_ms=round(signal_ms, 2),
            governor_latency_ms=round(gov_ms, 2),
            delivery_latency_ms=delivery_ms,
            total_end_to_end_ms=round(total_end_to_end_ms, 2),
        )
        self.latency_records.append(rec)

        return {
            "session_id": self.session_id,
            "chunk_index": chunk_index,
            "segment": segment.model_dump(),
            "new_nudges": [n.model_dump() for n in approved_nudges],
            "latency": rec.model_dump(),
            "telemetry": self.get_telemetry_report().model_dump(),
        }

    def get_telemetry_report(self) -> TelemetryReport:
        """Computes P50 and P95 latency percentiles over the session."""
        if not self.latency_records:
            return TelemetryReport(
                total_chunks_processed=0,
                total_nudges_generated=0,
                total_nudges_suppressed=0,
                p50_total_latency_ms=0.0,
                p95_total_latency_ms=0.0,
                p50_asr_latency_ms=0.0,
                p95_asr_latency_ms=0.0,
                p50_signal_latency_ms=0.0,
                p95_signal_latency_ms=0.0,
                suppression_reasons=self.governor.suppression_counts,
                compliance_violations_prevented=self.compliance_violations_prevented,
                cross_sell_opportunities_detected=self.cross_sells_detected,
            )

        total_latencies = [r.total_end_to_end_ms for r in self.latency_records]
        asr_latencies = [r.asr_latency_ms for r in self.latency_records]
        signal_latencies = [r.signal_extraction_latency_ms for r in self.latency_records]

        total_suppressed = sum(self.governor.suppression_counts.values())

        return TelemetryReport(
            total_chunks_processed=len(self.latency_records),
            total_nudges_generated=len(self.nudges),
            total_nudges_suppressed=total_suppressed,
            p50_total_latency_ms=round(float(np.percentile(total_latencies, 50)), 2),
            p95_total_latency_ms=round(float(np.percentile(total_latencies, 95)), 2),
            p50_asr_latency_ms=round(float(np.percentile(asr_latencies, 50)), 2),
            p95_asr_latency_ms=round(float(np.percentile(asr_latencies, 95)), 2),
            p50_signal_latency_ms=round(float(np.percentile(signal_latencies, 50)), 2),
            p95_signal_latency_ms=round(float(np.percentile(signal_latencies, 95)), 2),
            suppression_reasons=self.governor.suppression_counts,
            compliance_violations_prevented=self.compliance_violations_prevented,
            cross_sell_opportunities_detected=self.cross_sells_detected,
        )


class SessionManager:
    """Registry and factory for active call sessions."""
    _sessions: Dict[str, RealTimeCallSession] = {}

    @classmethod
    def get_or_create_session(cls, session_id: str, scenario_id: Optional[str] = None) -> RealTimeCallSession:
        if session_id not in cls._sessions:
            cls._sessions[session_id] = RealTimeCallSession(session_id, scenario_id)
        return cls._sessions[session_id]

    @classmethod
    def get_session(cls, session_id: str) -> Optional[RealTimeCallSession]:
        return cls._sessions.get(session_id)
