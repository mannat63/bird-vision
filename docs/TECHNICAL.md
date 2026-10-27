# Technical Explainer (interview reference)

A concise, defensible explanation of each core concept in BirdVision AI.

## CNN & transfer learning
A convolutional neural network learns a hierarchy of image features (edges → textures →
parts → objects) via learnable convolution filters. Instead of training from scratch, we
start from **EfficientNetB0 pretrained on ImageNet** (transfer learning): its backbone
already encodes general visual features. We replace the 1000-class ImageNet head with a
200-class softmax head for CUB-200-2011.

## Two-stage training
1. **Head training:** freeze the backbone, train only the new head so the randomly
   initialized head stops producing garbage gradients that would wreck pretrained weights.
2. **Fine-tuning:** unfreeze (part of) the backbone and train at a low learning rate so the
   features adapt to birds without catastrophic forgetting.

## Why the gap matters
Train top-1 (~90%) far above validation/test (~71%) signals **overfitting** — the model
memorizes training specifics that don't generalize. We report the **held-out test** number
(71.06%), never the training number, as the headline.

## Preprocessing (the subtle part)
EfficientNet in Keras has rescaling/normalization **inside** the model graph. So inputs are
224×224×3 RGB in the **0–255** range — we must **not** divide by 255 or call
`preprocess_input` again, or we normalize twice and silently corrupt predictions. The
backend mirrors exactly what training did (`model_config.json` records this contract).

## Metrics
- **Top-1 / Top-5:** is the true class the #1 / within the top-5 prediction.
- **Precision / recall / F1 per class**, then **macro** (unweighted mean over classes — fair
  to rare classes) and **weighted** (by support). Macro ≈ weighted here because class support
  is roughly balanced.
- **Confusion matrix** shows *which* classes get mistaken for which — the honest view of
  failure modes.

## Confidence
Softmax outputs sum to 1 but are **not calibrated probabilities**. We expose them as raw
scores, apply a heuristic abstention threshold, and say so — and we note a threshold is
**not** OOD detection.

## Grad-CAM
Gradient-weighted Class Activation Mapping: take the gradient of the predicted class score
w.r.t. the final conv feature map, global-average-pool those gradients into per-channel
weights, combine the feature maps, ReLU, and upsample to a heatmap. It highlights influential
regions — an attribution aid, not proof of reasoning. (Implementation note: because the model
is a nested functional backbone loaded in Keras 3, we run the forward pass eagerly inside a
`GradientTape` watching the backbone's feature tensor rather than rebuilding a symbolic
sub-model.)

## API architecture
FastAPI with Pydantic schemas, a lazily-loaded singleton model engine, per-endpoint rate
limits, upload validation (size + MIME + magic bytes), restricted CORS, and a consistent
error envelope. `/ready` reflects real model-load status (503 if unavailable) so the system
**reports** unavailability instead of faking predictions.

## LLM (Groq) separation (why it is not the classifier)
The CNN alone produces the species label and scores. Groq is called **after** a label
exists, only to explain/summarize that species, and the whole app degrades gracefully if
the LLM is down. This keeps the ML claim honest: the product's intelligence is the trained
model, not a general-purpose vision-language API.
