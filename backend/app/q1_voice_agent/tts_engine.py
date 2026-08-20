"""
Text-to-Speech (TTS) Engine for Question 1 & Question 3
Uses Edge-TTS for high-quality Microsoft Neural Voice synthesis without requiring API keys.
"""

import asyncio
import io
from pathlib import Path
from typing import Optional
import edge_tts
from backend.app.config import DEFAULT_TTS_VOICE


class TTSEngine:
    """
    Synthesizes conversational voice responses to MP3 audio buffers.
    Supports English, Filipino/Tagalog, and Indonesian voices.
    """

    VOICES = {
        "en": "en-US-AriaNeural",
        "en_male": "en-US-GuyNeural",
        "ph": "fil-PH-BlessicaNeural",
        "ph_male": "fil-PH-AngeloNeural",
        "id": "id-ID-GadisNeural",
        "id_male": "id-ID-ArdiNeural",
    }

    @classmethod
    async def synthesize_to_bytes_async(cls, text: str, voice: str = None) -> bytes:
        """
        Synthesizes text into MP3 audio bytes asynchronously with timeout.
        """
        selected_voice = voice or DEFAULT_TTS_VOICE
        try:
            communicate = edge_tts.Communicate(text, selected_voice)
            audio_buffer = io.BytesIO()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_buffer.write(chunk["data"])
            audio_buffer.seek(0)
            return audio_buffer.read()
        except Exception as e:
            return b""

    @classmethod
    def synthesize_to_bytes(cls, text: str, voice: str = None, timeout: float = 3.0) -> bytes:
        """
        Synchronous wrapper for synthesize_to_bytes_async with strict timeout.
        """
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            task = cls.synthesize_to_bytes_async(text, voice)
            return loop.run_until_complete(asyncio.wait_for(task, timeout=timeout))
        except Exception:
            return b""

    @classmethod
    async def synthesize_to_file_async(cls, text: str, output_file: Path, voice: str = None) -> Path:
        """
        Synthesizes text and saves to an MP3 file on disk.
        """
        output_file.parent.mkdir(parents=True, exist_ok=True)
        selected_voice = voice or DEFAULT_TTS_VOICE
        try:
            communicate = edge_tts.Communicate(text, selected_voice)
            await communicate.save(str(output_file))
            return output_file
        except Exception as e:
            print(f"[TTSEngine Warning] Edge-TTS file save failed: {e}")
            return output_file
