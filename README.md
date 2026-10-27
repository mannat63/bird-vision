---
title: BirdVision AI Backend
emoji: 🪶
colorFrom: green
colorTo: gray
sdk: docker
app_port: 7860
pinned: false
---

<!-- The YAML block above configures a Hugging Face Spaces (Docker) deployment of
     the backend; see docs/DEPLOY_BACKEND.md. It is ignored by normal Markdown
     viewers. -->

# 🪶 BirdVision AI

**Identify the wild. Understand the world.**

A production-minded bird-species identification platform. Upload a photograph and a
**genuinely trained EfficientNetB0 CNN** returns a real species prediction — with
confidence interpretation, Grad-CAM explainability, AI-assisted species intelligence,
and **real** nearby observations from eBird.

> The CNN classifier is the product. Groq and eBird are optional enrichment layers and
> the classifier works fully without them. No prediction, metric, or observation in this
> project is faked.

---

## What actually works (verified)

| Capability | Status | Evidence |
|---|---|---|
| CNN inference (EfficientNetB0, CUB-200-2011, 200 classes) | ✅ Implemented & tested | `backend/verify_model.py`, live `/api/predict` |
| Exact class mapping preserved | ✅ Tested | `tests/test_model.py`, `tests/test_species.py` |
| Held-out **test** metrics (top-1 **71.06%**, top-5 **92.44%**) | ✅ Real artifact | `metrics.json`, `/api/metrics` |
| Grad-CAM explainability | ✅ Implemented & tested | `/api/explain`, browser-verified overlay |
| Confidence / abstention policy | ✅ Implemented & tested | `confidence_note` in `/api/predict` |
| eBird species-specific sightings + hotspots | ✅ Live & verified | "Where can I see this bird near me?" — real Blue Jay sightings near Boston, taxon resolved to `blujay` |
| Groq LLM species intelligence + Q&A | ✅ Live & verified | `openai/gpt-oss-120b` returns real structured content via `/api/species/{id}/intel` and `/ask` |
| Next.js frontend wired to real inference | ✅ Built & browser-verified | production build passes, E2E flow verified |
| Automated tests | ✅ 58 backend tests pass | `pytest` |
| Public deployment | ⚠️ **Not deployed** — instructions provided | see `docs/DEPLOYMENT.md` |

**LLM enrichment (Groq):** species intelligence and the "Ask the bird expert" Q&A are
powered by Groq's OpenAI-compatible API using `openai/gpt-oss-120b` (with
`openai/gpt-oss-20b` as a transient-failure fallback). The key is server-side only.
Error handling classifies failures, retries transient ones with backoff+jitter, and
degrades gracefully — the CNN is fully independent of it.

---

## Architecture

```
┌──────────────────────┐        HTTPS/JSON        ┌───────────────────────────────┐
│   Next.js frontend    │  ───────────────────▶   │        FastAPI backend         │
│  (React, TS, Tailwind)│                          │                               │
│                      │  ◀───────────────────   │  • TensorFlow/Keras CNN  ◀─ authoritative
│  Discover / Results  │                          │  • Grad-CAM                    │
│  Insights / Nearby   │                          │  • Species metadata layer      │
└──────────────────────┘                          │  • Groq LLM service (enrichment)  │
       browser only                               │  • eBird service (observations)│
   NEXT_PUBLIC_API_BASE                            └───────────────────────────────┘
   (no secrets client-side)                           secrets: GROQ/EBIRD keys 
                                                       (server-side only)
```

- **The CNN is the single source of truth for predictions.** Groq never classifies images.
- All API keys live on the backend and are never shipped to the browser.
- Large model binaries are kept out of Git and loaded from a configurable artifact dir.

See `docs/` for the model card, dataset card, deployment guide, and recruiter demo script.

---

## Quick start (local)

Prerequisites: Python 3.11, Node 22+.

### 1. Backend (FastAPI + TensorFlow)

```bash
cd backend
python -m venv venv
# Windows:  venv\Scripts\activate       # macOS/Linux:  source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # then fill in EBIRD_API_KEY / GROQ_API_KEY (optional)
python verify_model.py          # sanity-check: loads the model + one real prediction
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Backend is now at `http://127.0.0.1:8000` (`/docs` for interactive API docs).

