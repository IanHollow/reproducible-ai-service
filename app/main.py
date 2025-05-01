from fastapi import FastAPI, HTTPException, Request, status
from pydantic import BaseModel
from typing import Dict, List, Any
from contextlib import asynccontextmanager
import time
import uuid  # For request IDs

from app.config import settings
from app.logger import get_logger
from app.controller import agent_controller  # Import the global controller instance
from app.agents.base import AgentOutput  # Import the common output model

# --- Prometheus Metrics (REQ-016) ---
from prometheus_client import Counter, Histogram, Gauge, make_asgi_app
import time

REQUEST_COUNT = Counter("http_requests_total", "Total HTTP Requests", ["method", "endpoint", "status_code"])
REQUEST_LATENCY = Histogram("http_request_latency_seconds", "HTTP request latency", ["endpoint"])
AGENT_HEALTH_GAUGE = Gauge("agent_health_status", "Health status of individual agents (1=OK, 0=FAIL)", ["agent_name"])
# Initialize gauges for known agents (prevents missing metrics until first health check)
for agent_name in agent_controller.agents.keys():
    AGENT_HEALTH_GAUGE.labels(agent_name=agent_name).set(1)  # Assume healthy on startup

# --- Rate Limiting (REQ-019) ---
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address, default_limits=[settings.RATE_LIMIT])

# --- Basic UI (REQ-017) ---
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

logger = get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Agent loading and warmup is handled by the AgentController constructor
    logger.info("Application startup complete. Agents loaded.")
    yield
    # Shutdown cleanup (optional)
    logger.info("Application shutting down.")


app = FastAPI(
    title="AIContentGuard API",
    description="Multi-agent content moderation service.",
    version="0.1.0",
    lifespan=lifespan,
)

# --- Middleware ---
# Rate Limiting State
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return _rate_limit_exceeded_handler(request, exc)


# Metrics Middleware (already added)
@app.middleware("http")
async def track_metrics(request: Request, call_next):
    status_code = 200  # Default status code
    start_time = time.time()
    endpoint = request.url.path

    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception as e:
        # Catch exceptions to record 500 errors if not handled elsewhere
        status_code = 500
        raise e  # Re-raise the exception
    finally:
        latency = time.time() - start_time
        # Exclude /metrics endpoint itself from latency histogram
        if endpoint != "/metrics":
            REQUEST_LATENCY.labels(endpoint=endpoint).observe(latency)
        REQUEST_COUNT.labels(method=request.method, endpoint=endpoint, status_code=status_code).inc()

    return response


# --- Mount Static Files and Templates (REQ-017) ---
# Ensure directories exist or handle potential errors if they don't
import os

static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")

if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
else:
    logger.warning(f"Static directory not found at {static_dir}, skipping mounting.")

if os.path.exists(templates_dir):
    templates = Jinja2Templates(directory=templates_dir)
else:
    logger.warning(f"Templates directory not found at {templates_dir}, UI endpoint will fail.")
    templates = None  # Set to None if dir missing

# --- Request and Response Models ---


class AnalyzeRequest(BaseModel):
    text: str
    # Optional: Add request metadata if needed
    # request_id: str | None = None


class AnalyzeResponse(BaseModel):
    request_id: str
    decision: str
    reasons: List[str]
    details: Dict[str, AgentOutput]
    latency_ms: float


class AvailableModel(BaseModel):
    model_id: str
    agent_type: str
    task: str | None = None
    description: str | None = None


class HealthStatus(BaseModel):
    status: str
    agents: Dict[str, bool]


# --- API Endpoints ---


@app.post("/analyze", response_model=AnalyzeResponse, status_code=status.HTTP_200_OK)
@limiter.limit(settings.RATE_LIMIT)  # Apply rate limit to specific endpoint (REQ-019)
async def analyze_text(payload: AnalyzeRequest, request: Request):
    """Analyzes input text using multiple content moderation agents."""
    request_id = str(uuid.uuid4())
    start_time = time.time()
    logger.info(
        f"[ReqID: {request_id}] Received /analyze request for text: '{payload.text[:50]}...'"
        if len(payload.text) > 50
        else f"[ReqID: {request_id}] Received /analyze request for text: '{payload.text}'"
    )

    try:
        # Run analysis via controller (REQ-001, REQ-020)
        analysis_details, agent_latency = await agent_controller.analyze(payload.text)

        # Aggregate decision (REQ-008)
        decision, reasons = agent_controller.aggregate_decision(analysis_details)

        total_latency_ms = (time.time() - start_time) * 1000
        logger.info(
            f"[ReqID: {request_id}] Analysis complete. Decision: {decision}, Reasons: {reasons}, Latency: {total_latency_ms:.2f}ms"
        )

        return AnalyzeResponse(
            request_id=request_id,
            decision=decision,
            reasons=reasons,
            details=analysis_details,
            latency_ms=total_latency_ms,
        )

    except Exception as e:
        logger.error(f"[ReqID: {request_id}] Error during /analyze request: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An internal error occurred during analysis. Request ID: {request_id}",
        )


@app.get("/available_models", response_model=List[AvailableModel], status_code=status.HTTP_200_OK)
async def get_models():
    """Lists the available moderation agents and their metadata."""  # (REQ-010)
    logger.info("Received /available_models request.")
    models_metadata = agent_controller.get_available_models()
    # Cast to ensure Pydantic validation
    return [AvailableModel(**meta) for meta in models_metadata]


@app.get("/health", response_model=HealthStatus, status_code=status.HTTP_200_OK)
async def health_check():
    """Checks the health and readiness of the service and its agents."""  # (REQ-023)
    logger.debug("Received /health request.")
    agent_health = agent_controller.health_check()
    overall_status = "OK" if all(agent_health.values()) else "DEGRADED"

    # Update Prometheus Gauges (REQ-016)
    for name, is_healthy in agent_health.items():
        AGENT_HEALTH_GAUGE.labels(agent_name=name).set(1 if is_healthy else 0)

    if overall_status == "DEGRADED":
        logger.warning(f"Health check status: DEGRADED. Agent status: {agent_health}")
        # Optionally return 503 if degraded status is critical
        # raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=HealthStatus(status=overall_status, agents=agent_health).dict())

    return HealthStatus(status=overall_status, agents=agent_health)


# --- Basic UI Endpoint (REQ-017) ---
@app.get("/ui", response_class=HTMLResponse)
async def read_item(request: Request):
    """Serves the basic HTML frontend."""
    if templates:
        return templates.TemplateResponse("index.html", {"request": request})
    else:
        raise HTTPException(status_code=404, detail="UI not available. Templates directory missing.")


# Mount the Prometheus metrics app (REQ-016)
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# To run locally:
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("app.main:app", host="0.0.0.0", port=settings.API_PORT, reload=True)
