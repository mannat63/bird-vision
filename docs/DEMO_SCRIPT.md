# Recruiter Demo Script (3–5 minutes)

**Goal:** show genuine ML, sound evaluation, and thoughtful product engineering.

### 0. Setup (before the call)
```bash
# Terminal 1
cd backend && uvicorn app.main:app --port 8000
# Terminal 2
cd frontend && npm run dev
```
Have one clear single-bird photo ready. Open `http://localhost:3000`.

---

### 1. The hook (30s)
> "BirdVision AI identifies bird species from a photo using a CNN I trained — EfficientNetB0
> on CUB-200-2011, 200 species. The classifier runs in a Python service; everything else is
> optional enrichment around it."

### 2. Live prediction (60s)
- Drag in the bird photo. Point out the loading state → result appears.
- Show **top-3 candidates** with scores and the **confidence note**:
  > "Scores are raw softmax — I label them as uncalibrated rather than pretending they're
  > probabilities. Below a threshold the app says *unable to identify reliably* instead of
  > guessing."

### 3. Explainability (45s)
- Click **Show heatmap** → Original / Heatmap / Overlay.
  > "Grad-CAM on the backbone's final feature map — it shows which regions drove the class
  > score. It's attribution, not proof of reasoning."

### 4. Enrichment, clearly separated (45s)
- Open species details → **Generate AI species intelligence** (Groq), and **Ask the bird
  expert**.
  > "Groq (openai/gpt-oss) explains the species the CNN already identified — it never classifies the image,
  > and the classifier works with the LLM fully offline."
- *(If Groq is rate-limited, show the graceful 'unavailable' state — that's the point:
  the CNN is independent.)*

### 5. Real geographic data (30s)
- Open **Nearby birds** → a preset city (or "Use my location").
  > "These are real recent eBird observations with dates, locations, and checklist IDs —
  > an API error is shown distinctly from a genuine 'no observations' result. Recent
  > reports aren't the same as range or abundance."

### 6. The differentiator — Model Insights (60s)
- Go to **Model Insights**.
  > "Every number here comes from a real evaluation artifact: test top-1 71.1%, top-5 92.4%,
  > macro-F1 71.5%. Training curves, confusion matrix, and per-class performance — sorted
  > weakest-first, so I can talk about *where* it fails: visually similar sparrows, gulls,
  > flycatchers. And I'm upfront about the ~19-point train/val gap."

### 7. Close (20s)
> "The engineering principles throughout: the CNN is the source of truth, nothing is faked,
> secrets stay server-side, and limitations are stated honestly. Backend has 34 passing
> tests; the frontend production build is green."

---

### Likely questions & crisp answers
- **Why 71% and not higher?** Fine-grained 200-class problem, small per-class data,
  EfficientNetB0 base. Next steps: stronger augmentation, longer fine-tuning, a larger
  backbone, class-balanced losses.
- **Preprocessing?** 224×224 RGB in 0–255; EfficientNet normalization is internal — no
  double normalization.
- **How do you know the mapping is right?** Output units are validated against
  `class_names.json` at load; a test asserts output index → label consistency.
- **Is the deployment live?** Built and verified locally end-to-end; public hosting needs
  credentials — the deploy guide is ready and I don't claim a live URL I haven't verified.
