from transformers.pipelines import pipeline, Pipeline


class SentimentModel:
    def __init__(self, model_name: str = "distilbert-base-uncased-finetuned-sst-2-english"):
        # initialize HuggingFace pipeline
        self.pipeline: Pipeline = pipeline("sentiment-analysis", model=model_name)

    def predict(self, text: str):
        # return list of predictions
        return self.pipeline(text)


def create_model() -> SentimentModel:
    # factory to create a loaded SentimentModel
    return SentimentModel()
