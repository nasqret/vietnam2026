"""A fixed, exposed-data capacity diagnostic, separate from legacy held-outs.

The 32 public goals are correlated authored examples, not unseen tests or
independent discoveries. No admission, FINAL expansion, or training permission
is granted here. Models only propose tactics; successful routes are independently
checked against their original goals. Offline verification does not regenerate
model outputs and is not hardware attestation of historical inference.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import sys

from peano_lab.batch import MODEL_V1_COMMANDS, run_proof
from peano_lab.ui.prove import SurfaceCapabilities
from hydra_training_v5.peano_hydra import evaluation as shared
from hydra_training_v5.peano_hydra.benchmark import build_development_benchmark
from hydra_training_v5.peano_hydra.development import _normalize_metavariables
from hydra_training_v5.peano_hydra.policy import HydraCandidatePolicy, PolicyHead, ProposalRecord
from hydra_training_v5.peano_hydra.review_runtime import ProcessLimits, run_bounded, validate_process_record
from hydra_training_v5.peano_hydra.runner import HYDRA_RUNNER_VERSION, SURFACE_MACRO_V0_INELIGIBILITY
from hydra_training_v5.peano_policy.contract import prompt_environment
from hydra_training_v5.peano_policy.prompt import CapabilityIdentity
from hydra_training_v5.peano_policy.search import SearchLimits


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/eval_peano_hydra_capacity.py"
PLAN_SCHEMA = "peano-hydra-exposed-capacity-plan-v1"
RESULT_SCHEMA = "peano-hydra-exposed-capacity-results-v1"
VERIFY_SCHEMA = "peano-hydra-exposed-capacity-verification-v1"
AUTHORITY_PLAN_SCHEMA = "peano-hydra-exposed-capacity-plan-v2"
AUTHORITY_RESULT_SCHEMA = "peano-hydra-exposed-capacity-results-v2"
AUTHORITY_VERIFY_SCHEMA = "peano-hydra-exposed-capacity-verification-v2"
GOAL_COUNT = 32
FAMILY_COUNT = 8
SEEDS = (0, 1, 2, 3)
LIMITS = SearchLimits(max_depth=16, beam_width=4, candidates_per_state=4,
                      max_model_calls=8, max_states=64)
MAX_NEW_TOKENS = 64
SEED = shared.DEFAULT_SEED
MAX_REPORT_BYTES = 24 * 1024**2
REPLAY_LIMITS = ProcessLimits(wall_seconds=45, cpu_seconds=30, rss_bytes=1024**3,
                              output_bytes=shared.MAX_GOAL_EVIDENCE_BYTES)
MAX_REPLAY_REQUEST_BYTES = 96 * 1024
CLAIM = ("32 public, correlated, potentially training-exposed development goals; "
         "not unseen-model advantage, a sealed benchmark, FINAL, or independent discoveries")
SOURCE_FILES = (
    "training/peano_hydra/capacity.py", "scripts/eval_peano_hydra_capacity.py",
    "training/peano_hydra/evaluation.py", "training/peano_hydra/benchmark.py",
    "training/peano_hydra/development.py", "training/peano_hydra/epoch.py",
    "training/peano_hydra/curriculum.py", "training/peano_hydra/protocol.py",
    "training/peano_hydra/posttrain.py", "training/peano_hydra/configs/qwen3_1_7b_alpha_posttrain.toml",
    "training/peano_hydra/policy.py", "training/peano_hydra/runner.py",
    "training/peano_hydra/review_runtime.py", "scripts/hydra_bounded_exec.py",
    "training/peano_policy/generate.py", "training/peano_policy/prompt.py",
    "training/peano_policy/search.py", "training/peano_policy/state_identity.py",
    "training/peano_policy/contract.py",
    "training/peano_policy/config.py", "training/peano_policy/objective.py",
    "training/peano_policy/runtime.py", "training/peano_policy/training_evidence.py",
    "training/peano_policy/manifest.py", "training/peano_policy/data.py",
    "peano-lab/py/peano_lab/__init__.py", "peano-lab/py/peano_lab/batch.py",
    "peano-lab/py/peano_lab/ui/__init__.py", "peano-lab/py/peano_lab/ui/prove.py",
    "peano-lab/py/peano_lab/ui/panels.py", "peano-lab/py/peano_lab/library/theorems.py",
)
SOURCE_DIRECTORIES = ("peano-lab/py/peano_lab/kernel", "peano-lab/py/peano_lab/engine")
MAX_SOURCE_FILES = 128
MAX_SOURCE_DIRECTORY_ENTRIES = 256
SOURCE_COVERAGE = ("Listed evaluation/training/replay sources and bounded native kernel/engine Python inventory; "
                   "not whole-repository source attestation")
_canonical = shared._canonical
_digest = shared._digest


class CapacityError(ValueError):
    """A diagnostic lost its exact original inputs or bounded evidence."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CapacityError(message)


def _same(left: object, right: object) -> bool:
    return _canonical(left) == _canonical(right)


