# BirdVision AI backend — portable container (Hugging Face Spaces, Fly.io,
# Railway, Google Cloud Run, or any Docker host).
# Build context is the REPOSITORY ROOT (the root-level JSON artifacts are needed).
FROM python:3.11-slim

# System deps kept minimal; tensorflow-cpu wheels are self-contained.
WORKDIR /app

# Install Python deps first for layer caching.
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# App code + the small model-metadata artifacts that live at the repo root.
COPY backend/ backend/
COPY class_names.json model_config.json metrics.json ./

# Artifacts (incl. the downloaded model) live at /app; see app/config.py.
ENV ARTIFACTS_DIR=/app \
    PYTHONUNBUFFERED=1

WORKDIR /app/backend

# Hugging Face Spaces expects port 7860; most PaaS inject $PORT. Support both.
EXPOSE 7860
CMD ["sh", "-c", "python download_model.py && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
