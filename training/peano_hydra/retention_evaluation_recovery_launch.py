"""One new held evaluation reservation for the saved retention adapter.

The original training and failed evaluation remain charged in their original
unchanged ledgers. This profile has no training stage, retry, resume or refund.
A new exact approval derives from the retained standing user directive. This
stdlib resource gate binds the historical admission bytes; scientific admission
is separately mandatory in the checked caller before any framework is loaded.
"""
import argparse
import datetime
import fcntl
import hashlib
import os
from pathlib import Path
import re
import stat
import sys

ROOT = Path(__file__).absolute().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from training.peano_hydra import search_launch as safe

require, canonical, digest, decode = safe.require, safe.canonical, safe.digest, safe.decode
read, fingerprint, exists, directory = safe.read, safe.fingerprint, safe.exists, safe.directory
PROFILE = "peano-hydra-retention-evaluation-recovery-v1"
RUN_ID = "retention-evaluation-recovery-v1"
PACKAGE = "_deploy/hydra-retention-evaluation-recovery-v1"
REQUEST = PACKAGE + "/resource-request.json"
APPROVAL = PACKAGE + "/approval.json"
REQUEST_SCHEMA = "peano-hydra-retention-evaluation-recovery-resource-request-v1"
APPROVAL_SCHEMA = "peano-hydra-retention-evaluation-recovery-standing-resource-approval-v1"
LEDGER_SCHEMA = "peano-hydra-retention-evaluation-recovery-held-ledger-v1"
REMOTE_PARENT = "codex-control/projects/peano-lab-training"
REMOTE_CHILD = "experiments/retention-evaluation-recovery-v1"
ACCOUNT = "plgccaiautore2026-gpu-gh200"
PARTITION = "plgrid-gpu-gh200"
STAGES = ("evaluate",)
RESERVATIONS = {"evaluate": {"seconds": 3600, "gpus": 1, "cpus": 8, "memory_gib": 64}}
WALL = {"evaluate": "01:00:00"}
JOBS = {"evaluate": "slurm/peano_hydra_retention_evaluation_recovery.sbatch"}
JOB_NAMES = {"evaluate": PROFILE + "-evaluate"}
LEDGERS = {"evaluate": "logs/hydra-retention-evaluation-recovery-v1-evaluate.jsonl"}
LOCK = "logs/.hydra-retention-evaluation-recovery-v1.lock"
EVALUATION_OUTPUT = "results/peano-hydra/evaluations/retention-evaluation-recovery-v1"
OUTPUTS = {"evaluate": EVALUATION_OUTPUT}
MODEL = {"model_id": "Qwen/Qwen3-1.7B-Base", "revision": "ea980cb0a6c2ae4b936e82123acc929f1cec04c1"}
MODEL_MANIFEST = {"bytes": 191597, "sha256": "cdacbda7777568120029b671374aaf16e994f2da2a54b867a00c81ece086d6ca"}
EVALUATION_PLAN = {"path": PACKAGE + "/evaluation-plan.json", "bytes": 110574,
                   "sha256": "7dd90249324b82846f6cbae6e157c5fef09e22e0b058b73822f11aae1b95f635"}
