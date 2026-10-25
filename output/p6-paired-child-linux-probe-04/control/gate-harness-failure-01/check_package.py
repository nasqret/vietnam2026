"""CPU04 file/AST and pure binding gate; never execute a probe or source module."""
import ast
import base64
import copy
import hashlib
import json
import os
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
PACKAGE = HERE.parent
PREVIOUS = PACKAGE.with_name("p6-paired-child-linux-probe-03")
SOURCE = Path("output/hydra-implementation-2026-09-04/combined-source-bundle-07").resolve()


def pin(path):
    raw = path.read_bytes()
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def form(node):
    return ast.dump(node, include_attributes=False)


def defs(tree):
    return {x.name: x for x in tree.body if isinstance(x, (ast.FunctionDef, ast.ClassDef))}


def assigns(tree):
    return {x.targets[0].id: x.value for x in tree.body if isinstance(x, ast.Assign)
            and len(x.targets) == 1 and isinstance(x.targets[0], ast.Name)}


def extract(nodes, namespace):
    module = ast.fix_missing_locations(ast.Module(body=copy.deepcopy(nodes), type_ignores=[]))
    exec(compile(module, "<pure-cpu04-extract>", "exec"), namespace)


def reject(call):
    try:
        call()
    except (ValueError, KeyError):
        return
    raise AssertionError("Invalid in-memory input was accepted.")


