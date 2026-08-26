"""Review orchestration rejects forged summaries and re-sealed partial ledgers.

Small synthetic receipts exercise protocol validation, not library evidence.
No full Alpha replay, compiler, preparation audit, or model runs in this file.
"""

from copy import deepcopy
from hashlib import sha256
import importlib.util
from pathlib import Path
import signal
import sys
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from peano_lab.kernel import proofs as p, terms as t  # noqa: E402
from training.peano_hydra import review as r  # noqa: E402
from training.peano_hydra.cold_replay import cold_target_record, fingerprint_certificate  # noqa: E402
from training.peano_hydra.epoch import EpochTheorem  # noqa: E402
from training.peano_hydra.frontier import canonical, digest  # noqa: E402
from training.peano_hydra.review_runtime import RESOURCE_MEASUREMENT  # noqa: E402


def _seal(record, field="receipt_sha256"):
    record.pop(field, None)
    record[field] = digest(record)
    return record


def _plan(*, batch_size=1, scope="full", budget=900):
    targets = [cold_target_record(EpochTheorem(
        f"fixture_{index}", "0 = 0", sha256(b"0 = 0").hexdigest(), ("refl",),
        sha256(b"refl\n").hexdigest(), (), "stable", index,
    )) for index in range(2)]
    cold = {"targets": targets, "target_count": 2, "edition_identity_sha256": "b" * 64,
            "certificate_limits": r.CertificateLimits().to_dict(), "batch_size": batch_size,
            "batches": [list(range(start, min(2, start + batch_size))) for start in range(0, 2, batch_size)]}
    return {"source": {"fixture": True}, "epoch_sha256": "a" * 64,
            "profile": {"profile_sha256": "c" * 64}, "cold_plan": cold,
            "cold_selection": r.cold_selection(cold, scope), "cold_wall_budget": budget}


def _positive(plan, index):
    target = plan["cold_plan"]["targets"][index]
    return _seal({
        "schema": r.COLD_REPLAY_SCHEMA, "status": "checked", "kernel_checked": True,
        "epoch_sha256": plan["epoch_sha256"], "edition_identity_sha256": plan["cold_plan"]["edition_identity_sha256"],
        **{key: target[key] for key in ("target_sha256", "name", "enrollment_index", "membership",
                                       "statement_sha256", "script_sha256", "dependencies_sha256")},
        "original_formula_sha256": "d" * 64, "certificate": fingerprint_certificate(p.EqRefl(t.Zero())),
        "certificate_limits": plan["cold_plan"]["certificate_limits"], "kernel_mode": "intuitionistic",
        "empty_context": True, "independent_recheck_calls": 1, "runtime_internal_kernel_calls": None,
        "all_scripts_regenerated": False, "lean_companion_invoked": False,
        "model_calls": 0, "solver_calls": 0, "research_claim_eligible": False,
    })


def _unknown(plan, index):
    return {"status": "unknown", "kernel_checked": False,
            **{key: plan["cold_plan"]["targets"][index][key] for key in ("name", "enrollment_index", "target_sha256")},
            "error_type": "ColdReplayError", "error": "bounded fixture did not complete"}


def _process(stdout, request, limits, *, code=0, reason="exited"):
    return {"command": [sys.executable, str(r.SCRIPT), "--worker"], "limits": limits.to_dict(),
            "stdin_bytes": len(request), "stdin_sha256": sha256(request).hexdigest(),
            "returncode": code, "reason": reason, "stdout": stdout, "stderr": "",
            "output_encoding": "utf-8", "raw_output_base64": None, "output_truncated": False,
            "stdout_bytes": len(stdout.encode()), "stderr_bytes": 0,
            "stdout_sha256": sha256(stdout.encode()).hexdigest(), "stderr_sha256": sha256(b"").hexdigest(),
            "resources": {"wall_seconds": 0.01, "cpu_seconds": 0.005,
                          "peak_rss_bytes": 1024**2, "sampled_peak_group_rss_bytes": None,
                          "cpu_instructions": None, "energy_joules": None},
            "observed_descendant_count": 0, "resource_measurement": RESOURCE_MEASUREMENT}


def _refresh(plan, ledger):
    ledger["rows"] = []
    for batch in ledger["batches"]:
        complete = batch["worker"]["stdout"].split("\n")[:-1]
        batch["completed_targets"] = len(complete)
        ledger["rows"].extend(r.decode(line.encode()) for line in complete)
    ledger["summary"] = r.summarize_cold(plan, ledger["rows"], ledger["batches"], wall_seconds=ledger["wall_seconds"])
    return ledger