RUNTIME = dict(safe.RUNTIME_DEPENDENCIES)
AUTHORITY_QUOTE = "You don't have to ask my permission to run new experiments."
STANDING_DIRECTIVE_SHA = "04ac3b5997b4f2a78c4ce41642b9e596d63abf1c82ec2441ab240b0f78fd5778"
PRODUCER_COMMIT = "4aeae795c8cb5bfc622c9943359b5b38446089b9"
PRODUCER_JOB = "21456251"
FAILED_EVALUATION_JOB = "21457058"
PRODUCER_CHILD = "experiments/retention-pilot-v1"
PRODUCER_PACKAGE = "_deploy/hydra-retention-pilot-v1"
PRODUCER_MODEL = "results/peano-hydra/qwen3-1.7b-authority-primitive-retention-pilot-v1/manifest.json"
PRODUCER_APPROVAL_SHA = "556cef2186a2003bf90ea327b927cc6cb3ea6ec0bd57f65e421bb6841e74d233"
PRODUCER_REQUEST_SHA = "67e0be409cf42ac90048029632479328e9b98b19c4f44f637f1fab6b5392f361"
PRODUCER_HEADER_SHA = "224ad02b154eb32a64e07cfd02710f81020cb4b108c83d6514b2dcf918802333"
PRODUCER_REFERENCE = {
    "schema": "peano-hydra-preserved-retention-producer-v1", "source_commit": PRODUCER_COMMIT,
    "source_manifest_sha256": "4f4fcbfcd51ff64b9674dfdde383b37337871d93f52792b3f6f9bedec6862665",
    "inputs_sha256": "3df7953c0d405364aef689b5e67b083f5fc744492159643ca5b09e418a06a388",
    "training_plan_sha256": "da26332740d587bdd946b12999fd37de73817115ed3da8983edf5004bd02abf0",
    "trainer_sha256": "d6529651c031fce3fe535f7b8b9ccbbb3396125083640184f7125065b9e26725",
    "evaluation_source_sha256": "1f42a76f0c1127b7edd2ce171c0e238b5846941a40b1c5cd185f676b9dc5bf92",
}
PRODUCER = {
    "source_commit": PRODUCER_COMMIT, "training_job_id": PRODUCER_JOB,
    "failed_evaluation_job_id": FAILED_EVALUATION_JOB, "model_manifest": MODEL_MANIFEST,
    "approval_sha256": PRODUCER_APPROVAL_SHA, "resource_request_sha256": PRODUCER_REQUEST_SHA,
    "source_header_sha256": PRODUCER_HEADER_SHA,
    "training_ledger_sha256": "3d1b5fa3114c4e7bbe0cbb7f6fee526bd46ecc99bd9a470aefcdd0b95e53ecb6",
    "failed_evaluation_ledger_sha256": "acdde37ddabdca99602b937939ba33848ba2946fa104367595ceb71a086049b3",
    "reserved_gpu_seconds": 10800, "reservations_fully_consumed": True,
    "reservation_reuse_allowed": False, "refunds": False,
}
PRODUCER_FILES = {
    PRODUCER_PACKAGE + "/approval.json": {"bytes": 854, "sha256": PRODUCER_APPROVAL_SHA},
    PRODUCER_PACKAGE + "/resource-request.json": {"bytes": 135557, "sha256": PRODUCER_REQUEST_SHA},
    "logs/hydra-retention-pilot-v1-train.jsonl": {"bytes": 4715, "sha256": PRODUCER["training_ledger_sha256"]},
    "logs/hydra-retention-pilot-v1-evaluate.jsonl": {"bytes": 4821, "sha256": PRODUCER["failed_evaluation_ledger_sha256"]},
    ".peano-source-provenance.tsv": {"bytes": 68, "sha256": "784781d6bf88f52ff66cf4edcc2a61ad31da6a63529a7f77528461d976a503e7"},
    PRODUCER_MODEL: MODEL_MANIFEST,
}
TRAINING_INPUTS_SHA = "e78399c688a1cf255567b15d6e130e478ba10a4c1d79f60775f55d477ef9aa3d"
LOCAL_EXECUTION = Path("/Users/bnaskrecki/codex/peano/_deploy/hydra-retention-evaluation-recovery-execution-20260831")
REMOTE_EXECUTION = Path("/net/scratch/hscra/plgrid/plgnasqret") / REMOTE_PARENT / REMOTE_CHILD
REQUIRED_SOURCES = frozenset(tuple(JOBS.values()) + (
    "training/peano_hydra/retention_evaluation_recovery_launch.py",
    "training/peano_hydra/retention_saved_artifact.py",
    "training/peano_hydra/retention_data.py", "training/peano_hydra/retention_training.py",
    "training/peano_hydra/retention_evaluation.py", "training/peano_hydra/retention_launch.py",
    "training/peano_hydra/helios_runtime.py", "training/peano_hydra/search_launch.py",
    "training/peano_hydra/paired_checkpoint.py", "training/peano_hydra/review_runtime.py",
    "training/peano_hydra/capacity.py", "training/peano_policy/search.py", "training/peano_policy/generate.py",
    "training/peano_policy/objective.py", "training/peano_policy/data.py",
    "training/peano_policy/train.py", "training/peano_policy/training_evidence.py",
    "training/peano_policy/manifest.py", "training/peano_policy/requirements-helios.lock",
    "scripts/hydra_bounded_exec.py", "scripts/authenticate_peano_hydra_retention_saved.py",
    "scripts/run_peano_hydra_retention_evaluation_recovery.sh",
    "scripts/execute_peano_hydra_retention_evaluation_recovery.py",
    "scripts/check_peano_hydra_frontier_runtime.py",
))


def _stage(stage):
    require(type(stage) is str and stage in STAGES, "unknown retention stage")
    return stage


def _descriptor(value):
    require(type(value) is dict and set(value) == {"path", "bytes", "sha256"}, "exact file descriptor required")
    path = safe.relative(value["path"])
    require(type(value["bytes"]) is int and 0 < value["bytes"] <= safe.MAX_JSON
            and type(value["sha256"]) is str and safe.HEX.fullmatch(value["sha256"]), "invalid input descriptor")
    require(path.startswith(PACKAGE + "/") and path not in (REQUEST, APPROVAL), "scientific input outside fixed package")
    return value


def _payload_descriptor(value, payloads, *, expected_path=None):
    _descriptor(value)
    require(expected_path is None or value["path"] == expected_path, "fixed scientific descriptor path changed")
    require(payloads.get(value["path"]) == {key: value[key] for key in ("bytes", "sha256")},
            "scientific descriptor differs from exact payload bytes")
    return decode(read(value["path"]))


