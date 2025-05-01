from transformers.pipelines import pipeline
from transformers.pipelines.base import Pipeline
from app.config import settings  # Import settings
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import uuid


class SentimentModel:

    def __init__(self, model_name: str):
        # initialize HuggingFace pipeline
        self.pipeline: Pipeline = pipeline("sentiment-analysis", model=model_name)

    def predict(self, text: str):
        # return list of predictions
        return self.pipeline(text)


# --- Agent Input/Output Models ---


class AgentOutput(BaseModel):
    """Standardized output structure for each agent."""

    label: str
    score: float = Field(..., ge=0, le=1)  # Normalized confidence score (REQ-007)


# --- API Request/Response Models ---


class AnalyzeRequest(BaseModel):
    text: str
    # Optional: Add context, user ID, etc. if needed later


class AgentDetail(BaseModel):
    label: str
    score: float


class AnalyzeResponse(BaseModel):
    request_id: uuid.UUID
    decision: str  # e.g., "safe", "flagged", "review"
    reasons: List[str]  # List of agent types that flagged the content (REQ-029)
    details: Dict[str, AgentDetail]  # Per-agent results including explanation (REQ-024)
    latency_ms: float


class AvailableModel(BaseModel):
    model_id: str
    agent_type: str
    task: str
    description: str


class AgentHealth(BaseModel):
    status: bool
    model_id: str


class HealthStatus(BaseModel):
    status: str  # e.g., "ok", "degraded"
    agents: Dict[str, bool]  # Agent name -> health status (True/False)
