"""One 900-second allocation for the exact exposed 32-goal DEV diagnostic.

Separate one-use reservation; no training, transfer, retry, or benchmark status.
Both original origin receipts and separately approved exact metadata are required.
Existing source/data and model roots are fixed read-only external dependencies,
not falsely included in the small transferred input package.
"""

import argparse
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys

ROOT = Path(__file__).absolute().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from hydra_training_v5.peano_hydra import search_launch as safe
from hydra_training_v5.peano_hydra import frontier_pilot_launch as preserved

require = safe.require
canonical = safe.canonical
digest = safe.digest
decode = safe.decode
relative = safe.relative
directory = safe.directory
read = safe.read
fingerprint = safe.fingerprint
exists = safe.exists
inventory = safe.inventory
run = safe.run
HEX = safe.HEX
COMMIT = safe.COMMIT
JOB_ID = safe.JOB_ID

PROFILE = "peano-hydra-frontier-diagnostic-v1"
RUN_ID = "frontier-diagnostic-v1"
PACKAGE = "_deploy/hydra-frontier-diagnostic-v1"
REQUEST = PACKAGE + "/resource-request.json"
APPROVAL = PACKAGE + "/approval.json"
REQUEST_SCHEMA = "peano-hydra-frontier-diagnostic-resource-request-v1"
APPROVAL_SCHEMA = "peano-hydra-frontier-diagnostic-resource-approval-v1"
LEDGER_SCHEMA = "peano-hydra-frontier-diagnostic-held-job-ledger-v1"
LEDGER = "logs/hydra-frontier-diagnostic-v1.jsonl"
LOCK = "logs/.hydra-frontier-diagnostic-v1.lock"
SUBMISSIONS = "logs/submissions.tsv"
SUBMISSION_HEADER = safe.SUBMISSION_HEADER
REMOTE_PARENT = preserved.REMOTE_PARENT
REMOTE_CHILD = "experiments/frontier-diagnostic-v1"
ACCOUNT = preserved.ACCOUNT
PARTITION = preserved.PARTITION
CONFIRM = "PEANO-HYDRA-FRONTIER-DIAGNOSTIC-900-GPU-SECONDS"
STAGES = ("evaluate",)
JOBS = {"evaluate": "slurm/peano_hydra_frontier_diagnostic.sbatch"}
JOB_NAMES = {"evaluate": PROFILE + "-evaluate"}
RESERVATIONS = {"evaluate": {"seconds": 900, "gpus": 1, "cpus": 8, "memory_gib": 64}}
WALL = {"evaluate": "00:15:00"}
MODEL = dict(preserved.MODEL)
RUNTIME = dict(preserved.RUNTIME, login_python="/usr/bin/python3.9", local_semantic_check_minimum_python="3.11")
INPUTS = {"evaluation_request": PACKAGE + "/evaluation-request.json"}
EVALUATION_SCHEMA = "peano-hydra-frontier-dev-diagnostic-request-v1"
EVALUATION = {
    "cohort": "review-candidate-dev", "goal_count": 32, "roles": ["saved-corrected", "new-frontier"],
    "budgets": [8, 16], "goal_records": 128, "maximum_model_calls": 1536,
    "hard_wall_seconds": 900, "whole_allocation_soft_deadline_seconds": 720,
    "candidate_binding": "already-completed-frontier-training-v1-final-manifest",
    "training_jobs": 0, "self_training": False, "automatic_retry": False,
    "pilot_acceptance_eligible": False, "benchmark_acceptance_eligible": False,
    "self_training_readiness_eligible": False, "heldout_or_reserved_goals_scored": False,
}
DEV_PLAN = {"bytes": 32267, "sha256": "a8084683ea64e4128f4d34eea0753c67fc42a55772e1c698a5dbd62865878c4b",
            "plan_sha256": "f3875b785182c624abd3ea7b402420a125b38468d4971a1839028ca0ecd7343d"}
LOCAL_PROJECT = "/Users/bnaskrecki/codex/peano"
REMOTE_PROJECT = "/net/scratch/hscra/plgrid/plgnasqret/" + REMOTE_PARENT
EXTERNAL_SOURCES = {
    "saved-corrected": {
        "local": LOCAL_PROJECT + "/_deploy/hydra-search-v2-build-20260829/_deploy/hydra-search-v2/origin-source",
        "remote": REMOTE_PROJECT + "/_deploy/hydra-search-v2/origin-source",
        "source_manifest_sha256": "7cb1a9d35b078989991362a979c3ea0d6abac929fbfcf9ae1e457458a24e513d",
        "source_commit": "5a197363745c61156ce86d64a880fd47b5cb90e3",
    },
    "new-frontier": {
        "local": LOCAL_PROJECT + "/_deploy/hydra-frontier-training-execution-20260830",
        "remote": REMOTE_PROJECT + "/experiments/frontier-training-v1",
        "source_manifest_sha256": "346f9ac39c7d66ebb2c340922d77fc5dbef8a2e867cb1825dddcea92e616ca3b",
        "source_commit": "b08a6b1303d73217f6cc23800ae15e50b17db792",
    },
}

