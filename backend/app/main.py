"""FastAPI application exposing a versioned Model B prediction endpoint."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .model_service import ModelBService
from .report_service import ModelReportService
from .schemas import ModelBScenarioRequest, ModelBScenarioResponse

MODEL_DIR = Path(os.getenv("MODEL_B_DIR", Path(__file__).resolve().parents[1] / "models"))
DATA_DIR = Path(os.getenv("MODEL_REPORT_DIR", Path(__file__).resolve().parents[1] / "data"))
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


@lru_cache
def get_report_service() -> ModelReportService:
    return ModelReportService(DATA_DIR, MODEL_DIR)


@app.get("/healthz")
def health_check() -> dict[str, str]:
    service = get_model_service()
    return {"status": "ok", "model_name": service.contract["model_name"], "model_status": service.contract["model_status"]}


@app.post("/api/v1/model-b/predict", response_model=ModelBScenarioResponse)
def predict_model_b(scenario: ModelBScenarioRequest) -> ModelBScenarioResponse:
    return get_model_service().predict(scenario)


@app.get("/api/v1/model-a/sessions")
def get_model_a_sessions() -> dict:
    return get_report_service().model_a_session_summaries()


@app.get("/api/v1/model-a/sessions/{session_id}/segments")
def get_model_a_segments(session_id: str, limit: int = Query(default=120, ge=1, le=500)) -> dict:
    report = get_report_service().model_a_segments(session_id, limit)
    if report is None:
        raise HTTPException(status_code=404, detail="Model A session was not found")
    return report


@app.get("/api/v1/dashboard/overview")
def get_dashboard_overview() -> dict:
    return get_report_service().dashboard_overview()
