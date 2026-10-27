# Deploying BirdVision AI — Frontend on Vercel, Backend on a separate host

The app is two pieces that deploy separately and talk over HTTPS:

- **Frontend** (Next.js) → **Vercel**.
- **Backend** (FastAPI + TensorFlow) → a host that can run a long-lived Python
  process with ~1 GB RAM. Vercel *cannot* run this part (serverless size/memory
  limits), so the backend goes elsewhere.

> **Keys security:** the Groq and eBird keys are SECRET and go only on the
> **backend** host. On Vercel you set just one, non-secret variable
> (`NEXT_PUBLIC_API_BASE`). Never put the API keys on Vercel — anything in the
> frontend is visible in the browser.

---

## Step 0 — Put the model file somewhere downloadable (once)

The trained `birdvision_model.keras` (~36 MB) is intentionally not in Git, so the
backend downloads it on boot from `MODEL_URL`. The easiest free host is a GitHub
Release on your repo:

1. Go to `https://github.com/mannat63/bird-vision/releases` → **Draft a new
   release** → tag `v1.0` → **Attach** `birdvision_model.keras` (drag the file
   from `C:\Users\manna\Desktop\bird_classification\`) → **Publish**.
2. Right-click the uploaded asset → **Copy link**. It looks like:
   `https://github.com/mannat63/bird-vision/releases/download/v1.0/birdvision_model.keras`
   That URL is your **`MODEL_URL`**.

The small `class_names.json`, `model_config.json` and `metrics.json` are already
in the repo, so they need no download.

---

## Step 1 — Deploy the backend

Pick **one** host. Option A is free and has plenty of RAM; Option B is the most
mainstream but its free tier is too small for TensorFlow.

### Option A (recommended, free) — Hugging Face Spaces (Docker)
Free tier gives 2 vCPU and 16 GB RAM, which comfortably runs TensorFlow.

1. Create a free account at huggingface.co.
2. **New → Space** → name it (e.g. `birdvision-backend`) → **SDK: Docker** →
   **Blank** → Create.
3. Push this repo to the Space (HF shows the exact git remote), e.g.:
   ```bash
   git remote add space https://huggingface.co/spaces/<you>/birdvision-backend
   git push space main
   ```
   (The repo already has a root `Dockerfile` that HF Spaces will build.)
4. In the Space → **Settings → Variables and secrets**, add **Secrets**:
   - `GROQ_API_KEY` = your Groq key
   - `EBIRD_API_KEY` = your eBird key
   - `MODEL_URL` = the GitHub Release link from Step 0
   - `CORS_ORIGINS` = your Vercel URL (fill in after Step 2, e.g.
     `https://bird-vision.vercel.app`)
5. The Space builds and starts. Your backend URL is
   `https://<you>-birdvision-backend.hf.space`.
6. Check it: open `.../health` (should return `{"status":"ok"}`) and `.../ready`.

### Option B — Render (Blueprint)
The repo includes `render.yaml`. **Note:** Render's Free/Starter instances are
512 MB and will likely run out of memory loading TensorFlow; the blueprint
therefore defaults to the **Standard** (2 GB, paid) plan.

1. Create an account at render.com → **New + → Blueprint** → connect the repo.
2. Render reads `render.yaml` and prompts for the `sync:false` values:
   `GROQ_API_KEY`, `EBIRD_API_KEY`, `MODEL_URL`, `CORS_ORIGINS`.
3. Deploy. Your backend URL is `https://birdvision-backend.onrender.com` (or
   similar). Health check path is `/health`.

---

## Step 2 — Deploy the frontend on Vercel

1. vercel.com → **Add New → Project** → import the repo.
2. **Root Directory: `frontend`** (important — the Next.js app lives there).
   Framework preset auto-detects as Next.js.
3. **Environment Variables** → add ONE:
   ```
   NEXT_PUBLIC_API_BASE = https://<your-backend-url-from-step-1>
   ```
   (no trailing slash). Do **not** add the Groq/eBird keys here.
4. Deploy. Vercel gives you a URL like `https://bird-vision.vercel.app`.

---

## Step 3 — Link the two (CORS)

Back on the backend host, set/confirm:
```
CORS_ORIGINS = https://bird-vision.vercel.app
```
(the exact Vercel URL from Step 2). Redeploy/restart the backend so it accepts
requests from your frontend. If you later add a custom domain, add it here too
(comma-separated).

---

## Step 4 — Verify end-to-end

- Open the Vercel URL. The landing page loads.
- Upload a bird photo → you should get a prediction (this proves the frontend is
  reaching the backend and the model loaded).
- If it says **"model unavailable"**: the backend is up but the model did not
  download — check `MODEL_URL` and the backend logs.
- If uploads fail with a network/CORS error: `NEXT_PUBLIC_API_BASE` is wrong, or
  `CORS_ORIGINS` on the backend does not match the Vercel URL.

---

## Environment variable summary

| Variable | Where | Secret? | Value |
|---|---|---|---|
| `NEXT_PUBLIC_API_BASE` | **Vercel** (frontend) | No | backend URL |
| `GROQ_API_KEY` | backend host | **Yes** | your Groq key |
| `EBIRD_API_KEY` | backend host | **Yes** | your eBird key |
| `MODEL_URL` | backend host | No | GitHub Release link to the .keras |
| `CORS_ORIGINS` | backend host | No | your Vercel URL |
| `GROQ_MODEL` | backend host | No | `openai/gpt-oss-120b` (default) |
| `GROQ_FALLBACK_MODEL` | backend host | No | `openai/gpt-oss-20b` (default) |

First inference after an idle period is slow (model graph tracing / cold start);
subsequent requests are fast.
