import os
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

# Search for .env in current directory and parent directory
env_path = Path(__file__).resolve().parent.parent / ".env"
if not env_path.exists():
    env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

class Settings(BaseModel):
    # graph8
    GRAPH8_API_KEY: str = os.getenv("GRAPH8_API_KEY", "")
    GRAPH8_BASE_URL: str = os.getenv("GRAPH8_BASE_URL", "https://be.graph8.com/api/v1")
    GRAPH8_WEBHOOK_SECRET: str = os.getenv("GRAPH8_WEBHOOK_SECRET", "mock_webhook_secret_graph8")
    
    # LLM (Groq OpenAI-compatible by default)
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
    
    # Supabase / DB
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    
    # Webhooks & Server
    WEBHOOK_BASE_URL: str = os.getenv("WEBHOOK_BASE_URL", "http://localhost:8000")
    PORT: int = int(os.getenv("PORT", "8000"))
    HOST: str = os.getenv("HOST", "0.0.0.0")
    
    # Features & Dev
    SIMULATION_MODE: bool = os.getenv("SIMULATION_MODE", "true").lower() in ("true", "1", "yes")
    VOICE_ESCALATION_ENABLED: bool = os.getenv("VOICE_ESCALATION_ENABLED", "false").lower() in ("true", "1", "yes")
    DEFAULT_USER_ID: str = "00000000-0000-0000-0000-000000000001"

settings = Settings()