def _ledger(plan):
    batches = []
    for number, index, indices in r._cold_schedule(plan):
        rows = [{"pass_number": number, "batch_number": index, "receipt": _positive(plan, target)} for target in indices]
        stdout = b"".join(canonical(row) + b"\n" for row in rows).decode()
        worker = _process(stdout, canonical(r._cold_request(plan, number, index, indices)), r.COLD_LIMITS)
        batches.append({"pass_number": number, "batch_number": index, "indices": indices,
                        "started_wall_seconds": len(batches) * 0.01,
                        "worker": worker, "completed_targets": len(rows)})
    return _refresh(plan, {"schema": r.COLD_LEDGER_SCHEMA, "batches": batches, "rows": [],
                          "wall_seconds": len(batches) * 0.01 + 0.1, "wall_budget": plan["cold_wall_budget"],
                          "stop_reason": "completed", "summary": {}})


def _replace_output(batch, text):
    batch["worker"].update(stdout=text, stdout_bytes=len(text.encode()), stdout_sha256=sha256(text.encode()).hexdigest())


def _edit_first_receipt(ledger, mutate):
    batch = ledger["batches"][0]
    rows = [r.decode(line.encode()) for line in batch["worker"]["stdout"].split("\n")[:-1]]
    mutate(rows[0]["receipt"])
    if rows[0]["receipt"].get("kernel_checked") is not False:
        _seal(rows[0]["receipt"])
    _replace_output(batch, b"".join(canonical(row) + b"\n" for row in rows).decode())


def test_exact_two_pass_ledger_and_reproduction():
    plan = _plan()
    ledger = _ledger(plan)
    r.validate_cold_ledger(plan, ledger)
    assert ledger["summary"]["full_epoch_replayed_twice"] is True
    assert r.compare_cold_reproduction(plan, ledger, deepcopy(ledger)) == 4


def test_sample_never_becomes_a_full_epoch_gate():
    plan = _plan(scope="sample")
    ledger = _ledger(plan)
    r.validate_cold_ledger(plan, ledger)
    assert ledger["summary"]["matching_complete_selected_passes"] is True
    assert ledger["summary"]["full_epoch_replayed_twice"] is False


@pytest.mark.parametrize("key,value", [
    ("name", "another_theorem"), ("enrollment_index", True), ("enrollment_index", 1),
    ("target_sha256", "0" * 64), ("statement_sha256", "0" * 64), ("script_sha256", "0" * 64),
    ("dependencies_sha256", "0" * 64), ("membership", "alpha_only"), ("epoch_sha256", "0" * 64),
    ("edition_identity_sha256", "0" * 64), ("kernel_mode", "classical"), ("empty_context", 1),
    ("independent_recheck_calls", True), ("runtime_internal_kernel_calls", 1), ("model_calls", True),
    ("solver_calls", 1), ("lean_companion_invoked", True), ("all_scripts_regenerated", True),
    ("research_claim_eligible", True), ("h0_complete", True), ("kernel_checked", 1),
])
def test_resealed_cold_receipt_cannot_change_target_or_authority(key, value):
    plan = _plan()
    ledger = _ledger(plan)
    _edit_first_receipt(ledger, lambda receipt: receipt.update({key: value}))
    _refresh(plan, ledger)
    with pytest.raises(ValueError):
        r.validate_cold_ledger(plan, ledger)


@pytest.mark.parametrize("key,value", [
    ("sha256", "wrong"), ("proof_nodes", True), ("proof_nodes", 500001),
    ("proof_depth", 257), ("annotation_nodes", -1), ("envelope_depth", 513),
    ("proof_objects", 2), ("proof_edges", -1), ("syntax_objects", 3),
    ("sharing_independent_digest", False), ("dne_objects", 1), ("dne_objects", False),
])
def test_resealed_certificate_cannot_change_shape_or_bounds(key, value):
    plan = _plan()
    ledger = _ledger(plan)
    _edit_first_receipt(ledger, lambda receipt: receipt["certificate"].update({key: value}))
    _refresh(plan, ledger)
    with pytest.raises(ValueError):
        r.validate_cold_ledger(plan, ledger)


