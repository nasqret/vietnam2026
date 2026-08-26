"""Deterministic, checked artifact contract for the M19 pilot generator."""

from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_ROOT = REPOSITORY_ROOT / "scripts"
GENERATOR_SOURCE = SCRIPTS_ROOT / "generate_peano_policy_corpus.py"
for import_root in (
    REPOSITORY_ROOT,
    SCRIPTS_ROOT,
    REPOSITORY_ROOT / "peano-lab" / "py",
):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from export_traces import load_trace_file  # noqa: E402
from peano_lab.batch import MODEL_V1_THEOREMS, run_proof  # noqa: E402
from peano_lab.library.theorems import get as get_theorem  # noqa: E402
from training.peano_policy.attest import (  # noqa: E402
    DatasetAttestationError,
    attest_dataset,
)


def _load_script(name: str, path: Path):
    specification = importlib.util.spec_from_file_location(name, path)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


generator = _load_script("_test_generate_peano_policy_corpus", GENERATOR_SOURCE)
builder = _load_script(
    "_test_policy_dataset_builder_for_generator",
    SCRIPTS_ROOT / "build_peano_policy_dataset.py",
)


def _paths(root: Path) -> tuple[Path, Path, Path]:
    return root / "raw.jsonl", root / "metadata.jsonl", root / "manifest.json"


def _jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_full_pilot_is_contiguous_checked_diverse_and_builder_compatible(
    tmp_path: Path,
) -> None:
    trace, metadata, manifest_path = _paths(tmp_path / "pilot")

    generated = generator.generate_corpus(trace, metadata, manifest_path)

    sessions = load_trace_file(trace)
    records = builder.load_metadata(metadata)
    manifest = generated.manifest
    assert len(sessions) == len(generator.PILOT_TEMPLATES) == 18
    assert len(records) == len(sessions)
    assert all(session.footer["qed"] is True for session in sessions)
    assert all(session.footer["proof_size"] > 0 for session in sessions)
    assert {session.session_id for session in sessions} == set(records)
    assert manifest["format"] == "peano-policy-corpus"
    assert manifest["version"] == manifest["trace_version"] == 1
    assert manifest["counts"]["kernel_checked_qed"] == len(sessions)
    assert manifest["counts"]["transition_records"] == sum(
        len(session.steps) for session in sessions
    )

    required_heads = {
        "apply",
        "cases",
        "compact_arith",
        "congr",
        "exact",
        "exists",
        "have",
        "induction",
        "intro",
        "left",
        "norm_num",
        "rewrite",
        "right",
        "ring",
        "simp",
        "split",
        "suffices",
        "symm",
        "trans",
        "use",
    }
    assert required_heads <= set(manifest["counts"]["tactic_heads"])
    required_tags = {
        "logic",
        "equality",
        "induction",
        "addition",
        "multiplication",
        "existential",
        "cases",
        "theorem-use",
        "have",
        "suffices",
        "norm_num",
        "ring",
        "compact_arith",
    }
    assert required_tags <= set(manifest["counts"]["tags"])

    sidecar = _jsonl(metadata)
    assert len({record["statement"] for record in sidecar}) == len(sidecar)
    assert len({record["lineage"] for record in sidecar}) == len(sidecar)
    assert all(record["classical"] is False for record in sidecar)
    assert all(record["surface"] == "model-v1" for record in sidecar)
    assert all(
        record["environment_sha256"]
        == manifest["environment"]["environment_sha256"]
        for record in sidecar
    )
    assert all(
        record["capabilities"] == manifest["environment"]["capabilities"]
        for record in sidecar
    )
    assert manifest["environment"]["capabilities"]["allowed_theorems"] == sorted(
        MODEL_V1_THEOREMS
    )

    # The downstream compiler independently replays every positive transition
    # sequence and checks the final certificate against the original theorem.
    dataset = builder.build_dataset(
        [trace],
        metadata,
        tmp_path / "dataset",
        seed="generator-integration",
        val_fraction=0.1,
        test_fraction=0.1,
    )
    assert dataset.manifest["replay"]["accepted_kernel_checked_sessions"] == len(
        sessions
    )
    assert dataset.manifest["replay"]["positive_rows"] == sum(
        len(session.steps) for session in sessions
    )
    attestation = attest_dataset(dataset.train_path, dataset.val_path)
    assert attestation["independent_replay"] is True
    assert attestation["held_out_contamination"] == 0
    assert attestation["dataset_sha256"] == dataset.manifest["dataset_sha256"]