def _scientific_input(request):
    """Join exact declarations only; the CLI still performs genuine admission."""
    payloads = request["payloads"]
    stage = _payload_descriptor(request["scientific_inputs"]["evaluate"], payloads,
                                expected_path=PACKAGE + "/evaluate-request.json")
    fields = {"schema", "profile", "run_id", "stage", "inputs", "preflight",
              "evaluation_plan_sha256", "bound_evaluation_plan_sha256", "model_manifest",
              "producer_source_commit", "training_job_id", "failed_evaluation_job_id", "output",
              "training_authorized", "automatic_retry", "resume", "historical_checkpoint_reuse_allowed"}
    require(set(stage) == fields and stage["schema"] == "peano-hydra-retention-evaluation-recovery-stage-request-v1"
            and stage["profile"] == PROFILE and stage["run_id"] == RUN_ID and stage["stage"] == "evaluate"
            and stage["evaluation_plan_sha256"] == EVALUATION_PLAN["sha256"]
            and type(stage["bound_evaluation_plan_sha256"]) is str and safe.HEX.fullmatch(stage["bound_evaluation_plan_sha256"])
            and stage["model_manifest"] == MODEL_MANIFEST and stage["producer_source_commit"] == PRODUCER_COMMIT
            and stage["training_job_id"] == PRODUCER_JOB and stage["failed_evaluation_job_id"] == FAILED_EVALUATION_JOB
            and stage["output"] == EVALUATION_OUTPUT
            and all(stage[key] is False for key in ("training_authorized", "automatic_retry", "resume",
                                                    "historical_checkpoint_reuse_allowed")),
            "evaluation request changed its exact historical model, goal selection or work scope")
    inputs = _payload_descriptor(stage["inputs"], payloads, expected_path=PACKAGE + "/inputs.json")
    preflight = _payload_descriptor(stage["preflight"], payloads)
    require(set(inputs) == {"schema", "profile", "run_id", "candidate_reference", "locations", "evaluation_plan"}
            and inputs["schema"] == "peano-hydra-retention-evaluation-recovery-inputs-v1"
            and inputs["profile"] == PROFILE and inputs["run_id"] == RUN_ID
            and inputs["evaluation_plan"] == EVALUATION_PLAN, "evaluation inputs changed the exact source proposal")
    candidate = inputs["candidate_reference"]
    require(type(candidate) is dict and set(candidate) == {"schema", "manifest_sha256", "training_inputs",
                                                           "producer", "admission_receipt_sha256"}
            and candidate["schema"] == "peano-hydra-preserved-retention-artifact-reference-v1"
            and candidate["manifest_sha256"] == MODEL_MANIFEST["sha256"]
            and candidate["producer"] == PRODUCER_REFERENCE
            and digest(candidate["training_inputs"]) == TRAINING_INPUTS_SHA
            and candidate["admission_receipt_sha256"] == request["historical_admission"]["sha256"],
            "saved candidate changed original training inputs, producer or actual admission receipt")
    locations = inputs["locations"]
    require(type(locations) is dict and set(locations) == {"local", "helios"}, "explicit local/Helios input locations required")
    for location, execution in (("local", LOCAL_EXECUTION), ("helios", REMOTE_EXECUTION)):
        item = locations[location]
        require(type(item) is dict and set(item) == {"manifest_path", "training_inputs", "producer", "admission_receipt_path"}
                and item["admission_receipt_path"] == str(execution / PACKAGE / "admission.json"),
                "historical admission must retain its exact separate raw payload")
    admission = _payload_descriptor(request["historical_admission"], payloads,
                                    expected_path=PACKAGE + "/admission.json")
    require(admission.get("schema") == "peano-hydra-preserved-retention-admission-custody-v1"
            and admission.get("status") == "completed-caller-admission",
            "completed historical admission custody is required; no bare, draft or failed record")
    preflight_fields = {"schema", "profile", "run_id", "inputs_sha256", "candidate_reference", "model_manifest",
                        "evaluation_plan", "bound_evaluation_plan", "model_weights_loaded", "gpu_allocated",
                        "training_authorized", "native_proof_replay_performed"}
    require(set(preflight) == preflight_fields
            and preflight["schema"] == "peano-hydra-retention-evaluation-recovery-input-check-v1"
            and preflight["profile"] == PROFILE and preflight["run_id"] == RUN_ID
            and preflight["inputs_sha256"] == stage["inputs"]["sha256"]
            and preflight["candidate_reference"] == candidate and preflight["model_manifest"] == MODEL_MANIFEST
            and preflight["evaluation_plan"] == EVALUATION_PLAN
            and type(preflight["bound_evaluation_plan"]) is dict
            and preflight["bound_evaluation_plan"].get("plan_sha256") == stage["bound_evaluation_plan_sha256"]
            and all(preflight[key] is False for key in ("model_weights_loaded", "gpu_allocated",
                "training_authorized", "native_proof_replay_performed")),
            "actual CPU input check differs from the exact declared candidate/inputs/bound evaluation")
    # These are byte/identity joins, not execution of an admission helper.
    return stage


