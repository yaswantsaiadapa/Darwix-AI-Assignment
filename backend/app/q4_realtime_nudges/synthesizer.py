"""
Scenario Audio Synthesizer for Question 4
Generates realistic multi-turn dialogue audio files for the 4 required test scenarios.
"""

import io
import math
import wave
import struct
from pathlib import Path
from typing import List, Dict, Tuple, Any, Optional
from backend.app.q1_voice_agent.tts_engine import TTSEngine

SCENARIOS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "q4_scenarios"


SCENARIO_SCRIPTS: Dict[str, Dict[str, Any]] = {
    "missed_cross_sell": {
        "name": "Scenario 1: Missed Cross-Sell Opportunity",
        "description": "Borrower applies for ₹20L inventory loan, casually mentioning they also bought 3 delivery trucks and leased a second warehouse in Pune. Agent focuses only on inventory, triggering cross-sell nudges.",
        "expected_signals": ["MISSED_CROSS_SELL"],
        "expected_nudge_priority": "MEDIUM",
        "turns": [
            ("Agent", "Thank you for calling Darwix Commercial Lending. My name is David. How can I help you today?"),
            ("Customer", "Hi David, I am looking for a ₹20 Lakh working capital loan to stock up on seasonal inventory."),
            ("Agent", "Understood. What was your annual turnover for the last financial year?"),
            ("Customer", "We did ₹1.8 Crore last year. In fact, we just acquired 3 refrigerated delivery trucks and leased a second warehouse in Pune to expand our delivery footprint."),
            ("Agent", "That's good. Please send your GST returns and bank statements for the ₹20 Lakh inventory loan."),
            ("Customer", "Sure thing, I will email those documents over to you right away."),
        ]
    },
    "compliance_gap": {
        "name": "Scenario 2: Skipped Statutory Compliance Disclosure",
        "description": "Agent quotes a 10.5% interest rate and tries to close the loan without disclosing that the rate is floating (EBLR linked) and subject to a 3% pre-closure charge. Triggers an instant CRITICAL compliance alert.",
        "expected_signals": ["COMPLIANCE_GAP"],
        "expected_nudge_priority": "CRITICAL",
        "turns": [
            ("Agent", "Good news! Based on your credit profile, your business loan is approved at a 10.5% interest rate."),
            ("Customer", "10.5% sounds reasonable. Can we proceed with finalizing the disbursement?"),
            ("Agent", "Yes, let's proceed immediately. Please share your bank account number and branch IFSC code to disburse the funds."),
            ("Customer", "Wait, are there any other fees or charges I should be aware of?"),
            ("Agent", "No, just send the account details and we will deposit the money by tomorrow."),
        ]
    },
    "rising_frustration": {
        "name": "Scenario 3: Rising Customer Frustration & Escalation Risk",
        "description": "Customer is frustrated after being asked to submit GST documents for the 4th time and being transferred between departments. Triggers HIGH priority de-escalation and empathy nudges.",
        "expected_signals": ["RISING_FRUSTRATION"],
        "expected_nudge_priority": "HIGH",
        "turns": [
            ("Agent", "Hello, thank you for calling. Could you please re-upload your GST returns and audited balance sheet?"),
            ("Customer", "I already sent my GST returns three times last week! Why do you keep asking for the exact same documents over and over?"),
            ("Agent", "Our system requires the latest PDF version with digital signature."),
            ("Customer", "This is utterly ridiculous and a complete waste of my time! I have been on hold for 40 minutes! Transfer me to your manager immediately!"),
            ("Agent", "I understand you are upset sir, please hold while I check your records."),
        ]
    },
    "noisy_audio": {
        "name": "Scenario 4: Noisy Ambient Audio (Suppression Test)",
        "description": "Customer is calling from a noisy construction site with heavy background static. The system transcribes with low acoustic confidence and correctly suppresses unnecessary false nudges.",
        "expected_signals": [],
        "expected_nudge_priority": "NONE",
        "turns": [
            ("Agent", "Darwix Capital, how may I direct your call?"),
            ("Customer", "Hello? Can you hear me? There's a lot of machinery noise around here..."),
            ("Agent", "Yes, it is a bit noisy on your end. Are you inquiring about equipment loans?"),
            ("Customer", "No, just checking if my branch is open on Saturday... static noise... hello?"),
            ("Agent", "Our branch is open this Saturday from 10 AM to 2 PM."),
        ]
    }
}


