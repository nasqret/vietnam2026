"""Focused contracts for scalable proof-first synthetic policy data."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from peano_lab.batch import MODEL_V1_COMMANDS, verify_proof


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_ROOT = REPOSITORY_ROOT / "scripts"
GENERATOR_SOURCE = SCRIPTS_ROOT / "generate_peano_synthetic_corpus.py"
for import_root in (SCRIPTS_ROOT, REPOSITORY_ROOT / "peano-lab" / "py"):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from export_traces import load_trace_file  # noqa: E402


def _load_script(name: str, path: Path):
    specification = importlib.util.spec_from_file_location(name, path)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


generator = _load_script("_test_generate_peano_synthetic_corpus", GENERATOR_SOURCE)
builder = _load_script(
    "_test_build_for_synthetic_corpus",
    SCRIPTS_ROOT / "build_peano_policy_dataset.py",
)


def _paths(root: Path) -> tuple[Path, Path, Path]:
    return root / "raw.jsonl", root / "metadata.jsonl", root / "manifest.json"


def _jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_catalog_is_diverse_model_v1_surface_data_not_a_second_prover() -> None:
    assert {schema.domain for schema in generator.SCHEMAS} == set(generator.DOMAINS)
    assert len(generator.SCHEMAS) == len({schema.name for schema in generator.SCHEMAS})
    assert len(generator.SCHEMAS) >= 25

    source = GENERATOR_SOURCE.read_text(encoding="utf-8")
    assert "run_proof(" in source
    assert "ProofSession" not in source
    assert "apply_tactic" not in source
    assert "checked_final" not in source
    assert "engine.search" not in source
    assert "StringIO" not in source

    for ordinal, schema in enumerate(generator.SCHEMAS, 1):
        candidate = schema.build(ordinal)
        assert candidate.tactics
        assert all(
            tactic.split(maxsplit=1)[0] in MODEL_V1_COMMANDS
            for tactic in candidate.tactics
        )
        result = verify_proof(
            candidate.statement,
            candidate.tactics,
            request_id=f"schema-{ordinal}",
            capabilities=generator.POLICY_CAPABILITIES,
        )
        assert result.status == "proved", (schema.name, result.error)
        assert result.kernel_checked is True
        assert result.proof_nodes and result.proof_nodes > 0


def test_streams_exact_budget_with_checked_roots_and_builder_replay(
    tmp_path: Path,
) -> None:
    trace, metadata_path, manifest_path = _paths(tmp_path / "synthetic")
    generated = generator.generate_corpus(
        trace,
        metadata_path,
        manifest_path,
        seed="smoke",
        row_budget=30,
    )

    sessions = load_trace_file(trace)
    metadata = _jsonl(metadata_path)
    manifest = generated.manifest
    assert sum(len(session.steps) for session in sessions) == 30
    assert all(session.footer["qed"] is True for session in sessions)
    assert all(step["status"] == "ok" for session in sessions for step in session.steps)
    assert len(metadata) == len(sessions) == manifest["counts"]["sessions"]
    assert manifest["counts"]["transition_records"] == 30
    assert manifest["counts"]["positive_tactic_rows"] == 30
    assert manifest["counts"]["kernel_checked_qed"] == len(sessions)
    assert manifest["counts"]["independent_roots"] == len(sessions)
    assert set(manifest["counts"]["sessions_by_domain"]) == set(generator.DOMAINS)

    roots = {record["root"] for record in metadata}
    assert len(roots) == len(metadata)
    assert all(
        record["family"] == record["lineage"] == record["root"]
        for record in metadata
    )
    assert all(record["parents"] == [] for record in metadata)
    assert all(record["classical"] is False for record in metadata)
    assert all(record["surface"] == "model-v1" for record in metadata)
    assert all(record["statement"] for record in metadata)
    assert len({record["statement"] for record in metadata}) == len(metadata)

    assert manifest["artifacts"]["trace"] == {
        "path": trace.name,
        "bytes": len(trace.read_bytes()),
        "sha256": _sha256(trace),
    }
    assert manifest["artifacts"]["metadata"] == {
        "path": metadata_path.name,
        "bytes": len(metadata_path.read_bytes()),
        "sha256": _sha256(metadata_path),
    }
    assert manifest["sources"][
        "scripts/generate_peano_synthetic_corpus.py"
    ]["sha256"] == _sha256(GENERATOR_SOURCE)
    assert not list(trace.parent.glob("*.tmp"))
    assert not list(trace.parent.glob(".*.tmp"))

    # The downstream compiler independently replays every successful tactic
    # sequence and performs the final kernel check again.
    dataset = builder.build_dataset(
        [trace],
        metadata_path,
        tmp_path / "dataset",
        seed="synthetic-builder-smoke",
        val_fraction=0.1,
        test_fraction=0.1,
    )
    assert dataset.manifest["replay"] == {
        "attempted_qed_sessions": len(sessions),
        "accepted_kernel_checked_sessions": len(sessions),
        "positive_rows": 30,
        "transactional_error_steps_ignored": 0,
    }


def test_byte_determinism_and_row_budget_are_bound_to_run_identity(
    tmp_path: Path,
) -> None:
    first = _paths(tmp_path / "first")
    second = _paths(tmp_path / "second")
    left = generator.generate_corpus(*first, seed="same", row_budget=1)
    right = generator.generate_corpus(*second, seed="same", row_budget=1)

    assert first[0].read_bytes() == second[0].read_bytes()
    assert first[1].read_bytes() == second[1].read_bytes()
    assert first[2].read_bytes() == second[2].read_bytes()
    assert left.manifest["run_fingerprint"] == right.manifest["run_fingerprint"]
    assert left.manifest["counts"]["positive_tactic_rows"] == 1

    third = _paths(tmp_path / "third")
    changed = generator.generate_corpus(*third, seed="same", row_budget=2)
    assert changed.manifest["run_fingerprint"] != left.manifest["run_fingerprint"]
    assert changed.manifest["counts"]["positive_tactic_rows"] == 2


def test_unchecked_result_discards_staging_and_preserves_old_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = _paths(tmp_path)
    old = (b"old trace\n", b"old metadata\n", b"old manifest\n")
    for path, payload in zip(paths, old, strict=True):
        path.write_bytes(payload)

    real_run_proof = generator.run_proof

    def unchecked(*args, **kwargs):
        return replace(real_run_proof(*args, **kwargs), kernel_checked=False)

    monkeypatch.setattr(generator, "run_proof", unchecked)
    with pytest.raises(generator.GenerationError, match="failed checked QED"):
        generator.generate_corpus(*paths, seed="unchecked", row_budget=1)

    assert tuple(path.read_bytes() for path in paths) == old
    assert not list(tmp_path.glob(".*.tmp"))


def test_invalid_budget_and_aliased_outputs_fail_before_generation(
    tmp_path: Path,
) -> None:
    paths = _paths(tmp_path)
    with pytest.raises(ValueError, match="between 1"):
        generator.generate_corpus(*paths, row_budget=0)
    with pytest.raises(generator.GenerationError, match="must be distinct"):
        generator.generate_corpus(paths[0], paths[0], paths[2], row_budget=1)
    assert not any(path.exists() for path in paths)