def test_duplicate_positive_cannot_cover_a_different_assigned_target():
    plan = _plan(batch_size=2)
    ledger = _ledger(plan)
    first = ledger["rows"][0]
    _replace_output(ledger["batches"][0], (canonical(first).decode() + "\n") * 2)
    _refresh(plan, ledger)
    with pytest.raises(ValueError, match="original target"):
        r.validate_cold_ledger(plan, ledger)


def test_row_list_cannot_duplicate_a_target_while_worker_output_stays_valid():
    plan = _plan()
    ledger = _ledger(plan)
    ledger["rows"][1] = deepcopy(ledger["rows"][0])
    ledger["summary"] = r.summarize_cold(plan, ledger["rows"], ledger["batches"], wall_seconds=ledger["wall_seconds"])
    with pytest.raises(ValueError, match="ordered worker outputs"):
        r.validate_cold_ledger(plan, ledger)


@pytest.mark.parametrize("mutation", ["order", "duplicate_batch", "extra_batch", "boolean_pass", "count", "stdin", "limits", "summary", "early_stop", "duration", "overlap", "unreserved_launch", "unknown_field"])
def test_cold_ledger_structure_and_resource_bindings_fail_closed(mutation):
    plan = _plan()
    ledger = _ledger(plan)
    if mutation == "order":
        ledger["batches"].reverse()
    elif mutation == "duplicate_batch":
        ledger["batches"][1] = deepcopy(ledger["batches"][0])
    elif mutation == "extra_batch":
        ledger["batches"].append(deepcopy(ledger["batches"][0]))
    elif mutation == "boolean_pass":
        ledger["batches"][0]["pass_number"] = True
    elif mutation == "count":
        ledger["batches"][0]["completed_targets"] = True
    elif mutation == "stdin":
        ledger["batches"][0]["worker"]["stdin_sha256"] = "0" * 64
    elif mutation == "limits":
        ledger["batches"][0]["worker"]["limits"]["cpu_seconds"] += 1
    elif mutation == "summary":
        ledger["summary"]["passes"][0]["checked"] += 1
    elif mutation == "early_stop":
        ledger["batches"].pop()
        ledger["stop_reason"] = "wall-budget-insufficient-for-next-worker"
        _refresh(plan, ledger)
    elif mutation == "duration":
        ledger["wall_seconds"] = 0
    elif mutation == "overlap":
        ledger["batches"][1]["started_wall_seconds"] = 0
    elif mutation == "unreserved_launch":
        ledger["batches"][0]["started_wall_seconds"] = plan["cold_wall_budget"] - 1
    else:
        ledger["silent_retry"] = True
    with pytest.raises(ValueError):
        r.validate_cold_ledger(plan, ledger)


def test_killed_batch_retains_only_complete_flushed_rows_and_never_claims_full():
    plan = _plan(batch_size=2)
    ledger = _ledger(plan)
    first = canonical(ledger["rows"][0]).decode() + "\n"
    batch = ledger["batches"][0]
    _replace_output(batch, first + '{"unfinished":')
    batch["worker"].update(reason="cpu_limit", returncode=-signal.SIGXCPU)
    _refresh(plan, ledger)
    r.validate_cold_ledger(plan, ledger)
    assert len(ledger["rows"]) == 3
    assert ledger["summary"]["passes"][0]["not_completed"] == 1
    assert ledger["summary"]["worker_failures"] == 1
    assert ledger["summary"]["full_epoch_replayed_twice"] is False


@pytest.mark.parametrize("text", ["", "{}", "{}\u2028", "{}\n", "{}\n{}\n"])
def test_normal_success_cannot_drop_or_misframe_its_receipts(text):
    plan = _plan()
    ledger = _ledger(plan)
    _replace_output(ledger["batches"][0], text)
    with pytest.raises(ValueError):
        r.validate_cold_ledger(plan, ledger)


def test_unknown_is_not_a_negative_theorem_and_need_not_reproduce_as_unknown():
    plan = _plan()
    old, fresh = _ledger(plan), _ledger(plan)
    _edit_first_receipt(old, lambda receipt: (receipt.clear(), receipt.update(_unknown(plan, 0))))
    _refresh(plan, old)
    r.validate_cold_ledger(plan, old)
    assert old["summary"]["passes"][0]["unknown"] == 1
    assert r.compare_cold_reproduction(plan, old, fresh) == 3
    with pytest.raises(ValueError, match="reproduce"):
        r.compare_cold_reproduction(plan, fresh, old)
    _edit_first_receipt(old, lambda receipt: receipt.update(negative_theorem=True))
    _refresh(plan, old)
    with pytest.raises(ValueError, match="diagnostic"):
        r.validate_cold_ledger(plan, old)


