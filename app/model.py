from transformers.pipelines import pipeline
from transformers.pipelines.base import Pipeline
from app.config import settings  # Import settings


class SentimentModel:

    def __init__(self, model_name: str):
        # initialize HuggingFace pipeline
        self.pipeline: Pipeline = pipeline("sentiment-analysis", model=model_name)

    def predict(self, text: str):
        # return list of predictions
        return self.pipeline(text)


def create_model(model_name: str = settings.MODEL_NAME) -> SentimentModel:
    # factory to create a loaded SentimentModel
    return SentimentModel(model_name=model_name)
