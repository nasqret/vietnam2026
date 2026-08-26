"""Model-v3 catalog trajectories are train-only, independently attested."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_ROOT = REPOSITORY_ROOT / "scripts"
for import_root in (REPOSITORY_ROOT, SCRIPTS_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from peano_lab.library.theorems import THEOREMS  # noqa: E402
from training.peano_policy import attest as attestor  # noqa: E402
from training.peano_policy.contract import MODEL_V3_LIBRARY_SIZE  # noqa: E402


def _load_builder() -> object:
    path = SCRIPTS_ROOT / "build_peano_policy_dataset.py"
    specification = importlib.util.spec_from_file_location(
        "_test_v3_split_lane_builder", path
    )
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


builder = _load_builder()


def test_v3_replay_watchdog_exceeds_measured_five_hour_build() -> None:
    assert attestor.REPLAY_WATCHDOG_SECONDS == 8 * 60 * 60


def _group(label: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    return ((f"family-{label}",), (f"lineage-{label}",))


def test_descendant_visible_catalog_targets_cannot_enter_holdout() -> None:
    target = _group("catalog-target")
    descendant = _group("catalog-descendant")
    synthetic = tuple(_group(f"synthetic-{index}") for index in range(4))
    session_groups = {
        "target": target,
        "descendant": descendant,
        **{
            f"synthetic-{index}": group
            for index, group in enumerate(synthetic)
        },
    }
    metadata = {
        "target": {
            "surface": "model-v3",
            "trajectory": builder.V3_CATALOG_TRAJECTORY,
        },
        "descendant": {
            "surface": "model-v3",
            "trajectory": builder.V3_CATALOG_TRAJECTORY,
        },
        **{
            f"synthetic-{index}": {
                "surface": "model-v3",
                "lane": builder.V3_SYNTHETIC_LANE,
            }
            for index in range(len(synthetic))
        },
    }
    forced = builder._v3_catalog_train_groups(session_groups, metadata)
    assert forced == frozenset((target, descendant))

    # Under the old all-component hash split, some deterministic seed can put
    # a target rung in holdout while a later rung remains in train.  The later
    # predecessor prefix literally contains the target theorem name, so this
    # is descendant leakage even if the target proof rows themselves are held.
    vulnerable_seed = None
    for index in range(2_000):
        candidate = f"descendant-leak-{index}"
        old = builder._assign_groups(
            session_groups.values(),
            seed=candidate,
            val_fraction=0.25,
            test_fraction=0.25,
        )
        if old[target] != "train" and old[descendant] == "train":
            vulnerable_seed = candidate
            break
    assert vulnerable_seed is not None
    assert THEOREMS[7].name in {spec.name for spec in THEOREMS[:9]}

    assignment = builder._assign_groups(
        session_groups.values(),
        seed=vulnerable_seed,
        val_fraction=0.25,
        test_fraction=0.25,
        forced_train_groups=forced,
    )
    assert assignment[target] == assignment[descendant] == "train"
    assert {
        group for group, split in assignment.items() if split != "train"
    } <= set(synthetic)


def test_attestor_rejects_catalog_rows_outside_train() -> None:
    prefix = 4
    spec = THEOREMS[prefix]
    record = {
        "surface": "model-v3",
        "session": "catalog-prefix-004",
        "formula": spec.statement,
        "theorem": spec.name,
        "metadata": {
            "library_prefix_length": prefix,
            "trajectory": attestor.V3_CATALOG_TRAJECTORY,
            "library_target_index": prefix,
            "library_target_name": spec.name,
            "statement": spec.statement,
        },
    }
    for split in ("val", "test"):
        with pytest.raises(
            attestor.DatasetAttestationError,
            match="outside the training split",
        ):
            attestor._record_v3_curriculum_evidence(
                record,
                {},
                library_size=MODEL_V3_LIBRARY_SIZE,
                location=f"forged-{split}",
                split=split,
            )

    evidence: dict[str, tuple[int, str, str]] = {}
    assert attestor._record_v3_curriculum_evidence(
        record,
        evidence,
        library_size=MODEL_V3_LIBRARY_SIZE,
        location="train-row",
        split="train",
    ) == attestor.V3_CATALOG_TRAJECTORY


def test_attestor_recomputes_and_rejects_forged_lane_populations() -> None:
    sessions = {
        attestor.V3_CATALOG_TRAJECTORY: {"catalog-a", "catalog-b"},
        attestor.V3_SYNTHETIC_LANE: {"synthetic-a"},
    }
    rows = {
        attestor.V3_CATALOG_TRAJECTORY: 17,
        attestor.V3_SYNTHETIC_LANE: 3,
    }
    exact = {
        attestor.V3_CATALOG_TRAJECTORY: {"sessions": 2, "rows": 17},
        attestor.V3_SYNTHETIC_LANE: {"sessions": 1, "rows": 3},
    }
    assert attestor._verify_v3_lane_populations(
        exact, sessions, rows, location="train"
    ) == exact
    forged = {
        **exact,
        attestor.V3_CATALOG_TRAJECTORY: {"sessions": 1, "rows": 17},
    }
    with pytest.raises(
        attestor.DatasetAttestationError,
        match="forged or stale",
    ):
        attestor._verify_v3_lane_populations(
            forged, sessions, rows, location="train"
        )
