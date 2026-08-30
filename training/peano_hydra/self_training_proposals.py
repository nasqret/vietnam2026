"""Explicit next-round TRAIN proposal search, followed by native harvesting.

Planning never loads a model or grants an allocation. Production generation
requires the actual preregistered pilot verifier, a separate external human
acceptance, and a caller-owned one-use resource reservation. Search proposals
remain untrusted: the existing self_training harvester freshly replays complete
original goals before any candidate transitions can be exported for review.
No function admits a trainer dataset, changes an old model, or starts training.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import resource
import sys
import time

from training.peano_hydra import origin_bridge as bridge
from training.peano_hydra import scaling_experiment as experiment
from training.peano_hydra import self_training as harvest


ROOT = Path(__file__).absolute().parents[2]
REQUEST_SCHEMA = "peano-hydra-self-training-proposal-request-v1"
PLAN_SCHEMA = "peano-hydra-self-training-proposal-plan-v1"
GENERATION_SCHEMA = "peano-hydra-self-training-proposal-generation-v1"
GOAL_SCHEMA = "peano-hydra-self-training-search-goal-v1"
REVIEW_SCHEMA = "peano-hydra-self-training-pilot-acceptance-v1"
AUTHORIZATION_SCHEMA = "peano-hydra-self-training-generation-authorization-v1"
FIXTURE_SCHEMA = "peano-hydra-self-training-authored-native-fixture-v1"
MAX_GOALS = harvest.MAX_GOALS
MAX_GOAL_BYTES = 512 * 1024
MAX_GENERATION_BYTES = 16 * 1024**2
MAX_WALL_SECONDS = 1800
MAX_EXCLUSIONS = 32768
SEARCH = {"max_depth": 16, "beam_width": 4, "candidates_per_state": 4, "max_states": 64}
FIXTURE_LIMITS = {"cpu_seconds": 30, "wall_seconds": 45,
                  "rss_bytes": 1024**3, "output_bytes": 1024**2}
EXTRA_SOURCES = (
    "training/peano_hydra/self_training_proposals.py", "scripts/propose_peano_hydra_self_training.py",
    "training/peano_hydra/policy.py", "training/peano_hydra/runner.py",
    "training/peano_hydra/evaluation.py", "training/peano_hydra/capacity.py",
    "training/peano_hydra/scaling_evaluation.py", "training/peano_hydra/paired_checkpoint.py",
    "training/peano_hydra/frontier_benchmark_protocol.py",
    "training/peano_hydra/frontier_benchmark_candidates.py",
    "training/peano_hydra/frontier_benchmark_audit.py",
    "training/peano_hydra/frontier_benchmark_run.py",
    "training/peano_hydra/frontier_saved_benchmark_run.py",
    "training/peano_policy/generate.py", "training/peano_policy/adapter_admission.py",
    "training/peano_policy/training_evidence.py", "training/peano_policy/pretrained_baseline.py",
)
CLAIMS = {"training_authorized": False, "dataset_admitted": False,
          "benchmark_comparison_authorized": False, "research_claim_eligible": False,
          "sealed_benchmark": False, "human_identity_attested": False,
          "automatic_retry": False, "resume": False, "parent_dataset_modified": False}
require, canonical, digest = experiment.require, experiment.canonical, experiment.digest


def _same(left, right):
    return canonical(left) == canonical(right)


def _signed(record, field):
    return {**record, field: digest(record)}


def _text(value, label, maximum=4096):
    require(type(value) is str and 0 < len(value.encode()) <= maximum
            and value == value.strip() and "\x00" not in value, label + " is not bounded text")
    return value


def _descriptor(record):
    experiment.keys(record, {"path", "sha256"}, "external raw-pinned input")
    experiment.sha(record["sha256"], "external raw input SHA")
    return bridge._absolute(Path(_text(record["path"], "input path")))


def _read(record, maximum=experiment.MAX_RECORD_BYTES):
    path = _descriptor(record)
    raw = bridge._read(path, maximum)
    require(hashlib.sha256(raw).hexdigest() == record["sha256"], "externally pinned input changed: " + path.name)
    return bridge._decode(raw, maximum, path.name)


def execution_sources():
    """Keep the parent candidate's historical inventory unchanged and separate."""
    result = experiment.execution_source_inventory()
    with bridge._Tree(ROOT) as tree:
        for name in EXTRA_SOURCES:
            item, _ = tree.fingerprint(name, maximum=2 * 1024**2)
            result[name] = {key: item[key] for key in ("bytes", "sha256")}
        tree.assert_unchanged()
    return dict(sorted(result.items()))


@lru_cache(maxsize=32768)
def _features(statement):
    from training.peano_hydra.frontier_benchmark_audit import formula_features
    return formula_features(statement)


def _goal(route):
    result = {"goal_id": route["name"], **{key: route[key] for key in (
        "source", "statement", "statement_sha256", "family", "lineage_sha256", "split")}}
    harvest._goal(result)
    from training.peano_hydra.protocol import validate_statement
    require(validate_statement(result["source"]) == result["statement"],
            "registered input formula is not its exact original canonical theorem")
    return result


def select_train_goals(routes, eligible, *, round_id, maximum):
    """Predeclared balanced round-robin; no outcomes or teacher commands used."""
    experiment.integer(maximum, "proposal goal limit", 1, MAX_GOALS)
    require(type(routes) is list and 1 <= len(routes) <= 2048 and type(eligible) is set,
            "bounded authenticated route inventory required")
    families = defaultdict(list)
    names = set()
    for route in routes:
        require(route["name"] not in names, "duplicate native route")
        names.add(route["name"])
        if route["name"] in eligible:
            require(route["split"] == "train", "declared eligibility crossed into DEV/TEST")
            families[route["family"]].append(_goal(route))
    require(eligible <= names and families, "no complete authenticated TRAIN partition")
    for goals in families.values():
        goals.sort(key=lambda row: (digest([round_id, row["statement_sha256"]]), row["goal_id"]))
    result = []
    for index in range(max(map(len, families.values()))):
        for family in sorted(families):
            if index < len(families[family]) and len(result) < maximum:
                result.append(families[family][index])
    require(len({g["statement_sha256"] for g in result}) == len(result), "selected roots are duplicated")
    return result


def _eligible(routes, proposal, checked_review):
    components = {name: component for component in proposal["components"] for name in component["route_ids"]}
    allocation = {item["component_id"]: item for item in checked_review["scope"]}
    return {row["name"] for row in routes if row["split"] == "train"
            and allocation.get(components[row["name"]]["component_id"], {}).get("split") == "train"}


def parent_exclusions(summary, proposal, eligible):
    """Match the unchanged v1 harvester's exact parent exclusion contract."""
    targets = set(proposal["inventory"]["exclusions"]["target_sha256s"])
    lineages = set()
    for route in summary["source_plan"]["routes"]:
        if route["name"] not in eligible:
            targets.add(route["statement_sha256"])
            lineages.add(route["lineage_sha256"])
    targets.update(hashlib.sha256(row["statement"].encode()).hexdigest()
                   for row in summary["source_plan"]["excluded_targets"])
    return sorted(targets), sorted(lineages)


