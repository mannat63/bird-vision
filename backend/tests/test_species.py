"""Species metadata tests (no TensorFlow required)."""

from __future__ import annotations

import json
from pathlib import Path

from app.services.species import (
    _scientific_map,
    label_to_common_name,
    species_record,
)

ARTIFACTS = Path(__file__).resolve().parents[2]


def test_common_name_strips_index_and_underscores():
    assert label_to_common_name("001.Black_footed_Albatross") == "Black footed Albatross"
    assert label_to_common_name("200.Common_Yellowthroat") == "Common Yellowthroat"


def test_class_names_are_unique_and_200():
    names = json.loads((ARTIFACTS / "class_names.json").read_text())
    assert len(names) == 200
    assert len(set(names)) == 200


def test_scientific_map_values_are_binomial():
    for label, sci in _scientific_map().items():
        assert not label.startswith("_")
        assert len(sci.split()) >= 2, f"{label} -> {sci}"


def test_species_record_marks_unverified_honestly():
    # Pick a label we did NOT curate -> scientific name must be None/unverified.
    rec = species_record(16, "017.Cardinal")
    assert rec["scientific_name"] is None
    assert rec["scientific_name_verified"] is False
    rec2 = species_record(0, "001.Black_footed_Albatross")
    assert rec2["scientific_name"] == "Phoebastria nigripes"
    assert rec2["scientific_name_verified"] is True
