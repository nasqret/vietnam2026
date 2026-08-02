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
        "max_new_tokens": 96,
        "max_steps": 16,
        "seed": 7,
        "sample": True,
        "search_beam_width": 8,
        "search_candidates_per_state": 4,
        "search_max_model_calls": 128,
        "search_max_states": 512,
        "created_at": "2026-07-28T12:00:00Z",
        "nonce": "a" * 32,
    }
    arguments.update(overrides)
    return REQUEST.build_request(**arguments)


TEST_MANIFEST_SHA256 = "e" * 64


def _test_authority(
    *,
    model_version: int = 2,
) -> tuple[dict[str, object], object, object]:
    environment = (
        REQUEST.trained_cli.model_v3_environment()
        if model_version == 3
        else REQUEST.trained_cli.model_v2_environment()
        if model_version == 2
        else REQUEST.trained_cli.model_v1_environment()
    )
    goal = REQUEST.trained_cli._user_goal("∀ x. x = x", environment)
    manifest: dict[str, object] = {
        "run": {"name": f"unit-v{model_version}"},
        "generation": {
            "max_new_tokens": 96,
            "do_sample": False,
            "temperature": 1.0,
            "top_p": 1.0,
        }
    }
    return manifest, environment, goal


def _test_adapter_provenance(environment: object) -> dict[str, object]:
    return {
        "training_manifest_sha256": TEST_MANIFEST_SHA256,
        "prompt_version": environment.prompt_version,
        "prompt_contract_sha256": REQUEST.prompt_contract_sha256(
            environment.prompt_version
        ),
        "base_model_id": "unit-base",
        "base_model_revision": "a" * 40,
        "adapter_sha256": "b" * 64,
        "run_name": f"unit-v{environment.prompt_version}",
        "dataset_sha256": "c" * 64,
        "environment_sha256": environment.sha256,
        "held_out_contract_sha256": "d" * 64,
        "library_snapshot_sha256": environment.library_sha256,
        "evaluation": {
            "sources": {"sha256": "1" * 64, "files": {}},
            "runtime": {"python": "unit"},
            "job": {"job_id": "123"},
        },
    }


def _patch_attested_authority(
    monkeypatch: pytest.MonkeyPatch,
) -> list[tuple[object, ...]]:
    def load(
        _adapter: Path,
        canonical_statement: str,
        *,
        require_model_v2: bool,
    ) -> tuple[object, ...]:
        assert canonical_statement == "∀ x. x = x"
        manifest, environment, goal = _test_authority(
            model_version=2 if require_model_v2 else 1
        )
        return manifest, TEST_MANIFEST_SHA256, environment, goal

    monkeypatch.setattr(REQUEST, "_load_attested_adapter_authority", load)
    snapshot_calls: list[tuple[object, ...]] = []
    monkeypatch.setattr(
        REQUEST.trained_cli,
        "_recheck_adapter_snapshot",
        lambda *args: snapshot_calls.append(args),
    )
    monkeypatch.setattr(
        REQUEST,
        "_expected_adapter_provenance",
        lambda adapter, manifest, digest: _test_adapter_provenance(
            REQUEST.trained_cli.model_v2_environment()
        ),
    )
    return snapshot_calls