REMOTE_ARTIFACTS = {
    "saved-corrected": {
        "relative_directory": "_deploy/hydra-search-v2/model",
        "adapter_manifest_sha256": "172a6928710192c5348dcd7b04f71e6d4d3f75dfa1ab0f7f5add601769704a7c",
    },
    "new-frontier": {
        "relative_directory": "experiments/frontier-training-v1/results/peano-hydra/qwen3-1.7b-authority-primitive-v28-f64b5f100c9c-frontier-training-v1",
        "adapter_manifest_sha256": "5795d5a3d70f781f56f81e83c2295c887d0949795924f4208f45d26a3ef89b68",
    },
}
EVALUATION_OUTPUT = "results/peano-hydra/evaluations/frontier-diagnostic-v1"
REQUIRED_SOURCES = frozenset(tuple(JOBS.values()) + (
    "training/peano_hydra/frontier_diagnostic_launch.py",
    "training/peano_hydra/frontier_diagnostic_run.py",
    "training/peano_hydra/frontier_benchmark_run.py",
    "training/peano_hydra/frontier_benchmark_protocol.py",
    "training/peano_hydra/frontier_pilot_launch.py",
    "training/peano_hydra/frontier_training_launch.py",
    "training/peano_hydra/search_launch.py",
    "training/peano_hydra/origin_bridge.py",
    "training/peano_hydra/scaling_evaluation.py",
    "training/peano_hydra/scaling_experiment.py",
    "training/peano_hydra/scaling_admission.py",
    "training/peano_hydra/helios_runtime.py",
    "training/peano_hydra/corrective_workflow.py",
    "training/peano_hydra/review_runtime.py",
    "training/peano_policy/runtime.py",
    "training/peano_policy/requirements-helios.lock",
    "scripts/helios_hydra_frontier_diagnostic.sh",
    "scripts/run_peano_hydra_frontier_diagnostic.sh",
    "scripts/prepare_peano_hydra_frontier_diagnostic_launch.py",
    "scripts/eval_peano_hydra_frontier_diagnostic.py",
    "scripts/check_peano_hydra_frontier_runtime.py",
))
MAX_METADATA, MAX_TOTAL = preserved.MAX_METADATA, preserved.MAX_TOTAL
REQUEST_FIELDS = frozenset((
    "schema", "status", "profile", "run_id", "source_commit", "source_files", "payloads", "payloads_sha256",
    "inputs", "model", "evaluation", "existing_remote_artifacts", "existing_read_only_sources", "reservations", "maximum_aggregate_gpu_seconds",
    "maximum_concurrent_gpus", "automatic_retry", "resume", "refunds", "runtime_dependencies",
    "transfer_authorized", "gpu_execution_authorized", "training_authorized", "self_training_authorized", "semantic_admission",
))


def output_protections(*, include_package=True, extra=()):
    """Read-only external inputs remain protected even when absent locally."""
    roots = [Path(value[place]) for value in EXTERNAL_SOURCES.values() for place in ("local", "remote")]
    roots.extend(Path(REMOTE_PROJECT) / value["relative_directory"] for value in REMOTE_ARTIFACTS.values())
    roots.append(Path(LOCAL_PROJECT) / "_deploy/hydra-search-v2-build-20260829/_deploy/hydra-search-v2/model")
    roots.extend(ROOT / prefix for prefix in ("training", "peano-lab", "scripts", "slurm", ".git"))
    if include_package:
        roots.append(ROOT / PACKAGE)
    roots.extend(Path(path) for path in extra)
    return tuple(dict.fromkeys(roots))


def request_template():
    """No missing review, source identity or approval is manufactured."""
    body = {
        "schema": REQUEST_SCHEMA, "status": "draft-missing-prerequisites",
        "profile": PROFILE, "run_id": RUN_ID, "source_commit": None, "source_files": {},
        "payloads": {}, "payloads_sha256": None, "inputs": dict(INPUTS), "model": dict(MODEL),
        "evaluation": dict(EVALUATION), "existing_remote_artifacts": REMOTE_ARTIFACTS,
        "existing_read_only_sources": EXTERNAL_SOURCES,
        "reservations": {key: dict(value) for key, value in RESERVATIONS.items()},
        "maximum_aggregate_gpu_seconds": 900, "maximum_concurrent_gpus": 1,
        "automatic_retry": False, "resume": False, "refunds": False,
        "runtime_dependencies": dict(RUNTIME), "transfer_authorized": False, "gpu_execution_authorized": False,
        "training_authorized": False, "self_training_authorized": False, "semantic_admission": None,
    }
    return decode(canonical(body))


