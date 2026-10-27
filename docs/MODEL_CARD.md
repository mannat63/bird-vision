# Model Card — BirdVision EfficientNetB0

## Overview
- **Task:** fine-grained bird species image classification (single label, 200 classes).
- **Architecture:** EfficientNetB0 backbone (ImageNet-pretrained) + global average pooling
  + dropout + 200-way softmax head. Transfer learning with a classification-head stage
  followed by fine-tuning.
- **Framework:** TensorFlow 2.21 / Keras 3.13 (`.keras` format).
- **Parameters:** 4,305,771. **Artifact size:** 36.4 MB.
- **Input:** 224×224×3 RGB, pixel range **0–255** (EfficientNet normalization is internal
  to the network — do not re-normalize).

## Training data
CUB-200-2011 (see `docs/DATASET_CARD.md`). Splits actually used:
- Train: 5,194 images · Validation: 800 · Held-out test: 5,794 · Classes: 200.

## Evaluation (held-out test set, from `metrics.json`)
| Metric | Value |
|---|---|
| Top-1 accuracy | **71.06%** |
| Top-5 accuracy | **92.44%** |
| Macro precision | 73.52% |
| Macro recall | 71.27% |
| Macro F1 | 71.46% |
| Weighted F1 | 71.27% |
| Inference latency (single image) | mean 293 ms, p95 313 ms (GPU during eval) |

Per-class precision/recall/F1/support: `classification_report.csv`.
Confusion matrix: `confusion_matrix.npy` / `confusion_matrix_top_classes.png`.

The earlier **stage-1** numbers (train top-1 ≈ 90.2%, val top-1 ≈ 70.9%) are *not* the
final test result and are not presented as such anywhere in the app.

## Confidence & abstention
Raw softmax scores are returned and labeled as **uncalibrated**. A configurable
abstention threshold (`LOW_CONFIDENCE_THRESHOLD`, default 0.35) triggers an
"unable to identify reliably" response. This is a heuristic tuned on validation behaviour;
it does **not** guarantee out-of-distribution detection.

## Intended use
Educational / birdwatching assistance for the 200 supported species. Best-guess
assistance, **not** authoritative identification.

## Limitations & failure modes
- ~19-point train/val generalization gap → some overfitting.
- Most frequent confusions are visually similar species: albatrosses, gulls, terns,
  sparrows, flycatchers, crows (visible in the per-class report and confusion matrix).
- Only 200 (largely North-American) species; out-of-set species map to the nearest class.
- Scores are relative, not probabilities.

## Explainability
Grad-CAM on the backbone's final feature map (7×7×1280). The heatmap indicates influential
regions for the predicted class — an attribution aid, **not** proof of causal reasoning or
a correctness guarantee.

## Ethical notes
Precise locations of sensitive/threatened species should not be amplified; the app shows
only user-/eBird-provided observations and does not infer or publish sensitive locations.