def _keys(value: object, fields: set[str], label: str) -> None:
    _require(type(value) is dict and set(value) == fields, f"{label} fields differ")


def _integer(value: object, label: str, maximum: int, minimum: int = 0) -> int:
    _require(type(value) is int and minimum <= value <= maximum, f"invalid {label}")
    return value


def _signed(value: dict[str, object], field: str) -> None:
    unsigned = dict(value)
    claimed = unsigned.pop(field, None)
    _require(type(claimed) is str and claimed == _digest(unsigned), f"{field} differs")


def _source_names(*, authority_profile: str | None = None) -> tuple[str, ...]:
    """Enumerate narrow native source trees without following links or loading a catalog."""
    names = set(SOURCE_FILES)
    if authority_profile is not None:
        names.update(("training/peano_policy/authority.py", "training/peano_policy/authority_runtime.py",
                      "training/peano_hydra/composition.py"))
    entries_seen = 0
    for relative in SOURCE_DIRECTORIES:
        directory = ROOT / relative
        _require(not directory.is_symlink() and directory.is_dir(), "native source root is not a regular directory")
        pending = [(directory, 0)]
        while pending:
            current, depth = pending.pop()
            with os.scandir(current) as entries:
                for entry in entries:
                    entries_seen += 1
                    _require(entries_seen <= MAX_SOURCE_DIRECTORY_ENTRIES, "native source inventory exceeds its entry bound")
                    if entry.name == "__pycache__":
                        continue
                    _require(not entry.is_symlink(), "native source inventory must not follow symlinks")
                    if entry.is_dir(follow_symlinks=False):
                        _require(depth < 4, "native source inventory exceeds its directory depth bound")
                        pending.append((Path(entry.path), depth + 1))
                    elif entry.name.endswith(".py"):
                        _require(entry.is_file(follow_symlinks=False), "native source is not a regular Python file")
                        names.add(Path(entry.path).relative_to(ROOT).as_posix())
                        _require(len(names) <= MAX_SOURCE_FILES, "capacity source inventory exceeds its file bound")
    _require(len(names) <= MAX_SOURCE_FILES, "capacity source inventory exceeds its file bound")
    return tuple(sorted(names))


def _sources(*, authority_profile: str | None = None) -> dict[str, str]:
    names = _source_names(authority_profile=authority_profile)
    result = {name: hashlib.sha256(shared._read_regular(
        ROOT / name, maximum=2 * 1024**2, description="capacity source")).hexdigest()
              for name in names}
    _require(_source_names(authority_profile=authority_profile) == names,
             "capacity source inventory changed during hashing")
    return result


def _select_goals(benchmark: dict[str, object]) -> tuple[dict[str, object], ...]:
    families = [row["id"] for row in benchmark["families"]]
    _require(len(families) == FAMILY_COUNT and len(set(families)) == FAMILY_COUNT,
             "capacity requires exactly the eight existing authored families")
    selected = []
    for family in families:
        rows = [row for row in benchmark["goals"]
                if row["cohort"] == "expanded" and row["family"] == family]
        candidates = {row["generator_seed"]: row for row in rows}
        _require(len(rows) == 8 and set(candidates) == set(range(8)), "public DEV seed inventory changed")
        for seed in SEEDS:
            row = candidates[seed]
            selected.append({name: row[name] for name in (
                "name", "source", "statement", "statement_sha256", "family",
                "generator_seed", "cohort",
            )})
    _require(len(selected) == GOAL_COUNT and len({row["name"] for row in selected}) == GOAL_COUNT,
             "capacity goal selection lost its exact count or unique names")
    return tuple(selected)