def ready_request(source_commit):
    require(exists(".git"), "request preparation requires its real clean execution Git snapshot")
    require(type(source_commit) is str and COMMIT.fullmatch(source_commit), "explicit frozen execution commit required")
    environment = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    environment.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL="/dev/null", GIT_NO_REPLACE_OBJECTS="1",
                       GIT_NO_LAZY_FETCH="1", GIT_OPTIONAL_LOCKS="0")
    tracked = safe.run(["git", "-C", str(ROOT), "ls-files", "-z"], environment).split("\0")
    require(tracked[-1] == "" and 1 <= len(tracked) - 1 <= 4096
            and len(set(tracked[:-1])) == len(tracked) - 1, "bounded unique tracked execution inventory required")
    sources = {relative(name): fingerprint(name)[0] for name in tracked[:-1]}
    safe._execution_commit(source_commit, {name: value["sha256"] for name, value in sources.items()})
    payloads = {name: fingerprint(name)[0] for name in sorted(inventory(PACKAGE) - {REQUEST, APPROVAL})}
    request = request_template()
    request.update(status="ready-for-explicit-resource-approval", source_commit=source_commit,
                   source_files=sources, payloads=payloads, payloads_sha256=digest(payloads))
    request["semantic_admission"] = semantic_check(request)
    return validate_request(request)


def _json(name):
    raw = read(name, MAX_METADATA)
    # The shared duplicate/nonfinite-rejecting decoder has a 4 MiB limit.
    # Large corpus manifests are bounded separately and never executed.
    require(len(raw) <= safe.MAX_JSON, "launch JSON metadata exceeds the 4 MiB gate")
    return decode(raw)


def _seal(record, field):
    require(type(record) is dict and type(record.get(field)) is str
            and HEX.fullmatch(record[field])
            and record[field] == digest({k: v for k, v in record.items() if k != field}),
            "semantic metadata seal differs: " + field)


def _files(mapping, label):
    require(type(mapping) is dict and 0 < len(mapping) <= 4096, label + " inventory is missing/oversized")
    total = 0
    for name, expected in mapping.items():
        relative(name)
        require(type(expected) is dict and set(expected) == {"bytes", "sha256"}
                and type(expected["bytes"]) is int and 0 <= expected["bytes"] <= safe.MAX_PAYLOAD
                and type(expected["sha256"]) is str and HEX.fullmatch(expected["sha256"]),
                label + " has an invalid file identity")
        total += expected["bytes"]
        require(total <= MAX_TOTAL, label + " exceeds the total byte cap")
        require(fingerprint(name)[0] == expected, label + " changed: " + name)


def _evaluation_metadata(request):
    """Login3.9 byte/claim joins; approved local semantics are checked separately."""
    value = _json(INPUTS["evaluation_request"])
    require(value.get("schema") == EVALUATION_SCHEMA
            and value.get("status") == "ready-for-explicit-resource-approval"
            and value.get("profile") == PROFILE and value.get("run_id") == RUN_ID,
            "both original origin receipts and the fixed DEV diagnostic are required")
    _seal(value, "request_sha256")
    require(value.get("existing_remote_artifacts") == REMOTE_ARTIFACTS
            and value.get("existing_read_only_sources") == EXTERNAL_SOURCES
            and value.get("limits") == EVALUATION,
            "fixed diagnostic origins or resource bounds changed")
    claims = ("gpu_execution_authorized", "sealed_benchmark", "research_claim_eligible",
              "pilot_acceptance_eligible", "benchmark_acceptance_eligible", "self_training_readiness_eligible",
              "heldout_or_reserved_goals_scored")
    require(all(value.get(k) is False for k in claims), "DEV diagnostics cannot authorize a benchmark or training")
    descriptors = [value.get("evaluation_plan")]
    for key, role in (("baseline", "saved-corrected"), ("candidate", "new-frontier")):
        origin = value.get(key)
        require(type(origin) is dict and origin.get("source_locations") == EXTERNAL_SOURCES[role],
                "original preserved source locations must be fixed external read-only inputs")
        descriptors.extend(origin.get(k) for k in ("source_manifest", "adapter_manifest", "receipt"))
    evidence = value.get("completed_training")
    require(type(evidence) is dict and set(evidence) == {"resource_request", "resource_approval",
        "launch_receipt", "terminal_observation"}, "completed training evidence is incomplete")
    descriptors.extend(evidence.values())
    for item in descriptors:
        require(type(item) is dict and set(item) == {"path", "bytes", "sha256"}
                and request["payloads"].get(item["path"]) == {k: item[k] for k in ("bytes", "sha256")},
                "required diagnostic metadata is absent or outside the exact input package")
    descriptor = value["evaluation_plan"]
    require({k: descriptor[k] for k in ("bytes", "sha256")} == {k: DEV_PLAN[k] for k in ("bytes", "sha256")},
            "the original 32-goal DEV plan cannot be replaced or extended")
    plan = _json(descriptor["path"])
    _seal(plan, "plan_sha256")
    require(plan.get("plan_sha256") == DEV_PLAN["plan_sha256"]
            and plan.get("schema") == "peano-hydra-frontier-matched-budget-plan-v1"
            and plan.get("cohort") == EVALUATION["cohort"]
            and plan.get("roles") == EVALUATION["roles"] and plan.get("budgets") == [8, 16]
            and len(plan.get("goals", [])) == 32 and len(plan.get("ordered_slots", [])) == 128
            and plan.get("max_model_calls_total") == 1536,
            "only the exact exposed DEV factorial diagnostic may run")
    callers = value.get("caller_sources")
    require(type(callers) is dict and len(callers) > 0
            and all(request["source_files"].get(k) == v for k, v in callers.items()),
            "diagnostic caller source is not part of the exact approved execution source")
    assertion = request["semantic_admission"]
    require(type(assertion) is dict and set(assertion) == {"schema", "status", "evaluation_request_sha256",
        "source_files_sha256", "payloads_sha256", "summary", "checker_python"}
        and assertion["schema"] == "peano-hydra-frontier-diagnostic-cpu-admission-v1"
        and assertion["status"] == "passed"
        and assertion["evaluation_request_sha256"] == request["payloads"][INPUTS["evaluation_request"]]["sha256"]
        and assertion["source_files_sha256"] == digest(request["source_files"])
        and assertion["payloads_sha256"] == request["payloads_sha256"]
        and type(assertion["checker_python"]) is list and len(assertion["checker_python"]) == 3
        and all(type(v) is int for v in assertion["checker_python"])
        and tuple(assertion["checker_python"]) >= (3, 11, 0),
        "a real separately approved source/input-bound local semantic check is required")
    summary = assertion["summary"]
    require(type(summary) is dict and summary.get("status") == "completed-origin-metadata-checked-not-executed"
            and summary.get("request_file_sha256") == assertion["evaluation_request_sha256"]
            and summary.get("candidate_adapter_manifest_sha256") == REMOTE_ARTIFACTS["new-frontier"]["adapter_manifest_sha256"]
            and summary.get("training_job_id") == "21438102" and summary.get("model_weights_loaded") is False
            and summary.get("existing_remote_artifact_bytes_checked") is False
            and summary.get("external_source_and_preparation_bytes_checked") is True
            and summary.get("remote_artifact_recheck_required_before_inference") is True
            and all(summary.get(k) is False for k in claims),
            "CPU admission cannot claim model quality, benchmark acceptance or completed remote artifact checks")