def validate_request(request):
    fields = {"schema", "status", "profile", "run_id", "source_commit", "source_files", "payloads",
              "payloads_sha256", "scientific_inputs", "authority_file", "model", "model_manifest",
              "producer", "historical_admission", "evaluation_plan", "reservations",
              "maximum_aggregate_gpu_seconds", "maximum_concurrent_gpus", "automatic_retry", "resume",
              "refunds", "runtime_dependencies", "training_authorized", "evaluation_scope",
              "historical_checkpoint_reuse_allowed"}
    require(type(request) is dict and set(request) == fields and request["schema"] == REQUEST_SCHEMA
            and request["status"] == "ready" and request["profile"] == PROFILE and request["run_id"] == RUN_ID,
            "not the exact fresh evaluation-only resource request")
    require(request["model"] == MODEL and request["model_manifest"] == MODEL_MANIFEST
            and request["producer"] == PRODUCER and request["evaluation_plan"] == EVALUATION_PLAN
            and request["reservations"] == RESERVATIONS
            and request["maximum_aggregate_gpu_seconds"] == 3600 and request["maximum_concurrent_gpus"] == 1
            and request["runtime_dependencies"] == RUNTIME
            and request["evaluation_scope"] == "old-dev32-and-frontier-dev32-at-8-and-16-calls",
            "historical model, spent producer reservation, new resources, runtime or scientific scope changed")
    require(all(request[key] is False for key in ("automatic_retry", "resume", "refunds", "training_authorized",
                                                  "historical_checkpoint_reuse_allowed")),
            "training, retry, resume, refund or historical checkpoint reuse forbidden")
    require(type(request["source_commit"]) is str and safe.COMMIT.fullmatch(request["source_commit"])
            and request["source_commit"] != PRODUCER_COMMIT, "new real frozen evaluation source commit required")
    sources, payloads = request["source_files"], request["payloads"]
    require(type(sources) is dict and REQUIRED_SOURCES <= set(sources) and len(sources) <= 4096,
            "missing or excessive execution source inventory")
    require(type(payloads) is dict and 1 <= len(payloads) <= 4096
            and request["payloads_sha256"] == digest(payloads), "invalid payload inventory")
    total = 0
    for mapping, source in ((sources, True), (payloads, False)):
        for name, file_identity in mapping.items():
            safe.relative(name)
            require(type(file_identity) is dict and set(file_identity) == {"bytes", "sha256"}, "exact raw file identity required")
            require(source or name.startswith(PACKAGE + "/") and name not in (REQUEST, APPROVAL), "payload scope differs")
            require(not source or not name.startswith(PACKAGE + "/"), "generated package cannot be frozen source")
            require(fingerprint(name)[0] == file_identity, "approved file bytes changed: " + name)
            total += file_identity["bytes"]
            require(total <= safe.MAX_TOTAL, "execution and inputs exceed original aggregate byte bound")
    require(safe.inventory(PACKAGE) - {REQUEST, APPROVAL} == set(payloads), "package has missing or undeclared files")
    require(type(request["scientific_inputs"]) is dict and set(request["scientific_inputs"]) == {"evaluate"},
            "only one evaluation scientific input may be reserved")
    for item in (request["authority_file"], request["evaluation_plan"], request["historical_admission"]):
        _descriptor(item)
        require(payloads.get(item["path"]) == {key: item[key] for key in ("bytes", "sha256")},
                "authority, proposal or admission descriptor does not join payload bytes")
    require(request["authority_file"]["sha256"] == STANDING_DIRECTIVE_SHA,
            "standing authority is not the actual retained user directive")
    _scientific_input(request)
    return request


def validate_metadata(expected_approval_sha256):
    require(type(expected_approval_sha256) is str and safe.HEX.fullmatch(expected_approval_sha256)
            and expected_approval_sha256 != PRODUCER_APPROVAL_SHA, "new external raw approval pin required; old approval is spent")
    raw, request_raw = read(APPROVAL), read(REQUEST)
    require(hashlib.sha256(raw).hexdigest() == expected_approval_sha256, "approval bytes differ from external pin")
    approval = decode(raw)
    require(set(approval) == {"schema", "profile", "run_id", "approved", "request_file_sha256",
                              "standing_authority_sha256", "authority_quote", "approval_reference"}
            and approval["schema"] == APPROVAL_SCHEMA and approval["profile"] == PROFILE
            and approval["run_id"] == RUN_ID and approval["approved"] is True
            and approval["standing_authority_sha256"] == STANDING_DIRECTIVE_SHA
            and approval["authority_quote"] == AUTHORITY_QUOTE
            and type(approval["approval_reference"]) is str and 1 <= len(approval["approval_reference"]) <= 2048,
            "resource authority does not match the user's actual standing instruction")
    require(hashlib.sha256(request_raw).hexdigest() == approval["request_file_sha256"], "approval pins another exact request")
    request = validate_request(decode(request_raw))
    require(read(APPROVAL) == raw and read(REQUEST) == request_raw, "request/authority changed during check")
    return approval, request


def identity(approval, request, approval_sha, *, local=False):
    if local:
        require(exists(".git"), "local check needs the real clean frozen checkout")
    sources = {name: item["sha256"] for name, item in request["source_files"].items()}
    synced = safe._execution_commit(request["source_commit"], sources)
    return {"approval_sha256": approval_sha, "resource_request_sha256": approval["request_file_sha256"],
            "producer_sha256": digest(request["producer"]),
            "historical_admission_sha256": request["historical_admission"]["sha256"],
            "source_commit": request["source_commit"], "source_files_sha256": digest(request["source_files"]),
            "payloads_sha256": request["payloads_sha256"], "synced_at": synced,
            "job_script_sha256": {stage: sources[JOBS[stage]] for stage in STAGES}}


def _remote_root():
    scratch = os.environ.get("SCRATCH")
    require(type(scratch) is str and scratch.startswith("/") and ".." not in Path(scratch).parts, "declared SCRATCH required")
    parent = Path(scratch) / REMOTE_PARENT
    require(ROOT == parent / REMOTE_CHILD, "retention pilot must use its own fixed deployment")
    fd = directory(ROOT)
    os.close(fd)
    return parent


def _elapsed(value):
    require(type(value) is str and re.fullmatch(r"(?:[0-9]+-)?[0-9]{2}:[0-9]{2}:[0-9]{2}", value), "unknown scheduler elapsed time")
    day, clock = value.split("-", 1) if "-" in value else ("0", value)
    hour, minute, second = map(int, clock.split(":"))
    require(minute < 60 and second < 60, "invalid scheduler elapsed components")
    return int(day) * 86400 + hour * 3600 + minute * 60 + second