@dataclass(frozen=True, slots=True)
class CapacityPlan:
    """Distinct goal authority; the legacy plan only authenticates preparation."""

    authority: shared.MatchedEvaluationPlan
    _goals_json: str
    benchmark_sha256: str
    profile_sha256: str
    _sources_json: str

    @property
    def goals(self) -> tuple[dict[str, object], ...]:
        return tuple(json.loads(self._goals_json))

    @property
    def epoch(self):
        return self.authority.epoch

    @property
    def model(self):
        return dict(self.authority.model)

    @property
    def capabilities(self):
        return self.authority.capabilities

    @property
    def environment(self):
        return self.authority.environment

    @property
    def authority_profile(self):
        return self.authority.authority_profile

    @property
    def limits(self):
        return LIMITS

    @property
    def seed(self):
        return SEED

    @property
    def max_new_tokens(self):
        return MAX_NEW_TOKENS

    @property
    def goal_set_sha256(self):
        return _digest(self.goals)

    @property
    def matched_budget(self) -> dict[str, object]:
        return {**shared._limits_record(LIMITS), "goal_count": GOAL_COUNT,
                "max_model_calls_per_lane": GOAL_COUNT * LIMITS.max_model_calls,
                "max_new_tokens": MAX_NEW_TOKENS, "seed": SEED,
                "sampling": "deterministic batched candidate beam search"}

    def to_dict(self) -> dict[str, object]:
        # Adapter availability is deliberately not a plan input. This exact
        # goal/authority plan can be retained before any training begins.
        record = {
            "schema": PLAN_SCHEMA if self.authority_profile is None else AUTHORITY_PLAN_SCHEMA,
            "development_only": True,
            "research_claim_eligible": False, "sealed_benchmark": False,
            "final_benchmark_expanded": False, "independent_discoveries": False,
            "public_correlated_exposed_data": True, "claim_boundary": CLAIM,
            "version": self.epoch.version, "epoch_sha256": self.epoch.epoch_sha256,
            "edition_identity_sha256": self.epoch.edition_identity_sha256,
            "preparation_manifest_sha256": self.authority.preparation_manifest_sha256,
            "model": self.model, "environment": self.environment,
            "benchmark_manifest_sha256": self.benchmark_sha256,
            "profile_sha256": self.profile_sha256,
            "selection": {"cohort": "expanded", "seeds_per_family": list(SEEDS),
                          "family_count": FAMILY_COUNT, "goal_count": GOAL_COUNT},
            "goals": list(self.goals), "goal_set_sha256": self.goal_set_sha256,
            "matched_budget": self.matched_budget, "lanes": ["pretrained", "trained"],
            "max_model_calls_total": 2 * GOAL_COUNT * LIMITS.max_model_calls,
            "max_goal_evidence_bytes": shared.MAX_GOAL_EVIDENCE_BYTES,
            "max_lane_evidence_bytes": shared.MAX_LANE_EVIDENCE_BYTES,
            "offline_replay_limits": REPLAY_LIMITS.to_dict(),
            "source_coverage": SOURCE_COVERAGE,
            "source_files": json.loads(self._sources_json),
        }
        if self.authority_profile is not None:
            authority = self.authority.to_dict()
            for field in ("authority_profile", "prompt_contract", "decoder_profile"):
                record[field] = authority[field]
            record["historical_results_comparable_without_profile_ablation"] = False
        record["plan_sha256"] = _digest(record)
        return record


def build_capacity_plan(preparation_directory: Path, *, trained_adapter: Path | None = None,
                        repository_root: Path = ROOT, authority_profile: str | None = None) -> CapacityPlan:
    authority = shared.build_matched_evaluation_plan(
        preparation_directory, limits=LIMITS, seed=SEED, max_new_tokens=MAX_NEW_TOKENS,
        trained_adapter=trained_adapter, repository_root=repository_root,
        **({"authority_profile": authority_profile} if authority_profile is not None else {}),
    )
    _require(type(authority) is shared.MatchedEvaluationPlan, "capacity requires validated preparation authority")
    benchmark = build_development_benchmark(authority.epoch)
    goals = _select_goals(benchmark)
    _require(GOAL_COUNT * LIMITS.max_model_calls <= shared.MAX_MODEL_CALLS_PER_LANE,
             "capacity exceeded the existing whole-lane model-call ceiling")
    return CapacityPlan(authority, _canonical(goals).decode(), benchmark["manifest_sha256"],
                        benchmark["profile_sha256"],
                        _canonical(_sources(**({"authority_profile": authority_profile}
                                               if authority_profile is not None else {}))).decode())


def _refresh(plan: CapacityPlan) -> None:
    _require(type(plan) is CapacityPlan, "capacity execution requires its own exact plan")
    adapter = plan.authority.trained_adapter
    fresh = build_capacity_plan(plan.authority.preparation_directory,
                                trained_adapter=None if adapter is None else Path(adapter["manifest_path"]),
                                **({"authority_profile": plan.authority_profile}
                                   if plan.authority_profile is not None else {}))
    _require(_same(fresh.to_dict(), plan.to_dict()), "capacity inputs changed after planning")
    _require(_same(fresh.authority.trained_adapter, adapter), "capacity adapter changed after planning")


def _portable_adapter(plan: CapacityPlan) -> dict[str, object]:
    adapter = plan.authority.trained_adapter
    _require(type(adapter) is dict, "capacity inference/replay needs an authenticated trained adapter")
    return {key: value for key, value in adapter.items() if key != "manifest_path"}


