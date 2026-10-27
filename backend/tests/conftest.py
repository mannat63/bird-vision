"""Shared test fixtures. External APIs are always mocked; no paid calls."""

from __future__ import annotations

import io

import pytest
from PIL import Image


@pytest.fixture
def png_bytes() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (300, 300), (120, 160, 90)).save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def tiny_png_bytes() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (4, 4), (10, 10, 10)).save(buf, format="PNG")
    return buf.getvalue()
