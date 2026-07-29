"""Checked predecessor-prefix contract for the model-v3 library corpus."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_ROOT = REPOSITORY_ROOT / "scripts"
GENERATOR_SOURCE = SCRIPTS_ROOT / "generate_peano_library_policy_corpus.py"
for import_root in (REPOSITORY_ROOT, SCRIPTS_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from export_traces import load_trace_file  # noqa: E402
from peano_lab.batch import MAX_REVIEWED_BATCH_TRACE_BYTES  # noqa: E402
from peano_lab.engine.trace import TraceLimitError  # noqa: E402
from peano_lab.library.theorems import THEOREMS  # noqa: E402
from training.peano_policy.contract import (  # noqa: E402
    MODEL_V3_LIBRARY_SIZE,
    model_v3_prefix_environment,
)


def _load_script(name: str, path: Path):
    specification = importlib.util.spec_from_file_location(name, path)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


generator = _load_script(
    "_test_generate_peano_library_policy_corpus", GENERATOR_SOURCE
)
builder = _load_script(
    "_test_build_dataset_for_library_corpus",
    SCRIPTS_ROOT / "build_peano_policy_dataset.py",
)


def _jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _artifact_paths(root: Path) -> tuple[Path, Path, Path]:
    return root / "raw.jsonl", root / "metadata.jsonl", root / "manifest.json"


def test_three_rungs_are_exact_checked_prefixes_and_builder_compatible(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    trace, metadata, manifest_path = _artifact_paths(tmp_path / "library")
    generated = generator.generate_corpus(trace, metadata, manifest_path, limit=3)

    sessions = load_trace_file(trace)
    records = _jsonl(metadata)
    assert len(sessions) == len(records) == 3
    assert generator.select_theorems() == THEOREMS
    assert MODEL_V3_LIBRARY_SIZE == len(THEOREMS) == 247
    assert generated.manifest["counts"] == {
        "sessions": 3,
        "kernel_checked_qed": 3,
        "transition_records": sum(
            len(spec.dependencies) + len(spec.script) for spec in THEOREMS[:3]
        ),
        "footer_records": 3,
        "proof_nodes": sum(session.footer["proof_size"] for session in sessions),
        "dependency_imports": 2,
        "authored_tactics": 11,
        "tactic_heads": generated.manifest["counts"]["tactic_heads"],
    }
    assert generated.manifest["artifacts"]["trace"]["sha256"] == hashlib.sha256(
        trace.read_bytes()
    ).hexdigest()
    assert generated.manifest["artifacts"]["metadata"][
        "sha256"
    ] == hashlib.sha256(metadata.read_bytes()).hexdigest()

    for index, (spec, session, record) in enumerate(
        zip(THEOREMS[:3], sessions, records, strict=True)
    ):
        environment = model_v3_prefix_environment(index)
        commands = tuple(f"use {name}" for name in spec.dependencies) + spec.script
        assert session.footer["qed"] is True
        assert tuple(step["tactic"] for step in session.steps) == commands
        assert record["tactics"] == list(commands)
        assert record["trajectory"] == "catalog-predecessor-prefix-v1"
        assert record["library_target_index"] == index
        assert record["library_target_name"] == record["theorem"] == spec.name
        assert record["library_prefix_length"] == index
        assert record["library_size"] == len(THEOREMS)
        assert record["environment_sha256"] == environment.sha256
        assert record["library_identity_sha256"] == environment.library_sha256
        assert record["library_full_identity_sha256"] == (
            environment.library_full_identity_sha256
        )
        assert spec.name not in record["capabilities"]["allowed_theorems"]
        assert set(record["capabilities"]["allowed_theorems"]) == {
            prior.name for prior in THEOREMS[:index]
        }

    replay_limits: list[object] = []
    real_run_proof = builder.run_proof

    def observed_replay(*args: object, **kwargs: object):
        replay_limits.append(kwargs.get("trace_byte_limit"))
        return real_run_proof(*args, **kwargs)

    monkeypatch.setattr(builder, "run_proof", observed_replay)
    dataset = builder.build_dataset(
        [trace],
        metadata,
        tmp_path / "dataset",
        seed="library-corpus-test",
        val_fraction=0.0,
        test_fraction=0.0,
    )
    assert dataset.manifest["replay"] == {
        "attempted_qed_sessions": 3,
        "accepted_kernel_checked_sessions": 3,
        "positive_rows": generated.manifest["counts"]["transition_records"],
        "transactional_error_steps_ignored": 0,
    }
    rows = _jsonl(dataset.train_path)
    assert len(rows) == generated.manifest["counts"]["transition_records"]
    assert replay_limits == [MAX_REVIEWED_BATCH_TRACE_BYTES] * 3
    assert all(
        row["metadata"]["trajectory"] == "catalog-predecessor-prefix-v1"
        for row in rows
    )
    assert dataset.manifest["split"]["method"] == builder.V3_SPLIT_METHOD
    catalog_rows = generated.manifest["counts"]["transition_records"]
    assert dataset.manifest["splits"]["train"]["lane_populations"] == {
        builder.V3_CATALOG_TRAJECTORY: {"sessions": 3, "rows": catalog_rows},
        builder.V3_SYNTHETIC_LANE: {"sessions": 0, "rows": 0},
    }
    for split in ("val", "test"):
        assert dataset.manifest["splits"][split]["lane_populations"] == {
            lane: {"sessions": 0, "rows": 0}
            for lane in builder.V3_SPLIT_LANES
        }


def test_generation_failure_preserves_existing_artifact_set(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    trace, metadata, manifest = _artifact_paths(tmp_path / "transaction")
    trace.parent.mkdir(parents=True)
    originals = ("old trace\n", "old metadata\n", "old manifest\n")
    for path, content in zip((trace, metadata, manifest), originals, strict=True):
        path.write_text(content, encoding="utf-8")

    def fail_run(*args: object, **kwargs: object) -> object:
        raise generator.GenerationError("injected checked-run failure")

    monkeypatch.setattr(generator, "run_proof", fail_run)
    with pytest.raises(generator.GenerationError, match="injected"):
        generator.generate_corpus(trace, metadata, manifest, limit=1)
    assert tuple(
        path.read_text(encoding="utf-8") for path in (trace, metadata, manifest)
    ) == originals


def test_trace_limit_names_the_failed_theorem_without_exposing_engine_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    trace, metadata, manifest = _artifact_paths(tmp_path / "trace-limit")
    observed: dict[str, object] = {}

    def fail_run(*args: object, **kwargs: object) -> object:
        observed.update(kwargs)
        raise TraceLimitError("trace exceeded its internal byte session limit")

    monkeypatch.setattr(
        generator,
        "_surface_capabilities",
        lambda index: (
            SimpleNamespace(allowed_theorems=frozenset()),
            SimpleNamespace(sha256="0" * 64),
        ),
    )
    monkeypatch.setattr(generator, "run_proof", fail_run)
    with pytest.raises(
        generator.GenerationError,
        match=r"^library theorem 'zero_add' exceeded the headless per-session trace limit$",
    ) as raised:
        generator.generate_corpus(trace, metadata, manifest, limit=1)
    assert raised.value.__suppress_context__ is True
    assert observed["trace_byte_limit"] == 128 * 1024 * 1024
    assert not trace.exists()
    assert not metadata.exists()
    assert not manifest.exists()


def test_checked_catalog_replay_names_trace_exhaustion(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    trace, metadata, manifest = _artifact_paths(tmp_path / "replay-limit")
    generator.generate_corpus(trace, metadata, manifest, limit=1)
    observed: dict[str, object] = {}

    def fail_replay(*args: object, **kwargs: object) -> object:
        observed.update(kwargs)
        raise TraceLimitError("injected replay byte limit")

    monkeypatch.setattr(builder, "run_proof", fail_replay)
    with pytest.raises(
        builder.DatasetBuildError,
        match=(
            r"^session 'peano-library-v3-000-[0-9a-f]+' theorem "
            r"'zero_add' exceeded its checked replay trace limit$"
        ),
    ) as raised:
        builder.build_dataset(
            [trace],
            metadata,
            tmp_path / "dataset",
            val_fraction=0.0,
            test_fraction=0.0,
        )
    assert raised.value.__suppress_context__ is True
    assert observed["trace_byte_limit"] == MAX_REVIEWED_BATCH_TRACE_BYTES
    assert not (tmp_path / "dataset").exists()


def test_builder_rejects_omitted_or_forged_predecessor_marker(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    trace, metadata, manifest = _artifact_paths(tmp_path / "marker-source")
    generator.generate_corpus(trace, metadata, manifest, limit=1)
    original = _jsonl(metadata)[0]
    replay_attempts = 0

    def forbidden_replay(*args: object, **kwargs: object) -> object:
        nonlocal replay_attempts
        replay_attempts += 1
        raise AssertionError("forged catalog metadata reached checked replay")

    monkeypatch.setattr(builder, "run_proof", forbidden_replay)

    for label, claimed in (("omitted", None), ("forged", "another-lane")):
        mutated = json.loads(json.dumps(original))
        if claimed is None:
            mutated.pop("trajectory")
        else:
            mutated["trajectory"] = claimed
        sidecar = tmp_path / f"{label}.jsonl"
        sidecar.write_text(
            json.dumps(mutated, ensure_ascii=False, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        with pytest.raises(
            builder.DatasetBuildError,
            match="must use the exact.*catalog-predecessor-prefix-v1",
        ):
            builder.build_dataset(
                [trace],
                sidecar,
                tmp_path / f"dataset-{label}",
                val_fraction=0.0,
                test_fraction=0.0,
            )
    assert replay_attempts == 0


@pytest.mark.parametrize("limit", [0, -1, 248, True])
def test_limit_must_be_a_positive_catalog_prefix(limit: object) -> None:
    with pytest.raises(ValueError, match="limit must be between"):
        generator.select_theorems(limit)  # type: ignore[arg-type]
