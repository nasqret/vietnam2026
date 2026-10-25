"""Synthetic origins/review/replay only; these tests never produce proof evidence.

Real versioned plans, source/preparation joins, checkpoints, file integrity,
authorization and acceptance arithmetic run. Native/human/model boundaries
are explicitly stubbed; genuine candidate proof evidence is tested separately.
"""
from copy import deepcopy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from test_peano_hydra_scaling_evaluation import context, row, raw, save, sha, checkpoint  # noqa: F401
from training.peano_hydra import scaling_evaluation as ev
from training.peano_hydra import frontier_benchmark_run as run
from training.peano_hydra.frontier_benchmark_protocol import BenchmarkReference


@pytest.fixture
def benchmark(context, monkeypatch):
    reference_files = [context.root / "benchmark-evidence" / name for name in ("benchmark-manifest.json", "exposure-audit.json", "human-review.json")]
    pins = [save(path, {"synthetic_only": path.name}) for path in reference_files]
    ref = BenchmarkReference(*[v for path, pin in zip(reference_files, pins) for v in (path, pin)])
    def goals(offset):
        return [{"name": f"synthetic_heldout_{i + offset:03d}", "source": f"{i + offset} = {i + offset}",
                 "statement": f"{i + offset} = {i + offset}", "statement_sha256": sha(f"{i + offset} = {i + offset}"),
                 "lineage_sha256": sha("synthetic-common-heldout-component")} for i in range(32)]
    data = {**ref.to_dict(), "manifest_sha256": sha("synthetic manifest canonical"), "audit_sha256": sha("synthetic audit"),
        "review_sha256": sha("synthetic review assertion"), "epoch_sha256": context.proposal["epoch_sha256"],
        "primary_goals": goals(100), "reserved_goals": goals(200),
        "heldout_goals_sha256": ev._digest(goals(100)),
        "audited_file_sha256": [context.admission["source_manifest_sha256"], sha("synthetic old source")],
        "claim_boundary": {"synthetic_test_only": True, "sealed_benchmark": False}}
    monkeypatch.setattr(BenchmarkReference, "load", lambda self: deepcopy(data))
    old = context.references[ev.ROLES[0]]
    old_prepared = {"source": {"manifest_sha256": sha("synthetic old source")}}
    prep_sha = save(old.request.preparation_directory / "manifest.json", old_prepared)
    context.references[ev.ROLES[0]] = replace(old, request=replace(old.request, preparation_manifest_sha256=prep_sha))
    context.origins[ev.ROLES[0]]["preparation_manifest_sha256"] = prep_sha
    benchmark_context = {
        "benchmark_manifest_sha256": pins[0], "benchmark_audit_sha256": pins[1], "benchmark_review_sha256": pins[2],
        "heldout_goals_sha256": data["heldout_goals_sha256"],
        "candidate_readiness_sha256": context.admission["candidate_readiness_sha256"],
    }
    fields = ("epoch_sha256", "authority_sha256", "lineage_proposal_sha256", "baseline_adapter_manifest_sha256",
              "candidate_training_plan_sha256", "source_files_sha256")
    proposal = ev.experiment.build_evaluation_plan(goals=data["primary_goals"], cohort=run.COHORTS[0],
        benchmark_context=benchmark_context, **{k: context.proposal[k] for k in fields})
    path = context.root / "benchmark-plans/heldout.json"
    pin = save(path, proposal)
    context.rebind = lambda: ev.bind_evaluation(path, expected_evaluation_plan_sha256=pin,
        baseline=context.references[ev.ROLES[0]], candidate=context.references[ev.ROLES[1]], benchmark_reference=ref)
    context.plan = context.rebind()
    context.proposal = proposal
    context.authorization = run._authorization(context.plan)
    context.auth_sha = ev._digest(context.authorization)
    context.benchmark_data = data
    context.benchmark_reference = ref
    return context


