"""Source-only parent orchestration for bounded paired-search CPU checks.

Native imports and metadata validation belong to one guarded child. Each
authenticated positive then gets its own bounded replay child. No nested
workers, model imports, retries, output overwrites or hidden checkpoint resume.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import resource
import sys

from hydra_training_v5.peano_hydra import origin_bridge as bridge
from hydra_training_v5.peano_hydra import corrective_workflow as fileio
from hydra_training_v5.peano_hydra.review_runtime import ProcessLimits, run_bounded, validate_process_record
from hydra_training_v5.peano_hydra.search_origin import load_reference


ROOT = Path(__file__).absolute().parents[2]
SCRIPT = ROOT / "scripts/eval_peano_hydra_search.py"
REQUEST_SCHEMA = "peano-hydra-paired-search-metadata-request-v1"
WORKER_SCHEMA = "peano-hydra-paired-search-metadata-worker-v1"
AUDIT_SCHEMA = "peano-hydra-paired-search-cpu-check-v1"
METADATA_LIMITS = ProcessLimits(cpu_seconds=30, wall_seconds=45, rss_bytes=1024**3, output_bytes=4 * 1024**2)
REPLAY_LIMITS = ProcessLimits(cpu_seconds=30, wall_seconds=45, rss_bytes=1024**3, output_bytes=1024**2)
MAX_REPORT_BYTES = 24 * 1024**2
MAX_REQUEST_BYTES = 1024**2
MAX_REPLAY_REQUEST_BYTES = 96 * 1024
MODES = ("plan", "report", "checkpoint")
canonical, digest = bridge._canonical, bridge._digest
require = bridge._require


class SearchWorkflowError(ValueError):
    def __init__(self, message, *, observation=None):
        super().__init__(message)
        self.observation = observation


def _no_models():
    require(not {"torch", "transformers", "peft", "tokenizers"} & set(sys.modules),
            "paired CPU verification cannot load model frameworks")


def _summary(process):
    return {key: value for key, value in process.items() if key not in {"stdout", "stderr", "raw_output_base64"}}


def _recheck_source(plan):
    files = plan.get("source_files")
    require(type(files) is dict and 1 <= len(files) <= 128, "paired source inventory exceeds its bound")
    with bridge._Tree(ROOT) as tree:
        for name, expected in files.items():
            bridge._relative(name)
            bridge._hash(expected, "paired execution source SHA")
            actual, _ = tree.fingerprint(name, maximum=2 * 1024**2)
            require(actual["sha256"] == expected, "paired execution source changed during CPU verification")
        tree.assert_unchanged()


def load_input(reference_path, reference_sha256, *, source_root=None, adapter_manifest=None):
    return load_reference(Path(reference_path), reference_sha256,
                          source_root=None if source_root is None else Path(source_root),
                          adapter_manifest=None if adapter_manifest is None else Path(adapter_manifest))


def protected_roots(reference):
    return (reference.request.source_root, reference.request.adapter_manifest.parent,
            reference.receipt_path.parent, *(ROOT / part for part in (
                "training", "scripts", "slurm", "peano-lab", "book", "docs", "artifacts/peano-library")))


def guard_output(path, reference, *, other_paths=()):
    path = bridge._absolute(Path(path))
    for other in other_paths:
        other = bridge._absolute(Path(other))
        require(path != other and path not in other.parents and other not in path.parents,
                "paired output and input/checkpoint paths must be separate")
    return fileio.guard_output(path, protected=protected_roots(reference))


def publish_metadata(path, value, reference):
    # Only the reviewed no-replace I/O helpers are reused, never an old
    # corrective approval, model validator or experiment schema.
    fileio.publish_metadata(path, value, protected=protected_roots(reference))


def _positive_material(lane, goal, row, plan):
    saved = row["evidence"]["replay"]
    return {
        "lane": lane, "goal": row["goal"], "commands_sha256": row["commands_sha256"],
        "proof_nodes": row["proof_nodes"], "saved_replay": saved,
        "request": {"source": goal["source"], "statement": goal["statement"],
                    "commands": row["evidence"]["search"]["commands"], "id": saved["id"],
                    "session": saved["session"],
                    "capabilities": plan["execution_contract"]["environment"]["capabilities"]},
    }


def _positive(lane, goal, row, plan, ordinal):
    """Small authenticated descriptor, not a duplicate of every saved trace."""
    material = _positive_material(lane, goal, row, plan)
    return {"ordinal": ordinal, "lane": lane, "goal": row["goal"],
            "commands_sha256": row["commands_sha256"], "proof_nodes": row["proof_nodes"],
            "row_sha256": digest(row), "request_sha256": digest(material["request"]),
            "saved_replay_sha256": digest(material["saved_replay"])}


def _hydrate_positive(descriptor, checked, mode, input_path, report_view):
    """Read only bytes already authenticated by the bounded metadata child."""
    bridge._keys(descriptor, {"ordinal", "lane", "goal", "commands_sha256", "proof_nodes",
                             "row_sha256", "request_sha256", "saved_replay_sha256"}, "paired positive descriptor")
    ordinal = bridge._integer(descriptor["ordinal"], 64, "positive ordinal", minimum=1)
    lane, index = ("legacy", "context-alpha")[(ordinal - 1) // 32], (ordinal - 1) % 32
    require(descriptor["lane"] == lane, "positive descriptor changed its lane order")
    goal = checked["plan"]["goals"][index]
    if mode == "report":
        row = report_view["lanes"][lane]["goals"][index]
    else:
        raw = bridge._read(Path(input_path).absolute() / f"{ordinal:06d}.goal.json", 1024**2 + 128 * 1024)
        require(hashlib.sha256(raw).hexdigest() == checked["input_identity"]["rows"][ordinal - 1],
                "checkpoint positive bytes changed after metadata authentication")
        record = bridge._decode(raw, 1024**2 + 128 * 1024, "authenticated paired row")
        row = record["row"]
    require(row["kernel_checked"] is True and row["goal"] == goal["name"]
            and canonical(descriptor) == canonical(_positive(lane, goal, row, checked["plan"], ordinal)),
            "positive trace/commands differ from the authenticated descriptor")
    return _positive_material(lane, goal, row, checked["plan"])


def metadata_worker(request):
    """Internal exact-resource child: metadata checks, never model inference."""
    _no_models()
    require(sys.flags.isolated and sys.dont_write_bytecode and sys.pycache_prefix == "/dev/null",
            "metadata worker needs isolated uncached Python")
    require(resource.getrlimit(resource.RLIMIT_CPU) == (METADATA_LIMITS.cpu_seconds, METADATA_LIMITS.cpu_seconds + 1),
            "metadata worker lacks its exact CPU guard")
    bridge._keys(request, {"schema", "mode", "reference_path", "reference_sha256", "source_root", "adapter_manifest", "input_path"},
                 "paired metadata request")
    require(request["schema"] == REQUEST_SCHEMA and request["mode"] in MODES, "unknown paired metadata request")
    require(request["mode"] == "plan" and request["input_path"] is None
            or request["mode"] != "plan" and type(request["input_path"]) is str, "paired metadata mode/input differ")
    reference = load_input(request["reference_path"], request["reference_sha256"],
                           source_root=request["source_root"], adapter_manifest=request["adapter_manifest"])
    from hydra_training_v5.peano_hydra import search_comparison as comparison

    plan = comparison.build_paired_plan(reference)
    record, positives, identity, verification = plan.to_dict(), [], None, None
    if request["mode"] == "report":
        path = bridge._absolute(Path(request["input_path"]))
        raw = bridge._read(path, MAX_REPORT_BYTES)
        report = bridge._decode(raw, MAX_REPORT_BYTES, "paired result")
        verification = comparison.validate_result(plan, report, replay=False)
        identity = {"kind": "report-file", "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
        for lane in comparison.LANES:
            for index, (goal, row) in enumerate(zip(plan.execution.goals, report["lanes"][lane]["goals"], strict=True)):
                if row["kernel_checked"]:
                    positives.append(_positive(lane, goal, row, record, comparison.LANES.index(lane) * 32 + index + 1))
        comparison._refresh(plan)
        require(bridge._read(path, MAX_REPORT_BYTES) == raw, "paired report changed during metadata validation")
    elif request["mode"] == "checkpoint":
        from hydra_training_v5.peano_hydra.paired_checkpoint import PairedCheckpointStore

        with PairedCheckpointStore(Path(request["input_path"]), plan, plan.origin,
                                   verify_only=True, replay_proofs=False) as store:
            verification = store.receipt(status="metadata-validated")
            identity = {"kind": "checkpoint-prefix", "rows": list(store.hashes),
                        "header_file_sha256": hashlib.sha256(store._read("header.json", cp_max_header())[1]).hexdigest(),
                        "head_file_sha256": hashlib.sha256(store._read("HEAD.json", cp_max_header())[1]).hexdigest()}
            for index, row in enumerate(store.rows):
                if row["kernel_checked"]:
                    binding = store._goal_binding(index)
                    positives.append(_positive(binding["lane"], plan.execution.goals[index % 32], row, record, index + 1))
            comparison._refresh(plan)
            store.assert_unchanged()
    else:
        comparison._refresh(plan)
    require(len(positives) <= 64, "paired positive inventory exceeds its fixed panel")
    _no_models()
    result = {"schema": WORKER_SCHEMA, "mode": request["mode"], "request_sha256": digest(request),
              "plan": record, "input_identity": identity, "verification": verification,
              "positives": positives, "model_frameworks_imported": False, "model_generation_performed": False}
    require(len(canonical(result)) < METADATA_LIMITS.output_bytes, "paired metadata response exceeds its byte bound")
    return result


def cp_max_header():
    from hydra_training_v5.peano_hydra.comparison_checkpoint import MAX_HEADER_BYTES
    return MAX_HEADER_BYTES


def _metadata(request, *, runtime_library_paths=()):
    payload = canonical(request)
    require(len(payload) <= MAX_REQUEST_BYTES, "paired metadata request exceeds its byte bound")
    command = (sys.executable, "-I", "-B", "-X", "pycache_prefix=/dev/null", str(SCRIPT), "--metadata-worker")
    process = run_bounded(command, cwd=ROOT, limits=METADATA_LIMITS, input_bytes=payload,
                          runtime_library_paths=runtime_library_paths)
    if process["reason"] != "exited" or process["returncode"] != 0:
        raise SearchWorkflowError("bounded paired metadata validation did not complete; no automatic retry",
                                  observation={"process": process})
    validate_process_record(process, command=command, limits=METADATA_LIMITS, input_bytes=payload,
                            success_codes=(0,), runtime_library_paths=runtime_library_paths)
    result = bridge._decode(process["stdout"].encode(), METADATA_LIMITS.output_bytes, "paired metadata response")
    bridge._keys(result, {"schema", "mode", "request_sha256", "plan", "input_identity", "verification", "positives",
                          "model_frameworks_imported", "model_generation_performed"}, "paired metadata response")
    require(result["schema"] == WORKER_SCHEMA and result["mode"] == request["mode"]
            and result["request_sha256"] == digest(request) and result["model_frameworks_imported"] is False
            and result["model_generation_performed"] is False, "paired metadata response lost its request binding")
    _recheck_source(result["plan"])
    return result, process


def offline_check(reference_path, reference_sha256, *, mode="plan", input_path=None,
                  source_root=None, adapter_manifest=None, progress=None):
    """Plan or verify using bounded native children; parent stays source-only."""
    _no_models()
    require(mode in MODES, "unknown paired CPU check mode")
    require((input_path is None) == (mode == "plan"), "paired CPU check mode/input differ")
    require(mode == "plan" or not os.environ.get("SLURM_JOB_ID"),
            "independent paired replay must run in a separate local CPU environment")
    request = {"schema": REQUEST_SCHEMA, "mode": mode,
               "reference_path": str(bridge._absolute(Path(reference_path))), "reference_sha256": reference_sha256,
               "source_root": None if source_root is None else str(bridge._absolute(Path(source_root))),
               "adapter_manifest": None if adapter_manifest is None else str(bridge._absolute(Path(adapter_manifest))),
               "input_path": None if input_path is None else str(bridge._absolute(Path(input_path)))}
    bridge._hash(reference_sha256, "external corrected origin reference SHA")
    libraries = ()
    if os.environ.get("SLURM_JOB_ID"):
        from hydra_training_v5.peano_hydra.helios_runtime import reviewed_runtime_library_paths
        libraries = reviewed_runtime_library_paths()
    checked, process = _metadata(request, runtime_library_paths=libraries)
    audit = {"schema": AUDIT_SCHEMA, "mode": mode, "status": "passed",
             "plan_sha256": checked["plan"]["plan_sha256"], "metadata_process": process,
             "model_generation_performed": False, "gpu_jobs_started": 0, "automatic_retry": False}
    if mode == "plan":
        _no_models()
        return checked["plan"], audit
    require(type(checked["positives"]) is list and len(checked["positives"]) <= 64,
            "paired metadata returned an invalid positive inventory")
    report_view = None
    if mode == "report":
        raw = bridge._read(Path(input_path).absolute(), MAX_REPORT_BYTES)
        require(checked["input_identity"] == {"kind": "report-file", "bytes": len(raw),
                                               "sha256": hashlib.sha256(raw).hexdigest()},
                "report changed after bounded metadata authentication")
        report_view = bridge._decode(raw, MAX_REPORT_BYTES, "authenticated paired report")
    replays = []
    for descriptor in checked["positives"]:
        _recheck_source(checked["plan"])
        positive = _hydrate_positive(descriptor, checked, mode, input_path, report_view)
        payload = canonical(positive["request"])
        require(len(payload) <= MAX_REPLAY_REQUEST_BYTES, "paired positive replay request exceeds its byte bound")
        command = (sys.executable, "-I", "-B", "-X", "pycache_prefix=/dev/null",
                   str(ROOT / "scripts/eval_peano_hydra_capacity.py"), "--replay-worker")
        receipt = run_bounded(command, cwd=ROOT, limits=REPLAY_LIMITS, input_bytes=payload)
        if receipt["reason"] != "exited" or receipt["returncode"] != 0:
            raise SearchWorkflowError("independent paired proof replay did not complete; no automatic retry",
                observation={"mode": mode, "lane": positive["lane"], "goal": positive["goal"],
                             "completed_replays": replays, "process": receipt})
        validate_process_record(receipt, command=command, limits=REPLAY_LIMITS, input_bytes=payload, success_codes=(0,))
        fresh = bridge._decode(receipt["stdout"].encode(), REPLAY_LIMITS.output_bytes, "independent paired replay")
        require(canonical(fresh) == canonical(positive["saved_replay"]) and fresh.get("kernel_checked") is True
                and fresh.get("theorem") == positive["request"]["statement"]
                and fresh.get("proof_nodes") == positive["proof_nodes"],
                "independent native replay differs from the authenticated paired positive")
        replays.append({key: positive[key] for key in ("lane", "goal", "commands_sha256", "proof_nodes")}
                       | {"replay_process": _summary(receipt)})
        if progress is not None:
            progress({"phase": "positive-replayed", "completed": len(replays), "total": len(checked["positives"]),
                      "lane": positive["lane"], "goal": positive["goal"]})
    # A second metadata check is post-replay input validation, not a retry of
    # failed work. It never regenerates model proposals or replays a proof.
    after, post_process = _metadata(request)
    require(canonical(after) == canonical(checked), "paired report/checkpoint/origin changed during independent replay")
    _recheck_source(checked["plan"])
    _no_models()
    verification = {**checked["verification"], "proof_replay_performed": True,
                    "independently_replayed_proofs": replays, "verification_complete": True,
                    "input_identity": checked["input_identity"], "model_outputs_regenerated": False,
                    "historical_gpu_inference_attested": False, "research_claim_eligible": False}
    if mode == "checkpoint":
        verification["committed_prefix_verified"] = True
        verification["complete_comparison"] = (verification["all_goal_records_present"]
                                                and verification["inflight"] is None)
        verification["verification_complete"] = verification["complete_comparison"]
        verification["status"] = "complete-checkpoint-verified" if verification["complete_comparison"] else (
            "interrupted-prefix-verified" if verification["inflight"] is not None else "clean-prefix-verified")
    audit["metadata_process"] = _summary(process)
    audit["post_replay_metadata_process"] = _summary(post_process)
    audit["independent_positive_replays"] = len(replays)
    return verification, audit