### 2. Frontend (Next.js)

```bash
cd frontend
npm install
cp .env.local.example .env.local   # NEXT_PUBLIC_API_BASE defaults to http://127.0.0.1:8000
npm run dev
```

Open `http://localhost:3000`.

---

## Model artifacts

The trained artifacts live in the repo root (produced in Google Colab) and are read via a
**configurable** directory (`ARTIFACTS_DIR`, default = repo root):

| File | Purpose |
|---|---|
| `birdvision_model.keras` | Trained EfficientNetB0 (Keras 3 / TF 2.21), 4.3M params, 36.4 MB |
| `class_names.json` | Exact ordered 200-class mapping (CUB-200-2011 labels) |
| `model_config.json` | Input size + preprocessing contract |
| `metrics.json` | Real held-out test metrics |
| `training_history.json`, `training_curves.png` | Training curves |
| `confusion_matrix.npy`, `confusion_matrix_top_classes.png` | Confusion matrix |
| `classification_report.csv` | Per-class precision/recall/F1/support |

**Preprocessing contract:** decode → RGB → resize 224×224 → float32 **in 0–255**.
EfficientNet's rescaling/normalization is baked into the network, so the backend does
**not** divide by 255 or call `preprocess_input` again (that would normalize twice).

Model binaries are gitignored; for deployment, mount or download them to `ARTIFACTS_DIR`.

---

## API

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | process health |
| GET | `/ready` | 200 if the CNN artifact is loaded, else 503 |
| GET | `/api/model-info` | architecture, version, class count, size, params |
| POST | `/api/predict` | multipart image → genuine CNN top-3 + confidence |
| POST | `/api/explain` | multipart image → Grad-CAM (original/heatmap/overlay) |
| GET | `/api/species/{id}` | species metadata (verified scientific name where known) |
| GET | `/api/species/{id}/intel` | Groq species intelligence (optional) |
| POST | `/api/species/{id}/ask` | Groq Q&A (optional) |
| GET | `/api/species/{id}/sightings` | **species-specific** eBird sightings + hotspots near a point |
| GET | `/api/observations/nearby` | eBird recent nearby observations (all species) |
| GET | `/api/metrics` | persisted evaluation metrics |

The species-specific sightings endpoint resolves the identified species to an
eBird species code via its **verified scientific name** against the official
eBird taxonomy (never by string-munging a common name), fetches recent
observations of that exact species, sorts them by distance from the search
center, and returns nearby hotspots. Every response echoes the exact
`search_center`, `radius_km` and `back_days` that were searched.

Safeguards: 10 MB upload limit, MIME + magic-byte validation, per-endpoint rate limits,
restricted CORS, consistent error envelopes, no stack traces / paths / secrets leaked.

---

## Testing

```bash
cd backend && pytest          # 34 tests; external APIs mocked, no paid calls
cd frontend && npm run build  # production build + type-check
```

**Last run:** 58 backend tests passed; frontend production build passed; full
upload→predict→Grad-CAM→insights flow verified in a real browser against the live CNN.

---

## Honest limitations

- Test top-1 is **71.06%** on 200 fine-grained classes; a ~19-point train/val gap shows
  some overfitting.
- Softmax scores are **uncalibrated** — shown as relative, not true probabilities.
- The abstention threshold is a heuristic and does **not** guarantee out-of-distribution
  detection for non-bird or unsupported-species images.
- Trained on 200 (largely North-American) species; anything else maps to the nearest
  known class.
- eBird "recent observations" ≠ abundance or range. Scientific names are shown only where
  human-verified; others are honestly marked unverified rather than fabricated.

See `docs/MODEL_CARD.md` and `docs/DATASET_CARD.md` for full detail.

---

## Security & privacy

- API keys are server-side only; `.env` and `*.keras` are gitignored.
- Uploaded images are processed in memory and not persisted.
- Geolocation is optional, requested only on explicit user action, and coordinates are
  not stored. Data sent to eBird/Groq is disclosed in the UI.

## Credits

- Dataset: **CUB-200-2011** (Caltech-UCSD Birds-200-2011).
- Observations: **eBird API 2.0** (Cornell Lab of Ornithology).
- Enrichment: **Groq** (openai/gpt-oss) via the OpenAI-compatible API.
