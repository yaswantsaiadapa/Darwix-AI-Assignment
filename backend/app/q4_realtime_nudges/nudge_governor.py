"""
Nudge Governor & Anti-Fatigue Arbiter for Question 4
Enforces confidence gating, duplicate suppression, priority preemption,
cooldown timers, and acoustic noise filtering.
"""

import time
import uuid
from typing import List, Dict, Any, Tuple, Optional
from backend.app.q4_realtime_nudges.models import (
    SignalType,
    PriorityLevel,
    DetectedSignal,
    Nudge,
)


class NudgeGovernor:
    """
    Acts as the safety controller between raw signals and the agent's live screen.
    Eliminates alert fatigue and prevents false-positive distractions.
    """

    def __init__(
        self,
        min_confidence_threshold: float = 0.75,
        duplicate_cooldown_seconds: float = 30.0,
        general_cooldown_seconds: float = 12.0,
    ):
        self.min_confidence_threshold = min_confidence_threshold
        self.duplicate_cooldown_seconds = duplicate_cooldown_seconds
        self.general_cooldown_seconds = general_cooldown_seconds

        # State tracking
        self.last_nudge_dispatched_at: float = 0.0
        self.recent_nudges_history: List[Nudge] = []
        self.active_nudges: List[Nudge] = []
        self.suppression_counts: Dict[str, int] = {
            "LOW_CONFIDENCE": 0,
            "DUPLICATE_ALERT": 0,
            "COOLDOWN_ACTIVE": 0,
            "ACOUSTIC_NOISE": 0,
        }

    def reset(self):
        """Resets governor state for a new call session."""
        self.last_nudge_dispatched_at = 0.0
        self.recent_nudges_history = []
        self.active_nudges = []
        self.suppression_counts = {
            "LOW_CONFIDENCE": 0,
            "DUPLICATE_ALERT": 0,
            "COOLDOWN_ACTIVE": 0,
            "ACOUSTIC_NOISE": 0,
        }

    def process_signals(
        self,
        signals: List[DetectedSignal],
        current_time: float,
        is_noisy_chunk: bool = False,
    ) -> Tuple[List[Nudge], float]:
        """
        Filters raw signals through governor rules and emits approved actionable nudges.
        
        Returns:
            Tuple[List[Nudge], governor_latency_ms]
        """
        t_start = time.perf_counter()
        approved_nudges: List[Nudge] = []

        # Rule 1: Acoustic Noise Filter
        if is_noisy_chunk:
            self.suppression_counts["ACOUSTIC_NOISE"] += len(signals)
            return [], (time.perf_counter() - t_start) * 1000.0

        for sig in signals:
            # Rule 2: Confidence Gate
            if sig.confidence < self.min_confidence_threshold:
                self.suppression_counts["LOW_CONFIDENCE"] += 1
                continue

            # Rule 3: Duplicate Suppression (Check last 30 seconds for same signal type)
            is_duplicate = False
            for recent in self.recent_nudges_history:
                if recent.signal_type == sig.signal_type:
                    if (current_time - recent.created_at) < self.duplicate_cooldown_seconds:
                        is_duplicate = True
                        break

            if is_duplicate:
                self.suppression_counts["DUPLICATE_ALERT"] += 1
                continue

            # Rule 4: Priority Preemption & Cooldown
            # CRITICAL priority (Statutory Compliance breaches) BYPASSES all cooldown timers
            if sig.priority != PriorityLevel.CRITICAL:
                time_since_last = current_time - self.last_nudge_dispatched_at
                if time_since_last < self.general_cooldown_seconds and self.last_nudge_dispatched_at > 0:
                    self.suppression_counts["COOLDOWN_ACTIVE"] += 1
                    continue

            # If CRITICAL compliance alert arrives, preempt/dismiss lower priority cards
            if sig.priority == PriorityLevel.CRITICAL:
                for active in self.active_nudges:
                    if active.priority != PriorityLevel.CRITICAL:
                        active.is_preempted = True

            # Formulate Approved Nudge
            nudge = Nudge(
                nudge_id=f"ndg_{uuid.uuid4().hex[:8]}",
                signal_type=sig.signal_type,
                priority=sig.priority,
                headline=sig.headline,
                actionable_recommendation=sig.actionable_recommendation,
                trigger_excerpt=sig.trigger_excerpt,
                confidence=round(sig.confidence, 2),
                created_at=current_time,
                expires_in_seconds=20 if sig.priority != PriorityLevel.CRITICAL else 45,
            )

            approved_nudges.append(nudge)
            self.recent_nudges_history.append(nudge)
            self.active_nudges.append(nudge)
            self.last_nudge_dispatched_at = current_time

        governor_latency_ms = (time.perf_counter() - t_start) * 1000.0
        return approved_nudges, governor_latency_ms
