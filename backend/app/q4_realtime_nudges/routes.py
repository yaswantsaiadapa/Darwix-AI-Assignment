"""
FastAPI Routes and WebSocket Stream Handler for Question 4
Provides REST endpoints and real-time WebSocket for the Live Agent Assist Cockpit.
"""

import io
import wave
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel

from backend.app.q4_realtime_nudges.models import Speaker
from backend.app.q4_realtime_nudges.synthesizer import (
    ScenarioAudioSynthesizer,
    SCENARIOS_DIR,
    SCENARIO_SCRIPTS,
)
from backend.app.q4_realtime_nudges.session_manager import SessionManager, RealTimeCallSession

q4_router = APIRouter(prefix="/api/v1/q4", tags=["Question 4: Real-Time Nudges"])


class ChunkProcessRequest(BaseModel):
    session_id: str
    chunk_index: int
    speaker: str
    text: str
    start_time: float
    end_time: float
    is_noisy: bool = False


@q4_router.get("/scenarios")
def list_scenarios():
    """Returns metadata for all 4 required test scenarios."""
    scenarios_data = ScenarioAudioSynthesizer.ensure_all_scenarios_generated()
    return {"scenarios": list(scenarios_data.values())}


@q4_router.get("/audio/{scenario_id}")
def get_scenario_audio(scenario_id: str):
    """Serves the synthesized WAV audio file for live audio playback."""
    audio_path = SCENARIOS_DIR / f"{scenario_id}.wav"
    if not audio_path.exists():
        ScenarioAudioSynthesizer.ensure_all_scenarios_generated()
    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="Scenario audio not found")
    return FileResponse(path=audio_path, media_type="audio/wav", filename=f"{scenario_id}.wav")


@q4_router.post("/process-chunk")
def process_single_chunk(req: ChunkProcessRequest):
    """Processes a single incoming audio chunk synchronously and returns nudges + latency telemetry."""
    session = SessionManager.get_or_create_session(req.session_id)
    speaker = Speaker.AGENT if req.speaker.lower() == "agent" else Speaker.CUSTOMER
    
    # Minimal silent audio byte placeholder for simulated turns
    silent_bytes = ScenarioAudioSynthesizer.generate_noise_pcm(duration_seconds=max(1.0, req.end_time - req.start_time), volume=0.01)

    result = session.process_audio_chunk(
        chunk_bytes=silent_bytes,
        chunk_index=req.chunk_index,
        start_time=req.start_time,
        end_time=req.end_time,
        inferred_speaker=speaker,
        fallback_text=req.text,
        is_noisy=req.is_noisy,
    )
    return result


@q4_router.get("/telemetry/{session_id}")
def get_session_telemetry(session_id: str):
    """Returns the P50/P95 latency report and false-positive filter summary for the session."""
    session = SessionManager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session.get_telemetry_report()


@q4_router.post("/reset/{session_id}")
def reset_session(session_id: str):
    """Resets an active session state."""
    if session_id in SessionManager._sessions:
        del SessionManager._sessions[session_id]
    return {"status": "reset_successful", "session_id": session_id}


# --- WEBSOCKET REAL-TIME STREAMING ENDPOINT ---

@q4_router.websocket("/ws/stream/{session_id}")
async def websocket_stream_endpoint(websocket: WebSocket, session_id: str):
    """
    Bi-directional WebSocket for real-time live streaming audio chunks,
    live transcript emission, and instantaneous push of approved agent nudges.
    """
    await websocket.accept()
    session = SessionManager.get_or_create_session(session_id)

    try:
        while True:
            raw_msg = await websocket.receive_text()
            data = json.loads(raw_msg)
            msg_type = data.get("type", "chunk")

            if msg_type == "chunk":
                chunk_idx = int(data.get("chunk_index", 0))
                speaker_str = data.get("speaker", "Customer")
                text = data.get("text", "")
                start_t = float(data.get("start_time", 0.0))
                end_t = float(data.get("end_time", start_t + 2.5))
                is_noisy = bool(data.get("is_noisy", False))

                speaker = Speaker.AGENT if speaker_str.lower() == "agent" else Speaker.CUSTOMER
                dummy_pcm = ScenarioAudioSynthesizer.generate_noise_pcm(duration_seconds=max(1.0, end_t - start_t), volume=0.01)

                chunk_result = session.process_audio_chunk(
                    chunk_bytes=dummy_pcm,
                    chunk_index=chunk_idx,
                    start_time=start_t,
                    end_time=end_t,
                    inferred_speaker=speaker,
                    fallback_text=text,
                    is_noisy=is_noisy,
                )

                # Push real-time event back over WebSocket
                await websocket.send_text(json.dumps({
                    "event": "CHUNK_PROCESSED",
                    "data": chunk_result,
                }))

            elif msg_type == "reset":
                session = SessionManager.get_or_create_session(session_id)
                session.governor.reset()
                await websocket.send_text(json.dumps({
                    "event": "SESSION_RESET",
                    "session_id": session_id,
                }))

    except WebSocketDisconnect:
        print(f"[WebSocket] Client disconnected from session: {session_id}")
    except Exception as e:
        print(f"[WebSocket Error] Error in stream session {session_id}: {e}")
        try:
            await websocket.close()
        except Exception:
            pass