def test_training_attestor_rejects_a_genuinely_checked_held_out_target(
    tmp_path: Path,
) -> None:
    specification = get_theorem("le_trans")
    assert specification is not None
    trace_sink = io.StringIO()
    result = run_proof(
        specification.statement,
        ("use add_assoc", *specification.script),
        request_id="contaminated-le-trans",
        capabilities=generator.POLICY_CAPABILITIES,
        trace_sink=trace_sink,
    )
    assert result.status == "proved" and result.kernel_checked is True
    raw = tmp_path / "raw.jsonl"
    raw.write_text(trace_sink.getvalue(), encoding="utf-8")
    capabilities = {
        "label": generator.POLICY_CAPABILITIES.label,
        "allowed_commands": sorted(generator.POLICY_CAPABILITIES.allowed_commands),
        "allowed_theorems": sorted(generator.POLICY_CAPABILITIES.allowed_theorems),
    }
    metadata = tmp_path / "metadata.jsonl"
    metadata.write_text(
        json.dumps(
            {
                "session": result.session_id,
                "theorem": "le_trans",
                "family": "forged-clean-family",
                "lineage": "forged-clean-lineage",
                "classical": False,
                "surface": "model-v1",
                "environment_sha256": result.environment_sha256,
                "capabilities": capabilities,
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )
    dataset = builder.build_dataset(
        [raw],
        metadata,
        tmp_path / "dataset",
        val_fraction=0.0,
        test_fraction=0.0,
    )

    with pytest.raises(DatasetAttestationError, match="held-out target"):
        attest_dataset(dataset.train_path, dataset.val_path)


def test_training_attestor_rejects_cross_split_policy_prompt_leakage(
    tmp_path: Path,
) -> None:
    trace, metadata, manifest_path = _paths(tmp_path / "pilot")
    generator.generate_corpus(trace, metadata, manifest_path)
    dataset = builder.build_dataset(
        [trace],
        metadata,
        tmp_path / "dataset",
        seed="prompt-leak-attestation",
        val_fraction=0.34,
        test_fraction=0.34,
    )
    split_paths = {
        "train": dataset.train_path,
        "val": dataset.val_path,
        "test": dataset.test_path,
    }
    rows = {split: _jsonl(path) for split, path in split_paths.items()}
    assert all(rows.values())

    # Forge a byte- and manifest-consistent artifact whose first row in every
    # split presents the exact same model input.  The original theorem fields
    # remain pairwise distinct, so a formula-only contamination gate would
    # miss this state-level policy leak.
    selected = {split: records[0] for split, records in rows.items()}
    assert len({record["formula"] for record in selected.values()}) == 3
    source = selected["train"]
    for split in ("val", "test"):
        selected[split]["state"] = list(source["state"])
        selected[split]["focus"] = source["focus"]
        selected[split]["prompt"] = source["prompt"]
    assert len({record["prompt"] for record in selected.values()}) == 1

    payloads: dict[str, bytes] = {}
    for split, path in split_paths.items():
        payload = "".join(
            json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"
            for record in rows[split]
        ).encode("utf-8")
        path.write_bytes(payload)
        payloads[split] = payload

    manifest = json.loads(dataset.manifest_path.read_text(encoding="utf-8"))
    aggregate = hashlib.sha256()
    for split in ("train", "val", "test"):
        manifest["splits"][split]["rows"] = len(rows[split])
        manifest["splits"][split]["sha256"] = hashlib.sha256(
            payloads[split]
        ).hexdigest()
        aggregate.update(split.encode("ascii") + b"\0")
        aggregate.update(payloads[split])
    manifest["dataset_sha256"] = aggregate.hexdigest()
    dataset.manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(DatasetAttestationError, match="policy prompts overlap"):
        attest_dataset(dataset.train_path, dataset.val_path)


def test_seeded_count_and_fixed_smoke_are_byte_deterministic(tmp_path: Path) -> None:
    first_paths = _paths(tmp_path / "first")
    second_paths = _paths(tmp_path / "second")

    first = generator.generate_corpus(*first_paths, seed="same", count=5)
    second = generator.generate_corpus(*second_paths, seed="same", count=5)

    assert [path.read_bytes() for path in first_paths] == [
        path.read_bytes() for path in second_paths
    ]
    assert first.manifest["counts"]["sessions"] == 5
    assert first.manifest["config"] == {
        "seed": "same",
        "count": 5,
        "smoke": False,
        "selection": "sha256-ranked-lineage-v1",
    }

    smoke_paths = _paths(tmp_path / "smoke")
    smoke = generator.generate_corpus(*smoke_paths, seed="same", smoke=True)
    assert smoke.manifest["counts"]["sessions"] == len(generator.SMOKE_THEOREMS)
    assert [entry["theorem"] for entry in smoke.manifest["sessions"]] == list(
        generator.SMOKE_THEOREMS
    )
    assert smoke.manifest["config"]["selection"] == "fixed-smoke-v1"


def test_manifest_binds_artifact_and_semantic_source_hashes(tmp_path: Path) -> None:
    trace, metadata, manifest_path = _paths(tmp_path)
    result = generator.generate_corpus(trace, metadata, manifest_path, count=2)
    manifest = result.manifest

    assert manifest["artifacts"]["trace"] == {
        "path": trace.name,
        "bytes": len(trace.read_bytes()),
        "sha256": _sha256(trace),
    }
    assert manifest["artifacts"]["metadata"] == {
        "path": metadata.name,
        "bytes": len(metadata.read_bytes()),
        "sha256": _sha256(metadata),
    }
    source_paths = {
        "scripts/generate_peano_policy_corpus.py",
        "scripts/export_traces.py",
    } | {
        path.relative_to(REPOSITORY_ROOT).as_posix()
        for path in (REPOSITORY_ROOT / "peano-lab" / "py" / "peano_lab").rglob(
            "*.py"
        )
    }
    assert set(manifest["sources"]) == source_paths
    assert manifest["runtime"] == {
        "implementation": sys.implementation.name,
        "python": ".".join(str(part) for part in sys.version_info[:3]),
    }
    for relative, record in manifest["sources"].items():
        assert record["sha256"] == _sha256(REPOSITORY_ROOT / relative)

    changed_sources = json.loads(json.dumps(manifest["sources"]))
    changed_sources["peano-lab/py/peano_lab/engine/tactics.py"]["sha256"] = "0" * 64
    selected = generator.select_templates(count=2)
    assert generator._generation_fingerprint(
        selected,
        seed=generator.DEFAULT_SEED,
        smoke=False,
        sources=changed_sources,
    ) != manifest["run_fingerprint"]


@pytest.mark.parametrize("duplicate", ["statement", "lineage"])
def test_duplicate_statements_and_lineages_are_rejected_before_publication(
    tmp_path: Path,
    duplicate: str,
) -> None:
    first, second = generator.PILOT_TEMPLATES[:2]
    if duplicate == "statement":
        second = replace(second, statement=first.statement)
    else:
        second = replace(second, lineage=first.lineage)
    paths = _paths(tmp_path)

    with pytest.raises(generator.GenerationError, match=f"duplicate {duplicate}"):
        generator.generate_corpus(*paths, templates=(first, second))

    assert not any(path.exists() for path in paths)


def test_non_qed_or_unchecked_batch_result_aborts_without_artifacts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    real_run_proof = generator.run_proof

    def untrusted_result(*args, **kwargs):
        return replace(real_run_proof(*args, **kwargs), kernel_checked=False)

    monkeypatch.setattr(generator, "run_proof", untrusted_result)
    paths = _paths(tmp_path)

    with pytest.raises(generator.GenerationError, match="checked QED"):
        generator.generate_corpus(*paths, count=1)

    assert not any(path.exists() for path in paths)


def test_cli_smoke_publishes_a_small_replayable_corpus(tmp_path: Path) -> None:
    trace, metadata, manifest = _paths(tmp_path)
    completed = subprocess.run(
        (
            sys.executable,
            str(GENERATOR_SOURCE),
            "--trace-output",
            str(trace),
            "--metadata-output",
            str(metadata),
            "--manifest",
            str(manifest),
            "--seed",
            "cli-smoke",
            "--smoke",
        ),
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert "generated 4 checked sessions" in completed.stdout
    assert len(load_trace_file(trace)) == 4
    assert len(builder.load_metadata(metadata)) == 4


def test_count_validation_and_smoke_conflict_are_explicit(tmp_path: Path) -> None:
    paths = _paths(tmp_path)
    with pytest.raises(ValueError, match="between 1"):
        generator.generate_corpus(*paths, count=0)
    with pytest.raises(ValueError, match="mutually exclusive"):
        generator.generate_corpus(*paths, count=1, smoke=True)
    assert not any(path.exists() for path in paths)


def test_v1_rejects_classical_template_before_publication(tmp_path: Path) -> None:
    classical = replace(generator.PILOT_TEMPLATES[0], classical=True)
    paths = _paths(tmp_path)

    with pytest.raises(generator.GenerationError, match="fixed intuitionistic"):
        generator.generate_corpus(*paths, templates=(classical,))
    assert not any(path.exists() for path in paths)


def test_publication_failure_restores_previous_coherent_corpus(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = _paths(tmp_path)
    old = (b"old trace\n", b"old metadata\n", b"old manifest\n")
    for path, payload in zip(paths, old, strict=True):
        path.write_bytes(payload)

    real_replace = generator.os.replace
    calls = 0

    def fail_second_install(source, destination):
        nonlocal calls
        calls += 1
        if calls == 5:  # three backups, first install, then fail
            raise OSError("injected corpus publish failure")
        return real_replace(source, destination)

    monkeypatch.setattr(generator.os, "replace", fail_second_install)
    with pytest.raises(OSError, match="injected corpus"):
        generator.generate_corpus(*paths, count=1)
    assert tuple(path.read_bytes() for path in paths) == old
