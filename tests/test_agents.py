import pytest
from app.agents.base import AgentOutput
from app.agents.sentiment import SentimentAgent
from app.agents.toxicity import ToxicityAgent
from app.agents.hate_speech import HateSpeechAgent
from app.config import settings

# --- Fixtures ---


# Use session scope to load models only once per test session
@pytest.fixture(scope="session")
def sentiment_agent():
    return SentimentAgent(model_id=settings.SENTIMENT_MODEL_ID)


@pytest.fixture(scope="session")
def toxicity_agent():
    return ToxicityAgent(model_id=settings.TOXICITY_MODEL_ID)


@pytest.fixture(scope="session")
def hate_speech_agent():
    return HateSpeechAgent(model_id=settings.HATE_SPEECH_MODEL_ID)


# --- Test Cases ---


# Sentiment Agent Tests
def test_sentiment_agent_predict(sentiment_agent):
    """Test SentimentAgent predict method returns expected format."""
    text = "This is a wonderful day!"
    prediction = sentiment_agent.predict(text)
    assert isinstance(prediction, list)
    assert len(prediction) > 0
    assert isinstance(prediction[0], dict)
    assert "label" in prediction[0]
    assert "score" in prediction[0]


def test_sentiment_agent_normalize(sentiment_agent):
    """Test SentimentAgent normalize_output method."""
    # Example raw output from the pipeline
    raw_output = {"label": "POSITIVE", "score": 0.998}
    normalized = sentiment_agent.normalize_output(raw_output)
    assert isinstance(normalized, AgentOutput)
    assert normalized.label == "POSITIVE"
    assert isinstance(normalized.score, float)
    assert 0 <= normalized.score <= 1


def test_sentiment_agent_health(sentiment_agent):
    """Test SentimentAgent health check."""
    assert sentiment_agent.health_check() is True


# Toxicity Agent Tests
def test_toxicity_agent_predict(toxicity_agent):
    """Test ToxicityAgent predict method returns expected format."""
    text = "You are an idiot."
    prediction = toxicity_agent.predict(text)
    # Toxicity models often return a list of dicts for different classes
    assert isinstance(prediction, list)
    assert len(prediction) > 0
    assert isinstance(prediction[0], dict)
    assert "label" in prediction[0]
    assert "score" in prediction[0]


def test_toxicity_agent_normalize_toxic(toxicity_agent):
    """Test ToxicityAgent normalize_output for toxic input."""
    # Example raw output (might be list or dict depending on model/pipeline)
    # Assuming top_k=None returns multiple labels
    raw_output = [{"label": "toxic", "score": 0.95}, {"label": "non-toxic", "score": 0.05}]
    normalized = toxicity_agent.normalize_output(raw_output)  # Pass the list
    assert isinstance(normalized, AgentOutput)
    assert normalized.label == "toxic"  # Expect normalized label
    assert isinstance(normalized.score, float)
    assert normalized.score == 0.95  # Score of the highest scoring label


def test_toxicity_agent_normalize_non_toxic(toxicity_agent):
    """Test ToxicityAgent normalize_output for non-toxic input."""
    raw_output = [{"label": "toxic", "score": 0.1}, {"label": "non-toxic", "score": 0.9}]
    normalized = toxicity_agent.normalize_output(raw_output)
    assert isinstance(normalized, AgentOutput)
    assert normalized.label == "non-toxic"
    assert isinstance(normalized.score, float)
    assert normalized.score == 0.9


def test_toxicity_agent_health(toxicity_agent):
    """Test ToxicityAgent health check."""
    assert toxicity_agent.health_check() is True


# Hate Speech Agent Tests
def test_hate_speech_agent_predict(hate_speech_agent):
    """Test HateSpeechAgent predict method returns expected format."""
    text = "I hate everyone like you."
    prediction = hate_speech_agent.predict(text)
    assert isinstance(prediction, list)
    assert len(prediction) > 0
    assert isinstance(prediction[0], dict)
    assert "label" in prediction[0]
    assert "score" in prediction[0]


def test_hate_speech_agent_normalize_hate(hate_speech_agent):
    """Test HateSpeechAgent normalize_output for hate speech."""
    # Example raw output (model might use 'LABEL_1' or 'hate')
    raw_output = [{"label": "hate", "score": 0.85}, {"label": "not-hate", "score": 0.15}]
    normalized = hate_speech_agent.normalize_output(raw_output)
    assert isinstance(normalized, AgentOutput)
    assert normalized.label == "hate_speech"  # Expect normalized label
    assert isinstance(normalized.score, float)
    assert normalized.score == 0.85


def test_hate_speech_agent_normalize_not_hate(hate_speech_agent):
    """Test HateSpeechAgent normalize_output for non-hate speech."""
    raw_output = [
        {"label": "LABEL_0", "score": 0.95},
        {"label": "LABEL_1", "score": 0.05},
    ]  # Assuming LABEL_0 is not hate
    normalized = hate_speech_agent.normalize_output(raw_output)
    assert isinstance(normalized, AgentOutput)
    assert normalized.label == "not_hate_speech"
    assert isinstance(normalized.score, float)
    assert normalized.score == 0.95


def test_hate_speech_agent_health(hate_speech_agent):
    """Test HateSpeechAgent health check."""
    assert hate_speech_agent.health_check() is True


# Add tests for Custom Model Agent when implemented (REQ-006)
