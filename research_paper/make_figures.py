"""Generate all figures for the BirdVision AI research paper from REAL artifacts.

Every plotted number comes from the repository's saved evaluation artifacts
(metrics.json, training_history.json, confusion_matrix.npy,
classification_report.csv) or from drawn architecture diagrams (clearly
illustrative). Run:  python research_paper/make_figures.py
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

ROOT = Path(__file__).resolve().parent.parent
FIG = Path(__file__).resolve().parent / "figures"
FIG.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 8,
    "axes.titlesize": 9,
    "axes.labelsize": 8,
    "savefig.dpi": 300,
    "figure.dpi": 300,
})

GREEN = "#1b3a2f"
ACCENT = "#356350"
GRAY = "#555555"


# --------------------------------------------------------------------------- #
def fig_system_pipeline():
    """Figure 1: end-to-end system architecture (illustrative, column-width)."""
    fig, ax = plt.subplots(figsize=(3.3, 4.6))
    ax.set_xlim(0, 40)
    ax.set_ylim(0, 56)
    ax.axis("off")

    def box(x, y, w, h, text, fc="#eef3f0", ec=GREEN, fs=6.8):
        ax.add_patch(FancyBboxPatch((x, y), w, h,
                     boxstyle="round,pad=0.3,rounding_size=0.9",
                     linewidth=1.0, edgecolor=ec, facecolor=fc))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs)

    def arrow(x1, y1, x2, y2, color=GRAY):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                     mutation_scale=8, linewidth=0.9, color=color))

    # Core vertical CNN pipeline
    core = [
        (8, 50, 24, 5, "Image upload (Next.js UI)"),
        (8, 43, 24, 5, "Validation & preprocessing\n(RGB, 224x224, 0-255)"),
        (8, 36, 24, 5, "EfficientNetB0 inference\n(FastAPI backend)"),
        (8, 29, 24, 5, "Class-index mapping ->\nranked top-3 + confidence"),
        (8, 22, 24, 5, "Grad-CAM explanation"),
    ]
    for x, y, w, h, t in core:
        box(x, y, w, h, t)
    for i in range(len(core) - 1):
        arrow(20, core[i][1], 20, core[i + 1][1] + core[i + 1][3])

    # Enrichment services, conditioned on the identified species
    box(2, 9, 18, 7,
        "Groq LLM\n(openai/gpt-oss-120b)\nspecies intel + Q&A",
        fc="#f3efe6", ec=ACCENT, fs=6.2)
    box(21, 9, 17, 7,
        "eBird service\nspecies sightings\n+ hotspots",
        fc="#f3efe6", ec=ACCENT, fs=6.2)
    arrow(16, 29, 11, 16, color=ACCENT)
    arrow(24, 29, 29, 16, color=ACCENT)
    ax.add_patch(plt.Rectangle((0.5, 7), 39, 11, fill=False,
                 linestyle=(0, (4, 3)), edgecolor=GRAY, linewidth=0.8))
    ax.text(20, 4.2, "Optional enrichment (never performs\nCNN classification)",
            ha="center", va="center", fontsize=5.8, style="italic", color=GRAY)
    fig.tight_layout(pad=0.2)
    fig.savefig(FIG / "fig1_system_pipeline.png", bbox_inches="tight")
    plt.close(fig)


def fig_model_arch():
    """Figure 2: model architecture (illustrative diagram)."""
    fig, ax = plt.subplots(figsize=(3.3, 4.6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 48)
    ax.axis("off")
    stack = [
        ("Input  224 x 224 x 3  (RGB, 0-255)", "#eef3f0"),
        ("Train-time augmentation\nFlip / Rotation / Zoom / Contrast", "#f3efe6"),
        ("EfficientNetB0 backbone\n(ImageNet pre-trained)\ninternal rescaling + normalization", "#eef3f0"),
        ("Feature map  7 x 7 x 1280", "#eef3f0"),
        ("Global Average Pooling  ->  1280", "#eef3f0"),
        ("Dropout  (p = 0.3)", "#eef3f0"),
        ("Dense + softmax  ->  200 classes", "#dce8e1"),
    ]
    h = 5.0
    y = 42
    for i, (t, fc) in enumerate(stack):
        ax.add_patch(FancyBboxPatch((0.5, y), 9, h,
                     boxstyle="round,pad=0.3,rounding_size=0.6",
                     linewidth=1.0, edgecolor=GREEN, facecolor=fc))
        ax.text(5, y + h / 2, t, ha="center", va="center", fontsize=6.6)
        if i < len(stack) - 1:
            ax.add_patch(FancyArrowPatch((5, y), (5, y - 1.5),
                         arrowstyle="-|>", mutation_scale=8,
                         linewidth=0.9, color=GRAY))
        y -= (h + 1.5)
    fig.tight_layout(pad=0.2)
    fig.savefig(FIG / "fig2_model_arch.png", bbox_inches="tight")
    plt.close(fig)


def fig_training_curves():
    """Figure 3: training/validation curves from training_history.json."""
    h = json.loads((ROOT / "training_history.json").read_text())
    ep = np.arange(1, len(h["accuracy"]) + 1)
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(3.3, 4.3))

    a1.plot(ep, h["accuracy"], "-o", ms=3, color=GREEN, label="Train top-1")
    a1.plot(ep, h["val_accuracy"], "-s", ms=3, color=ACCENT, label="Val top-1")
    a1.plot(ep, h["val_top5_accuracy"], "--^", ms=3, color=GRAY, label="Val top-5")
    a1.set_xlabel("Epoch"); a1.set_ylabel("Accuracy"); a1.set_ylim(0, 1.02)
    a1.grid(True, lw=0.3, alpha=0.5); a1.legend(fontsize=6, loc="lower right")
    a1.set_title("(a) Accuracy")

    a2.plot(ep, h["loss"], "-o", ms=3, color=GREEN, label="Train loss")
    a2.plot(ep, h["val_loss"], "-s", ms=3, color=ACCENT, label="Val loss")
    a2.set_xlabel("Epoch"); a2.set_ylabel("Cross-entropy loss")
    a2.grid(True, lw=0.3, alpha=0.5); a2.legend(fontsize=6)
    a2.set_title("(b) Loss")
    fig.tight_layout(pad=0.4)
    fig.savefig(FIG / "fig3_training_curves.png", bbox_inches="tight")
    plt.close(fig)


def fig_confusion():
    """Figure 4: full 200x200 confusion matrix heatmap."""
    cm = np.load(ROOT / "confusion_matrix.npy").astype(float)
    row = cm.sum(1, keepdims=True)
    norm = np.divide(cm, row, out=np.zeros_like(cm), where=row > 0)
    fig, ax = plt.subplots(figsize=(3.4, 3.0))
    im = ax.imshow(norm, cmap="Greens", vmin=0, vmax=1, aspect="auto")
    ax.set_xlabel("Predicted class index")
    ax.set_ylabel("True class index")
    ax.set_title("Row-normalized confusion matrix (200 classes)")
    cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cb.ax.tick_params(labelsize=6)
    fig.tight_layout(pad=0.3)
    fig.savefig(FIG / "fig4_confusion.png", bbox_inches="tight")
    plt.close(fig)


def fig_perclass():
    """Figure 5: per-class F1 distribution + weakest classes."""
    rows = list(csv.reader((ROOT / "classification_report.csv").open()))[1:]
    pc = [(r[0][4:].replace("_", " "), float(r[3]))
          for r in rows if r[0] not in ("accuracy", "macro avg", "weighted avg")]
    f1 = np.array([x[1] for x in pc])
    worst = sorted(pc, key=lambda x: x[1])[:8]

    fig, (a1, a2) = plt.subplots(2, 1, figsize=(3.3, 4.3))
    a1.hist(f1, bins=20, color=ACCENT, edgecolor=GREEN, linewidth=0.5)
    a1.axvline(f1.mean(), color="black", ls="--", lw=1,
               label=f"mean F1 = {f1.mean():.3f}")
    a1.set_xlabel("Per-class F1-score"); a1.set_ylabel("Number of classes")
    a1.legend(fontsize=6); a1.set_title("(a) F1 distribution")
    a1.grid(True, lw=0.3, alpha=0.5, axis="y")

    names = [w[0] for w in worst][::-1]
    vals = [w[1] for w in worst][::-1]
    a2.barh(names, vals, color=GREEN)
    a2.set_xlabel("F1-score"); a2.set_xlim(0, 0.5)
    a2.tick_params(axis="y", labelsize=5.5)
    a2.set_title("(b) Eight weakest classes")
    a2.grid(True, lw=0.3, alpha=0.5, axis="x")
    fig.tight_layout(pad=0.4)
    fig.savefig(FIG / "fig5_perclass.png", bbox_inches="tight")
    plt.close(fig)


def copy_gradcam():
    """Figure 6: the shipped Grad-CAM example artifact (real)."""
    import shutil
    src = ROOT / "gradcam_example.png"
    if src.exists():
        shutil.copy(src, FIG / "fig6_gradcam.png")


if __name__ == "__main__":
    fig_system_pipeline()
    fig_model_arch()
    fig_training_curves()
    fig_confusion()
    fig_perclass()
    copy_gradcam()
    print("Figures written to", FIG)
    for p in sorted(FIG.glob("*.png")):
        print(" ", p.name)