def exclusion_inventory(routes, eligible, benchmark_bundle, native_rows, legacy_targets):
    """Retain all64 benchmark roots/templates/states and all non-TRAIN states."""
    benchmark_routes = benchmark_bundle["plan"]["routes"]
    require(len(benchmark_routes) == len(benchmark_bundle["proofs"]) == 64,
            "all64 primary and reserve candidates must remain excluded")
    reserved = [route for route in routes if route["name"] not in eligible] + benchmark_routes
    excluded = {"targets": set(legacy_targets), "families": set(), "lineages": set(),
                "names": set(), "root_skeletons": set(), "states": set()}
    for route in reserved:
        features = _features(route["statement"])
        require(features["closed"] and features["canonical_sha256"] == route["statement_sha256"],
                "reserved route lost its canonical original statement")
        excluded["targets"].add(route["statement_sha256"])
        excluded["root_skeletons"].add(features["skeleton_sha256"])
        for key, field in (("families", "family"), ("lineages", "lineage_sha256"), ("names", "name")):
            excluded[key].add(route[field])
    existing, seen_routes, row_count = set(), set(), 0
    by_name = {row["name"]: row for row in routes}
    for row in native_rows:
        row_count += 1
        require(row_count <= 16384 and row["theorem_name"] in by_name, "unbounded/unregistered parent native rows")
        route = by_name[row["theorem_name"]]
        require(row["split"] == route["split"] and row["theorem"] == route["statement"]
                and row["family"] == route["family"] and row["lineage_sha256"] == route["lineage_sha256"],
                "parent native transition changed its route/split identity")
        seen_routes.add(route["name"])
        if route["name"] in eligible:
            require(row["split"] == "train", "existing-example inventory crossed TRAIN")
            existing.add(digest([row["epoch_sha256"], row["environment_sha256"], row["lineage_sha256"],
                                 row["state_sha256"], row["action"]]))
        else:
            for key in ("goals_before", "goals_after"):
                if row[key]:
                    excluded["states"].add(digest(row[key]))
    require(seen_routes == set(by_name), "parent source omitted a declared route")
    for proof in benchmark_bundle["proofs"]:
        for row in proof["native_result"]["trace"][:-1]:
            for key in ("goals_before", "goals_after"):
                if row[key]:
                    excluded["states"].add(digest(row[key]))
    require(all(len(values) <= MAX_EXCLUSIONS for values in (*excluded.values(), existing)),
            "exclusion/existing-example inventory exceeds its bound")
    return {key: sorted(values) for key, values in excluded.items()}, sorted(existing)


class ReservedOverlap(ValueError):
    pass


class GenerationStopped(BaseException):
    """Cannot be swallowed as an ordinary untrusted policy/tactic failure."""


def validate_exclusions(exclusions):
    experiment.keys(exclusions, {"targets", "families", "lineages", "names", "root_skeletons", "states"},
                    "complete TRAIN-only exclusion inventory")
    for name, values in exclusions.items():
        require(type(values) is list and len(values) <= MAX_EXCLUSIONS
                and all(type(value) is str for value in values) and values == sorted(set(values)),
                "exclusions must be bounded sorted unique strings")
        for value in values:
            if name in {"families", "names"}:
                _text(value, "reserved name", 128)
            else:
                experiment.sha(value, "reserved " + name)
    return exclusions


def check_states(goals, exclusions):
    require(type(goals) in (list, tuple) and len(goals) <= 64
            and all(type(goal) is str and 0 < len(goal.encode()) <= 65536 for goal in goals),
            "bounded complete rendered native state required")
    if goals and digest(list(goals)) in exclusions["states"]:
        raise ReservedOverlap("reserved complete DEV/benchmark proof state")
    for goal in goals:
        _, marker, target = goal.rpartition("⊢")
        require(marker and target.strip(), "native state has no displayed target")
        target = target.strip()
        if "?" in target:  # Open metavariables still retain the whole-state check.
            continue
        features = _features(target)
        if features["closed"] and (features["canonical_sha256"] in exclusions["targets"]
                or features["skeleton_sha256"] in exclusions["root_skeletons"]):
            raise ReservedOverlap("reserved closed target or whole logical template")


def check_goal(goal, exclusions):
    harvest._goal(goal)
    if (goal["goal_id"] in exclusions["names"] or goal["family"] in exclusions["families"]
            or goal["lineage_sha256"] in exclusions["lineages"]):
        raise ReservedOverlap("reserved root/family/lineage")
    check_states(["⊢ " + goal["statement"]], exclusions)


class _GuardedPolicy:
    def __init__(self, policy, exclusions, boundary):
        self.policy, self.exclusions, self.boundary = policy, exclusions, boundary
        self.name = policy.name + "-train-only"
        self.blocked_states = 0

    @property
    def policy_environment(self):
        return self.policy.policy_environment

    @property
    def evaluation_identity(self):
        return {"name": self.name, "kind": "train-only-reserved-state-guard-v1",
                "exclusions_sha256": digest(self.exclusions), "policy": self.policy.evaluation_identity}

    def propose(self, goals_before, *, max_candidates):
        try:
            self.boundary()
        except BaseException as error:
            raise GenerationStopped("generation reservation/deadline stopped before a proposal") from error
        try:
            check_states(goals_before, self.exclusions)
        except ReservedOverlap:
            self.blocked_states += 1
            return ()  # Never expose a reserved state to the underlying model.
        return self.policy.propose(goals_before, max_candidates=max_candidates)


