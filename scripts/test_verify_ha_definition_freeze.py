"""Focused mutation tests for the HA definition-freeze validator."""

from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
FREEZE_PATH = (
    REPOSITORY_ROOT
    / "research"
    / "arithmetic-library"
    / "ha-definition-representation-freeze-v1.json"
)
VALIDATOR_PATH = REPOSITORY_ROOT / "scripts" / "verify_ha_definition_freeze.py"


def _load_validator():
    spec = importlib.util.spec_from_file_location(
        "verify_ha_definition_freeze_under_test", VALIDATOR_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


VALIDATOR = _load_validator()


def _freeze() -> dict[str, object]:
    with FREEZE_PATH.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def _write_freeze(tmp_path: Path, value: dict[str, object]) -> Path:
    path = tmp_path / "freeze.json"
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    return path


def _definition(freeze: dict[str, object], name: str) -> dict[str, object]:
    return next(item for item in freeze["definitions"] if item["name"] == name)


def test_repository_definition_freeze_validates_without_replay() -> None:
    summary = VALIDATOR.validate_freeze(REPOSITORY_ROOT, FREEZE_PATH)
    assert summary == {
        "definitions": 11,
        "proved_api_rows": 45,
        "distinct_public_theorems": 44,
        "representation_obligations": 4,
        "replayed_public_theorems": 0,
    }


def test_duplicate_json_key_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "duplicate.json"
    path.write_text('{"schema":"first","schema":"second"}\n', encoding="utf-8")
    with pytest.raises(VALIDATOR.FreezeError, match="duplicate JSON key 'schema'"):
        VALIDATOR.validate_freeze(REPOSITORY_ROOT, path)


def test_changed_exact_template_is_rejected(tmp_path: Path) -> None:
    freeze = deepcopy(_freeze())
    _definition(freeze, "Dvd")["exact_expanded_template"] = "exists k. n = k * d"
    path = _write_freeze(tmp_path, freeze)
    with pytest.raises(
        VALIDATOR.FreezeError, match="does not exactly match the live registry template"
    ):
        VALIDATOR.validate_freeze(REPOSITORY_ROOT, path)


def test_changed_template_hash_is_rejected(tmp_path: Path) -> None:
    freeze = deepcopy(_freeze())
    _definition(freeze, "Prime")["template_source_sha256"] = "0" * 64
    path = _write_freeze(tmp_path, freeze)
    with pytest.raises(
        VALIDATOR.FreezeError, match="does not match exact template bytes"
    ):
        VALIDATOR.validate_freeze(REPOSITORY_ROOT, path)


def test_changed_campaign_classification_is_rejected(tmp_path: Path) -> None:
    freeze = deepcopy(_freeze())
    _definition(freeze, "ModEq")["campaign_classification"] = "frozen-compatible"
    path = _write_freeze(tmp_path, freeze)
    with pytest.raises(
        VALIDATOR.FreezeError, match="must remain 'bridge-required' in freeze v1"
    ):
        VALIDATOR.validate_freeze(REPOSITORY_ROOT, path)


def test_nonpublic_api_theorem_is_rejected(tmp_path: Path) -> None:
    freeze = deepcopy(_freeze())
    _definition(freeze, "Le")["proved_api"][0]["name"] = "invented_public_theorem"
    path = _write_freeze(tmp_path, freeze)
    with pytest.raises(
        VALIDATOR.FreezeError, match="is absent from the public theorem registry"
    ):
        VALIDATOR.validate_freeze(REPOSITORY_ROOT, path)


@pytest.mark.parametrize(
    ("field", "replacement", "message"),
    [
        ("stable_id", "PD9999", "does not match the live registry"),
        ("parameters", ["b", "a"], "does not match live parameter order"),
        ("registry_class", "adjacent", "is not in the live adjacent registry"),
    ],
)
def test_live_definition_identity_mutations_are_rejected(
    tmp_path: Path, field: str, replacement: object, message: str
) -> None:
    freeze = deepcopy(_freeze())
    _definition(freeze, "Le")[field] = replacement
    path = _write_freeze(tmp_path, freeze)
    with pytest.raises(VALIDATOR.FreezeError, match=message):
        VALIDATOR.validate_freeze(REPOSITORY_ROOT, path)


def test_baseline_file_hash_mutation_is_rejected(tmp_path: Path) -> None:
    freeze = deepcopy(_freeze())
    freeze["baseline"]["definition_inventory_sha256"] = "f" * 64
    path = _write_freeze(tmp_path, freeze)
    with pytest.raises(VALIDATOR.FreezeError, match="does not match"):
        VALIDATOR.validate_freeze(REPOSITORY_ROOT, path)


def test_controlling_blueprint_path_escape_is_rejected(tmp_path: Path) -> None:
    freeze = deepcopy(_freeze())
    freeze["baseline"]["controlling_spec_path"] = (
        "../ha_number_theory_formalization_campaign.md"
    )
    path = _write_freeze(tmp_path, freeze)
    with pytest.raises(VALIDATOR.FreezeError, match="repository-relative path"):
        VALIDATOR.validate_freeze(REPOSITORY_ROOT, path)


def test_beta_and_product_cannot_be_promoted_to_foundations(tmp_path: Path) -> None:
    freeze = deepcopy(_freeze())
    _definition(freeze, "BetaAt")["campaign_classification"] = "frozen-compatible"
    _definition(freeze, "BetaAt")["required_bridge_theorems"] = []
    path = _write_freeze(tmp_path, freeze)
    with pytest.raises(VALIDATOR.FreezeError, match="must remain 'legacy-late'"):
        VALIDATOR.validate_freeze(REPOSITORY_ROOT, path)


def test_crt_cannot_precede_the_noncrt_list_foundation(tmp_path: Path) -> None:
    freeze = deepcopy(_freeze())
    order = freeze["k3_quarantine"]["required_foundational_order"]
    order[1], order[4] = order[4], order[1]
    path = _write_freeze(tmp_path, freeze)
    with pytest.raises(
        VALIDATOR.FreezeError, match="must put non-CRT pair/list/folds before CRT"
    ):
        VALIDATOR.validate_freeze(REPOSITORY_ROOT, path)