def validate_request(request):
    require(type(request) is dict and set(request) == REQUEST_FIELDS
            and request.get("schema") == REQUEST_SCHEMA
            and request.get("status") == "ready-for-explicit-resource-approval"
            and request.get("profile") == PROFILE and request.get("run_id") == RUN_ID,
            "a draft or incomplete evaluation-only resource request cannot allocate")
    for key, expected in (("inputs", INPUTS), ("model", MODEL), ("evaluation", EVALUATION),
                          ("existing_remote_artifacts", REMOTE_ARTIFACTS), ("existing_read_only_sources", EXTERNAL_SOURCES),
                          ("reservations", RESERVATIONS),
                          ("runtime_dependencies", RUNTIME)):
        require(canonical(request.get(key)) == canonical(expected), "fixed resource scope changed: " + key)
    require(type(request.get("source_commit")) is str and COMMIT.fullmatch(request["source_commit"]),
            "real frozen evaluation source identity is required")
    require(type(request["maximum_aggregate_gpu_seconds"]) is int and request["maximum_aggregate_gpu_seconds"] == 900
            and type(request["maximum_concurrent_gpus"]) is int and request["maximum_concurrent_gpus"] == 1
            and all(request[name] is False for name in ("automatic_retry", "resume", "refunds", "training_authorized",
                    "self_training_authorized", "transfer_authorized", "gpu_execution_authorized")),
            "resource request changed its fixed no-training/no-retry scope or claims authorization")
    sources, payloads = request["source_files"], request["payloads"]
    _files(sources, "execution source")
    require(REQUIRED_SOURCES <= set(sources) and not any(name.startswith((".git/", PACKAGE + "/")) for name in sources),
            "execution inventory omits the new job or mixes source and inputs")
    for prefix in ("training", "peano-lab/py", "scripts", "slurm"):
        require(inventory(prefix) == {name for name in sources if name.startswith(prefix + "/")},
                "execution tree has missing, untracked or unapproved leaves: " + prefix)
    _files(payloads, "input payload")
    require(all(name.startswith(PACKAGE + "/") and name not in (REQUEST, APPROVAL) for name in payloads)
            and set(INPUTS.values()) <= set(payloads) and digest(payloads) == request["payloads_sha256"]
            and inventory(PACKAGE) - {REQUEST, APPROVAL} == set(payloads), "closed input inventory changed")
    require(sources["training/peano_policy/requirements-helios.lock"]["sha256"] == RUNTIME["requirements_sha256"],
            "the existing Helios runtime lock changed")
    _evaluation_metadata(request)
    return request


def semantic_check(request):
    """Read-only original-receipt/source/admission checking, no proof or model execution."""
    require(sys.version_info >= (3, 11), "semantic admission requires the reviewed Python>=3.11 CPU runtime")
    if str(ROOT / "peano-lab/py") not in sys.path:
        sys.path.insert(0, str(ROOT / "peano-lab/py"))
    from hydra_training_v5.peano_hydra import frontier_diagnostic_run as diagnostic
    pin = request["payloads"][INPUTS["evaluation_request"]]["sha256"]
    checked = diagnostic.check_request(ROOT / INPUTS["evaluation_request"], pin)
    require(checked.raw_sha256 == pin, "semantic diagnostic request changed")
    return {"schema": "peano-hydra-frontier-diagnostic-cpu-admission-v1", "status": "passed",
        "evaluation_request_sha256": pin, "source_files_sha256": digest(request["source_files"]),
        "payloads_sha256": request["payloads_sha256"], "summary": checked.summary(),
        "checker_python": list(sys.version_info[:3])}