def test_versioned_benchmark_roundtrip_and_limits(benchmark):
    plan = benchmark.plan
    assert ev.experiment.validate_evaluation_plan(plan.proposal) == plan.proposal
    assert plan.proposal["schema"] == ev.experiment.BENCHMARK_EVALUATION_SCHEMA
    assert plan.to_dict()["schema"] == ev.BENCHMARK_SCHEMAS[ev.PLAN_SCHEMA]
    assert len(plan.proposal["ordered_slots"]) == 128
    assert plan.proposal["max_model_calls_total"] == 1536
    assert plan.to_dict()["benchmark_reference"] == benchmark.benchmark_reference.to_dict()
    assert plan.proposal["sealed_benchmark"] is plan.proposal["independent_final_test_ownership_claimed"] is False
    assert benchmark.model_calls == []


def test_deferred_candidate_uses_the_actual_v28_trainer_destination(tmp_path):
    from training.peano_hydra import frontier_pilot_launch as launch, posttrain
    epoch = SimpleNamespace(version="v28", epoch_sha256=launch.PINS["epoch_sha256"])
    _, config = posttrain._config(epoch, output=tmp_path / "preparation",
                                  authority_profile=ev.AUTHORITY_PRIMITIVE_PROFILE, run_id="frontier-v1")
    # Native source is v28; the preserved old adapter's v25 is not reused.
    assert run.ADAPTER_OUTPUT == launch.ADAPTER_OUTPUT + "/manifest.json"
    assert launch.ADAPTER_OUTPUT == config.run.output_dir


def test_old_dev_cannot_become_benchmark_by_adding_a_review(context, tmp_path):
    fake = BenchmarkReference(tmp_path / "m", "1" * 64, tmp_path / "a", "2" * 64, tmp_path / "r", "3" * 64)
    with pytest.raises(ValueError, match="legacy DEV"):
        ev.bind_evaluation(context.evaluation, expected_evaluation_plan_sha256=context.evaluation_sha,
            baseline=context.references[ev.ROLES[0]], candidate=context.references[ev.ROLES[1]], benchmark_reference=fake)


@pytest.mark.parametrize("mutation", ["audit_source", "epoch", "readiness", "review", "goal"])
def test_changed_review_or_training_join_fails_before_inference(benchmark, mutation):
    data = benchmark.benchmark_data
    if mutation == "audit_source": data["audited_file_sha256"] = []
    elif mutation == "epoch": data["epoch_sha256"] = "f" * 64
    elif mutation == "readiness":
        benchmark.admission["bindings"]["execution_source_files_sha256"] = "f" * 64
    elif mutation == "review": data["review_file_sha256"] = "f" * 64
    else: data["primary_goals"][0]["statement"] = "False"
    with pytest.raises(ValueError): ev._refresh(benchmark.plan)
    assert benchmark.model_calls == [] and benchmark.replays == []


def test_new_cohort_cannot_relabel_arbitrary_goals_as_historical_regression(benchmark):
    plan = deepcopy(benchmark.proposal)
    plan["cohort"] = run.COHORTS[1]
    plan["plan_sha256"] = ev._digest({k: v for k, v in plan.items() if k != "plan_sha256"})
    with pytest.raises(ValueError, match="historical PRIMARY32"):
        ev.experiment.validate_evaluation_plan(plan)


def test_v2_checkpoint_readonly_replay_keeps_version_and_unknown_prefix(benchmark):
    target = checkpoint(benchmark, count=2, inflight=True)
    header = json.loads((target / "header.json").read_bytes())
    assert header["schema"] == ev.BENCHMARK_SCHEMAS[ev.HEADER_SCHEMA]
    assert json.loads((target / "HEAD.json").read_bytes())["schema"] == ev.BENCHMARK_SCHEMAS[ev.HEAD_SCHEMA]
    before = {p.name: p.read_bytes() for p in target.iterdir()}
    receipt = ev.verify_checkpoint(benchmark.plan, target, expected_authorization_sha256=benchmark.auth_sha)
    assert receipt["schema"] == ev.BENCHMARK_SCHEMAS[ev.VERIFY_SCHEMA]
    assert receipt["completed_goal_records"] == 2 and receipt["verification_complete"] is False
    assert receipt["inflight"] is not None and receipt["inflight_model_generate_calls"] is None
    assert {p.name: p.read_bytes() for p in target.iterdir()} == before
    assert len(benchmark.replays) == 1  # explicitly synthetic replay spy