def _valid_search_report(
    request: dict[str, object],
    *,
    proved: bool,
    model_version: int = 2,
) -> tuple[dict[str, object], str | None]:
    manifest, environment, goal = _test_authority(model_version=model_version)
    capabilities = goal.capabilities
    goal_environment_record = REQUEST._goal_environment_record(goal)
    identity_environment_record = REQUEST.environment_record(environment)
    prompt_digest = REQUEST.prompt_contract_sha256(environment.prompt_version)
    decoding = {
        "max_new_tokens": request["max_new_tokens"],
        "do_sample": request["sample"],
        "temperature": manifest["generation"]["temperature"],
        "top_p": manifest["generation"]["top_p"],
    }
    base_name = f"peano-policy:{manifest['run']['name']}:{TEST_MANIFEST_SHA256[:12]}"
    policy_name = f"{base_name}:kernel-guided-search"
    limits = {
        "max_depth": request["max_steps"],
        "beam_width": request["search_beam_width"],
        "candidates_per_state": request["search_candidates_per_state"],
        "max_model_calls": request["search_max_model_calls"],
        "max_states": request["search_max_states"],
    }
    commands: list[str] = ["intro", "refl"] if proved else []
    proof_nodes: int | None = None
    script: str | None = None
    publication: dict[str, object] = {"status": "no-proof"}
    if proved:
        replay = REQUEST.trained_cli.verify_proof(
            str(request["theorem"]),
            tuple(commands),
            request_id="unit-publication",
            classical=False,
            capabilities=capabilities,
        )
        assert replay.status == "proved" and replay.proof_nodes is not None
        proof_nodes = replay.proof_nodes
        script = "pa prove ∀ x. x = x\nintro\nrefl\nqed\n"
        publication = {
            "status": "proof",
            "sample": 0,
            "proof_nodes": proof_nodes,
            "commands": commands,
            "script": script,
            "script_sha256": hashlib.sha256(script.encode()).hexdigest(),
            "replay": {
                "status": "proved",
                "kernel_checked": True,
                "proof_nodes": proof_nodes,
                "surface": capabilities.label,
                "environment_sha256": REQUEST.trained_cli.capability_sha256(
                    capabilities
                ),
            },
        }
    result_status = "proof" if proved else "exhausted"
    attempt_status = "proof" if proved else "failing"
    status_counts = {
        name: int(name == attempt_status)
        for name in REQUEST.trained_cli.evaluator.ATTEMPT_STATUSES
    }
    model_calls = 2 if proved else 1
    states_discovered = 2 if proved else 1
    candidates_executed = 2 if proved else 0
    candidates_requested = (
        model_calls * int(request["search_candidates_per_state"])
    )
    candidate_lines = candidates_requested if proved else 0
    malformed = 0 if proved else candidates_requested
    attempt = {
        "sample": 0,
        "seed": REQUEST.trained_cli._stable_search_seed(int(request["seed"]), goal),
        "status": attempt_status,
        "steps": len(commands),
        "commands": commands,
        "proof_nodes": proof_nodes,
        "error": None if proved else "kernel-guided search exhausted",
    }
    goal_record = {
        "name": goal.name,
        "statement": "∀ x. x = x",
        "classical": False,
        "surface_profile": capabilities.label,
        "environment_sha256": goal_environment_record["environment_sha256"],
        "allowed_theorems": list(goal.allowed_theorems),
        "passed": proved,
        "status_counts": status_counts,
        "attempts": [attempt],
    }
    report: dict[str, object] = {
        "v": REQUEST.trained_cli.evaluator.EVAL_VERSION,
        "policy": policy_name,
        "policy_identity": {
            "name": policy_name,
            "kind": "peano-kernel-guided-search-v1",
            "base_policy": {
                "name": base_name,
                "kind": "peano-policy-adapter-v1",
                "prompt_version": environment.prompt_version,
                "prompt_contract_sha256": prompt_digest,
                "environment": identity_environment_record,
                "decoding": decoding,
                "provenance": _test_adapter_provenance(environment),
            },
            "limits": dict(limits),
            "seed": request["seed"],
            "seed_schedule": "sha256-json-v1(seed,goal_name,goal_statement)",
            "decoder_batching": "one-model-generate-call-per-search-state",
        },
        "evaluator": REQUEST._expected_evaluator_identity(),
        "judge": "checked_final(original_target, exact_mode)",
        "goal_set_sha256": REQUEST.trained_cli.evaluator._goal_set_sha256((goal,)),
        "seed": request["seed"],
        "k": 1,
        "max_steps": request["max_steps"],
        "goal_count": 1,
        "attempt_count": 1,
        "proved_goals": int(proved),
        "pass@k": float(proved),
        "status_counts": status_counts,
        "goals": [goal_record],
        "mode": "kernel-guided-search",
        "search": {
            "engine": "training.peano_policy.search.search-v1",
            "budget_scope": "per-goal",
            "limits": dict(limits),
            "aggregate_upper_bound": {
                "model_generate_calls": request["search_max_model_calls"],
                "candidate_sequences": (
                    request["search_max_model_calls"]
                    * request["search_candidates_per_state"]
                ),
                "generated_sequence_tokens": (
                    request["search_max_model_calls"]
                    * request["search_candidates_per_state"]
                    * request["max_new_tokens"]
                ),
            },
            "actual": {
                "model_generate_calls": model_calls,
                "states_expanded": model_calls,
                "states_discovered": states_discovered,
                "candidates_executed": candidates_executed,
                "candidate_sequences_requested": candidates_requested,
                "candidate_sequences_returned": candidates_requested,
                "candidate_lines_returned": candidate_lines,
                "malformed_sequences_rejected": malformed,
                "frontier_peak_per_goal": 1,
            },
            "goals": [
                {
                    "name": goal.name,
                    "environment_sha256": goal_environment_record[
                        "environment_sha256"
                    ],
                    "result": {
                        "status": result_status,
                        "theorem": "∀ x. x = x",
                        "commands": commands,
                        "certificate_nodes": proof_nodes,
                        "diagnostics": [],
                        "model_calls": model_calls,
                        "states_expanded": model_calls,
                        "states_discovered": states_discovered,
                        "candidates_executed": candidates_executed,
                        "frontier_peak": 1,
                        "depth_reached": len(commands),
                    },
                    "decoder": {
                        "model_generate_calls": model_calls,
                        "candidate_sequences_requested": candidates_requested,
                        "candidate_sequences_returned": candidates_requested,
                        "candidate_lines_returned": candidate_lines,
                        "malformed_sequences_rejected": malformed,
                        "one_batched_call_per_search_state": True,
                    },
                }
            ],
        },
        "proof_publication": publication,
    }
    return report, script


