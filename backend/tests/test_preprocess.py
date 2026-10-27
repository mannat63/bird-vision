"""Preprocessing tests."""

from __future__ import annotations

import pytest

from app.ml.preprocess import InvalidImageError, decode_image, preprocess_bytes


def test_preprocess_shape_and_range(png_bytes):
    batch = preprocess_bytes(png_bytes)
    assert batch.shape == (1, 224, 224, 3)
    assert batch.dtype.name == "float32"
    assert 0.0 <= batch.min() and batch.max() <= 255.0


def test_tiny_image_is_upscaled(tiny_png_bytes):
    assert preprocess_bytes(tiny_png_bytes).shape == (1, 224, 224, 3)


def test_corrupt_bytes_raise():
    with pytest.raises(InvalidImageError):
        decode_image(b"not an image at all")
