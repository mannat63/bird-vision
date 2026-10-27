"""Image decoding and preprocessing.

Reproduces the preprocessing used at training time for the EfficientNetB0
artifact: decode -> RGB -> resize to 224x224 -> float32 in the 0..255 range.

Per ``model_config.json`` the network has EfficientNet's rescaling/normalization
baked in, so we deliberately do NOT divide by 255 or call ``preprocess_input``
again here (that would normalize twice and corrupt predictions).
"""

from __future__ import annotations

import io

import numpy as np
from PIL import Image

INPUT_SIZE = (224, 224)


class InvalidImageError(ValueError):
    """Raised when uploaded bytes cannot be decoded as an image."""


def decode_image(data: bytes) -> Image.Image:
    """Decode raw bytes into a verified RGB PIL image."""
    try:
        # Image.open is lazy; load() forces a full decode so truncated/corrupt
        # files fail here rather than deep inside the model.
        img = Image.open(io.BytesIO(data))
        img.load()
    except Exception as exc:  # Pillow raises many subclasses
        raise InvalidImageError("Could not decode image") from exc
    return img.convert("RGB")


def preprocess(img: Image.Image) -> np.ndarray:
    """Resize an RGB image and build a (1, 224, 224, 3) float32 0..255 batch."""
    resized = img.resize(INPUT_SIZE, Image.BILINEAR)
    arr = np.asarray(resized, dtype=np.float32)  # already 0..255
    if arr.shape != (INPUT_SIZE[1], INPUT_SIZE[0], 3):
        raise InvalidImageError(f"Unexpected image shape {arr.shape}")
    return np.expand_dims(arr, axis=0)


def preprocess_bytes(data: bytes) -> np.ndarray:
    return preprocess(decode_image(data))