def test_benchmark_without_review_stays_unexecutable(benchmark):
    path = benchmark.plan.evaluation_path
    with pytest.raises(ValueError, match="externally pinned human review"):
        ev.bind_evaluation(path, expected_evaluation_plan_sha256=benchmark.plan.evaluation_raw_sha256,
            baseline=benchmark.plan.baseline, candidate=benchmark.plan.candidate)


def test_declared_projection_cannot_silently_gain_an_extra_context_field(benchmark):
    plan = deepcopy(benchmark.proposal)
    plan["benchmark_context"]["pretend_independent"] = "0" * 64
    plan["plan_sha256"] = ev._digest({k: v for k, v in plan.items() if k != "plan_sha256"})
    with pytest.raises(ValueError, match="benchmark context"):
        ev.experiment.validate_evaluation_plan(plan)


def _synthetic_reports(*, gain8=0, gain16=4, regression_loss=0, unknown=False):
    reports, receipts = {}, {}
    for cohort in run.COHORTS:
        slots, rows, pairs = [], [], []
        for role in ev.ROLES:
            for budget in (8, 16):
                count = 10 + (gain8 if budget == 8 else gain16) if role == ev.ROLES[1] and cohort == run.COHORTS[0] else 10
                if role == ev.ROLES[1] and cohort == run.COHORTS[1]: count -= regression_loss
                for i in range(32):
                    slots.append({"role": role, "max_model_calls": budget, "goal": "g" + str(i)})
                    rows.append({"kernel_checked": i < count, "model_generate_calls": 2 if i < count else budget})
        for budget in (8, 16):
            gain = (gain8 if budget == 8 else gain16) if cohort == run.COHORTS[0] else 0
            pairs.append({"max_model_calls": budget, "reported_gains": ["g" + str(i) for i in range(max(gain, 0))],
                "reported_losses": ["l" + str(i) for i in range(max(-gain, 0) if cohort == run.COHORTS[0] else regression_loss)]})
        reports[cohort] = {"evaluation_sha256": sha("synthetic-report-" + cohort), "rows": rows,
            "plan": {"evaluation_plan": {"cohort": cohort, "ordered_slots": slots}},
            "metrics": {"all_records_present": True, "explicit_unknown_records": int(unknown), "matched_comparisons": pairs}}
        receipts[cohort] = {"status": "passed", "verification_complete": True, "proof_replay_performed": True,
                           "evaluation_sha256": reports[cohort]["evaluation_sha256"]}
    return reports, receipts


@pytest.mark.parametrize("changes,passes", [({}, True), ({"gain16": 3}, False), ({"gain8": -1}, False),
                                          ({"regression_loss": 1}, False)])
def test_preregistered_gain_and_regression_thresholds(changes, passes):
    result = run._decision(*_synthetic_reports(**changes))
    assert (result["status"] == "pilot-gate-met") is passes
    assert result["self_training_authorized"] is result["scaling_authorized"] is False


def test_unknowns_and_metadata_only_cannot_trigger_scale_decision():
    with pytest.raises(ValueError, match="unknown"):
        run._decision(*_synthetic_reports(unknown=True))
    reports, receipts = _synthetic_reports()
    receipts[run.COHORTS[0]]["proof_replay_performed"] = False
    with pytest.raises(ValueError, match="fresh native replay"):
        run._decision(reports, receipts)


