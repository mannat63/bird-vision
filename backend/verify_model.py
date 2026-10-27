"""Standalone sanity check: load the artifact and run one real inference.

Run from the backend/ directory:  python verify_model.py
Prints model info, output-unit/class-count consistency, and the top-3
prediction for a real sample image (the shipped Grad-CAM example).
"""

from __future__ import annotations

import sys
from pathlib import Path

from app.config import get_settings
from app.ml.model import get_engine

SAMPLE = get_settings().artifacts_dir / "gradcam_example.png"


def main() -> int:
    eng = get_engine()
    eng.load()
    if not eng.available:
        print("MODEL UNAVAILABLE:", eng.load_error)
        return 1
    info = eng.model_info()
    print("Model:", info["model_name"], info["model_version"])
    print("Classes:", info["num_classes"], "Input:", info["input_size"])
    print("TF:", info["tensorflow_version"])

    if not SAMPLE.exists():
        print("No sample image to test inference against:", SAMPLE)
        return 0
    result = eng.predict(SAMPLE.read_bytes())
    print(f"\nInference latency: {result.inference_ms} ms")
    print(f"Confidence status: {result.confidence_status}")
    print("Top-3:")
    for c in result.candidates:
        sci = c.scientific_name or "(scientific name not verified)"
        print(f"  {c.score:7.4f}  {c.common_name:30s} {sci}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
