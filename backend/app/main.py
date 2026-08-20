import sys
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import base64
from fastapi import FastAPI, UploadFile, File, Form, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.app.q1_voice_agent.agent import VoiceAgent
from backend.app.q1_voice_agent.groq_service import GroqService
from backend.app.q1_voice_agent.tts_engine import TTSEngine
from backend.app.q2_knowledge_base.indexer import KnowledgeIndexer
from backend.app.q2_knowledge_base.retriever import HybridRetriever
from backend.app.q2_knowledge_base.chunker import MarkdownChunker
from backend.app.q2_knowledge_base.schema import KnowledgeRecord
from backend.app.config import (
    PROJECT_ROOT,
    VECTOR_DB_DIR,
    CLEANED_KB_DIR,
    EVALUATION_DIR,
    RECORDINGS_DIR,
    HYBRID_DENSE_WEIGHT,
    CONFIDENCE_THRESHOLD,
)

app = FastAPI(
    title="Darwix AI - Production Voice Agent & Knowledge Base",
    description="Knowledge-Grounded Voice Agent & RAG Pipeline for SME Business Lending",
    version="1.0.0",
)

# CORS middleware for local web testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Singleton Services (Starts with empty Knowledge Base by default)
print("[FastAPI] Initializing empty Knowledge Base Retriever and Voice Agent...", flush=True)
indexer = KnowledgeIndexer()
# Knowledge base starts clean and empty until user clicks a bank preset or uploads a document
retriever = HybridRetriever(indexer, dense_weight=HYBRID_DENSE_WEIGHT, confidence_threshold=CONFIDENCE_THRESHOLD)
groq_service = GroqService()
voice_agent = VoiceAgent(retriever=retriever, groq_service=groq_service)
current_active_source = "None (Empty)"


# --- REQUEST & RESPONSE SCHEMAS ---
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"


class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 3


# --- REST API ENDPOINTS ---

@app.get("/api/v1/health")
def health_check():
    return {
        "status": "healthy",
        "knowledge_records_indexed": len(indexer.records) if indexer.records else 0,
        "groq_api_active": groq_service.client is not None,
    }


@app.post("/api/v1/voice/greet")
def get_voice_greeting():
    """Initializes a new call session and returns the agent opening greeting."""
    voice_agent.reset_session()
    return voice_agent.get_greeting()


@app.post("/api/v1/voice/chat")
def process_voice_chat(req: ChatRequest):
    """Processes a conversational turn and returns text, audio, state, citations, and CRM lead."""
    return voice_agent.interact(req.message)


@app.post("/api/v1/voice/transcribe")
async def transcribe_audio_file(file: UploadFile = File(...)):
    """Transcribes an uploaded voice audio clip using Groq Whisper."""
    audio_bytes = await file.read()
    transcription = groq_service.transcribe_audio(audio_bytes, filename=file.filename or "audio.wav")
    return {"transcription": transcription}


@app.post("/api/v1/kb/ingest-preset")
def ingest_dataset_preset(preset_req: Dict[str, str]):
    """Ingests a predefined dataset preset ('default', 'hdfc', or 'sbi') and hot-reloads the retriever."""
    global indexer, retriever, voice_agent, current_active_source
    preset = preset_req.get("preset", "default").lower()

    if preset == "hdfc":
        input_dir = PROJECT_ROOT / "test_data_banks" / "hdfc"
        current_active_source = "HDFC Bank"
    elif preset == "sbi":
        input_dir = PROJECT_ROOT / "test_data_banks" / "sbi"
        current_active_source = "SBI Bank"
    else:
        input_dir = PROJECT_ROOT / "data" / "default_knowledge"
        current_active_source = "Default MSME Rules"

    cleaned_json = CLEANED_KB_DIR / "knowledge_records.json"
    chunker = MarkdownChunker()
    records = chunker.process_directory(input_dir, output_json=cleaned_json)

    if not indexer:
        indexer = KnowledgeIndexer()
    indexer.build_indices(records)
    indexer.save_indices(VECTOR_DB_DIR)

    retriever = HybridRetriever(indexer, dense_weight=HYBRID_DENSE_WEIGHT, confidence_threshold=CONFIDENCE_THRESHOLD)
    voice_agent = VoiceAgent(retriever=retriever, groq_service=groq_service)

    return {
        "status": "success",
        "preset": preset,
        "source_dir": str(input_dir.name),
        "total_records": len(records),
        "pii_redacted_records": sum(1 for r in records if r.has_pii),
    }


