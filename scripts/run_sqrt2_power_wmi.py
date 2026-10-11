#!/usr/bin/env python3
"""One AP090 Slurm pilot, explicit cluster resources, unchanged proof checks."""
import argparse
import gzip
from hashlib import sha256
import json
import os
from pathlib import Path
import platform
import sys
import time

from package_sqrt2_power_wmi import ROOT, PRODUCER_SHA256, verify_snapshot
import sqrt2_power_wmi_resources as resources

OBS = "research/arithmetic-library/sqrt2-power/observations/"
HA_FOLDER = OBS + "shared-wave-fixed-half-log-root-v1"
LEAN_FOLDER = OBS + "shared-wave-fixed-half-log-root-lean-wmi-v1"
LEAN = Path("/work/bnaskrecki/peano-lab-kernel/toolchains/lean-4.31.0-linux-"
    "07a633cc8d9151cbc08825ea4cdda50d4b02a2c9cb852c0131b13046f49cad7f/lean-4.31.0-linux/bin/lean")
TARGET = "41651cb7c7afc07ceb0eaeab7bf02392001a704ec0891d7bf1db0ed4aa33211f"


def run_wmi_wave(output, *, case="AP090"):
    """Use the unchanged producer and full replay in fresh bounded processes.

    This explicit WMI controller does not patch the historical local driver,
    its leaf budgets, its resource supervisor, or any kernel/certificate limits.
    """
    from run_sqrt2_power_pilot import save_new, successful, controller_deadline
    from sqrt2_power_automation_baseline import runtime
    import run_sqrt2_power_wave as wave
    resources.require_allocation()
    if output.exists() or output.is_symlink():
        raise ValueError("new HA observation directory required")
    if case not in {"AP090", "AP091", "AP092", "AP093", "AP094", "AP095"}:
        raise ValueError("unconfigured WMI proof case")
    target = wave.formula_sha256(wave.target_for(case))
    if case == "AP090" and target != TARGET:
        raise ValueError("historical AP090 target changed")
    before = wave.pins(case)
    started = time.monotonic()
    report = dict(schema=wave.SCHEMA, case=case, source_pins=before,
        source_snapshots={}, status="not_checked", IR_parents_closed=0,
        library_admissions=0, independent_lean_checked=False, model_proof_search_calls=0,
        authority="remote_observation_not_library_admission", resource_profile=resources.NAME,
        results={}, process_records={}, execution_controller_sources={},
        budget=dict(cpu_seconds=2*(resources.HA_PHASE[0]+1),
            wall_seconds=resources.HA_CONTROLLER_WALL, max_workers=1,
            rss_bytes=resources.WORKER_RSS_BYTES, reserved_cpu_seconds=0))
    def archive(name, pin, destination):
        raw = (ROOT/name).read_bytes()
        if len(raw) != pin["bytes"] or sha256(raw).hexdigest() != pin["sha256"]:
            raise ValueError("source changed before archival")
        save_new(output/destination, gzip.compress(raw, mtime=0))
    try:
        with controller_deadline(started+resources.HA_CONTROLLER_WALL):
            for name, pin in before.items():
                destination = "sources/"+name+".gz"
                archive(name, pin, destination)
                report["source_snapshots"][name] = destination
            for name in ("scripts/run_sqrt2_power_wmi.py", "scripts/sqrt2_power_wmi_resources.py"):
                pin = runtime().hash_file(ROOT/name)
                destination = "controller-sources/"+name+".gz"
                archive(name, pin, destination)
                report["execution_controller_sources"][name] = dict(pin, path=destination)
            value, input_bytes = None, b""
            for phase, option in (("generation", "--worker"), ("fresh_replay", "--replay")):
                command = (sys.executable, "-B", str(wave.SCRIPT), option, case)
                cpu, wall = resources.HA_PHASE
                limits = runtime().ProcessLimits(cpu_seconds=cpu, wall_seconds=wall,
                    rss_bytes=resources.WORKER_RSS_BYTES, output_bytes=8*1024**2)
                report["budget"]["reserved_cpu_seconds"] += cpu+1
                process = runtime().run_bounded(command, cwd=ROOT, limits=limits, input_bytes=input_bytes)
                runtime().validate_process_record(process, command=command, limits=limits, input_bytes=input_bytes)
                raw = wave.canonical(process)
                destination = phase+"-process.json.gz"
                save_new(output/destination, gzip.compress(raw, mtime=0))
                report["process_records"][phase] = dict(path=destination, raw_sha256=sha256(raw).hexdigest(),
                    reason=process["reason"], returncode=process["returncode"], resources=process["resources"])
                if not successful(process):
                    raise ValueError(phase+" did not finish successfully; no retry")
                parsed = json.loads(process["stdout"])
                expected = "native_generated" if phase == "generation" else "fresh_ordinary_HA_checked"
                if (parsed.get("schema") != wave.SCHEMA or parsed.get("case") != case
                        or parsed.get("status") != expected or parsed.get("source_pins") != before
                        or parsed.get("target_ast_sha256") != target):
                    raise ValueError("unbound original worker output")
                if phase == "generation":
                    value = parsed
                    input_bytes = wave.canonical(value)
                elif (parsed.get("bundle_sha256") != value["bundle_sha256"]
                        or not all(parsed.get(k) is True for k in ("original_target_checked", "empty_context",
                            "false_target_rejected", "forged_body_rejected"))):
                    raise ValueError("full fresh replay acceptance checks changed")
                report["results"][phase] = {k:v for k,v in parsed.items() if k != "bundle"}
            if wave.pins(case) != before:
                raise ValueError("proof sources changed during execution")
            report["status"] = "fresh_ordinary_HA_checked"
    except BaseException as error:
        report["exception"] = dict(type=type(error).__name__, message=str(error)[:2000])
    finally:
        report["elapsed_wall_seconds"] = time.monotonic()-started
        save_new(output/"report.json", json.dumps(report, sort_keys=True, indent=2).encode()+b"\n")
    return {key:report[key] for key in ("case", "status", "elapsed_wall_seconds", "process_records")}


