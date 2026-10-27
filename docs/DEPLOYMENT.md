# Deployment Guide

> Status: **not deployed publicly** from this environment (no hosting credentials were
> available). The steps below are the intended, tested-locally deployment path. A public
> URL should be claimed only after the deployed endpoints are actually verified.

## Topology
Two independently deployed services:

1. **Backend** (FastAPI + TensorFlow) — needs real CPU/RAM and the ~36 MB model artifact.
   **Do not** try to host the TensorFlow model inside a frontend serverless function or
   bundle it into client JS.
2. **Frontend** (Next.js) — static/edge-friendly; talks to the backend via
   `NEXT_PUBLIC_API_BASE`.

## Backend hosting
Pick a host that supports long-lived Python processes with enough memory for TF
(≥1 GB RAM recommended) — e.g. Render, Railway, Fly.io, a container on Cloud Run, or a VM.

Checklist before choosing:
- TensorFlow 2.21 CPU wheel available for the runtime (Python 3.11).
- Cold-start / model-load time acceptable (first inference traces the graph, ~3–4 s).
- Artifact delivery: mount a volume or download `birdvision_model.keras` + `class_names.json`
  + `model_config.json` + `metrics.json` into `ARTIFACTS_DIR` at boot.

### Container sketch
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
# Provide artifacts at runtime via a mount or an entrypoint download step:
ENV ARTIFACTS_DIR=/artifacts
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Backend environment variables
| Var | Required | Notes |
|---|---|---|
| `ARTIFACTS_DIR` | recommended | where model artifacts are mounted |
| `EBIRD_API_KEY` | optional | enables nearby observations |
| `GROQ_API_KEY` | optional | enables AI enrichment (Groq) |
| `GROQ_MODEL` | optional | default `openai/gpt-oss-120b` |
| `GROQ_FALLBACK_MODEL` | optional | default `openai/gpt-oss-20b` |
| `CORS_ORIGINS` | yes (prod) | set to the deployed frontend origin(s) only |
| `LOW_CONFIDENCE_THRESHOLD` | optional | abstention threshold (default 0.35) |

Readiness probe: `GET /ready` (503 until the model loads).

## Frontend hosting
Deploy `frontend/` to Vercel/Netlify/any Node host:
```bash
cd frontend
npm ci
npm run build
npm run start      # or the platform's build/start
```
Set `NEXT_PUBLIC_API_BASE=https://<your-backend-host>`.

## Production hardening
- Restrict `CORS_ORIGINS` to the exact frontend origin.
- Put the backend behind HTTPS and a rate-limiting proxy if exposed publicly.
- Rotate the eBird/Groq keys that were used during development before going public.
- Keep `.keras` binaries out of Git (already gitignored); deliver them out-of-band.

## Verifying a real deployment
```bash
curl https://<backend>/health
curl https://<backend>/ready
curl -F "file=@some_bird.jpg" https://<backend>/api/predict
```
Only after these succeed against the deployed host should the deployment be described as live.
