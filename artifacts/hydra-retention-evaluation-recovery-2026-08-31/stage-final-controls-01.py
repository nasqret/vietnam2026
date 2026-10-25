"""Stage exact evaluation-only metadata after the two real CPU gates passed."""
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path("/Users/bnaskrecki/codex/peano")
B = ROOT / "artifacts/hydra-retention-evaluation-recovery-2026-08-31"
SOURCE = ROOT / "_deploy/hydra-retention-evaluation-recovery-execution-20260831"
PACKAGE = SOURCE / "_deploy/hydra-retention-evaluation-recovery-v1"
COMMIT = "dca88930b59e3147a95d0234d804076ccf757a74"
assert sys.flags.isolated and sys.dont_write_bytecode
sys.path.insert(0, str(SOURCE))
from training.peano_hydra import retention_evaluation_recovery_launch as gate

def pin(path):
    assert path.is_file() and not path.is_symlink(), str(path)
    raw = path.read_bytes()
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}

def checked(path, expected_sha):
    assert pin(path)["sha256"] == expected_sha, str(path)
    return json.loads(path.read_bytes())

def descriptor(path):
    return {"path": path.relative_to(SOURCE).as_posix(), **pin(path)}

def write_new(path, value=None, raw=None):
    assert (value is None) != (raw is None)
    if value is not None:
        raw = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()
    with path.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    return pin(path)

os.umask(0o077)
catalog = checked(SOURCE / "_deploy/hydra-retention-evaluation-recovery-source.json",
    "f866666c81c94a6c0c2db685c27f5dfa5c68d84508c5652d848e820caf9b741c")
checked(SOURCE / "_deploy/hydra-retention-evaluation-recovery-execution-freeze.json",
    "646beb5b9ee4c8982e7b203dbe95cb832d3c3263836548e8b0bbe87ed95ef2fb")
assert catalog["git_commit"] == COMMIT
sources = {name: {key: identity[key] for key in ("bytes", "sha256")}
           for name, identity in catalog["files"].items()}
assert len(sources) == 896 and sum(x["bytes"] for x in sources.values()) == 91225189
owner = checked(B / "input-check-01/owner.json",
    "ebd7667707bcce6a5e7efc5ec6650d6ab0330574ce0dc7644e8c1465d5374df8")
preflight_path = B / "input-check-01/preflight.json"
preflight = checked(preflight_path,
    "ebc32fae93365d5a1741b8859b5b9c060bb0b450840c07450758f248d88ce983")
external_exit = json.loads((B / "input-check-01/invocation-exit.json").read_bytes())
assert external_exit["exit_code"] == 0 and external_exit["observed_from"] == "actual-tool-process-completion"
assert external_exit["owner_result"] == {"path": str(B / "input-check-01/owner.json"), **pin(B / "input-check-01/owner.json")}
assert external_exit["output"] == {"path": str(preflight_path), **pin(preflight_path)}
assert owner["status"] == "passed" and owner["error"] is None
assert owner["inputs_unchanged"] and owner["source_unchanged"]
assert owner["accounting"]["whole_process_tree_quiescent"]
assert owner["source_commit"] == COMMIT
assert owner["output"] == external_exit["output"]
inputs = checked(PACKAGE / "inputs.json",
    "e8dae306086368b059f2085441ae3e6ffbf46c7394c84275db7e21af61340a70")
assert preflight["inputs_sha256"] == pin(PACKAGE / "inputs.json")["sha256"]
assert preflight["candidate_reference"] == inputs["candidate_reference"]
custody = checked(PACKAGE / "admission.json",
    "b0f1836c27c044f1c8746ab3efeec491d815bafb861f62939153f5baabe32bb6")
assert custody["status"] == "completed-caller-admission"
assert pin(PACKAGE / "admission.json") == pin(B / "admission-03/admission-custody.json")
assert inputs["candidate_reference"]["admission_receipt_sha256"] == pin(PACKAGE / "admission.json")["sha256"]
assert preflight["bound_evaluation_plan"]["plan_sha256"] == "a1a4410428653082d8c4f0f183dcbf9701d0ae41e5c10523d2a28c31bb1b9867"
assert pin(PACKAGE / "evaluation-plan.json") == {k:gate.EVALUATION_PLAN[k] for k in ("bytes","sha256")}
assert pin(PACKAGE / "authority.json")["sha256"] == gate.STANDING_DIRECTIVE_SHA

