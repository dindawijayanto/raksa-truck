"""FastAPI application exposing a versioned Model B prediction endpoint."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .model_service import ModelBService
from .schemas import ModelBScenarioRequest, ModelBScenarioResponse

MODEL_DIR = Path(os.getenv("MODEL_B_DIR", Path(__file__).resolve().parents[1] / "models"))
ALLOWED_ORIGINS = [origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",") if origin.strip()]

app = FastAPI(title="Raksa Model B API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@lru_cache
def get_model_service() -> ModelBService:
    return ModelBService(MODEL_DIR)


@app.get("/healthz")
def health_check() -> dict[str, str]:
    service = get_model_service()
    return {"status": "ok", "model_name": service.contract["model_name"], "model_status": service.contract["model_status"]}


@app.post("/api/v1/model-b/predict", response_model=ModelBScenarioResponse)
def predict_model_b(scenario: ModelBScenarioRequest) -> ModelBScenarioResponse:
    return get_model_service().predict(scenario)
