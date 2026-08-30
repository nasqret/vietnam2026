"""Bounded local admission and explicit approval for one fresh Hydra experiment.

Planning never grants compute authority. Approved cluster stages must bind an
externally supplied raw readiness hash, both old-origin receipts, the input
package, and current execution sources. Historical receipts are data, not shell
commands. No mode uploads, trains, or automatically retries a failed stage.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import re
import resource
import stat
import sys
import uuid

ROOT = Path(__file__).absolute().parents[2]
PROFILE = "peano-hydra-corrective-v2"
RUN_ID = "corrective-v2"
BUNDLE = "_deploy/hydra-corrective-v2"
INPUT = "_deploy/hydra-corrective-v2-inputs/origin-request.json"
APPROVAL = "_deploy/hydra-corrective-v2-inputs/approval.json"
# This second attempt receives one additional CPU reservation, not another
# GPU allowance. The first attempt's immutable ledger charged no GPU work.
PRIOR_ATTEMPT = {
    "profile": "peano-hydra-corrective-v1",
    "source_commit": "26dd5c6527ed80b5fc8b49bfba86c9e2addefec3",
    "approval_sha256": "b8d713335981b17a443033001f66cdafdcd39949f7caf5891c1af9808daaa6b9",
    "ledger": "logs/hydra-corrective-v1.jsonl",
    "ledger_sha256": "85769e0edc5b14a1db2f1bda17bf830a62715798ca21d9543c5cd9b06fe1a1c0",
    "cpu_job_id": "21402731",
    "cpu_reserved_seconds": 1200,
    "gpu_reserved_seconds": 0,
}
INPUT_SCHEMA = "peano-hydra-corrective-origin-inputs-v1"
READINESS_SCHEMA = "peano-hydra-corrective-readiness-v1"
APPROVAL_SCHEMA = "peano-hydra-corrective-approval-v2"
SOURCE_SCHEMA = "peano-hydra-native-witness-corrective-source-v1"
SOURCE_COMMIT = "85a970b1b24170edb9997d5328c1eb6d1d95a8fd"
EPOCH_PAYLOADS = (
    "book/_static/constructive-grand-campaign/campaign.json",
    "book/_static/constructive-grand-campaign/definitions.json",
    "artifacts/peano-library/catalog-v1.json", "artifacts/peano-library/channels-v25.json",
    "artifacts/peano-library/alpha/catalog-v25.json",
)
CORRECTIVE_ORIGIN_PAYLOADS = tuple(
    "artifacts/peano-hydra/native-search-repair-2026-08-28/witness-fixture-02/" + name
    for name in ("plan.json", "manifest.json", "coverage.json", "proofs.json", "sft.jsonl")
)
PINS = {
    "catalog": {
        "preparation_relative_path": "_deploy/hydra-posttrain-capacity-fit",
        "preparation_manifest_sha256": "094482ca2949a4248e5720384bb50970259850aaf80dc4f690c94efcf9cea0c2",
        "adapter_manifest_sha256": "723d0f8109c0272774f445c552d781c8e64cadfa50d0516246eb0fa2fd31a955",
        "authority_profile": None,
    },
    "scaled": {
        "preparation_relative_path": "_deploy/hydra-authority-scale-v1-attempt2/preparation",
        "preparation_manifest_sha256": "3f240267eb89ba58b52cf61514bf995965709f22653e7a0b9d5f2b3d7f712c40",
        "adapter_manifest_sha256": "e3c569796be42cdfb3afd677c3c6c1a6e82c67728b8410a410034c35791d20a4",
        "authority_profile": "peano-authority-primitive-v1",
    },
}
JOBS = {stage: f"slurm/peano_hydra_corrective_{stage}.sbatch" for stage in ("prepare", "train", "evaluate")}
RESERVATIONS = {
    "prepare": {"seconds": 1200, "gpus": 0, "cpus": 4, "memory_gib": 8},
    "train": {"seconds": 5400, "gpus": 1, "cpus": 8, "memory_gib": 64},
    "evaluate": {"seconds": 1800, "gpus": 1, "cpus": 8, "memory_gib": 64},
}
STAGES = ("source", "preparation", "preflight", "capacity-plan")
NATIVE_LIMITS = {"cpu_seconds": 120, "wall_seconds": 180, "rss_bytes": 2 * 1024**3, "output_bytes": 4 * 1024**2}
MAX_JSON = 4 * 1024**2
MAX_FILE = 512 * 1024**2
MAX_PAYLOAD_FILES = 4096
COUNTS = {"teacher_routes": 1024, "train_rows": 8932, "dev_rows": 744, "optimizer_steps": 1117}
READINESS_FIELDS = {
    "schema", "profile", "run_id", "status", "complete", "output_directory", "origin_request_file",
    "origin_request_sha256", "preserved_origins", "files", "source_manifest_sha256",
    "preparation_manifest_sha256", "capacity_plan_sha256", "epoch_sha256", *COUNTS,
    "execution_source_files", "native_stage_limits", "token_budget_checked", "token_audit_required_before_weights",
    "model_training_authorized", "model_trained", "research_claim_eligible",
    "same_process_publication_rechecks_are_independent_process_checks", "readiness_sha256",
}
APPROVAL_FIELDS = {
    "schema", "profile", "run_id", "approved", "approval_reference", "source_commit", "source_files",
    "origin_request_sha256", "ready_bundle_sha256", "reservations", "maximum_aggregate_gpu_seconds",
    "maximum_concurrent_gpus", "automatic_retry", "payloads", "payloads_sha256",
    "prior_attempt",
}
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_COMMIT = re.compile(r"[0-9a-f]{40}\Z")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def decode(raw):
    require(len(raw) <= MAX_JSON, "corrective JSON exceeds its bound")
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "duplicate corrective JSON key")
            result[key] = value
        return result
    def nonfinite(value):
        raise ValueError("non-finite corrective JSON: " + value)
    value = json.loads(raw, object_pairs_hook=pairs, parse_constant=nonfinite)
    require(type(value) is dict, "corrective JSON must be an object")
    return value


def directory(path):
    path = Path(path).absolute()
    require(".." not in path.parts and 1 < len(path.parts) <= 64 and len(str(path).encode()) <= 4096,
            "unsafe corrective directory path")
    access = getattr(os, "O_PATH", os.O_RDONLY) if sys.platform == "linux" else os.O_RDONLY
    fd = os.open(path.anchor, access | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for index, part in enumerate(path.parts[1:], 1):
            flags = os.O_RDONLY if index == len(path.parts) - 1 else access
            child = os.open(part, flags | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
        result, fd = fd, -1
        return result
    finally:
        if fd >= 0:
            os.close(fd)


def project_path(relative):
    require(type(relative) is str and 0 < len(relative.encode()) <= 4096, "invalid project-relative path")
    path = Path(relative)
    require(not path.is_absolute() and all(part not in {"", ".", ".."} for part in relative.split("/")),
            "path must remain canonical and project-relative")
    return ROOT / path


def relative(path):
    path = Path(path).absolute()
    require(".." not in path.parts, "path contains traversal")
    return project_path(path.relative_to(ROOT).as_posix()).relative_to(ROOT).as_posix()


def read(path, maximum=MAX_JSON):
    parent = directory(Path(path).parent)
    fd = -1
    try:
        fd = os.open(Path(path).name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        before = os.fstat(fd)
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_size <= maximum,
                "corrective input must be a bounded single-link regular file")
        chunks, size = [], 0
        while True:
            block = os.read(fd, min(65536, maximum + 1 - size))
            if not block:
                break
            size += len(block)
            require(size <= maximum, "corrective input grew beyond its bound")
            chunks.append(block)
        after = os.fstat(fd)
        current = os.stat(Path(path).name, dir_fd=parent, follow_symlinks=False)
        fields = ("st_dev", "st_ino", "st_nlink", "st_size", "st_mtime_ns", "st_ctime_ns")
        require(size == before.st_size and all(getattr(before, field) == getattr(after, field) == getattr(current, field)
                                              for field in fields), "corrective input changed during reading")
        return b"".join(chunks)
    finally:
        if fd >= 0:
            os.close(fd)
        os.close(parent)


def file_record(path):
    # Bound memory even for the two safetensors adapters in a staged package.
    path = Path(path)
    parent, fd = directory(path.parent), -1
    try:
        fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        before = os.fstat(fd)
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_size <= MAX_FILE,
                "payload must be a bounded single-link regular file")
        size, hasher = 0, hashlib.sha256()
        while block := os.read(fd, 1024**2):
            size += len(block)
            require(size <= MAX_FILE, "payload grew beyond its byte bound")
            hasher.update(block)
        after = os.fstat(fd)
        current = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
        fields = ("st_dev", "st_ino", "st_nlink", "st_size", "st_mtime_ns", "st_ctime_ns")
        require(size == before.st_size and all(getattr(before, key) == getattr(after, key) == getattr(current, key)
                                               for key in fields), "payload changed during hashing")
        return {"bytes": size, "sha256": hasher.hexdigest()}
    finally:
        if fd >= 0:
            os.close(fd)
        os.close(parent)


def protected_roots(*, origin_request=None, bundle=None, extra=()):
    roots = [ROOT / "_deploy/hydra-authority-scale-build-20260828",
             ROOT / "_deploy/hydra-corrective-v1",
             ROOT / "_deploy/hydra-corrective-inputs",
             ROOT / "artifacts/peano-hydra/authority-scale-2026-08-28",
             ROOT / "artifacts/peano-hydra/native-search-repair-2026-08-28", *extra]
    if bundle is not None:
        roots.append(Path(bundle))
        summary = Path(bundle) / "preparation.json"
        if summary.exists() or summary.is_symlink():
            roots.append(project_path(decode(read(summary))["adapter_output_dir"]))
    if origin_request is not None and (Path(origin_request).exists() or Path(origin_request).is_symlink()):
        _, requests, _ = load_origin_requests(origin_request)
        roots.extend(request.source_root for request in requests.values())
        roots.extend(request.adapter_manifest.parent for request in requests.values())
    return tuple(dict.fromkeys(Path(path).absolute() for path in roots))


def guard_output(path, *, protected=()):
    """Check before any work and again before publishing, without creating files.

    No symlink ancestor is followed. Inode checks also catch an existing
    directory alias (e.g. a bind mount), not just lexical descendant paths.
    """
    path = Path(path).absolute()
    require(".." not in path.parts and path.name not in {"", ".", ".."}, "unsafe output path")
    parent = directory(path.parent)
    os.close(parent)
    require(not path.exists() and not path.is_symlink(), "output must be fresh")
    ancestor_ids = set()
    for ancestor in (path.parent, *path.parent.parents):
        info = ancestor.stat(follow_symlinks=False)
        ancestor_ids.add((info.st_dev, info.st_ino))
    for root in protected:
        root = Path(root).absolute()
        require(path != root and root not in path.parents, "output is inside protected input: " + str(root))
        if root.exists() or root.is_symlink():
            fd = directory(root)
            try:
                info = os.fstat(fd)
                require((info.st_dev, info.st_ino) not in ancestor_ids, "output aliases protected input")
            finally:
                os.close(fd)
    return path


def publish_metadata(path, value, *, protected=(), raw=False):
    return write_new(guard_output(path, protected=protected), value, raw=raw)


def write_new(path, value, *, raw=False):
    payload = value if raw else (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
    require(type(payload) is bytes and len(payload) <= MAX_JSON, "corrective output exceeds its bound")
    parent = directory(Path(path).parent)
    temporary = ".corrective-publication-" + uuid.uuid4().hex
    try:
        try:
            os.stat(Path(path).name, dir_fd=parent, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise ValueError("output must be fresh")
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=parent)
        with os.fdopen(fd, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, Path(path).name, src_dir_fd=parent, dst_dir_fd=parent, follow_symlinks=False)
        os.unlink(temporary, dir_fd=parent)
        os.fsync(parent)
    finally:
        os.close(parent)


def specification():
    return {"schema": "peano-hydra-corrective-experiment-specification-v1", "profile": PROFILE,
            "run_id": RUN_ID, "source_schema": SOURCE_SCHEMA,
            "teacher_routes": 1024, "train_rows": 8932, "dev_rows": 744, "optimizer_steps": 1117,
            "training": "one fresh-base epoch; no continuation, repetition, sweep or checkpoint selection",
            "roles": ["base", "catalog", "scaled", "corrected"], "primary_goals_per_role": 32,
            "total_goal_records": 128, "maximum_model_calls": 1024,
            "reservations": RESERVATIONS, "maximum_aggregate_gpu_seconds": 7200,
            "maximum_concurrent_gpus": 1, "automatic_retry": False,
            "launch_protocol": "submit the complete held chain before releasing evaluate, train, then prepare",
            "prior_attempt": dict(PRIOR_ATTEMPT),
            "gpu_authorized": False, "source_admission_performed": False,
            "model_trained": False, "autonomous_improvement_verified": False,
            "claim": "Exposed corrective curriculum and development ablation, not unseen generalization."}


def execution_sources():
    from training.peano_hydra.corrective_comparison import _sources
    sources = _sources()
    for name in (*JOBS.values(), "scripts/helios_common.sh", "scripts/helios_hydra_corrective.sh",
                 "training/peano_hydra/corrective_launch.py",
                 "training/peano_hydra/review_sources.py", "training/peano_hydra/witness_repair.py",
                 "scripts/prepare_peano_hydra_witness_repair.py",
                 "scripts/helios_submit_job.sh", "scripts/submit_slurm_job.sh", "scripts/helios_hydra_chain.sh"):
        sources[name] = hashlib.sha256(read(ROOT / name, 2 * 1024**2)).hexdigest()
    return dict(sorted(sources.items()))


def load_origin_requests(path):
    from training.peano_hydra.origin_bridge import OriginRequest
    raw = read(path)
    record = decode(raw)
    require(set(record) == {"schema", "source_commit", "source_root", "source_manifest", "source_manifest_sha256", "origins"}
            and record["schema"] == INPUT_SCHEMA and record["source_commit"] == SOURCE_COMMIT,
            "origin package must declare the exact preserved source commit")
    require(type(record["source_manifest_sha256"]) is str and _SHA.fullmatch(record["source_manifest_sha256"]),
            "origin source bundle needs its external raw SHA")
    require(type(record["origins"]) is dict and set(record["origins"]) == set(PINS), "origin package role inventory differs")
    origin_root, manifest_path = project_path(record["source_root"]), project_path(record["source_manifest"])
    requests = {}
    for role, pin in PINS.items():
        value = record["origins"][role]
        require(type(value) is dict and set(value) == {*pin, "adapter_manifest"}
                and canonical({key: value[key] for key in pin}) == canonical(pin),
                "origin package changed an original preparation, adapter or authority anchor")
        requests[role] = OriginRequest(
            origin_root, manifest_path, record["source_manifest_sha256"], SOURCE_COMMIT,
            origin_root / value["preparation_relative_path"], value["preparation_manifest_sha256"],
            project_path(value["adapter_manifest"]), value["adapter_manifest_sha256"], value["authority_profile"])
    return record, requests, hashlib.sha256(raw).hexdigest()


def runtime_libraries():
    if os.environ.get("SLURM_JOB_ID") is None:
        return ()
    from training.peano_hydra.helios_runtime import reviewed_runtime_library_paths
    return reviewed_runtime_library_paths()


def worker(request):
    soft, hard = resource.getrlimit(resource.RLIMIT_CPU)
    require((soft, hard) == (NATIVE_LIMITS["cpu_seconds"], NATIVE_LIMITS["cpu_seconds"] + 1),
            "corrective worker requires its inherited finite CPU guard")
    fields = {"source": {"stage", "output"}, "preparation": {"stage", "source", "output", "run_id"},
              "preflight": {"stage", "preparation"}, "capacity-plan": {"stage", "preparation"},
              "verify-data": {"stage", "preparation"}, "source-plan": {"stage"}}
    comparison_fields = {"stage", "experiment", "origin_request", "expected_readiness_sha256", "trained_adapter"}
    fields.update({"comparison-plan": comparison_fields, "comparison-report": comparison_fields | {"report"}})
    stage = request.get("stage")
    require(type(stage) is str and stage in fields and set(request) == fields[stage]
            and all(type(value) is str and (key == "trained_adapter" or len(value) > 0) and len(value) <= 4096
                    for key, value in request.items()),
            "invalid corrective worker request")
    if stage in {"comparison-plan", "comparison-report"}:
        from training.peano_hydra import corrective_comparison as comparison
        from training.peano_hydra.evaluation import _json_object
        experiment = project_path(request["experiment"])
        _, references = load_bundle(experiment, origin_request=project_path(request["origin_request"]),
                                    expected_readiness_sha256=request["expected_readiness_sha256"])
        adapter = project_path(request["trained_adapter"]) if request["trained_adapter"] else None
        plan = comparison.build_corrective_plan(experiment / "preparation", catalog=references["catalog"],
                                                scaled=references["scaled"], trained_adapter=adapter)
        if stage == "comparison-plan":
            return plan.to_dict()
        raw = read(project_path(request["report"]), comparison.comparison.MAX_REPORT_BYTES)
        # Structural/origin verification in this guarded worker; each positive
        # is subsequently replayed by its own guarded child, never nested here.
        result = comparison.validate_result(plan, _json_object(raw, description="corrective result"), replay=False)
        return {"verification": result, "report_file_sha256": hashlib.sha256(raw).hexdigest()}
    from training.peano_hydra import posttrain
    if stage == "source-plan":
        from training.peano_hydra.corrective_source import corrective_source_profile_record
        return corrective_source_profile_record()
    if stage == "source":
        from training.peano_hydra.corrective_source import build_corrective_source, publish_corrective_source
        source = build_corrective_source()
        destination = publish_corrective_source(source, project_path(request["output"]))
        return {"source_directory": relative(destination), "source_schema": SOURCE_SCHEMA,
                "epoch_sha256": source.epoch.epoch_sha256,
                "manifest_sha256": hashlib.sha256(source.payloads["manifest.json"]).hexdigest(),
                "verified_routes": source.manifest["composition"]["verified_route_count"],
                "verified_transitions": len(source.curriculum.transitions), "model_generated": False}
    if stage == "preparation":
        require(request["run_id"] == RUN_ID, "corrective run identity is fixed")
        prepared = posttrain.prepare_posttraining(project_path(request["source"]), project_path(request["output"]), run_id=RUN_ID)
        require(prepared.source.manifest["schema"] == SOURCE_SCHEMA, "corrective preparation used another source")
        posttrain.publish_preparation(prepared)
        return preparation_summary(prepared)
    preparation = project_path(request["preparation"])
    if stage == "preflight":
        return posttrain.preflight(preparation)
    if stage == "verify-data":
        # A completed model makes training preflight correctly refuse reuse.
        # Data-only revalidation therefore has its own explicit operation;
        # it does not relax that preflight or authorize another training run.
        prepared = posttrain.load_preparation(preparation)
        require(prepared.source.manifest["schema"] == SOURCE_SCHEMA, "corrective source was replaced")
        posttrain._validate_model_config(prepared.config)
        posttrain._proof_examples(prepared, prepared.train_rows, split="train")
        posttrain._proof_examples(prepared, prepared.development_rows, split="dev")
        return preparation_summary(prepared)
    from training.peano_hydra.capacity import build_capacity_plan
    return build_capacity_plan(preparation, authority_profile="peano-authority-primitive-v1").to_dict()


def preparation_summary(prepared):
    return {"preparation_directory": relative(prepared.output_directory),
            "manifest_sha256": hashlib.sha256(prepared.payloads["manifest.json"]).hexdigest(),
            "training_rows": len(prepared.train_rows), "development_rows": len(prepared.development_rows),
            "quarantine_rows": prepared.manifest["held_out"]["quarantine_rows"],
            "adapter_output_dir": prepared.config.run.output_dir}


def admission_requests(bundle):
    return (
        {"stage": "source", "output": bundle + "/source"},
        {"stage": "preparation", "source": bundle + "/source", "output": bundle + "/preparation", "run_id": RUN_ID},
        {"stage": "preflight", "preparation": bundle + "/preparation"},
        {"stage": "capacity-plan", "preparation": bundle + "/preparation"},
    )


def check_admission_summaries(results, *, bundle):
    source, preparation, preflight, plan = (results[name] for name in STAGES)
    require(set(source) == {"source_directory", "source_schema", "epoch_sha256", "manifest_sha256",
                            "verified_routes", "verified_transitions", "model_generated"}
            and source["source_directory"] == bundle + "/source" and source["source_schema"] == SOURCE_SCHEMA
            and source["model_generated"] is False, "source admission summary differs")
    require(set(preparation) == {"preparation_directory", "manifest_sha256", "training_rows", "development_rows",
                                 "quarantine_rows", "adapter_output_dir"}
            and preparation["preparation_directory"] == bundle + "/preparation",
            "preparation admission summary differs")
    for record, fields in ((source, {"verified_routes": 1024, "verified_transitions": 9676}),
                           (preparation, {"training_rows": 8932, "development_rows": 744, "quarantine_rows": 0}),
                           (preflight, {"training_rows": 8932, "development_rows": 744, "quarantined_rows": 0,
                                        "expected_optimizer_steps": 1117})):
        require(all(type(record.get(key)) is int and record[key] == count for key, count in fields.items()),
                "mixed admission disagrees with its fixed exact integer counts")
    require(preflight.get("schema") == "peano-hydra-posttrain-preflight-v2"
            and preflight.get("authority_profile") == "peano-authority-primitive-v1"
            and preflight.get("run_id") == RUN_ID
            and preflight.get("preparation_manifest_sha256") == preparation["manifest_sha256"]
            and preflight.get("adapter_output_dir") == preparation["adapter_output_dir"]
            and all(preflight.get(key) is False for key in ("model_trained", "cuda_initialized",
                    "historical_model_authority_changed", "research_claim_eligible", "token_budget_verified",
                    "unseen_holdout_claim_eligible"))
            and preflight.get("tokenizer_audit_required_before_model_weights") is True,
            "preflight inflated its training, token or authority claims")
    project_path(preparation["adapter_output_dir"])
    require(plan.get("schema") == "peano-hydra-exposed-capacity-plan-v2"
            and plan.get("authority_profile") == "peano-authority-primitive-v1"
            and plan.get("plan_sha256") == digest({key: value for key, value in plan.items() if key != "plan_sha256"})
            and plan.get("preparation_manifest_sha256") == preparation["manifest_sha256"]
            and source["epoch_sha256"] == preflight.get("epoch_sha256") == plan.get("epoch_sha256")
            and all(plan.get(key) is False for key in ("research_claim_eligible", "sealed_benchmark",
                                                     "final_benchmark_expanded", "independent_discoveries")),
            "admitted execution panel or mathematical epoch differs")
    for value in (source["manifest_sha256"], source["epoch_sha256"], preparation["manifest_sha256"], plan["plan_sha256"]):
        require(type(value) is str and _SHA.fullmatch(value), "admission summary has a malformed digest")


def saved_admission_results(output):
    """Validate portable historical worker receipts as data, never execute argv."""
    from training.peano_hydra.review_runtime import ProcessLimits, validate_process_record
    results = {}
    for request in admission_requests(relative(output)):
        name = request["stage"]
        process = decode(read(output / (name + "-process.json")))
        command = process.get("command")
        require(type(command) is list and len(command) == 6 and type(command[0]) is str
                and Path(command[0]).is_absolute()
                and command[1:] == ["-B", "-X", "pycache_prefix=/dev/null", "scripts/prepare_peano_hydra_corrective.py", "--worker"],
                "saved admission changed its guarded source-only worker command")
        validate_process_record(process, command=tuple(command), limits=ProcessLimits(**NATIVE_LIMITS),
                                input_bytes=canonical(request), success_codes=(0,))
        result = decode(read(output / (name + ".json")))
        require(canonical(decode(process["stdout"].encode())) == canonical(result),
                "saved admission result differs from the worker's exact output")
        results[name] = result
    check_admission_summaries(results, bundle=relative(output))
    return results


def stage(request, *, output=None):
    from training.peano_hydra.review_runtime import ProcessLimits, run_bounded, validate_process_record
    limits = ProcessLimits(**NATIVE_LIMITS)
    command = (sys.executable, "-B", "-X", "pycache_prefix=/dev/null", "scripts/prepare_peano_hydra_corrective.py", "--worker")
    payload = canonical(request)
    options = {"runtime_library_paths": runtime_libraries()} if os.environ.get("SLURM_JOB_ID") else {}
    print("corrective: " + request["stage"] + " (CPU<=120s, wall<=180s, RSS<=2GiB)", file=sys.stderr, flush=True)
    before = execution_sources()
    process = run_bounded(command, cwd=ROOT, limits=limits, input_bytes=payload, **options)
    if output is not None:
        write_new(output / (request["stage"] + "-process.json"), process)
    validate_process_record(process, command=command, limits=limits, input_bytes=payload, success_codes=(0,), **options)
    require(execution_sources() == before, "execution source changed during bounded admission")
    value = decode(process["stdout"].encode())
    if output is not None:
        write_new(output / (request["stage"] + ".json"), value)
    return value


def prepare_bundle(output, *, origin_request, run_id=RUN_ID):
    from training.peano_hydra.origin_bridge import authenticate_origin
    require(run_id == RUN_ID and relative(output) == BUNDLE, "corrective preparation has one declared run/path")
    inputs, requests, input_sha = load_origin_requests(origin_request)
    protected = protected_roots(origin_request=origin_request)
    guard_output(output, protected=protected)
    parent = directory(output.parent)
    try:
        guard_output(output, protected=protected)
        os.mkdir(output.name, 0o700, dir_fd=parent)
        os.fsync(parent)
    finally:
        os.close(parent)
    origins = {}
    for role in PINS:
        print("corrective: authenticate preserved " + role + " origin", file=sys.stderr, flush=True)
        try:
            verified = authenticate_origin(requests[role], python=Path(sys.executable), runtime_library_paths=runtime_libraries())
        except (ValueError, TypeError, KeyError, OSError, RuntimeError, ImportError) as error:
            # Preserve even an original-validator CPU/resource failure. This
            # directory is incomplete; neither a handle nor readiness exists.
            write_new(output / (role + "-origin-failure.json"), {
                "schema": "peano-hydra-corrective-origin-failure-v1", "role": role,
                "status": "not-authenticated", "error": " ".join(str(error).split())[:3000],
                "observation": getattr(error, "observation", None), "automatic_retry": False,
            })
            raise
        name = role + "-origin.json"
        write_new(output / name, verified.receipt_bytes, raw=True)
        origins[role] = {"file": name, "sha256": verified.receipt_sha256,
                         "request": requests[role].to_dict(), "origin_sha256": verified.origin["origin_sha256"]}
    bundle = relative(output)
    results = {request["stage"]: stage(request, output=output) for request in admission_requests(bundle)}
    source, preparation, preflight, plan = (results[name] for name in STAGES)
    check_admission_summaries(results, bundle=bundle)
    files = {name: file_record(output / name) for name in (
        *(item for key in STAGES for item in (key + ".json", key + "-process.json")),
        "catalog-origin.json", "scaled-origin.json")}
    require(load_origin_requests(origin_request)[2] == input_sha, "origin input changed during admission")
    record = {"schema": READINESS_SCHEMA, "profile": PROFILE, "run_id": RUN_ID, "status": "admitted",
              "complete": True, "output_directory": bundle, "origin_request_file": relative(origin_request),
              "origin_request_sha256": input_sha, "preserved_origins": origins, "files": files,
              "source_manifest_sha256": source["manifest_sha256"],
              "preparation_manifest_sha256": preparation["manifest_sha256"],
              "capacity_plan_sha256": plan["plan_sha256"], "epoch_sha256": source["epoch_sha256"],
              "teacher_routes": 1024, "train_rows": 8932, "dev_rows": 744, "optimizer_steps": 1117,
              "execution_source_files": execution_sources(), "native_stage_limits": NATIVE_LIMITS,
              "token_budget_checked": False, "token_audit_required_before_weights": True,
              "model_training_authorized": False, "model_trained": False, "research_claim_eligible": False,
              "same_process_publication_rechecks_are_independent_process_checks": False}
    record["readiness_sha256"] = digest(record)
    write_new(output / "readiness.json", record)
    return record


def load_bundle(output, *, origin_request, expected_readiness_sha256):
    from training.peano_hydra.corrective_comparison import OriginReceipt
    raw = read(output / "readiness.json")
    require(type(expected_readiness_sha256) is str and _SHA.fullmatch(expected_readiness_sha256)
            and hashlib.sha256(raw).hexdigest() == expected_readiness_sha256,
            "bundle requires its external raw readiness anchor, not a self-hashed claim")
    ready = decode(raw)
    require(set(ready) == READINESS_FIELDS and ready.get("schema") == READINESS_SCHEMA and ready.get("profile") == PROFILE
            and ready.get("run_id") == RUN_ID and ready.get("complete") is True
            and ready.get("status") == "admitted"
            and ready.get("model_training_authorized") is False and ready.get("model_trained") is False
            and all(ready.get(key) is False for key in ("token_budget_checked", "research_claim_eligible",
                         "same_process_publication_rechecks_are_independent_process_checks"))
            and ready.get("token_audit_required_before_weights") is True
            and all(type(ready.get(key)) is int and ready[key] == count for key, count in COUNTS.items())
            and canonical(ready.get("native_stage_limits")) == canonical(NATIVE_LIMITS)
            and ready.get("readiness_sha256") == digest({key: value for key, value in ready.items() if key != "readiness_sha256"})
            and ready.get("output_directory") == relative(output) == BUNDLE,
            "incorrect, incomplete or relabelled corrective readiness")
    _, requests, input_sha = load_origin_requests(origin_request)
    require(ready["origin_request_sha256"] == input_sha and ready["origin_request_file"] == relative(origin_request),
            "readiness changed its explicitly supplied origin input")
    expected_files = {item for key in STAGES for item in (key + ".json", key + "-process.json")}
    expected_files.update({"catalog-origin.json", "scaled-origin.json"})
    require(type(ready["files"]) is dict and set(ready["files"]) == expected_files,
            "readiness stage inventory differs")
    fd = directory(output)
    try:
        require(set(os.listdir(fd)) == expected_files | {"readiness.json", "source", "preparation"},
                "bundle has missing or unexpected entries")
    finally:
        os.close(fd)
    for name, expected in ready["files"].items():
        require(file_record(output / name) == expected, "saved admission receipt bytes changed")
    require(ready["execution_source_files"] == execution_sources(), "admitted execution sources changed")
    results = saved_admission_results(output)
    source, preparation, preflight, plan = (results[name] for name in STAGES)
    require(ready["source_manifest_sha256"] == source["manifest_sha256"]
            and ready["preparation_manifest_sha256"] == preparation["manifest_sha256"]
            and ready["capacity_plan_sha256"] == plan["plan_sha256"]
            and ready["epoch_sha256"] == source["epoch_sha256"], "readiness does not join its guarded admission results")
    require(hashlib.sha256(read(output / "source/manifest.json")).hexdigest() == ready["source_manifest_sha256"]
            and hashlib.sha256(read(output / "preparation/manifest.json")).hexdigest() == ready["preparation_manifest_sha256"],
            "admitted source or preparation manifest changed")
    require(type(ready["preserved_origins"]) is dict and set(ready["preserved_origins"]) == set(PINS),
            "readiness changed its preserved role inventory")
    references = {}
    for role, request in requests.items():
        saved = ready["preserved_origins"][role]
        require(type(saved) is dict and set(saved) == {"file", "request", "sha256", "origin_sha256"}
                and saved["file"] == role + "-origin.json" and saved["request"] == request.to_dict()
                and saved["sha256"] == ready["files"][saved["file"]]["sha256"], "origin receipt binding changed")
        reference = OriginReceipt(request, output / saved["file"], saved["sha256"])
        require(reference.load().origin["origin_sha256"] == saved["origin_sha256"], "preserved origin digest changed")
        references[role] = reference
    return ready, references


def verify_bundle(output, *, origin_request, expected_readiness_sha256):
    ready, _ = load_bundle(output, origin_request=origin_request, expected_readiness_sha256=expected_readiness_sha256)
    fresh = stage({"stage": "verify-data", "preparation": relative(output) + "/preparation"})
    require(fresh == decode(read(output / "preparation.json")), "freshly replayed admitted data differ")
    fresh_plan = stage({"stage": "capacity-plan", "preparation": relative(output) + "/preparation"})
    require(fresh_plan == decode(read(output / "capacity-plan.json")), "fresh execution panel differs")
    load_bundle(output, origin_request=origin_request, expected_readiness_sha256=expected_readiness_sha256)
    return {"schema": READINESS_SCHEMA, "status": "verified", "readiness_file_sha256": expected_readiness_sha256,
            "teacher_routes": ready["teacher_routes"], "train_rows": ready["train_rows"], "dev_rows": ready["dev_rows"],
            "token_audit_required_before_weights": True, "model_training_authorized": False, "model_trained": False}


def offline_comparison(output, *, origin_request, expected_readiness_sha256, trained_adapter=None, report=None):
    """Bound all native planning/replay, without loading weights in the parent."""
    require(not {"torch", "transformers", "peft"} & set(sys.modules), "offline verification must not load model frameworks")
    before = execution_sources()
    request = {"stage": "comparison-plan" if report is None else "comparison-report", "experiment": relative(output),
               "origin_request": relative(origin_request), "expected_readiness_sha256": expected_readiness_sha256,
               "trained_adapter": "" if trained_adapter is None else relative(trained_adapter)}
    if report is not None:
        require(not os.environ.get("SLURM_JOB_ID"), "independent report replay is a separate local CPU operation")
        request["report"] = relative(report)
    result = stage(request)
    if report is None:
        return result
    from training.peano_hydra import capacity, corrective_comparison as comparison
    from training.peano_hydra.evaluation import _json_object
    from training.peano_hydra.review_runtime import run_bounded, validate_process_record
    raw = read(report, comparison.comparison.MAX_REPORT_BYTES)
    require(hashlib.sha256(raw).hexdigest() == result["report_file_sha256"], "report changed after guarded validation")
    saved_report = _json_object(raw, description="corrective result")
    goals = {goal["name"]: goal for goal in saved_report["plan"]["goals"]}
    checked = []
    for role in comparison.ROLES:
        for row in saved_report["lanes"][role]["primary"]["goals"]:
            if row["kernel_checked"] is not True:
                continue
            goal, saved = goals[row["goal"]], row["evidence"]["replay"]
            replay_request = {"source": goal["source"], "statement": goal["statement"],
                              "commands": row["evidence"]["search"]["commands"], "id": saved["id"],
                              "session": saved["session"],
                              "capabilities": saved_report["plan"]["execution_contract"]["environment"]["capabilities"]}
            payload = canonical(replay_request)
            require(len(payload) <= capacity.MAX_REPLAY_REQUEST_BYTES, "positive replay request exceeds its bound")
            command = (sys.executable, "-B", "-X", "pycache_prefix=/dev/null", str(capacity.SCRIPT), "--replay-worker")
            process = run_bounded(command, cwd=ROOT, limits=capacity.REPLAY_LIMITS, input_bytes=payload)
            validate_process_record(process, command=command, limits=capacity.REPLAY_LIMITS,
                                    input_bytes=payload, success_codes=(0,))
            fresh = _json_object(process["stdout"].encode(), description="independent corrective replay")
            require(canonical(fresh) == canonical(saved) and fresh.get("kernel_checked") is True
                    and fresh.get("theorem") == goal["statement"] and fresh.get("proof_nodes") == row["proof_nodes"],
                    "fresh native replay differs from the authenticated positive")
            summary = {key: value for key, value in process.items() if key not in {"stdout", "stderr", "raw_output_base64"}}
            checked.append({"role": role, "cohort": "primary", "goal": row["goal"],
                            "commands_sha256": row["commands_sha256"], "proof_nodes": row["proof_nodes"],
                            "replay_process": summary})
    require(hashlib.sha256(read(report, comparison.comparison.MAX_REPORT_BYTES)).hexdigest() == result["report_file_sha256"]
            and execution_sources() == before, "report or execution changed during independent verification")
    load_bundle(output, origin_request=origin_request, expected_readiness_sha256=expected_readiness_sha256)
    # Reauthenticate the new dataset payloads and the corrected adapter too,
    # not merely their manifest files or the two preserved origin trees.
    require(canonical(stage(request)) == canonical(result),
            "current data or corrected adapter changed during independent replay")
    return {**result["verification"], "report_file_sha256": result["report_file_sha256"],
            "proof_replay_performed": True, "independently_replayed_proofs": checked}


def payload_files(output, *, origin_request):
    """Exact portable files to stage; never discovers credentials or other runs."""
    inputs, requests, _ = load_origin_requests(origin_request)
    names = {relative(origin_request), inputs["source_manifest"], relative(output / "readiness.json"),
             *EPOCH_PAYLOADS, *CORRECTIVE_ORIGIN_PAYLOADS}
    source_manifest = decode(read(project_path(inputs["source_manifest"])))
    require(type(source_manifest.get("files")) is dict, "source bundle lacks its exact payload inventory")
    for name in source_manifest["files"]:
        names.add(relative(project_path(inputs["source_root"]) / name))
    for request in requests.values():
        preparation = decode(read(request.preparation_directory / "manifest.json"))
        names.update(relative(request.preparation_directory / name) for name in {"manifest.json", *preparation["files"]})
        source_name = preparation["source"]["directory"]
        require(type(source_name) is str and not Path(source_name).is_absolute(), "original source path must stay repository-relative")
        project_path(source_name)
        source = request.source_root / source_name
        names.update(relative(source / name) for name in ("epoch.json", "manifest.json", "sft.jsonl", "preferences.jsonl", "discovery.jsonl"))
        names.add(relative(request.adapter_manifest))
        adapter = decode(read(request.adapter_manifest))
        for kind in ("adapter", "tokenizer"):
            names.update(relative(request.adapter_manifest.parent / name) for name in adapter[kind]["files"])
    ready = decode(read(output / "readiness.json"))
    names.update(relative(output / name) for name in ready["files"])
    names.update(relative(output / "source" / name) for name in ("epoch.json", "manifest.json", "sft.jsonl", "preferences.jsonl", "discovery.jsonl"))
    names.update(relative(output / "preparation" / name) for name in ("manifest.json", "config.toml", "train.jsonl", "dev.jsonl", "preferences.jsonl", "discovery.jsonl", "quarantine.jsonl"))
    require(len(names) <= MAX_PAYLOAD_FILES, "staged payload inventory exceeds its file bound")
    return tuple(sorted(names))


def approval_proposal(output, *, origin_request, source_commit):
    require(type(source_commit) is str and _COMMIT.fullmatch(source_commit), "proposal requires a frozen commit identity")
    check_prior_attempt()
    ready_sha = hashlib.sha256(read(output / "readiness.json")).hexdigest()
    load_bundle(output, origin_request=origin_request, expected_readiness_sha256=ready_sha)
    payloads = {name: file_record(project_path(name)) for name in payload_files(output, origin_request=origin_request)}
    require(sum(row["bytes"] for row in payloads.values()) <= 2 * 1024**3, "proposed payload exceeds its byte ceiling")
    check_prior_attempt()
    return {"schema": APPROVAL_SCHEMA, "profile": PROFILE, "run_id": RUN_ID,
            "approved": False, "approval_reference": None, "source_commit": source_commit,
            "source_files": execution_sources(), "origin_request_sha256": hashlib.sha256(read(origin_request)).hexdigest(),
            "ready_bundle_sha256": ready_sha, "reservations": RESERVATIONS,
            "maximum_aggregate_gpu_seconds": 7200, "maximum_concurrent_gpus": 1,
            "automatic_retry": False, "payloads": payloads, "payloads_sha256": digest(payloads),
            "prior_attempt": dict(PRIOR_ATTEMPT)}


def check_prior_attempt():
    """Authenticate the zero-GPU predecessor without adopting or editing it."""
    raw = read(project_path(PRIOR_ATTEMPT["ledger"]), 65536)
    require(hashlib.sha256(raw).hexdigest() == PRIOR_ATTEMPT["ledger_sha256"],
            "prior attempt ledger changed; unused GPU scope cannot be reset or combined")


def check_execution_commit(expected_commit):
    """Clean local Git or the exact remote sync provenance, not a fallback."""
    if (ROOT / ".git").exists():
        from training.peano_hydra.review_sources import bounded_git
        def git(*arguments):
            return bounded_git(ROOT, *arguments, maximum=1024**2)
        require(git("rev-parse", "HEAD").decode().strip() == expected_commit
                and git("status", "--porcelain", "--untracked-files=no") == b"",
                "approval is not bound to this clean local source commit")
        names = tuple(execution_sources())
        tracked = git("ls-files", "--error-unmatch", "--", *names).decode().splitlines()
        require(set(tracked) == set(names), "approved execution contains an uncommitted source file")
    else:
        provenance = read(ROOT / ".peano-source-provenance.tsv", 1024)
        expected = re.fullmatch(rb"([0-9a-f]{40})\tfalse\t([0-9TZ:+-]+)\n", provenance)
        require(expected is not None and expected.group(1).decode() == expected_commit,
                "approval is not bound to this clean staged source")


def check_approval(path, *, origin_request, output, stage_name, run_id=RUN_ID, require_job=False):
    require(stage_name in JOBS and run_id == RUN_ID and relative(output) == BUNDLE,
            "approval is for one fixed corrective experiment and stage")
    raw = read(path)
    approval = decode(raw)
    require(set(approval) == APPROVAL_FIELDS and approval.get("schema") == APPROVAL_SCHEMA and approval.get("approved") is True,
            "fresh explicit user approval is required; a proposal does not authorize compute")
    require(canonical(approval.get("prior_attempt")) == canonical(PRIOR_ATTEMPT),
            "approval changed its immutable prior attempt or zero-GPU boundary")
    check_prior_attempt()
    require(approval.get("profile") == PROFILE and approval.get("run_id") == RUN_ID
            and canonical(approval.get("reservations")) == canonical(RESERVATIONS)
            and type(approval.get("maximum_aggregate_gpu_seconds")) is int
            and approval["maximum_aggregate_gpu_seconds"] == 7200
            and approval.get("automatic_retry") is False and type(approval.get("maximum_concurrent_gpus")) is int
            and approval["maximum_concurrent_gpus"] == 1
            and type(approval.get("approval_reference")) is str and 0 < len(approval["approval_reference"]) <= 2048,
            "approval changed its exact reservation, scope or human reference")
    require(type(approval.get("source_commit")) is str and _COMMIT.fullmatch(approval["source_commit"]),
            "approval requires a frozen execution commit")
    check_execution_commit(approval["source_commit"])
    if require_job or os.environ.get("SLURM_JOB_ID") is not None:
        require(re.fullmatch(r"[0-9]+", os.environ.get("SLURM_JOB_ID", "")) is not None
                and os.environ.get("PEANO_HYDRA_PROFILE") == PROFILE
                and os.environ.get("PEANO_JOB_SCRIPT") == JOBS[stage_name],
                "approval stage differs from the actual declared scheduler job")
    require(approval.get("source_files") == execution_sources(), "approved execution files changed")
    require(hashlib.sha256(read(origin_request)).hexdigest() == approval.get("origin_request_sha256"),
            "approved original-source package changed")
    require(hashlib.sha256(read(output / "readiness.json")).hexdigest() == approval.get("ready_bundle_sha256"),
            "approved readiness bytes changed")
    payloads = approval.get("payloads")
    require(type(payloads) is dict and 1 <= len(payloads) <= MAX_PAYLOAD_FILES
            and approval.get("payloads_sha256") == digest(payloads), "approval lacks its complete staged payload inventory")
    require(set(payloads) == set(payload_files(output, origin_request=origin_request)),
            "approval omitted or added a staged source, origin, model or readiness payload")
    total = 0
    for name, expected_file in payloads.items():
        actual = file_record(project_path(name))
        require(actual == expected_file, "approved payload bytes changed: " + name)
        total += actual["bytes"]
        require(total <= 2 * 1024**3, "approved input package exceeds its byte ceiling")
    # The raw readiness hash is the external anchor for cached old-origin
    # receipts. Reading a caller-resealed readiness alone is never sufficient.
    load_bundle(output, origin_request=origin_request, expected_readiness_sha256=approval["ready_bundle_sha256"])
    check_prior_attempt()
    require(read(path) == raw, "approval changed during its check")
    if require_job or os.environ.get("SLURM_JOB_ID") is not None:
        from training.peano_hydra.corrective_launch import check_job_reservation
        check_job_reservation(stage_name, hashlib.sha256(raw).hexdigest())
    return approval


__all__ = ["specification", "prepare_bundle", "verify_bundle", "load_bundle", "load_origin_requests", "check_approval"]
