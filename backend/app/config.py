"""Centralized configuration for the BirdVision AI backend.

All secrets and tunables are read from the environment (see ``.env.example``).
Nothing here is ever sent to the client; the frontend only ever talks to the
FastAPI endpoints in :mod:`app.main`.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/config.py -> backend/ -> repo root
BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent


class Settings(BaseSettings):
    """Application settings loaded from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        protected_namespaces=(),
    )

    # --- Artifact locations -------------------------------------------------
    # Directory containing the trained model + metadata. Defaults to the repo
    # root where the Colab artifacts were placed, but is fully configurable so
    # the model can be mounted/downloaded separately in production.
    artifacts_dir: Path = REPO_ROOT
    model_filename: str = "birdvision_model.keras"
    class_names_filename: str = "class_names.json"
    model_config_filename: str = "model_config.json"
    metrics_filename: str = "metrics.json"

    # --- Inference tunables -------------------------------------------------
    # Softmax score below which we decline to assert a confident ID. This is a
    # heuristic abstention threshold tuned on validation behaviour, NOT a
    # calibrated probability and NOT a guarantee of out-of-distribution
    # detection. Documented as such in the UI and model card.
    low_confidence_threshold: float = 0.35
    top_k: int = 3
    max_upload_bytes: int = 10 * 1024 * 1024  # 10 MB

    # --- External services (server-side secrets) ----------------------------
    # Groq LLM enrichment (OpenAI-compatible API). Server-side only.
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-120b"
    # Optional fallback model, used only for transient failures and only if it
    # is available to the same API key. Empty disables fallback.
    groq_fallback_model: str = "openai/gpt-oss-20b"
    groq_timeout_s: float = 20.0

    ebird_api_key: str = ""
    ebird_timeout_s: float = 12.0

    # --- Server / CORS ------------------------------------------------------
    # Comma-separated list of allowed frontend origins.
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    environment: str = "development"

    @property
    def model_path(self) -> Path:
        return self.artifacts_dir / self.model_filename

    @property
    def class_names_path(self) -> Path:
        return self.artifacts_dir / self.class_names_filename

    @property
    def model_config_path(self) -> Path:
        return self.artifacts_dir / self.model_config_filename

    @property
    def metrics_path(self) -> Path:
        return self.artifacts_dir / self.metrics_filename

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
