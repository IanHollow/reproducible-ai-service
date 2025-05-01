from abc import ABC, abstractmethod
from typing import Any, Dict, Optional  # Add Optional
from pydantic import BaseModel  # Moved import to the top


class AgentOutput(BaseModel):
    label: str
    score: float
    # Optional: Add other fields like raw_output if needed


class AgentResponse(BaseModel):
    label: str
    confidence: float


class BaseAgent(ABC):
    """Abstract base class for all content moderation agents."""

    def __init__(self, model_id: str, cache_dir: str | None = None):
        """
        Initializes the agent, potentially loading models.

        Args:
            model_id (str): The HuggingFace model identifier.
            cache_dir (str | None): Optional directory to cache models.
        """
        self.model_id = model_id
        self.cache_dir = cache_dir
        # Model loading logic might go here or be deferred to predict

    @abstractmethod
    def _load_pipeline(self) -> Any:
        """Loads the specific HuggingFace pipeline or model for the agent."""
        pass

    @abstractmethod
    def predict(self, text: str) -> AgentResponse:
        """
        Analyzes the input text and returns a classification label and confidence.

        Args:
            text (str): The input text to analyze.

        Returns:
            AgentResponse: A Pydantic model containing the label and confidence score.
        """
        pass

    @abstractmethod
    def normalize_output(
        self, prediction: list[dict]
    ) -> Optional[AgentOutput]:  # Change input type to Any, return Optional
        """Normalizes the raw model output to a common AgentOutput format."""
        pass

    def health_check(self) -> bool:
        """Basic health check to see if the pipeline is loaded."""
        try:
            # Simple check: run predict on a dummy string
            self.predict("health check")
            return True
        except Exception:
            return False

    def get_metadata(self) -> Dict[str, str]:
        """Returns metadata about the agent."""
        return {"model_id": self.model_id, "agent_type": self.__class__.__name__}

    def __repr__(self):
        return f"{self.__class__.__name__}(model_id='{self.model_id}')"
