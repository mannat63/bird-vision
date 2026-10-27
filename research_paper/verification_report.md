# Verification Report — BirdVision AI Research Paper

Scope: what in `birdvision_research_paper.pdf` is verified from the repository,
what still requires evidence, unresolved discrepancies, and limitations of the
generated paper itself. Written to satisfy the research-integrity requirements
of the task.

## A. Claims verified against artifacts / code
| # | Claim in paper | How verified |
|---|---|---|
| 1 | 200 output units == 200 unique, ordered class names | Loaded model; `audit_prediction_integrity.py` §1; startup guard in `backend/app/ml/model.py` |
| 2 | Preprocessing is RGB 224×224 at 0–255 with NO double normalization | Introspected `Rescaling`+`Normalization` layers inside backbone; preprocessed tensor min 20 / max 255 (audit §2) |
| 3 | Test top-1 71.06%, top-5 92.44%, macro-F1 0.7146 | `metrics.json`, recomputed from `confusion_matrix.npy` to 4 d.p. (audit §3) |
| 4 | Per-class F1 range 0.19–0.98 (mean 0.715); named best/worst classes | `classification_report.csv` |
| 5 | Confusion pairs (Chipping→Tree Sparrow ×15, etc.) | `confusion_matrix.npy` off-diagonal ranking |
| 6 | Params 4,305,771 (2,293,720 trainable); dropout 0.3; artifact 36.4 MB | Model introspection |
| 7 | Augmentation = Flip/Rotation(±0.08)/Zoom/Contrast(0.1) | Read from saved `training_augmentation` sub-model |
| 8 | 20 training epochs; LR 1e-3 decaying; train 0.936 / val ~0.72 | `training_history.json` |
| 9 | Grad-CAM targets final backbone feature map; eager-tape; degenerate-map guard | `backend/app/ml/gradcam.py`; live overlay verified earlier |
| 10 | Groq `openai/gpt-oss-120b` (fallback 20b) returns 200; server-side key | Live API calls returned HTTP 200 |
| 11 | eBird species-specific sightings + hotspots; taxon via verified sci-name (128/200) | Live API; `backend/app/services/ebird.py`; `species_scientific.json` |
| 12 | OOD inputs (noise/grey) score 0.12 / 0.01 → flagged uncertain | `audit_prediction_integrity.py` §5 |
| 13 | 58 passing backend tests | `pytest` run (reported earlier in the project) |

## B. External published facts (verified via web, cited)
All 18 references are canonical and were checked. Four domain/detail-sensitive
citations were verified against primary/official sources during drafting:
CUB-200-2011 tech report CNS-TR-2011-001 (Caltech dataset page); eBird
(Sullivan et al., *Biol. Conserv.* 142(10):2282–2292, 2009); BirdNET
(Kahl et al., *Ecol. Inform.* 61:101236, 2021); iNaturalist (Van Horn et al.,
CVPR 2018, pp. 8769–8778); Bilinear CNN 84.1% on CUB (Lin et al., ICCV 2015).
Reported figures from other works are presented as **not directly comparable**
(different datasets/modalities/protocols); no ranking claim is made.

## C. Claims explicitly marked as requiring verification (not fabricated)
- Optimizer, batch size, exact LR schedule, loss function — the training
  notebook is absent; cross-entropy is stated as the conventional choice, not as
  a logged fact.
- Head-training vs. fine-tuning epoch boundary and the exact set of unfrozen
  layers.
- Split assignment methodology (random vs. official CUB partition) and any
  duplicate/leakage audit — not performed.
- Training hardware (a GPU is implied by `metrics.json`; exact device not given).

## D. Unresolved discrepancies between sources
- **Dataset naming:** config records a Kaggle slug, but labels are CUB-200-2011.
  Resolved in the paper by reporting CUB-200-2011 and explaining the mirror.
- **Validation vs. test:** best validation top-1 (72.37%) is slightly above test
  top-1 (71.06%); the paper reports test only, as the headline, and flags the
  gap.
- **Latency:** `metrics.json` records ~293 ms on GPU; local CPU runs showed
  ~130–290 ms warm and multi-second cold. Both are reported.
- No contradictions were found between the saved metrics, the confusion matrix,
  and the per-class report — they are mutually consistent to 4 d.p.

## E. Known bugs / status at time of writing
- The Groq-backed backend server process had exited (a background task reported
  a non-zero exit) when the paper was built; this does not affect the paper,
  whose figures derive from static artifacts. The Groq integration itself was
  verified returning HTTP 200 earlier and the code is unchanged.
- No application code or model weights were modified to support the paper.

## F. Limitations of the generated paper
- **Toolchain:** no LaTeX/poppler was available, so the PDF is produced with
  reportlab rather than compiled from the IEEEtran `.tex`. The layout faithfully
  follows the two-column IEEE style of the reference but is not byte-identical to
  an IEEEtran build. The editable `.tex` is provided for an authentic compile.
- **Figures/tables are column-width.** Unlike the reference, which occasionally
  spans both columns, all figures/tables here fit a single column (the system
  diagram was drawn vertically for this reason). This is a deliberate, documented
  deviation for generation robustness; no content is lost.
- **`.docx`** is a single-column editable export (not a two-column reproduction);
  equations and figures are embedded as images.
- **No field validation.** The paper documents system behaviour and benchmark
  metrics; it does not claim expert-verified field accuracy, and the previously
  observed screenshot cases could not be re-run (image files absent).

## G. Integrity statement
No experimental results, dataset statistics, training settings, author details,
citations, or API capabilities were fabricated. Measured results, implementation
facts, external published findings, and proposed future work are separated
throughout. Author/affiliation fields are left as placeholders because they were
not supplied or verifiable.