@pytest.mark.parametrize("field", ["original_formula_sha256", "certificate"])
def test_fresh_reproduction_compares_complete_deterministic_receipts(field):
    plan = _plan()
    old, fresh = _ledger(plan), _ledger(plan)
    def mutate(receipt):
        if field == "certificate":
            receipt["certificate"]["sha256"] = "e" * 64
        else:
            receipt[field] = "e" * 64
    _edit_first_receipt(fresh, mutate)
    _refresh(plan, fresh)
    with pytest.raises(ValueError, match="reproduce"):
        r.compare_cold_reproduction(plan, old, fresh)


def test_scope_none_and_insufficient_whole_budget_remain_explicit():
    for scope, budget in (("none", 900), ("full", 30)):
        plan = _plan(scope=scope, budget=budget)
        ledger = {"schema": r.COLD_LEDGER_SCHEMA, "batches": [], "rows": [], "wall_seconds": 0.01,
                  "wall_budget": budget, "stop_reason": "completed" if scope == "none" else "wall-budget-insufficient-for-next-worker"}
        ledger["summary"] = r.summarize_cold(plan, [], [], wall_seconds=0.01)
        r.validate_cold_ledger(plan, ledger)
        assert ledger["summary"]["full_epoch_replayed_twice"] is False


def test_global_wall_overrun_cannot_satisfy_full_cold_gate():
    plan = _plan()
    ledger = _ledger(plan)
    ledger["wall_seconds"] = plan["cold_wall_budget"] + 1
    _refresh(plan, ledger)
    r.validate_cold_ledger(plan, ledger)
    assert ledger["summary"]["matching_complete_selected_passes"] is True
    assert ledger["summary"]["whole_stage_within_budget"] is False
    assert ledger["summary"]["full_epoch_replayed_twice"] is False


@pytest.mark.parametrize("raw", [b'[],"extra":1', b'{}', b'null', b'[NaN]', b'[{"split":"train","split":"dev"}]', b'[] []'])
def test_allocations_are_standalone_strict_json(raw, tmp_path):
    path = tmp_path / "proposal.json"
    path.write_bytes(raw)
    with pytest.raises(ValueError):
        r.read_allocations(path)


def test_standalone_allocation_array_is_preserved_for_component_validation(tmp_path):
    path = tmp_path / "proposal.json"
    value = [{"component_id": "fixture", "split": "quarantine"}]
    path.write_bytes(canonical(value))
    assert r.read_allocations(path) == value


def _header():
    return _seal({"schema": r.SCHEMA, "status": "completed-with-open-gates",
                  "started_at": "2026-08-27T12:00:00+00:00", "finished_at": "2026-08-27T12:01:00+00:00",
                  "plan": {}, "cases": {}, "plan_sha256": "a" * 64, "evidence": {}, "summary": {},
                  "model_calls": 0, "solver_calls": 0, "model_training_authorized": False,
                  "independent_human_review_granted": False, "h0_complete": False, "h1_complete": False,
                  "sealed_benchmark": False, "research_claim_eligible": False}, "report_sha256")


@pytest.mark.parametrize("field,value", [
    ("schema", "old-review"), ("model_calls", False), ("solver_calls", 1),
    ("h0_complete", True), ("h1_complete", True), ("model_training_authorized", True),
    ("independent_human_review_granted", True), ("sealed_benchmark", True), ("research_claim_eligible", True),
    ("finished_at", "2026-08-27T11:59:00+00:00"), ("started_at", "2026-08-27T12:00:00"),
    ("unknown_field", False),
])
def test_resealed_header_cannot_promote_or_hide_open_gates(field, value):
    report = _header()
    r.validate_report_header(report)
    report[field] = value
    _seal(report, "report_sha256")
    with pytest.raises(ValueError):
        r.validate_report_header(report)


