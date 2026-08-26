"""Strict loading and source binding for the model-v3 curriculum."""

from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
import sys

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
PEANO_PYTHON = REPOSITORY_ROOT / "peano-lab" / "py"
for import_root in (REPOSITORY_ROOT, PEANO_PYTHON):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from training.peano_policy.contract import (  # noqa: E402
    environment_record,
    model_v1_environment,
)
import training.peano_policy.curriculum as curriculum_module  # noqa: E402
from training.peano_policy.curriculum import (  # noqa: E402
    CURRICULUM_FORMAT,
    CurriculumLoadError,
    LoadedCurriculum,
    canonical_curriculum_json,
    curriculum_record_sha256,
    load_curriculum,
)
from training.peano_policy.data import ROW_FIELDS  # noqa: E402
from training.peano_policy.prompt import (  # noqa: E402
    PromptEnvironment,
    PromptError,
    prompt_manifest_record,
    render_prompt,
)
from training.peano_policy.selection import (  # noqa: E402
    CATALOG_LANE,
    SYNTHETIC_LANE,
    CurriculumSelectionContract,
    row_from_validated_record,
)


TEST_SCHEMA = "test-root-refl"
TEST_CONTRACT = CurriculumSelectionContract(
    library_size=2,
    expected_catalog_rows=2,
    root_heads=("refl",),
    schema_heads=((TEST_SCHEMA, "refl"),),
)


def _row(
    *,
    environment: PromptEnvironment,
    session: str,
    theorem: str,
    formula: str,
    metadata: dict[str, object],
) -> dict[str, object]:
    goals = ("⊢ 0 = 0",)
    row = {
        "v": 1,
        "task": "next_tactic",
        "env": environment.text,
        "surface": environment.capabilities.label,
        "environment_sha256": environment.sha256,
        "classical": False,
        "capabilities": environment.capabilities.to_record(),
        "split": "train",
        "session": session,
        "step": 1,
        "formula": formula,
        "theorem": theorem,
        "family": f"test/{session}",
        "lineage": f"test/{session}",
        "state": list(goals),
        "focus": 0,
        "prompt": render_prompt(
            goals=goals,
            focus=0,
            environment=environment,
        ),
        "completion": "refl</tactic>",
        # The production builder sorts metadata extras before row emission.
        "metadata": dict(sorted(metadata.items())),
    }
    assert tuple(row) == ROW_FIELDS
    return row


def _build_artifacts() -> tuple[bytes, bytes]:
    # The generic builder-row validator is exercised with a tiny, genuine
    # model-v1 environment.  An autouse seam below changes only the selector's
    # surface label, allowing this loader test to stay bounded; model-v3's real
    # row adapter and 247-target contract have their own focused selector tests.
    environment = model_v1_environment()
    rows: list[dict[str, object]] = []
    for index in range(2):
        rows.append(
            _row(
                environment=environment,
                session=f"catalog-{index:03d}",
                theorem=f"catalog_{index}",
                formula="0 = 0",
                metadata={
                    "library_size": 2,
                    "library_prefix_length": index,
                    "trajectory": CATALOG_LANE,
                    "library_target_index": index,
                    "library_target_name": f"catalog_{index}",
                    "tactics": ["refl"],
                },
            )
        )

    rows.append(
        _row(
            environment=environment,
            session="synthetic-refl",
            theorem="synthetic.refl",
            formula="0 = 0",
            metadata={
                "library_size": 2,
                "library_prefix_length": 2,
                "lane": SYNTHETIC_LANE,
                "template": TEST_SCHEMA,
                "root_first_tactic_head": "refl",
                "tactic_rows": 1,
                "tactics": ["refl"],
            },
        )
    )

    train = "".join(
        json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n"
        for row in rows
    ).encode("utf-8")
    empty_hash = hashlib.sha256(b"").hexdigest()
    manifest = {
        "format": "peano-lab-next-tactic",
        "version": 1,
        "trace_version": 1,
        "prompt": prompt_manifest_record(),
        "split": {"method": "test-model-v3-curriculum"},
        "source": {"qed_true_sessions": len(rows)},
        "replay": {
            "attempted_qed_sessions": len(rows),
            "accepted_kernel_checked_sessions": len(rows),
            "positive_rows": len(rows),
            "transactional_error_steps_ignored": 0,
        },
        "environments": [
            {**environment_record(environment), "sessions": len(rows)}
        ],
        "splits": {
            "train": {
                "groups": [],
                "sessions": len(rows),
                "rows": len(rows),
                "sha256": hashlib.sha256(train).hexdigest(),
            },
            "val": {
                "groups": [],
                "sessions": 0,
                "rows": 0,
                "sha256": empty_hash,
            },
            "test": {
                "groups": [],
                "sessions": 0,
                "rows": 0,
                "sha256": empty_hash,
            },
        },
        "dataset_sha256": "not-used-by-the-split-loader",
    }
    manifest_raw = (
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    ).encode("utf-8")
    return train, manifest_raw


@pytest.fixture(scope="module")
def canonical_artifacts() -> tuple[bytes, bytes]:
    return _build_artifacts()


@pytest.fixture
def dataset(
    tmp_path: Path,
    canonical_artifacts: tuple[bytes, bytes],
) -> Path:
    train, manifest = canonical_artifacts
    path = tmp_path / "train.jsonl"
    path.write_bytes(train)
    (tmp_path / "manifest.json").write_bytes(manifest)
    return path


