from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from app.model import create_model, SentimentModel
from app.config import settings  # Import settings
from app.logger import get_logger  # Import logger
from typing import Any
from contextlib import asynccontextmanager

logger = get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load SentimentModel before handling requests using model name from settings
    logger.info(f"Loading model: {settings.MODEL_NAME}")
    app.state.sentiment_model = create_model(model_name=settings.MODEL_NAME)
    logger.info("Model loaded successfully.")
    yield
    # shutdown cleanup (optional)
    logger.info("Application shutting down.")


app = FastAPI(lifespan=lifespan)


class PredictionRequest(BaseModel):
    text: str


class PredictionResponse(BaseModel):
    label: str
    score: float


@app.post("/predict", response_model=PredictionResponse)
def predict(req: Request, payload: PredictionRequest):
    logger.info(
        f"Received prediction request for text: '{payload.text[:50]}...'"
        if len(payload.text) > 50
        else f"Received prediction request for text: '{payload.text}'"
    )
    # retrieve model instance from app state
    sentiment_model: SentimentModel = req.app.state.sentiment_model
    raw_results: Any = sentiment_model.predict(payload.text)

    if not raw_results:
        logger.error("Model did not return predictions.")
        raise HTTPException(status_code=400, detail="No predictions returned")
    results: list[dict] = list(raw_results)

    # use first prediction
    result = results[0]
    label = str(result.get("label"))
    score = float(result.get("score", 0.0))
    logger.info(f"Prediction result: label='{label}', score={score:.4f}")
    return PredictionResponse(label=label, score=score)


# To run locally:
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("app.main:app", host="0.0.0.0", port=settings.API_PORT, reload=True)
