# Reproducibility Notes — BirdVision AI Research Paper

This document records the provenance of every quantitative claim in
`birdvision_research_paper.pdf` and how to regenerate the deliverables.

## 1. Dataset provenance
- **Dataset:** Caltech-UCSD Birds-200-2011 (CUB-200-2011), 200 species, 11,788 images.
- **Source recorded in config:** `backend/app/model_config.json` and `metrics.json`
  list the Kaggle slug `veeralakrishna/200-bird-species-with-11788-images`. The
  class labels in `class_names.json` are CUB folder identifiers
  (`001.Black_footed_Albatross` … `200.Common_Yellowthroat`), confirming the
  Kaggle item is a CUB-200-2011 mirror, not a different dataset.
- **Splits used (from `metrics.json`):** train 5,194 / validation 800 /
  held-out test 5,794 (sum = 11,788).
- **Per-class test support:** min 11, max 30, mean 29.0 (from
  `classification_report.csv`).
- **Not available:** the raw image files, the official-vs-random split
  assignment, and any duplicate/leakage audit. These are **not** in the
  repository and are flagged as requiring verification.

## 2. Metrics sources (all values trace to a file)
| Claim | Source artifact |
|---|---|
| Top-1 71.06%, Top-5 92.44% | `metrics.json` |
| Macro P/R/F1 0.7352 / 0.7127 / 0.7146; weighted F1 0.7127 | `metrics.json` |
| Confusion matrix, confusion pairs | `confusion_matrix.npy` |
| Per-class P/R/F1/support, best/worst classes, F1 range 0.19–0.98 | `classification_report.csv` |
| Training curves (20 epochs), LR 1e-3→~0 | `training_history.json` |
| Params 4,305,771 (2,293,720 trainable), 36.4 MB, dropout 0.3, augmentation | introspected from `birdvision_model.keras` |
| Latency mean 293 ms / p95 313 ms (GPU) | `metrics.json` |
| Metrics recomputed from confusion matrix match `metrics.json` to 4 d.p. | `backend/audit_prediction_integrity.py` |

**Independent cross-check:** `backend/audit_prediction_integrity.py` recomputes
top-1, macro precision, recall and F1 directly from `confusion_matrix.npy` and
confirms they equal `metrics.json` (and `classification_report.csv`) to four
decimal places, establishing class-index integrity end-to-end.

## 3. Experiment configuration
- **Model:** EfficientNetB0 (ImageNet-pretrained) → GlobalAveragePooling2D →
  Dropout(0.3) → Dense(200, softmax).
- **Input:** 224×224×3 RGB, pixel range 0–255 (internal `Rescaling` +
  `Normalization` layers verified inside the backbone; no external /255).
- **Augmentation (read from the saved model):** RandomFlip(horizontal),
  RandomRotation(±0.08 rad), RandomZoom, RandomContrast(0.1).
- **Trainable fraction:** 2,293,720 of 4,305,771 → partial fine-tuning into the
  upper backbone.
- **Seed:** 42 (`model_config.json`).
- **NOT recorded (requires verification):** optimizer identity, batch size,
  exact LR schedule, loss function (cross-entropy is the conventional choice and
  is stated as such), head-vs-fine-tune epoch boundary, training hardware. The
  Colab training notebook is not in the repository.

## 4. Environment
- Python 3.11; TensorFlow/Keras 2.21 / 3.13 (per `metrics.json` and artifact).
- Paper tooling (this directory): `pymupdf`, `matplotlib`, `reportlab`,
  `python-docx` in `backend/venv`.
- No LaTeX/poppler toolchain was available in the build environment; the PDF is
  generated with reportlab (see §6).

## 5. External services (implementation facts, not experiments)
- **Groq LLM:** `openai/gpt-oss-120b` (fallback `openai/gpt-oss-20b`), verified
  available and returning HTTP 200; server-side key only.
- **eBird API 2.0:** species code resolved from the human-verified scientific
  name (128/200 classes) against the official eBird taxonomy; species-specific
  observations + hotspots verified live.

## 6. Regenerating the deliverables
From the repository root, using the backend virtual environment:

```bash
# figures (from real artifacts) + equation images
backend/venv/Scripts/python.exe research_paper/make_figures.py
backend/venv/Scripts/python.exe -c "import sys; sys.path.insert(0,'research_paper'); \
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt; \
from paper_content import EQUATIONS; from pathlib import Path; \
F=Path('research_paper/figures'); plt.rcParams.update({'mathtext.fontset':'cm'}); \
[ (lambda n,e: (plt.figure(figsize=(3.2,0.55)).text(0.5,0.5,f'\${e}\$',ha='center',va='center',fontsize=13) or plt.savefig(F/f'eq{n}.png',dpi=300,bbox_inches='tight',pad_inches=0.04,transparent=True) or plt.close()))(n,e) for n,e in EQUATIONS.items() ]"

# PDF (primary), LaTeX source + .bib, and Word export
backend/venv/Scripts/python.exe research_paper/build_pdf.py
backend/venv/Scripts/python.exe research_paper/build_tex.py
backend/venv/Scripts/python.exe research_paper/build_docx.py
```

The equation step is also embedded in the build if preferred; the simplest full
rebuild is `make_figures.py` then `build_pdf.py`. To compile the LaTeX source to
PDF (not done here), run `pdflatex birdvision_research_paper.tex` twice in a TeX
environment such as Overleaf.

## 7. Known limitations of the artifacts
- Validation best top-1 (72.37%) ≠ test top-1 (71.06%); the paper reports the
  **test** figure as the headline and never substitutes validation for test.
- Softmax scores are uncalibrated; no calibration error (ECE) was computed.
- No out-of-distribution detector was trained or evaluated.
- The three previously-observed screenshot cases could not be re-evaluated: the
  image files are not in the repository.