def _policy_identity(plan: CapacityPlan, goal: dict, lane: str, provider: dict) -> dict:
    """Recreate only identity objects; no framework, weights or generation."""
    from hydra_training_v5.peano_policy.generate import (
        PeanoPolicyAdapter, PeanoPolicyCandidateAdapter, PeanoPretrainedBasePolicy,
    )
    environment_factory = prompt_environment
    if plan.authority_profile is not None:
        from hydra_training_v5.peano_policy.contract import authority_prompt_environment

        environment_factory = authority_prompt_environment
    environment = environment_factory(False, CapabilityIdentity.from_record(plan.environment["capabilities"]))
    goal_seed = int.from_bytes(hashlib.sha256(_canonical([SEED, goal["name"]])).digest()[:8], "big") & (2**63 - 1)
    kind = PeanoPretrainedBasePolicy if lane == "pretrained" else PeanoPolicyAdapter
    policy = kind(model=None, tokenizer=None, environment=environment,
                  name=f"hydra-alpha-{lane}-{goal['name']}", max_new_tokens=MAX_NEW_TOKENS,
                  do_sample=False, temperature=1.0, top_p=1.0, provenance=provider,
                  **({"authority_profile": plan.authority_profile} if plan.authority_profile is not None else {}))
    candidate = PeanoPolicyCandidateAdapter(policy, seed=goal_seed,
                                            name=f"hydra-alpha-candidate-{lane}-{goal['name']}")
    return HydraCandidatePolicy((PolicyHead(f"matched-{lane}-model", "control", 4, candidate),),
                                name=f"hydra-alpha-portfolio-{lane}-{goal['name']}").evaluation_identity


def _provider(plan: CapacityPlan, lane: str, runtime: dict, artifacts: dict) -> dict:
    return {"kind": "pinned-pretrained-base-no-peft" if lane == "pretrained" else "epoch-compatible-pinned-alpha-lora",
            "adapter_attached": lane == "trained", "base_model": plan.model,
            "trained_adapter_manifest_sha256": _portable_adapter(plan)["manifest_sha256"],
            "trained_adapter_artifacts": artifacts, "runtime": runtime, "research_claim_eligible": False}


def _metrics(plan: CapacityPlan, lanes: dict) -> dict:
    result = {}
    families = list(dict.fromkeys(goal["family"] for goal in plan.goals))
    for name in ("pretrained", "trained"):
        rows = lanes[name]["goals"]
        result[name] = {
            "goal_count": GOAL_COUNT,
            "kernel_checked_proofs": sum(row["kernel_checked"] for row in rows),
            "unproved_within_bounds": sum(not row["kernel_checked"] for row in rows),
            "model_generate_calls": sum(row["model_generate_calls"] for row in rows),
            "candidate_sequences_returned": sum(row["generation"]["candidate_sequences_returned"] for row in rows),
            "candidate_lines_returned": sum(row["generation"]["candidate_lines_returned"] for row in rows),
            "malformed_sequences_rejected": sum(row["generation"]["malformed_sequences_rejected"] for row in rows),
            "by_family": [{"family": family, "goals": len(SEEDS),
                           "kernel_checked_proofs": sum(row["kernel_checked"] for goal, row in zip(plan.goals, rows)
                                                        if goal["family"] == family)} for family in families],
        }
        if plan.authority_profile is not None:
            result[name]["authority_sequences_rejected"] = sum(
                row["generation"]["authority_sequences_rejected"] for row in rows
            )
    return result


def execute_capacity(plan: CapacityPlan) -> dict[str, object]:
    _refresh(plan)
    adapter_directory, tokenizer_directory, artifacts = shared._verify_trained_artifacts(plan.authority)
    torch, transformers, peft = shared._model_runtime()
    shared._reset_seed(torch, transformers, SEED)
    tokenizer = transformers.AutoTokenizer.from_pretrained(str(tokenizer_directory), trust_remote_code=False,
                                                           use_fast=True, local_files_only=True)
    if tokenizer.pad_token_id is None:
        _require(tokenizer.eos_token_id is not None, "capacity tokenizer lacks EOS/padding identity")
        tokenizer.pad_token_id = tokenizer.eos_token_id
    runtime = {"torch_version": str(torch.__version__), "transformers_version": str(transformers.__version__),
               "peft_version": str(peft.__version__), "visible_cuda_devices": 1,
               "cuda_device": torch.cuda.get_device_name(0), "dtype": "bfloat16", "attention": "sdpa",
               "local_files_only": True, "model_loading": "sequential-pretrained-unload-then-trained-lora"}
    lanes = {}
    for lane in ("pretrained", "trained"):
        shared._verify_trained_artifacts(plan.authority)
        shared._reset_seed(torch, transformers, SEED)
        model = None
        try:
            model = shared._load_base_model(torch, transformers, plan.model)
            if lane == "trained":
                model = peft.PeftModel.from_pretrained(model, str(adapter_directory), is_trainable=False)
            model.to("cuda:0")
            model.eval()
            # The shared backend only consumes the typed goal/budget interface.
            # Its legacy <=256-call, replay and byte guards remain unchanged.
            lanes[lane] = shared._run_model_lane(plan, model=model, tokenizer=tokenizer, lane=lane,
                                                provider=_provider(plan, lane, runtime, artifacts))
        finally:
            del model
            shared._release_gpu(torch)
    shared._verify_trained_artifacts(plan.authority)
    _refresh(plan)
    result = {"schema": RESULT_SCHEMA if plan.authority_profile is None else AUTHORITY_RESULT_SCHEMA,
              "status": "executed", "plan": plan.to_dict(),
              "trained_adapter": _portable_adapter(plan), "provider_runtime": runtime,
              "lanes": lanes, "metrics": _metrics(plan, lanes), "claim_boundary": CLAIM,
              "research_claim_eligible": False, "sealed_benchmark": False,
              "final_benchmark_expanded": False, "independent_discoveries": False}
    result["evaluation_sha256"] = _digest(result)
    _require(len(_canonical(result)) <= MAX_REPORT_BYTES, "capacity report exceeds its total retained-byte bound")
    validate_capacity_result(plan, result, artifacts=artifacts, replay=False)
    return result


