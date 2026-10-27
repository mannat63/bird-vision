"""Grad-CAM explainability for the trained EfficientNetB0 model.

Produces a class-activation heatmap for the predicted class and overlays it on
the original image. If the architecture does not expose a usable convolutional
layer, this returns a controlled error instead of breaking prediction.

Note: a Grad-CAM heatmap shows where in the image the network's activations
most influenced the chosen class score. It is an attribution visualization, not
proof of causal reasoning and not a correctness guarantee.
"""

from __future__ import annotations

import base64
import io

import numpy as np
from PIL import Image

from app.ml.preprocess import INPUT_SIZE, decode_image


class GradCAMError(RuntimeError):
    pass


def _find_feature_layer(model):
    """Return the layer whose output is the last convolutional feature map,
    expressed in the OUTER model's graph (so it stays connected to inputs).

    For a transfer-learning model the feature extractor is a nested functional
    backbone (e.g. ``efficientnetb0``) used as a single layer; its ``.output``
    is a node in the outer graph (shape (None, H, W, C)) and is ideal for
    Grad-CAM. Falls back to the last top-level Conv2D otherwise.
    """
    import keras

    for layer in reversed(model.layers):
        if isinstance(layer, keras.Model):
            shp = layer.output.shape
            if len(shp) == 4:
                return layer
    for layer in reversed(model.layers):
        if isinstance(layer, keras.layers.Conv2D):
            return layer
    raise GradCAMError("No convolutional feature layer found for Grad-CAM")


def _heatmap(model, batch: np.ndarray, class_index: int) -> np.ndarray:
    import tensorflow as tf

    # Keras 3 does not allow rebuilding a Functional model that taps a nested
    # backbone's output after loading, so we run the forward pass eagerly:
    # backbone -> remaining head layers, watching the backbone feature map.
    feature_layer = _find_feature_layer(model)
    idx = model.layers.index(feature_layer)
    head_layers = model.layers[idx + 1:]  # GAP, dropout, dense, ...

    x = tf.convert_to_tensor(batch)
    with tf.GradientTape() as tape:
        conv_out = feature_layer(x, training=False)  # (1, H, W, C)
        tape.watch(conv_out)
        h = conv_out
        for layer in head_layers:
            h = layer(h, training=False)
        loss = h[:, class_index]
    grads = tape.gradient(loss, conv_out)
    if grads is None:
        raise GradCAMError("Gradients are disconnected for the selected layer")
    pooled = tf.reduce_mean(grads, axis=(0, 1, 2))
    conv_out = conv_out[0]
    cam = tf.reduce_sum(conv_out * pooled, axis=-1)
    cam = tf.nn.relu(cam)
    # Return the RAW (post-ReLU, un-normalized) activation map; validation and
    # normalization happen in generate() after sanity checks.
    return cam.numpy().astype(np.float32)


def _normalize_cam(cam: np.ndarray) -> np.ndarray:
    """Validate the raw activation map and normalize to 0..1.

    Raises GradCAMError on degenerate maps (NaN/inf, wrong rank, or a flat map
    with no spatial contrast) so the caller can show an 'unavailable' state
    rather than a blank or misleading heatmap.
    """
    if cam.ndim != 2:
        raise GradCAMError(f"Activation map has wrong rank {cam.ndim} (expected 2)")
    if not np.all(np.isfinite(cam)):
        raise GradCAMError("Activation map contains NaN/inf values")
    lo, hi = float(cam.min()), float(cam.max())
    if hi <= 0.0 or (hi - lo) < 1e-8:
        raise GradCAMError("Activation map has zero range (no class evidence)")
    return (cam - lo) / (hi - lo)


def _apply_colormap(cam: np.ndarray) -> np.ndarray:
    """Map a 0..1 heatmap to an RGB 'jet'-style colormap without matplotlib."""
    cam = np.clip(cam, 0.0, 1.0)
    r = np.clip(1.5 - np.abs(4 * cam - 3), 0, 1)
    g = np.clip(1.5 - np.abs(4 * cam - 2), 0, 1)
    b = np.clip(1.5 - np.abs(4 * cam - 1), 0, 1)
    rgb = np.stack([r, g, b], axis=-1) * 255.0
    return rgb.astype(np.uint8)


def generate(image_bytes: bytes, model, class_index: int, alpha: float = 0.6) -> dict:
    """Return base64 PNGs for the original image, heatmap and overlay."""
    img = decode_image(image_bytes)
    resized = img.resize(INPUT_SIZE, Image.BILINEAR)
    batch = np.expand_dims(np.asarray(resized, dtype=np.float32), 0)

    raw_cam = _heatmap(model, batch, class_index)  # (H, W) raw activations
    cam = _normalize_cam(raw_cam)                   # 0..1, validated

    # Resize the normalized 0..1 map to the image size, keeping float precision
    # (scale to 0..255 uint8 only for the resample, then back to 0..1).
    cam_img = Image.fromarray((cam * 255.0).astype(np.uint8)).resize(
        INPUT_SIZE, Image.BILINEAR
    )
    cam_resized = np.asarray(cam_img, dtype=np.float32) / 255.0  # (224,224) 0..1
    heat_rgb = _apply_colormap(cam_resized)

    # Per-pixel alpha proportional to activation: cold regions keep the original
    # image untouched; only hot regions get colorized (no global darkening).
    base = np.asarray(resized, dtype=np.float32)
    a = (cam_resized[..., None] * alpha)
    overlay = (base * (1.0 - a) + heat_rgb.astype(np.float32) * a)
    overlay = overlay.clip(0, 255).astype(np.uint8)

    return {
        "original_png": _to_b64(np.asarray(resized, dtype=np.uint8)),
        "overlay_png": _to_b64(overlay),
        "heatmap_png": _to_b64(heat_rgb),
    }


def _to_b64(arr: np.ndarray) -> str:
    buf = io.BytesIO()
    Image.fromarray(arr).save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
