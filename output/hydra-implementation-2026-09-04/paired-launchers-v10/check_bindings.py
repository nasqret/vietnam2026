"""One file-only binding and negative-admission gate; never launches a process."""
from __future__ import annotations

import ast
import copy
import hashlib
import importlib.abc
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
BASE, ROOT = HERE.parent, HERE.parents[2]
sys.dont_write_bytecode = True


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def pin(path):
    raw = path.read_bytes()
    return {"path": path.relative_to(ROOT).as_posix(), "bytes": len(raw), "sha256": digest(raw)}


def function_bodies(path):
    return {node.name: ast.dump(node, include_attributes=False) for node in ast.parse(path.read_bytes()).body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}


def changed_functions(old, new):
    before, after = function_bodies(old), function_bodies(new)
    assert set(before) == set(after), "Unexpected helper/function population change"
    return sorted(name for name in before if before[name] != after[name])


attempted_process_or_network = []
blocked_runtime_imports = []


def audit(event, args):
    if event in {"subprocess.Popen", "os.system", "os.fork", "os.forkpty", "os.posix_spawn"} or event.startswith("socket."):
        attempted_process_or_network.append(event)
        raise AssertionError("File-only gate forbids " + event)


class NoRuntime(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".", 1)[0] in {"torch", "transformers", "peft", "numpy", "peano_lab", "experimental_model",
                "hybrid_search", "model_runtime", "vampire_bridge", "decision_pilot"}:
            blocked_runtime_imports.append(fullname)
            raise AssertionError("File-only gate forbids runtime import " + fullname)
        return None


sys.addaudithook(audit)
sys.meta_path.insert(0, NoRuntime())


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


control = load("remote_paired_control", HERE / "remote_paired_control.py")
local = load("_paired_v10_file_gate", HERE / "paired_launchers.py")
control.require_frozen_bindings()
assert control.SELECTED_ARMS == ("fresh_1_7b", "fresh_4b")
assert control.PROFILE_SECONDS[control.SELECTED_PROFILE] == 1560
assert control.SELECTION_SHA == "dc2a12ee2203e6fa4c925d4f3e19c95c3223b6be613e6472c2cf002c64dac5b6"
assert not (HERE / "prepared").exists(), "This gate precedes actual preparation"

old = BASE / "paired-launchers-v9"
local_changes = changed_functions(old / "paired_launchers.py", HERE / "paired_launchers.py")
remote_changes = changed_functions(old / "remote_paired_control.py", HERE / "remote_paired_control.py")
assert local_changes == sorted(["bundle_inputs", "current_ledger", "admit_copy_transfer", "admit_selection", "admit_monitor_probe", "prepare", "load_prepared"]), local_changes
assert remote_changes == sorted(["attempt", "require_frozen_bindings"]), remote_changes

manifest_raw = (local.BUNDLE / "manifest.json").read_bytes()
manifest = json.loads(manifest_raw)
source_map = json.loads((local.BUNDLE / "paired-source-pins.json").read_bytes())
assert digest(manifest_raw) == control.MANIFEST_SHA
assert digest(control.canonical(manifest)) == control.MANIFEST_CONTENT_SHA
assert manifest["archive_sha256"] == control.ARCHIVE_SHA
assert manifest["file_count"] == 1345 and manifest["expanded_bytes"] == 112221252
assert len(source_map) == 734 and digest(control.canonical(source_map)) == control.SOURCE_MAP_SHA
assert len(manifest["added_files"]) == 20 and manifest["added_bytes"] == 128574
assert set(manifest["changed_files"]) == {control.CONTROL + "/paired_controller.py"}
for name, expected in (("paired_controller.py", control.CONTROLLER_SHA), ("paired_common.py", control.COMMON_SHA),
                       ("paired_case_worker.py", control.WORKER_SHA)):
    p = local.BUNDLE / "source" / control.CONTROL / name
    assert digest(p.read_bytes()) == expected == source_map[control.CONTROL + "/" + name]["sha256"]

study_path = BASE / "paired-size-study-04/study.json"
study = json.loads(study_path.read_bytes())
previous = json.loads((BASE / "paired-size-study-03/study.json").read_bytes())
assert set(study) == set(previous)
assert sorted(key for key in study if study[key] != previous[key]) == ["source_pins_sha256", "study_id"]
assert study["source_pins_sha256"] == control.SOURCE_MAP_SHA
assert study["study_id"] == "paired-size-20260905-v4"
assert set(study["arms"]) == set(control.ARMS)
choice_path = BASE / "paired-choice-04/choice.template.json"
choice = json.loads(choice_path.read_bytes())
assert choice["study"] == {"path": study_path.relative_to(ROOT).as_posix(), "sha256": digest(study_path.read_bytes())}
assert choice["schema"] == "hydra-paired-launch-choice-v5"
assert all(value == {"path": None, "sha256": None} for kind in ("transfer", "monitor_probe") for value in choice[kind].values())
local.admit_selection(choice["selection"])