def _run_fake_report(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    request: dict[str, object],
    report_record: dict[str, object],
    *,
    status: int,
    proof_script: str | None = None,
) -> dict[str, object]:
    _patch_attested_authority(monkeypatch)
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
        lambda **kwargs: {
            "path": "logs/proof-requests.tsv",
            "row": {},
            "row_sha256": "d" * 64,
        },
    )

    def fake_main(arguments: list[str]) -> int:
        report = Path(arguments[arguments.index("--output") + 1])
        proof = Path(arguments[arguments.index("--proof-output") + 1])
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(json.dumps(report_record) + "\n", encoding="utf-8")
        if proof_script is not None:
            proof.write_text(proof_script, encoding="utf-8")
        return status

    monkeypatch.setattr(REQUEST.trained_cli, "main", fake_main)
    return REQUEST.run_request(str(request["id"]), tmp_path / "adapter")


def _claim_zero_search_work(report: dict[str, object]) -> None:
    search = report["search"]
    search_goal = search["goals"][0]
    result = search_goal["result"]
    decoder = search_goal["decoder"]
    result.update(
        {
            "model_calls": 0,
            "states_expanded": 0,
            "states_discovered": 1,
            "candidates_executed": 0,
            "frontier_peak": 1,
        }
    )
    decoder.update(
        {
            "model_generate_calls": 0,
            "candidate_sequences_requested": 0,
            "candidate_sequences_returned": 0,
            "candidate_lines_returned": 0,
            "malformed_sequences_rejected": 0,
        }
    )
    search["actual"] = {
        "model_generate_calls": 0,
        "states_expanded": 0,
        "states_discovered": 1,
        "candidates_executed": 0,
        "candidate_sequences_requested": 0,
        "candidate_sequences_returned": 0,
        "candidate_lines_returned": 0,
        "malformed_sequences_rejected": 0,
        "frontier_peak_per_goal": 1,
    }


def test_request_identity_binds_exact_theorem_and_search_budget() -> None:
    first = _request()
    assert REQUEST.validate_request(first) == first
    assert len(first["id"]) == 64
    assert first["v"] == 2
    assert first["mode"] == "kernel-guided-search"
    assert first["theorem"] == "forall n. n = n"
    assert _request(nonce="b" * 32)["id"] != first["id"]
    assert _request(theorem="forall n. n + 0 = n")["id"] != first["id"]
    for field in (
        "max_new_tokens",
        "max_steps",
        "search_beam_width",
        "search_candidates_per_state",
        "search_max_model_calls",
        "search_max_states",
    ):
        changed = _request(**{field: int(first[field]) + 1})
        assert changed["id"] != first["id"]


