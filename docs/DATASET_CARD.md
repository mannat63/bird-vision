# Dataset Card — CUB-200-2011

## Identity & provenance
- **Dataset:** Caltech-UCSD Birds-200-2011 (CUB-200-2011).
- **Content:** ~11,788 images across **200** bird species, with per-image species labels.
- **Label format used as the model's class mapping:** the original CUB folder names, e.g.
  `001.Black_footed_Albatross` … `200.Common_Yellowthroat` (see `class_names.json`).

### Note on the Kaggle slug
`model_config.json` / `metrics.json` record the source as the Kaggle dataset
`veeralakrishna/200-bird-species-with-11788-images`. That Kaggle dataset is a **mirror of
CUB-200-2011** (same 200 species, same ~11,788 images, same label scheme). The project does
**not** claim a different dataset was used — the artifacts are authoritative and the class
labels are unambiguously CUB-200-2011.

## Splits actually used in this project
| Split | Images |
|---|---|
| Train | 5,194 |
| Validation | 800 |
| Test (held-out) | 5,794 |
| **Classes** | **200** |

The held-out test set was untouched during tuning and used only for the final metrics in
`metrics.json`.

## Known biases & caveats
- Species are heavily **North-American-centric**; global coverage is limited.
- Fine-grained, visually similar species make some classes intrinsically hard.
- Class support in the test set is roughly balanced (~29–30 images/class) but not identical.
- Historical English names in CUB may differ slightly from current taxonomic authorities;
  scientific names are attached only where human-verified (`backend/app/data/species_scientific.json`).

## Licensing
CUB-200-2011 is distributed for research/educational use by Caltech. Review the dataset's
terms before any commercial redistribution. This project ships only the derived model and
small evaluation artifacts, not the raw image dataset.