def search_goal(round_plan, goal, *, policy, exclusions, capabilities, max_model_calls,
                provider_kind, boundary=lambda: None):
    """Use the existing persistent-prefix/context-alpha runner and fresh replay."""
    from training.peano_hydra.runner import run_hydra
    from training.peano_hydra.policy import HydraCandidatePolicy, PolicyHead
    from training.peano_policy.search import SearchLimits
    from training.peano_policy.state_identity import CONTEXT_ALPHA_V1
    round_plan = harvest.validate_round_plan(round_plan)
    validate_exclusions(exclusions)
    require(goal in round_plan["goals"] and provider_kind in {"model-proposal", "authored-test-fixture"},
            "search needs an exact registered TRAIN goal and explicit provider kind")
    experiment.integer(max_model_calls, "proposal model-call limit", 1, 16)
    check_goal(goal, exclusions)
    guarded = _GuardedPolicy(policy, exclusions, boundary)
    portfolio = HydraCandidatePolicy((PolicyHead("train-only-model", "control", 4, guarded),),
                                    name="hydra-self-training-" + goal["goal_id"])
    result = run_hydra(goal["source"], portfolio, capabilities=capabilities,
        limits=SearchLimits(**SEARCH, max_model_calls=max_model_calls),
        search_profile=CONTEXT_ALPHA_V1, label="self-training-" + goal["goal_id"])
    require(result.theorem == goal["statement"], "search changed the independently retained original goal")
    evidence = result.to_dict(include_trace=True)
    require(len(canonical(evidence)) <= MAX_GOAL_BYTES, "search evidence exceeds its goal byte cap")
    status = "unknown-provider-failure" if result.degraded else "unproved-not-a-non-theorem-label"
    candidate = None
    if guarded.blocked_states:
        status = "quarantined-reserved-state"
    elif result.proved and not result.degraded:
        require(result.replay is not None and result.replay.kernel_checked is True
                and result.replay.theorem == goal["statement"] and not result.replay.goals
                and len(result.commands) <= SEARCH["max_depth"], "search proof lacks complete original-goal replay")
        try:
            for row in result.replay.trace[:-1]:
                check_states(row["goals_before"], exclusions)
                check_states(row["goals_after"], exclusions)
        except ReservedOverlap:
            status = "quarantined-reserved-state"
        else:
            status = "complete-proof-proposal-pending-independent-harvest"
            candidate = {"schema": harvest.CANDIDATE_SCHEMA, "round_sha256": round_plan["round_sha256"],
                "goal_id": goal["goal_id"], "commands": list(result.commands),
                "commands_sha256": digest(list(result.commands)),
                "model_origin_sha256": round_plan["model_origin_sha256"],
                "proposal_evidence_sha256": digest(evidence), "provider_kind": provider_kind}
            harvest.validate_candidate(round_plan, candidate)
    generation = getattr(policy, "generation_provenance", None)
    if provider_kind == "model-proposal":
        require(type(generation) is dict and type(generation.get("model_generate_calls")) is int
                and generation["model_generate_calls"] == result.search.model_calls - guarded.blocked_states
                and generation["candidate_sequences_requested"] == 4 * generation["model_generate_calls"],
                "physical batched model-call accounting changed")
    else:
        require(generation is None, "authored fixture may not be relabelled model output")
    return {"schema": GOAL_SCHEMA, "goal_id": goal["goal_id"], "status": status,
        "round_sha256": round_plan["round_sha256"], "model_origin_sha256": round_plan["model_origin_sha256"],
        "exclusions_sha256": digest(exclusions), "provider_kind": provider_kind,
        "search_calls": result.search.model_calls, "blocked_state_calls": guarded.blocked_states,
        "model_generate_calls": 0 if generation is None else generation["model_generate_calls"],
        "generation": generation, "candidate": candidate, "evidence": evidence,
        "evidence_sha256": digest(evidence), "negative_training_labels": [], **CLAIMS}


@dataclass(frozen=True, slots=True)
class BoundProposal:
    request_path: Path
    request_sha256: str
    _json: str
    origin: object

    def to_dict(self):
        return json.loads(self._json)

    @property
    def goals(self):
        return self.to_dict()["round"]["goals"]

    def protected_paths(self):
        request = self.to_dict()["request"]
        return (self.request_path.parent, Path(request["parent_bundle"]["path"]),
                self.origin.request.source_root, self.origin.request.adapter_manifest.parent,
                _descriptor(request["benchmark"]["manifest"]).parent,
                _descriptor(request["benchmark"]["audit"]).parent)


def _origin(record):
    from training.peano_hydra.scaling_evaluation import OriginReference
    experiment.keys(record, {"identity", "locations", "receipt"}, "completed model origin")
    request = bridge._request(record["identity"], record["locations"])
    ref = OriginReference(request, _descriptor(record["receipt"]), record["receipt"]["sha256"])
    ref.load()
    return ref


def check_request(path, expected_request_sha256):
    """Bind actual parent/lineage/model/native-exclusion bytes; no generation."""
    from training.peano_hydra import scaling_workflow as workflow, scaling_lineage as lineage
    from training.peano_hydra import frontier_benchmark_protocol as benchmark
    path = bridge._absolute(Path(path))
    request = _read({"path": str(path), "sha256": expected_request_sha256})
    experiment.keys(request, {"schema", "round_id", "parent_bundle", "lineage_review", "model_origin",
                              "benchmark", "max_goals", "max_model_calls"}, "proposal request")
    require(request["schema"] == REQUEST_SCHEMA, "unknown proposal request")
    experiment.integer(request["max_model_calls"], "proposal call limit", 1, 16)
    experiment.keys(request["parent_bundle"], {"path", "readiness_sha256"}, "parent candidate bundle")
    bundle = bridge._absolute(Path(request["parent_bundle"]["path"]))
    ready, summary = workflow._check_bundle_metadata(bundle,
        expected_readiness_sha256=request["parent_bundle"]["readiness_sha256"])
    review = _read(request["lineage_review"])
    proposal, _ = workflow.read_json(bundle / "lineage-proposal.json")
    checked_review = lineage.validate_review_record(review, proposal=proposal,
        expected_proposal_sha256=ready["lineage_proposal_sha256"],
        expected_review_sha256=review["review_sha256"], required_scope=proposal["allocations"])
    require(checked_review["decision"] == "accept", "proposal planning requires an externally accepted TRAIN allocation")
    origin = _origin(request["model_origin"])
    model = origin.load().origin
    require(model["epoch_sha256"] == summary["epoch_sha256"]
            and model["model"] == {"model_id": experiment.MODEL_ID, "revision": experiment.MODEL_REVISION}
            and model["training_authority_profile"] == "peano-authority-primitive-v1",
            "completed model origin differs from the parent epoch, base or primitive authority")
    from training.peano_hydra.scaling_admission import admission_identity
    parent_admission = admission_identity(origin.request.preparation_directory.parent / "source")
    require(parent_admission["candidate_readiness_sha256"] == request["parent_bundle"]["readiness_sha256"]
            and parent_admission["review_sha256"] == checked_review["review_sha256"],
            "completed adapter did not train on this exact reviewed parent")
    experiment.keys(request["benchmark"], {"manifest", "audit"}, "all64 benchmark reservation")
    manifest_path, audit_path = (_descriptor(request["benchmark"][key]) for key in ("manifest", "audit"))
    requirements = benchmark.benchmark_review_requirements(manifest_path,
        request["benchmark"]["manifest"]["sha256"], audit_path, request["benchmark"]["audit"]["sha256"])
    manifest = _read(request["benchmark"]["manifest"])
    with bridge._Tree(manifest_path.parent) as tree:
        raw = tree.read("bundle.json", 8 * 1024**2)
        require(hashlib.sha256(raw).hexdigest() == manifest["artifacts"]["bundle.json"]["sha256"],
                "benchmark original-goal proof bundle changed")
        benchmark_bundle = bridge._decode(raw, 8 * 1024**2, "benchmark native bundle")
        tree.assert_unchanged()
    require(summary["epoch_sha256"] == requirements["candidate_binding"]["epoch_sha256"]
            and ready["source_manifest_sha256"] in requirements["audited_file_sha256"]
            and summary["source_files"]["sft.jsonl"]["sha256"] in requirements["audited_file_sha256"],
            "benchmark audit does not bind this complete parent source/epoch")
    routes = summary["source_plan"]["routes"]
    eligible = _eligible(routes, proposal, checked_review)
    goals = select_train_goals(routes, eligible, round_id=request["round_id"], maximum=request["max_goals"])
    targets, lineages = parent_exclusions(summary, proposal, eligible)
    exclusions, existing = exclusion_inventory(routes, eligible, benchmark_bundle,
        workflow.source_rows(bundle / "source", expected_manifest_sha256=ready["source_manifest_sha256"]), targets)
    for goal in goals:
        check_goal(goal, exclusions)
    round_plan = harvest.build_round_plan(round_id=request["round_id"], parent_dataset_sha256=ready["shard_manifest_sha256"],
        lineage_proposal_sha256=ready["lineage_proposal_sha256"], epoch_sha256=summary["epoch_sha256"],
        authority_sha256=summary["authority_sha256"], model_origin_sha256=model["origin_sha256"],
        execution_sources_sha256=digest(experiment.execution_source_inventory()), goals=goals,
        excluded_statement_sha256s=targets, excluded_lineage_sha256s=lineages, max_candidates=len(goals))
    sources = execution_sources()
    record = _signed({"schema": PLAN_SCHEMA, "status": "planned-pending-pilot-acceptance-and-resource-review",
        "request_file_sha256": expected_request_sha256, "request": request, "round": round_plan,
        "origin": model, "lineage_review_sha256": checked_review["review_sha256"],
        "source_manifest_sha256": ready["source_manifest_sha256"],
        "execution_sources": sources, "execution_sources_sha256": digest(sources),
        "exclusions": exclusions, "exclusions_sha256": digest(exclusions),
        "benchmark_binding": requirements["candidate_binding"],
        "existing_train_example_sha256s": existing,
        "goal_selection": "round-id/root-SHA ordering, round-robin across authenticated TRAIN families",
        "search_profile": "context-alpha-v1", "fixed_search": SEARCH,
        "max_model_calls_per_goal": request["max_model_calls"],
        "max_model_calls_total": len(goals) * request["max_model_calls"],
        "max_new_tokens": 64, "seed": experiment.SEED, "max_wall_seconds": MAX_WALL_SECONDS,
        "max_generation_bytes": MAX_GENERATION_BYTES, "fresh_native_harvest_required": True,
        "model_generation_performed": False, "candidate_generation_authorized": False, **CLAIMS}, "plan_sha256")
    require(_read({"path": str(path), "sha256": expected_request_sha256}) == request
            and execution_sources() == sources and origin.load().origin == model, "proposal inputs changed while binding")
    return BoundProposal(path, expected_request_sha256, canonical(record).decode(), origin)


