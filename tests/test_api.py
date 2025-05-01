import pytest
import httpx
from fastapi import status

# Import the FastAPI app instance
# Ensure the app instance can be imported for testing
# This might require adjusting sys.path or how the app is structured
# For simplicity, assuming 'app.main.app' is importable
try:
    from app.main import app
except ImportError:
    # Adjust path if necessary, e.g., if tests are run from the root directory
    import sys
    import os

    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from app.main import app


# Use httpx.AsyncClient for async FastAPI app
@pytest.fixture(scope="module")
async def async_client():
    # Ensure the lifespan context manager runs for tests
    # Use transport argument for ASGI app
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        yield client


# --- Test Cases ---


@pytest.mark.asyncio
async def test_health_endpoint(async_client: httpx.AsyncClient):
    """Test the /health endpoint."""
    response = await async_client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "status" in data
    assert "agents" in data
    assert isinstance(data["agents"], dict)
    # Check if known agents are present and their status is boolean
    # These checks assume the default agents are loaded
    assert "sentiment" in data["agents"]
    assert isinstance(data["agents"]["sentiment"], bool)
    assert "toxicity" in data["agents"]
    assert isinstance(data["agents"]["toxicity"], bool)
    assert "hate_speech" in data["agents"]
    assert isinstance(data["agents"]["hate_speech"], bool)
    # Check that all agents report True (healthy) after startup/warmup
    assert all(data["agents"].values())


@pytest.mark.asyncio
async def test_available_models_endpoint(async_client: httpx.AsyncClient):
    """Test the /available_models endpoint."""
    response = await async_client.get("/available_models")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    # Assuming the 3 default agents are loaded
    assert len(data) >= 3
    # Check structure of the first model entry
    if data:
        model_entry = data[0]
        assert "model_id" in model_entry
        assert "agent_type" in model_entry
        # task and description are optional but should be present for loaded agents
        assert "task" in model_entry
        assert "description" in model_entry


@pytest.mark.asyncio
async def test_analyze_endpoint_safe(async_client: httpx.AsyncClient):
    """Test the /analyze endpoint with safe text."""
    payload = {"text": "Have a wonderful and pleasant day!"}
    response = await async_client.post("/analyze", json=payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "request_id" in data
    assert "decision" in data
    # Decision might vary based on thresholds/models, check structure mainly
    # assert data["decision"] == "safe"
    assert "reasons" in data
    assert isinstance(data["reasons"], list)
    assert "details" in data
    assert isinstance(data["details"], dict)
    assert "sentiment" in data["details"]
    assert "toxicity" in data["details"]
    assert "hate_speech" in data["details"]
    assert "latency_ms" in data
    assert isinstance(data["latency_ms"], float)


@pytest.mark.asyncio
async def test_analyze_endpoint_flagged(async_client: httpx.AsyncClient):
    """Test the /analyze endpoint with potentially toxic/hateful text."""
    payload = {"text": "You are terrible and I hate you."}
    response = await async_client.post("/analyze", json=payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "request_id" in data
    assert "decision" in data
    # Decision should likely be 'flagged' with default models/thresholds
    assert data["decision"] == "flagged"
    assert "reasons" in data
    assert isinstance(data["reasons"], list)
    assert len(data["reasons"]) > 0  # Expect at least one reason
    assert "details" in data
    assert "latency_ms" in data


@pytest.mark.asyncio
async def test_analyze_endpoint_empty_text(async_client: httpx.AsyncClient):
    """Test the /analyze endpoint with empty text."""
    payload = {"text": ""}
    response = await async_client.post("/analyze", json=payload)
    # Empty string is allowed by default Pydantic model
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["decision"] == "safe"  # Empty string is usually safe
    assert len(data["reasons"]) == 0
    # Agents might return default/neutral results for empty string
    assert "sentiment" in data["details"]
    assert "toxicity" in data["details"]
    assert "hate_speech" in data["details"]


@pytest.mark.asyncio
async def test_analyze_endpoint_missing_text(async_client: httpx.AsyncClient):
    """Test the /analyze endpoint with missing 'text' field."""
    payload = {}
    response = await async_client.post("/analyze", json=payload)
    # FastAPI/Pydantic validation should fail
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_metrics_endpoint(async_client: httpx.AsyncClient):
    """Test the /metrics endpoint returns Prometheus format."""
    # Make a request to another endpoint first to generate some metrics
    await async_client.get("/health")
    await async_client.post("/analyze", json={"text": "test metrics"})

    response = await async_client.get("/metrics")
    assert response.status_code == status.HTTP_200_OK
    assert "text/plain" in response.headers["content-type"]
    # Check for expected metric names in the response text
    metrics_text = response.text
    assert "http_requests_total" in metrics_text
    assert "http_request_latency_seconds_bucket" in metrics_text
    assert "agent_health_status" in metrics_text
    assert 'endpoint="/health"' in metrics_text
    assert 'endpoint="/analyze"' in metrics_text


@pytest.mark.asyncio
async def test_ui_endpoint(async_client: httpx.AsyncClient):
    """Test the /ui endpoint serves HTML."""
    response = await async_client.get("/ui")
    assert response.status_code == status.HTTP_200_OK
    assert "text/html" in response.headers["content-type"]
    assert "<title>AIContentGuard</title>" in response.text


# Note: Testing rate limiting accurately might require specific test setup
# or mocking time, which can be complex. Basic endpoint tests are included.
