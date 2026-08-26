"""Focused trust-boundary tests for sealed model-v3 corpus reuse."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass
import hashlib
import json
from pathlib import Path
import sys
from typing import Callable

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from training.peano_policy import (  # noqa: E402
    attest,
    contract,
    corpus_eligibility,
    corpus_seal,
    library_identity_v3,
)
from training.peano_policy.contract import (  # noqa: E402
    held_out_contract_record,
    held_out_contract_sha256,
)
from training.peano_policy.manifest import sha256_file, sha256_json  # noqa: E402
from training.peano_policy.prompt import (  # noqa: E402
    PEANO_PROMPT_V3,
    prompt_contract_sha256,
    prompt_manifest_record,
)
from peano_lab.library import theorems as theorem_library  # noqa: E402


COMMIT = "a" * 40
JOB_ID = "172729"
LIBRARY_PREFIX_SHA256 = "1" * 64
LIBRARY_FULL_SHA256 = "2" * 64


def _canonical(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_canonical(value) + "\n", encoding="utf-8")


def _file_record(root: Path, relative: str) -> dict[str, object]:
    path = root / relative
    return {
        "path": relative,
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def _current_compiler_record() -> dict[str, object]:
    sources = {
        path.relative_to(attest.REPOSITORY_ROOT).as_posix(): {
            "sha256": sha256_file(path)
        }
        for path in attest._compiler_paths()
    }
    return {
        "runtime": {"implementation": "CPython", "python": "3.12.12"},
        "sources": sources,
    }


@dataclass
class _Fixture:
    root: Path
    dataset_manifest: dict[str, object]
    historical_attestation: dict[str, object]
    seal_manifest: dict[str, object]

    @property
    def train(self) -> Path:
        return self.root / "data" / "train.jsonl"

    @property
    def evaluation(self) -> Path:
        return self.root / "data" / "val.jsonl"

    def refresh_bindings(self) -> None:
        """Rebind the fake verified seal after an intentional semantic edit."""

        _write_json(self.root / "data" / "manifest.json", self.dataset_manifest)
        manifest_sha256 = sha256_file(self.root / "data" / "manifest.json")
        dataset = self.seal_manifest["dataset"]
        assert isinstance(dataset, dict)
        dataset["manifest_sha256"] = manifest_sha256
        self.historical_attestation["manifest_sha256"] = manifest_sha256
        _write_json(
            self.root / "reports" / "dataset-attestation.json",
            self.historical_attestation,
        )

        files = [
            _file_record(self.root, relative)
            for relative in (
                "data/manifest.json",
                "data/train.jsonl",
                "data/val.jsonl",
                "reports/dataset-attestation.json",
            )
        ]
        files.sort(key=lambda record: str(record["path"]))
        reports = self.seal_manifest["reports"]
        assert isinstance(reports, dict)
        report_identity = reports["dataset_attestation"]
        assert isinstance(report_identity, dict)
        report_identity["sha256"] = next(
            record["sha256"]
            for record in files
            if record["path"] == "reports/dataset-attestation.json"
        )
        report_identity["manifest_sha256"] = manifest_sha256
        self.seal_manifest["files"] = files
        self.seal_manifest["files_sha256"] = sha256_json(files)
        identity = {
            key: self.seal_manifest[key]
            for key in ("source", "dataset", "model", "reports", "files")
        }
        self.seal_manifest["content_sha256"] = sha256_json(identity)


def _fixture(tmp_path: Path) -> _Fixture:
    root = tmp_path / "sealed"
    (root / "data").mkdir(parents=True)
    (root / "reports").mkdir()
    (root / "data" / "train.jsonl").write_text('{"split":"train"}\n')
    (root / "data" / "val.jsonl").write_text('{"split":"val"}\n')

    compiler_record = _current_compiler_record()
    dataset_manifest: dict[str, object] = {
        "source": {"compiler": compiler_record},
    }
    _write_json(root / "data" / "manifest.json", dataset_manifest)
    compiler_identity = attest._verify_compiler(dataset_manifest)

    train_sha256 = sha256_file(root / "data" / "train.jsonl")
    val_sha256 = sha256_file(root / "data" / "val.jsonl")
    dataset_sha256 = "d" * 64
    training_environments_sha256 = "e" * 64
    authority_schedule = {
        "method": "catalog-predecessor-prefix-v1+full-synthetic-v1",
        "full_library_sha256": LIBRARY_FULL_SHA256,
        "library_size": 247,
        "training_prefixes": list(range(248)),
        "inference_prefix": 247,
    }
    current_environment = corpus_eligibility._current_inference_environment(
        LIBRARY_PREFIX_SHA256,
        LIBRARY_FULL_SHA256,
    )
    historical_attestation: dict[str, object] = {
        "format": "peano-policy-dataset-attestation",
        "v": 2,
        "attestor": {
            "runtime": {"implementation": "CPython", "python": "3.12.12"},
            "sources_sha256": "f" * 64,
        },
        "compiler": compiler_identity,
        "manifest_sha256": sha256_file(root / "data" / "manifest.json"),
        "dataset_sha256": dataset_sha256,
        "prompt_version": PEANO_PROMPT_V3,
        "prompt_contract": prompt_manifest_record(PEANO_PROMPT_V3),
        "prompt_contract_sha256": prompt_contract_sha256(PEANO_PROMPT_V3),
        "held_out_contract": held_out_contract_record(PEANO_PROMPT_V3),
        "held_out_contract_sha256": held_out_contract_sha256(PEANO_PROMPT_V3),
        "library_snapshot_sha256": LIBRARY_PREFIX_SHA256,
        "inference_environment": current_environment,
        "training_environments_sha256": training_environments_sha256,
        "authority_schedule": authority_schedule,
        "independent_replay": True,
        "held_out_contamination": 0,
        "splits": {
            "train": {"rows": 2, "sha256": train_sha256},
            "val": {"rows": 1, "sha256": val_sha256},
        },
    }
    _write_json(root / "reports" / "dataset-attestation.json", historical_attestation)

    seal_manifest: dict[str, object] = {
        "format": corpus_seal.SEAL_FORMAT,
        "version": corpus_seal.SEAL_VERSION,
        "source": {
            "git_commit": COMMIT,
            "prepare_job_id": JOB_ID,
        },
        "dataset": {
            "manifest_sha256": sha256_file(root / "data" / "manifest.json"),
            "dataset_sha256": dataset_sha256,
            "prompt_version": PEANO_PROMPT_V3,
            "library_snapshot_sha256": LIBRARY_PREFIX_SHA256,
            "prompt_contract_sha256": prompt_contract_sha256(PEANO_PROMPT_V3),
            "held_out_contract_sha256": held_out_contract_sha256(
                PEANO_PROMPT_V3
            ),
            "training_environments_sha256": training_environments_sha256,
            "authority_schedule": authority_schedule,
            "splits": {
                "train": {"rows": 2, "sha256": train_sha256},
                "val": {"rows": 1, "sha256": val_sha256},
            },
        },
        "model": {
            "id": "Qwen/Qwen3-1.7B-Base",
            "revision": "ea980cb0a6c2ae4b936e82123acc929f1cec04c1",
        },
        "reports": {
            "dataset_attestation": {
                "sealed_path": "reports/dataset-attestation.json",
                "sha256": sha256_file(
                    root / "reports" / "dataset-attestation.json"
                ),
                "format": "peano-policy-dataset-attestation",
                "version": 2,
                "manifest_sha256": sha256_file(root / "data" / "manifest.json"),
                "dataset_sha256": dataset_sha256,
            }
        },
        "files": [],
        "files_sha256": "0" * 64,
        "content_sha256": "0" * 64,
    }
    fixture = _Fixture(
        root=root,
        dataset_manifest=dataset_manifest,
        historical_attestation=historical_attestation,
        seal_manifest=seal_manifest,
    )
    fixture.refresh_bindings()
    return fixture


def _install_verifier(
    monkeypatch: pytest.MonkeyPatch,
    fixture: _Fixture,
) -> list[tuple[object, object, object]]:
    calls: list[tuple[object, object, object]] = []

    def fake_verify(
        destination: object,
        *,
        source_commit: object = None,
        prepare_job_id: object = None,
    ) -> dict[str, object]:
        calls.append((destination, source_commit, prepare_job_id))
        if source_commit != COMMIT or prepare_job_id != JOB_ID:
            raise corpus_seal.CorpusSealError("external anchor mismatch")
        return fixture.seal_manifest

    monkeypatch.setattr(corpus_eligibility.corpus_seal, "verify_seal", fake_verify)
    return calls


def _verify(fixture: _Fixture) -> corpus_eligibility.SealedCorpusEligibility:
    return corpus_eligibility.verify_sealed_corpus_eligibility(
        fixture.root,
        configured_train_path=fixture.train,
        configured_eval_path=fixture.evaluation,
        historical_source_commit=COMMIT,
        historical_prepare_job_id=JOB_ID,
        sealed_content_sha256=str(fixture.seal_manifest["content_sha256"]),
    )


def test_returns_immutable_canonical_record_bound_to_external_anchors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _fixture(tmp_path)
    calls = _install_verifier(monkeypatch, fixture)

    eligibility = _verify(fixture)

    assert calls == [(fixture.root, COMMIT, JOB_ID)]
    record = eligibility.record
    assert record["format"] == corpus_eligibility.ELIGIBILITY_FORMAT
    assert record["seal"]["content_sha256"] == fixture.seal_manifest[
        "content_sha256"
    ]
    assert record["historical_attestation"]["independent_replay"] is True
    assert record["inputs"]["train"] == {
        "configured_path": str(fixture.train),
        "sealed_path": "data/train.jsonl",
        "bytes": fixture.train.stat().st_size,
        "rows": 2,
        "sha256": sha256_file(fixture.train),
    }
    assert record["current_compatibility"]["compiler"]["status"] == (
        "exact-source-inventory-match"
    )
    inference = record["current_compatibility"]["inference_environment"]
    assert inference == fixture.historical_attestation["inference_environment"]
    assert inference["library_identity_sha256"] == LIBRARY_PREFIX_SHA256
    assert inference["library_full_identity_sha256"] == LIBRARY_FULL_SHA256
    assert (
        inference["library_identity_sha256"]
        != inference["library_full_identity_sha256"]
    )
    assert eligibility.sha256 == corpus_eligibility.eligibility_record_sha256(
        record
    )
    assert eligibility.record_json == corpus_eligibility.canonical_eligibility_json(
        record
    )
    assert eligibility.dataset_attestation_json == (
        fixture.root / "reports" / "dataset-attestation.json"
    ).read_text(encoding="utf-8")
    assert eligibility.dataset_attestation == fixture.historical_attestation

    record["seal"]["content_sha256"] = "0" * 64
    assert eligibility.record["seal"]["content_sha256"] != "0" * 64
    detached_attestation = eligibility.dataset_attestation
    detached_attestation["independent_replay"] = False
    assert eligibility.dataset_attestation["independent_replay"] is True
    with pytest.raises(FrozenInstanceError):
        eligibility.record_json = "{}"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        eligibility.dataset_attestation_json = "{}"  # type: ignore[misc]


def test_success_path_never_replays_a_theorem(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _fixture(tmp_path)
    _install_verifier(monkeypatch, fixture)
    contract.model_v3_prefix_environment.cache_clear()
    library_identity_v3.clear_model_v3_library_identity_cache()

    def forbidden_replay(_name: str) -> object:
        raise AssertionError("eligibility must not reconstruct proof certificates")

    monkeypatch.setattr(theorem_library, "replay", forbidden_replay)
    monkeypatch.setattr(library_identity_v3, "_replay_record", forbidden_replay)
    assert _verify(fixture).record["historical_attestation"][
        "independent_replay"
    ] is True


def test_rejects_content_hash_not_obtained_from_external_trust_anchor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _fixture(tmp_path)
    _install_verifier(monkeypatch, fixture)

    with pytest.raises(
        corpus_eligibility.CorpusEligibilityError,
        match="externally trusted content hash",
    ):
        corpus_eligibility.verify_sealed_corpus_eligibility(
            fixture.root,
            configured_train_path=fixture.train,
            configured_eval_path=fixture.evaluation,
            historical_source_commit=COMMIT,
            historical_prepare_job_id=JOB_ID,
            sealed_content_sha256="0" * 64,
        )


@pytest.mark.parametrize(
    ("source_commit", "prepare_job_id"),
    (("b" * 40, JOB_ID), (COMMIT, "999999")),
)
def test_passes_and_enforces_historical_source_and_job_anchors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    source_commit: str,
    prepare_job_id: str,
) -> None:
    fixture = _fixture(tmp_path)
    calls = _install_verifier(monkeypatch, fixture)

    with pytest.raises(
        corpus_eligibility.CorpusEligibilityError,
        match="sealed corpus verification failed: external anchor mismatch",
    ):
        corpus_eligibility.verify_sealed_corpus_eligibility(
            fixture.root,
            configured_train_path=fixture.train,
            configured_eval_path=fixture.evaluation,
            historical_source_commit=source_commit,
            historical_prepare_job_id=prepare_job_id,
            sealed_content_sha256=str(fixture.seal_manifest["content_sha256"]),
        )
    assert calls == [(fixture.root, source_commit, prepare_job_id)]


@pytest.mark.parametrize(
    ("field", "wrong", "message"),
    (
        ("train", "data/val.jsonl", "exactly seal/data/train.jsonl"),
        ("eval", "data/train.jsonl", "exactly seal/data/val.jsonl"),
        ("train", "data/../data/train.jsonl", "parent traversal"),
    ),
)
def test_rejects_loader_paths_other_than_exact_sealed_train_and_val(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    wrong: str,
    message: str,
) -> None:
    fixture = _fixture(tmp_path)
    _install_verifier(monkeypatch, fixture)
    train = fixture.train
    evaluation = fixture.evaluation
    if field == "train":
        train = fixture.root / wrong
    else:
        evaluation = fixture.root / wrong

    with pytest.raises(corpus_eligibility.CorpusEligibilityError, match=message):
        corpus_eligibility.verify_sealed_corpus_eligibility(
            fixture.root,
            configured_train_path=train,
            configured_eval_path=evaluation,
            historical_source_commit=COMMIT,
            historical_prepare_job_id=JOB_ID,
            sealed_content_sha256=str(fixture.seal_manifest["content_sha256"]),
        )


def test_rejects_current_compiler_inventory_growth_without_replaying_proofs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _fixture(tmp_path)
    _install_verifier(monkeypatch, fixture)
    original: Callable[[], tuple[Path, ...]] = attest._compiler_paths
    monkeypatch.setattr(
        attest,
        "_compiler_paths",
        lambda: (*original(), Path(__file__).resolve()),
    )

    with pytest.raises(
        corpus_eligibility.CorpusEligibilityError,
        match="source inventory differs",
    ):
        _verify(fixture)


def test_rejects_current_compiler_source_hash_mismatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _fixture(tmp_path)
    compiler = fixture.dataset_manifest["source"]["compiler"]
    sources = compiler["sources"]
    first = next(iter(sources))
    sources[first] = {"sha256": "0" * 64}
    fixture.refresh_bindings()
    _install_verifier(monkeypatch, fixture)

    with pytest.raises(
        corpus_eligibility.CorpusEligibilityError,
        match="source hash mismatch",
    ):
        _verify(fixture)


def test_rejects_full_library_digest_not_bound_by_authority_schedule(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _fixture(tmp_path)
    dataset = fixture.seal_manifest["dataset"]
    dataset["authority_schedule"]["full_library_sha256"] = "3" * 64
    fixture.refresh_bindings()
    _install_verifier(monkeypatch, fixture)

    with pytest.raises(
        corpus_eligibility.CorpusEligibilityError,
        match="full-library identity differs from the authority schedule",
    ):
        _verify(fixture)


@pytest.mark.parametrize(
    ("mutation", "message"),
    (
        (
            lambda report: report.__setitem__("independent_replay", False),
            "not an independent uncontaminated",
        ),
        (
            lambda report: report["prompt_contract"].__setitem__(
                "task", "tampered-task"
            ),
            "different current prompt contract",
        ),
        (
            lambda report: report["held_out_contract"].__setitem__("v", 99),
            "different current held-out contract",
        ),
    ),
)
def test_rejects_semantically_tampered_historical_attestation_even_when_rebound(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: Callable[[dict[str, object]], None],
    message: str,
) -> None:
    fixture = _fixture(tmp_path)
    mutation(fixture.historical_attestation)
    fixture.refresh_bindings()
    _install_verifier(monkeypatch, fixture)

    with pytest.raises(corpus_eligibility.CorpusEligibilityError, match=message):
        _verify(fixture)


def test_rechecks_loaded_json_against_verified_seal_file_record(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _fixture(tmp_path)
    _install_verifier(monkeypatch, fixture)
    (fixture.root / "data" / "manifest.json").write_text("{}\n", encoding="utf-8")

    with pytest.raises(
        corpus_eligibility.CorpusEligibilityError,
        match="(byte count|hash) differs from the verified seal",
    ):
        _verify(fixture)


def test_rejects_noncanonical_or_digest_tampered_eligibility_records(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _fixture(tmp_path)
    _install_verifier(monkeypatch, fixture)
    eligibility = _verify(fixture)
    record = eligibility.record
    record["eligibility_sha256"] = "0" * 64

    with pytest.raises(
        corpus_eligibility.CorpusEligibilityError,
        match="digest mismatch",
    ):
        corpus_eligibility.SealedCorpusEligibility(
            _canonical(record) + "\n",
            eligibility.dataset_attestation_json,
        )
    with pytest.raises(
        corpus_eligibility.CorpusEligibilityError,
        match="not canonical",
    ):
        corpus_eligibility.SealedCorpusEligibility(
            json.dumps(eligibility.record, indent=2) + "\n",
            eligibility.dataset_attestation_json,
        )
    with pytest.raises(
        corpus_eligibility.CorpusEligibilityError,
        match="differs from the bound sealed report",
    ):
        corpus_eligibility.SealedCorpusEligibility(
            eligibility.record_json,
            eligibility.dataset_attestation_json.replace(
                '"independent_replay":true', '"independent_replay":false'
            ),
        )