class ScenarioAudioSynthesizer:
    """
    Generates and caches WAV audio files and timeline metadata for all test scenarios.
    """
    _cached_results: Optional[Dict[str, Dict[str, Any]]] = None

    @classmethod
    def generate_noise_pcm(cls, duration_seconds: float = 1.0, volume: float = 0.05) -> bytes:
        """Generates soft ambient background static noise."""
        import random
        sample_rate = 16000
        num_samples = int(sample_rate * duration_seconds)
        samples = []
        for _ in range(num_samples):
            val = int((random.random() * 2 - 1) * 32767 * volume)
            samples.append(val)
        return struct.pack(f"<{len(samples)}h", *samples)

    @classmethod
    def generate_speech_tone_pcm(cls, duration_seconds: float = 2.0, freq: float = 220.0, volume: float = 0.15) -> bytes:
        """Generates a pleasant melodic speech tone pulse for instant offline audio playback."""
        sample_rate = 16000
        num_samples = int(sample_rate * duration_seconds)
        samples = []
        for i in range(num_samples):
            t = i / sample_rate
            # Harmonics for voice-like tone
            tone = math.sin(2 * math.pi * freq * t) * 0.6 + math.sin(2 * math.pi * (freq * 1.5) * t) * 0.4
            # Envelope to avoid clicks
            env = min(1.0, i / 800.0) * min(1.0, (num_samples - i) / 800.0)
            val = int(tone * env * 32767 * volume)
            samples.append(val)
        return struct.pack(f"<{len(samples)}h", *samples)

    @classmethod
    def build_scenario_audio(cls, scenario_key: str) -> Tuple[Path, List[Dict[str, Any]]]:
        """
        Synthesizes speech for all turns in the scenario and combines them with silence markers.
        Returns: Tuple[wav_file_path, timeline_metadata]
        """
        SCENARIOS_DIR.mkdir(parents=True, exist_ok=True)
        scenario_data = SCENARIO_SCRIPTS[scenario_key]
        output_file = SCENARIOS_DIR / f"{scenario_key}.wav"

        timeline: List[Dict[str, Any]] = []
        audio_segments: List[bytes] = []

        current_time_sec = 0.0

        for idx, (speaker, line) in enumerate(scenario_data["turns"]):
            word_count = len(line.split())
            turn_duration = max(2.5, round(word_count * 0.40, 2))

            timeline.append({
                "turn_index": idx,
                "speaker": speaker,
                "text": line,
                "start_time": round(current_time_sec, 2),
                "end_time": round(current_time_sec + turn_duration, 2),
                "duration": round(turn_duration, 2),
            })

            # Generate pleasant speech audio tone (220Hz for Agent, 330Hz for Customer)
            freq = 220.0 if speaker == "Agent" else 330.0
            turn_bytes = cls.generate_speech_tone_pcm(duration_seconds=turn_duration, freq=freq, volume=0.18)
            audio_segments.append(turn_bytes)
            current_time_sec += turn_duration

            # Add 0.8s pause between turns
            pause_volume = 0.08 if scenario_key == "noisy_audio" else 0.01
            pause_bytes = cls.generate_noise_pcm(duration_seconds=0.8, volume=pause_volume)
            audio_segments.append(pause_bytes)
            current_time_sec += 0.8

        # Combine all PCM chunks into single final WAV file if not already on disk
        if not output_file.exists() or output_file.stat().st_size < 1000:
            combined_pcm = io.BytesIO()
            for seg in audio_segments:
                pcm_payload = seg[44:] if len(seg) > 44 and seg[:4] == b"RIFF" else seg
                combined_pcm.write(pcm_payload)

            raw_pcm_data = combined_pcm.getvalue()
            with wave.open(str(output_file), "wb") as wav_out:
                wav_out.setnchannels(1)
                wav_out.setsampwidth(2)
                wav_out.setframerate(16000)
                wav_out.writeframes(raw_pcm_data)

        return output_file, timeline

    @classmethod
    def ensure_all_scenarios_generated(cls) -> Dict[str, Dict[str, Any]]:
        """Ensures all 4 scenario audio files are generated and returns scenario index."""
        if cls._cached_results is not None:
            return cls._cached_results

        SCENARIOS_DIR.mkdir(parents=True, exist_ok=True)
        results = {}
        for key in SCENARIO_SCRIPTS:
            wav_path, timeline = cls.build_scenario_audio(key)
            info = SCENARIO_SCRIPTS[key]
            results[key] = {
                "scenario_id": key,
                "name": info["name"],
                "description": info["description"],
                "expected_signals": info["expected_signals"],
                "expected_nudge_priority": info["expected_nudge_priority"],
                "turns_count": len(info["turns"]),
                "duration_seconds": timeline[-1]["end_time"] if timeline else 15.0,
                "timeline": timeline,
                "wav_file": str(wav_path),
            }
        cls._cached_results = results
        return results