def _refresh(bound):
    require(type(bound) is BoundProposal, "production proposal work requires its checked binding")
    fresh = check_request(bound.request_path, bound.request_sha256)
    require(_same(fresh.to_dict(), bound.to_dict()), "bound proposal/model/parent/exclusions changed")
    return fresh


def check_pilot_acceptance(bound, *, pilot_request, pilot_run, pilot_verification, review):
    """Run the existing complete pilot verifier; a saved loss or assertion cannot pass."""
    from training.peano_hydra import frontier_saved_benchmark_run as pilot
    from training.peano_hydra.frontier_benchmark_run import acceptance_protocol
    plan = bound.to_dict()
    acceptance = _read(review)
    experiment.keys(acceptance, {"schema", "decision", "human_assertion", "reviewer_reference",
        "plan_sha256", "model_origin_sha256", "pilot_request_file_sha256", "pilot_run_file_sha256",
        "pilot_verification_file_sha256", "protocol_sha256", "training_authorized"}, "external pilot acceptance")
    require(acceptance["schema"] == REVIEW_SCHEMA and acceptance["decision"] == "accept"
            and acceptance["human_assertion"] is True and acceptance["training_authorized"] is False
            and acceptance["plan_sha256"] == plan["plan_sha256"]
            and acceptance["model_origin_sha256"] == plan["round"]["model_origin_sha256"]
            and acceptance["protocol_sha256"] == acceptance_protocol()["protocol_sha256"],
            "self-training needs separate exact pilot acceptance, never diagnostic loss")
    _text(acceptance["reviewer_reference"], "human reviewer reference", 512)
    for key, value in (("pilot_request", pilot_request), ("pilot_run", pilot_run), ("pilot_verification", pilot_verification)):
        require(acceptance[key + "_file_sha256"] == value["sha256"], "pilot acceptance changed an external evidence pin")
    saved = _read(pilot_verification, 16 * 1024**2)
    run = _read(pilot_run, 16 * 1024**2)
    require(_descriptor(pilot_run).name == "run.json"
            and run["candidate_adapter_manifest_sha256"] == plan["origin"]["adapter_manifest_sha256"],
            "pilot did not evaluate the exact completed adapter selected for proposals")
    checked = pilot.check_request(_descriptor(pilot_request), pilot_request["sha256"])
    # A successful pilot on some other benchmark cannot unlock a proposal
    # whose exclusion set reserves different goals. Bind raw manifests/audits
    # and their complete primary/reserve/template identity before any replay.
    pilot_record = checked.record
    expected_benchmark = plan["request"]["benchmark"]
    for field, key in (("benchmark_manifest", "manifest"), ("benchmark_audit", "audit")):
        require(pilot_record[field]["sha256"] == expected_benchmark[key]["sha256"],
                "accepted pilot benchmark raw pins differ from proposal exclusions")
    benchmark = checked.benchmark.load()
    binding = plan["benchmark_binding"]
    require(all(benchmark[key] == binding[key] for key in ("manifest_file_sha256", "manifest_sha256",
                "audit_file_sha256", "audit_sha256", "epoch_sha256", "reserved_goals_sha256", "all64_exclusions_sha256"))
            and benchmark["heldout_goals_sha256"] == binding["primary_goals_sha256"]
            and checked.candidate.load().origin["origin_sha256"] == plan["round"]["model_origin_sha256"],
            "accepted pilot changed candidate/primary/reserve/template/model identity")
    actual = pilot.verify_run(checked, _descriptor(pilot_run).parent, pilot_run["sha256"])
    stable_decision = lambda value: {key: item for key, item in value["decision"].items()
                                    if key not in {"decision_sha256", "verification_sha256"}}
    # Fresh replay resource measurements change. Compare stable proof outcomes
    # and exact report identities, never demand identical elapsed-time receipts.
    require(saved.get("schema") == actual["schema"] and saved.get("status") == actual["status"] == "passed"
            and saved.get("request_file_sha256") == actual["request_file_sha256"] == pilot_request["sha256"]
            and saved.get("run_file_sha256") == actual["run_file_sha256"] == pilot_run["sha256"]
            and _same(stable_decision(actual), stable_decision(saved))
            and set(actual["cohorts"]) == set(saved["cohorts"])
            and all(actual["cohorts"][key]["evaluation_sha256"] == saved["cohorts"][key]["evaluation_sha256"]
                    and actual["cohorts"][key]["proof_replay_performed"] is True
                    and actual["cohorts"][key]["verification_complete"] is True for key in actual["cohorts"])
            and actual["decision"]["status"] == "pilot-gate-met"
            and actual["decision"]["protocol_sha256"] == acceptance["protocol_sha256"]
            and actual["run_file_sha256"] == pilot_run["sha256"],
            "preregistered pilot is incomplete, changed, or did not meet its actual proof gate")
    return {"review_file_sha256": review["sha256"], "verification_file_sha256": pilot_verification["sha256"],
            "decision_sha256": actual["decision"]["decision_sha256"], "human_identity_attested": False}