def test_legacy_rollout_request_remains_valid_with_its_original_identity() -> None:
    body = {
        "created_at": "2026-07-28T12:00:00Z",
        "k": 4,
        "max_steps": 16,
        "nonce": "b" * 32,
        "sample": True,
        "seed": 7,
        "theorem": "forall n. n = n",
        "v": 1,
    }
    legacy = {"id": REQUEST._request_digest(body), **body}

    assert legacy["id"] == (
        "df6f1e0a449108bbaf0f405e0d045c0ea1f30e20a38c5fd9d5c64a9b40ee2009"
    )
    assert REQUEST.validate_request(legacy) == legacy


@pytest.mark.parametrize(
    "overrides",
    (
        {"theorem": "n = n"},
        {"max_new_tokens": 1_025},
        {"max_steps": 33},
        {"search_beam_width": 257},
        {"search_candidates_per_state": 65},
        {"search_max_model_calls": 4_097},
        {"search_max_states": 4_097},
        {"seed": -1},
        {"seed": 2**63},
        {"nonce": "../unsafe"},
        {"created_at": "not-a-time"},
    ),
)
def test_request_rejects_open_unsafe_or_excessive_work(
    overrides: dict[str, object],
) -> None:
    with pytest.raises((TypeError, ValueError)):
        _request(**overrides)


def test_request_rejects_decoder_search_cross_product_before_model_loading() -> None:
    with pytest.raises(ValueError, match="generated sequence tokens"):
        _request(
            max_new_tokens=96,
            search_candidates_per_state=64,
            search_max_model_calls=4_096,
        )


