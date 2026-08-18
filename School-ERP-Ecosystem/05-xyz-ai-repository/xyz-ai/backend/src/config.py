import os
import warnings
from typing import List
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

# Load .env file if it exists (for local development)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class Settings(BaseSettings):
    model_config = ConfigDict(case_sensitive=True, extra="allow")
    
    PROJECT_NAME: str = "XYZ AI — Human-Like School Assistant"
    API_V1_STR: str = "/api/v1"

    # JWT Secret — NEVER hardcoded; fail loudly if missing in non-dev
    SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    DEFAULT_SUPABASE_URL: str = "postgresql://postgres.eskgeukkkllczotrowtj:V%24AM%24RT8J%2457he%21@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres"
    DATABASE_URL: str = os.getenv("DATABASE_URL") or (
        "sqlite:///./school_erp.db" if (os.getenv("PYTEST_CURRENT_TEST") or os.getenv("CI")) else "postgresql://postgres.eskgeukkkllczotrowtj:V%24AM%24RT8J%2457he%21@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres"
    )

    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # LLM Provider Keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_RPM", "60"))
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        o.strip() for o in os.getenv("ALLOWED_ORIGINS", "*").split(",")
    ]

    @property
    def nlu_mode(self) -> str:
        if self.OPENAI_API_KEY or self.GEMINI_API_KEY or self.ANTHROPIC_API_KEY:
            return "llm"
        return "keyword_fallback"

settings = Settings()

# --- Startup validation ---
_is_test = os.getenv("PYTEST_CURRENT_TEST") is not None
_is_ci = os.getenv("CI") is not None

if not settings.SECRET_KEY and not _is_test and not _is_ci:
    # Generate a temporary random key for local dev, but warn loudly
    import secrets
    settings.SECRET_KEY = secrets.token_hex(32)
    warnings.warn(
        "[SECURITY WARNING] JWT_SECRET_KEY is not set. A random temporary key has been "
        "generated for this session only. Set JWT_SECRET_KEY in your .env for persistent security.",
        RuntimeWarning,
        stacklevel=2
    )
elif not settings.SECRET_KEY and _is_test:
    # Stable test key for repeatable pytest runs
    settings.SECRET_KEY = "test-only-static-secret-key-for-pytest-runs"

if settings.nlu_mode == "keyword_fallback":
    print(
        "[WARNING] No LLM API key configured — running in degraded keyword-matching mode. "
        "Natural language understanding will be significantly limited. "
        "Set OPENAI_API_KEY, GEMINI_API_KEY, or ANTHROPIC_API_KEY in .env to enable real NLU."
    )