def test_primary_cost_regression_blocks_even_when_more_proofs_are_reported():
    reports, receipts = _synthetic_reports()
    for slot, record in zip(reports[run.COHORTS[0]]["plan"]["evaluation_plan"]["ordered_slots"],
                            reports[run.COHORTS[0]]["rows"]):
        if slot["max_model_calls"] == 16:
            record["model_generate_calls"] = 1 if slot["role"] == ev.ROLES[0] else 16
    decision = run._decision(reports, receipts)
    assert decision["criteria"]["primary_net_gain_at_16_calls"] is True
    assert decision["criteria"]["cost_ratio"] is False
    assert decision["status"] == "pilot-gate-not-met"


def test_draft_and_raw_mismatch_reject_before_any_package_input(tmp_path, monkeypatch):
    record = {k: None for k in ("schema", "status", "profile", "run_id", "benchmark_manifest", "benchmark_audit", "benchmark_review",
        "cohorts", "admitted_inputs", "baseline", "candidate", "acceptance_protocol", "limits", "gpu_execution_authorized",
        "sealed_benchmark", "research_claim_eligible", "request_sha256")}
    record.update(schema=run.SCHEMA, status="draft-pending-human-reference-review")
    path = tmp_path / "request.json"
    pin = save(path, record)
    monkeypatch.setattr(run, "_read", lambda *_a, **_k: pytest.fail("draft touched package"))
    with pytest.raises(ValueError, match="still a draft"): run.check_request(path, pin)
    with pytest.raises(ValueError, match="raw SHA differs"): run.check_request(path, "0" * 64)


def test_large_factorial_report_has_its_own_existing_cap_and_never_overwrites(tmp_path):
    value = {"synthetic_padding": "x" * (4 * 1024**2 + 1)}
    path = tmp_path / "synthetic-report.json"
    run.write_report(path, value)
    assert json.loads(path.read_bytes()) == value
    before = path.read_bytes()
    with pytest.raises(ValueError, match="fresh"): run.write_report(path, {"replacement": True})
    assert path.read_bytes() == before


def test_report_writer_refuses_symlink_ancestor(tmp_path):
    actual, alias = tmp_path / "actual", tmp_path / "alias"
    actual.mkdir()
    alias.symlink_to(actual, target_is_directory=True)
    with pytest.raises((ValueError, OSError)): run.write_report(alias / "report.json", {"synthetic": True})
    assert list(actual.iterdir()) == []


def _job_fixture():
    script = "slurm/peano_hydra_frontier_train.sbatch"
    commit, script_sha, prep_sha = "c" * 40, sha("synthetic frontier job"), sha("synthetic preparation")
    checked = SimpleNamespace(record={"candidate": {"source_commit": commit},
        "admitted_inputs": {"preparation_manifest": {"sha256": prep_sha}}})
    reservation = {"jobs": {"train": "1234", "evaluate": "1235"}}
    resource = {"source_files": {script: {"sha256": script_sha}}}
    adapter = {"run_id": "frontier-v1", "model_trained": True, "preparation_manifest_sha256": prep_sha,
        "job": {"scheduler": "slurm", "job_id": "1234",
            "submission": {"job_id": "1234", "script": script, "script_sha256": script_sha,
                           "git_commit": commit, "git_dirty": "false"},
            "deployment": {"job_script": {"path": script, "sha256": script_sha, "status": "declared"},
                           "source_sync": {"git_commit": commit, "git_dirty": False}}}}
    return checked, adapter, reservation, resource


@pytest.mark.parametrize("changed", ["job", "submission", "script", "commit", "preparation", "incomplete"])
def test_same_source_adapter_from_wrong_run_cannot_satisfy_deferred_binding(changed):
    checked, adapter, reservation, resource = _job_fixture()
    run._check_trained_job(checked, adapter, reservation, resource)
    if changed == "job": adapter["job"]["job_id"] = "1230"
    elif changed == "submission": adapter["job"]["submission"]["job_id"] = "1230"
    elif changed == "script": adapter["job"]["submission"]["script_sha256"] = "f" * 64
    elif changed == "commit": adapter["job"]["deployment"]["source_sync"]["git_commit"] = "f" * 40
    elif changed == "preparation": adapter["preparation_manifest_sha256"] = "f" * 64
    else: adapter["model_trained"] = False
    with pytest.raises(ValueError, match="exact approved training predecessor"):
        run._check_trained_job(checked, adapter, reservation, resource)