def check_authorization(plan, authorization, *, expected_raw_sha256, pilot_review_sha256):
    """Validate an external allocation declaration; never create/consume one."""
    require(hashlib.sha256(canonical(authorization) + b"\n").hexdigest() == expected_raw_sha256,
            "generation authorization must use its exact canonical raw bytes plus newline")
    experiment.keys(authorization, {"schema", "plan_sha256", "model_origin_sha256", "pilot_review_file_sha256",
        "max_goals", "max_model_calls", "wall_seconds", "gpus", "one_use", "automatic_retry",
        "resume", "training_authorized"}, "generation resource authorization")
    require(authorization["schema"] == AUTHORIZATION_SCHEMA
            and authorization["plan_sha256"] == plan["plan_sha256"]
            and authorization["model_origin_sha256"] == plan["round"]["model_origin_sha256"]
            and authorization["pilot_review_file_sha256"] == pilot_review_sha256
            and type(authorization["max_goals"]) is int and authorization["max_goals"] == len(plan["round"]["goals"])
            and type(authorization["max_model_calls"]) is int and authorization["max_model_calls"] == plan["max_model_calls_total"]
            and type(authorization["wall_seconds"]) is int and 1 <= authorization["wall_seconds"] <= MAX_WALL_SECONDS
            and type(authorization["gpus"]) is int and authorization["gpus"] == 1
            and authorization["one_use"] is True
            and all(authorization[key] is False for key in ("automatic_retry", "resume", "training_authorized")),
            "generation reservation changed plan, model, bounds or training authority")
    return authorization


def _fresh_output(bound, output):
    from training.peano_hydra import corrective_workflow as files, scaling_workflow as workflow
    output = bridge._absolute(Path(output))
    files.guard_output(output, protected=(*workflow._protected(), *bound.protected_paths()))
    with bridge._Tree(output.parent) as parent:
        os.mkdir(output.name, 0o700, dir_fd=parent.directory())
        os.fsync(parent.directory())
        parent.assert_unchanged()
    return output


def generate(bound, *, output, pilot_inputs, authorization, authorization_sha256,
             reservation_check, stop_requested=lambda: False):
    """One explicit model generation run, owned by a separate reviewed launcher.

    The trusted callback must consume/check a one-use reservation before entry
    and enforce the scheduler/hard process bounds. It is mandatory, never an
    optional assertion inferred from a JSON file. This API does not submit jobs.
    """
    require(callable(reservation_check) and callable(stop_requested),
            "generation requires a caller-owned one-use reservation and stop gate")
    plan = _refresh(bound).to_dict()
    authorization = check_authorization(plan, authorization, expected_raw_sha256=authorization_sha256,
                                        pilot_review_sha256=pilot_inputs["review"]["sha256"])
    started = time.monotonic()
    def boundary():
        if stop_requested() or time.monotonic() - started >= authorization["wall_seconds"]:
            raise GenerationStopped("generation stopped at its existing reservation/deadline")
        try:
            reservation_check(json.loads(canonical(authorization)))
        except BaseException as error:
            raise GenerationStopped("one-use reservation is not valid") from error
    boundary()
    pilot = check_pilot_acceptance(bound, **pilot_inputs)
    boundary()
    from training.peano_hydra import scaling_workflow as workflow
    request = plan["request"]
    review = _read(request["lineage_review"])
    workflow.authenticate_harvest_parent(request["parent_bundle"]["path"],
        parent_readiness_sha256=request["parent_bundle"]["readiness_sha256"], review=review,
        review_sha256=plan["lineage_review_sha256"], round_plan=plan["round"])
    boundary()
    _refresh(bound)
    from training.peano_hydra import evaluation as shared, composition
    from training.peano_hydra.epoch import freeze_epoch
    from training.peano_policy.generate import PeanoPolicyAdapter, PeanoPolicyCandidateAdapter
    from training.peano_policy.authority import AUTHORITY_PRIMITIVE_PROFILE
    from training.peano_hydra import corrective_workflow as files
    epoch = freeze_epoch(ROOT)
    caps, environment, authority, _, _ = composition._authority(epoch, composition.COMPOSITION_PROFILE)
    require(epoch.epoch_sha256 == plan["round"]["epoch_sha256"]
            and digest(authority) == plan["round"]["authority_sha256"], "generation native authority changed")
    handle = bound.origin.load()
    require(handle.origin == plan["origin"], "model origin changed before loading")
    out = _fresh_output(bound, output)
    rows, descriptors, total_bytes, model_calls = [], [], 0, 0
    torch = model = tokenizer = base = policy = None
    try:
        boundary()
        torch, transformers, peft = shared._model_runtime()
        boundary()
        shared._reset_seed(torch, transformers, plan["seed"])
        tokenizer = transformers.AutoTokenizer.from_pretrained(str(handle.tokenizer_directory),
            trust_remote_code=False, use_fast=True, local_files_only=True)
        boundary()
        if tokenizer.pad_token_id is None:
            require(tokenizer.eos_token_id is not None, "pinned tokenizer lacks EOS/padding")
            tokenizer.pad_token_id = tokenizer.eos_token_id
        model = shared._load_base_model(torch, transformers, plan["origin"]["model"])
        boundary()
        model = peft.PeftModel.from_pretrained(model, str(handle.adapter_directory), is_trainable=False)
        boundary()
        model.to("cuda:0")
        boundary()
        model.eval()
        boundary()
        for index, goal in enumerate(plan["round"]["goals"], 1):
            boundary()
            provider = {"kind": "pinned-train-only-self-training-model-v1",
                        "origin_sha256": plan["round"]["model_origin_sha256"],
                        "plan_sha256": plan["plan_sha256"], "adapter_attached": True}
            base = PeanoPolicyAdapter(model=model, tokenizer=tokenizer, environment=environment,
                name="hydra-self-training-" + goal["goal_id"], max_new_tokens=plan["max_new_tokens"],
                do_sample=False, temperature=1.0, top_p=1.0, provenance=provider,
                authority_profile=AUTHORITY_PRIMITIVE_PROFILE)
            seed = int.from_bytes(hashlib.sha256(canonical([plan["seed"], goal["goal_id"]])).digest()[:8], "big") & (2**63 - 1)
            policy = PeanoPolicyCandidateAdapter(base, seed=seed, name="self-train-model-" + goal["goal_id"])
            row = search_goal(plan["round"], goal, policy=policy, exclusions=plan["exclusions"],
                capabilities=caps, max_model_calls=plan["max_model_calls_per_goal"],
                provider_kind="model-proposal", boundary=boundary)
            raw = canonical(row) + b"\n"
            total_bytes += len(raw)
            model_calls += row["model_generate_calls"]
            require(total_bytes <= MAX_GENERATION_BYTES and model_calls <= plan["max_model_calls_total"],
                    "complete generation exceeded its evidence/call bound")
            filename = f"{index:04d}.goal.json"
            files.write_new(out / filename, raw, raw=True)
            # Bind the actual published compact bytes, including their newline.
            observed = bridge._read(out / filename, MAX_GOAL_BYTES + 128 * 1024)
            descriptors.append({"path": filename, "sha256": hashlib.sha256(observed).hexdigest(), "bytes": len(observed)})
            rows.append(row)
        boundary()
        _refresh(bound)
        manifest = _signed({"schema": GENERATION_SCHEMA, "status": "complete-pending-independent-native-harvest",
            "plan_sha256": plan["plan_sha256"], "round_sha256": plan["round"]["round_sha256"],
            "model_origin_sha256": plan["round"]["model_origin_sha256"],
            "exclusions_sha256": plan["exclusions_sha256"], "pilot_acceptance": pilot,
            "authorization_file_sha256": authorization_sha256, "goal_files": descriptors,
            "candidate_count": sum(row["candidate"] is not None for row in rows),
            "model_generate_calls": model_calls, "elapsed_wall_seconds": time.monotonic() - started,
            "model_generation_performed": True, "model_generation_identity_attested": False,
            "positive_training_rows": 0, **CLAIMS}, "generation_sha256")
        files.write_new(out / "generation.json", manifest)
        return manifest
    except BaseException as error:
        files.write_new(out / "generation-failure.json", {"schema": GENERATION_SCHEMA,
            "status": "unknown-incomplete-prefix-retained", "plan_sha256": plan["plan_sha256"],
            "completed_goal_files": descriptors,
            "model_generate_calls_completed_goals": sum(row["model_generate_calls"] for row in rows),
            "latest_policy_generation": getattr(policy, "generation_provenance", None),
            "inflight_calls_may_have_occurred": model is not None,
            "error_type": type(error).__name__, "error": " ".join(str(error).split())[:2048],
            "positive_training_rows": 0, **CLAIMS})
        raise
    finally:
        base = policy = model = tokenizer = None
        if torch is not None:
            shared._release_gpu(torch)


