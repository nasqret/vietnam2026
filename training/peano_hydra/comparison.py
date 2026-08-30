"""Matched base/previous/new inference on predeclared, exposed native goals.

Training origins remain separate: the previous V1 adapter is not relabelled as
authority-trained. All three models execute the same V4 primitive contract.
These authored parameter variants are correlated development diagnostics, not
unseen tests or independent mathematical discoveries. No model is imported by
planning, goal generation, or offline original-goal proof verification.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
PLAN_SCHEMA = "peano-hydra-three-origin-comparison-plan-v1"
RESULT_SCHEMA = "peano-hydra-three-origin-comparison-results-v1"
VERIFY_SCHEMA = "peano-hydra-three-origin-comparison-verification-v1"
PREVIOUS_MANIFEST_SHA256 = "723d0f8109c0272774f445c552d781c8e64cadfa50d0516246eb0fa2fd31a955"
FAMILIES = (
    "closed_arithmetic", "arithmetic_witnesses", "implication_transport",
    "conjunction_transport", "disjunction_transport", "universal_equalities",
    "inductive_arithmetic", "existential_composition",
)
COHORTS = ("primary", "parameter_transfer_04_07", "parameter_transfer_08_11")
ROLES = ("base", "previous", "new")
GOAL_COUNT = 96
MAX_REPORT_BYTES = 48 * 1024**2
CLAIM = (
    "32 original public development goals plus 64 small parameter variants of the same eight known families; "
    "correlated, exposed developmental diagnostics, not unseen-model advantage, FINAL, a sealed benchmark, "
    "or independent discoveries; training origins remain distinct from the shared V4 execution contract"
)


def comparison_goals() -> tuple[dict[str, object], ...]:
    """Return the fixed 96 canonical exclusion/evaluation targets, without I/O.

    The first 32 exactly preserve the original capacity panel. Two further
    32-goal cohorts extend its declared small generators to seeds 4..11. All
    decimal literals are <=24, and all 96 canonical statements are distinct.
    Seeds 4..7 were already public in the broader DEV set: no new exposure or
    semantic-independence claim follows from using a different numeric seed.
    """
    from training.peano_hydra.protocol import validate_statement

    result = []
    for start in (0, 4, 8):
        for family in FAMILIES:
            for seed in range(start, start + 4):
                k = seed + 1
                if family == "closed_arithmetic":
                    a, b, c = seed % 4 + 1, (seed // 2) % 3 + 1, seed % 3
                    source = f"({a} + {b}) * 2 + {c} = {2 * (a + b) + c}"
                elif family == "arithmetic_witnesses":
                    offset = seed % 3 + 1
                    source = f"exists x. x + {offset} = {k + offset}"
                elif family == "implication_transport":
                    source = f"forall n m. n = m -> {k} + n = {k} + m"
                elif family == "conjunction_transport":
                    source = f"forall n m. (n = m /\\ {k} = {k}) -> ({k} = {k} /\\ m = n)"
                elif family == "disjunction_transport":
                    source = f"forall n. n = {k} -> (n = {k} \\/ n = {k + 1})"
                elif family == "universal_equalities":
                    source = f"forall n. (n + {k}) + 0 = n + {k}"
                elif family == "inductive_arithmetic":
                    source = f"forall n. (n + {k}) * 2 = n * 2 + {2 * k}"
                else:
                    source = f"forall n. exists x. (x = n + {k} /\\ x + 1 = n + {k + 1})"
                statement = validate_statement(source)
                result.append({
                    "name": f"{'dev' if start == 0 else 'transfer'}_{family}_{seed:02d}",
                    "source": source, "statement": statement,
                    "statement_sha256": hashlib.sha256(statement.encode()).hexdigest(),
                    "family": family, "generator_seed": seed,
                    "cohort": "expanded" if start == 0 else "parameter_transfer",
                })
    if len(result) != GOAL_COUNT or len({row["statement"] for row in result}) != GOAL_COUNT:
        raise ValueError("comparison generators lost their exact distinct target inventory")
    return tuple(result)


# These imports do not initialize a model framework. Keeping the declaration
# above independent of preparation data lets the teacher source exclude exact
# targets without an evaluator/curriculum construction cycle.
from training.peano_hydra import capacity, evaluation as shared
from training.peano_hydra.development import _normalize_metavariables
from training.peano_hydra.runner import HYDRA_RUNNER_VERSION, SURFACE_MACRO_V0_INELIGIBILITY
from training.peano_policy.authority import AUTHORITY_PRIMITIVE_PROFILE

ComparisonError = capacity.CapacityError
_canonical = shared._canonical
_digest = shared._digest
_require = capacity._require
_same = capacity._same
_keys = capacity._keys
_integer = capacity._integer
LOADING = "sequential-fresh-base-unload-previous-lora-unload-new-lora"
EXTRA_SOURCE_FILES = (
    "training/peano_hydra/comparison.py", "scripts/eval_peano_hydra_comparison.py",
    "training/peano_hydra/composition_scale.py",
    "scripts/prepare_peano_hydra_authority.py",
    "scripts/prepare_peano_hydra_authority_scale.py",
    "training/peano_hydra/helios_runtime.py",
    "scripts/helios_sync_project.sh",
)


def _sources() -> dict[str, str]:
    result = capacity._sources(authority_profile=AUTHORITY_PRIMITIVE_PROFILE)
    for name in EXTRA_SOURCE_FILES:
        result[name] = hashlib.sha256(shared._read_regular(
            ROOT / name, maximum=2 * 1024**2, description="comparison source"
        )).hexdigest()
    _require(len(result) <= capacity.MAX_SOURCE_FILES, "comparison source inventory exceeds its bound")
    return dict(sorted(result.items()))


def _manifest(authority: shared.MatchedEvaluationPlan) -> dict:
    adapter = authority.trained_adapter
    _require(type(adapter) is dict, "comparison requires a completed adapter from its own preparation")
    raw = shared._read_regular(Path(adapter["manifest_path"]), maximum=shared.MAX_MANIFEST_BYTES,
                               description="comparison training-origin manifest")
    _require(hashlib.sha256(raw).hexdigest() == adapter["manifest_sha256"],
             "training-origin manifest changed after authentication")
    return shared._json_object(raw, description="comparison training-origin manifest")


def _origin(authority: shared.MatchedEvaluationPlan, *, previous: bool) -> tuple[dict, Path, Path]:
    """Bind a strictly validated original training run, not an execution relabel."""
    _require(type(authority) is shared.MatchedEvaluationPlan, "origin requires its exact validated training plan")
    _require(authority.authority_profile == (None if previous else AUTHORITY_PRIMITIVE_PROFILE),
             "training origin was relabelled with a different authority profile")
    record = _manifest(authority)
    if previous:
        _require(authority.trained_adapter["manifest_sha256"] == PREVIOUS_MANIFEST_SHA256,
                 "previous adapter differs from the predeclared external manifest anchor")
    adapter, tokenizer, artifacts = shared._verify_trained_artifacts(authority)
    origin = {
        "kind": "completed-posttraining-origin",
        "schema": record["schema"], "version": record["version"], "run_id": record["run_id"],
        "model": dict(authority.model), "epoch_sha256": authority.epoch.epoch_sha256,
        "edition_identity_sha256": authority.epoch.edition_identity_sha256,
        "theorem_dag_sha256": authority.epoch.theorem_dag_sha256,
        "reviewed_definition_dag_sha256": authority.epoch.reviewed_definition_dag_sha256,
        "preparation_manifest_sha256": authority.preparation_manifest_sha256,
        "adapter_manifest_sha256": authority.trained_adapter["manifest_sha256"],
        "training_authority_profile": authority.authority_profile,
        # V1 did not emit these new fields: preserving None is intentional.
        "training_prompt_contract": record.get("prompt_contract"),
        "training_decoder_profile": record.get("decoder_profile"),
        "training_evidence": authority.trained_adapter["training_evidence"],
        "training_source_commit": record["deployment"]["source_sync"].get("git_commit"),
        "artifacts": artifacts, "research_claim_eligible": False,
    }
    origin["origin_sha256"] = _digest(origin)
    return origin, adapter, tokenizer


@dataclass(frozen=True, slots=True)
class ComparisonPlan:
    """One new execution authority with an independently validated V1 origin."""

    execution: capacity.CapacityPlan
    previous: shared.MatchedEvaluationPlan
    _previous_origin_json: str
    _sources_json: str

    @property
    def previous_origin(self) -> dict:
        return json.loads(self._previous_origin_json)

    @property
    def model(self) -> dict:
        return self.execution.model

    def cohort(self, name: str) -> capacity.CapacityPlan:
        _require(name in COHORTS, "unknown comparison cohort")
        index = COHORTS.index(name)
        # A distinct CapacityPlan-compatible view only supplies goals to the
        # shared bounded backend. It is never presented as a capacity report.
        return capacity.CapacityPlan(
            self.execution.authority,
            _canonical(comparison_goals()[32 * index:32 * (index + 1)]).decode(),
            self.execution.benchmark_sha256, self.execution.profile_sha256,
            self.execution._sources_json,
        )

    def to_dict(self) -> dict:
        execution = self.execution.to_dict()
        contract = {key: execution[key] for key in (
            "version", "epoch_sha256", "edition_identity_sha256", "environment", "model",
            "authority_profile", "prompt_contract", "decoder_profile", "profile_sha256",
        )}
        contract["tokenizer"] = self.previous_origin["artifacts"]["tokenizer"]
        contract["contract_sha256"] = _digest(contract)
        goals = comparison_goals()
        record = {
            "schema": PLAN_SCHEMA, "claim_boundary": CLAIM,
            "development_only": True, "public_correlated_exposed_data": True,
            "research_claim_eligible": False, "sealed_benchmark": False,
            "final_benchmark_expanded": False, "independent_discoveries": False,
            "historical_results_comparable_without_profile_ablation": False,
            "training_origins": {
                "previous": self.previous_origin,
                "new": {"preparation_manifest_sha256": self.execution.authority.preparation_manifest_sha256,
                        "authority_profile": AUTHORITY_PRIMITIVE_PROFILE,
                        "endpoint": "single-completed-one-epoch-final-adapter-no-checkpoint-selection"},
            },
            "execution_contract": contract,
            "primary_capacity_plan_sha256": execution["plan_sha256"],
            "primary_benchmark_manifest_sha256": self.execution.benchmark_sha256,
            "goals": list(goals), "goal_set_sha256": _digest(goals),
            "cohorts": [{"name": name, "goal_set_sha256": self.cohort(name).goal_set_sha256,
                         "matched_budget": self.cohort(name).matched_budget} for name in COHORTS],
            "roles": list(ROLES), "goal_count_per_role": GOAL_COUNT,
            "max_model_calls_per_role": GOAL_COUNT * capacity.LIMITS.max_model_calls,
            "max_model_calls_total": len(ROLES) * GOAL_COUNT * capacity.LIMITS.max_model_calls,
            "max_goal_evidence_bytes": shared.MAX_GOAL_EVIDENCE_BYTES,
            "max_cohort_evidence_bytes": shared.MAX_LANE_EVIDENCE_BYTES,
            "max_report_bytes": MAX_REPORT_BYTES,
            "offline_replay_limits": capacity.REPLAY_LIMITS.to_dict(),
            "source_coverage": capacity.SOURCE_COVERAGE,
            "source_files": json.loads(self._sources_json),
        }
        record["plan_sha256"] = _digest(record)
        return record


def build_comparison_plan(preparation_directory: Path, *, previous_preparation_directory: Path,
                          previous_adapter: Path, trained_adapter: Path | None = None,
                          repository_root: Path = ROOT) -> ComparisonPlan:
    """Authenticate each original preparation; planning needs no new weights.

    Preparation directories must retain their config-bound repository-relative
    locations. Adapter bundles may be relocated. The source checkout must carry
    the common frozen epoch (v25 for the pinned previous run); no implicit
    conversion of a V1/v25 origin into a later epoch or V2 source is supported.
    """
    previous = shared.build_matched_evaluation_plan(
        previous_preparation_directory, trained_adapter=previous_adapter,
        limits=capacity.LIMITS, seed=capacity.SEED, max_new_tokens=capacity.MAX_NEW_TOKENS,
        repository_root=repository_root,
    )
    previous_origin, _, _ = _origin(previous, previous=True)
    execution = capacity.build_capacity_plan(
        preparation_directory, trained_adapter=trained_adapter, repository_root=repository_root,
        authority_profile=AUTHORITY_PRIMITIVE_PROFILE,
    )
    _require(type(execution) is capacity.CapacityPlan
             and execution.authority_profile == AUTHORITY_PRIMITIVE_PROFILE,
             "comparison requires a separately authenticated V2/V4 preparation")
    _require(_same(previous.model, execution.model)
             and previous.epoch.epoch_sha256 == execution.epoch.epoch_sha256,
             "comparison training origins must share the exact pinned base and frozen epoch")
    _require(_same(execution.goals, comparison_goals()[:32]), "original 32-goal panel changed")
    if execution.authority.trained_adapter is not None:
        current, _, _ = _origin(execution.authority, previous=False)
        _require(_same(current["artifacts"]["tokenizer"], previous_origin["artifacts"]["tokenizer"]),
                 "comparison origins require byte-identical pinned tokenizer artifacts")
    return ComparisonPlan(execution, previous, _canonical(previous_origin).decode(), _canonical(_sources()).decode())


def _refresh(plan: ComparisonPlan) -> None:
    _require(type(plan) is ComparisonPlan, "comparison requires its own exact validated plan")
    current = plan.execution.authority.trained_adapter
    fresh = build_comparison_plan(
        plan.execution.authority.preparation_directory,
        previous_preparation_directory=plan.previous.preparation_directory,
        previous_adapter=Path(plan.previous.trained_adapter["manifest_path"]),
        trained_adapter=None if current is None else Path(current["manifest_path"]),
    )
    _require(_same(fresh.to_dict(), plan.to_dict())
             and _same(fresh.execution.authority.trained_adapter, current),
             "comparison source, preparation or adapter changed after planning")


def _origins(plan: ComparisonPlan) -> tuple[dict, dict[str, Path], Path]:
    previous, old_directory, tokenizer = _origin(plan.previous, previous=True)
    current, new_directory, _ = _origin(plan.execution.authority, previous=False)
    _require(_same(previous, plan.previous_origin), "previous training origin changed after planning")
    _require(_same(previous["artifacts"]["tokenizer"], current["artifacts"]["tokenizer"]),
             "comparison origins require byte-identical pinned tokenizer artifacts")
    base = {"kind": "pinned-pretrained-base", "model": plan.model,
            "adapter_attached": False, "training_authority_profile": None,
            "research_claim_eligible": False}
    base["origin_sha256"] = _digest(base)
    return {"base": base, "previous": previous, "new": current}, {
        "previous": old_directory, "new": new_directory,
    }, tokenizer


def _provider(plan: ComparisonPlan, role: str, runtime: dict, origins: dict) -> dict:
    origin = origins[role]
    return {
        "kind": "pinned-pretrained-base-no-peft" if role == "base" else "independently-authenticated-training-origin-lora",
        "comparison_role": role, "adapter_attached": role != "base", "base_model": plan.model,
        "training_origin_sha256": origin["origin_sha256"],
        "adapter_manifest_sha256": origin.get("adapter_manifest_sha256"),
        "adapter_artifacts_sha256": None if role == "base" else _digest(origin["artifacts"]),
        "shared_execution_contract_sha256": plan.to_dict()["execution_contract"]["contract_sha256"],
        "runtime": runtime, "research_claim_eligible": False,
    }


def _rows(lanes: dict, role: str, cohorts: tuple[str, ...]) -> list[dict]:
    return [row for name in cohorts for row in lanes[role][name]["goals"]]


def _panel_metrics(goals: tuple[dict, ...], rows: list[dict]) -> dict:
    passed = [row for row in rows if row["kernel_checked"]]
    return {
        "goal_count": len(goals), "kernel_checked_proofs": len(passed),
        "unproved_within_bounds": len(goals) - len(passed),
        "model_generate_calls": sum(row["model_generate_calls"] for row in rows),
        "successful_goal_model_generate_calls": sum(row["model_generate_calls"] for row in passed),
        "successful_tactic_decisions": sum(row["tactic_decisions"] for row in passed),
        "successful_proof_nodes": sum(row["proof_nodes"] for row in passed),
        **{field: sum(row["generation"][field] for row in rows) for field in (
            "candidate_sequences_returned", "candidate_lines_returned", "malformed_sequences_rejected",
            "authority_sequences_rejected",
        )},
        "candidate_attempts": sum(row["evidence"]["search"]["candidates_executed"] for row in rows),
        "attempt_failures": sum(d["kind"] in {"surface_error", "tactic_error", "tactic_limit",
                                              "replay_error", "kernel_rejection"} for row in rows
                                for d in row["evidence"]["search"]["diagnostics"]),
        "by_family": [{"family": family, "goals": sum(goal["family"] == family for goal in goals),
                       "kernel_checked_proofs": sum(row["kernel_checked"] for goal, row in zip(goals, rows, strict=True)
                                                    if goal["family"] == family)} for family in FAMILIES],
    }


def _metrics(lanes: dict) -> dict:
    result = {}
    all_goals = comparison_goals()
    for panel, cohorts, goals in (
        ("primary", COHORTS[:1], all_goals[:32]),
        ("parameter_transfer", COHORTS[1:], all_goals[32:]),
        ("all", COHORTS, all_goals),
    ):
        rows = {role: _rows(lanes, role, cohorts) for role in ROLES}
        metrics = {role: _panel_metrics(goals, rows[role]) for role in ROLES}
        paired = {}
        for reference in ("base", "previous"):
            pairs = list(zip(rows[reference], rows["new"], strict=True))
            paired[f"new_vs_{reference}"] = {
                "both_proved": sum(a["kernel_checked"] and b["kernel_checked"] for a, b in pairs),
                "new_only": [goal["name"] for goal, (a, b) in zip(goals, pairs, strict=True)
                             if not a["kernel_checked"] and b["kernel_checked"]],
                "reference_only": [goal["name"] for goal, (a, b) in zip(goals, pairs, strict=True)
                                   if a["kernel_checked"] and not b["kernel_checked"]],
                "neither_proved": sum(not a["kernel_checked"] and not b["kernel_checked"] for a, b in pairs),
                "kernel_checked_proof_delta": metrics["new"]["kernel_checked_proofs"] - metrics[reference]["kernel_checked_proofs"],
            }
        result[panel] = {"roles": metrics, "paired": paired}
    return result


def execute_comparison(plan: ComparisonPlan) -> dict:
    """One fresh base allocation per role, two exact adapters, no retries."""
    _refresh(plan)
    origins, adapter_directories, tokenizer_directory = _origins(plan)
    torch, transformers, peft = shared._model_runtime()
    shared._reset_seed(torch, transformers, capacity.SEED)
    tokenizer = transformers.AutoTokenizer.from_pretrained(
        str(tokenizer_directory), trust_remote_code=False, use_fast=True, local_files_only=True,
    )
    if tokenizer.pad_token_id is None:
        _require(tokenizer.eos_token_id is not None, "comparison tokenizer has no EOS/padding identity")
        tokenizer.pad_token_id = tokenizer.eos_token_id
    runtime = {"torch_version": str(torch.__version__), "transformers_version": str(transformers.__version__),
               "peft_version": str(peft.__version__), "visible_cuda_devices": 1,
               "cuda_device": torch.cuda.get_device_name(0), "dtype": "bfloat16", "attention": "sdpa",
               "local_files_only": True, "model_loading": LOADING}
    lanes = {}
    for role in ROLES:
        fresh_origins, _, _ = _origins(plan)
        _require(_same(fresh_origins, origins), "training-origin bytes changed before model loading")
        shared._reset_seed(torch, transformers, capacity.SEED)
        model = None
        try:
            model = shared._load_base_model(torch, transformers, plan.model)
            if role != "base":
                model = peft.PeftModel.from_pretrained(model, str(adapter_directories[role]), is_trainable=False)
            model.to("cuda:0")
            model.eval()
            # The core runner's internal "trained" role correctly marks BOTH
            # attached adapters. The outer role and provider bind which one.
            backend_role = "pretrained" if role == "base" else "trained"
            lanes[role] = {name: shared._run_model_lane(
                plan.cohort(name), model=model, tokenizer=tokenizer, lane=backend_role,
                provider=_provider(plan, role, runtime, origins),
            ) for name in COHORTS}
        finally:
            del model
            shared._release_gpu(torch)
    final_origins, _, _ = _origins(plan)
    _require(_same(final_origins, origins), "training-origin bytes changed during inference")
    _refresh(plan)
    result = {
        "schema": RESULT_SCHEMA, "status": "executed", "plan": plan.to_dict(),
        "training_origins": origins, "provider_runtime": runtime, "lanes": lanes,
        "metrics": _metrics(lanes), "claim_boundary": CLAIM,
        "research_claim_eligible": False, "sealed_benchmark": False,
        "final_benchmark_expanded": False, "independent_discoveries": False,
    }
    result["evaluation_sha256"] = _digest(result)
    validate_comparison_result(plan, result, replay=False, origins=origins)
    return result


def _validate_lane(plan: ComparisonPlan, role: str, cohort_name: str, lane: dict,
                   runtime: dict, origins: dict, *, replay: bool) -> list[dict]:
    """Validate the unchanged bounded runner ledger for one declared cohort."""
    cohort = plan.cohort(cohort_name)
    name = "pretrained" if role == "base" else "trained"
    limits = capacity.LIMITS
    provider = _provider(plan, role, runtime, origins)
    _keys(lane, {"status", "lane", "model", "adapter_attached", "epoch_sha256", "environment_sha256",
                 "goal_set_sha256", "matched_budget", "provider", "goals", "kernel_checked_proofs",
                 "model_generate_calls", "retained_evidence_bytes", "research_claim_eligible"}, "model cohort")
    _require(lane["status"] == "executed" and lane["lane"] == name
             and lane["adapter_attached"] is (role != "base") and lane["research_claim_eligible"] is False
             and _same(lane["model"], cohort.model) and lane["epoch_sha256"] == cohort.epoch.epoch_sha256
             and lane["environment_sha256"] == cohort.environment["environment_sha256"]
             and lane["goal_set_sha256"] == cohort.goal_set_sha256
             and _same(lane["matched_budget"], cohort.matched_budget) and _same(lane["provider"], provider),
             "model cohort changed its exact shared authority or original adapter")
    _require(type(lane["goals"]) is list and len(lane["goals"]) == 32, "model cohort goal inventory differs")
    checked = []
    calls = retained = 0
    for goal, row in zip(cohort.goals, lane["goals"], strict=True):
        _keys(row, {"goal", "status", "kernel_checked", "tactic_decisions", "proof_nodes", "commands_sha256",
                    "model_generate_calls", "generation", "policy_identity", "evidence", "evidence_sha256",
                    "research_claim_eligible"}, "model goal")
        _require(row["goal"] == goal["name"] and row["research_claim_eligible"] is False, "goal order or claim changed")
        calls += _integer(row["model_generate_calls"], "goal calls", limits.max_model_calls)
        evidence = row["evidence"]
        encoded = _canonical(evidence)
        retained += len(encoded)
        _require(len(encoded) <= shared.MAX_GOAL_EVIDENCE_BYTES
                 and hashlib.sha256(encoded).hexdigest() == row["evidence_sha256"], "goal evidence bytes differ")
        _keys(evidence, {"v", "label", "status", "proved", "theorem", "policy", "policy_identity", "environment",
                         "limits", "commands_sha256", "proposal_records", "degraded", "eligible_for_comparison",
                         "comparison_ineligibility_reasons", "degradation_reasons", "search", "replay"}, "Hydra evidence")
        _require(evidence["theorem"] == goal["statement"] and _same(evidence["environment"], cohort.environment)
                 and _same(evidence["limits"], shared._limits_record(limits)) and evidence["degraded"] is False
                 and evidence["degradation_reasons"] == []
                 and type(evidence["v"]) is int and evidence["v"] == HYDRA_RUNNER_VERSION
                 and evidence["label"] == f"hydra-alpha-eval-{name}-{goal['name']}"
                 and evidence["policy"] == f"hydra-alpha-portfolio-{name}-{goal['name']}"
                 and evidence["eligible_for_comparison"] is False
                 and evidence["comparison_ineligibility_reasons"] == [SURFACE_MACRO_V0_INELIGIBILITY],
                 "proof goal, authority, claim or resource bounds differ")
        search = evidence["search"]
        _keys(search, {"status", "theorem", "commands", "certificate_nodes", "diagnostics", "model_calls",
                       "states_expanded", "states_discovered", "candidates_executed", "frontier_peak", "depth_reached"},
              "search result")
        _require(row["status"] == evidence["status"] == search["status"] and search["theorem"] == goal["statement"]
                 and type(search["model_calls"]) is int and search["model_calls"] == row["model_generate_calls"]
                 and type(search["states_expanded"]) is int and search["states_expanded"] == row["model_generate_calls"],
                 "search status/call identity differs")
        for field, maximum, minimum in (("states_discovered", limits.max_states, 1),
                                         ("candidates_executed", limits.max_model_calls * 4, 0),
                                         ("frontier_peak", limits.beam_width, 1), ("depth_reached", limits.max_depth, 0)):
            _integer(search[field], field, maximum, minimum)
        _require(type(search["diagnostics"]) is list and len(search["diagnostics"]) <= 128,
                 "search diagnostic inventory exceeds its bound")
        for diagnostic in search["diagnostics"]:
            _keys(diagnostic, {"kind", "depth", "state_sha256", "command", "message"}, "search diagnostic")
            _integer(diagnostic["depth"], "diagnostic depth", limits.max_depth)
            _require(all(type(diagnostic[field]) is str and len(diagnostic[field].encode()) <= 4096
                         for field in ("kind", "state_sha256", "message"))
                     and (diagnostic["command"] is None or type(diagnostic["command"]) is str
                          and len(diagnostic["command"].encode()) <= 4096), "diagnostic text exceeds its bound")
        commands = search["commands"]
        _require(type(commands) is list and len(commands) <= limits.max_depth
                 and all(type(command) is str and len(command.encode()) <= 4096 for command in commands),
                 "proof commands exceed their bounds")
        expected_commands = _digest(commands) if row["status"] == "proof" else None
        _require(type(row["tactic_decisions"]) is int and row["tactic_decisions"] == len(commands)
                 and row["commands_sha256"] == evidence["commands_sha256"] == expected_commands,
                 "command digest/count differs")
        proposals = capacity._validate_proposals(cohort, goal, name, row, provider)
        if row["status"] != "proof":
            _require(row["status"] in {"limit", "exhausted"} and row["kernel_checked"] is False
                     and evidence["proved"] is False and not commands and evidence["replay"] is None
                     and row["proof_nodes"] is None and search["certificate_nodes"] is None,
                     "invalid unknown/proof claim")
            continue
        _require(row["kernel_checked"] is True and evidence["proved"] is True and commands,
                 "successful route lost its checked proof claim")
        saved = evidence["replay"]
        _require(type(saved) is dict and saved.get("kernel_checked") is True
                 and saved.get("theorem") == goal["statement"] and saved.get("status") == "proved"
                 and type(saved.get("trace")) is list and len(saved["trace"]) == len(commands) + 1,
                 "successful route lacks its original checked trace")
        _integer(row["proof_nodes"], "proof nodes", 1_000_000, 1)
        _require(type(search["certificate_nodes"]) is int and type(saved.get("proof_nodes")) is int
                 and row["proof_nodes"] == search["certificate_nodes"] == saved["proof_nodes"], "proof node count differs")
        for command, step in zip(commands, saved["trace"][:-1], strict=True):
            _require(type(step) is dict and step.get("tactic") == command and type(step.get("goals_before")) is list,
                     "saved proof trace changed its command/prestate")
            normalized = _normalize_metavariables(tuple(step["goals_before"]))
            _require(any(command in p["accepted_candidates"]
                         and _normalize_metavariables(tuple(p["goals"])) == normalized for p in proposals),
                     "successful command/prestate was not among model proposals")
        process = None
        if replay:
            fresh, process = capacity._replay_success(cohort, goal, row)
            _require(fresh.get("kernel_checked") is True and fresh.get("theorem") == goal["statement"]
                     and fresh.get("proof_nodes") == row["proof_nodes"] and _same(fresh, saved),
                     "independent original-goal kernel replay differs")
        checked.append({"role": role, "cohort": cohort_name, "goal": goal["name"],
                        "commands_sha256": row["commands_sha256"], "proof_nodes": row["proof_nodes"],
                        "replay_process": process})
    _require(type(lane["kernel_checked_proofs"]) is int and lane["kernel_checked_proofs"] == len(checked)
             and type(lane["model_generate_calls"]) is int and lane["model_generate_calls"] == calls <= 256
             and type(lane["retained_evidence_bytes"]) is int
             and lane["retained_evidence_bytes"] == retained <= shared.MAX_LANE_EVIDENCE_BYTES,
             "cohort aggregate proof/call/byte accounting differs")
    return checked


def validate_comparison_result(plan: ComparisonPlan, result: dict, *, replay: bool,
                               origins: dict | None = None) -> dict:
    """Authenticate receipts; fresh native replay validates proofs, not GPU history.

    This does not regenerate model outputs or attest historical hardware. A
    report hash published before archival review is still an external anchor.
    ``origins`` is a live-run optimization only; offline callers reauthenticate
    both closed artifact trees from their independently supplied preparations.
    """
    _require(type(plan) is ComparisonPlan and type(replay) is bool, "invalid comparison verification inputs")
    _require(not replay or "torch" not in sys.modules, "offline comparison replay must start without model frameworks")
    _require(len(_canonical(result)) <= MAX_REPORT_BYTES, "comparison result exceeds its byte bound")
    _keys(result, {"schema", "status", "plan", "training_origins", "provider_runtime", "lanes", "metrics",
                   "claim_boundary", "research_claim_eligible", "sealed_benchmark", "final_benchmark_expanded",
                   "independent_discoveries", "evaluation_sha256"}, "comparison result")
    capacity._signed(result, "evaluation_sha256")
    if origins is None or replay:
        origins, _, _ = _origins(plan)
    _require(result["schema"] == RESULT_SCHEMA and result["status"] == "executed"
             and _same(result["plan"], plan.to_dict()) and _same(result["training_origins"], origins),
             "comparison schema, exact plan or training origin differs")
    _require(result["claim_boundary"] == CLAIM and all(result[key] is False for key in (
        "research_claim_eligible", "sealed_benchmark", "final_benchmark_expanded", "independent_discoveries")),
        "comparison inflated its exposed development claim")
    runtime = result["provider_runtime"]
    _keys(runtime, {"torch_version", "transformers_version", "peft_version", "visible_cuda_devices", "cuda_device",
                    "dtype", "attention", "local_files_only", "model_loading"}, "provider runtime")
    _require(all(type(runtime[key]) is str and 1 <= len(runtime[key]) <= 256 for key in (
        "torch_version", "transformers_version", "peft_version", "cuda_device")), "runtime identity is malformed")
    _require(type(runtime["visible_cuda_devices"]) is int and runtime["visible_cuda_devices"] == 1
             and runtime["dtype"] == "bfloat16" and runtime["attention"] == "sdpa"
             and runtime["local_files_only"] is True and runtime["model_loading"] == LOADING,
             "runtime contract differs")
    _keys(result["lanes"], set(ROLES), "comparison roles")
    checked = []
    for role in ROLES:
        _keys(result["lanes"][role], set(COHORTS), "comparison cohorts")
        for name in COHORTS:
            checked.extend(_validate_lane(plan, role, name, result["lanes"][role][name], runtime, origins, replay=replay))
    _require(_same(result["metrics"], _metrics(result["lanes"])), "comparison aggregate/paired metrics differ")
    _require(not replay or "torch" not in sys.modules, "offline comparison replay imported a model framework")
    return {
        "schema": VERIFY_SCHEMA, "status": "passed", "evaluation_sha256": result["evaluation_sha256"],
        "plan_sha256": plan.to_dict()["plan_sha256"], "metrics": result["metrics"],
        "independently_replayed_proofs": checked if replay else [], "proof_replay_performed": replay,
        "model_outputs_regenerated": False, "historical_gpu_inference_attested": False,
        "cuda_initialized": False if replay else None, "research_claim_eligible": False, "claim_boundary": CLAIM,
    }


def verify_comparison(path: Path, *, preparation_directory: Path, previous_preparation_directory: Path,
                      previous_adapter: Path, trained_adapter: Path | None = None) -> dict:
    _require("torch" not in sys.modules, "offline comparison verification must start without model frameworks")
    raw = shared._read_regular(path, maximum=MAX_REPORT_BYTES, description="comparison result")
    report = shared._json_object(raw, description="comparison result")
    plan = build_comparison_plan(preparation_directory,
                                 previous_preparation_directory=previous_preparation_directory,
                                 previous_adapter=previous_adapter, trained_adapter=trained_adapter)
    result = validate_comparison_result(plan, report, replay=True)
    result["report_file_sha256"] = hashlib.sha256(raw).hexdigest()
    return result


__all__ = ["ComparisonError", "ComparisonPlan", "PREVIOUS_MANIFEST_SHA256", "comparison_goals",
           "build_comparison_plan", "execute_comparison", "validate_comparison_result", "verify_comparison"]