def test_shared_deadline_prevents_second_cohort_and_retains_first_report(tmp_path, monkeypatch):
    """Real two-stage coordinator; scheduler/origin/model are synthetic stubs."""
    from training.peano_hydra import frontier_pilot_launch as launch
    monkeypatch.setattr(run, "ROOT", tmp_path)
    clock = [0]
    monkeypatch.setattr(run, "time", SimpleNamespace(monotonic=lambda: clock[0]))
    checked = SimpleNamespace(path=tmp_path / "synthetic-request.json", raw_sha256=sha("synthetic-request"),
                              record={"candidate": {"source_commit": "c" * 40}})
    approval = {"request_file_sha256": sha("synthetic resource request")}
    resource = {"payloads": {launch.INPUTS["evaluation_request"]: {"sha256": checked.raw_sha256}}, "source_commit": "c" * 40}
    reservation = {"jobs": {"train": "1234", "evaluate": "1235"}, "evaluation_request_sha256": checked.raw_sha256}
    monkeypatch.setattr(launch, "validate_metadata", lambda _sha: (approval, resource))
    monkeypatch.setattr(launch, "check_job_reservation", lambda *_a: deepcopy(reservation))
    monkeypatch.setattr(run, "check_request", lambda *_a: checked)
    monkeypatch.setattr(run, "_candidate_request", lambda *_a: "synthetic-origin-request")
    monkeypatch.setattr(run, "_check_trained_job", lambda *_a: None)
    libraries = ("/synthetic/reviewed/central/lib",)
    monkeypatch.setattr(run.files, "runtime_libraries", lambda: libraries)
    origin_calls = []
    def authenticate(request, **options):
        origin_calls.append(options)
        return SimpleNamespace(request=request, receipt_bytes=b"{}\n", receipt_sha256=sha(b"{}\n"))
    monkeypatch.setattr(run.bridge, "authenticate_origin", authenticate)
    monkeypatch.setattr(run.evaluation, "OriginReference", lambda *_a: "synthetic-origin-reference")
    monkeypatch.setattr(run, "_bind", lambda *_a: {name: name for name in run.COHORTS})
    monkeypatch.setattr(run, "_authorization", lambda plan: {"synthetic_plan": plan})
    calls = []
    def evaluate(plan, **options):
        options["reservation_check"](options["authorization"])
        assert options["stop_requested"]() is False
        calls.append(plan)
        clock[0] = 1501
        return {"synthetic_report_not_model_output": plan}
    monkeypatch.setattr(run.evaluation, "execute_evaluation", evaluate)
    adapter = tmp_path / run.ADAPTER_OUTPUT
    adapter.parent.mkdir(parents=True)
    adapter.write_text('{"synthetic":true}\n')
    output = tmp_path / launch.outputs(reservation["jobs"])["evaluation"]
    with pytest.raises(ValueError, match="shared evaluation deadline"):
        run.execute(checked, approval_path=tmp_path / launch.APPROVAL, approval_sha256=sha("syntheticapproval"),
                    output=output, stop_after_seconds=1500, started=0)
    assert calls == [run.COHORTS[0]]
    assert origin_calls[0]["runtime_library_paths"] == libraries
    assert (output / (run.COHORTS[0] + ".json")).is_file()
    assert not (output / "run.json").exists()
    status = json.loads((output / "execution-status.json").read_bytes())
    assert status["uncompleted_outcomes"] == "unknown" and status["automatic_retry"] is False
