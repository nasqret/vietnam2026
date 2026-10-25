"""Synthetic origin/model/replay stubs; no corpus, native proof or model calls.

Real bounded file, plan, authority, proposal, row, checkpoint and result
validators run. Origin-authentication and fresh-proof execution are explicitly
mocked; positive counters below are NOT an actual evaluation/proof receipt.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from training.peano_hydra import scaling_evaluation as ev
from training.peano_hydra.policy import state_sha256


def raw(value): return ev._canonical(value) + b"\n"
def sha(value): return hashlib.sha256(value if type(value) is bytes else value.encode()).hexdigest()
def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value if type(value) is bytes else raw(value))
    return sha(path.read_bytes())
def file_record(value): return {"bytes": len(value), "sha256": sha(value)}
def signed(value, field="plan_sha256"):
    value[field] = ev._digest({key: item for key, item in value.items() if key != field})
    return value


@pytest.fixture
def context(tmp_path, monkeypatch, request):
    count = getattr(request, "param", 2)
    root = tmp_path.resolve()
    old_root, new_root = root / "old-source", root / "candidate-source"
    old_models, new_models = root / "old-model", root / "candidate-model"
    for path in (old_root, new_root, old_models, new_models): path.mkdir()
    caps = ev.SurfaceCapabilities(label="hydra-native-no-imports-v1", allowed_commands=ev.MODEL_V1_COMMANDS,
                                   allowed_theorems=frozenset())
    identity = ev.CapabilityIdentity(caps.label, tuple(sorted(caps.allowed_commands)), ())
    environment = ev.authority_prompt_environment(False, identity)
    authority = {"capabilities": identity.to_record(), "environment_sha256": environment.sha256, "classical": False}
    epoch = sha("synthetic candidate epoch")
    lineage = sha("synthetic lineage proposal")
    source_files = {"synthetic-core.py": {"bytes": 1, "sha256": sha("core")}}
    goals = [{"name": f"synthetic_dev_{i:02d}", "source": f"{i} = {i}", "statement": f"{i} = {i}",
              "statement_sha256": sha(f"{i} = {i}"), "lineage_sha256": sha(f"dev-lineage-{i}")} for i in range(count)]
    source_manifest = {"schema": ev.admission.SOURCE_SCHEMA,
        "composition": {"plan": {"routes": [{**goal, "split": "dev"} for goal in goals]}}}
    source_path = new_root / "_deploy/candidate/source"
    source_sha = save(source_path / "manifest.json", source_manifest)
    baseline_adapter_sha = save(old_models / "manifest.json", {"synthetic": "old completed adapter, not real weights"})
    counts = {"train": 1, "dev": count, "quarantine": 0, "test": 0}
    pilot = ev.experiment.build_pilot_plan(run_id="frontier-smoke-v1", profile="smoke",
        source_manifest_sha256=source_sha, shard_manifest_sha256=sha("synthetic shards"),
        lineage_proposal_sha256=lineage, epoch_sha256=epoch, authority_sha256=ev._digest(authority),
        baseline_adapter_manifest_sha256=baseline_adapter_sha,
        split_rows={key: counts[key] for key in ("train", "dev", "quarantine")})
    proposal = ev.experiment.build_evaluation_plan(goals=goals, cohort="review-candidate-dev", epoch_sha256=epoch,
        authority_sha256=ev._digest(authority), lineage_proposal_sha256=lineage,
        baseline_adapter_manifest_sha256=baseline_adapter_sha, candidate_training_plan_sha256=pilot["plan_sha256"],
        source_files_sha256=ev._digest(source_files))
    evaluation = root / "preregistered/evaluation-plan.json"
    evaluation_sha = save(evaluation, proposal)
    ready = {"profile": "smoke", "shard_manifest_sha256": pilot["shard_manifest_sha256"], "source_files": source_files,
        "split_rows": counts, "files": {"evaluation-plan.json": file_record(raw(proposal)), "pilot-plan.json": file_record(raw(pilot))}}
    sidecars = {name: raw({"synthetic_not_native_evidence": name}) for name in ev.admission.METADATA_FILES}
    sidecars["candidate-readiness.json"] = raw(ready)
    sidecars["training-admission.json"] = raw({"synthetic": "externally authenticated admission stub"})
    for name, value in sidecars.items(): save(source_path.parent / name, value)
    admission = {"schema": ev.admission.IDENTITY_SCHEMA, "admission_file_sha256": sha(sidecars["training-admission.json"]),
        "admission_sha256": sha("synthetic-admission"), "candidate_readiness_sha256": sha(sidecars["candidate-readiness.json"]),
        "proposal_sha256": lineage, "review_sha256": sha("synthetic accepted assertion"), "source_manifest_sha256": source_sha,
        "scope_sha256": sha("synthetic scope"), "counts": {},
        "bindings": {"epoch_sha256": epoch, "authority_sha256": ev._digest(authority),
                     "execution_source_files_sha256": ev._digest(source_files)},
        "model_training_authorized": False, "gpu_execution_authorized": False}
    curriculum = {"source_schema": ev.admission.SOURCE_SCHEMA, "review_admission": admission,
                  "projection_policy": ev.admission.PROJECTION_POLICY}
    prepared = {"source": {"directory": source_path.relative_to(new_root).as_posix(), "manifest_sha256": source_sha},
        "epoch_sha256": epoch, "authority": authority, "curriculum_identity": curriculum,
        "splits": {"train": {"lineages": [sha("train")]}, "dev": {"theorems": [g["name"] for g in goals]}}}
    prepared_path = new_root / "_deploy/candidate/preparation/manifest.json"
    prepared_sha = save(prepared_path, prepared)
    candidate_adapter_sha = save(new_models / "manifest.json", {"curriculum_identity": curriculum,
                                                                "synthetic": "new adapter, not real weights"})
    old_prep = old_root / "_deploy/original/preparation/manifest.json"
    old_prep_sha = save(old_prep, {"synthetic": "original reviewed preparation"})
    origins, references, expected_weights, load_calls = {}, {}, {}, []
    for role, src, models, prep, prep_sha, adapter_sha, version in (
        (ev.ROLES[0], old_root, old_models, old_prep, old_prep_sha, baseline_adapter_sha, "v25"),
        (ev.ROLES[1], new_root, new_models, prepared_path, prepared_sha, candidate_adapter_sha, "v28")):
        request_source = save(src / "source-manifest.json", {"synthetic": version})
        receipt = root / (role + "-origin") / "origin-receipt.json"
        receipt_sha = save(receipt, {"synthetic": "mocked origin authentication " + role})
        origin_request = ev.bridge.OriginRequest(src, src / "source-manifest.json", request_source, "a" * 40,
            prep.parent, prep_sha, models / "manifest.json", adapter_sha, ev.AUTHORITY_PRIMITIVE_PROFILE)
        references[role] = ev.OriginReference(origin_request, receipt, receipt_sha)
        origin = {"schema": "synthetic-completed-origin", "version": version,
            "model": {"model_id": ev.experiment.MODEL_ID, "revision": ev.experiment.MODEL_REVISION},
            "epoch_sha256": sha("synthetic original epoch") if role == ev.ROLES[0] else epoch,
            "preparation_manifest_sha256": prep_sha, "adapter_manifest_sha256": adapter_sha,
            "training_authority_profile": ev.AUTHORITY_PRIMITIVE_PROFILE,
            "training_prompt_contract": ev.authority_contract_record(),
            "training_decoder_profile": ev.authority_profile_record(environment),
            "artifacts": {"tokenizer": {"root": "tokenizer", "sha256": sha("same tokenizer"), "files": {}},
                          "adapter": {"synthetic": role}}, "research_claim_eligible": False}
        origin["origin_sha256"] = ev._digest(origin)
        origins[role] = origin
        weight = models / "adapter/synthetic-weight.bin"
        expected_weights[role] = (weight, save(weight, b"not real model weights"))
        (models / "tokenizer").mkdir()
    state = SimpleNamespace(root=root, goals=goals, origins=origins, references=references, proposal=proposal,
        evaluation=evaluation, evaluation_sha=evaluation_sha, source_path=source_path, sidecars=sidecars,
        admission=admission, prepared_path=prepared_path, prepared=prepared, weights=expected_weights,
        load_calls=load_calls, replays=[], native_calls=[], model_calls=[], gate_calls=[], releases=[])
    def mocked_load(ref):
        role = next(role for role, expected in references.items() if ref.request == expected.request)
        load_calls.append(role)
        ev._read(ref.receipt_path, ref.receipt_sha256)
        ev._read(ref.request.preparation_directory / "manifest.json", ref.request.preparation_manifest_sha256)
        ev._read(ref.request.adapter_manifest, ref.request.adapter_manifest_sha256)
        weight, expected = expected_weights[role]
        ev._require(sha(weight.read_bytes()) == expected, "synthetic artifact bytes changed")
        return ev.bridge.AuthenticatedOrigin(ref.request, ev._canonical(origins[role]).decode(),
                                             ref.receipt_path.read_bytes(), "synthetic-only-not-original-validation")
    def mocked_admission(path):
        assert path == source_path
        ev._require(all((source_path.parent / name).read_bytes() == value for name, value in sidecars.items()),
                    "synthetic admission sidecar changed")
        return deepcopy(state.admission)
    monkeypatch.setattr(ev.OriginReference, "load", mocked_load)
    monkeypatch.setattr(ev.admission, "admission_identity", mocked_admission)
    files = ("training/peano_hydra/origin_bridge.py", "peano-lab/py/peano_lab/engine/rewrite.py",
             "training/peano_hydra/scaling_evaluation.py")
    execution_sources = {name: sha((ev.ROOT / name).read_bytes()) for name in files}
    monkeypatch.setattr(ev, "execution_sources", lambda: deepcopy(execution_sources))
    state.execution_sources = execution_sources
    def forbidden(*_args, **_kwargs):
        state.native_calls.append(True)
        raise AssertionError("test must never execute native proofs or model runtime")
    monkeypatch.setattr(ev.shared, "_model_runtime", forbidden)
    monkeypatch.setattr(ev.shared, "run_hydra", forbidden)
    monkeypatch.setattr(ev.capacity, "run_proof", forbidden)
    def mocked_replay(view, goal, row):
        state.replays.append((goal["name"], view.budget))
        return deepcopy(row["evidence"]["replay"]), {"synthetic": True, "actual_native_replay": False}
    monkeypatch.setattr(ev.capacity, "_replay_success", mocked_replay)
    state.rebind = lambda: ev.bind_evaluation(evaluation, expected_evaluation_plan_sha256=evaluation_sha,
                                             baseline=references[ev.ROLES[0]], candidate=references[ev.ROLES[1]])
    state.plan = state.rebind()
    state.runtime = {"torch_version": "synthetic", "transformers_version": "synthetic", "peft_version": "synthetic",
        "visible_cuda_devices": 1, "cuda_device": "synthetic-no-GPU", "dtype": "bfloat16", "attention": "sdpa",
        "local_files_only": True, "model_loading": ev.LOADING}
    state.authorization = {"schema": ev.AUTHORIZATION_SCHEMA, "authorization_id": "synthetic-evaluation-only",
        "plan_sha256": state.plan.to_dict()["plan_sha256"],
        "execution_binding_sha256": state.plan.to_dict()["execution_binding"]["execution_binding_sha256"],
        "model_inference_authorized": True, "gpu_count": 1, "max_wall_seconds": 60,
        "max_model_calls": proposal["max_model_calls_total"], "max_goal_records": len(proposal["ordered_slots"]),
        "external_hard_wall_limit_required": True, "training_authorized": False, "upload_authorized": False,
        "new_allocation_authorized": False, "automatic_retry": False, "resume": False,
        "historical_checkpoint_reuse_allowed": False}
    state.auth_sha = ev._digest(state.authorization)
    state.path = root / "synthetic-checkpoint"
    yield state
    assert state.native_calls == [], "an unmocked native/model operation was attempted"


def row(context, role=ev.ROLES[0], budget=8, index=0, *, proved=False, calls=None):
    goal = context.plan.goals[index]
    view = ev._view(context.plan, budget)
    provider = ev._provider(context.plan, role, budget, context.runtime)
    identity = ev.capacity._policy_identity(view, goal, "trained", provider)
    head, calls = identity["heads"][0], (1 if proved else budget) if calls is None else calls
    before, candidates = ("⊢ " + goal["statement"],), ("refl" if proved else "intro",) * 4
    proposals = [ev.ProposalRecord(i + 1, head["name"], "control", head["identity_sha256"], before,
        state_sha256(before), 4, 4, "ok", candidates, (candidates[0],), 3, ev._digest(candidates)).to_record() for i in range(calls)]
    commands, status = (["refl"], "proof") if proved else ([], "limit" if calls == budget else "exhausted")
    contract = ev.search_profile_contract(ev.CONTEXT_ALPHA_V1)
    search = {"status": status, "theorem": goal["statement"], "commands": commands, "certificate_nodes": 1 if proved else None,
        "diagnostics": [], "model_calls": calls, "states_expanded": calls, "states_discovered": 1,
        "candidates_executed": calls, "frontier_peak": 1, "depth_reached": 1 if proved else 0,
        "state_identity": {"contract": contract, "counters": {"key_attempts": 1, "keys_built": 1,
            "keys_declined": 0, "duplicate_states": 0, "renamed_states": 0, "retained_key_bytes": 10, "key_budget_declines": 0}}}
    evidence = {"v": 2, "label": f"hydra-alpha-eval-trained-{goal['name']}", "status": status, "proved": proved,
        "theorem": goal["statement"], "policy": f"hydra-alpha-portfolio-trained-{goal['name']}", "policy_identity": identity,
        "environment": view.environment, "limits": ev.shared._limits_record(view.limits), "commands_sha256": ev._digest(commands) if proved else None,
        "proposal_records": proposals, "degraded": False, "eligible_for_comparison": False,
        "comparison_ineligibility_reasons": [ev.SURFACE_MACRO_V0_INELIGIBILITY], "degradation_reasons": [],
        "search": search, "replay": None, "search_profile": contract}
    if proved:
        request_id, session = ev.paired._replay_ids(evidence, contract)
        evidence["replay"] = {"v": 1, "id": request_id, "session": session, "status": "proved", "kernel_checked": True,
            "theorem": goal["statement"], "goals": [], "tactics_requested": 1, "tactics_applied": 1, "engine_steps": 1,
            "failed_tactics": 0, "proof_nodes": 1, "failed_step": None, "error_type": None, "error": None,
            "mode": "trace", "surface": view.environment["surface"], "environment_sha256": view.environment["environment_sha256"],
            "classical": False, "on_error": "stop", "trace_v": 1,
            "trace": [{"v": 1, "session": session, "step": 1, "goals_before": list(before), "focus": 0, "tactic": "refl",
                       "goals_after": [], "status": "ok", "error": None},
                      {"qed": True, "theorem": goal["statement"], "proof_size": 1, "tactic_count": 1}]}
    return {"goal": goal["name"], "status": status, "kernel_checked": proved, "tactic_decisions": len(commands),
        "proof_nodes": 1 if proved else None, "commands_sha256": evidence["commands_sha256"], "model_generate_calls": calls,
        "generation": {"model_generate_calls": calls, "candidate_sequences_requested": calls * 4,
            "candidate_sequences_returned": calls * 4, "candidate_lines_returned": calls * 4,
            "malformed_sequences_rejected": 0, "authority_sequences_rejected": 0, "one_batched_call_per_search_state": True},
        "policy_identity": identity, "evidence": evidence, "evidence_sha256": ev._digest(evidence), "research_claim_eligible": False,
        "resources": {"goal_wall_seconds": 1, "goal_cpu_seconds": .1, "process_peak_rss_bytes": 1024,
                      "cuda_peak_allocated_bytes": 0, "cuda_peak_reserved_bytes": 0}}


def reseal_row(value):
    value["evidence_sha256"] = ev._digest(value["evidence"])
    return value


def validate(context, value, role=ev.ROLES[0], budget=8, *, replay=False):
    goal = next(goal for goal in context.plan.goals if goal["name"] == value["goal"])
    return ev.validate_row(context.plan, role, budget, goal, value, context.runtime, replay=replay)


def checkpoint(context, count=2, *, inflight=False):
    with ev.EvaluationCheckpoint(context.path, context.plan, authorization=context.authorization,
        expected_authorization_sha256=context.auth_sha, runtime=context.runtime) as store:
        for i, slot in enumerate(context.plan.proposal["ordered_slots"][:count]):
            goal_index = i % len(context.plan.goals)
            store.begin(slot["role"], "calls-" + str(slot["max_model_calls"]), context.plan.goals[goal_index])
            store.append(row(context, slot["role"], slot["max_model_calls"], goal_index, proved=i == 0))
        if inflight:
            slot = context.plan.proposal["ordered_slots"][count]
            store.begin(slot["role"], "calls-" + str(slot["max_model_calls"]), context.plan.goals[count % len(context.plan.goals)])
    return context.path


def test_binding_keeps_distinct_original_epochs_and_all_new_gates_closed(context):
    plan = context.plan.to_dict()
    assert plan["training_origins"][ev.ROLES[0]]["version"] == "v25"
    assert plan["training_origins"][ev.ROLES[1]]["version"] == "v28"
    assert context.plan.origins[ev.ROLES[0]]["epoch_sha256"] != context.plan.origins[ev.ROLES[1]]["epoch_sha256"]
    assert plan["execution_binding"]["contract"]["execution_epoch_sha256"] == context.plan.origins[ev.ROLES[1]]["epoch_sha256"]
    assert plan["gpu_execution_authorized"] is plan["training_authorized"] is plan["research_claim_eligible"] is False
    # Saved artifacts are key-sorted; the model-facing capability record must
    # still satisfy the unchanged canonical prompt transport field order.
    view = ev._view(context.plan, 16)
    assert ev.CapabilityIdentity.from_record(view.environment["capabilities"]).allowed_theorems == ()
    assert context.native_calls == context.replays == []


@pytest.mark.parametrize("change", ["baseline-model", "baseline-prompt", "baseline-decoder", "tokenizer", "admission", "weights", "receipt"])
def test_binding_rejects_changed_authenticated_inputs(context, change):
    old = context.origins[ev.ROLES[0]]
    if change == "baseline-model": old["model"]["revision"] = "b" * 40
    elif change == "baseline-prompt": old["training_prompt_contract"] = {}
    elif change == "baseline-decoder": old["training_decoder_profile"] = {}
    elif change == "tokenizer": old["artifacts"]["tokenizer"]["sha256"] = "d" * 64
    elif change == "admission": save(context.source_path.parent / "training-admission.json", {"changed": True})
    elif change == "weights": context.weights[ev.ROLES[1]][0].write_bytes(b"changed")
    else: context.references[ev.ROLES[0]].receipt_path.write_bytes(b"{}\n")
    with pytest.raises(ValueError): context.rebind()
    assert context.replays == []


@pytest.mark.parametrize("change", ["source-too-long", "wrong-cohort", "only-eight", "foreign-plan-file"])
def test_plan_mismatch_rejects_before_model_runtime(context, change):
    proposal = deepcopy(context.proposal)
    if change == "source-too-long": proposal["goals"][0]["source"] = "x" * 4097
    elif change == "wrong-cohort": proposal["cohort"] = "posthoc-frontier12"
    elif change == "only-eight": proposal["budgets"] = [8]
    else: proposal["candidate_training_plan_sha256"] = "d" * 64
    fields = ("goals", "cohort", "epoch_sha256", "authority_sha256", "lineage_proposal_sha256",
              "baseline_adapter_manifest_sha256", "candidate_training_plan_sha256", "source_files_sha256")
    if change != "wrong-cohort":
        proposal = ev.experiment.build_evaluation_plan(**{key: proposal[key] for key in fields}, budgets=tuple(proposal["budgets"]))
    else: signed(proposal)
    anchor = save(context.evaluation, proposal)
    with pytest.raises(ValueError):
        ev.bind_evaluation(context.evaluation, expected_evaluation_plan_sha256=anchor,
            baseline=context.references[ev.ROLES[0]], candidate=context.references[ev.ROLES[1]])


@pytest.mark.parametrize("calls", [1, 8, 9, 15, 16])
def test_limits_aware_validator_accepts_the_declared_sixteen_call_records(context, calls):
    value = row(context, budget=16, calls=calls)
    assert validate(context, value, budget=16) is None
    assert value["generation"]["candidate_sequences_returned"] == calls * 4
    assert context.replays == []


def test_new_validator_does_not_widen_historical_capacity(context):
    value = row(context, budget=16, calls=16)
    view = ev._view(context.plan, 16)
    with pytest.raises(ValueError):
        ev.capacity._validate_proposals(view, context.plan.goals[0], "trained", value,
                                        ev._provider(context.plan, ev.ROLES[0], 16, context.runtime))
    assert ev.capacity.LIMITS.max_model_calls == 8


@pytest.mark.parametrize("change", ["budget", "role", "profile", "nested-profile", "runner", "call-count", "sequence-count",
                                    "authority", "counter-extra", "counter-missing", "bool-calls", "proof-claim", "resource"])
def test_resealed_row_tampering_fails_before_replay(context, change):
    value = row(context, budget=16, calls=16)
    actual_budget, actual_role = 16, ev.ROLES[0]
    if change == "budget": actual_budget = 8
    elif change == "role": actual_role = ev.ROLES[1]
    elif change == "profile": value["evidence"]["search_profile"] = None
    elif change == "nested-profile": value["evidence"]["search"]["state_identity"]["contract"] = None
    elif change == "runner": value["evidence"]["v"] = 1
    elif change == "call-count": value["model_generate_calls"] = 17
    elif change == "sequence-count": value["generation"]["candidate_sequences_returned"] = 32
    elif change == "authority": value["evidence"]["environment"]["capabilities"]["allowed_theorems"] = ["forbidden"]
    elif change == "counter-extra": value["evidence"]["search"]["state_identity"]["counters"]["unknown"] = 0
    elif change == "counter-missing": value["evidence"]["search"]["state_identity"]["counters"].pop("key_budget_declines")
    elif change == "bool-calls": value["model_generate_calls"] = True
    elif change == "proof-claim": value["kernel_checked"] = True
    else: value["resources"]["goal_wall_seconds"] = float("inf")
    if change != "resource": reseal_row(value)
    with pytest.raises((ValueError, TypeError)):
        validate(context, value, role=actual_role, budget=actual_budget, replay=True)
    assert context.replays == []


def test_positive_requires_exact_saved_profile_replay_and_proposal_binding(context):
    value = row(context, proved=True)
    checked = validate(context, value, replay=True)
    assert checked["max_model_calls"] == 8 and context.replays == [(value["goal"], 8)]
    context.replays.clear()
    value["evidence"]["replay"]["id"] = "legacy-unbound-replay"
    with pytest.raises(ValueError): validate(context, reseal_row(value), replay=True)
    assert context.replays == []


@pytest.mark.parametrize("field,value", [("gpu_count", True), ("max_model_calls", 999999), ("max_wall_seconds", 7201),
    ("model_inference_authorized", False), ("training_authorized", True), ("resume", True),
    ("external_hard_wall_limit_required", False), ("plan_sha256", "d" * 64), ("extra", False)])
def test_authorization_rejects_resealed_foreign_or_expanded_scope_before_loading(context, field, value):
    record = {**context.authorization, field: value}
    with pytest.raises(ValueError):
        ev.execute_evaluation(context.plan, authorization=record, expected_authorization_sha256=ev._digest(record),
            checkpoint_directory=context.path, reservation_check=lambda value: context.gate_calls.append(value))
    assert not context.path.exists() and context.gate_calls == []


def test_missing_or_denied_external_reservation_cannot_load_models(context):
    with pytest.raises(ValueError):
        ev.execute_evaluation(context.plan, authorization=context.authorization, expected_authorization_sha256=context.auth_sha,
                              checkpoint_directory=context.path, reservation_check=None)
    def denied(_): raise ValueError("synthetic reservation refused")
    with pytest.raises(ValueError, match="refused"):
        ev.execute_evaluation(context.plan, authorization=context.authorization, expected_authorization_sha256=context.auth_sha,
                              checkpoint_directory=context.path, reservation_check=denied)
    assert not context.path.exists()


def test_checkpoint_partial_and_inflight_are_readonly_and_not_full_results(context):
    checkpoint(context, 1, inflight=True)
    before = {p.name: p.read_bytes() for p in context.path.iterdir()}
    checked = ev.verify_checkpoint(context.plan, context.path, expected_authorization_sha256=context.auth_sha, replay=False)
    assert checked["completed_goal_records"] == 1 and checked["inflight"]["ordinal"] == 2
    assert checked["inflight_model_generate_calls"] is None and checked["verification_complete"] is False
    assert checked["proof_replay_performed"] is False and context.replays == []
    with ev.EvaluationCheckpoint(context.path, context.plan, expected_authorization_sha256=context.auth_sha,
                                 verify_only=True, replay_proofs=False) as store:
        with pytest.raises(ValueError): store.begin(ev.ROLES[0], "calls-8", context.plan.goals[1])
        with pytest.raises(ValueError): store.append(row(context))
    assert before == {p.name: p.read_bytes() for p in context.path.iterdir()}


@pytest.mark.parametrize("change", ["old-schema", "missing", "uncommitted", "transaction", "hardlink", "symlink", "fifo", "row-digest"])
def test_checkpoint_full_metadata_preflight_rejects_before_any_positive_replay(context, change):
    checkpoint(context)
    if change == "old-schema":
        p = context.path / "HEAD.json"; value = json.loads(p.read_bytes()); value["schema"] = ev.cp.HEAD_SCHEMA
        save(p, signed(value, "head_sha256"))
    elif change == "missing": (context.path / "000002.goal.json").unlink()
    elif change == "uncommitted": save(context.path / "000003.goal.json", {})
    elif change == "transaction": save(context.path / ".transaction-interrupted", {})
    elif change == "hardlink": os.link(context.path / "000001.goal.json", context.root / "hardlink")
    elif change == "symlink": (context.path / "foreign").symlink_to(context.root / "missing")
    elif change == "fifo": os.mkfifo(context.path / "foreign")
    else:
        p = context.path / "000002.goal.json"; value = json.loads(p.read_bytes()); value["row_sha256"] = "d" * 64; save(p, value)
    with pytest.raises((ValueError, OSError)):
        ev.verify_checkpoint(context.plan, context.path, expected_authorization_sha256=context.auth_sha)
    assert context.replays == []


def test_fresh_writer_cannot_resume_or_overwrite_checkpoint(context):
    checkpoint(context, 1)
    before = {p.name: p.read_bytes() for p in context.path.iterdir()}
    with pytest.raises((ValueError, OSError)):
        ev.EvaluationCheckpoint(context.path, context.plan, expected_authorization_sha256=context.auth_sha,
                                authorization=context.authorization, runtime=context.runtime)
    with pytest.raises(TypeError):
        ev.EvaluationCheckpoint(context.path, context.plan, expected_authorization_sha256=context.auth_sha, resume=True)
    assert before == {p.name: p.read_bytes() for p in context.path.iterdir()}


def test_stale_source_or_authorization_rejects_before_checkpoint_replay(context):
    checkpoint(context, 1)
    with pytest.raises(ValueError):
        ev.verify_checkpoint(context.plan, context.path, expected_authorization_sha256="d" * 64)
    context.execution_sources["training/peano_hydra/scaling_evaluation.py"] = "d" * 64
    with pytest.raises(ValueError):
        ev.verify_checkpoint(context.plan, context.path, expected_authorization_sha256=context.auth_sha)
    assert context.replays == []


def install_model_stubs(context, monkeypatch, *, interrupt=False):
    class Model:
        def to(self, _): return self
        def eval(self): return self
    cuda = SimpleNamespace(get_device_name=lambda _: "synthetic-no-GPU", synchronize=lambda: None,
        reset_peak_memory_stats=lambda _: None, max_memory_allocated=lambda _: 0, max_memory_reserved=lambda _: 0)
    torch = SimpleNamespace(__version__="synthetic", cuda=cuda)
    def tokenizer(*_a, **_kw): return SimpleNamespace(pad_token_id=0, eos_token_id=1)
    transformers = SimpleNamespace(__version__="synthetic", AutoTokenizer=SimpleNamespace(from_pretrained=tokenizer))
    peft = SimpleNamespace(__version__="synthetic", PeftModel=SimpleNamespace(from_pretrained=lambda model, *_a, **_k: model))
    monkeypatch.setattr(ev.shared, "_model_runtime", lambda: (torch, transformers, peft))
    monkeypatch.setattr(ev.shared, "_reset_seed", lambda *_: None)
    monkeypatch.setattr(ev.shared, "_load_base_model", lambda *_: Model())
    monkeypatch.setattr(ev.shared, "_release_gpu", lambda *_: context.releases.append(True))
    def lane(view, *, provider, on_goal_start, on_goal, search_profile, **_kwargs):
        assert search_profile == ev.CONTEXT_ALPHA_V1 and len(view.goals) <= 8
        context.model_calls.append((provider["role"], view.budget, [goal["name"] for goal in view.goals]))
        for goal in view.goals:
            on_goal_start(goal)
            if interrupt: raise RuntimeError("synthetic interrupted goal; no actual inference")
            index = next(i for i, candidate in enumerate(context.plan.goals) if candidate["name"] == goal["name"])
            value = row(context, provider["role"], view.budget, index, proved=index == 0)
            value.pop("resources")
            on_goal(value)
        return {"synthetic": "not a real model lane"}
    monkeypatch.setattr(ev.shared, "_run_model_lane", lane)


@pytest.mark.parametrize("context", [9], indirect=True)
def test_explicit_mock_execution_uses_fixed_eight_goal_chunks_and_all_four_arms(context, monkeypatch):
    install_model_stubs(context, monkeypatch)
    result = ev.execute_evaluation(context.plan, authorization=context.authorization, expected_authorization_sha256=context.auth_sha,
        checkpoint_directory=context.path, reservation_check=lambda record: context.gate_calls.append(record))
    assert len(result["rows"]) == 36 and len(context.model_calls) == 8 and len(context.releases) == 4
    assert [(role, budget, len(goals)) for role, budget, goals in context.model_calls] == [
        (role, budget, count) for role in ev.ROLES for budget in ev.BUDGETS for count in (8, 1)]
    checked = ev.verify_result(context.plan, result, expected_authorization_sha256=context.auth_sha)
    assert checked["verification_complete"] is True and len(context.replays) == 4
    assert checked["historical_gpu_inference_attested"] is False
    assert result["metrics"]["model_generation_attested"] is False


def test_mock_execution_interruption_keeps_unknown_inflight_without_final_report(context, monkeypatch):
    install_model_stubs(context, monkeypatch, interrupt=True)
    with pytest.raises(RuntimeError, match="interrupted"):
        ev.execute_evaluation(context.plan, authorization=context.authorization, expected_authorization_sha256=context.auth_sha,
            checkpoint_directory=context.path, reservation_check=lambda _: None)
    checked = ev.verify_checkpoint(context.plan, context.path, expected_authorization_sha256=context.auth_sha, replay=False)
    assert checked["completed_goal_records"] == 0 and checked["inflight"]["ordinal"] == 1
    assert checked["inflight_model_generate_calls"] is None and len(context.releases) == 1


def test_stop_request_before_loading_creates_no_checkpoint_or_model(context):
    with pytest.raises(ev.cp.CheckpointPaused) as caught:
        ev.execute_evaluation(context.plan, authorization=context.authorization, expected_authorization_sha256=context.auth_sha,
            checkpoint_directory=context.path, reservation_check=lambda _: None, stop_requested=lambda: True)
    assert caught.value.receipt["model_loaded"] is False and not context.path.exists()


@pytest.mark.parametrize("kind", ["stop-hook", "deadline"])
@pytest.mark.parametrize("boundary", [
    "initial-reservation", "initial-refresh", "validation-progress", "old-handle", "new-handle", "runtime",
    "checkpoint-refresh", "arm-refresh", "arm-reservation", "loading-progress", "tokenizer", "base",
    "adapter", "placement", "eval-mode",
])
def test_slow_validation_or_loading_boundary_cannot_start_the_next_phase(context, monkeypatch, kind, boundary):
    """No real runtime/model; mock time or operator stop changes inside a slow call."""
    install_model_stubs(context, monkeypatch)
    events, clock, stop = [], [100.0], [False]
    refreshes, reservations = [0], [0]
    def completed(name):
        events.append(name)
        if name == boundary:
            if kind == "deadline": clock[0] += context.authorization["max_wall_seconds"]
            else: stop[0] = True
    monkeypatch.setattr(ev.time, "monotonic", lambda: clock[0])
    def refresh(_plan):
        refreshes[0] += 1
        completed({1: "initial-refresh", 2: "checkpoint-refresh", 3: "arm-refresh"}.get(refreshes[0], "later-refresh"))
    monkeypatch.setattr(ev, "_refresh", refresh)
    def reservation(_record):
        reservations[0] += 1
        completed("initial-reservation" if reservations[0] == 1 else "arm-reservation")
    original_load = ev.OriginReference.load
    def origin_load(ref):
        handle = original_load(ref)
        completed("old-handle" if ref == context.plan.baseline else "new-handle")
        return handle
    monkeypatch.setattr(ev.OriginReference, "load", origin_load)
    torch, transformers, peft = ev.shared._model_runtime()  # The installed test stub only.
    def runtime():
        completed("runtime")
        return torch, transformers, peft
    monkeypatch.setattr(ev.shared, "_model_runtime", runtime)
    original_tokenizer = transformers.AutoTokenizer.from_pretrained
    def tokenizer(*args, **kwargs):
        value = original_tokenizer(*args, **kwargs)
        completed("tokenizer")
        return value
    monkeypatch.setattr(transformers.AutoTokenizer, "from_pretrained", tokenizer)
    class Model:
        def to(self, _): completed("placement"); return self
        def eval(self): completed("eval-mode"); return self
    def base(*_args): completed("base"); return Model()
    def adapter(model, *_args, **_kwargs): completed("adapter"); return model
    monkeypatch.setattr(ev.shared, "_load_base_model", base)
    monkeypatch.setattr(peft.PeftModel, "from_pretrained", adapter)
    def emit(event, **_fields):
        if event == "frontier-validation-complete": completed("validation-progress")
        elif event == "frontier-model-loading-start": completed("loading-progress")
    with pytest.raises(ev.cp.CheckpointPaused) as caught:
        ev.execute_evaluation(context.plan, authorization=context.authorization, expected_authorization_sha256=context.auth_sha,
            checkpoint_directory=context.path, reservation_check=reservation, progress=SimpleNamespace(emit=emit),
            stop_requested=lambda: stop[0])
    assert boundary in events
    # A stop inside an earlier phase must prevent later authentication/imports
    # and weight loading, not merely prevent the first model-generation call.
    assert events[-1] == boundary
    assert context.model_calls == context.replays == []
    assert caught.value.receipt["completed_goal_records"] == 0
    before_checkpoint = boundary in {
        "initial-reservation", "initial-refresh", "validation-progress", "old-handle", "new-handle", "runtime",
    }
    assert context.path.exists() is not before_checkpoint
    if before_checkpoint:
        assert caught.value.receipt["checkpoint_created"] is False
        assert caught.value.receipt["model_loaded"] is False
        assert context.releases == []
    else:
        assert json.loads((context.path / "HEAD.json").read_bytes())["inflight"] is None
        assert caught.value.receipt["status"] == "stopped-at-clean-boundary"
        assert len(context.releases) == 1


def full_report(context):
    rows = [row(context, slot["role"], slot["max_model_calls"], i % len(context.plan.goals), proved=i % len(context.plan.goals) == 0)
            for i, slot in enumerate(context.plan.proposal["ordered_slots"])]
    return ev._result(context.plan, rows, context.runtime, context.authorization, context.auth_sha)


@pytest.mark.parametrize("change", ["missing-row", "last-row", "metrics", "claim"])
def test_final_report_all_metadata_precedes_any_fresh_replay(context, change):
    report = full_report(context)
    if change == "missing-row": report["rows"].pop()
    elif change == "last-row": report["rows"][-1]["model_generate_calls"] += 1
    elif change == "metrics": report["metrics"]["record_count"] += 1
    else: report["historical_gpu_inference_attested"] = True
    signed(report, "evaluation_sha256")
    with pytest.raises(ValueError): ev.verify_result(context.plan, report, expected_authorization_sha256=context.auth_sha)
    assert context.replays == []


def test_post_replay_artifact_mutation_is_detected(context, monkeypatch):
    report = full_report(context)
    def changed(_view, _goal, value):
        context.weights[ev.ROLES[1]][0].write_bytes(b"changed during mocked replay")
        return deepcopy(value["evidence"]["replay"]), {"synthetic": True}
    monkeypatch.setattr(ev.capacity, "_replay_success", changed)
    with pytest.raises(ValueError, match="artifact bytes"):
        ev.verify_result(context.plan, report, expected_authorization_sha256=context.auth_sha)