probe_path = ROOT / "output/p6-paired-child-linux-probe-01/manifest.json"
probe = json.loads(probe_path.read_bytes())
assert digest(probe_path.read_bytes()) == local.MONITOR_PROBE_MANIFEST_SHA
assert probe["schema"] == "hydra-child-linux-monitor-probe-package-v1"
assert probe["files"]["paired_controller.py"]["sha256"] == control.CONTROLLER_SHA
assert probe["files"]["paired_common.py"]["sha256"] == control.COMMON_SHA
assert probe["limits"]["maximum_scheduler_children"] == 16
assert probe["limits"]["aggregate_cpu_seconds"] == 24
assert probe["limits"]["inner_wall_seconds"] == 30
review_raw = (local.BUNDLE / "COPY_REVIEW.json").read_bytes()
review = json.loads(review_raw)
assert digest(control.canonical(review)) == control.COPY_REVIEW_SHA

checks = []


def rejects(label, call, fragment=None):
    try:
        call()
    except (ValueError, TypeError, KeyError) as error:
        if fragment is not None:
            assert fragment in str(error), (label, str(error))
        checks.append(label)
    else:
        raise AssertionError("Negative admission unexpectedly succeeded: " + label)


specs = {arm: local.make_spec(study, digest(study_path.read_bytes()), arm, "0" * 32) for arm in control.SELECTED_ARMS}
assert {arm: spec["attempt"] for arm, spec in specs.items()} == {
    "fresh_1_7b": "p6-paired-fresh-1-7b-v6-01", "fresh_4b": "p6-paired-fresh-4b-v6-01"}
assert sum(spec["seconds"] for spec in specs.values()) == 3120
rejects("unselected symbolic arm", lambda: control.attempt("symbolic"))
wrong = dict(specs["fresh_4b"], attempt="p6-paired-fresh-4b-v5-01")
rejects("consumed old attempt identity", lambda: control.validate_spec(wrong))
wrong_seconds = dict(specs["fresh_4b"], seconds=1561)
rejects("changed allocation ceiling", lambda: control.validate_spec(wrong_seconds))
wrong_source = dict(specs["fresh_4b"], source=control.SOURCE.replace("source-05", "source-04"))
rejects("previous source identity", lambda: control.validate_spec(wrong_source))
rejects("missing actual child probe evidence", lambda: local.admit_monitor_probe(choice["monitor_probe"]))
rejects("missing actual transfer evidence", lambda: local.admit_copy_transfer(b"{}", b"{}", manifest))
ledger_sha = digest((BASE / "campaign.json").read_bytes())
rejects("4B before reconciled new 1.7B charge", lambda: local.current_ledger(ledger_sha, "fresh_4b"),
        "selected 1.7B release charge")
rejects("null choice cannot prepare", lambda: local.prepare(SimpleNamespace(choice=str(choice_path),
        choice_sha256=digest(choice_path.read_bytes()), ledger_sha256=ledger_sha)))
assert not (HERE / "prepared").exists()
assert not attempted_process_or_network and not blocked_runtime_imports

report = {"schema": "hydra-paired-v10-local-binding-gate-v1", "passed": True,
    "source_scope": "file metadata, AST and in-memory negative admission only",
    "changed_local_functions": local_changes, "changed_remote_functions": remote_changes,
    "negative_admission_checks": checks,
    "files": {name: pin(HERE / name) for name in ("paired_launchers.py", "remote_paired_control.py", "check_bindings.py")},
    "study": pin(study_path), "choice_template": pin(choice_path), "cpu_probe_manifest": pin(probe_path),
    "copy_review": pin(local.BUNDLE / "COPY_REVIEW.json"), "ledger_read_sha256": ledger_sha,
    "selected_attempts": {arm: spec["attempt"] for arm, spec in specs.items()},
    "selected_gpu_seconds": 3120, "preparation_performed": False,
    "process_or_network_attempts": attempted_process_or_network,
    "forbidden_runtime_import_attempts": blocked_runtime_imports,
    "gpu_allocations": 0, "model_calls": 0, "native_runs": 0}
with (HERE / "bindings.json").open("x") as stream:
    json.dump(report, stream, sort_keys=True, indent=2)
    stream.write("\n")
print(json.dumps({"passed": True, "negative_checks": len(checks), "bindings": pin(HERE / "bindings.json"),
                  "gpu_allocations": 0, "model_calls": 0, "native_runs": 0}))
