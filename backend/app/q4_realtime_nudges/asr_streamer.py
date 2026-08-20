"""
Streaming ASR Transcriber with Latency Profiler for Question 4
Transcribes sequential audio chunks via Groq Whisper Large v3 and records chunk-level ASR latency.
"""

import time
import io
import wave
from typing import Dict, Any, Optional, Tuple
from backend.app.q1_voice_agent.groq_service import GroqService
from backend.app.q4_realtime_nudges.models import Speaker, TranscriptSegment


class StreamingASR:
    """
    Continuous streaming ASR processor for 2.0s to 3.0s audio chunks.
    """

    def __init__(self, groq_service: Optional[GroqService] = None):
        self.groq_service = groq_service or GroqService()

    def transcribe_chunk(
        self,
        audio_bytes: bytes,
        chunk_index: int,
        start_time: float,
        end_time: float,
        inferred_speaker: Speaker = Speaker.UNKNOWN,
        fallback_text: Optional[str] = None,
    ) -> Tuple[TranscriptSegment, float]:
        """
        Transcribes an incoming audio chunk and measures the exact ASR latency in milliseconds.
        
        Returns:
            Tuple[TranscriptSegment, asr_latency_ms]
        """
        t_start = time.perf_counter()

        # Wrap raw PCM in minimal WAV header if missing
        if len(audio_bytes) > 0 and audio_bytes[:4] != b"RIFF":
            wav_buf = io.BytesIO()
            with wave.open(wav_buf, "wb") as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(16000)
                w.writeframes(audio_bytes)
            audio_bytes = wav_buf.getvalue()

        transcribed_text = ""
        if fallback_text:
            transcribed_text = fallback_text
        elif self.groq_service and self.groq_service.client and len(audio_bytes) > 1000:
            try:
                transcribed_text = self.groq_service.transcribe_audio(audio_bytes, filename=f"chunk_{chunk_index}.wav")
            except Exception as e:
                print(f"[StreamingASR Warning] Groq Whisper chunk transcription failed: {e}")
                transcribed_text = ""

        asr_latency_ms = (time.perf_counter() - t_start) * 1000.0

        # Heuristic speaker attribution based on conversational flow
        speaker = inferred_speaker
        if speaker == Speaker.UNKNOWN:
            # Simple alternating or keyword-based heuristic
            if any(w in transcribed_text.lower() for w in ["thank you for calling", "good news", "let's proceed", "our system", "darwix"]):
                speaker = Speaker.AGENT
            else:
                speaker = Speaker.CUSTOMER

        segment = TranscriptSegment(
            segment_id=f"seg_{chunk_index:04d}",
            speaker=speaker,
            text=transcribed_text.strip(),
            start_time=start_time,
            end_time=end_time,
            confidence=0.94 if transcribed_text else 0.40,
        )

        return segment, asr_latency_ms