def validate_metadata(expected_approval_sha256):
    require(type(expected_approval_sha256) is str and HEX.fullmatch(expected_approval_sha256),
            "external RAW resource approval SHA required")
    raw = read(APPROVAL)
    require(hashlib.sha256(raw).hexdigest() == expected_approval_sha256, "external resource approval bytes differ")
    approval = decode(raw)
    require(set(approval) == {"schema", "profile", "run_id", "approved", "approval_reference", "request_file_sha256"}
            and approval.get("schema") == APPROVAL_SCHEMA and approval.get("profile") == PROFILE
            and approval.get("run_id") == RUN_ID and approval.get("approved") is True
            and type(approval.get("approval_reference")) is str
            and 1 <= len(approval["approval_reference"]) <= 2048
            and approval["approval_reference"].strip() == approval["approval_reference"],
            "a proposal is not a separately supplied explicit resource approval")
    request_raw = read(REQUEST)
    require(hashlib.sha256(request_raw).hexdigest() == approval["request_file_sha256"],
            "resource approval does not pin this exact RAW request")
    request = validate_request(decode(request_raw))
    require(read(APPROVAL) == raw and read(REQUEST) == request_raw, "approval or request changed during admission")
    return approval, request


def _identity(approval, request, expected_sha, *, local=False):
    sources = {name: value["sha256"] for name, value in request["source_files"].items()}
    if local:
        require(exists(".git"), "local launch requires its own clean frozen Git checkout")
    synced = safe._execution_commit(request["source_commit"], sources)
    return {"approval_sha256": expected_sha, "request_file_sha256": approval["request_file_sha256"],
            "source_commit": request["source_commit"], "source_files_sha256": digest(request["source_files"]),
            "payloads_sha256": request["payloads_sha256"], "synced_at": synced,
            "job_script_sha256": {stage: sources[JOBS[stage]] for stage in STAGES}}


def _remote_root():
    scratch = os.environ.get("SCRATCH")
    require(type(scratch) is str and scratch.startswith("/") and ".." not in Path(scratch).parts,
            "configured SCRATCH is required")
    parent = Path(scratch) / REMOTE_PARENT
    require(ROOT == parent / REMOTE_CHILD, "frontier must use its own fixed experiment directory")
    fd = directory(ROOT)
    os.close(fd)
    return parent


def _elapsed_seconds(value):
    require(type(value) is str and re.fullmatch(r"(?:[0-9]{1,3}-)?[0-9]{2}:[0-5][0-9]:[0-5][0-9]", value),
            "bounded scheduler RunTime is required for the whole-allocation deadline")
    days, separator, clock = value.partition("-")
    if not separator:
        days, clock = "0", value
    hours, minutes, seconds = map(int, clock.split(":"))
    return int(days) * 86400 + hours * 3600 + minutes * 60 + seconds


def _snapshot(raw, stage, job, predecessor=None, running=False):
    require(type(raw) is str and 0 < len(raw.encode()) <= 65536 and len(raw.strip().splitlines()) == 1,
            "held controller record exceeds its bound")
    keys = {"JobId", "JobName", "WorkDir", "JobState", "Reason", "Priority", "Dependency", "Requeue",
            "Account", "Partition", "TimeLimit", "NumNodes", "NumCPUs", "ReqTRES", "RunTime"}
    fields = {}
    for match in re.finditer(r"(?:^|\s)([A-Za-z][A-Za-z0-9]*)=(\S*)", raw):
        key, value = match.groups()
        if key in keys:
            require(key not in fields, "duplicate guarded controller field")
            fields[key] = value
    elapsed = _elapsed_seconds(fields.get("RunTime"))
    require(elapsed <= 900 and (running or elapsed == 0), "scheduler elapsed time exceeds this fresh diagnostic")
    dependency = "(null)" if predecessor is None else "afterok:" + predecessor
    allowed_dependencies = ((dependency, dependency + "(fulfilled)", "(null)") if running
                            else (dependency, dependency + "(unfulfilled)"))
    require(set(fields) == keys and fields["JobId"] == job and fields["JobName"] == JOB_NAMES[stage]
            and fields["WorkDir"] == str(ROOT)
            and (fields["JobState"] == "RUNNING" if running else
                 fields["JobState"] == "PENDING" and fields["Reason"] == "JobHeldUser" and fields["Priority"] == "0")
            and fields["Dependency"] in allowed_dependencies
            and fields["Requeue"] == "0" and fields["Account"] == ACCOUNT
            and fields["Partition"] == PARTITION and fields["TimeLimit"] == WALL[stage]
            and fields["NumNodes"] in ("1", "1-1") and fields["NumCPUs"] == "8",
            "held frontier job changed its identity, dependency, resources or restart policy")
    resources = {}
    for item in fields["ReqTRES"].split(","):
        key, sep, value = item.partition("=")
        require(sep and key and value and key not in resources, "ambiguous controller resources")
        resources[key] = value
    require(resources.get("cpu") == "8" and resources.get("node") == "1"
            and resources.get("gres/gpu") == "1" and resources.get("mem") in ("64G", "65536M", "67108864K")
            and all(v == "1" for k, v in resources.items() if k.startswith("gres/gpu:")),
            "controller changed the one-GPU/64 GiB reservation")
    return {"raw": raw, "raw_sha256": hashlib.sha256(raw.encode()).hexdigest(), "fields": fields}


