import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
RESEARCH_DIR = PROJECT_ROOT / "research-takeaways"

# Vercel's filesystem is read-only; we copy chroma_db to /tmp at startup.
CHROMA_DIR = Path("/tmp/chroma_db") if os.getenv("VERCEL") else PROJECT_ROOT / "chroma_db"
COLLECTION   = "psychologist_research"

EMBED_MODEL        = "models/gemini-embedding-001"
LLM_PROVIDER       = os.getenv("LLM_PROVIDER", "groq")          # "groq" | "openrouter"
LLM_MODEL          = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
OPENROUTER_MODEL   = os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-120b:free")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
RETRIEVAL_K        = 6

TOPIC_MAP = {
    "Strategic Automaticity_ The Power of If-Then Planning":
        "if-then planning and implementation intentions",
    "The Disciplined Pursuit of Less but Better":
        "essentialism",
    "The Dynamics of Change_ A Behaviour Change Wheel Framework":
        "behaviour change",
    "The Mechanics of Procrastination and Temporal Motivation Theory":
        "procrastination and temporal motivation",
    "The Will to Meaning_ Lessons from Logotherapy":
        "logotherapy and meaning-making",
    "MBTI 16 Personality Types":
        "MBTI personality types and psychologist communication guidance",
}