def check_search_envelope(row, plan):
    """The saved generator cannot expand the older harvester's 24-line cap."""
    from training.peano_policy.state_identity import search_profile_contract
    evidence, search = row["evidence"], row["evidence"]["search"]
    expected = {**plan["fixed_search"], "max_model_calls": plan["max_model_calls_per_goal"]}
    require(_same(evidence["limits"], expected)
            and evidence["search_profile"] == search_profile_contract("context-alpha-v1"),
            "saved proposal changed the fixed search limits/profile")
    experiment.integer(search["model_calls"], "saved native search calls", 0, expected["max_model_calls"])
    experiment.integer(search["depth_reached"], "saved native search depth", 0, expected["max_depth"])
    require(search["model_calls"] == row["search_calls"], "saved native search-call counter differs")
    commands = search["commands"]
    require(type(commands) is list and len(commands) <= expected["max_depth"],
            "saved proposal route exceeds the planned search depth")
    if row["candidate"] is not None:
        require(1 <= len(row["candidate"]["commands"]) <= expected["max_depth"]
                and commands == row["candidate"]["commands"],
                "candidate exceeds or differs from the declared search envelope")


def harvest_generation(bound, directory, expected_generation_sha256, *, pilot_inputs):
    """Fresh native admission of proposal material; never a trainer dataset."""
    from training.peano_hydra import scaling_workflow as workflow
    plan = _refresh(bound).to_dict()
    pilot_acceptance = check_pilot_acceptance(bound, **pilot_inputs)
    directory = bridge._absolute(Path(directory))
    candidates, source_rows = [], []
    with bridge._Tree(directory) as tree:
        raw = tree.read("generation.json", experiment.MAX_RECORD_BYTES)
        require(hashlib.sha256(raw).hexdigest() == expected_generation_sha256, "external generation manifest pin changed")
        generated = bridge._decode(raw, experiment.MAX_RECORD_BYTES, "completed proposal generation")
        require(generated.get("schema") == GENERATION_SCHEMA
                and generated.get("status") == "complete-pending-independent-native-harvest"
                and generated.get("plan_sha256") == plan["plan_sha256"]
                and generated.get("round_sha256") == plan["round"]["round_sha256"]
                and generated.get("model_origin_sha256") == plan["round"]["model_origin_sha256"]
                and generated.get("exclusions_sha256") == plan["exclusions_sha256"]
                and generated.get("generation_sha256") == digest({k: v for k, v in generated.items() if k != "generation_sha256"})
                and generated.get("model_generation_performed") is True
                and generated.get("pilot_acceptance", {}).get("review_file_sha256") == pilot_acceptance["review_file_sha256"]
                and generated.get("pilot_acceptance", {}).get("verification_file_sha256") == pilot_acceptance["verification_file_sha256"]
                and all(generated.get(k) is value for k, value in CLAIMS.items()),
                "proposal generation changed plan, completion, origin, exclusions or scope")
        require(type(generated["goal_files"]) is list and len(generated["goal_files"]) == len(plan["round"]["goals"]),
                "partial proposal generations cannot be harvested")
        total = 0
        calls = 0
        for index, (goal, descriptor) in enumerate(zip(plan["round"]["goals"], generated["goal_files"], strict=True), 1):
            experiment.keys(descriptor, {"path", "bytes", "sha256"}, "proposal goal descriptor")
            require(descriptor["path"] == f"{index:04d}.goal.json", "generation changed the deterministic goal order")
            observed, raw = tree.fingerprint(descriptor["path"], maximum=MAX_GOAL_BYTES + 128 * 1024, retain=True)
            require({k: observed[k] for k in ("bytes", "sha256")} == {k: descriptor[k] for k in ("bytes", "sha256")},
                    "actual proposal goal bytes changed")
            total += len(raw)
            require(total <= MAX_GENERATION_BYTES, "proposal evidence exceeds total bound")
            row = bridge._decode(raw, MAX_GOAL_BYTES + 128 * 1024, "proposal goal")
            from training.peano_policy.state_identity import search_profile_contract
            require(row["schema"] == GOAL_SCHEMA and row["goal_id"] == goal["goal_id"]
                    and row["provider_kind"] == "model-proposal" and row["negative_training_labels"] == []
                    and row["exclusions_sha256"] == plan["exclusions_sha256"]
                    and row["round_sha256"] == plan["round"]["round_sha256"]
                    and row["model_origin_sha256"] == plan["round"]["model_origin_sha256"]
                    and row["evidence_sha256"] == digest(row["evidence"])
                    and row["evidence"]["theorem"] == goal["statement"]
                    and row["evidence"]["search_profile"] == search_profile_contract("context-alpha-v1")
                    and all(row.get(key) is value for key, value in CLAIMS.items()), "proposal row identity changed")
            experiment.integer(row["model_generate_calls"], "saved proposal calls", 0, plan["max_model_calls_per_goal"])
            experiment.integer(row["search_calls"], "saved search calls", 0, plan["max_model_calls_per_goal"])
            experiment.integer(row["blocked_state_calls"], "saved blocked calls", 0, row["search_calls"])
            require(row["search_calls"] == row["model_generate_calls"] + row["blocked_state_calls"]
                    and row["generation"]["model_generate_calls"] == row["model_generate_calls"]
                    and row["generation"]["candidate_sequences_requested"] == 4 * row["model_generate_calls"]
                    and row["status"] in {"unknown-provider-failure", "unproved-not-a-non-theorem-label",
                        "quarantined-reserved-state", "complete-proof-proposal-pending-independent-harvest"},
                    "saved proposal model/search accounting or status differs")
            check_search_envelope(row, plan)
            calls += row["model_generate_calls"]
            if row["candidate"] is not None:
                candidate = row["candidate"]
                require(row["status"] == "complete-proof-proposal-pending-independent-harvest"
                        and candidate["provider_kind"] == "model-proposal"
                        and candidate["proposal_evidence_sha256"] == row["evidence_sha256"]
                        and candidate["goal_id"] == goal["goal_id"]
                        and row["evidence"]["degraded"] is False
                        and row["evidence"]["search"]["commands"] == candidate["commands"],
                        "only complete exact original-goal proposals may be harvested")
                harvest.validate_candidate(plan["round"], candidate)
                candidates.append(candidate)
            source_rows.append(row)
        require(type(generated["candidate_count"]) is int and generated["candidate_count"] == len(candidates)
                and type(generated["model_generate_calls"]) is int
                and generated["model_generate_calls"] == calls <= plan["max_model_calls_total"],
                "proposal candidate/call accounting differs")
        request = plan["request"]
        review = _read(request["lineage_review"])
        # Reuse the original native worker unchanged. The small wrapper checks
        # the COMPLETE fresh trace against added reservations before dedup;
        # otherwise a removed old example could hide an excluded proof step.
        result = _replay_proposals(plan, candidates, parent_bundle=request["parent_bundle"]["path"],
            parent_readiness_sha256=request["parent_bundle"]["readiness_sha256"],
            review=review, review_sha256=plan["lineage_review_sha256"])
        tree.assert_unchanged()
    _refresh(bound)
    return _signed({"schema": "peano-hydra-self-training-proposal-native-harvest-v1",
        "status": "verified-material-pending-new-lineage-and-data-admission",
        "plan_sha256": plan["plan_sha256"], "generation_file_sha256": expected_generation_sha256,
        "native_harvest_sha256": result["harvest_sha256"], "outcomes": result["outcomes"],
        "quarantined_complete_candidate_sha256s": [item["candidate_sha256"] for item in result["outcomes"]
                                                    if item["status"] == "quarantined-extra-reservation"],
        "accepted_transitions": result["accepted_transitions"], "accepted_transition_count": len(result["accepted_transitions"]),
        "existing_parent_examples_excluded": len(plan["existing_train_example_sha256s"]),
        "benchmark_candidates_reserved": 64, "dev_preserved": True,
        "model_generation_performed_by_this_check": False, "negative_training_labels": [], **CLAIMS}, "harvest_sha256")