write_new(PACKAGE / "preflight.json", raw=preflight_path.read_bytes())
stage = {
    "schema": "peano-hydra-retention-evaluation-recovery-stage-request-v1",
    "profile": gate.PROFILE, "run_id": gate.RUN_ID, "stage": "evaluate",
    "inputs": descriptor(PACKAGE / "inputs.json"),
    "preflight": descriptor(PACKAGE / "preflight.json"),
    "evaluation_plan_sha256": gate.EVALUATION_PLAN["sha256"],
    "bound_evaluation_plan_sha256": preflight["bound_evaluation_plan"]["plan_sha256"],
    "model_manifest": gate.MODEL_MANIFEST,
    "producer_source_commit": gate.PRODUCER_COMMIT,
    "training_job_id": gate.PRODUCER_JOB,
    "failed_evaluation_job_id": gate.FAILED_EVALUATION_JOB,
    "output": gate.EVALUATION_OUTPUT,
    "training_authorized": False, "automatic_retry": False, "resume": False,
    "historical_checkpoint_reuse_allowed": False,
}
write_new(PACKAGE / "evaluate-request.json", value=stage)
payloads = {path.relative_to(SOURCE).as_posix(): pin(path) for path in sorted(PACKAGE.iterdir())}
assert len(payloads) == 7
request = {
    "schema": gate.REQUEST_SCHEMA, "status": "ready",
    "profile": gate.PROFILE, "run_id": gate.RUN_ID, "source_commit": COMMIT,
    "source_files": sources, "payloads": payloads, "payloads_sha256": gate.digest(payloads),
    "scientific_inputs": {"evaluate": descriptor(PACKAGE / "evaluate-request.json")},
    "authority_file": descriptor(PACKAGE / "authority.json"),
    "model": gate.MODEL, "model_manifest": gate.MODEL_MANIFEST, "producer": gate.PRODUCER,
    "historical_admission": descriptor(PACKAGE / "admission.json"),
    "evaluation_plan": gate.EVALUATION_PLAN, "reservations": gate.RESERVATIONS,
    "maximum_aggregate_gpu_seconds": 3600, "maximum_concurrent_gpus": 1,
    "automatic_retry": False, "resume": False, "refunds": False,
    "runtime_dependencies": gate.RUNTIME, "training_authorized": False,
    "evaluation_scope": "old-dev32-and-frontier-dev32-at-8-and-16-calls",
    "historical_checkpoint_reuse_allowed": False,
}
write_new(PACKAGE / "resource-request.json", value=request)
approval = {
    "schema": gate.APPROVAL_SCHEMA, "profile": gate.PROFILE, "run_id": gate.RUN_ID,
    "approved": True, "request_file_sha256": pin(PACKAGE / "resource-request.json")["sha256"],
    "standing_authority_sha256": gate.STANDING_DIRECTIVE_SHA,
    "authority_quote": gate.AUTHORITY_QUOTE,
    "approval_reference": (
        "This exact bounded evaluation-only request is authorized under the user's retained "
        "standing instruction: You don't have to ask my permission to run new experiments. "
        "The user also directed: Yes, proceed. This record applies that existing authority; "
        "it does not claim a new per-run chat approval. One fresh GH200 for at most 3600 seconds, "
        "8 CPUs and 64 GiB; no training, automatic retry, resume, refund or second GPU."
    ),
}
write_new(PACKAGE / "approval.json", value=approval)
receipt = {
    "schema": "peano-hydra-retention-evaluation-recovery-control-staging-v1",
    "status": "staged-for-gate-check", "source_commit": COMMIT,
    "source_file_count": len(sources), "payload_count": len(payloads),
    "files": {path.relative_to(SOURCE).as_posix(): pin(path) for path in sorted(PACKAGE.iterdir())},
    "actual_cpu_input_check_exit": {"path": str(B / "input-check-01/invocation-exit.json"),
                                   **pin(B / "input-check-01/invocation-exit.json")},
    "standing_authority_applied": True, "fresh_chat_approval_claimed": False,
    "upload_performed": False, "gpu_allocated": False, "training_authorized": False,
}
receipt_pin = write_new(B / "final-control-staging-01.json", value=receipt)
print(json.dumps({
    "status": receipt["status"], "receipt": receipt_pin,
    "approval": pin(PACKAGE / "approval.json"),
    "request": pin(PACKAGE / "resource-request.json"),
    "stage_request": pin(PACKAGE / "evaluate-request.json"),
    "bound_evaluation_plan_sha256": stage["bound_evaluation_plan_sha256"],
    "source_files": len(sources), "payloads": len(payloads),
}, sort_keys=True))