def _validate_proposals(plan: CapacityPlan, goal: dict, lane: str, row: dict, provider: dict) -> list[dict]:
    evidence = row["evidence"]
    identity = _policy_identity(plan, goal, lane, provider)
    _require(_same(row["policy_identity"], identity) and _same(evidence["policy_identity"], identity),
             "capacity policy identity or provider changed")
    head = identity["heads"][0]
    records = evidence["proposal_records"]
    _require(type(records) is list and len(records) == row["model_generate_calls"], "proposal/call count differs")
    candidates = 0
    for number, record in enumerate(records, 1):
        _keys(record, {"portfolio_call", "head", "role", "head_identity_sha256", "goals", "state_sha256",
                       "quota", "requested", "outcome", "candidates", "accepted_candidates",
                       "suppressed_duplicates", "response_sha256", "error_type", "error"}, "proposal")
        _require(type(record["goals"]) is list and 1 <= len(record["goals"]) <= 64,
                 "proposal goals exceed their bound")
        _require(type(record["candidates"]) is list and len(record["candidates"]) <= 4
                 and type(record["accepted_candidates"]) is list, "proposal candidate inventory differs")
        try:
            converted = {**record, "goals": tuple(record["goals"]), "candidates": tuple(record["candidates"]),
                         "accepted_candidates": tuple(record["accepted_candidates"])}
            ProposalRecord(**converted)
        except (TypeError, ValueError) as error:
            raise CapacityError(f"invalid retained proposal: {error}") from error
        _require(record["portfolio_call"] == number and record["head"] == head["name"]
                 and record["role"] == "control" and record["head_identity_sha256"] == head["identity_sha256"]
                 and record["outcome"] == "ok" and record["quota"] == record["requested"] == 4,
                 "proposal changed its exact model head/quota")
        _require(all(type(command) is str and len(command.encode()) <= 4096 for command in record["candidates"]),
                 "retained candidate exceeds its text bound")
        unique = list(dict.fromkeys(record["candidates"]))
        _require(record["accepted_candidates"] == unique
                 and record["suppressed_duplicates"] == len(record["candidates"]) - len(unique)
                 and record["response_sha256"] == _digest(record["candidates"]), "proposal response/merge differs")
        candidates += len(record["candidates"])
    generation = row["generation"]
    fields = {"model_generate_calls", "candidate_sequences_requested", "candidate_sequences_returned",
              "candidate_lines_returned", "malformed_sequences_rejected", "one_batched_call_per_search_state"}
    if plan.authority_profile is not None:
        fields.add("authority_sequences_rejected")
    _keys(generation, fields, "generation")
    for field in generation.keys() - {"one_batched_call_per_search_state"}:
        _integer(generation[field], field, LIMITS.max_model_calls * 4)
    _require(generation["model_generate_calls"] == row["model_generate_calls"]
             and generation["candidate_sequences_requested"] == generation["candidate_sequences_returned"] == 4 * len(records)
             and generation["candidate_lines_returned"] == candidates
             and generation["malformed_sequences_rejected"] + generation.get("authority_sequences_rejected", 0)
             == 4 * len(records) - candidates
             and generation["one_batched_call_per_search_state"] is True, "generation accounting differs")
    if plan.authority_profile is not None:
        from hydra_training_v5.peano_policy.authority import validate_authority_tactic
        from hydra_training_v5.peano_policy.contract import authority_prompt_environment

        environment = authority_prompt_environment(
            False, CapabilityIdentity.from_record(plan.environment["capabilities"])
        )
        for record in records:
            for command in record["candidates"]:
                validate_authority_tactic(command, environment)
    return records