def replay_worker(request):
    """Add exclusions around, never replace, the original guarded native worker."""
    experiment.keys(request, {"native", "exclusions", "execution_sources_sha256"}, "extended native proposal request")
    exclusions = validate_exclusions(request["exclusions"])
    require(digest(execution_sources()) == request["execution_sources_sha256"],
            "proposal replay wrapper source changed")
    check_goal(request["native"]["goal"], exclusions)
    result = harvest.native_replay_worker(request["native"])
    if result["status"] == "verified-training-candidate":
        try:
            for row in result["positive_transitions"]:
                check_states(row["goals_before"], exclusions)
                check_states(row["goals_after"], exclusions)
        except ReservedOverlap:
            result = {**result, "status": "quarantined-extra-reservation", "positive_transitions": [],
                      "proof_nodes": None, "error": "complete freshly replayed proof intersects DEV/benchmark reservation"}
    require(digest(execution_sources()) == request["execution_sources_sha256"], "proposal replay wrapper changed during proof")
    return {**result, "complete_extra_reservations_checked": True,
            "extra_exclusions_sha256": digest(exclusions)}


def _replay_proposals(plan, candidates, *, parent_bundle, parent_readiness_sha256, review, review_sha256):
    """Sequential original workers, full-trace exclusions, then deduplication."""
    from training.peano_hydra import scaling_workflow as workflow, corrective_workflow as files
    from training.peano_hydra.review_runtime import ProcessLimits, run_bounded, validate_process_record
    round_plan = harvest.validate_round_plan(plan["round"])
    require(type(candidates) is list and len(candidates) <= round_plan["max_candidates"], "proposal batch exceeds round")
    validate_exclusions(plan["exclusions"])
    requests = [{"native": harvest._worker_request(round_plan, candidate), "exclusions": plan["exclusions"],
                 "execution_sources_sha256": plan["execution_sources_sha256"]} for candidate in candidates]
    workflow.authenticate_harvest_parent(parent_bundle, parent_readiness_sha256=parent_readiness_sha256,
        review=review, review_sha256=review_sha256, round_plan=round_plan)
    require(digest(execution_sources()) == plan["execution_sources_sha256"], "proposal execution source changed before harvesting")
    limits = ProcessLimits(**harvest.WORKER_LIMITS)
    command = (sys.executable, "-I", "-B", "-X", "pycache_prefix=/dev/null",
               str(ROOT / "scripts/propose_peano_hydra_self_training.py"), "--replay-worker")
    known = set(plan["existing_train_example_sha256s"])
    require(len(known) <= MAX_EXCLUSIONS, "existing TRAIN example inventory exceeds bound")
    for value in known:
        experiment.sha(value, "existing TRAIN example SHA")
    seen, outcomes, accepted, accepted_bytes = set(), [], [], 0
    for candidate, request in zip(candidates, requests, strict=True):
        candidate_sha = digest(candidate)
        key = (candidate["goal_id"], candidate["commands_sha256"])
        if key in seen:
            outcomes.append({"candidate_sha256": candidate_sha, "status": "duplicate-proof", "worker_started": False})
            continue
        seen.add(key)
        payload = canonical(request)
        process = run_bounded(command, cwd=ROOT, limits=limits, input_bytes=payload,
                              runtime_library_paths=files.runtime_libraries())
        receipt = {key: value for key, value in process.items() if key not in {"stdout", "stderr", "raw_output_base64"}}
        receipt["stderr_excerpt"] = process.get("stderr", "")[:4096]
        require(digest(execution_sources()) == plan["execution_sources_sha256"], "proposal execution source drifted during harvesting")
        if process["reason"] != "exited" or process["returncode"] != 0:
            outcomes.append({"candidate_sha256": candidate_sha, "status": "unknown-worker-failure",
                             "worker_started": True, "process": receipt})
            continue
        validate_process_record(process, command=command, limits=limits, input_bytes=payload, success_codes=(0,))
        result = bridge._decode(process["stdout"].encode(), harvest.WORKER_LIMITS["output_bytes"], "fresh proposal replay")
        native_request = request["native"]
        require(result["schema"] == harvest.WORKER_SCHEMA
                and all(result[key] == native_request[key] for key in ("round_sha256", "candidate_sha256", "epoch_sha256", "authority_sha256"))
                and result["goal_id"] == candidate["goal_id"] and result["commands_sha256"] == candidate["commands_sha256"]
                and result["model_generation_performed"] is False and result["training_authorized"] is False
                and result["complete_extra_reservations_checked"] is True
                and result["extra_exclusions_sha256"] == plan["exclusions_sha256"], "native proposal replay changed request/exclusions")
        status, rows = result["status"], result["positive_transitions"]
        require(status in {"verified-training-candidate", "quarantined-extra-reservation", "rejected-authority",
            "rejected-candidate-not-a-non-theorem-label", "quarantined-intermediate-overlap"}
            and type(rows) is list and len(rows) <= harvest.MAX_COMMANDS, "invalid native proposal outcome")
        if status == "verified-training-candidate":
            require(result["native_replay_performed"] is True and len(rows) == len(candidate["commands"])
                    and type(result["proof_nodes"]) is int and result["proof_nodes"] > 0, "proposal lacks a fresh complete proof")
        else:
            require(rows == [] and result["proof_nodes"] is None, "unproved/quarantined proposal supplied positives")
        harvest._checked_transitions(rows, native_request, candidate)
        additions, keys = [], set()
        for row in rows:
            require(row["split"] == "train" and row["epoch_sha256"] == round_plan["epoch_sha256"]
                    and row["lineage_sha256"] == native_request["goal"]["lineage_sha256"]
                    and row["theorem"] == native_request["goal"]["statement"]
                    and row["theorem_name"] == candidate["goal_id"] and row["kernel_checked"] is True
                    and row["commands_sha256"] == candidate["commands_sha256"], "positive proposal changed its original TRAIN theorem")
            check_states(row["goals_before"], plan["exclusions"])
            check_states(row["goals_after"], plan["exclusions"])
            identity = digest([row["epoch_sha256"], row["environment_sha256"], row["lineage_sha256"], row["state_sha256"], row["action"]])
            if identity not in known and identity not in keys:
                keys.add(identity)
                additions.append({"example_sha256": identity, "candidate_sha256": candidate_sha,
                    "proposal_evidence_sha256": candidate["proposal_evidence_sha256"],
                    "provider_kind": candidate["provider_kind"], "transition": row})
        size = len(canonical(additions))
        if accepted_bytes + size > harvest.MAX_ACCEPTED_BYTES:
            status, additions, keys = "verified-but-output-budget", [], set()
        else:
            accepted_bytes += size
            accepted.extend(additions)
            known.update(keys)
        outcomes.append({"candidate_sha256": candidate_sha, "status": status, "worker_started": True,
            "retained_transitions": len(additions), "native_result_sha256": digest(result), "process": receipt})
    return _signed({"schema": "peano-hydra-complete-exclusion-proposal-harvest-v1", "outcomes": outcomes,
        "accepted_transitions": accepted, "accepted_transition_count": len(accepted),
        "all_extra_exclusions_checked_before_deduplication": True, **CLAIMS}, "harvest_sha256")


