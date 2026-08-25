"""Shared paths for the offline AIC modelling archive.

The research package lives under ``backend/modeling`` while its reproducible
outputs are stored alongside the deployed API artifacts at repository level.
Keeping this mapping in one place avoids scripts writing into accidental,
duplicate directories.
"""

from pathlib import Path


MODELING_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = MODELING_ROOT.parents[1]
SOURCE_DIR = MODELING_ROOT / "src"
BACKEND_DIR = REPOSITORY_ROOT / "backend"
DATA_DIR = BACKEND_DIR / "data"
DEPLOYMENT_MODELS_DIR = BACKEND_DIR / "models"
RESEARCH_MODELS_DIR = DEPLOYMENT_MODELS_DIR / "research"
REPORTS_DIR = REPOSITORY_ROOT / "reports" / "modeling"