def _header(identity):
    return {"kind": "header", "schema": LEDGER_SCHEMA, "profile": PROFILE, "run_id": RUN_ID,
            "identity": identity, "reservations": RESERVATIONS, "maximum_aggregate_gpu_seconds": 900,
            "maximum_concurrent_gpus": 1, "automatic_retry": False, "resume": False, "refunds": False}


def load_ledger(identity):
    state = {"events": [], "raw": b"", "phase": "empty", "jobs": {}, "created_at": None, "gpu_seconds": 0}
    if not exists(LEDGER):
        return state
    raw = read(LEDGER, safe.MAX_LEDGER)
    lines = raw.splitlines(keepends=True)
    require(raw.endswith(b"\n") and 1 <= len(lines) <= 6, "one-use evaluation ledger is truncated or extended")
    kinds = ("header", "reserve", "evaluate-accepted", "held-validated", "release-authorized", "evaluate-released")
    previous = "0" * 64
    for index, line in enumerate(lines):
        event = decode(line)
        require(set(event) == {"index", "previous_sha256", "payload", "sha256"}
                and type(event["index"]) is int and event["index"] == index and event["previous_sha256"] == previous
                and event["sha256"] == digest({k: event[k] for k in ("index", "previous_sha256", "payload")})
                and canonical(event) + b"\n" == line, "ledger canonical hash chain differs")
        value = event["payload"]
        require(type(value) is dict and value.get("kind") == kinds[index], "evaluation ledger stage order changed")
        if index == 0:
            require(canonical(value) == canonical(_header(identity)), "ledger belongs to another approval/source")
        elif index == 1:
            require(set(value) == {"kind", "reservations", "created_at"}
                    and value["reservations"] == RESERVATIONS and type(value["created_at"]) is str
                    and re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z", value["created_at"]),
                    "ledger reservation differs")
            state["gpu_seconds"], state["created_at"] = 900, value["created_at"]
        elif index == 2:
            require(set(value) == {"kind", "job_id", "dependency_job_id"}
                    and type(value["job_id"]) is str and JOB_ID.fullmatch(value["job_id"])
                    and value["dependency_job_id"] is None, "accepted evaluation job changed or added a dependency")
            state["jobs"]["evaluate"] = value["job_id"]
        elif index == 3:
            require(set(value) == {"kind", "snapshots"} and set(value["snapshots"]) == {"evaluate"},
                    "held evaluation barrier has another job")
            snapshot = value["snapshots"]["evaluate"]
            require(canonical(snapshot) == canonical(_snapshot(snapshot["raw"], "evaluate", state["jobs"]["evaluate"])),
                    "held evaluation snapshot changed")
        elif index == 4:
            require(set(value) == {"kind", "jobs"} and value["jobs"] == state["jobs"], "release barrier changed")
        else:
            require(set(value) == {"kind", "job_id"} and value["job_id"] == state["jobs"]["evaluate"],
                    "evaluation release acknowledgment changed")
        state["events"].append(event)
        previous, state["phase"] = event["sha256"], kinds[index]
    state["raw"] = raw
    return state


def _record(state, payload):
    event = {"index": len(state["events"]),
             "previous_sha256": state["events"][-1]["sha256"] if state["events"] else "0" * 64,
             "payload": payload}
    event["sha256"] = digest(event)
    safe._append(LEDGER, state["raw"], canonical(event) + b"\n", safe.MAX_LEDGER)


def _submission_row(stage, state, identity):
    require(stage == "evaluate", "only one evaluation job belongs to this profile")
    return [state["created_at"], state["jobs"][stage], JOBS[stage], "", str(ROOT),
            identity["source_commit"], "false", identity["synced_at"], identity["job_script_sha256"][stage]]


def _history(state, identity):
    rows, _ = safe._submissions()
    own = [row for row in rows if row[2] in JOBS.values() or row[1] in state["jobs"].values()]
    require(own == [_submission_row(stage, state, identity) for stage in STAGES if stage in state["jobs"]],
            "frontier submission history differs; no historical adoption or refund")