def snapshot(raw, stage, job, *, running=False):
    _stage(stage)
    require(type(raw) is str and 0 < len(raw.encode()) <= 65536 and len(raw.strip().splitlines()) == 1, "one bounded scheduler snapshot required")
    keys = {"JobId", "JobName", "WorkDir", "JobState", "Reason", "Priority", "Dependency", "Requeue",
            "Account", "Partition", "TimeLimit", "NumNodes", "NumCPUs", "ReqTRES", "RunTime"}
    fields = {}
    for match in re.finditer(r"(?:^|\s)([A-Za-z][A-Za-z0-9]*)=(\S*)", raw):
        key, value = match.groups()
        if key in keys:
            require(key not in fields, "duplicate guarded scheduler field")
            fields[key] = value
    require(set(fields) == keys and fields["JobId"] == job and fields["JobName"] == JOB_NAMES[stage]
            and fields["WorkDir"] == str(ROOT) and fields["Dependency"] in ("(null)", "(null)(unfulfilled)")
            and fields["Requeue"] == "0" and fields["Account"] == ACCOUNT and fields["Partition"] == PARTITION
            and fields["TimeLimit"] == WALL[stage] and fields["NumNodes"] in ("1", "1-1") and fields["NumCPUs"] == "8",
            "scheduler changed exact stage identity/resources/restart policy")
    if running:
        require(fields["JobState"] == "RUNNING", "job is not actually running")
    else:
        require(fields["JobState"] == "PENDING" and fields["Reason"] == "JobHeldUser" and fields["Priority"] == "0"
                and _elapsed(fields["RunTime"]) == 0, "job is not held before any compute")
    tres = {}
    for item in fields["ReqTRES"].split(","):
        key, sep, value = item.partition("=")
        require(sep and key and value and key not in tres, "ambiguous requested resources")
        tres[key] = value
    require(tres.get("cpu") == "8" and tres.get("node") == "1" and tres.get("gres/gpu") == "1"
            and tres.get("mem") in ("64G", "65536M", "67108864K")
            and all(v == "1" for k, v in tres.items() if k.startswith("gres/gpu:")), "one GH200/64 GiB required")
    elapsed = _elapsed(fields["RunTime"])
    require(elapsed < RESERVATIONS[stage]["seconds"], "allocation already exhausted")
    return {"raw": raw, "raw_sha256": hashlib.sha256(raw.encode()).hexdigest(), "fields": fields,
            "allocation_elapsed_seconds": elapsed}


def _header(stage, bound):
    return {"kind": "header", "schema": LEDGER_SCHEMA, "profile": PROFILE, "run_id": RUN_ID,
            "stage": stage, "identity": bound, "reservation": RESERVATIONS[stage],
            "maximum_aggregate_gpu_seconds": 3600, "maximum_concurrent_gpus": 1,
            "automatic_retry": False, "resume": False, "refunds": False}


def load_ledger(stage, bound):
    _stage(stage)
    state = {"events": [], "raw": b"", "job_id": None, "phase": "empty", "created_at": None,
             "gpu_seconds": 0, "model_manifest": None}
    if not exists(LEDGERS[stage]):
        return state
    raw = read(LEDGERS[stage], safe.MAX_LEDGER)
    lines = raw.splitlines(keepends=True)
    kinds = ("header", "reserve", "accepted", "held-validated", "release-authorized", "released")
    require(raw.endswith(b"\n") and 1 <= len(lines) <= len(kinds), "stage ledger is truncated or extended")
    previous = "0" * 64
    for index, line in enumerate(lines):
        event = decode(line)
        require(set(event) == {"index", "previous_sha256", "payload", "sha256"}
                and type(event["index"]) is int and event["index"] == index and event["previous_sha256"] == previous
                and event["sha256"] == digest({k: event[k] for k in ("index", "previous_sha256", "payload")})
                and canonical(event) + b"\n" == line, "stage ledger canonical chain changed")
        value = event["payload"]
        require(type(value) is dict and value.get("kind") == kinds[index], "stage ledger event order changed")
        if index == 0:
            require(value == _header(stage, bound), "ledger belongs to another source/approval/stage")
        elif index == 1:
            require(set(value) == {"kind", "reservation", "created_at", "model_manifest"} and value["reservation"] == RESERVATIONS[stage]
                    and type(value["created_at"]) is str and re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z", value["created_at"]),
                    "stage reservation changed")
            model_pin = value["model_manifest"]
            require(model_pin == MODEL_MANIFEST, "new evaluation must pin the exact completed original model")
            state["gpu_seconds"], state["created_at"] = RESERVATIONS[stage]["seconds"], value["created_at"]
            state["model_manifest"] = model_pin
        elif index == 2:
            require(set(value) == {"kind", "job_id"} and type(value["job_id"]) is str and safe.JOB_ID.fullmatch(value["job_id"]), "accepted job changed")
            require(value["job_id"] not in (PRODUCER_JOB, FAILED_EVALUATION_JOB),
                    "original spent jobs cannot be adopted into the new ledger")
            state["job_id"] = value["job_id"]
        elif index == 3:
            require(set(value) == {"kind", "snapshot"} and value["snapshot"] == snapshot(value["snapshot"]["raw"], stage, state["job_id"]), "held barrier changed")
        else:
            require(value == {"kind": kinds[index], "job_id": state["job_id"]}, "release identity changed")
        state["events"].append(event)
        previous, state["phase"] = event["sha256"], kinds[index]
    state["raw"] = raw
    return state


