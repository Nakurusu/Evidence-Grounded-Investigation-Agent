from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    UPLOAD_DIR: str = "uploads"

    # LLM / narrative generation
    LLM_MODE: str = "mock"
    """Provider mode for narrative generation.

    Supported values:
    - "mock"   → MockNarrativeGenerator (deterministic, no API calls)
    - "openai" → LLMNarrativeGenerator (OpenAI-compatible API)
    """

    LLM_API_KEY: str = ""
    """API key for the LLM provider.  Required when LLM_MODE='openai'."""

    LLM_BASE_URL: str = "https://api.openai.com/v1"
    """Base URL for the OpenAI-compatible API endpoint.
    Override to use other providers (e.g., 'https://api.anthropic.com/v1'
    via a compatible proxy, or a local model endpoint)."""

    LLM_MODEL: str = "gpt-4o"
    """Model name passed to the API.  Any OpenAI-compatible model works:
    gpt-4o, gpt-4o-mini, claude-sonnet-5 (via proxy), etc."""

    LLM_TIMEOUT_SECONDS: float = 30.0
    """Maximum time to wait for one LLM API request before falling back."""

    LLM_TEMPERATURE: float = 0.3
    """Sampling temperature for narrative generation."""

    LLM_MAX_TOKENS: int = 4096
    """Maximum narrative response size requested from the provider."""

    LLM_MAX_RETRIES: int = 1
    """Retry count for invalid JSON responses."""

    model_config = ConfigDict(
        env_file=".env"
    )

settings = Settings()
