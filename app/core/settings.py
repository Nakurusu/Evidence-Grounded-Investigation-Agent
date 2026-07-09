from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    UPLOAD_DIR: str = "uploads"

    # LLM / narrative generation
    LLM_MODE: str = "mock"
    """Provider mode for narrative generation.

    Supported values:
    - "mock"       → MockNarrativeGenerator (deterministic, no API calls)
    - "anthropic"  → (future) AnthropicNarrativeGenerator
    - "openai"     → (future) OpenAINarrativeGenerator
    """

    model_config = ConfigDict(
        env_file=".env"
    )

settings = Settings()