def _record(stage, state, payload, bound):
    event = {"index": len(state["events"]), "previous_sha256": state["events"][-1]["sha256"] if state["events"] else "0" * 64,
             "payload": payload}
    event["sha256"] = digest(event)
    safe._append(LEDGERS[stage], state["raw"], canonical(event) + b"\n", safe.MAX_LEDGER)
    return load_ledger(stage, bound)


def _history(states, bound):
    rows, _ = safe._submissions()
    own = [row for row in rows if row[2] in JOBS.values() or row[1] in {state["job_id"] for state in states.values()}]
    expected = []
    for stage in STAGES:
        state = states[stage]
        if state["job_id"] is not None:
            expected.append([state["created_at"], state["job_id"], JOBS[stage], "", str(ROOT),
                             bound["source_commit"], "false", bound["synced_at"], bound["job_script_sha256"][stage]])
    require(own == expected, "submission history differs; no adoption or reset")


def _queue_history(states):
    parent = _remote_root()
    user = os.environ.get("USER", "")
    require(re.fullmatch(r"[A-Za-z0-9._-]{1,64}", user), "scheduler user missing")
    accepted = {state["job_id"]: stage for stage, state in states.items() if state["job_id"]}
    active = set()
    for line in safe.run(["squeue", "-h", "-u", user, "-o", "%i|%Z|%j|%T"]).splitlines():
        fields = line.split("|")
        require(len(fields) == 4 and safe.JOB_ID.fullmatch(fields[0]), "ambiguous scheduler queue record")
        job, workdir, name, _ = fields
        if workdir == str(parent) or workdir.startswith(str(parent) + "/") or name in JOB_NAMES.values():
            require(job in accepted and workdir == str(ROOT) and name == JOB_NAMES[accepted[job]] and job not in active,
                    "another project allocation is active")
            active.add(job)
    seen = set()
    for line in safe.run(["sacct", "-n", "-P", "-X", "-u", user, "--starttime=2026-08-31",
                          "--name=" + ",".join(JOB_NAMES.values()), "--format=JobIDRaw,JobName%80,WorkDir%4096"]).splitlines():
        if not line.strip():
            continue
        fields = line.split("|")
        require(len(fields) in (3, 4) and (len(fields) == 3 or fields[3] == ""), "ambiguous accounting history")
        job, name, workdir = fields[:3]
        require(job in accepted and job not in seen and name == JOB_NAMES[accepted[job]] and workdir == str(ROOT),
                "unrecorded retention allocation; deletion does not refund")
        seen.add(job)
    require(seen | active == set(accepted), "accepted stage missing from scheduler history")
    require(len(active) <= 1, "pilot stages must never allocate concurrently")
    return active


def _producer_read(root, name, expected):
    """Read only the fixed historical root; never reuse or rewrite its ledger."""
    path = root / safe.relative(name)
    parent, fd = directory(path.parent), -1
    try:
        fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        before = os.fstat(fd)
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1
                and 0 < before.st_size == expected["bytes"] <= safe.MAX_JSON, "historical file size/type changed")
        raw = bytearray()
        while True:
            block = os.read(fd, min(65536, expected["bytes"] + 1 - len(raw)))
            if not block: break
            raw.extend(block)
            require(len(raw) <= expected["bytes"], "historical file grew beyond its exact pin")
        after, named = os.fstat(fd), os.stat(path.name, dir_fd=parent, follow_symlinks=False)
        fields = ("st_dev", "st_ino", "st_mode", "st_size", "st_nlink", "st_mtime_ns", "st_ctime_ns")
        require(len(raw) == expected["bytes"] and hashlib.sha256(raw).hexdigest() == expected["sha256"]
                and all(getattr(before, key) == getattr(after, key) == getattr(named, key) for key in fields),
                "actual historical producer bytes changed")
        return bytes(raw)
    finally:
        if fd >= 0: os.close(fd)
        os.close(parent)


