"""Model engine tests. Require the real artifact to be present.

Skipped automatically if TensorFlow or the model file is unavailable, so the
rest of the suite still runs in a model-less environment.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from app.config import get_settings
from app.ml.model import get_engine

pytest.importorskip("tensorflow")

ARTIFACTS = Path(__file__).resolve().parents[2]
SAMPLE = ARTIFACTS / "gradcam_example.png"


@pytest.fixture(scope="module")
def engine():
    eng = get_engine()
    eng.load()
    if not eng.available:
        pytest.skip(f"Model unavailable: {eng.load_error}")
    return eng


def test_class_count_matches_output(engine):
    out = engine._model.output_shape
    n = out[-1] if isinstance(out, tuple) else out[0][-1]
    assert n == len(engine.class_names) == 200


def test_prediction_returns_ordered_topk(engine):
    result = engine.predict(SAMPLE.read_bytes())
    assert len(result.candidates) == 3
    scores = [c.score for c in result.candidates]
    assert scores == sorted(scores, reverse=True)
    assert all(0.0 <= s <= 1.0 for s in scores)


def test_prediction_indices_valid(engine):
    result = engine.predict(SAMPLE.read_bytes())
    for c in result.candidates:
        assert 0 <= c.species_id < 200
        assert engine.class_names[c.species_id] == c.label


def test_gradcam_shape(engine):
    from app.ml import gradcam

    idx = engine.predict(SAMPLE.read_bytes()).candidates[0].species_id
    out = gradcam.generate(SAMPLE.read_bytes(), engine._model, idx)
    assert out["overlay_png"].startswith("data:image/png;base64,")
    assert out["heatmap_png"].startswith("data:image/png;base64,")


def test_gradcam_heatmap_is_not_uniform(engine):
    """Regression for the 'uniform dark-blue heatmap' bug: the decoded heatmap
    must have real spatial contrast, and the overlay must differ from original."""
    import base64
    import io

    from PIL import Image

    from app.ml import gradcam

    idx = engine.predict(SAMPLE.read_bytes()).candidates[0].species_id
    out = gradcam.generate(SAMPLE.read_bytes(), engine._model, idx)

    def arr(b64):
        raw = base64.b64decode(b64.split(",")[1])
        return np.asarray(Image.open(io.BytesIO(raw)).convert("RGB"))

    heat = arr(out["heatmap_png"])
    orig = arr(out["original_png"])
    overlay = arr(out["overlay_png"])
    assert heat.std() > 10.0  # not a flat/uniform image
    assert len(np.unique(heat.reshape(-1, 3), axis=0)) > 20
    assert np.abs(overlay.astype(int) - orig.astype(int)).mean() > 1.0


def test_gradcam_normalize_rejects_degenerate():
    from app.ml import gradcam

    with pytest.raises(gradcam.GradCAMError):
        gradcam._normalize_cam(np.zeros((7, 7), dtype=np.float32))  # zero range
    with pytest.raises(gradcam.GradCAMError):
        gradcam._normalize_cam(np.full((7, 7), np.nan, dtype=np.float32))  # NaN


def test_gradcam_normalize_scales_to_unit_range():
    from app.ml import gradcam

    cam = np.array([[0.0, 1.0], [2.0, 4.0]], dtype=np.float32)
    out = gradcam._normalize_cam(cam)
    assert out.min() == 0.0 and out.max() == 1.0
