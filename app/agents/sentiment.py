from cProfile import label
from typing import Any, Dict, List, Optional  # Add Optional
from transformers.pipelines import pipeline
from transformers.pipelines.base import Pipeline
from app.agents.base import AgentResponse, BaseAgent, AgentOutput
from app.config import settings
import logging  # Import logging

logger = logging.getLogger(__name__)  # Initialize logger


class SentimentAgent(BaseAgent):
    """Agent for sentiment analysis using a HuggingFace pipeline."""

    def __init__(self, model_id: str = settings.SENTIMENT_MODEL_ID):  # Use correct setting
        # Default model_id comes from settings if not provided
        super().__init__(model_id)
        self.pipeline: Pipeline = self._load_pipeline()  # Initialize pipeline

    def _load_pipeline(self) -> Pipeline:
        """Loads the sentiment-analysis pipeline."""
        # classes = (Very Negative, Negative, Neutral, Positive, Very Positive)
        return pipeline("text-classification", model=self.model_id, token=settings.HF_API_KEY)

    def predict(self, text: str) -> AgentResponse:
        """Runs the sentiment analysis pipeline and normalizes the output."""
        try:
            # The pipeline usually returns a list containing one dictionary
            raw_results: Any = self.pipeline(text)
        except Exception as e:
            logger.error(f"Sentiment pipeline prediction failed for model {self.model_id}: {e}")
            return AgentResponse(label="ERROR", confidence=0.0)

        # check if the pipeline returned a list of results
        if not raw_results:
            logger.warning(f"Sentiment pipeline returned empty results for input: {text[:50]}...")
            return AgentResponse(label="NO_RESULT", confidence=0.0)

        # Pass the first result dictionary to normalize_output
        normalized: Optional[AgentOutput] = self.normalize_output(list(raw_results))

        if normalized:
            return AgentResponse(label=normalized.label, confidence=normalized.score)
        else:
            logger.warning(f"Sentiment normalization failed for input: {text[:50]}... Output: {list(raw_results)}")
            return AgentResponse(label="NORMALIZATION_FAILED", confidence=0.0)

    def normalize_output(
        self, prediction: list[dict]
    ) -> Optional[AgentOutput]:  # Change input type to Any, return Optional
        """Normalizes the raw pipeline output."""
        score = 0.0
        normalized_label = "negative"
        temp_label = "UNKNOWN"

        # find the label with the highest score
        for result in prediction:
            label = str(result.get("label", "UNKNOWN")).lower()
            new_score = float(result.get("score", 0.0))

            if new_score > score:
                score = new_score
                temp_label = label.replace(" ", "_")  # Normalize label to a consistent format

        if "positive" in temp_label.split("_"):
            score = 1 - score

        if "very" in temp_label.split("_"):
            normalized_label = "very_" + normalized_label

        return AgentOutput(label=normalized_label, score=score)

    def get_metadata(self) -> Dict[str, str]:
        """Returns metadata specific to the sentiment agent."""
        base_meta = super().get_metadata()
        base_meta["task"] = "sentiment"
        base_meta["description"] = "Detects the emotional tone (Positive/Negative) of the text."
        return base_meta
