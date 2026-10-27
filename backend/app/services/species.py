"""Species metadata layer.

Maps the *exact* model label (CUB-200-2011 folder names such as
``001.Black_footed_Albatross``) to display-ready common names and, where it has
been human-verified, a scientific name. Labels without a verified scientific
name are returned with ``scientific_name=None`` and flagged ``not verified`` so
the UI never presents a fabricated binomial.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SCI_NAME_FILE = DATA_DIR / "species_scientific.json"

_LABEL_RE = re.compile(r"^\d+\.(.+)$")


def label_to_common_name(label: str) -> str:
    """Derive a human-readable common name from a CUB folder label.

    ``001.Black_footed_Albatross`` -> ``Black footed Albatross``. Underscores in
    CUB encode both spaces and hyphens ambiguously, so we render them as spaces
    and document that the name is derived from the dataset label.
    """
    m = _LABEL_RE.match(label)
    core = m.group(1) if m else label
    return core.replace("_", " ").strip()


@lru_cache
def _scientific_map() -> dict[str, str]:
    if not SCI_NAME_FILE.exists():
        return {}
    data = json.loads(SCI_NAME_FILE.read_text(encoding="utf-8"))
    return {k: v for k, v in data.items() if not k.startswith("_")}


def species_record(species_id: int, label: str) -> dict:
    """Build a metadata record for one species.

    ``scientific_name_verified`` is explicit so callers never have to guess
    whether the binomial is authoritative.
    """
    sci = _scientific_map().get(label)
    return {
        "species_id": species_id,
        "label": label,
        "common_name": label_to_common_name(label),
        "scientific_name": sci,
        "scientific_name_verified": sci is not None,
        "taxonomy_source": "CUB-200-2011 dataset label"
        + ("; scientific name human-verified" if sci else ""),
    }