def replay_worker(request: dict) -> dict:
    """Native-only stdin worker. The parent authenticates the frozen authority."""
    _require("torch" not in sys.modules, "replay worker must not import a model framework")
    _require(len(_canonical(request)) <= MAX_REPLAY_REQUEST_BYTES, "replay request exceeds its byte bound")
    _keys(request, {"source", "statement", "commands", "id", "session", "capabilities"}, "replay request")
    declared = request["capabilities"]
    _keys(declared, {"label", "allowed_commands", "allowed_theorems"}, "replay capabilities")
    _require(type(declared["label"]) is str and 1 <= len(declared["label"]) <= 256
             and declared["allowed_commands"] == sorted(MODEL_V1_COMMANDS)
             and declared["allowed_theorems"] == [], "replay requires finite native commands and no imports")
    capabilities = SurfaceCapabilities(label=declared["label"], allowed_commands=MODEL_V1_COMMANDS,
                                       allowed_theorems=frozenset())
    commands = request["commands"]
    _require(type(commands) is list and 1 <= len(commands) <= LIMITS.max_depth
             and all(type(command) is str and len(command.encode()) <= 4096 for command in commands),
             "replay commands exceed their bounds")
    _require(all(type(request[field]) is str and 1 <= len(request[field].encode()) <= 4096
                 for field in ("source", "statement")), "replay goal text exceeds its bound")
    result = run_proof(request["source"], tuple(commands), request_id=request["id"],
                       session_id=request["session"], classical=False, on_error="stop", capabilities=capabilities,
                       trace_byte_limit=shared.MAX_GOAL_EVIDENCE_BYTES)
    _require(result.kernel_checked is True and result.theorem == request["statement"]
             and "torch" not in sys.modules, "native replay did not prove the original goal")
    return result.to_dict(include_trace=True)


def _replay_success(plan: CapacityPlan, goal: dict, row: dict) -> tuple[dict, dict]:
    saved = row["evidence"]["replay"]
    request = {"source": goal["source"], "statement": goal["statement"],
               "commands": row["evidence"]["search"]["commands"], "id": saved["id"], "session": saved["session"],
               "capabilities": plan.environment["capabilities"]}
    payload = _canonical(request)
    _require(len(payload) <= MAX_REPLAY_REQUEST_BYTES, "replay request exceeds its byte bound")
    command = (sys.executable, str(SCRIPT), "--replay-worker")
    # Only the explicitly reviewed recovery job needs central ARM libraries to
    # start its isolated Python replay worker. Historical/local callers retain
    # ordinary loader stripping, including unrelated scheduled jobs.
    libraries: tuple[str, ...] = ()
    if os.environ.get("PEANO_JOB_SCRIPT") == "slurm/peano_hydra_authority_scale_evaluate_recovery.sbatch":
        from .helios_runtime import reviewed_runtime_library_paths
        libraries = reviewed_runtime_library_paths()
    receipt = run_bounded(command, cwd=ROOT, limits=REPLAY_LIMITS, input_bytes=payload,
                          runtime_library_paths=libraries)
    validate_process_record(receipt, command=command, limits=REPLAY_LIMITS, input_bytes=payload,
                            success_codes=(0,), runtime_library_paths=libraries)
    result = shared._json_object(receipt["stdout"].encode(), description="native capacity replay")
    # Full trace remains in the original result; the fresh OS receipt retains
    # exact input/output hashes and resources without duplicating that trace.
    summary = {key: value for key, value in receipt.items() if key not in {"stdout", "stderr", "raw_output_base64"}}
    return result, summary