@app.post("/api/v1/kb/upload-file")
async def upload_and_ingest_document(file: UploadFile = File(...)):
    """Uploads any heterogeneous business document (PDF, CSV, HTML, TXT, MD), parses, cleans, scrubs PII, and re-indexes."""
    global indexer, retriever, voice_agent, current_active_source
    upload_dir = PROJECT_ROOT / "data" / "uploaded_documents"
    upload_dir.mkdir(parents=True, exist_ok=True)

    dest_file = upload_dir / file.filename
    content_bytes = await file.read()
    dest_file.write_bytes(content_bytes)

    chunker = MarkdownChunker()
    new_records = chunker.process_file(dest_file)

    if not new_records:
        return {"status": "error", "message": f"Could not extract valid text chunks from {file.filename}."}

    # Build index EXCLUSIVELY for the uploaded document (no other bank data)
    cleaned_json = CLEANED_KB_DIR / "knowledge_records.json"
    CLEANED_KB_DIR.mkdir(parents=True, exist_ok=True)
    with open(cleaned_json, "w", encoding="utf-8") as f:
        json.dump([r.model_dump() for r in new_records], f, indent=2)

    if not indexer:
        indexer = KnowledgeIndexer()
    indexer.build_indices(new_records)
    indexer.save_indices(VECTOR_DB_DIR)

    current_active_source = file.filename
    retriever = HybridRetriever(indexer, dense_weight=HYBRID_DENSE_WEIGHT, confidence_threshold=CONFIDENCE_THRESHOLD)
    voice_agent = VoiceAgent(retriever=retriever, groq_service=groq_service)

    return {
        "status": "success",
        "filename": file.filename,
        "new_chunks_added": len(new_records),
        "total_active_chunks": len(new_records),
        "pii_redacted_records": sum(1 for r in new_records if r.has_pii),
        "sample_chunk_id": new_records[0].record_id if new_records else None,
    }


@app.post("/api/v1/kb/search")
def search_knowledge_base(req: SearchRequest):
    """Executes hybrid dense + sparse retrieval with citations and confidence scores."""
    if not indexer or not indexer.records:
        return {
            "query": req.query,
            "is_supported": False,
            "explanation": "Knowledge base is currently empty. Please select a knowledge preset or upload a custom document to begin searching.",
            "results": [],
        }
    is_supported, results, explanation = retriever.grounded_retrieval(req.query, top_k=req.top_k)
    return {
        "query": req.query,
        "is_supported": is_supported,
        "explanation": explanation,
        "results": [r.model_dump() for r in results],
    }


@app.get("/api/v1/kb/status")
def get_kb_status():
    """Returns active knowledge base status and chunk count."""
    count = len(indexer.records) if (indexer and indexer.records) else 0
    return {
        "active_records": count,
        "source": current_active_source if count > 0 else "Empty",
        "is_empty": count == 0,
    }


@app.get("/api/v1/kb/records")
def get_all_kb_records():
    """Returns all structured knowledge records with PII audit status."""
    kb_file = CLEANED_KB_DIR / "knowledge_records.json"
    if kb_file.exists():
        with open(kb_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


@app.get("/api/v1/crm/leads")
def get_crm_leads():
    """Returns all captured CRM qualification leads and full transcripts."""
    leads_file = RECORDINGS_DIR / "crm_leads.json"
    if leads_file.exists():
        with open(leads_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


@app.get("/api/v1/evaluations/q2")
def get_q2_retrieval_report():
    """Returns the formal Q2 retrieval benchmark evaluation report."""
    report_file = EVALUATION_DIR / "q2_retrieval_report.json"
    if report_file.exists():
        with open(report_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


@app.get("/api/v1/transcripts/q1")
def get_q1_call_transcripts():
    """Returns all recorded test call transcripts for Question 1."""
    transcripts_file = RECORDINGS_DIR / "q1_call_transcripts.json"
    if transcripts_file.exists():
        with open(transcripts_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


# Include Question 3 Multilingual Bots Router
from backend.app.q3_multilingual_bots.routes import router as q3_router
app.include_router(q3_router)

# Include Question 4 Real-Time Nudges Router
from backend.app.q4_realtime_nudges.routes import q4_router
app.include_router(q4_router)

# Mount static frontend directory
frontend_dir = PROJECT_ROOT / "frontend"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")

