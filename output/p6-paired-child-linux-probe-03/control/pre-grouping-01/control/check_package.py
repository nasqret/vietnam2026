"""Bounded file/AST and pure admission gate; no process, /proc or network calls."""
import ast
import base64
import copy
import hashlib
import json
import math
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
PAYLOAD = HERE.parent
PREVIOUS = PAYLOAD.with_name("p6-paired-child-linux-probe-02")
OLD_CONTROL = PREVIOUS / "control-v2"


def pin(path):
    raw = path.read_bytes()
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def form(node):
    return ast.dump(node, include_attributes=False)


def definitions(tree):
    return {node.name: node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef))}


def assignments(tree):
    return {node.targets[0].id: node.value for node in tree.body if isinstance(node, ast.Assign)
            and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)}


def extract(nodes, namespace):
    module = ast.fix_missing_locations(ast.Module(body=copy.deepcopy(nodes), type_ignores=[]))
    exec(compile(module, "<pure-reviewed-source-extract>", "exec"), namespace)


def rejects(operation, message):
    try:
        operation()
    except (ValueError, TypeError):
        return
    raise AssertionError(message)


def run():
    remote = ast.parse((HERE / "remote_probe_control.py").read_text())
    old_remote = ast.parse((OLD_CONTROL / "remote_probe_control.py").read_text())
    funcs, old_funcs = definitions(remote), definitions(old_remote)
    assert set(funcs) == set(old_funcs)
    assert all(form(funcs[key]) == form(old_funcs[key]) for key in funcs)
    globals_, old_globals = assignments(remote), assignments(old_remote)
    assert set(globals_) == set(old_globals)
    assert {key for key in globals_ if form(globals_[key]) != form(old_globals[key])} == {
        "PACKAGE", "JOB_NAME", "PINS", "RUN_FILES"}
    local = ast.parse((HERE / "probe_control.py").read_text())
    old_local = ast.parse((OLD_CONTROL / "probe_control.py").read_text())
    local_funcs, old_local_funcs = definitions(local), definitions(old_local)
    assert set(local_funcs) == set(old_local_funcs)
    assert {key for key in local_funcs if form(local_funcs[key]) != form(old_local_funcs[key])} == {"save_observation"}
    pins = ast.literal_eval(globals_["PINS"])
    uploads = ast.literal_eval(globals_["UPLOADS"])
    copies = ast.literal_eval(globals_["COPIES"])
    manifest = json.loads((PAYLOAD / "manifest.json").read_bytes())
    for name, expected in pins.items():
        assert pin(PAYLOAD / name) == expected
    assert manifest["files"] == {key: value for key, value in pins.items() if key != "manifest.json"}
    assert (PAYLOAD / "paired_controller.py").read_bytes() == (
        PAYLOAD.with_name("p6-paired-child-monitor-fix-02") / "paired_controller.py").read_bytes()
    assert pins["paired_controller.py"]["sha256"] == "caff33d11918bad304ddf0a04021550a6d686d254e604342190df094958ce482"
    for name in ("paired_common.py", "job.sh"):
        assert (PAYLOAD / name).read_bytes() == (PREVIOUS / name).read_bytes()

    actual = {name: (PAYLOAD / name).read_bytes() for name in uploads}
    copied = {name: (PAYLOAD / name).read_bytes() for name in copies}
    encoded = {name: base64.b64encode(raw).decode("ascii") for name, raw in actual.items()}
    namespace = {"base64": base64, "hashlib": hashlib, "PINS": pins, "UPLOADS": uploads,
                 "COPIES": copies, "SOURCE_MANIFEST": ast.literal_eval(globals_["SOURCE_MANIFEST"]), "Path": Path}
    extract([funcs[name] for name in ("require", "digest", "pin", "decode_uploads", "request_binding", "stage")], namespace)
    assert namespace["decode_uploads"](encoded) == actual
    uploaded_bytes = sum(map(len, actual.values()))
    payload_bytes = sum(item["bytes"] for item in pins.values())
    assert uploaded_bytes == 96030 and payload_bytes == 117374
    malformed = (
        dict(encoded, **{uploads[0]: base64.b64encode(actual[uploads[0]] + b"x").decode("ascii")}),
        {key: value for key, value in encoded.items() if key != uploads[0]},
        dict(encoded, **{"unlisted.py": ""}),
        dict(encoded, **{uploads[0]: "!"}),
    )
    for value in malformed:
        rejects(lambda: namespace["decode_uploads"](value), "Malformed payload admitted.")
    request = {"schema": "hydra-child-linux-monitor-control-request-v1", "phase": "stage",
               "nonce": "0" * 32, "manifest_sha256": pins["manifest.json"]["sha256"],
               "remote_control_sha256": pin(HERE / "remote_probe_control.py")["sha256"], "uploads": encoded}
    # This value is an in-memory size fixture, never saved or submitted.
    wire_bytes = len(json.dumps(request, sort_keys=True, separators=(",", ":"), allow_nan=False).encode())
    assert wire_bytes <= 128 * 1024
    effects = []
    class ExistingPackage:
        def exists(self):
            effects.append("target_exists")
            return True
        def is_symlink(self):
            raise AssertionError("Existing target must stop immediately.")
        def __str__(self):
            return "/unit-fixture/existing-package"
    class NoCommands:
        def queue(self):
            raise AssertionError("No scheduler call before target absence admission.")
    def sources():
        effects.append("source_admission_stub")
        return copied
    namespace.update(PACKAGE=ExistingPackage(), CAMPAIGN="/unit-fixture", verify_sources=sources,
                     owned_directory=lambda path: effects.append("owned_directory_stub"))
    rejects(lambda: namespace["stage"](request, NoCommands()), "Existing target admitted.")
    assert effects == ["source_admission_stub", "owned_directory_stub", "target_exists"]
    result_expression = next(node.value for node in funcs["stage"].body if isinstance(node, ast.Assign)
                             and any(isinstance(t, ast.Name) and t.id == "result" for t in node.targets))
    namespace.update(request=request, queue=[])
    result = eval(compile(ast.Expression(result_expression), "<pure-receipt-expression>", "eval"), namespace)
    assert result["uploaded_bytes"] == uploaded_bytes and result["payload_bytes"] == payload_bytes
    assert result["uploaded_files"] == {name: pins[name] for name in uploads}
    assert result["copied_files"] == {name: pins[name] for name in copies}

    run_files = eval(compile(ast.Expression(globals_["RUN_FILES"]), "<fixed-whitelist>", "eval"), {})
    assert len(run_files) == 70
    allowed = {"actual-process-exit.txt", "slurm-0.out", "slurm-0.err"} | {"run-01/" + name for name in run_files}
    assert len(allowed) == 73
    collection_guard = next(node.value.args[0] for node in local_funcs["save_observation"].body
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Name) and node.value.func.id == "require"
        and isinstance(node.value.args[1], ast.Constant) and node.value.args[1].value == "Unlisted collected file.")
    check = compile(ast.Expression(collection_guard), "<pure-collection-guard>", "eval")
    assert eval(check, {"files": {name: None for name in allowed}, "allowed": allowed})
    assert not eval(check, {"files": {"run-01/unlisted.json": None}, "allowed": allowed})

    worker = ast.parse((PAYLOAD / "paired_case_worker.py").read_text())
    old_worker = ast.parse((PREVIOUS / "paired_case_worker.py").read_text())
    worker_funcs, worker_globals = definitions(worker), assignments(worker)
    popen = lambda tree: [node for node in ast.walk(tree) if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "subprocess" and node.func.attr == "Popen"]
    assert len(popen(worker)) == len(popen(old_worker)) == 1
    assert form(popen(worker)[0]) == form(popen(old_worker)[0])
    assert not any(isinstance(node, ast.keyword) and node.arg == "preexec_fn" for node in ast.walk(worker))
    assert ast.literal_eval(worker_globals["QUERIES"]) == 64
    assert ast.literal_eval(worker_globals["CHILD_CPU_BUDGET"]) == 18.0
    assert ast.literal_eval(worker_globals["NEXT_QUERY_CPU_RESERVE"]) == 1.0
    limits_calls = lambda tree: [node for node in ast.walk(tree) if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "resource" and node.func.attr == "setrlimit"]
    assert [form(node) for node in limits_calls(worker)] == [form(node) for node in limits_calls(old_worker)]
    # Execute only the actual source prefix ending BEFORE TemporaryFile/Popen.
    admission = copy.deepcopy(worker_funcs["one_query"])
    admission.name = "prelaunch_admission"
    split = next(i for i, node in enumerate(admission.body) if isinstance(node, ast.Assign)
                 and any(isinstance(t, ast.Tuple) and any(isinstance(x, ast.Name) and x.id == "active_deadline"
                         for x in t.elts) for t in node.targets))
    admission.body = admission.body[:split] + [ast.Return(value=ast.Name(id="cpu_before", ctx=ast.Load()))]
    usage = SimpleNamespace(ru_utime=0.0, ru_stime=0.0)
    saved = []
    pure = {"math": math, "resource": SimpleNamespace(RUSAGE_CHILDREN=1, getrusage=lambda _: usage),
            "time": SimpleNamespace(monotonic=lambda: 100.0), "CHILD_CPU_BUDGET": 18.0,
            "NEXT_QUERY_CPU_RESERVE": 1.0, "save": lambda path, record: saved.append(record)}
    extract([worker_funcs["require"], worker_funcs["child_cpu_seconds"], admission], pure)
    call = lambda deadline=120.0: pure["prelaunch_admission"](0, "/fixed/scontrol", "0", Path("/unit-fixture"), deadline)
    usage.ru_utime = 17.0
    assert call() == 17.0 and not saved
    usage.ru_utime = 17.0001
    rejects(call, "Exhausted CPU reserve admitted.")
    assert saved[-1]["actual_launches"] == 0 and saved[-1]["phase"] == "before_launch"
    usage.ru_utime = 0.0
    rejects(lambda: call(103.05), "Absent full wall/cleanup reserve admitted.")
    assert saved[-1]["actual_launches"] == 0 and saved[-1]["passed"] is False
    for invalid in (float("nan"), float("inf"), -0.001):
        usage.ru_utime = invalid
        rejects(call, "Unavailable child CPU accounting admitted.")

    probe = ast.parse((PAYLOAD / "run_probe.py").read_text())
    old_probe = ast.parse((PREVIOUS / "run_probe.py").read_text())
    probe_funcs, probe_globals = definitions(probe), assignments(probe)
    assert form(probe_funcs["query_identity_observed"]) == form(definitions(old_probe)["query_identity_observed"])
    probe_ns = {"QUERIES": 64}
    limits = eval(compile(ast.Expression(probe_globals["LIMITS"]), "<fixed-limits>", "eval"), probe_ns)
    assert limits == manifest["limits"]
    assert limits["parent_cpu_hard_seconds"] + limits["fixture_cpu_hard_seconds"] + limits["shared_child_cpu_budget_seconds"] == 23
    assert limits["aggregate_cpu_seconds"] == 24 and limits["inner_wall_seconds"] == 30
    assert limits["scheduler_seconds"] == 60 and limits["query_cpu_hard_seconds"] == 1
    assert limits["retained_trace_bytes"] + limits["query_summary_bytes"] + limits["execution_summary_bytes"] == 237568
    assert limits["file_bytes"] - 237568 == 24576 and limits["total_result_bytes"] == 2 * 1024**2
    for name in ("paired_controller.py", "paired_common.py"):
        ast.parse((PAYLOAD / name).read_text())
    assert not (HERE / "attempt").exists() and not (HERE / ".phase.lock").exists()
    print(json.dumps({"passed": True, "scope": "file_ast_and_pure_prelaunch_admission_only",
        "uploaded_bytes": uploaded_bytes, "payload_bytes": payload_bytes, "encoded_request_bytes": wire_bytes,
        "query_count": 64, "fixed_collected_paths": 73, "malformed_payload_rejections": 4,
        "cpu_wall_accounting_rejections": 5, "exact_production_popen_preserved": True,
        "remote_function_bodies_unchanged": True, "local_function_delta": ["save_observation"],
        "target_absence_guard_exercised": True, "actual_receipt_expression_totals_checked": True,
        "processes_or_proc_reads_or_network_calls": 0, "source_modules_imported": False,
        "synthetic_completion_receipts_written": False, "runtime_probe_executed": False}, sort_keys=True))


if __name__ == "__main__":
    run()
