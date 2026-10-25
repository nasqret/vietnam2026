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
from training.peano_hydra import review_v28 as r  # noqa: E402
from training.peano_hydra.cold_replay_v28 import cold_target_record, fingerprint_certificate  # noqa: E402
from training.peano_hydra.epoch import EpochTheorem  # noqa: E402
from training.peano_hydra.frontier import canonical, digest  # noqa: E402
from training.peano_hydra.review_runtime import RESOURCE_MEASUREMENT  # noqa: E402
from training.peano_hydra import review_sources_v28 as sources
from training.peano_hydra.epoch import freeze_epoch


def _seal(record, field="receipt_sha256"):
    record.pop(field, None)
    record[field] = digest(record)
    return record


def _plan(*, batch_size=1, scope="full", budget=900):
    targets = [cold_target_record(EpochTheorem(
        r.HOTSPOT_NAMES[index], "0 = 0", sha256(b"0 = 0").hexdigest(), ("refl",),
        sha256(b"refl\n").hexdigest(), (), "stable", index,
    )) for index in range(2)]
    cold = {"targets": targets, "selected_targets": {str(i): target for i, target in enumerate(targets)}, "target_count": 2, "edition_identity_sha256": "b" * 64,
            "certificate_limits": r.CertificateLimits().to_dict(), "batch_size": batch_size,
            "batches": [list(range(start, min(2, start + batch_size))) for start in range(0, 2, batch_size)]}
    return {"mode": "native-hotspots", "source": {"fixture": True}, "execution_root": str(r.ROOT), "epoch_sha256": "a" * 64,
            "profile": {"profile_sha256": "c" * 64}, "cold_plan": cold,
            "ancillary_inputs": r.ancillary_input_closure("native-hotspots"),
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
    return {"command": list(r._worker_command(str(r.ROOT))), "limits": limits.to_dict(),
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
    return _refresh(plan, {"schema": r.COLD_LEDGER_SCHEMA, "execution_root": plan["execution_root"], "batches": batches, "rows": [],
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
    assert ledger["summary"]["full_epoch_replayed_twice"] is False
    assert ledger["summary"]["matching_complete_selected_passes"] is True
    assert r.compare_cold_reproduction(plan, ledger, deepcopy(ledger)) == 4


def test_sample_never_becomes_a_full_epoch_gate():
    plan = _plan(scope="hotspots")
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


@pytest.fixture(scope="module")
def real_plan():
    # Metadata only; dirty sources are explicitly allowed to draft but not run.
    return r.build_review_plan(mode="native-hotspots")


def test_actual_plan_has_no_lean_or_human_readiness_and_exact_hotspot_budget(real_plan):
    r.validate_plan(real_plan, live_sources=False)
    assert real_plan["cold_selection"]["indices"] == [1108, 1940]
    assert real_plan["worker_reservations"]["workers"] == 4
    assert real_plan["worker_reservations"]["sum_worker_cpu_seconds"] == 120
    assert real_plan["worker_reservations"]["sum_worker_wall_seconds"] == 180
    assert real_plan["reference"] is None
    assert real_plan["whole_controller_guard"]["implemented_by_this_controller"] is False
    assert all(real_plan[key] is False for key in r.FALSE_CLAIMS)


@pytest.mark.parametrize("change", ["epoch", "h0", "cpu", "guard", "order", "body", "omission", "ancillary_inputs"])
def test_resealed_actual_plan_cannot_change_inventory_scope_or_budgets(real_plan, change):
    changed = deepcopy(real_plan)
    if change == "epoch":
        changed["epoch_sha256"] = "0" * 64
    elif change == "h0":
        changed["h0_complete"] = True
    elif change == "cpu":
        changed["worker_reservations"]["sum_worker_cpu_seconds"] += 1
    elif change == "guard":
        changed["whole_controller_guard"]["implemented_by_this_controller"] = True
    elif change == "order":
        changed["cold_plan"]["targets"].reverse()
    elif change == "body":
        changed["cold_plan"]["selected_targets"]["1108"]["script"].append("refl")
    elif change == "ancillary_inputs":
        changed["ancillary_inputs"]["files"].pop(next(iter(changed["ancillary_inputs"]["files"])))
        _seal(changed["ancillary_inputs"], "input_closure_sha256")
    else:
        changed["cold_plan"]["targets"].pop()
    _seal(changed, "plan_sha256")
    with pytest.raises(ValueError):
        r.validate_plan(changed, live_sources=False)


def test_full_plan_cannot_allocate_or_create_output(monkeypatch, tmp_path):
    monkeypatch.setattr(r, "validate_plan", lambda *a, **k: pytest.fail("full run reached validation/work"))
    monkeypatch.setattr(r, "run_bounded", lambda *a, **k: pytest.fail("full run spawned a worker"))
    output = tmp_path / "never-created"
    with pytest.raises(ValueError, match="envelope"):
        r.execute_review({"mode": "full-plan-only"}, output)
    with pytest.raises(ValueError, match="envelope"):
        r.run_cold({"mode": "full-plan-only", "cold_selection": {"scope": "full"}})
    assert not output.exists()


@pytest.mark.parametrize("version,pin,matches", [
    ("4.28.0", "leanprover/lean4:v4.31.0", False),
    ("4.28.0", "leanprover/lean4:v4.28.0", True),
    ("4.31.0-rc1", "leanprover/lean4:v4.31.0", True),
])
def test_v28_reference_cannot_relabel_older_or_release_candidate_compiler(monkeypatch, version, pin, matches):
    monkeypatch.setattr(r, "validate_reference_identity", lambda identity: None)
    with pytest.raises(ValueError, match="4.31.0"):
        r._reference_v28({"compiler_version": f"Lean (version {version}, fixture)",
                          "project_toolchain_pin": pin, "matches_project_toolchain_pin": matches})


def test_v28_reference_accepts_exact_version_only_as_metadata(monkeypatch):
    monkeypatch.setattr(r, "validate_reference_identity", lambda identity: None)
    r._reference_v28({"compiler_version": "Lean (version 4.31.0, test-only)",
                      "project_toolchain_pin": "leanprover/lean4:v4.31.0", "matches_project_toolchain_pin": True})


def test_dirty_plan_cannot_create_an_execution_archive(real_plan, tmp_path):
    if real_plan["source"]["git_dirty"] is not True:
        pytest.skip("draft worktree is already independently frozen")
    with pytest.raises(ValueError, match="clean committed"):
        r.execute_review(real_plan, tmp_path / "never-created")
    assert not (tmp_path / "never-created").exists()


def test_worker_receipts_are_retained_before_any_decoder_failure(monkeypatch, tmp_path):
    plan = _plan(scope="hotspots")
    observed = {"malformed": "synthetic failed worker output"}
    monkeypatch.setattr(r, "check_ancillary_inputs", lambda *a, **k: {})
    monkeypatch.setattr(r, "run_bounded", lambda *a, **k: observed)
    with pytest.raises(ValueError):
        r.run_cold(plan, archive=tmp_path)
    assert r.read_record(tmp_path / "cold-worker-pass-1-batch-0.json") == observed


def test_output_is_fresh_and_symlink_ancestors_are_rejected(tmp_path):
    existing = tmp_path / "existing"
    existing.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(existing, target_is_directory=True)
    for path in (existing, alias, alias / "new"):
        with pytest.raises(ValueError):
            r._fresh_directory(path)
    assert not (existing / "new").exists()


def _cli():
    spec = importlib.util.spec_from_file_location("review_v28_cli_test", r.SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("extra", [["--mode", "native-hotspots"], ["--cold-wall-budget=3600"], ["--full-plan"]])
def test_cli_rejects_plan_overrides_during_saved_execution(extra, tmp_path, monkeypatch):
    cli = _cli()
    monkeypatch.setattr(cli, "execute_review", lambda *a, **k: pytest.fail("execution reached"))
    assert cli.main(["--run", "--plan-file", "missing", "--plan-sha256", "a" * 64,
                     "--output-dir", str(tmp_path / "out"), *extra]) == 2


def test_cli_requires_exact_raw_plan_pin_before_execution(tmp_path, monkeypatch):
    cli = _cli()
    plan = tmp_path / "plan.json"
    plan.write_text('{"mode":"native-hotspots"}\n')
    monkeypatch.setattr(cli, "execute_review", lambda *a, **k: pytest.fail("unmatched plan executed"))
    assert cli.main(["--run", "--plan-file", str(plan), "--plan-sha256", "0" * 64,
                     "--output-dir", str(tmp_path / "out")]) == 2


def test_v28_source_inventory_explicitly_includes_its_cli_and_new_controller():
    assert "scripts/check_peano_hydra_review_v28.py" in sources.SCRIPTS
    assert {f"training/peano_hydra/{name}.py" for name in
            ("review_v28", "review_sources_v28", "review_inputs_v28", "cold_replay_v28")} <= sources.REQUIRED_FILES


def test_v28_source_receipt_cannot_omit_or_reseal_modified_cli(tmp_path, monkeypatch):
    import os
    import subprocess
    repository = tmp_path / "source"
    repository.mkdir()
    for name in sources.REQUIRED_FILES:
        path = repository / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# synthetic source: {name}\n")
    environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    environment.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
    base = ["git", "-C", str(repository), "-c", "user.name=V28 fixture", "-c", "user.email=fixture@example.invalid",
            "-c", "commit.gpgsign=false", "-c", f"core.hooksPath={os.devnull}"]
    for arguments in (["init", "-q"], ["add", "--all"], ["commit", "-q", "-m", "Synthetic fixture"]):
        subprocess.run([*base, *arguments], check=True, capture_output=True, timeout=5, env=environment)
    monkeypatch.setattr(sources, "ROOT", repository)
    identity = sources.source_identity()
    sources.validate_sources(identity)
    cli = sources.SCRIPT.as_posix()
    omitted = deepcopy(identity)
    omitted["files"].pop(cli)
    omitted["files_sha256"] = sources._digest(omitted["files"])
    with pytest.raises(ValueError, match="omits"):
        sources.validate_sources(omitted)
    (repository / cli).write_text("# changed after original commit\n")
    changed = deepcopy(identity)
    body = (repository / cli).read_bytes()
    changed["files"][cli] = {"bytes": len(body), "sha256": sha256(body).hexdigest()}
    changed["files_sha256"] = sources._digest(changed["files"])
    with pytest.raises(ValueError, match="Git blob"):
        sources.validate_sources(changed)