def run():
    old_paths = [PREVIOUS / name for name in ("manifest.json", "run_probe.py", "paired_case_worker.py",
        "paired_controller.py", "paired_common.py", "job.sh", "control/PREPARED.json",
        "observation-001/result.json", "observation-001/actual-completion.json")]
    before = {str(path): pin(path) for path in old_paths}
    manifest = json.loads((PACKAGE / "manifest.json").read_bytes())
    remote = ast.parse((HERE / "remote_probe_control.py").read_text())
    old_remote = ast.parse((PREVIOUS / "control/remote_probe_control.py").read_text())
    current, previous = defs(remote), defs(old_remote)
    assert set(current) == set(previous)
    changed = {name for name in current if form(current[name]) != form(previous[name])}
    assert changed == {"verify_sources", "decode_uploads"}
    # Upload admission differs only in the error text; the finite copy/stage,
    # ownership, byte limits, scheduler, transport and collection bodies match.
    upload_copy = copy.deepcopy(current["decode_uploads"])
    upload_copy.body[1].value.args[1].value = previous["decode_uploads"].body[1].value.args[1].value
    assert form(upload_copy) == form(previous["decode_uploads"])
    globals_, old_globals = assigns(remote), assigns(old_remote)
    assert set(globals_) - set(old_globals) == {"SOURCE_SCHEMA"}
    assert {name for name in old_globals if form(globals_[name]) != form(old_globals[name])} == {
        "PACKAGE", "SOURCE", "SOURCE_MANIFEST", "JOB_NAME", "PINS", "UPLOADS", "COPIES"}
    assert (HERE / "probe_control.py").read_bytes() == (PREVIOUS / "control/probe_control.py").read_bytes()
    pins, uploads, copies = (ast.literal_eval(globals_[name]) for name in ("PINS", "UPLOADS", "COPIES"))
    assert set(uploads) == {"run_probe.py", "paired_case_worker.py", "job.sh", "manifest.json"}
    assert copies == ("paired_common.py", "paired_controller.py")
    assert manifest["files"] == {name: desc for name, desc in pins.items() if name != "manifest.json"}
    for name, expected in pins.items():
        assert pin(PACKAGE / name) == expected
        if name.endswith(".py"):
            ast.parse((PACKAGE / name).read_text())
    source_pin = ast.literal_eval(globals_["SOURCE_MANIFEST"])
    assert pin(SOURCE / "manifest.json") == source_pin == {k: manifest["source_copy"]["source_manifest"][k] for k in ("bytes", "sha256")}
    source_manifest = json.loads((SOURCE / "manifest.json").read_bytes())
    source_control = ast.literal_eval(globals_["SOURCE_CONTROL"])
    for name in copies:
        assert pin(SOURCE / "source" / source_control / name) == pins[name]
        assert source_manifest["files"][source_control + "/" + name] == pins[name]
    assert pin(PACKAGE.with_name("p6-paired-child-monitor-fix-03") / "paired_controller.py") == pins["paired_controller.py"]
    assert manifest["controller_origin"]["sha256"] == pins["paired_controller.py"]["sha256"]
    for key in ("prepared", "pure_gate"):
        descriptor = manifest["controller_origin"][key]
        assert pin(Path(descriptor["path"])) == {k: descriptor[k] for k in ("bytes", "sha256")}
    assert pin(Path(manifest["selection"]["path"])) == {k: manifest["selection"][k] for k in ("bytes", "sha256")}

    namespace = {"hashlib": hashlib, "base64": base64, "json": json, "PINS": pins,
        "UPLOADS": uploads, "COPIES": copies, "SOURCE_MANIFEST": source_pin,
        "SOURCE_SCHEMA": ast.literal_eval(globals_["SOURCE_SCHEMA"]), "SOURCE": SOURCE / "source",
        "SOURCE_CONTROL": source_control}
    extract([current[name] for name in ("require", "digest", "pin", "decode_uploads", "verify_sources")], namespace)
    uploaded = {name: (PACKAGE / name).read_bytes() for name in uploads}
    encoded = {name: base64.b64encode(raw).decode("ascii") for name, raw in uploaded.items()}
    assert namespace["decode_uploads"](encoded) == uploaded
    reject(lambda: namespace["decode_uploads"]({name: raw for name, raw in encoded.items() if name != "job.sh"}))
    reject(lambda: namespace["decode_uploads"](dict(encoded, unlisted="")))
    reject(lambda: namespace["decode_uploads"](dict(encoded, **{"job.sh": base64.b64encode(b"bad").decode()})))
    # Exercise source identity and both copied-file pins using supplied memory
    # bytes; the owned-file I/O itself stays AST-identical to CPU03.
    memory = {SOURCE / "manifest.json": (SOURCE / "manifest.json").read_bytes()}
    memory.update({SOURCE / "source" / source_control / name: (PACKAGE / name).read_bytes() for name in copies})
    namespace.update(owned_directory=lambda path: None, owned_bytes=lambda path, bound: memory[path])
    expected_copies = {name: (PACKAGE / name).read_bytes() for name in copies}
    assert namespace["verify_sources"]() == expected_copies
    for name in copies:
        path = SOURCE / "source" / source_control / name
        original = memory[path]
        memory[path] = original + b"x"
        reject(namespace["verify_sources"])
        memory[path] = original
    original = memory[SOURCE / "manifest.json"]
    memory[SOURCE / "manifest.json"] = original + b" "
    reject(namespace["verify_sources"])
    memory[SOURCE / "manifest.json"] = original
    request = {"schema": "hydra-child-linux-monitor-control-request-v1", "phase": "stage", "nonce": "0" * 32,
        "manifest_sha256": pins["manifest.json"]["sha256"], "remote_control_sha256": pin(HERE / "remote_probe_control.py")["sha256"], "uploads": encoded}
    wire_bytes = len(json.dumps(request, sort_keys=True, separators=(",", ":"), allow_nan=False).encode())
    assert wire_bytes <= 131072
    run_files = eval(compile(ast.Expression(globals_["RUN_FILES"]), "<fixed-collection-whitelist>", "eval"), {})
    assert len(run_files) == 22 and len(run_files) + 3 == 25
    assert {"case-00/query-batch-%02d.jsonl" % i for i in range(16)} <= run_files
    assert 16 + 4 == 20 <= 32

    probe = ast.parse((PACKAGE / "run_probe.py").read_text())
    old_probe = ast.parse((PREVIOUS / "run_probe.py").read_text())
    probe_defs, old_probe_defs = defs(probe), defs(old_probe)
    assert set(probe_defs) == set(old_probe_defs)
    assert {name for name in probe_defs if form(probe_defs[name]) != form(old_probe_defs[name])} == {"SamplerObservation", "run"}
    probe_globals = assigns(probe)
    assert form(probe_globals["LIMITS"]) == form(assigns(old_probe)["LIMITS"])
    limits = eval(compile(ast.Expression(probe_globals["LIMITS"]), "<fixed-limits>", "eval"), {"QUERIES": 64})
    assert limits == manifest["limits"] and limits["nominal_aggregate_cpu_hard_seconds"] == 23
    assert limits["shared_child_cpu_budget_seconds"] == 18 and limits["aggregate_cpu_seconds"] == 24
    worker = ast.parse((PACKAGE / "paired_case_worker.py").read_text())
    old_worker = ast.parse((PREVIOUS / "paired_case_worker.py").read_text())
    assert {k: form(v) for k, v in defs(worker).items()} == {k: form(v) for k, v in defs(old_worker).items()}
    assert {k for k in assigns(worker) if form(assigns(worker)[k]) != form(assigns(old_worker)[k])} == {"JOB_NAME"}
    assert not any(isinstance(x, ast.keyword) and x.arg == "preexec_fn" for x in ast.walk(worker))
    assert (PACKAGE / "job.sh").read_bytes() == (PREVIOUS / "job.sh").read_bytes()

    # Exercise only the new observation wrapper with an inert delegated
    # callable. No monitor function, proc read, process or source module runs.
    calls = []
    marker = object()
    delegate = lambda *args, **kwargs: calls.append((args, kwargs)) or 123
    monitor = SimpleNamespace(proc_read=lambda *args: (_ for _ in ()).throw(AssertionError("No proc I/O")), sample_scheduler_child=delegate)
    pure = {"os": os, "hashlib": hashlib, "LIMITS": limits, "QUERIES": 64,
            "canonical": lambda value: json.dumps(value, sort_keys=True, separators=(",", ":")).encode()}
    extract([probe_defs["SamplerObservation"]], pure)
    observer = pure["SamplerObservation"](monitor)
    args, kwargs = (11, 10, "1", "/fixed/scontrol"), {"parent_argv": b"owned-parent\0", "pending": marker}
    assert observer.child(*args, **kwargs) == 123 and calls == [(args, kwargs)]
    assert observer.pids == {11} and observer.observation_errors == 0 and not observer.limit_exceeded
    assert "parent_argv" not in observer.traces[0] and not observer.authenticated_fork_observed
    raised = ValueError("delegate-marker")
    observer.original_child = lambda *args, **kwargs: (_ for _ in ()).throw(raised)
    try:
        observer.child(12, *args[1:], **kwargs)
    except ValueError as error:
        assert error is raised
    else:
        raise AssertionError("Delegate failure was hidden.")
    assert observer.pids == {11, 12} and observer.traces[-1]["result_kind"] == "raised"
    trace = {"leader": 10, "candidate_parent_argv_sha256": "abc", "reads": [
        {"kind": "stat", "flags": "64", "ppid": "10", "pgid": "10", "sid": "10", "start_ticks": "20"},
        {"kind": "stat", "flags": "64", "ppid": "10", "pgid": "10", "sid": "10", "start_ticks": "20"},
        {"kind": "status", "uid_matches": True, "rss_fields": 1},
        {"kind": "children", "empty": True}, {"kind": "cmdline", "inherited_parent_argv_matches": True}]}
    fork = {"pending_kind": "fork", "fork_flag_observed": True, "parent_argv_sha256": "abc"}
    assert observer.fork_observed(fork, trace)
    fork_rejections = 0
    for index, key, value in ((0, "flags", "0"), (1, "start_ticks", "21"), (2, "uid_matches", False),
                              (2, "rss_fields", 0), (3, "empty", False), (4, "inherited_parent_argv_matches", False)):
        bad = copy.deepcopy(trace)
        bad["reads"][index][key] = value
        assert not observer.fork_observed(fork, bad)
        fork_rejections += 1
    for key, value in (("pending_kind", "exit"), ("fork_flag_observed", False), ("parent_argv_sha256", "bad")):
        assert not observer.fork_observed(dict(fork, **{key: value}), trace)
        fork_rejections += 1

    # The actual report expressions must keep an observed, unrecorded child
    # in the lower bound without claiming a complete scheduler-launch count.
    final = next(node.finalbody for node in probe_defs["run"].body if isinstance(node, ast.Try) and node.finalbody)
    selected = {"recorded_launch_pids", "observed_child_pids", "completed_query_records", "launch_accounting_complete"}
    counter_nodes = [node for node in final if isinstance(node, ast.Assign) and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name) and node.targets[0].id in selected]
    assert len(counter_nodes) == 4
    result_dict = next(node.value for node in final if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "result" for target in node.targets))
    fields = {"actual_scheduler_launches", "scheduler_launch_accounting_complete", "query_record_count",
              "completed_query_record_count", "recorded_query_launches", "observed_child_count", "query_process_launch_lower_bound"}
    pairs = [(key, value) for key, value in zip(result_dict.keys, result_dict.values) if key.value in fields]
    counter_expression = ast.Expression(ast.Dict(keys=[key for key, _ in pairs], values=[value for _, value in pairs]))
    queries = [{"pid": index + 100, "passed": True, "actual_launches": 1, "actual_exit_code": 0,
        "reaped": True, "natural_exit_observed": True, "forced_signal": False} for index in range(64)]
    counters = {"QUERIES": 64, "queries": queries, "passed": True,
                "observer": SimpleNamespace(pids={row["pid"] for row in queries})}
    extract(counter_nodes, counters)
    complete = eval(compile(counter_expression, "<pure-counter-fields>", "eval"), counters)
    assert complete["actual_scheduler_launches"] == 64 and complete["scheduler_launch_accounting_complete"] is True
    assert all(value == 64 for key, value in complete.items() if key != "scheduler_launch_accounting_complete")
    counters.update(queries=queries[:47], passed=False, observer=SimpleNamespace(pids=set(range(100, 148))))
    extract(counter_nodes, counters)
    incomplete = eval(compile(counter_expression, "<pure-counter-fields>", "eval"), counters)
    assert incomplete["actual_scheduler_launches"] is None and incomplete["scheduler_launch_accounting_complete"] is False
    assert incomplete["query_record_count"] == incomplete["completed_query_record_count"] == incomplete["recorded_query_launches"] == 47
    assert incomplete["observed_child_count"] == incomplete["query_process_launch_lower_bound"] == 48

    contract = json.loads((PACKAGE / "ACTUAL_COMPLETION_CONTRACT.json").read_bytes())
    assert contract["required_observed_variable_fields"]["manifest_sha256"] == pins["manifest.json"]["sha256"]
    assert contract["required_observed_variable_fields"]["controller_sha256"] == pins["paired_controller.py"]["sha256"]
    assert contract["source_copy"] == manifest["source_copy"] and contract["selection"] == manifest["selection"]
    assert all(pin(Path(path)) == desc for path, desc in before.items())
    assert not (HERE / "attempt").exists() and not (HERE / ".phase.lock").exists()
    print(json.dumps({"passed": True, "scope": "file_ast_and_pure_cpu04_binding_observer_only",
        "encoded_request_bytes": wire_bytes, "request_byte_ceiling": 131072,
        "uploaded_bytes": sum(map(len, uploaded.values())), "payload_bytes": sum(x["bytes"] for x in pins.values()),
        "normal_copy_files": list(copies), "query_count": 64, "query_batch_files": 16,
        "case_file_count_including_execution": 20, "fixed_collected_paths": 25,
        "malformed_upload_rejections": 3, "source_copy_pin_rejections": 3,
        "fork_observation_rejections": fork_rejections, "exact_argument_return_exception_forwarding": True,
        "incomplete_launch_count_lower_bound_checked": True,
        "local_control_unchanged": True, "remote_function_delta": sorted(changed),
        "worker_function_bodies_unchanged": True, "limits_unchanged": True,
        "cpu03_inputs_unchanged": True, "source_modules_imported": False, "monitor_tests_repeated": False,
        "network_or_proc_or_process_calls": 0, "runtime_probe_executed": False,
        "synthetic_completion_receipts_written": False}, sort_keys=True))


if __name__ == "__main__":
    run()
