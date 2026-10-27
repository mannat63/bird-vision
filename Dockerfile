# BirdVision AI backend — portable container (Hugging Face Spaces, Fly.io,
# Railway, Google Cloud Run, or any Docker host).
# Build context is the REPOSITORY ROOT (the root-level JSON artifacts are needed).
FROM python:3.11-slim

# Hugging Face Spaces (and good practice) run the container as a non-root user
# (UID 1000). Create it so the model download at startup can write to /app.
RUN useradd -m -u 1000 user

WORKDIR /app

# Install Python deps first (as root) for layer caching; they go to the shared
# system site-packages and remain importable by the non-root user.
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# App code + the small model-metadata artifacts that live at the repo root.
COPY backend/ backend/
COPY class_names.json model_config.json metrics.json ./

# Hand /app to the non-root user so download_model.py can write the .keras.
RUN chown -R user:user /app
USER user

ENV ARTIFACTS_DIR=/app \
    HOME=/home/user \
    PYTHONUNBUFFERED=1

WORKDIR /app/backend

# Hugging Face Spaces expects port 7860 (see app_port in README); most other
# PaaS inject $PORT. Support both.
EXPOSE 7860
CMD ["sh", "-c", "python download_model.py && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