def _validation_plan(monkeypatch, tmp_path):
    plan = _plan()
    plan.update(schema=r.SCHEMA, status="planned", source={}, development_directory="development",
                development_plan_sha256="d" * 64, preparation_directories=["preparation"],
                allocation_input=None, lineage_review={}, reference={}, reference_project=str(tmp_path),
                conformance={"case_count": 0}, parallel_workers=1, native_limits=r.NATIVE_LIMITS.to_dict(),
                reserved_reference_processes=len(r.MODULES) + 1, model_calls=0, solver_calls=0, data_written=False,
                model_training_authorized=False, independent_human_review_granted=False, h0_complete=False,
                h1_complete=False, sealed_benchmark=False, research_claim_eligible=False)
    _seal(plan, "plan_sha256")
    monkeypatch.setattr(r, "ROOT", tmp_path)
    monkeypatch.setattr(r, "validate_sources", lambda record: None)
    monkeypatch.setattr(r, "validate_reference_identity", lambda record: None)
    monkeypatch.setattr(r, "validate_reference_provenance", lambda project, record: None)
    monkeypatch.setattr(r, "freeze_epoch", lambda: SimpleNamespace(epoch_sha256=plan["epoch_sha256"]))
    monkeypatch.setattr(r, "development_profile", lambda: deepcopy(plan["profile"]))
    frozen_cold, frozen_cases = deepcopy(plan["cold_plan"]), deepcopy(plan["conformance"])
    monkeypatch.setattr(r, "build_cold_replay_plan", lambda epoch, batch_size: deepcopy(frozen_cold))
    monkeypatch.setattr(r, "build_conformance_cases", lambda: ())
    monkeypatch.setattr(r, "conformance_manifest", lambda cases, epoch_sha256: deepcopy(frozen_cases))
    return plan


def test_repository_relative_preparations_remain_valid_from_another_cwd(monkeypatch, tmp_path):
    plan = _validation_plan(monkeypatch, tmp_path)
    outside = tmp_path / "another-working-directory"
    outside.mkdir()
    monkeypatch.chdir(outside)
    original = {"plan_sha256": plan["development_plan_sha256"], "benchmark": {}, "source": {},
                "preparation_audits": [{"preparation_directory": "preparation", "audit": {}}]}
    monkeypatch.setattr(r, "_development", lambda path: original)
    def review_lineages(epoch, **kwargs):
        assert kwargs["preparation_dirs"] == (tmp_path / "preparation",)
        return {}
    monkeypatch.setattr(r, "build_lineage_review", review_lineages)
    r.validate_plan(plan)


@pytest.mark.parametrize("field,value", [
    ("reserved_reference_processes", 0), ("reserved_reference_processes", True),
    ("parallel_workers", True), ("model_calls", False), ("cold_wall_budget", 3601),
    ("h0_complete", True), ("data_written", True), ("extra_authority", True),
    ("preparation_directories", ["/outside/preparation"]), ("development_directory", "../outside"),
])
def test_resealed_plan_resource_and_input_boundaries(field, value, monkeypatch, tmp_path):
    plan = _validation_plan(monkeypatch, tmp_path)
    r.validate_plan(plan, live_audits=False)
    plan[field] = value
    _seal(plan, "plan_sha256")
    with pytest.raises(ValueError):
        r.validate_plan(plan, live_audits=False)


def test_claimed_summary_is_derived_from_all_saved_evidence(monkeypatch):
    plan = _plan()
    plan.update(conformance={"distinct_positive_formula_count": 1024},
                reference={"matches_project_toolchain_pin": False},
                lineage_review={"status": "blocked", "feasibility": {"unexposed_structural_component_count": 0}})
    results = {"native": {"positive_certificates_accepted": 1024, "certificate_mutations_rejected": 280},
               "native_worker": {}, "reference_build": {}, "reference_results": {"case_count": 1321, "status": "passed"},
               "cold": _ledger(plan)}
    calls = []
    monkeypatch.setattr(r, "build_conformance_cases", lambda: ())
    monkeypatch.setattr(r, "validate_native_evidence", lambda *args: calls.append("native"))
    monkeypatch.setattr(r, "validate_build_receipt", lambda *args: calls.append("build"))
    monkeypatch.setattr(r, "validate_reference_results", lambda *args: calls.append("reference"))
    report = {"summary": r.review_summary(plan, results)}
    r.validate_saved_results(plan, report, results)
    assert calls == ["native", "build", "reference"]
    report["summary"]["reference_cases_matched"] += 1000
    with pytest.raises(ValueError, match="summary"):
        r.validate_saved_results(plan, report, results)


