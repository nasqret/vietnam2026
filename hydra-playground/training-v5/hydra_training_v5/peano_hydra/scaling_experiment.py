"""Fresh, CPU-only contracts for the next Qwen curriculum experiment.

These plans are requests, not GPU approvals. Old eight-call plans, model
origins, source caps and completed experiments are never edited or resumed.
Data validation, human lineage/reference review, token preflight and a new
transfer/allocation approval are separate, explicit gates.
"""

from __future__ import annotations

from collections import defaultdict
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat


PILOT_SCHEMA = "peano-hydra-frontier-pilot-plan-v1"
EVALUATION_SCHEMA = "peano-hydra-frontier-matched-budget-plan-v1"
BENCHMARK_EVALUATION_SCHEMA = "peano-hydra-frontier-benchmark-budget-plan-v2"
BENCHMARK_COHORTS = frozenset(("frontier-heldout-candidate32", "frontier-regression32"))
BENCHMARK_CONTEXT_FIELDS = frozenset((
    "benchmark_manifest_sha256", "benchmark_audit_sha256", "benchmark_review_sha256",
    "heldout_goals_sha256", "candidate_readiness_sha256",
))
METRICS_SCHEMA = "peano-hydra-frontier-matched-budget-metadata-v1"
MODEL_ID = "Qwen/Qwen3-1.7B-Base"
MODEL_REVISION = "ea980cb0a6c2ae4b936e82123acc929f1cec04c1"
SEED = 20260826
# Exact ordered name/source/canonical-statement/hash projections from the
# independently replayed search-v2 report fa8cfbaf...9924ef5. Lineage metadata
# is a separate bound input, never permission to rename the fixed cohorts.
COHORT_GOAL_SHA256 = {
    "exposed-primary32": "e55c830c67bafc979d1317b975c89bbf5b599e362787d516828e9c7c27216efb",
    "posthoc-frontier12": "4d0153958836e2f9a4fb905957e18949e842bd16f45fa279b77bf19ee49d9d0f",
}
MAX_PILOT_ROWS = 16_384
MAX_OPTIMIZER_STEPS = 2_048
MAX_EVALUATION_GOALS = 128
MAX_RECORD_BYTES = 4 * 1024**2
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_NAME = re.compile(r"[a-z][a-z0-9_-]{0,95}\Z")
ROOT = Path(__file__).absolute().parents[2]
_SOURCE_FILES = (
    "scripts/prepare_peano_hydra_scaling.py", "scripts/hydra_bounded_exec.py",
    "scripts/review_peano_hydra_scaling.py",
    "training/peano_hydra/scaling_experiment.py", "training/peano_hydra/scaling_workflow.py",
    "training/peano_hydra/scaling_lineage.py", "training/peano_hydra/scaling_shards.py",
    "training/peano_hydra/scaling_admission.py",
    "training/peano_hydra/origin_bridge.py", "training/peano_hydra/comparison.py",
    "training/peano_hydra/frontier_curriculum.py", "training/peano_hydra/self_training.py",
    "training/peano_hydra/composition.py", "training/peano_hydra/composition_scale.py",
    "training/peano_hydra/witness_repair.py", "training/peano_hydra/posttrain.py",
    "training/peano_hydra/curriculum.py", "training/peano_hydra/epoch.py",
    "training/peano_hydra/protocol.py", "training/peano_hydra/review_runtime.py",
    "training/peano_hydra/development.py", "training/peano_hydra/corrective_workflow.py",
    "training/peano_policy/authority.py", "training/peano_policy/authority_runtime.py",
    "training/peano_policy/contract.py", "training/peano_policy/prompt.py",
    "training/peano_policy/data.py", "training/peano_policy/search.py",
    "training/peano_policy/state_identity.py", "training/peano_policy/manifest.py",
    "training/peano_hydra/configs/qwen3_1_7b_alpha_posttrain.toml",
    "peano-lab/py/peano_lab/batch.py", "peano-lab/py/peano_lab/ui/prove.py",
    "peano-lab/py/peano_lab/library/theorems.py",
)