def _producer_completed():
    """Actual old success and old failure stay terminal and fully charged."""
    root = _remote_root() / PRODUCER_CHILD
    saved = {name: _producer_read(root, name, expected) for name, expected in PRODUCER_FILES.items()}
    producer_request = decode(saved[PRODUCER_PACKAGE + "/resource-request.json"])
    producer_approval = decode(saved[PRODUCER_PACKAGE + "/approval.json"])
    require(producer_request["source_commit"] == PRODUCER_COMMIT
            and producer_request["maximum_aggregate_gpu_seconds"] == 10800
            and producer_approval["request_file_sha256"] == PRODUCER_REQUEST_SHA,
            "original producer authority or total charged reservation changed")
    for stage, job in (("train", PRODUCER_JOB), ("evaluate", FAILED_EVALUATION_JOB)):
        raw = saved["logs/hydra-retention-pilot-v1-" + stage + ".jsonl"]
        events = [decode(line) for line in raw.splitlines(keepends=True)]
        require(len(events) == 6 and events[0]["payload"]["stage"] == stage
                and digest(events[0]["payload"]["identity"]) == PRODUCER_HEADER_SHA
                and events[2]["payload"] == {"kind": "accepted", "job_id": job}
                and events[-1]["payload"] == {"kind": "released", "job_id": job}
                and events[1]["payload"]["reservation"]["seconds"] == (7200 if stage == "train" else 3600)
                and events[1]["payload"]["model_manifest"] == (None if stage == "train" else MODEL_MANIFEST),
                "original fully charged source/job/ledger binding changed")
    manifest = decode(saved[PRODUCER_MODEL])
    require(manifest["reservation"]["source_commit"] == PRODUCER_COMMIT
            and manifest["reservation"]["job_id"] == manifest["final_reservation"]["job_id"] == PRODUCER_JOB
            and manifest["training_plan_sha256"] == PRODUCER_REFERENCE["training_plan_sha256"],
            "completed model no longer identifies its original producer")
    command = ["sacct", "-n", "-P", "-X", "-j", PRODUCER_JOB + "," + FAILED_EVALUATION_JOB,
        "--format=JobIDRaw,State,ExitCode,JobName%80,WorkDir%4096,TimelimitRaw,AllocCPUS,ReqMem,Account,Partition,User"]
    rows = [line.split("|") for line in safe.run(command).splitlines() if line.strip()]
    require(len(rows) == 2 and all(len(row) in (11, 12) and (len(row) == 11 or row[11] == "") for row in rows),
            "unique actual original terminal accounting required")
    found = {row[0]: row[:11] for row in rows}
    require(len(found) == 2 and found == {
        PRODUCER_JOB: [PRODUCER_JOB, "COMPLETED", "0:0", "peano-hydra-retention-pilot-v1-train", str(root),
                      "120", "8", "64G", ACCOUNT, PARTITION, "plgnasqret"],
        FAILED_EVALUATION_JOB: [FAILED_EVALUATION_JOB, "FAILED", "2:0", "peano-hydra-retention-pilot-v1-evaluate", str(root),
                      "60", "8", "64G", ACCOUNT, PARTITION, "plgnasqret"]},
            "original training must have completed and failed evaluation must remain its actual separate failure")
    for name, expected in PRODUCER_FILES.items():
        require(_producer_read(root, name, expected) == saved[name], "historical producer changed during accounting")
    return dict(MODEL_MANIFEST)


def _lock(create):
    if create:
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
        fd = os.open(Path(LOCK).name, (os.O_RDWR | os.O_CREAT if create else os.O_RDONLY)
                     | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600, dir_fd=parent)
    finally:
        os.close(parent)
    info = os.fstat(fd)
    require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_size == 0, "unsafe stage reservation lock")
    return fd


