from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from training.peano_policy import evaluation_replay as replay  # noqa: E402


SOURCE_COMMIT = "1" * 40
JOB_ID = "172999"
SCRIPT_SHA = "2" * 64
SUPPORT_SHA = "3" * 64
MANIFEST_SHA = "4" * 64
ADAPTER_SHA = "5" * 64
DATASET_SHA = "6" * 64
PROMPT_SHA = "7" * 64
HELDOUT_SHA = "8" * 64
LIBRARY_SHA = "9" * 64
EVALUATOR_SHA = "a" * 64
SOURCE_GROUP = {"files": {"fake.py": "b" * 64}, "sha256": "c" * 64}
SEMANTIC_GROUP = {"files": {"kernel.py": "d" * 64}, "sha256": "e" * 64}
REPLAY_GROUP = {"files": {"replay.py": "f" * 64}, "sha256": "0" * 64}


def _sha(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _runtime() -> dict[str, object]:
    packages = {"python": "test"}
    return {
        "implementation": "CPython",
        "python": "3.12.0",
        "machine": "x86_64",
        "platform": "test-linux",
        "hostname": "test-node",
        "packages": packages,
        "packages_sha256": _sha(packages),
    }


def _authority() -> replay.FrozenAuthority:
    goals = tuple(
        replay.FrozenGoal(name, f"{index} = {index}", f"{index} = {index}")
        for index, name in enumerate(replay.EXPECTED_GOAL_NAMES)
    )
    environment = {
        "classical": False,
        "surface": "model-v3",
        "environment_sha256": replay.EXPECTED_ENVIRONMENT_SHA256,
        "capabilities": {
            "label": "model-v3",
            "allowed_commands": ["norm_num"],
            "allowed_theorems": ["lemma"],
        },
        "library_identity_sha256": LIBRARY_SHA,
        "library_full_identity_sha256": LIBRARY_SHA,
        "library_prefix_length": 1,
        "library_size": 1,
    }
    return replay.FrozenAuthority(
        goals=goals,
        capabilities=object(),
        environment=environment,
        allowed_theorems=("lemma",),
        evaluator_source_sha256=EVALUATOR_SHA,
        evaluator_semantic_sources=SEMANTIC_GROUP,
        evaluation_sources=SOURCE_GROUP,
        prompt_contract_sha256=PROMPT_SHA,
        held_out_contract_sha256=HELDOUT_SHA,
        library_snapshot_sha256=LIBRARY_SHA,
    )


def _job() -> dict[str, object]:
    support = {
        "status": "declared",
        "path": replay.EXPECTED_SUPPORT_SCRIPT.as_posix(),
        "sha256": SUPPORT_SHA,
        "sourced_sha256": SUPPORT_SHA,
    }
    composite = hashlib.sha256(
        f"{SCRIPT_SHA}\n{SUPPORT_SHA}\n".encode("ascii")
    ).hexdigest()
    submission = {
        "job_id": JOB_ID,
        "script": replay.EXPECTED_EVALUATION_SCRIPT.as_posix(),
        "script_sha256": composite,
        "git_commit": SOURCE_COMMIT,
        "git_dirty": "false",
        "dependency_job_id": "172998",
        "workdir": "/work/test",
        "sync_timestamp": "2026-07-30T00:00:00Z",
    }
    return {
        "scheduler": "slurm",
        "job_id": JOB_ID,
        "environment": {"SLURM_JOB_NAME": "peano-v3-eval"},
        "deployment": {
            "mode": "slurm",
            "source_sync": {
                "status": "synced",
                "path": ".peano-source-provenance.tsv",
                "sha256": "1" * 64,
                "git_commit": SOURCE_COMMIT,
                "git_dirty": False,
                "synced_at": "2026-07-30T00:00:00Z",
            },
            "job_script": {
                "status": "declared",
                "path": replay.EXPECTED_EVALUATION_SCRIPT.as_posix(),
                "file_sha256": SCRIPT_SHA,
                "sha256": composite,
                "support_script": support,
            },
            "support_script": support,
            "modules": {"status": "loaded"},
        },
        "submission": submission,
        "ledger": {"path": "logs/submissions.tsv", "row_sha256": _sha(submission)},
    }


def _context(
    calls: list[tuple[object, ...]],
    *,
    override: dict[str, object] | None = None,
) -> replay.ReplayContext:
    authority = _authority()

    def verify_proof(theorem, commands, **keywords):
        calls.append((theorem, commands, keywords))
        goal = next(goal for goal in authority.goals if goal.source == theorem)
        values = {
            "status": "proved",
            "kernel_checked": True,
            "theorem": goal.theorem,
            "tactics_requested": len(commands),
            "tactics_applied": len(commands),
            "failed_tactics": 0,
            "proof_nodes": 7,
            "mode": "verify",
            "surface": "model-v3",
            "environment_sha256": replay.EXPECTED_ENVIRONMENT_SHA256,
            "classical": False,
            "on_error": "stop",
            "goals": (),
        }
        values.update(override or {})
        return SimpleNamespace(**values)

    return replay.ReplayContext(
        authority=authority,
        verify_proof=verify_proof,
        evaluation_script_sha256=SCRIPT_SHA,
        support_script_sha256=SUPPORT_SHA,
        replay_sources=REPLAY_GROUP,
        replay_runtime=_runtime(),
        replay_job={"scheduler": "none", "deployment": {"mode": "local"}},
    )


def _search_seed(goal: replay.FrozenGoal) -> int:
    payload = json.dumps(
        [1, replay.EXPECTED_SEED, goal.name, goal.source],
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") & (2**63 - 1)


def _report(*, proved: tuple[int, ...] = (0,)) -> dict[str, object]:
    authority = _authority()
    limits = replay.EXPECTED_SEARCH_LIMITS
    goal_records: list[dict[str, object]] = []
    search_goals: list[dict[str, object]] = []
    actual = {
        "model_generate_calls": 0,
        "states_expanded": 0,
        "states_discovered": 0,
        "candidates_executed": 0,
        "candidate_sequences_requested": 0,
        "candidate_sequences_returned": 0,
        "candidate_lines_returned": 0,
        "malformed_sequences_rejected": 0,
        "frontier_peak_per_goal": 0,
    }
    top_counts = {name: 0 for name in replay.ATTEMPT_STATUSES}
    for index, goal in enumerate(authority.goals):
        is_proof = index in proved
        status = "proof" if is_proof else "failing"
        commands = ["norm_num"] if is_proof else []
        nodes = 7 if is_proof else None
        attempt = {
            "sample": 0,
            "seed": _search_seed(goal),
            "status": status,
            "steps": len(commands),
            "commands": commands,
            "proof_nodes": nodes,
            "error": None if is_proof else "kernel-guided search exhausted",
        }
        counts = {name: int(name == status) for name in replay.ATTEMPT_STATUSES}
        top_counts[status] += 1
        goal_records.append(
            {
                "name": goal.name,
                "statement": goal.theorem,
                "classical": False,
                "surface_profile": "model-v3",
                "environment_sha256": replay.EXPECTED_ENVIRONMENT_SHA256,
                "allowed_theorems": ["lemma"],
                "passed": is_proof,
                "status_counts": counts,
                "attempts": [attempt],
            }
        )
        counters = {
            "model_calls": 1,
            "states_expanded": 1,
            "states_discovered": 1,
            "candidates_executed": int(is_proof),
            "frontier_peak": 1,
            "depth_reached": 1 if is_proof else 0,
        }
        decoder = {
            "model_generate_calls": 1,
            "candidate_sequences_requested": limits["candidates_per_state"],
            "candidate_sequences_returned": int(is_proof),
            "candidate_lines_returned": int(is_proof),
            "malformed_sequences_rejected": 0,
            "one_batched_call_per_search_state": True,
        }
        search_goals.append(
            {
                "name": goal.name,
                "environment_sha256": replay.EXPECTED_ENVIRONMENT_SHA256,
                "result": {
                    "status": "proof" if is_proof else "exhausted",
                    "theorem": goal.theorem,
                    "commands": commands,
                    "certificate_nodes": nodes,
                    "diagnostics": [],
                    **counters,
                },
                "decoder": decoder,
            }
        )
        actual["model_generate_calls"] += 1
        actual["states_expanded"] += 1
        actual["states_discovered"] += 1
        actual["candidates_executed"] += int(is_proof)
        actual["candidate_sequences_requested"] += limits["candidates_per_state"]
        actual["candidate_sequences_returned"] += int(is_proof)
        actual["candidate_lines_returned"] += int(is_proof)
        actual["frontier_peak_per_goal"] = 1

    evaluation = {
        "sources": SOURCE_GROUP,
        "runtime": _runtime(),
        "job": _job(),
        "training_job_binding": {
            "status": "slurm-bound",
            "training_manifest_job_id": "172998",
            "evaluation_job_id": JOB_ID,
            "dependency_job_id": "172998",
        },
    }
    provenance = {
        "training_manifest_sha256": MANIFEST_SHA,
        "prompt_version": 3,
        "prompt_contract_sha256": PROMPT_SHA,
        "base_model_id": "Qwen/Qwen3-1.7B-Base",
        "base_model_revision": "revision",
        "adapter_sha256": ADAPTER_SHA,
        "run_name": "v3-test",
        "dataset_sha256": DATASET_SHA,
        "environment_sha256": replay.EXPECTED_ENVIRONMENT_SHA256,
        "held_out_contract_sha256": HELDOUT_SHA,
        "library_snapshot_sha256": LIBRARY_SHA,
        "evaluation": evaluation,
    }
    base_name = f"peano-policy:v3-test:{MANIFEST_SHA[:12]}"
    policy_name = f"{base_name}:kernel-guided-search"
    policy_identity = {
        "name": policy_name,
        "kind": "peano-kernel-guided-search-v1",
        "base_policy": {
            "name": base_name,
            "kind": "peano-policy-adapter-v1",
            "prompt_version": 3,
            "prompt_contract_sha256": PROMPT_SHA,
            "environment": authority.environment,
            "decoding": {
                "max_new_tokens": replay.EXPECTED_MAX_NEW_TOKENS,
                "do_sample": True,
                "temperature": 0.8,
                "top_p": 0.95,
            },
            "provenance": provenance,
        },
        "limits": limits,
        "seed": replay.EXPECTED_SEED,
        "seed_schedule": "sha256-json-v1(seed,goal_name,goal_statement)",
        "decoder_batching": "one-model-generate-call-per-search-state",
    }
    goal_count = len(authority.goals)
    proof_count = len(proved)
    return {
        "v": replay.EVALUATOR_VERSION,
        "policy": policy_name,
        "policy_identity": policy_identity,
        "evaluator": {
            "source_sha256": EVALUATOR_SHA,
            "semantic_sources": SEMANTIC_GROUP,
            "runtime": _runtime(),
        },
        "judge": replay.EXPECTED_JUDGE,
        "goal_set_sha256": replay.EXPECTED_GOAL_SET_SHA256,
        "seed": replay.EXPECTED_SEED,
        "k": 1,
        "max_steps": limits["max_depth"],
        "goal_count": goal_count,
        "attempt_count": goal_count,
        "proved_goals": proof_count,
        "pass@k": proof_count / goal_count,
        "status_counts": top_counts,
        "goals": goal_records,
        "mode": replay.EXPECTED_MODE,
        "search": {
            "engine": "training.peano_policy.search.search-v1",
            "budget_scope": "per-goal",
            "limits": limits,
            "aggregate_upper_bound": {
                "model_generate_calls": goal_count * limits["max_model_calls"],
                "candidate_sequences": goal_count
                * limits["max_model_calls"]
                * limits["candidates_per_state"],
                "generated_sequence_tokens": goal_count
                * limits["max_model_calls"]
                * limits["candidates_per_state"]
                * replay.EXPECTED_MAX_NEW_TOKENS,
            },
            "actual": actual,
            "goals": search_goals,
        },
    }


def _write_report(path: Path, report: dict[str, object]) -> bytes:
    payload = (
        json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")
    path.write_bytes(payload)
    return payload


def test_valid_report_replays_every_claim_and_emits_self_bound_attestation(
    tmp_path: Path,
) -> None:
    calls: list[tuple[object, ...]] = []
    context = _context(calls)
    report_path = tmp_path / "evaluation.json"
    payload = _write_report(report_path, _report(proved=(0, 2)))

    attestation = replay._replay_evaluation_report(
        report_path,
        expected_source_commit=SOURCE_COMMIT,
        expected_evaluation_job_id=JOB_ID,
        context=context,
        recheck_context=False,
    )

    assert len(calls) == 2
    assert [call[0] for call in calls] == ["0 = 0", "2 = 2"]
    assert all(call[2]["capabilities"] is context.authority.capabilities for call in calls)
    assert attestation["input"]["sha256"] == hashlib.sha256(payload).hexdigest()
    assert attestation["summary"]["claimed_proofs"] == 2
    assert attestation["summary"]["kernel_replayed_proofs"] == 2
    core = dict(attestation)
    claimed_digest = core.pop("attestation_sha256")
    assert claimed_digest == _sha(core)

    output = tmp_path / "replay.json"
    replay.write_replay_attestation(output, attestation)
    assert output.read_bytes() == (
        json.dumps(attestation, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")
    with pytest.raises(FileExistsError):
        replay.write_replay_attestation(output, attestation)


def test_zero_proof_report_is_verified_without_calling_kernel(tmp_path: Path) -> None:
    calls: list[tuple[object, ...]] = []
    path = tmp_path / "evaluation.json"
    _write_report(path, _report(proved=()))
    attestation = replay._replay_evaluation_report(
        path,
        expected_source_commit=SOURCE_COMMIT,
        expected_evaluation_job_id=JOB_ID,
        context=_context(calls),
        recheck_context=False,
    )
    assert calls == []
    assert attestation["summary"]["claimed_proofs"] == 0
    assert attestation["status"] == "passed"


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda value: value.__setitem__("goal_set_sha256", "0" * 64), "envelope"),
        (
            lambda value: value["goals"].reverse(),
            "theorem or capability authority",
        ),
        (
            lambda value: value["goals"][0].__setitem__("environment_sha256", "0" * 64),
            "capability authority",
        ),
        (lambda value: value.__setitem__("proved_goals", 0), "summary"),
        (
            lambda value: value["search"]["goals"][0]["result"].__setitem__(
                "certificate_nodes", 8
            ),
            "duplicated proof payload",
        ),
        (
            lambda value: value["search"]["actual"].__setitem__(
                "model_generate_calls", 5
            ),
            "aggregate search counters",
        ),
        (
            lambda value: value["policy_identity"]["base_policy"]["provenance"]
            ["evaluation"]["training_job_binding"].__setitem__(
                "training_manifest_job_id", "172997"
            ),
            "training-job binding",
        ),
    ],
)
def test_redundant_or_authority_mutations_fail_before_kernel(
    mutate, message: str
) -> None:
    calls: list[tuple[object, ...]] = []
    record = _report()
    mutate(record)
    with pytest.raises(replay.EvaluationReplayError, match=message):
        replay.validate_evaluation_record(
            record,
            expected_source_commit=SOURCE_COMMIT,
            expected_evaluation_job_id=JOB_ID,
            context=_context(calls),
        )
    assert calls == []


@pytest.mark.parametrize(
    ("override", "field"),
    [
        ({"theorem": "9 = 9"}, "theorem"),
        ({"proof_nodes": 8}, "proof_nodes"),
        ({"tactics_applied": 0}, "tactics_applied"),
        ({"environment_sha256": "0" * 64}, "environment_sha256"),
        ({"kernel_checked": False}, "kernel_checked"),
    ],
)
def test_independent_replay_must_match_theorem_nodes_steps_and_environment(
    tmp_path: Path, override: dict[str, object], field: str
) -> None:
    path = tmp_path / "evaluation.json"
    _write_report(path, _report())
    with pytest.raises(replay.EvaluationReplayError, match=field):
        replay._replay_evaluation_report(
            path,
            expected_source_commit=SOURCE_COMMIT,
            expected_evaluation_job_id=JOB_ID,
            context=_context([], override=override),
            recheck_context=False,
        )


def test_report_parser_rejects_duplicates_nonfinite_and_noncanonical_json(
    tmp_path: Path,
) -> None:
    duplicate = tmp_path / "duplicate.json"
    duplicate.write_text('{"v":4,"v":4}\n', encoding="utf-8")
    with pytest.raises(replay.EvaluationReplayError, match="duplicate JSON key"):
        replay.load_evaluation_report(duplicate)

    nonfinite = tmp_path / "nan.json"
    nonfinite.write_text('{"v":NaN}\n', encoding="utf-8")
    with pytest.raises(replay.EvaluationReplayError, match="non-finite"):
        replay.load_evaluation_report(nonfinite)

    compact = tmp_path / "compact.json"
    compact.write_text(json.dumps(_report(), sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(replay.EvaluationReplayError, match="not canonical"):
        replay.load_evaluation_report(compact)


def test_report_parser_requires_one_bounded_regular_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    oversized = tmp_path / "oversized.json"
    oversized.write_bytes(b"{" + b" " * 32 + b"}\n")
    monkeypatch.setattr(replay, "MAX_REPORT_BYTES", 16)
    with pytest.raises(replay.EvaluationReplayError, match="exceeds 16 bytes"):
        replay.load_evaluation_report(oversized)

    target = tmp_path / "target.json"
    target.write_text("{}\n", encoding="utf-8")
    link = tmp_path / "link.json"
    link.symlink_to(target)
    with pytest.raises(replay.EvaluationReplayError, match="symlink"):
        replay.load_evaluation_report(link)


def test_evaluation_job_and_current_source_are_externally_anchored() -> None:
    record = _report()
    context = _context([])
    with pytest.raises(replay.EvaluationReplayError, match="different Slurm job"):
        replay.validate_evaluation_record(
            record,
            expected_source_commit=SOURCE_COMMIT,
            expected_evaluation_job_id="1",
            context=context,
        )
    with pytest.raises(replay.EvaluationReplayError, match="different or dirty source"):
        replay.validate_evaluation_record(
            record,
            expected_source_commit="0" * 40,
            expected_evaluation_job_id=JOB_ID,
            context=context,
        )


def test_module_and_cli_help_do_not_import_model_frameworks() -> None:
    code = """
import sys
import training.peano_policy.evaluation_replay
assert 'torch' not in sys.modules
assert 'transformers' not in sys.modules
assert 'peft' not in sys.modules
"""
    imported = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert imported.returncode == 0, imported.stderr
    help_result = subprocess.run(
        [sys.executable, "scripts/replay_peano_v3_evaluation.py", "--help"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert help_result.returncode == 0, help_result.stderr
    assert "--evaluation-job-id" in help_result.stdout
    assert "--source-commit" in help_result.stdout


def test_real_frozen_authority_has_exact_v3_goals_hash_and_capabilities() -> None:
    authority = replay._load_frozen_authority()
    assert tuple(goal.name for goal in authority.goals) == replay.EXPECTED_GOAL_NAMES
    assert tuple(goal.theorem for goal in authority.goals) == (
        "0 · 0 + 3 + (0 · 1 + 1) + (3 + 0) = 7",
        "∃ x. 7 = x + 2",
        "∀ x. x + 0 + 0 = x",
        "∀ x. ∃ y. x · (x + 1) = 2 · y",
    )
    assert authority.environment["environment_sha256"] == (
        replay.EXPECTED_ENVIRONMENT_SHA256
    )
    assert authority.environment["library_prefix_length"] == 247
    assert authority.environment["library_size"] == 247
    assert len(authority.allowed_theorems) == 247
