from hmac import new
from typing import Any, Dict, List, Optional
from torch import norm
from transformers.pipelines import pipeline
from transformers.pipelines.base import Pipeline
from app.agents.base import BaseAgent, AgentOutput, AgentResponse
from app.config import settings
import logging  # Import logging

logger = logging.getLogger(__name__)  # Initialize logger


class HateSpeechAgent(BaseAgent):
    """Agent for hate speech detection using a HuggingFace pipeline."""

    def __init__(self, model_id: str = settings.HATE_SPEECH_MODEL_ID):
        super().__init__(model_id)
        self.pipeline: Pipeline = self._load_pipeline()  # Initialize pipeline attribute

    def _load_pipeline(self) -> Pipeline:
        """Loads the text-classification pipeline for hate speech."""
        # Ensure the task is appropriate for the model
        return pipeline("text-classification", model=self.model_id, top_k=None, token=settings.HF_API_KEY)  # Pass token

    def predict(self, text: str) -> AgentResponse:
        """Runs the hate speech classification pipeline and normalizes the output."""
        try:
            raw_results: Any = self.pipeline(text)
        except Exception as e:
            logger.error(f"Pipeline prediction failed for model {self.model_id}: {e}")
            return AgentResponse(label="ERROR", confidence=0.0)

        # The pipeline might return List[List[Dict]] or List[Dict]
        if not raw_results:
            logger.warning(f"Pipeline returned empty results for input: {text[:50]}...")
            return AgentResponse(label="NO_RESULT", confidence=0.0)

        # Now prediction_input should be List[Dict] or similar structure normalize_output expects
        normalized: Optional[AgentOutput] = self.normalize_output(list(raw_results)[0])

        if normalized:
            return AgentResponse(label=normalized.label, confidence=normalized.score)
        else:
            logger.warning(f"Normalization failed for input: {text[:50]}... Output: {list(raw_results)[0]}")
            return AgentResponse(label="NORMALIZATION_FAILED", confidence=0.0)

    def normalize_output(self, prediction: list[dict]) -> Optional[AgentOutput]:
        """Normalizes the raw pipeline output. Finds the highest scoring label."""
        score = 0.0
        normalized_label = "hate_speech"
        temp_label = "UNKNOWN"

        # find the label with the highest score
        for result in prediction:
            label = str(result.get("label", "UNKNOWN")).lower()
            new_score = float(result.get("score", 0.0))

            if new_score > score:
                score = new_score
                temp_label = label.replace(" ", "_")  # Normalize label to a consistent format

        if temp_label == "nothate":
            score = 1 - score

        return AgentOutput(label=normalized_label, score=score)

    def get_metadata(self) -> Dict[str, str]:
        """Returns metadata specific to the hate speech agent."""
        base_meta = super().get_metadata()
        # Ensure base_meta is a dict, although super() should return one
        if not isinstance(base_meta, dict):
            logger.error(f"BaseAgent.get_metadata() returned non-dict: {type(base_meta)}")
            base_meta = {}  # Fallback to empty dict
        base_meta["task"] = "hate_speech"
        base_meta["description"] = "Detects hate speech or offensive language."
        return base_meta  # Explicitly return