@pytest.mark.parametrize("mutation", ["stdin", "command", "returncode", "output_hash", "stderr", "native_count", "native_claim"])
def test_saved_native_worker_is_checked_not_just_its_favorable_summary(mutation):
    plan = _plan()
    plan["conformance"] = {"manifest_sha256": "f" * 64}
    cases = r.build_conformance_cases()[:1]
    native = r.check_native_cases(cases)
    request = canonical(r._request(plan, "native", case_manifest_sha256="f" * 64))
    worker = _process(canonical(native).decode() + "\n", request, r.NATIVE_LIMITS)
    r.validate_native_evidence(plan, native, worker, cases)
    if mutation == "stdin":
        worker["stdin_sha256"] = "0" * 64
    elif mutation == "command":
        worker["command"][-1] = "--plan"
    elif mutation == "returncode":
        worker["returncode"] = 1
    elif mutation == "output_hash":
        worker["stdout_sha256"] = "0" * 64
    elif mutation == "stderr":
        worker.update(stderr="unexpected warning", stderr_bytes=18,
                      stderr_sha256=sha256(b"unexpected warning").hexdigest())
    else:
        if mutation == "native_count":
            native["positive_certificates_accepted"] += 1
        else:
            native["independent_reference_checked"] = True
        _seal(native, "report_sha256")
        worker = _process(canonical(native).decode() + "\n", request, r.NATIVE_LIMITS)
    with pytest.raises(ValueError):
        r.validate_native_evidence(plan, native, worker, cases)


def test_archive_verification_rechecks_live_plan_after_fresh_work(monkeypatch, tmp_path):
    plan = _plan()
    plan.update(conformance={"distinct_positive_formula_count": 0},
                reference={"matches_project_toolchain_pin": False},
                lineage_review={"status": "blocked", "feasibility": {"unexposed_structural_component_count": 0}})
    _seal(plan, "plan_sha256")
    results = {"native": {"positive_certificates_accepted": 0, "certificate_mutations_rejected": 0},
               "native_worker": {}, "reference_build": {"axiom_footprint": {}, "compiled_files": {}},
               "reference_results": {"case_count": 0, "status": "passed", "cases": []}, "cold": _ledger(plan)}
    def write(name, raw):
        (tmp_path / name).write_bytes(raw)
        return {"path": name, "bytes": len(raw), "sha256": sha256(raw).hexdigest()}
    report = _header()
    report.update(plan=write("plan.json", canonical(plan)), cases=write("cases.jsonl", b""),
                  plan_sha256=plan["plan_sha256"], summary=r.review_summary(plan, results),
                  evidence={name: write(f"{name}.json", canonical(value)) for name, value in results.items()})
    write("report.json", canonical(_seal(report, "report_sha256")))
    events = []
    monkeypatch.setattr(r, "build_conformance_cases", lambda: ())
    monkeypatch.setattr(r, "validate_plan", lambda *args, **kwargs: events.append("live-audit"))
    monkeypatch.setattr(r, "validate_saved_results", lambda *args: events.append("saved-validation"))
    def fresh(*args, **kwargs):
        events.append("fresh-work")
        return deepcopy(results)
    monkeypatch.setattr(r, "_execute_checks", fresh)
    verified = r.verify_review(tmp_path)
    assert verified["status"] == "passed" and verified["cold_positive_receipts_reproduced"] == 4
    assert events == ["live-audit", "saved-validation", "fresh-work", "live-audit"]


def _cli():
    spec = importlib.util.spec_from_file_location("hydra_review_cli_fixture", ROOT / "scripts/check_peano_hydra_review.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("option", [
    ["--cold-scope", "sample"], ["--cold-batch-size=1"], ["--cold-wall-budget", "900"],
    ["--reference-project", "unused"], ["--development-directory", "unused"], ["--full-plan"],
    ["--lean-binary", "/unused/lean"], ["--output-dir", "unused"], ["--allocations", "unused"],
])
def test_verify_cli_refuses_silently_ignored_plan_overrides(option, monkeypatch, capsys):
    module = _cli()
    monkeypatch.setattr(module, "verify_review", lambda *args, **kwargs: pytest.fail("invalid override reached verifier"))
    assert module.main(["--verify", "unused", *option]) == 2
    assert "frozen plan" in capsys.readouterr().err


def test_internal_worker_cli_cannot_mix_interactive_planning_flags(monkeypatch, capsys):
    module = _cli()
    monkeypatch.setattr(module, "worker", lambda *args: pytest.fail("invalid mixed worker command"))
    assert module.main(["--worker", "--cold-scope", "full"]) == 2
    assert "bounded stdin request" in capsys.readouterr().err
