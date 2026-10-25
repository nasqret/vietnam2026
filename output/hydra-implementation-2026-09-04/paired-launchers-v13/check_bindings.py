"""One file-only binding/negative-admission gate; no preparation or runtime work."""
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
                "hybrid_search", "model_runtime", "decision_pilot", "vampire_bridge"}:
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
    return {node.name: ast.dump(node, include_attributes=False) for node in ast.parse(path.read_bytes()).body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


old = BASE / "paired-launchers-v12"
assert digest((old / "paired_launchers.py").read_bytes()) == "3a90ffb59d6d8f3ccce797b0357d9122bdbcdfbecb669cacf57682c3f14d3468"
assert digest((old / "remote_paired_control.py").read_bytes()) == "44ee943d7391da555230a76981644f871c282cdeeee68fa4a11586bc955ccdcb"
before, after = functions(old / "paired_launchers.py"), functions(HERE / "paired_launchers.py")
assert set(after) - set(before) == {"admit_fork_update"} and not (set(before) - set(after))
local_changed = sorted(name for name in before if before[name] != after[name])
assert local_changed == sorted(["current_ledger", "admit_copy_transfer", "admit_remaining_update",
                                "admit_monitor_probe", "prepare", "load_prepared"]), local_changed
old_remote, new_remote = functions(old / "remote_paired_control.py"), functions(HERE / "remote_paired_control.py")
assert set(old_remote) == set(new_remote)
remote_changed = sorted(name for name in old_remote if old_remote[name] != new_remote[name])
assert remote_changed == ["attempt", "require_frozen_bindings"], remote_changed

reviewed = json.loads((HERE / "NARROW_REVIEW.json").read_bytes())
assert reviewed["verdict"] == "no_blocker_in_reviewed_scope"
for name, expected in reviewed["reviewed_functions_ast_sha256"].items():
    assert digest(after[name].encode()) == expected

control = load("remote_paired_control", HERE / "remote_paired_control.py")
local = load("_paired_v13_file_gate", HERE / "paired_launchers.py")
control.require_frozen_bindings()
assert control.SELECTED_ARMS == ("fresh_4b",)
assert control.attempt("fresh_4b") == "p6-paired-fresh-4b-v8-01"
assert control.PROFILE_SECONDS[control.SELECTED_PROFILE] * len(control.SELECTED_ARMS) == 1560
assert not (HERE / "prepared").exists()

manifest, source_map = local.bundle_inputs()
assert digest((local.BUNDLE / "manifest.json").read_bytes()) == control.MANIFEST_SHA
assert digest(control.canonical(manifest)) == control.MANIFEST_CONTENT_SHA
assert manifest["file_count"] == 1345 and manifest["expanded_bytes"] == 112226730
assert manifest["added_files"] == {} and manifest["added_bytes"] == 0
assert sorted(manifest["changed_files"]) == [control.CONTROL + "/paired_controller.py"]
parent = json.loads((BASE / "combined-source-bundle-06/manifest.json").read_bytes())
assert set(manifest["files"]) == set(parent["files"])
assert sorted(name for name in manifest["files"] if manifest["files"][name] != parent["files"][name]) == [
    control.CONTROL + "/paired_controller.py"]
for name in ("student", "teacher", "teacher-paired"):
    assert manifest["source_maps"][name] == parent["source_maps"][name]
for name, expected in (("paired_controller.py", control.CONTROLLER_SHA), ("paired_common.py", control.COMMON_SHA),
                       ("paired_case_worker.py", control.WORKER_SHA)):
    path = local.BUNDLE / "source" / control.CONTROL / name
    assert digest(path.read_bytes()) == source_map[control.CONTROL + "/" + name]["sha256"] == expected

study_path = BASE / "paired-size-study-06/study.json"
study = json.loads(study_path.read_bytes())
previous_study = json.loads((BASE / "paired-size-study-05/study.json").read_bytes())
assert set(study) == set(previous_study)
assert sorted(key for key in study if study[key] != previous_study[key]) == ["source_pins_sha256", "study_id"]
assert study["study_id"] == "paired-size-20260905-v6" and study["source_pins_sha256"] == control.SOURCE_MAP_SHA
assert set(study["arms"]) == set(control.ARMS)
choice = json.loads((HERE / "choice.template.json").read_bytes())
assert (HERE / "choice.template.json").read_bytes() == (BASE / "paired-choice-06/choice.template.json").read_bytes()
assert choice["schema"] == "hydra-paired-launch-choice-v8"
assert choice["study"] == {"path": study_path.relative_to(ROOT).as_posix(), "sha256": digest(study_path.read_bytes())}
previous_choice = json.loads((old / "choice.template.json").read_bytes())
assert {key: value for key, value in choice.items() if key not in {"schema", "study", "fork_update"}} == {
    key: value for key, value in previous_choice.items() if key not in {"schema", "study"}}
assert all(value == {"path": None, "sha256": None} for kind in ("transfer", "monitor_probe") for value in choice[kind].values())
assert local.admit_selection(choice["selection"]) == choice["selection"]
assert local.admit_cpu_update(choice["cpu_update"], choice["selection"]) == choice["cpu_update"]
assert local.admit_remaining_update(choice["remaining_update"], choice["selection"]) == choice["remaining_update"]
assert local.admit_fork_update(choice["fork_update"], choice["selection"], choice["remaining_update"]) == choice["fork_update"]

probe_path = ROOT / "output/p6-paired-child-linux-probe-04/manifest.json"
probe = json.loads(probe_path.read_bytes())
assert digest(probe_path.read_bytes()) == local.MONITOR_PROBE_MANIFEST_SHA
contract_path = probe_path.parent / "ACTUAL_COMPLETION_CONTRACT.json"
assert digest(contract_path.read_bytes()) == "e7035b032c9db49ca03fc4f339f2e0f0e316546346ff559b80a0cf81b92f8617"
completion_contract = json.loads(contract_path.read_bytes())
assert completion_contract["status"] == "schema_only_no_actual_receipt"
assert completion_contract["required_observed_variable_fields"]["manifest_sha256"] == local.MONITOR_PROBE_MANIFEST_SHA
assert completion_contract["required_observed_variable_fields"]["controller_sha256"] == control.CONTROLLER_SHA
assert completion_contract["source_copy"] == probe["source_copy"]
assert probe["files"]["paired_controller.py"]["sha256"] == control.CONTROLLER_SHA
assert probe["files"]["paired_common.py"]["sha256"] == control.COMMON_SHA
for name, data in probe["files"].items():
    actual = pin(probe_path.parent / name)
    assert {key: actual[key] for key in ("bytes", "sha256")} == data
limits = probe["limits"]
assert limits["maximum_scheduler_children"] == 64
assert limits["query_batch_rows"] == 4 and limits["maximum_query_batch_files"] == 16
assert limits["maximum_simultaneous_scheduler_children"] == 1
assert limits["shared_child_cpu_budget_seconds"] == 18 and limits["next_query_cpu_reserve_seconds"] == 1
assert limits["parent_cpu_hard_seconds"] == 4 and limits["fixture_cpu_hard_seconds"] == limits["query_cpu_hard_seconds"] == 1
assert limits["nominal_aggregate_cpu_hard_seconds"] == 23 and limits["aggregate_cpu_seconds"] == 24
assert limits["inner_wall_seconds"] == 30 and limits["scheduler_seconds"] == 60 and limits["file_bytes"] == 262144
assert not any(isinstance(node, ast.keyword) and node.arg == "preexec_fn"
               for node in ast.walk(ast.parse((probe_path.parent / "paired_case_worker.py").read_bytes())))
review_raw = (local.BUNDLE / "COPY_REVIEW.json").read_bytes()
review = json.loads(review_raw)
assert digest(review_raw) == control.COPY_REVIEW_RAW_SHA
assert digest(control.canonical(review)) == control.COPY_REVIEW_SHA
assert control.COPY_PAYLOAD_BYTES == 443094 and control.COPY_QUOTA_REQUIRED == 1674

transfer = BASE / "combined-inference-transfer-07"
response_raw = (transfer / "stdout.json").read_bytes()
transport_raw = (transfer / "actual-completion.json").read_bytes()
actual_raw = (transfer / "actual-tool-completion.json").read_bytes()
assert digest(response_raw) == "293ee2d74d8f433914a1524db4e73a4bb9a93b5ca0d6206ee0d1f8388ffa9563"
assert digest(transport_raw) == "939c7434799423481ea0f030cb379f75fc45e6dd47a03d12617743464a3029c2"
assert digest(actual_raw) == "1b20b4b36a5163eddc3f7a006769047b54636d3159d6a02be2e42c1a8bb467eb"
actual_transfer = json.loads(actual_raw)
local.actual_completion(actual_transfer)
assert actual_transfer["schema"] == "hydra-source07-stage-root-tool-completion-v1"
assert actual_transfer["completion_chunk"] == "326e1e" and actual_transfer["source_copy_completed"] is True
assert actual_transfer["review_sha256"] == control.COPY_REVIEW_RAW_SHA
assert actual_transfer["stdout"] == {"bytes": len(response_raw), "sha256": digest(response_raw)}
assert actual_transfer["transport"] == {"bytes": len(transport_raw), "sha256": digest(transport_raw)}
local.admit_copy_transfer(response_raw, transport_raw, manifest)

checks = []


def rejects(label, call):
    try:
        call()
    except (ValueError, TypeError, KeyError):
        checks.append(label)
    else:
        raise AssertionError("Negative admission unexpectedly succeeded: " + label)


spec = local.make_spec(study, digest(study_path.read_bytes()), "fresh_4b", "0" * 32)
assert spec["seconds"] == 1560 and spec["cpus"] == 8 and spec["memory_gib"] == 64 and spec["gpus"] == 1
assert spec["attempt"] == "p6-paired-fresh-4b-v8-01" and spec["source"] == control.SOURCE
rejects("failed fresh1.7 arm cannot be selected", lambda: control.attempt("fresh_1_7b"))
rejects("unselected symbolic arm", lambda: control.attempt("symbolic"))
rejects("abandoned first 4B attempt", lambda: control.validate_spec(dict(spec, attempt="p6-paired-fresh-4b-v6-01")))
rejects("abandoned CPU03-bound 4B attempt", lambda: control.validate_spec(dict(spec, attempt="p6-paired-fresh-4b-v7-01")))
rejects("source06 cannot run the new allocation", lambda: control.validate_spec(dict(spec, source=control.SOURCE.replace("source-07", "source-06"))))
rejects("allocation ceiling cannot expand", lambda: control.validate_spec(dict(spec, seconds=1561)))
rejects("missing remaining-arm selection", lambda: local.admit_remaining_update(None, choice["selection"]))
rejects("missing actual CPU04 evidence", lambda: local.admit_monitor_probe(choice["monitor_probe"]))
rejects("missing actual source07 transfer", lambda: local.admit_copy_transfer(b"{}", b"{}", manifest))
rejects("missing fork-transition selection", lambda: local.admit_fork_update(None, choice["selection"], choice["remaining_update"]))
assert not attempts and not (HERE / "prepared").exists()

report = {"schema": "hydra-paired-v13-file-binding-gate-v1", "passed": True,
    "changed_existing_local_functions": local_changed, "added_local_functions": ["admit_fork_update"],
    "changed_remote_functions": remote_changed, "unchanged_transport_release_collection_and_resource_helpers": True,
    "only_new_fresh4b_attempt_selected": True, "maximum_new_gpu_seconds": 1560,
    "original_decisions_and_failed_fresh1_7b_evidence_preserved": True,
    "study_changes": ["source_pins_sha256", "study_id"], "negative_admission_checks": checks,
    "files": {name: pin(HERE / name) for name in ("paired_launchers.py", "remote_paired_control.py", "check_bindings.py", "choice.template.json")},
    "study": pin(study_path), "cpu_manifest": pin(probe_path),
    "cpu_completion_contract": pin(probe_path.parent / "ACTUAL_COMPLETION_CONTRACT.json"),
    "remaining_update": pin(ROOT / choice["remaining_update"]["path"]),
    "fork_update": pin(ROOT / choice["fork_update"]["path"]),
    "failed_CPU03_preserved_as_failed": True,
    "copy_review": pin(local.BUNDLE / "COPY_REVIEW.json"), "narrow_review": pin(HERE / "NARROW_REVIEW.json"),
    "actual_source07_transfer_admitted": True,
    "actual_source07_transfer": {"response": pin(transfer / "stdout.json"),
        "transport": pin(transfer / "actual-completion.json"), "actual_tool_completion": pin(transfer / "actual-tool-completion.json")},
    "process_network_or_runtime_attempts": attempts, "actual_cpu_result_created": False,
    "actual_source_transfer_created": False, "preparation_performed": False,
    "gpu_allocations": 0, "native_runs": 0, "model_calls": 0}
with (HERE / "bindings.json").open("x") as stream:
    json.dump(report, stream, sort_keys=True, indent=2)
    stream.write("\n")
print(json.dumps({"passed": True, "bindings": pin(HERE / "bindings.json"), "negative_checks": len(checks), "preparation_performed": False}))