def _queue_history(state):
    parent = _remote_root()
    user = os.environ.get("USER", "")
    require(re.fullmatch(r"[A-Za-z0-9._-]{1,64}", user), "scheduler user is not declared")
    accepted = {job: JOB_NAMES[stage] for stage, job in state["jobs"].items()}
    active = set()
    for line in run(["squeue", "-h", "-u", user, "-o", "%i|%Z|%j|%T"]).splitlines():
        fields = line.split("|")
        require(len(fields) == 4 and JOB_ID.fullmatch(fields[0]), "ambiguous scheduler queue record")
        job, workdir, name, _ = fields
        if workdir == str(parent) or workdir.startswith(str(parent) + "/") or name in JOB_NAMES.values():
            require(job in accepted and name == accepted[job] and workdir == str(ROOT) and job not in active,
                    "another project allocation is active")
            active.add(job)
    seen = set()
    args = ["sacct", "-n", "-P", "-X", "-u", user, "--starttime=2026-08-30",
            "--name=" + ",".join(JOB_NAMES[stage] for stage in STAGES),
            "--format=JobIDRaw,JobName%80,WorkDir%4096"]
    for line in run(args).splitlines():
        if not line.strip():
            continue
        fields = line.split("|")
        require(len(fields) in (3, 4) and (len(fields) == 3 or fields[3] == ""), "ambiguous accounting record")
        job, name, workdir = fields[:3]
        require(job in accepted and job not in seen and name == accepted[job] and workdir == str(ROOT),
                "unrecorded frontier allocation; deleting a ledger does not refund")
        seen.add(job)
    require(seen | active == set(accepted), "accepted frontier job is missing from queue/accounting")


def outputs(jobs):
    return {"evaluation": EVALUATION_OUTPUT}


def _options(stage, approval_sha):
    require(stage == "evaluate", "only the reviewed evaluation job may be submitted")
    result = ["sbatch", "--parsable", "--hold", "--no-requeue", "--kill-on-invalid-dep=yes",
              "--account=" + ACCOUNT, "--partition=" + PARTITION, "--nodes=1", "--ntasks=1",
              "--cpus-per-task=8", "--mem=64G", "--gres=gpu:1", "--time=" + WALL[stage], "--signal=B:USR1@180",
              "--chdir=" + str(ROOT), "--export=ALL", "--job-name=" + JOB_NAMES[stage],
              "--output=logs/" + JOB_NAMES[stage] + "-%j.out", "--error=logs/" + JOB_NAMES[stage] + "-%j.err"]
    return result + [JOBS[stage], approval_sha]


