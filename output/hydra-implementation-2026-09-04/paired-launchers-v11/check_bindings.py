"""One file-only gate for the CPU02 prerequisite binding; no preparation or jobs."""
from __future__ import annotations
import ast
import hashlib
import importlib.abc
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
BASE, ROOT = HERE.parent, HERE.parents[2]
sys.dont_write_bytecode = True
attempts = []


def audit(event, args):
    if event in {"subprocess.Popen", "os.system", "os.fork", "os.forkpty", "os.posix_spawn"} or event.startswith("socket."):
        attempts.append(event)
        raise AssertionError("File-only gate forbids " + event)


class NoRuntime(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".", 1)[0] in {"torch", "transformers", "peft", "numpy", "peano_lab", "experimental_model",
                "hybrid_search", "model_runtime", "decision_pilot"}:
            attempts.append("import:" + fullname)
            raise AssertionError("Runtime import is forbidden")
        return None


sys.addaudithook(audit)
sys.meta_path.insert(0, NoRuntime())


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def pin(path):
    raw = path.read_bytes()
    return {"path": path.relative_to(ROOT).as_posix(), "bytes": len(raw), "sha256": digest(raw)}


def functions(path):
    return {n.name: ast.dump(n, include_attributes=False) for n in ast.parse(path.read_bytes()).body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


old = BASE / "paired-launchers-v10"
assert digest((old / "paired_launchers.py").read_bytes()) == "790028b65ca609d561878416b8552d7902e5dc8b9f402bc027053a5f11ac716c"
assert (old / "remote_paired_control.py").read_bytes() == (HERE / "remote_paired_control.py").read_bytes()
assert digest((HERE / "remote_paired_control.py").read_bytes()) == "7f3f149aabfed8416d263b71d9f718223634e7a0204372cfe5475ece362c8821"
before, after = functions(old / "paired_launchers.py"), functions(HERE / "paired_launchers.py")
assert set(after) - set(before) == {"admit_cpu_update"} and not (set(before) - set(after))
changed = sorted(name for name in before if before[name] != after[name])
assert changed == ["admit_monitor_probe", "load_prepared", "prepare"], changed
assert before["admit_copy_transfer"] == after["admit_copy_transfer"]
control = load("remote_paired_control", HERE / "remote_paired_control.py")
local = load("_paired_v11_file_gate", HERE / "paired_launchers.py")
control.require_frozen_bindings()
assert control.SELECTED_ARMS == ("fresh_1_7b", "fresh_4b")
assert {arm: control.attempt(arm) for arm in control.SELECTED_ARMS} == {
    "fresh_1_7b": "p6-paired-fresh-1-7b-v6-01", "fresh_4b": "p6-paired-fresh-4b-v6-01"}
assert control.PROFILE_SECONDS[control.SELECTED_PROFILE] * len(control.SELECTED_ARMS) == 3120
assert not (HERE / "prepared").exists()
choice = json.loads((HERE / "choice.template.json").read_bytes())
assert choice["schema"] == "hydra-paired-launch-choice-v6"
previous_choice = json.loads((BASE / "paired-choice-04/choice.template.json").read_bytes())
assert {key: value for key, value in choice.items() if key not in {"schema", "cpu_update"}} == {
    key: value for key, value in previous_choice.items() if key != "schema"}
assert all(value == {"path": None, "sha256": None} for kind in ("transfer", "monitor_probe") for value in choice[kind].values())
assert local.admit_selection(choice["selection"]) == choice["selection"]
assert local.admit_cpu_update(choice["cpu_update"], choice["selection"]) == choice["cpu_update"]
assert digest((BASE / "paired-size-study-04/study.json").read_bytes()) == "6124c2110209680f05530885e121e4600ef830b68bae883e3d9a539819ff2d02"
probe_path = ROOT / "output/p6-paired-child-linux-probe-02/manifest.json"
probe = json.loads(probe_path.read_bytes())
assert digest(probe_path.read_bytes()) == local.MONITOR_PROBE_MANIFEST_SHA
assert probe["files"]["paired_controller.py"]["sha256"] == control.CONTROLLER_SHA
assert probe["files"]["paired_common.py"]["sha256"] == control.COMMON_SHA
assert probe["limits"]["fixture_cpu_hard_seconds"] == probe["limits"]["query_cpu_hard_seconds"] == 1
assert probe["limits"]["nominal_aggregate_cpu_hard_seconds"] == 21
assert probe["limits"]["aggregate_cpu_seconds"] == 24 and probe["limits"]["inner_wall_seconds"] == 30
assert probe["limits"]["maximum_scheduler_children"] == 16
for name, data in probe["files"].items():
    assert pin(probe_path.parent / name)["sha256"] == data["sha256"]
worker = (probe_path.parent / "paired_case_worker.py").read_text()
assert not any(isinstance(n, ast.keyword) and n.arg == "preexec_fn" for n in ast.walk(ast.parse(worker)))
reused = old / "copy-admission-01/result.json"
assert digest(reused.read_bytes()) == "23c42f8352b88b775d71d077c5206b4acc30a696d327e3369855c58b49e4f995"
assert json.loads(reused.read_bytes())["passed"] is True
reused_actual = old / "copy-admission-01/actual-completion.json"
assert digest(reused_actual.read_bytes()) == "6be5ae62d46e8fdd84a966087baa3f03b73e86f9a054da34eab21c641e89e713"
assert json.loads(reused_actual.read_bytes())["actual_exit_code"] == 0
assert not attempts and not (HERE / "prepared").exists()
report = {"schema": "hydra-paired-v11-file-binding-gate-v1", "passed": True,
    "changed_existing_local_functions": changed, "added_local_functions": ["admit_cpu_update"],
    "remote_bytes_unchanged": True, "original_decision_unchanged": True,
    "gpu_attempts_and_limits_unchanged": True, "study_unchanged": True,
    "original_failed_cpu_evidence_admitted_as_failure_only": True,
    "source_copy_reader_ast_identical": True, "reused_actual_source_copy_admission": pin(reused),
    "reused_source_copy_actual_completion": pin(reused_actual),
    "files": {name: pin(HERE / name) for name in ("paired_launchers.py", "remote_paired_control.py", "check_bindings.py", "choice.template.json")},
    "cpu_manifest": pin(probe_path), "cpu_update": pin(ROOT / choice["cpu_update"]["path"]),
    "process_network_or_runtime_attempts": attempts, "preparation_performed": False,
    "actual_cpu02_result_created": False, "gpu_allocations": 0, "native_runs": 0, "model_calls": 0}
with (HERE / "bindings.json").open("x") as stream:
    json.dump(report, stream, sort_keys=True, indent=2)
    stream.write("\n")
print(json.dumps({"passed": True, "bindings": pin(HERE / "bindings.json"), "preparation_performed": False}))
