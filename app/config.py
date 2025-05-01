import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()


class Settings:
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
    LOG_TO_FILE: bool = os.getenv("LOG_TO_FILE", "True").lower() in (
        "true",
        "1",
        "yes",
    )  # Enable JSONL logging by default (REQ-028)

    # Rate Limiting (REQ-019)
    RATE_LIMIT: str = "100/minute"  # Default rate limit

    # Hugging Face API Key
    HF_API_KEY: str | None = os.getenv("HF_API_KEY", None)

    # Model Configuration
    # NOTE: overwriting these will lead to functions most likely not working
    SENTIMENT_MODEL_ID: str = os.getenv("SENTIMENT_MODEL_ID", "tabularisai/multilingual-sentiment-analysis")
    TOXICITY_MODEL_ID: str = os.getenv(
        "TOXICITY_MODEL_ID", "s-nlp/roberta_toxicity_classifier"
    )  # Default toxicity model
    HATE_SPEECH_MODEL_ID: str = os.getenv(
        "HATE_SPEECH_MODEL_ID", "facebook/roberta-hate-speech-dynabench-r4-target"
    )  # Default hate speech model

    # Optional: Add cache directory for models
    HF_CACHE_DIR: str | None = os.getenv("HF_CACHE_DIR", None)

settings = Settings()