def launch(expected_approval_sha256, *, submit=False, expected_commit=None):
    require(type(submit) is bool and "SLURM_JOB_ID" not in os.environ, "submission cannot nest inside a job")
    require(not any(k.startswith("SBATCH_") for k in os.environ), "SBATCH overrides are unauthorized")
    _remote_root()
    approval, request = validate_metadata(expected_approval_sha256)
    identity = _identity(approval, request, expected_approval_sha256)
    require(identity["source_commit"] == expected_commit and identity["synced_at"] is not None,
            "remote launch requires the exact clean staged source provenance")
    fd = -1
    try:
        if submit:
            parent = directory(ROOT)
            try:
                try:
                    os.mkdir("logs", 0o700, dir_fd=parent)
                except FileExistsError:
                    pass
            finally:
                os.close(parent)
            parent = directory(ROOT / "logs")
            try:
                fd = os.open(Path(LOCK).name, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK,
                             0o600, dir_fd=parent)
            finally:
                os.close(parent)
            info = os.fstat(fd)
            require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_size == 0, "unsafe reservation lock")
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        state = load_ledger(identity)
        require(not state["events"], "frontier budget already opened/charged; no retry, resume, reset or refund")
        _history(state, identity)
        _queue_history(state)
        require(not exists(EVALUATION_OUTPUT), "evaluation output already exists; no resume or adoption")
        if not submit:
            return {"status": "test-only", "allocation_performed": False, "scheduler_submission_tested": False,
                    "reservations": RESERVATIONS, "maximum_aggregate_gpu_seconds": 900, "automatic_retry": False}
        require(_identity(*validate_metadata(expected_approval_sha256), expected_approval_sha256) == identity,
                "approved inputs or source changed before reservation")

        def record(payload):
            _record(state, payload)
            return load_ledger(identity)

        state = record(_header(identity))
        state = record({"kind": "reserve", "reservations": RESERVATIONS,
                        "created_at": datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"})
        # Charge the complete one-job budget durably BEFORE sbatch. An uncertain
        # scheduler response is never automatically retried or refunded.
        for stage in STAGES:
            raw = run(_options(stage, expected_approval_sha256)).strip()
            require(re.fullmatch(r"[1-9][0-9]{0,19}(?:;[A-Za-z0-9_-]{1,64})?", raw),
                    "ambiguous submission; all 900 GPU seconds remain charged and jobs remain held")
            job = raw.split(";", 1)[0]
            state = record({"kind": stage + "-accepted", "job_id": job, "dependency_job_id": None})
            rows, before = safe._submissions()
            require(job not in {row[1] for row in rows}, "accepted job already exists in submission history")
            added = ((SUBMISSION_HEADER if not before else "") + "\t".join(_submission_row(stage, state, identity)) + "\n").encode()
            safe._append(SUBMISSIONS, before, added, safe.MAX_JSON)
            _history(state, identity)
            _queue_history(state)
        require(all(not exists(path) for path in outputs(state["jobs"]).values()), "output/checkpoints already exist")
        snapshots = {stage: _snapshot(run(["scontrol", "-o", "show", "job", state["jobs"][stage]]), stage,
                     state["jobs"][stage]) for stage in STAGES}
        state = record({"kind": "held-validated", "snapshots": snapshots})
        require(_identity(*validate_metadata(expected_approval_sha256), expected_approval_sha256) == identity,
                "approved inputs changed before release; allocations remain held and charged")
        state = record({"kind": "release-authorized", "jobs": state["jobs"]})
        for stage in STAGES:
            # Runtime may observe the durable barrier before release returns.
            fcntl.flock(fd, fcntl.LOCK_UN)
            run(["scontrol", "release", state["jobs"][stage]])
            safe._await_lock(fd, fcntl.LOCK_EX)
            state = record({"kind": stage + "-released", "job_id": state["jobs"][stage]})
        return {"status": "submitted", "profile": PROFILE, "run_id": RUN_ID, "jobs": state["jobs"],
                "reserved_gpu_seconds": 900, "maximum_concurrent_gpus": 1, "automatic_retry": False,
                "resume": False, "refunds": False, "ledger": LEDGER, "outputs": outputs(state["jobs"])}
    finally:
        if fd >= 0:
            os.close(fd)


def check_job_reservation(expected_approval_sha256, stage):
    """Read-only gate for an exact job admitted through this held evaluation reservation."""
    require(stage in STAGES, "unknown frontier stage")
    _remote_root()
    job = os.environ.get("SLURM_JOB_ID", "")
    require(JOB_ID.fullmatch(job) and os.environ.get("SLURM_RESTART_COUNT", "0") == "0"
            and os.environ.get("PEANO_JOB_SCRIPT") == JOBS[stage]
            and os.environ.get("PEANO_HYDRA_PROFILE") == PROFILE
            and os.environ.get("SLURM_SUBMIT_DIR") == str(ROOT)
            and not any(k.startswith("SBATCH_") for k in os.environ),
            "scheduled frontier identity, restart or overrides differ")
    approval, request = validate_metadata(expected_approval_sha256)
    identity = _identity(approval, request, expected_approval_sha256)
    parent = directory(ROOT / "logs")
    try:
        fd = os.open(Path(LOCK).name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
    finally:
        os.close(parent)
    try:
        info = os.fstat(fd)
        require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_size == 0, "unsafe reservation lock")
        safe._await_lock(fd, fcntl.LOCK_SH)
        state = load_ledger(identity)
        require(state["phase"] in ("release-authorized", "evaluate-released")
                and state["jobs"].get(stage) == job and state["gpu_seconds"] == 900,
                "job has no durable exact frontier reservation/release barrier")
        _history(state, identity)
        snapshot = _snapshot(run(["scontrol", "-o", "show", "job", job]), stage, job, running=True)
        return {"status": "job-verified", "stage": stage, "job_id": job, "jobs": state["jobs"],
                "approval_sha256": expected_approval_sha256,
                "request_file_sha256": approval["request_file_sha256"],
                "evaluation_request_sha256": request["payloads"][INPUTS["evaluation_request"]]["sha256"],
                "source_commit": identity["source_commit"], "allocation_performed": False,
                "allocation_elapsed_seconds": _elapsed_seconds(snapshot["fields"]["RunTime"])}
    finally:
        os.close(fd)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--check", action="store_true")
    modes.add_argument("--check-job", choices=STAGES)
    modes.add_argument("--test-only", action="store_true")
    modes.add_argument("--submit", action="store_true")
    parser.add_argument("--approval-sha256", required=True, help="externally supplied RAW approval-file SHA")
    parser.add_argument("--source-commit")
    parser.add_argument("--local", action="store_true")
    parser.add_argument("--confirm")
    args = parser.parse_args(argv)
    try:
        require(args.confirm == CONFIRM if args.submit else args.confirm is None,
                "real submission requires the separate explicit 900 GPU-second confirmation")
        require(not args.local or args.check, "--local belongs only to pre-SSH metadata checking")
        if args.check:
            require(args.source_commit is None, "metadata check accepts no source override")
            approval, request = validate_metadata(args.approval_sha256)
            identity = _identity(approval, request, args.approval_sha256, local=args.local)
            if args.local:
                fresh = semantic_check(request)
                require({k: v for k, v in fresh.items() if k != "checker_python"}
                        == {k: v for k, v in request["semantic_admission"].items() if k != "checker_python"},
                        "local diagnostic semantic admission changed before SSH")
            result = {"status": "metadata-verified", "source_commit": identity["source_commit"],
                      "evaluation_request_sha256": request["payloads"][INPUTS["evaluation_request"]]["sha256"],
                      "helper_sha256": request["source_files"]["training/peano_hydra/frontier_diagnostic_launch.py"]["sha256"],
                      "approval_sha256": args.approval_sha256, "allocation_performed": False}
        elif args.check_job:
            require(args.source_commit is None, "job check accepts no source override")
            result = check_job_reservation(args.approval_sha256, args.check_job)
        else:
            result = launch(args.approval_sha256, submit=args.submit, expected_commit=args.source_commit)
        print(json.dumps(result, sort_keys=True, allow_nan=False), flush=True)
        return 0
    except (ValueError, TypeError, KeyError, OSError, RuntimeError) as error:
        print("frontier-diagnostic-launch: " + " ".join(str(error).split()), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