def fixture_worker(request):
    """Tiny genuine native search/replay fixture, never a model or data source."""
    require(sys.flags.isolated and sys.dont_write_bytecode and sys.pycache_prefix == "/dev/null"
            and resource.getrlimit(resource.RLIMIT_CPU) == (30, 31), "fixture needs its exact isolated native guard")
    experiment.keys(request, {"schema", "source", "commands", "exclusions", "max_model_calls"}, "authored fixture")
    require(request["schema"] == FIXTURE_SCHEMA and type(request["commands"]) is list
            and 1 <= len(request["commands"]) <= 16, "authored fixture exceeds tiny route bound")
    from peano_lab.batch import run_proof
    from training.peano_hydra import composition
    from training.peano_hydra.epoch import freeze_epoch
    from training.peano_hydra.policy import ScriptCandidatePolicy
    from training.peano_hydra.runner import policy_environment
    from training.peano_hydra.protocol import validate_statement
    epoch = freeze_epoch(ROOT)
    caps, _, authority, _, _ = composition._authority(epoch, composition.COMPOSITION_PROFILE)
    statement = validate_statement(request["source"])
    goal = {"goal_id": "authored_native_fixture", "source": request["source"], "statement": statement,
        "statement_sha256": hashlib.sha256(statement.encode()).hexdigest(), "family": "authored_native_fixture",
        "lineage_sha256": digest(["authored-native-fixture", statement]), "split": "train"}
    plan = harvest.build_round_plan(round_id="authored-native-fixture", parent_dataset_sha256="1" * 64,
        lineage_proposal_sha256="2" * 64, epoch_sha256=epoch.epoch_sha256, authority_sha256=digest(authority),
        model_origin_sha256=digest({"kind": "authored-test-fixture-no-model"}),
        execution_sources_sha256=digest(experiment.execution_source_inventory()), goals=[goal],
        excluded_statement_sha256s=[], excluded_lineage_sha256s=[], max_candidates=1)
    original = run_proof(request["source"], tuple(request["commands"]), capabilities=caps,
        classical=False, on_error="stop", trace_byte_limit=128 * 1024)
    policy = ScriptCandidatePolicy.from_batch_result(original, name="authored-fixture", policy_environment=policy_environment(caps),
                                                    allow_partial=True)
    row = search_goal(plan, goal, policy=policy, exclusions=request["exclusions"], capabilities=caps,
        max_model_calls=request["max_model_calls"], provider_kind="authored-test-fixture")
    native = None
    if row["candidate"] is not None:
        # Even fixtures cross the original registered-goal native worker; the
        # fixture result is kept separate from all production harvest schemas.
        native = harvest.native_replay_worker(harvest._worker_request(plan, row["candidate"]))
    require(not {"torch", "transformers", "peft", "tokenizers"} & set(sys.modules), "fixture imported model frameworks")
    return {"schema": FIXTURE_SCHEMA, "round": plan, "search": row, "independent_native_replay": native,
            "model_calls": 0, "production_train_membership_authenticated": False,
            "positive_training_rows": 0, **CLAIMS}