def cost_preflight():
    """Actual row/size audit, not an ancestor proof or an acceptance shortcut."""
    import gc
    import sqrt2_power_fixed_half_log_root as p
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_binary_dag import BinaryDAGLimits, _body_metrics, _row_preflight
    from sqrt2_power_quadratic_trace_exists import _inert_metrics
    from peano_lab.library.proof_bundle import encode_formula, encode_proof
    registry = p.definition_registry()
    target = p.frozen_fixed_half_log_root_target(_registry=registry)
    limits = BinaryDAGLimits()
    endpoint_formulas = {name: encode_formula(parse_named(source, registry=registry))
        for name, source in p.ENDPOINT_SOURCES.items()}
    rows, keys, endpoints, owners = [], {}, {}, {}
    for pin in p.ARCHIVES:
        original, remap = p.read_mixed_archive(pin), {}
        for old, row in enumerate(original):
            if not all(type(d) is int and 0 <= d < old for d in row[2]):
                raise ValueError("invalid dependency order")
            linked = [row[0], row[1], [remap[d] for d in row[2]], row[3]]
            key = p.canonical(linked)
            if key not in keys:
                keys[key] = len(rows)
                rows.append(linked)
            remap[old] = keys[key]
        for name, formula in endpoint_formulas.items():
            if p.ENDPOINT_OWNERS[name] != pin["case"]:
                continue
            matches = [i for i, row in enumerate(original) if row[1] == formula]
            if len(matches) != 1:
                raise ValueError("ambiguous original endpoint")
            endpoints[name], owners[name] = remap[matches[0]], [pin["case"], matches[0]]
        del original, remap
        gc.collect()
    body = p.introduce(p.Scope(), (), p.HELPER_DEPENDENCIES["AP090"], lambda s: p._root(s, registry))
    native = json.loads((ROOT / (OBS + "fixed-half-log-root-native-constructor-audit-v1.json")).read_bytes())
    prior = json.loads(native["stdout"])
    body_hash = p.json_hash(encode_proof(body))
    if (native["returncode"] != 0 or native["reason"] != "exited"
            or prior["producer_source_pin"]["sha256"] != PRODUCER_SHA256
            or sha256((ROOT / "scripts/sqrt2_power_fixed_half_log_root.py").read_bytes()).hexdigest() != PRODUCER_SHA256
            or prior["new_body"]["body_sha256"] != body_hash):
        raise ValueError("previous native check does not bind these actual constructor bytes")
    count, depth = _body_metrics(body, limits)
    _row_preflight(target, body, limits)
    rows.append([8 * count + 16, encode_formula(target),
        [endpoints[d] for d in p.HELPER_DEPENDENCIES["AP090"]], encode_proof(body)])
    reached, pending = set(), [len(rows) - 1]
    while pending:
        old = pending.pop()
        if old not in reached:
            reached.add(old)
            pending.extend(rows[old][2])
    retained = sorted(reached)
    remap = {old: new for new, old in enumerate(retained)}
    rows = [[rows[old][0], rows[old][1], [remap[d] for d in rows[old][2]], rows[old][3]] for old in retained]
    constructors = sum(_inert_metrics(row[3], limits)[0] for row in rows)
    raw = p.canonical(["peano-lab-bundle-v1", len(rows) - 1, encode_formula(target), rows]) + b"\n"
    if (len(raw) > limits.max_payload_bytes or constructors > limits.max_total_body_nodes
            or len(rows) > limits.max_nodes or rows[:p.UNIFORM_ARCHIVE["nodes"]] != p.read_mixed_archive(p.UNIFORM_ARCHIVE)):
        raise ValueError("changed AP089 prefix or exceeded original certificate bounds")
    pins = p.fixed_half_log_root_source_pins()
    if "peano_lab.library.theorems" in sys.modules:
        raise ValueError("unexpected full theorem registry import")
    return dict(status="passed", case="AP090", target_ast_sha256=p.TARGET_SHA256,
        new_body=dict(constructors=count, depth=depth, body_sha256=body_hash),
        actual_retained_nodes=len(rows), actual_retained_constructors=constructors,
        actual_canonical_bytes=len(raw), actual_bundle_sha256=sha256(raw).hexdigest(),
        all_583_AP089_rows_preserved=True, exact_owned_endpoints=owners,
        source_pin_count=len(pins), definition_count=len(registry), proof_authority=False)


