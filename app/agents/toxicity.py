from typing import Any, Dict, List, Optional  # Add Optional
from transformers.pipelines import pipeline
from transformers.pipelines.base import Pipeline  # Correct import
from app.agents.base import AgentResponse, BaseAgent, AgentOutput
from app.config import settings
import logging  # Import logging

logger = logging.getLogger(__name__)  # Initialize logger

class ToxicityAgent(BaseAgent):
    """Agent for toxicity detection using a HuggingFace pipeline."""

    def __init__(self, model_id: str = settings.TOXICITY_MODEL_ID):
        super().__init__(model_id)
        self.pipeline: Pipeline = self._load_pipeline()  # Initialize pipeline

    def _load_pipeline(self) -> Pipeline:
        """Loads the text-classification pipeline for toxicity."""
        # Note: Some toxicity models might need specific pipeline tasks or configurations.
        # Adjust task if needed based on the chosen model.
        return pipeline("text-classification", model=self.model_id, token=settings.HF_API_KEY)  # Pass token

    def predict(self, text: str) -> AgentResponse:
        """Runs the toxicity classification pipeline and normalizes the output."""
        try:
            # Toxicity pipelines often return List[Dict] or List[List[Dict]]
            raw_results = self.pipeline(text)
        except Exception as e:
            logger.error(f"Toxicity pipeline prediction failed for model {self.model_id}: {e}")
            return AgentResponse(label="ERROR", confidence=0.0)

        if not raw_results:
            logger.warning(f"Toxicity pipeline returned empty results for input: {text[:50]}...")
            return AgentResponse(label="NO_RESULT", confidence=0.0)

        # Now prediction_input should be List[Dict]
        normalized: Optional[AgentOutput] = self.normalize_output(list(raw_results))

        if normalized:
            # Use the normalized label and score for the final response
            return AgentResponse(label=normalized.label, confidence=normalized.score)
        else:
            logger.warning(f"Toxicity normalization failed for input: {text[:50]}... Output: {list(raw_results)}")
            # If normalization fails, it might mean no toxic label was found or an error occurred
            # Return 'not_toxic' or a specific error label depending on desired behavior
            return AgentResponse(label="NOT_TOXIC", confidence=0.0)  # Default to not_toxic if normalization fails

    def normalize_output(self, prediction: Any) -> Optional[AgentOutput]:  # Change input type to Any, return Optional
        """Normalizes the raw pipeline output. Finds the highest scoring toxic label."""
        score = 0.0
        normalized_label = "toxic"
        temp_label = "UNKNOWN"

        # find the label with the highest score
        for result in prediction:
            label = str(result.get("label", "UNKNOWN")).lower()
            new_score = float(result.get("score", 0.0))

            if new_score > score:
                score = new_score
                temp_label = label.replace(" ", "_")  # Normalize label to a consistent format

        if temp_label in "neutral":
            score = 1 - score

        return AgentOutput(label=normalized_label, score=score)

    def get_metadata(self) -> Dict[str, str]:
        """Returns metadata specific to the toxicity agent."""
        base_meta = super().get_metadata()
        base_meta["task"] = "toxicity"
        base_meta["description"] = "Detects toxic or inflammatory language."
        return base_meta