class ScalingExperimentError(ValueError):
    """A new experiment lost its evidence or matched-budget boundary."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ScalingExperimentError(message)


def canonical(value: object) -> bytes:
    try:
        raw = json.dumps(value, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, RecursionError, UnicodeError) as error:
        raise ScalingExperimentError("record is not finite UTF-8 JSON") from error
    require(len(raw) <= MAX_RECORD_BYTES, "metadata record exceeds its byte bound")
    return raw


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def execution_source_inventory() -> dict[str, dict]:
    """Bounded no-follow fingerprints, not a whole-repository attestation."""
    names = set(_SOURCE_FILES)
    entries_seen = 0
    for relative in ("peano-lab/py/peano_lab/kernel", "peano-lab/py/peano_lab/engine"):
        pending = [(ROOT / relative, 0)]
        while pending:
            directory, depth = pending.pop()
            require(directory.is_dir() and not directory.is_symlink(), "unsafe native source directory")
            with os.scandir(directory) as entries:
                for entry in entries:
                    entries_seen += 1
                    require(entries_seen <= 256, "native source entry bound exceeded")
                    if entry.name == "__pycache__":
                        continue
                    require(not entry.is_symlink(), "source inventory cannot follow symlinks")
                    if entry.is_dir(follow_symlinks=False):
                        require(depth < 4, "source inventory depth exceeded")
                        pending.append((Path(entry.path), depth + 1))
                    elif entry.name.endswith(".py"):
                        names.add(Path(entry.path).relative_to(ROOT).as_posix())
    require(len(names) <= 128, "execution source file bound exceeded")
    result = {}
    for name in sorted(names):
        path = ROOT / name
        require(not any(parent.is_symlink() for parent in path.parents), "symlink source ancestor")
        with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), "rb") as stream:
            before = os.fstat(stream.fileno())
            require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_size <= 2 * 1024**2,
                    "execution input is not one bounded regular file")
            raw = stream.read(2 * 1024**2 + 1)
            after = os.fstat(stream.fileno())
        signature = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns, s.st_nlink)
        require(len(raw) == before.st_size and signature(before) == signature(after) == signature(path.lstat()),
                "execution source changed during fingerprinting")
        result[name] = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
    return result


def sha(value: object, label: str) -> str:
    require(type(value) is str and _SHA.fullmatch(value) is not None,
            label + " must be an exact lowercase SHA-256")
    return value


def integer(value: object, label: str, minimum: int, maximum: int) -> int:
    require(type(value) is int and minimum <= value <= maximum,
            label + " exceeds its integer bound")
    return value


def keys(value: object, expected: set[str], label: str) -> None:
    require(type(value) is dict and set(value) == expected, label + " has unexpected fields")


def _name(value: object, label: str) -> str:
    require(type(value) is str and _NAME.fullmatch(value) is not None,
            label + " is not a bounded experiment identifier")
    return value


def _signed(record: dict, field: str) -> dict:
    require(type(record) is dict and field in record, "missing signed metadata")
    body = {k: v for k, v in record.items() if k != field}
    require(record[field] == digest(body), "metadata digest differs")
    return body


def build_pilot_plan(*, run_id: str, source_manifest_sha256: str,
                     shard_manifest_sha256: str, lineage_proposal_sha256: str,
                     epoch_sha256: str, authority_sha256: str,
                     baseline_adapter_manifest_sha256: str,
                     split_rows: dict[str, int], profile: str = "pilot") -> dict:
    """Plan one fresh-base one-epoch SFT run; never claim any gate passed."""
    _name(run_id, "run ID")
    require(type(profile) is str and profile in {"smoke", "pilot"}, "unknown pilot profile")
    pins = {
        "source_manifest_sha256": source_manifest_sha256,
        "shard_manifest_sha256": shard_manifest_sha256,
        "lineage_proposal_sha256": lineage_proposal_sha256,
        "epoch_sha256": epoch_sha256,
        "authority_sha256": authority_sha256,
        "baseline_adapter_manifest_sha256": baseline_adapter_manifest_sha256,
    }
    for label, value in pins.items():
        sha(value, label)
    keys(split_rows, {"train", "dev", "quarantine"}, "pilot split counts")
    counts = {k: integer(v, k + " rows", 0, MAX_PILOT_ROWS) for k, v in split_rows.items()}
    require(counts["train"] > 0 and counts["dev"] > 0, "nonempty TRAIN and DEV required")
    require(sum(counts.values()) <= MAX_PILOT_ROWS, "total source rows exceed existing pilot cap")
    require(profile != "pilot" or 12_000 <= counts["train"] <= 15_000,
            "pilot requires the separately declared 12k–15k TRAIN band")
    updates = math.ceil(counts["train"] / 8)
    require(updates <= MAX_OPTIMIZER_STEPS, "optimizer schedule exceeds existing cap")
    body = {
        "schema": PILOT_SCHEMA, "run_id": run_id, "profile": profile,
        "status": "smoke-only-not-a-training-run" if profile == "smoke" else "planned-not-admitted",
        **pins, "split_rows": counts,
        "model": {"model_id": MODEL_ID, "revision": MODEL_REVISION},
        "initialization": "fresh-pinned-base-plus-new-lora; never overwrite or resume saved adapter",
        "objective": "completion-only-next-native-tactic-sft",
        "epochs": 1, "per_device_train_batch_size": 1, "gradient_accumulation_steps": 8,
        "expected_optimizer_steps": updates, "max_optimizer_steps": MAX_OPTIMIZER_STEPS,
        "configured_sequence_tokens": 4096, "token_fit_checked": False,
        "preferences_consumed": False, "reinforcement_learning": False,
        "checkpoint_selection_uses_final_test": False,
        "adapter_destination": "models/peano-hydra-" + run_id,
        "required_gates": [
            "fresh-source-native-replay-and-shard-byte-join",
            "reviewed-whole-lineage-model-facing-allocation",
            "required-semantic-reference-readiness-for-new-lineage-claims",
            "exact-token-and-total-token-budget-preflight",
            "clean-frozen-execution-source-and-baseline-origin-authentication",
            "new-explicit-transfer-and-gpu-resource-approval",
        ],
        "suggested_resource_envelope": None,
        "resource_envelope_reason": "derive after token/throughput preflight; no inherited reservation",
        "training_authorized": False, "transfer_authorized": False,
        "gpu_execution_authorized": False, "model_trained": False,
        "automatic_retry": False, "resume": False, "research_claim_eligible": False,
    }
    return {**body, "plan_sha256": digest(body)}


def validate_pilot_plan(record: dict) -> dict:
    _signed(record, "plan_sha256")
    fields = ("run_id", "source_manifest_sha256", "shard_manifest_sha256",
              "lineage_proposal_sha256", "epoch_sha256", "authority_sha256",
              "baseline_adapter_manifest_sha256", "split_rows", "profile")
    try:
        expected = build_pilot_plan(**{k: record[k] for k in fields})
    except KeyError as error:
        raise ScalingExperimentError("pilot plan lost required input") from error
    require(canonical(record) == canonical(expected), "pilot plan changed its fixed contract")
    return expected


def build_evaluation_plan(*, goals: list[dict], cohort: str,
                          epoch_sha256: str, authority_sha256: str,
                          lineage_proposal_sha256: str,
                          baseline_adapter_manifest_sha256: str,
                          candidate_training_plan_sha256: str,
                          source_files_sha256: str,
                          budgets: tuple[int, ...] = (8, 16),
                          benchmark_context: dict | None = None) -> dict:
    """Register a factorial OLD/NEW by search-budget comparison before inference.

    The training-plan digest is not a preparation or adapter digest: binding
    both actual artifacts and approving allocation remain execution gates.
    Exposed frontier-only diagnostics cannot become an overall benchmark.
    """
    benchmark = benchmark_context is not None
    allowed = BENCHMARK_COHORTS if benchmark else {"exposed-primary32", "posthoc-frontier12", "review-candidate-dev"}
    require(type(cohort) is str and cohort in allowed,
            "unknown evaluation cohort; sealed final tests need their independent owner")
    if benchmark:
        keys(benchmark_context, set(BENCHMARK_CONTEXT_FIELDS), "benchmark context")
        for label, value in benchmark_context.items():
            sha(value, label)
        require(budgets == (8, 16), "benchmark pilot fixes both eight/sixteen budgets")
    require(type(budgets) is tuple and all(type(n) is int for n in budgets)
            and budgets in {(8,), (8, 16)},
            "only explicitly versioned eight/sixteen-call comparisons are supported")
    require(type(goals) is list and 1 <= len(goals) <= MAX_EVALUATION_GOALS,
            "evaluation goal count exceeds its bound")
    expected_count = 32 if benchmark else {"exposed-primary32": 32, "posthoc-frontier12": 12}.get(cohort)
    require(expected_count is None or len(goals) == expected_count, "cohort goal count differs")
    clean, names, statements = [], set(), set()
    for goal in goals:
        keys(goal, {"name", "source", "statement", "statement_sha256", "lineage_sha256"}, "goal")
        _name(goal["name"], "goal name")
        for label in ("source", "statement"):
            require(type(goal[label]) is str and 1 <= len(goal[label].encode()) <= 16_384
                    and "\x00" not in goal[label], "goal text exceeds its bound")
        sha(goal["statement_sha256"], "goal statement SHA")
        sha(goal["lineage_sha256"], "goal lineage SHA")
        require(hashlib.sha256(goal["statement"].encode()).hexdigest() == goal["statement_sha256"],
                "goal statement hash differs")
        require(goal["name"] not in names and goal["statement_sha256"] not in statements,
                "evaluation contains duplicate goals")
        names.add(goal["name"])
        statements.add(goal["statement_sha256"])
        clean.append(dict(goal))
    if cohort in COHORT_GOAL_SHA256:
        projection = [{k: g[k] for k in ("name", "source", "statement", "statement_sha256")} for g in clean]
        require(digest(projection) == COHORT_GOAL_SHA256[cohort],
                "named diagnostic cohort changed its exact ordered targets")
    if cohort == "frontier-regression32":
        projection = [{k: g[k] for k in ("name", "source", "statement", "statement_sha256")} for g in clean]
        require(digest(projection) == COHORT_GOAL_SHA256["exposed-primary32"],
                "regression cohort changed the exact historical PRIMARY32 targets")
    if cohort == "frontier-heldout-candidate32":
        require(digest(clean) == benchmark_context["heldout_goals_sha256"],
                "held-out candidate differs from its preregistered exact ordered targets")
    pins = {
        "epoch_sha256": epoch_sha256, "authority_sha256": authority_sha256,
        "lineage_proposal_sha256": lineage_proposal_sha256,
        "baseline_adapter_manifest_sha256": baseline_adapter_manifest_sha256,
        "candidate_training_plan_sha256": candidate_training_plan_sha256,
        "source_files_sha256": source_files_sha256,
    }
    for label, value in pins.items():
        sha(value, label)
    body = {
        "schema": BENCHMARK_EVALUATION_SCHEMA if benchmark else EVALUATION_SCHEMA,
        "status": "planned-not-run", **pins,
        "cohort": cohort, "goals": clean, "goal_set_sha256": digest(clean),
        "roles": ["saved-corrected", "new-frontier"], "budgets": list(budgets),
        "search_profile": "context-alpha-v1",
        "fixed_search": {"max_depth": 16, "beam_width": 4, "candidates_per_state": 4,
                         "max_states": 64, "max_new_tokens": 64, "seed": SEED},
        "ordered_slots": [{"role": role, "max_model_calls": budget, "goal": goal["name"]}
                          for role in ("saved-corrected", "new-frontier")
                          for budget in budgets for goal in clean],
        "max_model_calls_total": 2 * len(clean) * sum(budgets),
        "comparisons": {
            "training_effect": "saved versus new at the SAME call limit and authority",
            "search_effect": "eight versus sixteen with the SAME adapter",
            "cross_budget_training_claim_allowed": False,
        },
        "candidate_adapter_binding_required_after_training": True,
        "candidate_preparation_binding_required_before_execution": True,
        "all_positive_proofs_require_fresh_native_replay": True,
        "interrupted_or_unstarted": "unknown; never an invented failed proof",
        "model_generation_performed": False, "gpu_execution_authorized": False,
        "sealed_benchmark": False, "research_claim_eligible": False,
        "unknown_base_pretraining_exposure": True,
        "automatic_retry": False, "resume": False,
    }
    if benchmark:
        body["benchmark_context"] = dict(benchmark_context)
        body["independent_final_test_ownership_claimed"] = False
        body["cohort_scope"] = "agent-authored candidate with declared-source exposure review; not sealed H1"
    return {**body, "plan_sha256": digest(body)}


def validate_evaluation_plan(record: dict) -> dict:
    _signed(record, "plan_sha256")
    fields = ("goals", "cohort", "epoch_sha256", "authority_sha256", "lineage_proposal_sha256",
              "baseline_adapter_manifest_sha256", "candidate_training_plan_sha256",
              "source_files_sha256")
    try:
        context = ({"benchmark_context": record["benchmark_context"]}
                   if record["schema"] == BENCHMARK_EVALUATION_SCHEMA else {})
        expected = build_evaluation_plan(**{k: record[k] for k in fields},
                                         budgets=tuple(record["budgets"]), **context)
    except (KeyError, TypeError) as error:
        raise ScalingExperimentError("evaluation plan lost its exact inputs") from error
    require(canonical(record) == canonical(expected), "evaluation plan changed its fixed contract")
    return expected


def summarize_outcomes(plan: dict, records: list[dict]) -> dict:
    """Validate bounded result metadata, without pretending to replay proofs.

    Saved positive flags are reported, not independently verified scores.
    Missing slots and explicit interruptions stay unknown. A proof-length
    comparison uses only goals reportedly solved by both matched lanes.
    """
    plan = validate_evaluation_plan(plan)
    require(type(records) is list and len(records) <= len(plan["ordered_slots"]),
            "result metadata exceeds its slot bound")
    slots = {(r["role"], r["max_model_calls"], r["goal"]) for r in plan["ordered_slots"]}
    rows = {}
    for row in records:
        keys(row, {"role", "max_model_calls", "goal", "status", "model_generate_calls",
                   "tactic_decisions", "proof_nodes", "commands_sha256"}, "outcome")
        budget = integer(row["max_model_calls"], "call limit", 8, 16)
        _name(row["role"], "outcome role")
        _name(row["goal"], "outcome goal")
        key = (row["role"], budget, row["goal"])
        require(key in slots and key not in rows, "unplanned or duplicate evaluation outcome")
        require(type(row["status"]) is str and row["status"] in {"proof", "exhausted", "call-limit", "unknown"},
                "invalid outcome status")
        integer(row["model_generate_calls"], "generation calls", 0, budget)
        if row["status"] == "proof":
            integer(row["tactic_decisions"], "proof decisions", 1, 16)
            integer(row["proof_nodes"], "proof nodes", 1, 1_000_000)
            sha(row["commands_sha256"], "proof commands SHA")
        else:
            require(all(row[k] is None for k in ("tactic_decisions", "proof_nodes", "commands_sha256")),
                    "unproved outcome cannot supply a positive proof")
            if row["status"] == "call-limit":
                require(row["model_generate_calls"] == budget,
                        "call-limit outcome must account for its full call bound")
        rows[key] = dict(row)
    comparisons = []
    for budget in plan["budgets"]:
        by_role = defaultdict(dict)
        for (role, bound, goal), row in rows.items():
            if bound == budget:
                by_role[role][goal] = row
        old, new = by_role["saved-corrected"], by_role["new-frontier"]
        paired = [g["name"] for g in plan["goals"] if g["name"] in old and g["name"] in new
                  and old[g["name"]]["status"] != "unknown" and new[g["name"]]["status"] != "unknown"]
        common = [g for g in paired if old[g]["status"] == new[g]["status"] == "proof"]
        comparisons.append({
            "max_model_calls": budget, "known_paired_goals": len(paired),
            "unknown_pairs": len(plan["goals"]) - len(paired),
            "reported_gains": [g for g in paired if new[g]["status"] == "proof" and old[g]["status"] != "proof"],
            "reported_losses": [g for g in paired if old[g]["status"] == "proof" and new[g]["status"] != "proof"],
            "common_reported_proofs": common,
            "common_proof_decisions": {
                "saved-corrected": sum(old[g]["tactic_decisions"] for g in common),
                "new-frontier": sum(new[g]["tactic_decisions"] for g in common),
            },
        })
    body = {
        "schema": METRICS_SCHEMA, "plan_sha256": plan["plan_sha256"],
        "status": "metadata-only-not-independent-proof-verification",
        "record_count": len(rows), "missing_records": len(slots) - len(rows),
        "explicit_unknown_records": sum(r["status"] == "unknown" for r in rows.values()),
        "all_records_present": len(rows) == len(slots),
        "matched_comparisons": comparisons, "proof_replay_performed": False,
        "model_generation_attested": False, "research_claim_eligible": False,
    }
    return {**body, "summary_sha256": digest(body)}
