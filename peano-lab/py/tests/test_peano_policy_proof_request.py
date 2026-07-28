"""Model-free tests for immutable WMI arbitrary-theorem requests."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPOSITORY_ROOT / "scripts" / "peano_policy_proof_request.py"
SPEC = importlib.util.spec_from_file_location("_peano_policy_proof_request", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
REQUEST = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = REQUEST
SPEC.loader.exec_module(REQUEST)


def _request(**overrides: object) -> dict[str, object]:
    arguments: dict[str, object] = {
        "theorem": "forall n. n = n",
        "k": 4,
        "max_steps": 16,
        "seed": 7,
        "sample": True,
        "created_at": "2026-07-28T12:00:00Z",
        "nonce": "a" * 32,
    }
    arguments.update(overrides)
    return REQUEST.build_request(**arguments)


def test_request_identity_binds_exact_theorem_and_search_budget() -> None:
    first = _request()
    assert REQUEST.validate_request(first) == first
    assert len(first["id"]) == 64
    assert first["theorem"] == "forall n. n = n"
    assert _request(nonce="b" * 32)["id"] != first["id"]
    assert _request(theorem="forall n. n + 0 = n")["id"] != first["id"]


@pytest.mark.parametrize(
    "overrides",
    (
        {"theorem": "n = n"},
        {"k": 2, "sample": False},
        {"k": 256, "max_steps": 17},
        {"nonce": "../unsafe"},
        {"created_at": "not-a-time"},
    ),
)
def test_request_rejects_open_unsafe_or_excessive_work(
    overrides: dict[str, object],
) -> None:
    with pytest.raises((TypeError, ValueError)):
        _request(**overrides)


def test_receive_is_canonical_immutable_and_reloads_exactly(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(REQUEST, "REPOSITORY_ROOT", tmp_path)
    monkeypatch.setattr(
        REQUEST,
        "REQUEST_ROOT",
        tmp_path / "results" / "peano-policy" / "requests",
    )
    request = _request()
    payload = REQUEST._json_bytes(request)
    path, digest = REQUEST.receive_request(request["id"], payload)

    assert digest == hashlib.sha256(payload).hexdigest()
    assert path.read_bytes() == payload
    loaded, loaded_path, loaded_digest = REQUEST.load_request(request["id"])
    assert loaded == request
    assert loaded_path == path
    assert loaded_digest == digest
    with pytest.raises(FileExistsError, match="refusing to replace"):
        REQUEST.receive_request(request["id"], payload)
    with pytest.raises(ValueError, match="canonical JSON"):
        REQUEST._parse_request_bytes(b"  " + payload, expected_id=request["id"])


def test_proof_ledger_binds_job_request_and_bytes(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    ledger = tmp_path / "logs" / "proof-requests.tsv"
    ledger.parent.mkdir()
    request = _request()
    digest = "b" * 64
    ledger.write_text(
        "timestamp\tjob_id\trequest_id\trequest_sha256\n"
        f"2026-07-28T12:00:00+07:00\t123\t{request['id']}\t{digest}\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(REQUEST, "REPOSITORY_ROOT", tmp_path)
    monkeypatch.setattr(REQUEST, "PROOF_LEDGER", ledger)
    monkeypatch.setenv("SLURM_JOB_ID", "123")

    identity = REQUEST._proof_ledger_identity(
        request_id=request["id"],
        request_sha256=digest,
    )
    assert identity["row"]["request_id"] == request["id"]
    with pytest.raises(ValueError, match="does not match"):
        REQUEST._proof_ledger_identity(
            request_id=request["id"],
            request_sha256="c" * 64,
        )


def test_run_request_accepts_only_report_bound_proof(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    request = _request(k=1, sample=False)
    request_path = tmp_path / "request.json"
    request_payload = REQUEST._json_bytes(request)
    request_path.write_bytes(request_payload)
    output_root = tmp_path / "results" / "peano-policy" / "user-proofs"
    monkeypatch.setattr(REQUEST, "REPOSITORY_ROOT", tmp_path)
    monkeypatch.setattr(REQUEST, "OUTPUT_ROOT", output_root)
    monkeypatch.setattr(
        REQUEST,
        "load_request",
        lambda request_id: (
            request,
            request_path,
            hashlib.sha256(request_payload).hexdigest(),
        ),
    )
    monkeypatch.setattr(
        REQUEST,
        "_proof_ledger_identity",
        lambda **kwargs: {"path": "logs/proof-requests.tsv", "row": {}, "row_sha256": "d" * 64},
    )

    def fake_main(arguments: list[str]) -> int:
        report = Path(arguments[arguments.index("--output") + 1])
        proof = Path(arguments[arguments.index("--proof-output") + 1])
        script = "pa prove ∀ x. x = x\nintro\nrefl\nqed\n"
        proof.parent.mkdir(parents=True, exist_ok=True)
        proof.write_text(script, encoding="utf-8")
        report.write_text(
            json.dumps(
                {
                    "seed": 7,
                    "k": 1,
                    "max_steps": 16,
                    "goal_count": 1,
                    "goals": [
                        {
                            "statement": "∀ x. x = x",
                            "classical": False,
                            "surface_profile": "model-v1",
                            "passed": True,
                        }
                    ],
                    "proof_publication": {
                        "status": "proof",
                        "script_sha256": hashlib.sha256(script.encode()).hexdigest(),
                    }
                }
            )
            + "\n",
            encoding="utf-8",
        )
        return 0

    monkeypatch.setattr(REQUEST.trained_cli, "main", fake_main)
    summary = REQUEST.run_request(request["id"], tmp_path / "adapter")

    assert summary["status"] == "proved"
    assert summary["proof"]["sha256"]
    assert (output_root / f"{request['id']}.run.json").is_file()


def test_run_request_rejects_report_for_different_theorem_or_budget(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    request = _request(k=1, sample=False)
    request_path = tmp_path / "request.json"
    request_payload = REQUEST._json_bytes(request)
    request_path.write_bytes(request_payload)
    monkeypatch.setattr(REQUEST, "REPOSITORY_ROOT", tmp_path)
    monkeypatch.setattr(
        REQUEST,
        "OUTPUT_ROOT",
        tmp_path / "results" / "peano-policy" / "user-proofs",
    )
    monkeypatch.setattr(
        REQUEST,
        "load_request",
        lambda request_id: (
            request,
            request_path,
            hashlib.sha256(request_payload).hexdigest(),
        ),
    )
    monkeypatch.setattr(
        REQUEST,
        "_proof_ledger_identity",
        lambda **kwargs: {"path": "logs/proof-requests.tsv", "row": {}, "row_sha256": "d" * 64},
    )

    def fake_main(arguments: list[str]) -> int:
        report = Path(arguments[arguments.index("--output") + 1])
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(
            json.dumps(
                {
                    "seed": 7,
                    "k": 1,
                    "max_steps": 15,
                    "goal_count": 1,
                    "goals": [
                        {
                            "statement": "0 = 0",
                            "classical": False,
                            "surface_profile": "model-v1",
                            "passed": False,
                        }
                    ],
                    "proof_publication": {"status": "no-proof"},
                }
            )
            + "\n",
            encoding="utf-8",
        )
        return 1

    monkeypatch.setattr(REQUEST.trained_cli, "main", fake_main)
    with pytest.raises(RuntimeError, match="request, status, and evaluation report"):
        REQUEST.run_request(request["id"], tmp_path / "adapter")