@pytest.fixture(autouse=True)
def bounded_model_v3_adapter_seam(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep loader tests small while retaining the production row adapter."""

    def adapt(example: object, record: dict[str, object]) -> object:
        selector_record = dict(record)
        selector_record["surface"] = "model-v3"
        return row_from_validated_record(example, selector_record)

    monkeypatch.setattr(
        curriculum_module,
        "row_from_validated_record",
        adapt,
    )


def _rewrite_manifest(path: Path, transform: object) -> None:
    manifest_path = path.parent / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert callable(transform)
    transform(manifest)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _bind_train_payload(path: Path, payload: bytes, *, rows: int) -> None:
    path.write_bytes(payload)

    def update(manifest: dict[str, object]) -> None:
        splits = manifest["splits"]
        replay = manifest["replay"]
        assert isinstance(splits, dict) and isinstance(replay, dict)
        train = splits["train"]
        assert isinstance(train, dict)
        train["rows"] = rows
        train["sha256"] = hashlib.sha256(payload).hexdigest()
        replay["positive_rows"] = rows

    _rewrite_manifest(path, update)


def _load(path: Path, *, seed: str = "curriculum-test") -> LoadedCurriculum:
    return load_curriculum(
        path,
        seed=seed,
        synthetic_row_ceiling=1,
        contract=TEST_CONTRACT,
    )


def test_loader_returns_exact_examples_and_source_bound_immutable_attestation(
    dataset: Path,
) -> None:
    train_before = hashlib.sha256(dataset.read_bytes()).hexdigest()
    manifest_path = dataset.parent / "manifest.json"
    manifest_before = hashlib.sha256(manifest_path.read_bytes()).hexdigest()

    loaded = _load(dataset)
    record = loaded.attestation

    assert len(loaded.examples) == 3
    assert record["format"] == CURRICULUM_FORMAT
    assert record["source"]["train"]["sha256"] == train_before
    assert record["source"]["manifest"]["sha256"] == manifest_before
    assert record["selection"]["source"]["rows"] == 3
    assert record["selection"]["selected"]["rows"] == 3
    assert curriculum_record_sha256(record) == loaded.sha256
    assert canonical_curriculum_json(record) == loaded.attestation_json
    assert hashlib.sha256(dataset.read_bytes()).hexdigest() == train_before
    assert hashlib.sha256(manifest_path.read_bytes()).hexdigest() == manifest_before

    detached = loaded.attestation
    detached["selected"]["rows"] = 0
    assert loaded.attestation["selected"]["rows"] == 3
    with pytest.raises(CurriculumLoadError, match="selected examples"):
        LoadedCurriculum(
            examples=loaded.examples[:-1],
            attestation_json=loaded.attestation_json,
        )
    forged = replace(loaded.examples[0], completion="symm</tactic>")
    with pytest.raises(CurriculumLoadError, match="selected examples"):
        LoadedCurriculum(
            examples=(forged, *loaded.examples[1:]),
            attestation_json=loaded.attestation_json,
        )


def test_outer_digest_prevents_one_selection_from_floating_between_manifests(
    dataset: Path,
    tmp_path: Path,
) -> None:
    first = _load(dataset)
    second_root = tmp_path / "second"
    second_root.mkdir()
    second_path = second_root / "train.jsonl"
    second_path.write_bytes(dataset.read_bytes())
    manifest = json.loads(
        (dataset.parent / "manifest.json").read_text(encoding="utf-8")
    )
    manifest["split"]["audit_note"] = "same rows, distinct source manifest"
    (second_root / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    second = _load(second_path)

    assert first.selection_sha256 == second.selection_sha256
    assert first.sha256 != second.sha256
    assert (
        first.attestation["source"]["manifest"]["sha256"]
        != second.attestation["source"]["manifest"]["sha256"]
    )


@pytest.mark.parametrize("mutation", ["whitespace", "duplicate-key"])
def test_loader_rejects_noncanonical_or_duplicate_row_json(
    dataset: Path,
    mutation: str,
) -> None:
    payload = dataset.read_bytes()
    if mutation == "whitespace":
        payload = payload.replace(b'{"v":1,', b'{ "v":1,', 1)
        message = "not canonical builder JSON"
    else:
        payload = payload.replace(b'{"v":1,', b'{"v":1,"v":1,', 1)
        message = "duplicate JSON key"
    _bind_train_payload(dataset, payload, rows=3)

    with pytest.raises(PromptError, match=message):
        _load(dataset)


def test_loader_rejects_duplicate_examples_even_when_manifest_counts_match(
    dataset: Path,
) -> None:
    payload = dataset.read_bytes()
    first_line = payload.splitlines(keepends=True)[0]
    payload += first_line
    _bind_train_payload(dataset, payload, rows=4)

    with pytest.raises(PromptError, match="duplicate example id"):
        _load(dataset)


def test_loader_rejects_noncanonical_manifest_before_selection(dataset: Path) -> None:
    manifest_path = dataset.parent / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False),
        encoding="utf-8",
    )

    with pytest.raises(PromptError, match="manifest is not canonical builder JSON"):
        _load(dataset)


def test_loader_delegates_manifest_environment_and_count_checks(dataset: Path) -> None:
    def forge(manifest: dict[str, object]) -> None:
        environments = manifest["environments"]
        assert isinstance(environments, list)
        environments[0]["environment_sha256"] = "0" * 64

    _rewrite_manifest(dataset, forge)

    with pytest.raises(PromptError, match="capability hash mismatch"):
        _load(dataset)
