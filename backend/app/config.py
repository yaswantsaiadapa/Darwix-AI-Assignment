"""
Global App Configuration
Loads environment variables and sets defaults for Groq API, models, and paths.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_KNOWLEDGE_DIR = DATA_DIR / "default_knowledge"
TEST_DATA_BANKS_DIR = PROJECT_ROOT / "test_data_banks"
CLEANED_KB_DIR = DATA_DIR / "cleaned_kb"
VECTOR_DB_DIR = DATA_DIR / "vector_db"
AUDIO_SAMPLES_DIR = DATA_DIR / "audio_samples"
EVALUATION_DIR = PROJECT_ROOT / "evaluation"
RECORDINGS_DIR = PROJECT_ROOT / "recordings_and_transcripts"

# Groq API Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_LLM_MODEL = os.getenv("GROQ_LLM_MODEL", "openai/gpt-oss-120b")
GROQ_WHISPER_MODEL = os.getenv("GROQ_WHISPER_MODEL", "whisper-large-v3")

# Retrieval & Grounding Thresholds
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.55"))
HYBRID_DENSE_WEIGHT = float(os.getenv("HYBRID_DENSE_WEIGHT", "0.70"))

# TTS Voice Settings
DEFAULT_TTS_VOICE = os.getenv("DEFAULT_TTS_VOICE", "en-US-AriaNeural")
