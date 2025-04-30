from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from app.model import create_model, SentimentModel
from typing import Any
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load SentimentModel before handling requests
    app.state.sentiment_model = create_model()
    yield
    # shutdown cleanup (optional)


app = FastAPI(lifespan=lifespan)


class PredictionRequest(BaseModel):
    text: str


class PredictionResponse(BaseModel):
    label: str
    score: float


@app.post("/predict", response_model=PredictionResponse)
def predict(req: Request, payload: PredictionRequest):
    # retrieve model instance from app state
    sentiment_model: SentimentModel = req.app.state.sentiment_model
    raw_results: Any = sentiment_model.predict(payload.text)

    if not raw_results:
        raise HTTPException(status_code=400, detail="No predictions returned")
    results: list[dict] = list(raw_results)

    # use first prediction
    result = results[0]
    label = str(result.get("label"))
    score = float(result.get("score", 0.0))
    return PredictionResponse(label=label, score=score)


# To run locally:
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