def launch(stage, approval_sha, expected_commit, *, submit=False):
    _stage(stage)
    require(type(submit) is bool and "SLURM_JOB_ID" not in os.environ
            and not any(key.startswith("SBATCH_") for key in os.environ), "nested submission or scheduler override forbidden")
    _remote_root()
    approval, request = validate_metadata(approval_sha)
    bound = identity(approval, request, approval_sha)
    require(bound["source_commit"] == expected_commit and bound["synced_at"] is not None, "exact staged source provenance required")
    fd = -1
    try:
        if submit:
            fd = _lock(True)
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        states = {name: load_ledger(name, bound) for name in STAGES}
        require(not states[stage]["events"], "stage reservation already opened; no retry/resume/reset/refund")
        require(not exists(OUTPUTS[stage]), "stage output already exists; no adoption or resume")
        _history(states, bound)
        require(not _queue_history(states), "another pilot stage is still active")
        model_pin = _producer_completed()
        if not submit:
            return {"status": "test-only", "stage": stage, "reservation": RESERVATIONS[stage],
                    "allocation_performed": False, "model_manifest": model_pin, "automatic_retry": False}
        require(identity(*validate_metadata(approval_sha), approval_sha) == bound, "approved source/inputs changed before reservation")
        state = _record(stage, states[stage], _header(stage, bound), bound)
        state = _record(stage, state, {"kind": "reserve", "reservation": RESERVATIONS[stage], "model_manifest": model_pin,
            "created_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}, bound)
        # Full stage budget is charged durably BEFORE any uncertain sbatch call.
        options = ["sbatch", "--parsable", "--hold", "--no-requeue", "--kill-on-invalid-dep=yes",
                   "--account=" + ACCOUNT, "--partition=" + PARTITION, "--nodes=1", "--ntasks=1",
                   "--cpus-per-task=8", "--mem=64G", "--gres=gpu:1", "--time=" + WALL[stage],
                   "--chdir=" + str(ROOT), "--export=ALL", "--job-name=" + JOB_NAMES[stage],
                   "--output=logs/" + JOB_NAMES[stage] + "-%j.out", "--error=logs/" + JOB_NAMES[stage] + "-%j.err",
                   JOBS[stage], approval_sha]
        raw = safe.run(options).strip()
        require(re.fullmatch(r"[1-9][0-9]{0,19}(?:;[A-Za-z0-9_-]{1,64})?", raw), "uncertain submission; budget remains spent, never retry")
        job = raw.split(";", 1)[0]
        require(job not in (PRODUCER_JOB, FAILED_EVALUATION_JOB), "scheduler returned an already consumed original job")
        state = _record(stage, state, {"kind": "accepted", "job_id": job}, bound)
        states[stage] = state
        rows, before = safe._submissions()
        require(job not in {row[1] for row in rows}, "accepted job already appears in history")
        row = [state["created_at"], job, JOBS[stage], "", str(ROOT), bound["source_commit"], "false",
               bound["synced_at"], bound["job_script_sha256"][stage]]
        safe._append(safe.SUBMISSIONS, before,
                     ((safe.SUBMISSION_HEADER if not before else "") + "\t".join(row) + "\n").encode(), safe.MAX_JSON)
        _history(states, bound)
        _queue_history(states)
        state = _record(stage, state, {"kind": "held-validated", "snapshot": snapshot(safe.run(["scontrol", "-o", "show", "job", job]), stage, job)}, bound)
        require(identity(*validate_metadata(approval_sha), approval_sha) == bound and not exists(OUTPUTS[stage]),
                "source/input/output changed before release; job stays held and charged")
        require(_producer_completed() == model_pin, "original producer or failed reservation changed before new release")
        state = _record(stage, state, {"kind": "release-authorized", "job_id": job}, bound)
        fcntl.flock(fd, fcntl.LOCK_UN)
        safe.run(["scontrol", "release", job])
        safe._await_lock(fd, fcntl.LOCK_EX)
        state = _record(stage, state, {"kind": "released", "job_id": job}, bound)
        return {"status": "submitted", "profile": PROFILE, "run_id": RUN_ID, "stage": stage, "job_id": job,
                "reserved_gpu_seconds": state["gpu_seconds"], "maximum_aggregate_gpu_seconds": 3600,
                "maximum_concurrent_gpus": 1, "ledger": LEDGERS[stage], "output": OUTPUTS[stage],
                "automatic_retry": False, "resume": False, "refunds": False}
    finally:
        if fd >= 0:
            os.close(fd)


def check_job_reservation(approval_sha, stage):
    _stage(stage)
    _remote_root()
    job = os.environ.get("SLURM_JOB_ID", "")
    require(safe.JOB_ID.fullmatch(job) and os.environ.get("SLURM_RESTART_COUNT", "0") == "0"
            and os.environ.get("SLURM_SUBMIT_DIR") == str(ROOT)
            and os.environ.get("PEANO_HYDRA_PROFILE") == PROFILE and os.environ.get("PEANO_JOB_SCRIPT") == JOBS[stage]
            and not any(key.startswith("SBATCH_") for key in os.environ), "actual scheduled stage identity/restart differs")
    approval, request = validate_metadata(approval_sha)
    bound = identity(approval, request, approval_sha)
    fd = _lock(False)
    try:
        safe._await_lock(fd, fcntl.LOCK_SH)
        states = {name: load_ledger(name, bound) for name in STAGES}
        state = states[stage]
        require(state["phase"] in ("release-authorized", "released") and state["job_id"] == job
                and state["gpu_seconds"] == RESERVATIONS[stage]["seconds"], "actual job lacks its exact durable reservation")
        _history(states, bound)
        current = snapshot(safe.run(["scontrol", "-o", "show", "job", job]), stage, job, running=True)
        require(_producer_completed() == state["model_manifest"], "original model/history differs from the new reserved raw manifest")
        elapsed = current["allocation_elapsed_seconds"]
        return {"status": "job-verified", "profile": PROFILE, "run_id": RUN_ID, "stage": stage, "job_id": job,
                **{key: bound[key] for key in ("approval_sha256", "resource_request_sha256", "source_commit",
                                               "source_files_sha256", "payloads_sha256")},
                "reservation": dict(RESERVATIONS[stage]), "scientific_input": request["scientific_inputs"][stage],
                "model_manifest": state["model_manifest"], "producer_source_commit": PRODUCER_COMMIT,
                "training_job_id": PRODUCER_JOB, "failed_evaluation_job_id": FAILED_EVALUATION_JOB,
                "allocation_elapsed_seconds": elapsed, "allocation_remaining_seconds": RESERVATIONS[stage]["seconds"] - elapsed,
                "automatic_retry": False, "resume": False}
    finally:
        os.close(fd)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--approval-sha256", required=True)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--check", action="store_true")
    modes.add_argument("--test-only", choices=STAGES)
    modes.add_argument("--submit", choices=STAGES)
    modes.add_argument("--check-job", choices=STAGES)
    parser.add_argument("--local", action="store_true")
    parser.add_argument("--source-commit")
    args = parser.parse_args(argv)
    if args.check:
        require(args.source_commit is None, "metadata check does not override source")
        approval, request = validate_metadata(args.approval_sha256)
        result = {"status": "metadata-verified", **identity(approval, request, args.approval_sha256, local=args.local),
                  "scientific_inputs": request["scientific_inputs"], "reservations": RESERVATIONS}
    elif args.check_job:
        require(not args.local and args.source_commit is None, "job check cannot override location/source")
        result = check_job_reservation(args.approval_sha256, args.check_job)
    else:
        require(not args.local and args.source_commit is not None, "launch needs exact remote source commit")
        result = launch(args.submit or args.test_only, args.approval_sha256, args.source_commit, submit=args.submit is not None)
    print(canonical(result).decode(), flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError, TypeError) as error:
        print("retention-evaluation-recovery-launch: " + " ".join(str(error).split())[:2048], file=sys.stderr)
        raise SystemExit(2)