def pilot(stage, evidence):
    from run_sqrt2_power_pilot import save_new, successful
    from sqrt2_power_automation_baseline import runtime
    import run_sqrt2_power_wave as wave
    import check_sqrt2_power_fresh_lean as fresh
    resources.require_allocation()
    if (wave.generation_phase_limits("AP090") != (28, 40)
            or wave.replay_phase_limits("AP090") != (30, 40)):
        raise ValueError("AP090 approved phase limits changed")
    if evidence.exists() or evidence.is_symlink():
        raise ValueError("new pilot evidence directory required")
    evidence.mkdir()
    report = dict(schema="sqrt2-power-wmi-pilot-v2", case="AP090", status="not_checked",
        job_id=os.environ["SLURM_JOB_ID"], host=platform.node(), python=sys.version,
        source_snapshot_sha256=os.environ["PEANO_SQRT2_SNAPSHOT_SHA256"],
        authority="remote_observation_not_library_admission", IR_parents_closed=0,
        library_admissions=0, full_attempt_started=False, max_workers=1,
        requested=dict(resources.REQUESTED), resource_profile=resources.NAME,
        predecessor_job_id="257867", node_local_scratch=True,
        source_root=str(ROOT), evidence_root=str(evidence))
    started = time.monotonic()
    try:
        report["snapshot_before"] = verify_snapshot(stage)
        tests = (sys.executable, "-B", "-m", "unittest", "discover", "-s", "scripts",
            "-p", "test_sqrt2_power_wmi.py", "-v")
        test_limits = runtime().ProcessLimits(cpu_seconds=25, wall_seconds=35,
            rss_bytes=512*1024**2, output_bytes=1024**2)
        test_process = runtime().run_bounded(tests, cwd=ROOT, limits=test_limits)
        runtime().validate_process_record(test_process, command=tests, limits=test_limits)
        report["migration_tests"] = test_process
        if not successful(test_process):
            raise ValueError("migration regression tests failed; full attempt not started")
        command = (sys.executable, "-B", str(Path(__file__).resolve()), "--cost-preflight")
        limits = runtime().ProcessLimits(cpu_seconds=resources.PREFLIGHT_PHASE[0], wall_seconds=resources.PREFLIGHT_PHASE[1],
            rss_bytes=1024**3, output_bytes=65536)
        process = runtime().run_bounded(command, cwd=ROOT, limits=limits)
        runtime().validate_process_record(process, command=command, limits=limits)
        report["preflight"] = process
        save_new(evidence / "constructor-cost-process.json", json.dumps(process, sort_keys=True, indent=2).encode()+b"\n")
        if not successful(process):
            raise ValueError("constructor-cost preflight failed; full attempt not started")
        cost = json.loads(process["stdout"])
        if cost["status"] != "passed" or cost["target_ast_sha256"] != TARGET:
            raise ValueError("preflight target changed")
        report["cost"] = cost
        save_new(evidence / "AP090-attempt-started.json", json.dumps(dict(case="AP090",
            job_id=report["job_id"], source_snapshot_sha256=report["source_snapshot_sha256"])).encode()+b"\n")
        report["full_attempt_started"] = True
        report["ha"] = run_wmi_wave(ROOT / HA_FOLDER)
        if report["ha"]["status"] != "fresh_ordinary_HA_checked":
            raise ValueError("full AP090 HA attempt did not pass; no automatic retry")
        ha = json.loads((ROOT / HA_FOLDER / "report.json").read_bytes())
        if ha["results"]["fresh_replay"]["bundle_sha256"] != cost["actual_bundle_sha256"]:
            raise ValueError("full certificate differs from actual preflight rows")
        report["lean"] = fresh.execute(ROOT / LEAN_FOLDER, [ROOT / HA_FOLDER],
            lean=LEAN, lean_repo=stage / "lean", resource_profile=resources.NAME)
        if report["lean"]["status"] != "fresh_lean_checked":
            raise ValueError("independent fresh Lean did not pass")
        report["status"] = "HA_and_fresh_Lean_checked"
    except BaseException as error:
        report["status"] = "failed_or_incomplete"
        report["exception"] = dict(type=type(error).__name__, message=str(error)[:2000])
    finally:
        try:
            report["snapshot_after"] = verify_snapshot(stage)
            if report.get("snapshot_before") != report["snapshot_after"]:
                raise ValueError("snapshot boundary changed during pilot")
        except BaseException as error:
            report["status"] = "failed_or_incomplete"
            report["snapshot_exception"] = dict(type=type(error).__name__, message=str(error)[:2000])
        report["elapsed_wall_seconds"] = time.monotonic() - started
        save_new(evidence / "pilot-report.json", json.dumps(report, sort_keys=True, indent=2).encode()+b"\n")
    print(json.dumps({k: report[k] for k in ("case", "status", "job_id", "full_attempt_started", "elapsed_wall_seconds")}), flush=True)
    return report["status"] == "HA_and_fresh_Lean_checked"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cost-preflight", action="store_true")
    parser.add_argument("--stage", type=Path)
    parser.add_argument("--evidence", type=Path)
    args = parser.parse_args()
    if args.cost_preflight:
        print(json.dumps(cost_preflight(), sort_keys=True))
    else:
        if args.stage is None or args.evidence is None:
            parser.error("pilot requires explicit snapshot and evidence paths")
        raise SystemExit(0 if pilot(args.stage.resolve(), args.evidence.resolve()) else 1)