def validate_capacity_result(plan: CapacityPlan, result: dict[str, object], *, artifacts: dict,
                             replay: bool) -> dict[str, object]:
    """Validate exact receipt identities; optionally re-run successful kernel proofs."""
    _require(type(plan) is CapacityPlan and type(replay) is bool, "expected exact capacity validation inputs")
    _require(not replay or "torch" not in sys.modules, "offline replay must start without model frameworks")
    _require(len(_canonical(result)) <= MAX_REPORT_BYTES, "capacity result exceeds its byte bound")
    _keys(result, {"schema", "status", "plan", "trained_adapter", "provider_runtime", "lanes", "metrics",
                   "claim_boundary", "research_claim_eligible", "sealed_benchmark", "final_benchmark_expanded",
                   "independent_discoveries", "evaluation_sha256"}, "capacity result")
    _signed(result, "evaluation_sha256")
    schema = RESULT_SCHEMA if plan.authority_profile is None else AUTHORITY_RESULT_SCHEMA
    _require(result["schema"] == schema and result["status"] == "executed"
             and _same(result["plan"], plan.to_dict()) and _same(result["trained_adapter"], _portable_adapter(plan)),
             "capacity plan, schema or adapter differs")
    _require(result["claim_boundary"] == CLAIM and all(result[key] is False for key in (
        "research_claim_eligible", "sealed_benchmark", "final_benchmark_expanded", "independent_discoveries")),
        "capacity result inflated its development claim")
    runtime = result["provider_runtime"]
    _keys(runtime, {"torch_version", "transformers_version", "peft_version", "visible_cuda_devices", "cuda_device",
                    "dtype", "attention", "local_files_only", "model_loading"}, "provider runtime")
    _require(all(type(runtime[key]) is str and 1 <= len(runtime[key]) <= 256 for key in (
        "torch_version", "transformers_version", "peft_version", "cuda_device")), "runtime identity is malformed")
    _require(type(runtime["visible_cuda_devices"]) is int and runtime["visible_cuda_devices"] == 1
             and runtime["dtype"] == "bfloat16" and runtime["attention"] == "sdpa"
             and runtime["local_files_only"] is True
             and runtime["model_loading"] == "sequential-pretrained-unload-then-trained-lora", "runtime contract differs")
    _keys(result["lanes"], {"pretrained", "trained"}, "model lanes")
    checked = []
    for name in ("pretrained", "trained"):
        lane = result["lanes"][name]
        _keys(lane, {"status", "lane", "model", "adapter_attached", "epoch_sha256", "environment_sha256",
                     "goal_set_sha256", "matched_budget", "provider", "goals", "kernel_checked_proofs",
                     "model_generate_calls", "retained_evidence_bytes", "research_claim_eligible"}, "model lane")
        provider = _provider(plan, name, runtime, artifacts)
        _require(lane["status"] == "executed" and lane["lane"] == name
                 and lane["adapter_attached"] is (name == "trained") and lane["research_claim_eligible"] is False
                 and _same(lane["model"], plan.model) and lane["epoch_sha256"] == plan.epoch.epoch_sha256
                 and lane["environment_sha256"] == plan.environment["environment_sha256"]
                 and lane["goal_set_sha256"] == plan.goal_set_sha256
                 and _same(lane["matched_budget"], plan.matched_budget) and _same(lane["provider"], provider),
                 "model lane changed its matched authority")
        _require(type(lane["goals"]) is list and len(lane["goals"]) == GOAL_COUNT, "model goal inventory differs")
        proofs = calls = retained = 0
        for goal, row in zip(plan.goals, lane["goals"], strict=True):
            _keys(row, {"goal", "status", "kernel_checked", "tactic_decisions", "proof_nodes", "commands_sha256",
                        "model_generate_calls", "generation", "policy_identity", "evidence", "evidence_sha256",
                        "research_claim_eligible"}, "model goal result")
            _require(row["goal"] == goal["name"] and row["research_claim_eligible"] is False,
                     "goal order or claim changed")
            calls += _integer(row["model_generate_calls"], "goal model calls", LIMITS.max_model_calls)
            evidence = row["evidence"]
            encoded = _canonical(evidence)
            retained += len(encoded)
            _require(len(encoded) <= shared.MAX_GOAL_EVIDENCE_BYTES
                     and hashlib.sha256(encoded).hexdigest() == row["evidence_sha256"], "goal evidence bytes differ")
            _keys(evidence, {"v", "label", "status", "proved", "theorem", "policy", "policy_identity", "environment",
                             "limits", "commands_sha256", "proposal_records", "degraded", "eligible_for_comparison",
                             "comparison_ineligibility_reasons", "degradation_reasons", "search", "replay"}, "Hydra evidence")
            _require(evidence["theorem"] == goal["statement"] and _same(evidence["environment"], plan.environment)
                     and _same(evidence["limits"], shared._limits_record(LIMITS)) and evidence["degraded"] is False
                     and evidence["degradation_reasons"] == []
                     and type(evidence["v"]) is int and evidence["v"] == HYDRA_RUNNER_VERSION
                     and evidence["label"] == f"hydra-alpha-eval-{name}-{goal['name']}"
                     and evidence["policy"] == f"hydra-alpha-portfolio-{name}-{goal['name']}"
                     and evidence["eligible_for_comparison"] is False
                     and evidence["comparison_ineligibility_reasons"] == [SURFACE_MACRO_V0_INELIGIBILITY],
                     "proof goal, authority, claim or resource bounds differ")
            search = evidence["search"]
            _keys(search, {"status", "theorem", "commands", "certificate_nodes", "diagnostics", "model_calls",
                           "states_expanded", "states_discovered", "candidates_executed", "frontier_peak",
                           "depth_reached"}, "search result")
            _require(row["status"] == evidence["status"] == search["status"]
                     and search["theorem"] == goal["statement"]
                     and type(search["model_calls"]) is int and search["model_calls"] == row["model_generate_calls"],
                     "search status/call identity differs")
            _require(type(search["states_expanded"]) is int
                     and search["states_expanded"] == row["model_generate_calls"], "expanded state/call count differs")
            for field, maximum, minimum in (("states_discovered", LIMITS.max_states, 1),
                                             ("candidates_executed", LIMITS.max_model_calls * 4, 0),
                                             ("frontier_peak", LIMITS.beam_width, 1),
                                             ("depth_reached", LIMITS.max_depth, 0)):
                _integer(search[field], field, maximum, minimum)
            _require(type(search["diagnostics"]) is list and len(search["diagnostics"]) <= 128,
                     "search diagnostic inventory exceeds its bound")
            for diagnostic in search["diagnostics"]:
                _keys(diagnostic, {"kind", "depth", "state_sha256", "command", "message"}, "search diagnostic")
                _integer(diagnostic["depth"], "diagnostic depth", LIMITS.max_depth)
                _require(all(type(diagnostic[field]) is str and len(diagnostic[field].encode()) <= 4096
                             for field in ("kind", "state_sha256", "message"))
                         and (diagnostic["command"] is None or type(diagnostic["command"]) is str
                              and len(diagnostic["command"].encode()) <= 4096), "diagnostic text exceeds its bound")
            commands = search["commands"]
            _require(type(commands) is list and len(commands) <= LIMITS.max_depth
                     and all(type(command) is str and len(command.encode()) <= 4096 for command in commands),
                     "proof commands exceed their bounds")
            expected_commands = _digest(commands) if row["status"] == "proof" else None
            _require(type(row["tactic_decisions"]) is int and row["tactic_decisions"] == len(commands)
                     and row["commands_sha256"] == evidence["commands_sha256"] == expected_commands,
                     "command digest/count differs")
            proposals = _validate_proposals(plan, goal, name, row, provider)
            if row["status"] != "proof":
                _require(row["status"] in {"limit", "exhausted"} and row["kernel_checked"] is False
                         and evidence["proved"] is False and not commands and evidence["replay"] is None
                         and row["proof_nodes"] is None and search["certificate_nodes"] is None, "invalid unknown/proof claim")
                continue
            _require(row["kernel_checked"] is True and evidence["proved"] is True and commands,
                     "successful route lost its checked proof claim")
            saved = evidence["replay"]
            _require(type(saved) is dict and saved.get("kernel_checked") is True
                     and saved.get("theorem") == goal["statement"] and saved.get("status") == "proved"
                     and type(saved.get("trace")) is list and len(saved["trace"]) == len(commands) + 1,
                     "successful route lacks its original checked trace")
            _integer(row["proof_nodes"], "proof nodes", 1_000_000, 1)
            _require(type(search["certificate_nodes"]) is int
                     and row["proof_nodes"] == search["certificate_nodes"] == saved["proof_nodes"], "proof node count differs")
            for command, step in zip(commands, saved["trace"][:-1], strict=True):
                _require(type(step) is dict and step.get("tactic") == command
                         and type(step.get("goals_before")) is list,
                         "saved proof trace changed its command/prestate")
                normalized = _normalize_metavariables(tuple(step["goals_before"]))
                _require(any(command in proposal["accepted_candidates"]
                             and _normalize_metavariables(tuple(proposal["goals"])) == normalized for proposal in proposals),
                         "successful command/prestate was not among model proposals")
            replay_process = None
            if replay:
                fresh, replay_process = _replay_success(plan, goal, row)
                _require(fresh.get("kernel_checked") is True and fresh.get("theorem") == goal["statement"]
                         and fresh.get("proof_nodes") == row["proof_nodes"] and _same(fresh, saved),
                         "independent original-goal kernel replay differs")
            proofs += 1
            checked.append({"lane": name, "goal": goal["name"], "commands_sha256": row["commands_sha256"],
                            "proof_nodes": row["proof_nodes"], "replay_process": replay_process})
        _require(type(lane["kernel_checked_proofs"]) is int and lane["kernel_checked_proofs"] == proofs
                 and type(lane["model_generate_calls"]) is int and lane["model_generate_calls"] == calls <= 256
                 and type(lane["retained_evidence_bytes"]) is int
                 and lane["retained_evidence_bytes"] == retained <= shared.MAX_LANE_EVIDENCE_BYTES,
                 "lane aggregate proof/call/byte accounting differs")
    _require(_same(result["metrics"], _metrics(plan, result["lanes"])), "capacity aggregate metrics differ")
    _require(not replay or "torch" not in sys.modules, "offline replay imported a model framework")
    return {"schema": VERIFY_SCHEMA if plan.authority_profile is None else AUTHORITY_VERIFY_SCHEMA,
            "status": "passed", "evaluation_sha256": result["evaluation_sha256"],
            "plan_sha256": plan.to_dict()["plan_sha256"], "metrics": result["metrics"],
            "independently_replayed_proofs": checked if replay else [],
            "proof_replay_performed": replay, "model_outputs_regenerated": False,
            "cuda_initialized": False if replay else None, "research_claim_eligible": False, "claim_boundary": CLAIM}


def verify_capacity(path: Path, *, preparation_directory: Path, trained_adapter: Path | None = None,
                    authority_profile: str | None = None) -> dict:
    _require("torch" not in sys.modules, "offline capacity verification must start without model frameworks")
    raw = shared._read_regular(path, maximum=MAX_REPORT_BYTES, description="capacity result")
    report = shared._json_object(raw, description="capacity result")
    plan = build_capacity_plan(preparation_directory, trained_adapter=trained_adapter,
                               **({"authority_profile": authority_profile} if authority_profile is not None else {}))
    _, _, artifacts = shared._verify_trained_artifacts(plan.authority)
    result = validate_capacity_result(plan, report, artifacts=artifacts, replay=True)
    _require("torch" not in sys.modules, "offline capacity verification imported a model framework")
    result["report_file_sha256"] = hashlib.sha256(raw).hexdigest()
    return result


__all__ = ["CapacityError", "CapacityPlan", "build_capacity_plan", "execute_capacity",
           "validate_capacity_result", "verify_capacity"]
