"""Trained CNN loader and inference engine.

This module owns the single source of truth for predictions. Groq and eBird
never touch it. If the artifact cannot be loaded the engine reports
``available == False`` and the API returns 503 rather than a fake prediction.
"""

from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from app.config import Settings, get_settings
from app.ml.preprocess import preprocess_bytes
from app.services.species import species_record


@dataclass
class Candidate:
    species_id: int
    label: str
    common_name: str
    scientific_name: str | None
    scientific_name_verified: bool
    score: float  # raw softmax score (NOT a calibrated probability)


@dataclass
class PredictionResult:
    candidates: list[Candidate]
    confident: bool
    confidence_status: str
    confidence_note: str
    inference_ms: float
    model_version: str


@dataclass
class ModelEngine:
    """Lazily loads and holds the Keras model + class mapping."""

    settings: Settings = field(default_factory=get_settings)
    _model: object | None = field(default=None, repr=False)
    _class_names: list[str] = field(default_factory=list)
    _model_meta: dict = field(default_factory=dict)
    _load_error: str | None = None
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    _loaded: bool = False

    # -- loading -------------------------------------------------------------
    def load(self) -> None:
        """Load class mapping then the model. Validates mapping integrity.

        Safe to call repeatedly; only the first call does work.
        """
        if self._loaded:
            return
        with self._lock:
            if self._loaded:
                return
            try:
                self._load_class_names()
                self._load_model()
                self._loaded = True
                self._load_error = None
            except Exception as exc:  # surface clearly, never silently fake
                self._load_error = str(exc)
                self._model = None

    def _load_class_names(self) -> None:
        path = self.settings.class_names_path
        if not path.exists():
            raise FileNotFoundError(f"Class names file missing: {path}")
        names = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(names, list) or not names:
            raise ValueError("class_names.json must be a non-empty list")
        if len(set(names)) != len(names):
            raise ValueError("class_names.json contains duplicate labels")
        self._class_names = names
        # model_config.json carries the authoritative expected class count.
        cfg = {}
        if self.settings.model_config_path.exists():
            cfg = json.loads(self.settings.model_config_path.read_text("utf-8"))
        expected = cfg.get("num_classes")
        if expected is not None and expected != len(names):
            raise ValueError(
                f"num_classes mismatch: config={expected} labels={len(names)}"
            )
        self._model_meta = cfg

    def _load_model(self) -> None:
        import keras  # imported lazily so the module imports without TF present

        path = self.settings.model_path
        if not path.exists():
            raise FileNotFoundError(f"Model file missing: {path}")
        model = keras.models.load_model(path, compile=False)
        out = model.output_shape
        n_out = out[-1] if isinstance(out, tuple) else out[0][-1]
        if n_out != len(self._class_names):
            raise ValueError(
                f"Model output units ({n_out}) != class count "
                f"({len(self._class_names)}); mapping would be wrong."
            )
        self._model = model

    # -- status --------------------------------------------------------------
    @property
    def available(self) -> bool:
        return self._loaded and self._model is not None

    @property
    def load_error(self) -> str | None:
        return self._load_error

    @property
    def class_names(self) -> list[str]:
        return self._class_names

    @property
    def model_version(self) -> str:
        return self._model_meta.get("model_name", "EfficientNetB0") + "-v1"

    def model_info(self) -> dict:
        params = None
        size_mb = None
        if self._model is not None:
            try:
                params = int(self._model.count_params())
            except Exception:
                params = None
        try:
            size_mb = round(self.settings.model_path.stat().st_size / 1e6, 1)
        except OSError:
            size_mb = None
        return {
            "model_name": self._model_meta.get("model_name", "EfficientNetB0"),
            "model_version": self.model_version,
            "available": self.available,
            "load_error": self._load_error,
            "num_classes": len(self._class_names),
            "input_size": self._model_meta.get("input_size", [224, 224, 3]),
            "preprocessing": self._model_meta.get("preprocessing", {}),
            "dataset_slug": self._model_meta.get("dataset_slug"),
            "tensorflow_version": self._model_meta.get("tensorflow_version"),
            "parameter_count": params,
            "artifact_size_mb": size_mb,
        }

    # -- inference -----------------------------------------------------------
    def _softmax(self, logits: np.ndarray) -> np.ndarray:
        # The training head ends in softmax, but apply a numerically stable
        # softmax defensively in case scores are not already normalized.
        s = float(logits.sum())
        if abs(s - 1.0) < 1e-3 and float(logits.min()) >= 0.0:
            return logits  # already a probability vector
        e = np.exp(logits - logits.max())
        return e / e.sum()

    def predict(self, image_bytes: bytes) -> PredictionResult:
        if not self.available:
            raise RuntimeError("Model not available")
        batch = preprocess_bytes(image_bytes)
        t0 = time.perf_counter()
        raw = self._model.predict(batch, verbose=0)[0]
        inference_ms = (time.perf_counter() - t0) * 1000.0

        scores = self._softmax(np.asarray(raw, dtype=np.float64))
        k = min(self.settings.top_k, len(scores))
        top_idx = np.argsort(scores)[::-1][:k]

        candidates: list[Candidate] = []
        for idx in top_idx:
            idx = int(idx)
            rec = species_record(idx, self._class_names[idx])
            candidates.append(
                Candidate(
                    species_id=idx,
                    label=rec["label"],
                    common_name=rec["common_name"],
                    scientific_name=rec["scientific_name"],
                    scientific_name_verified=rec["scientific_name_verified"],
                    score=float(scores[idx]),
                )
            )

        top_score = candidates[0].score
        threshold = self.settings.low_confidence_threshold
        confident = top_score >= threshold
        if confident:
            status = "confident"
            note = (
                "Top raw softmax score is above the abstention threshold "
                f"({threshold:.2f}). Scores are uncalibrated model outputs, "
                "not statistically calibrated probabilities."
            )
        else:
            status = "uncertain"
            note = (
                "Top score is below the abstention threshold "
                f"({threshold:.2f}); the model cannot identify this image "
                "reliably. A threshold does not guarantee out-of-distribution "
                "detection for non-bird or unsupported-species images."
            )
        return PredictionResult(
            candidates=candidates,
            confident=confident,
            confidence_status=status,
            confidence_note=note,
            inference_ms=round(inference_ms, 2),
            model_version=self.model_version,
        )


_engine: ModelEngine | None = None
_engine_lock = threading.Lock()


def get_engine() -> ModelEngine:
    global _engine
    if _engine is None:
        with _engine_lock:
            if _engine is None:
                _engine = ModelEngine()
    return _engine