def test_search_request_rejects_attested_model_v1_but_legacy_can_replay_it(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    manifest = {"kind": "unit-v1"}
    environment = REQUEST.trained_cli.model_v1_environment()
    monkeypatch.setattr(
        REQUEST.trained_cli,
        "_read_adapter_manifest_snapshot",
        lambda adapter: (manifest, TEST_MANIFEST_SHA256),
    )
    monkeypatch.setattr(
        REQUEST.trained_cli,
        "attested_training_environment",
        lambda value: environment,
    )

    with pytest.raises(ValueError, match="exact model-v2 or model-v3 authority"):
        REQUEST._load_attested_adapter_authority(
            tmp_path / "adapter",
            "∀ x. x = x",
            require_model_v2=True,
        )
    loaded, digest, legacy_environment, goal = (
        REQUEST._load_attested_adapter_authority(
            tmp_path / "adapter",
            "∀ x. x = x",
            require_model_v2=False,
        )
    )
    assert loaded is manifest
    assert digest == TEST_MANIFEST_SHA256
    assert legacy_environment == environment
    assert goal.surface_profile == "model-v1"


def test_search_request_accepts_exact_model_v3_247_theorem_authority(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    manifest = {"kind": "unit-v3"}
    environment = REQUEST.trained_cli.model_v3_environment()
    monkeypatch.setattr(
        REQUEST.trained_cli,
        "_read_adapter_manifest_snapshot",
        lambda adapter: (manifest, TEST_MANIFEST_SHA256),
    )
    monkeypatch.setattr(
        REQUEST.trained_cli,
        "attested_training_environment",
        lambda value: environment,
    )

    loaded, digest, search_environment, goal = (
        REQUEST._load_attested_adapter_authority(
            tmp_path / "adapter",
            "∀ x. x = x",
            require_model_v2=True,
        )
    )

    assert loaded is manifest
    assert digest == TEST_MANIFEST_SHA256
    assert search_environment == environment
    assert goal.surface_profile == "model-v3"
    assert goal.allowed_theorems == environment.capabilities.allowed_theorems
    assert len(goal.allowed_theorems) == 247


def test_search_report_accepts_only_exact_model_v3_decode_and_authority(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    request = _request(sample=False)
    report, script = _valid_search_report(
        request,
        proved=False,
        model_version=3,
    )
    manifest, environment, goal = _test_authority(model_version=3)
    limits = {
        "max_depth": request["max_steps"],
        "beam_width": request["search_beam_width"],
        "candidates_per_state": request["search_candidates_per_state"],
        "max_model_calls": request["search_max_model_calls"],
        "max_states": request["search_max_states"],
    }
    monkeypatch.setattr(
        REQUEST,
        "_expected_adapter_provenance",
        lambda adapter, loaded, digest: _test_adapter_provenance(environment),
    )

    REQUEST._validate_v2_report_identity(
        report,
        request,
        tmp_path / "adapter",
        manifest,
        TEST_MANIFEST_SHA256,
        environment,
        goal,
        limits,
    )
    assert script is None
    assert report["goals"][0]["surface_profile"] == "model-v3"
    assert len(report["goals"][0]["allowed_theorems"]) == 247
    REQUEST._validate_v2_search_accounting(
        report,
        request,
        goal,
        report["proof_publication"],
        status=1,
        expected_limits=limits,
    )


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
    request = _request(sample=False)
    snapshot_calls = _patch_attested_authority(monkeypatch)
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
        assert arguments[arguments.index("--max-new-tokens") + 1] == "96"
        assert arguments[arguments.index("--mode") + 1] == "search"
        assert arguments[arguments.index("--search-beam-width") + 1] == "8"
        assert arguments[arguments.index("--search-candidates-per-state") + 1] == "4"
        assert arguments[arguments.index("--search-max-model-calls") + 1] == "128"
        assert arguments[arguments.index("--search-max-states") + 1] == "512"
        assert "--k" not in arguments
        report = Path(arguments[arguments.index("--output") + 1])
        proof = Path(arguments[arguments.index("--proof-output") + 1])
        report_record, script = _valid_search_report(request, proved=True)
        assert script is not None
        proof.parent.mkdir(parents=True, exist_ok=True)
        proof.write_text(script, encoding="utf-8")
        report.write_text(
            json.dumps(report_record) + "\n",
            encoding="utf-8",
        )
        return 0

    monkeypatch.setattr(REQUEST.trained_cli, "main", fake_main)
    summary = REQUEST.run_request(request["id"], tmp_path / "adapter")

    assert summary["status"] == "proved"
    assert summary["proof"]["sha256"]
    assert len(snapshot_calls) == 2
    assert all(call[0] == tmp_path / "adapter" for call in snapshot_calls)
    assert all(call[2] == TEST_MANIFEST_SHA256 for call in snapshot_calls)
    assert (output_root / f"{request['id']}.run.json").is_file()


def test_run_request_preserves_legacy_v1_rollout_dispatch(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    request = REQUEST._build_legacy_request(
        theorem="forall n. n = n",
        k=4,
        max_steps=16,
        seed=7,
        sample=True,
        created_at="2026-07-28T12:00:00Z",
        nonce="c" * 32,
    )
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
        lambda **kwargs: {
            "path": "logs/proof-requests.tsv",
            "row": {},
            "row_sha256": "d" * 64,
        },
    )

    def fake_main(arguments: list[str]) -> int:
        assert arguments[arguments.index("--k") + 1] == "4"
        assert "--mode" not in arguments
        assert "--max-new-tokens" not in arguments
        assert not any(argument.startswith("--search-") for argument in arguments)
        report = Path(arguments[arguments.index("--output") + 1])
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(
            json.dumps(
                {
                    "seed": 7,
                    "k": 4,
                    "max_steps": 16,
                    "goal_count": 1,
                    "goals": [
                        {
                            "statement": "∀ x. x = x",
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
    summary = REQUEST.run_request(request["id"], tmp_path / "adapter")

    assert summary["status"] == "no-proof"
    assert summary["proof"] is None


def test_run_request_rejects_report_for_different_search_budget(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    request = _request(sample=False)
    _patch_attested_authority(monkeypatch)
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
        report_record, _script = _valid_search_report(request, proved=False)
        report_record["search"]["limits"]["max_model_calls"] = 127
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(
            json.dumps(report_record) + "\n",
            encoding="utf-8",
        )
        return 1

    monkeypatch.setattr(REQUEST.trained_cli, "main", fake_main)
    with pytest.raises(RuntimeError, match="search engine or limits"):
        REQUEST.run_request(request["id"], tmp_path / "adapter")


@pytest.mark.parametrize(
    "mutation",
    (
        "missing-policy",
        "missing-evaluator",
        "search-kind",
        "adapter-kind",
        "adapter-name",
        "provenance",
        "sample",
        "surface",
        "environment",
    ),
)
def test_v2_run_rejects_missing_or_forged_policy_and_environment_identity(
    mutation: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    request = _request(sample=False)
    report, _script = _valid_search_report(request, proved=False)
    identity = report["policy_identity"]
    if mutation == "missing-policy":
        report.pop("policy_identity")
    elif mutation == "missing-evaluator":
        report.pop("evaluator")
    elif mutation == "search-kind":
        identity["kind"] = "forged-search"
    elif mutation == "adapter-kind":
        identity["base_policy"]["kind"] = "forged-adapter"
    elif mutation == "adapter-name":
        identity["base_policy"]["name"] = "forged-adapter-name"
    elif mutation == "provenance":
        identity["base_policy"]["provenance"]["dataset_sha256"] = "0" * 64
    elif mutation == "sample":
        identity["base_policy"]["decoding"]["do_sample"] = True
    elif mutation == "surface":
        identity["base_policy"]["environment"]["surface"] = "model-v1"
    elif mutation == "environment":
        identity["base_policy"]["environment"]["environment_sha256"] = "0" * 64
    else:  # pragma: no cover - parametrization invariant
        raise AssertionError(mutation)

    with pytest.raises(RuntimeError, match="identity"):
        _run_fake_report(
            monkeypatch,
            tmp_path,
            request,
            report,
            status=1,
        )


@pytest.mark.parametrize(
    "mutation",
    (
        "missing-aggregate",
        "missing-actual",
        "missing-decoder",
        "bool-top-count",
        "bool-result-count",
        "inflated-result-count",
        "forged-aggregate-bound",
        "incoherent-actual",
        "incoherent-decoder",
        "no-proof-with-proof-attempt",
    ),
)
def test_v2_run_rejects_missing_inflated_or_incoherent_search_accounting(
    mutation: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    request = _request(sample=False)
    report, _script = _valid_search_report(request, proved=False)
    search = report["search"]
    search_goal = search["goals"][0]
    result = search_goal["result"]
    if mutation == "missing-aggregate":
        search.pop("aggregate_upper_bound")
    elif mutation == "missing-actual":
        search.pop("actual")
    elif mutation == "missing-decoder":
        search_goal.pop("decoder")
    elif mutation == "bool-top-count":
        report["attempt_count"] = True
    elif mutation == "bool-result-count":
        result["model_calls"] = True
    elif mutation == "inflated-result-count":
        result["states_discovered"] = request["search_max_states"] + 1
    elif mutation == "forged-aggregate-bound":
        search["aggregate_upper_bound"]["candidate_sequences"] += 1
    elif mutation == "incoherent-actual":
        search["actual"]["states_expanded"] += 1
    elif mutation == "incoherent-decoder":
        search_goal["decoder"]["candidate_sequences_returned"] -= 1
    elif mutation == "no-proof-with-proof-attempt":
        report["goals"][0]["attempts"][0]["status"] = "proof"
    else:  # pragma: no cover - parametrization invariant
        raise AssertionError(mutation)

    with pytest.raises(RuntimeError):
        _run_fake_report(
            monkeypatch,
            tmp_path,
            request,
            report,
            status=1,
        )


def test_v2_run_rejects_proved_report_with_zero_search_work(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    request = _request(sample=False)
    report, script = _valid_search_report(request, proved=True)
    assert script is not None

    # Keep the root/frontier counters genuine while claiming that the depth-2
    # proof required no expansion, decoding, or executed candidate.  This used
    # to satisfy all pairwise accounting equations despite being impossible for
    # training.peano_policy.search.search.
    _claim_zero_search_work(report)

    with pytest.raises(RuntimeError, match="internally inconsistent"):
        _run_fake_report(
            monkeypatch,
            tmp_path,
            request,
            report,
            status=0,
            proof_script=script,
        )


def test_v2_run_rejects_no_proof_report_that_never_expanded_the_root(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    request = _request(sample=False)
    report, script = _valid_search_report(request, proved=False)
    assert script is None
    _claim_zero_search_work(report)

    with pytest.raises(RuntimeError, match="internally inconsistent"):
        _run_fake_report(
            monkeypatch,
            tmp_path,
            request,
            report,
            status=1,
        )


@pytest.mark.parametrize(
    "mutation",
    (
        "too-few-model-calls",
        "too-few-executed-candidates",
        "too-few-returned-lines",
    ),
)
def test_v2_run_rejects_work_below_the_proved_path_depth(
    mutation: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    request = _request(sample=False)
    report, script = _valid_search_report(request, proved=True)
    assert script is not None
    search = report["search"]
    search_goal = search["goals"][0]
    result = search_goal["result"]
    decoder = search_goal["decoder"]

    if mutation == "too-few-model-calls":
        result["model_calls"] = 1
        result["states_expanded"] = 1
        decoder["model_generate_calls"] = 1
        decoder["candidate_sequences_requested"] = 4
        decoder["candidate_sequences_returned"] = 4
        decoder["candidate_lines_returned"] = 4
    elif mutation == "too-few-executed-candidates":
        result["candidates_executed"] = 1
    elif mutation == "too-few-returned-lines":
        result["candidates_executed"] = 1
        decoder["candidate_sequences_returned"] = 1
        decoder["candidate_lines_returned"] = 1
    else:  # pragma: no cover - parametrization invariant
        raise AssertionError(mutation)

    search["actual"] = {
        "model_generate_calls": result["model_calls"],
        "states_expanded": result["states_expanded"],
        "states_discovered": result["states_discovered"],
        "candidates_executed": result["candidates_executed"],
        "candidate_sequences_requested": decoder[
            "candidate_sequences_requested"
        ],
        "candidate_sequences_returned": decoder["candidate_sequences_returned"],
        "candidate_lines_returned": decoder["candidate_lines_returned"],
        "malformed_sequences_rejected": decoder["malformed_sequences_rejected"],
        "frontier_peak_per_goal": result["frontier_peak"],
    }

    with pytest.raises(
        RuntimeError,
        match="proved search counters cannot account for the winning path",
    ):
        _run_fake_report(
            monkeypatch,
            tmp_path,
            request,
            report,
            status=0,
            proof_script=script,
        )


def test_legacy_report_rejects_present_null_search_key(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    request = REQUEST._build_legacy_request(
        theorem="forall n. n = n",
        k=1,
        max_steps=16,
        seed=7,
        sample=False,
        created_at="2026-07-28T12:00:00Z",
        nonce="9" * 32,
    )
    report = {
        "seed": 7,
        "k": 1,
        "max_steps": 16,
        "goal_count": 1,
        "goals": [
            {
                "statement": "∀ x. x = x",
                "classical": False,
                "surface_profile": "model-v1",
                "passed": False,
            }
        ],
        "search": None,
        "proof_publication": {"status": "no-proof"},
    }
    with pytest.raises(RuntimeError, match="evaluation report disagree"):
        _run_fake_report(
            monkeypatch,
            tmp_path,
            request,
            report,
            status=1,
        )


def test_v2_run_rejects_forged_publication_replay_metadata(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    request = _request(sample=False)
    report, script = _valid_search_report(request, proved=True)
    assert script is not None
    report["proof_publication"]["replay"]["kernel_checked"] = False

    with pytest.raises(RuntimeError, match="independent original-goal replay"):
        _run_fake_report(
            monkeypatch,
            tmp_path,
            request,
            report,
            status=0,
            proof_script=script,
        )


def test_v2_run_rejects_self_consistent_hash_for_wrong_script_bytes(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    request = _request(sample=False)
    report, script = _valid_search_report(request, proved=True)
    assert script is not None
    forged = "pa prove 0 = 0\nrefl\nqed\n"
    publication = report["proof_publication"]
    publication["script"] = forged
    publication["script_sha256"] = hashlib.sha256(forged.encode()).hexdigest()

    with pytest.raises(RuntimeError, match="not exactly report-bound"):
        _run_fake_report(
            monkeypatch,
            tmp_path,
            request,
            report,
            status=0,
            proof_script=forged,
        )


def test_legacy_v1_proof_still_uses_attested_original_goal_replay(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    request = REQUEST._build_legacy_request(
        theorem="forall n. n = n",
        k=4,
        max_steps=16,
        seed=7,
        sample=True,
        created_at="2026-07-28T12:00:00Z",
        nonce="f" * 32,
    )
    source_request = _request(sample=True)
    search_report, script = _valid_search_report(
        source_request,
        proved=True,
        model_version=1,
    )
    assert script is not None
    legacy_report = {
        "seed": 7,
        "k": 4,
        "max_steps": 16,
        "goal_count": 1,
        "goals": search_report["goals"],
        "proof_publication": search_report["proof_publication"],
    }

    summary = _run_fake_report(
        monkeypatch,
        tmp_path,
        request,
        legacy_report,
        status=0,
        proof_script=script,
    )
    assert summary["status"] == "proved"
