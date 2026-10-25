"""One local five-stage Hydra preparation workflow; never a GPU launcher.

Candidate proofs, declared lineage review, sharded bytes, matched experiments
and TRAIN-only harvesting share exact hashes. A source candidate is not an
admitted training preparation, a lineage proposal is not human review, and a
development diagnostic is not a sealed final benchmark.
"""

from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
import os
from pathlib import Path
import resource
import stat
import subprocess
import sys
import uuid

from hydra_training_v5.peano_hydra import scaling_experiment as experiment
from hydra_training_v5.peano_hydra import scaling_lineage as lineage
from hydra_training_v5.peano_hydra import scaling_shards as shards
from hydra_training_v5.peano_hydra import corrective_workflow as fileio
from hydra_training_v5.peano_hydra.review_runtime import ProcessLimits, run_bounded, validate_process_record


ROOT = Path(__file__).absolute().parents[2]
SCRIPT = ROOT / "scripts/prepare_peano_hydra_scaling.py"
WORKER_SCHEMA = "peano-hydra-frontier-cpu-stage-v1"
BUNDLE_SCHEMA = "peano-hydra-frontier-candidate-bundle-v1"
ADMISSION_SCHEMA = "peano-hydra-frontier-model-data-admission-v1"
ADMISSION_WORKER_SCHEMA = "peano-hydra-frontier-admission-cpu-stage-v1"
BASELINE_MANIFEST_SHA256 = "172a6928710192c5348dcd7b04f71e6d4d3f75dfa1ab0f7f5add601769704a7c"
NATIVE_LIMITS = ProcessLimits(cpu_seconds=120, wall_seconds=180,
                              rss_bytes=2 * 1024**3, output_bytes=8 * 1024**2)
MAX_METADATA_BYTES = 16 * 1024**2
MAX_SOURCE_BYTES = 64 * 1024**2
MAX_ROW_BYTES = 256 * 1024
MAX_ROWS = 16_384
_BUNDLE_FILES = frozenset((
    "native-summary.json", "source-build-process.json", "source-verify-process.json",
    "lineage-proposal.json", "lineage-audit.json", "shard-structural-check.json",
    "pilot-plan.json", "evaluation-plan.json", "review-request.json",
))
_FALSE_CLAIMS = (
    "independent_process_per_route", "human_review_passed", "reference_readiness_passed",
    "training_preparation_created", "token_preflight_passed", "model_trained",
    "training_authorized", "transfer_authorized", "sealed_benchmark", "research_claim_eligible",
)
require = experiment.require
digest = experiment.digest
sha = experiment.sha


class NativeStageError(ValueError):
    """Retain a failed owned process as evidence, never as a proof result."""

    def __init__(self, message, process):
        self.process = process
        detail = " ".join(str(process.get("stderr", "")).split())[:2000]
        super().__init__(message + ": " + str(process.get("reason"))
                         + " (exit " + str(process.get("returncode")) + ")"
                         + ("; " + detail if detail else ""))


def canonical(value):
    try:
        raw = json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False,
                         separators=(",", ":")).encode()
    except (ValueError, TypeError, RecursionError, UnicodeError) as error:
        raise ValueError("invalid frontier workflow JSON") from error
    require(len(raw) <= MAX_METADATA_BYTES, "workflow metadata exceeds its byte bound")
    return raw


def decode(raw):
    require(type(raw) is bytes and 0 < len(raw) <= MAX_METADATA_BYTES, "unbounded workflow JSON")
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "duplicate workflow JSON key")
            result[key] = value
        return result
    def constant(_):
        raise ValueError("nonfinite workflow JSON")
    result = json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)
    require(type(result) is dict, "workflow JSON must be an object")
    canonical(result)
    return result


def read_json(path, expected_raw_sha256=None):
    raw = fileio.read(Path(path), maximum=MAX_METADATA_BYTES)
    if expected_raw_sha256 is not None:
        sha(expected_raw_sha256, "external raw metadata SHA")
        require(hashlib.sha256(raw).hexdigest() == expected_raw_sha256, "external raw metadata hash differs")
    return decode(raw), hashlib.sha256(raw).hexdigest()


def _protected():
    paths = tuple(ROOT / name for name in (
        "training", "scripts", "slurm", "docs", "book", "peano-lab",
        "artifacts/peano-library",
    ))
    git = ROOT / ".git"
    # In a linked worktree .git is a regular pointer file, not a directory.
    # The fresh-output check already forbids replacing it. A directory (or
    # unsafe link) must still pass the directory/ancestor protection below.
    if not git.exists() or git.is_symlink() or not stat.S_ISREG(git.lstat().st_mode):
        paths += (git,)
    return paths


def write_json(path, value):
    """Commit one bounded fresh JSON file, with no replacement or alias."""
    path = fileio.guard_output(Path(path), protected=_protected())
    raw = canonical(value) + b"\n"
    parent = fileio.directory(path.parent)
    temporary = ".frontier-partial-" + uuid.uuid4().hex
    try:
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                     0o600, dir_fd=parent)
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path.name, src_dir_fd=parent, dst_dir_fd=parent, follow_symlinks=False)
        os.unlink(temporary, dir_fd=parent)
        os.fsync(parent)
    finally:
        os.close(parent)
    return hashlib.sha256(raw).hexdigest()


def _fresh_directory(path, *, protected=()):
    path = fileio.guard_output(Path(path), protected=(*_protected(), *protected))
    parent = fileio.directory(path.parent)
    try:
        os.mkdir(path.name, mode=0o700, dir_fd=parent)
        os.fsync(parent)
    finally:
        os.close(parent)
    return path


def source_rows(source_directory, *, expected_manifest_sha256):
    """Stream exact historically/candidate-pinned SFT bytes, not native proof validation."""
    source_directory = Path(source_directory).absolute()
    manifest, _ = read_json(source_directory / "manifest.json", expected_manifest_sha256)
    require(type(manifest.get("files")) is dict and "sft.jsonl" in manifest["files"],
            "source lost its positive row inventory")
    identity = manifest["files"]["sft.jsonl"]
    require(type(identity) is dict and type(identity.get("bytes")) is int
            and 0 < identity["bytes"] <= MAX_SOURCE_BYTES, "source SFT byte bound differs")
    sha(identity.get("sha256"), "source SFT SHA")
    fd = fileio.directory(source_directory)
    count, total, content_hash = 0, 0, hashlib.sha256()
    try:
        descriptor = os.open("sft.jsonl", os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
        with os.fdopen(descriptor, "rb") as stream:
            before = os.fstat(stream.fileno())
            require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1
                    and before.st_size == identity["bytes"], "source SFT is not one pinned regular file")
            while True:
                raw = stream.readline(MAX_ROW_BYTES + 1)
                if not raw:
                    break
                count += 1
                total += len(raw)
                require(count <= MAX_ROWS and len(raw) <= MAX_ROW_BYTES and raw.endswith(b"\n")
                        and total <= identity["bytes"], "source row framing/count/bytes exceeds bound")
                content_hash.update(raw)
                yield decode(raw)
            after = os.fstat(stream.fileno())
        signature = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns, s.st_nlink)
        require(signature(before) == signature(after) == signature(os.stat("sft.jsonl", dir_fd=fd, follow_symlinks=False))
                and total == identity["bytes"] and content_hash.hexdigest() == identity["sha256"],
                "streamed source bytes changed from their manifest")
        require(read_json(source_directory / "manifest.json")[1] == expected_manifest_sha256,
                "source manifest changed during streaming")
    finally:
        os.close(fd)


def _envelopes(source_directory, source_sha):
    # The native source remains complete and unchanged. Repeated identical
    # state/action identities within one lineage are removed only in this
    # candidate training projection, with before/after counts reported.
    seen = set()
    for row in source_rows(source_directory, expected_manifest_sha256=source_sha):
        identity = digest([row["epoch_sha256"], row["environment_sha256"],
                           row["lineage_sha256"], row["state_sha256"], row["action"]])
        if identity not in seen:
            seen.add(identity)
            yield {"example_id": identity, "split": row["split"],
                   "lineage_sha256": row["lineage_sha256"], "payload": row}


def _source_summary(source):
    from hydra_training_v5.peano_hydra.posttrain import _goal_target
    plan = source.manifest["composition"]["plan"]
    by_name = defaultdict(list)
    for row in source.curriculum.transitions:
        by_name[row["theorem_name"]].append(row)
    records = []
    for route in plan["routes"]:
        statements, states = set(), set()
        for row in by_name[route["name"]]:
            states.add(row["state_sha256"])
            for displayed in (*row["goals_before"], *row["goals_after"]):
                target = _goal_target(displayed)
                if target is not None:
                    statements.add(hashlib.sha256(target.encode()).hexdigest())
        records.append({"route": route, "intermediate_statement_sha256s": sorted(statements),
                        "intermediate_state_sha256s": sorted(states)})
    return {
        "source_manifest_sha256": hashlib.sha256(source.payloads["manifest.json"]).hexdigest(),
        "source_files": {name: {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
                         for name, raw in sorted(source.payloads.items())},
        "epoch_sha256": source.epoch.epoch_sha256,
        "authority_sha256": digest(source.manifest["authority"]),
        "source_plan": plan, "lineage_records": records,
        "raw_split_rows": dict(Counter(row["split"] for row in source.curriculum.transitions)),
        "native_verified_routes": source.manifest["composition"]["verified_route_count"],
        "native_verified_transitions": len(source.curriculum.transitions),
        "recovery_attempts": sum(len(r["recovery_attempts"]) for r in plan["routes"]),
        "model_generation_performed": False, "training_authorized": False,
        "independent_process_per_route": False,
    }


def native_worker(request):
    require(sys.flags.isolated and sys.dont_write_bytecode and sys.pycache_prefix == "/dev/null",
            "frontier CPU worker must use isolated uncached Python")
    require(resource.getrlimit(resource.RLIMIT_CPU) == (120, 121), "frontier CPU worker lacks exact CPU guard")
    require(not {"torch", "transformers", "peft", "tokenizers"} & set(sys.modules),
            "frontier CPU worker cannot load model frameworks")
    experiment.keys(request, {"schema", "mode", "profile", "source", "output",
                               "execution_sources_sha256"}, "frontier worker request")
    require(request["schema"] == WORKER_SCHEMA and request["mode"] in {"plan", "build", "verify"},
            "unsupported frontier native stage")
    require(request["profile"] in {"smoke", "pilot"}, "unknown frontier profile")
    current = experiment.execution_source_inventory()
    require(digest(current) == request["execution_sources_sha256"], "native execution source changed")
    from hydra_training_v5.peano_hydra import frontier_curriculum as frontier
    from hydra_training_v5.peano_hydra.epoch import freeze_epoch
    if request["mode"] == "plan":
        require(request["source"] is None and request["output"] is None, "plan cannot write/read a source")
        result = {"source_plan": frontier.frontier_plan(freeze_epoch(ROOT), profile=request["profile"]),
                  "native_proofs_checked": 0, "model_generation_performed": False}
    elif request["mode"] == "build":
        require(request["source"] is None and type(request["output"]) is str, "invalid native build destination")
        destination = fileio.guard_output(Path(request["output"]), protected=_protected())
        source = frontier.build_frontier_source(freeze_epoch(ROOT), profile=request["profile"])
        frontier.publish_frontier_source(source, destination)
        result = _source_summary(source)
    else:
        require(request["output"] is None and type(request["source"]) is str, "invalid source verification input")
        source = frontier.verify_frontier_source(Path(request["source"]))
        require(source.manifest["curriculum_profile"] == request["profile"], "verified source changed profile")
        result = _source_summary(source)
    require(digest(experiment.execution_source_inventory()) == request["execution_sources_sha256"],
            "execution source changed during native stage")
    require(not {"torch", "transformers", "peft", "tokenizers"} & set(sys.modules), "CPU stage imported a model")
    return {"schema": WORKER_SCHEMA, "mode": request["mode"],
            "request_sha256": digest(request), "result": result}


def native_stage(mode, *, profile, source=None, output=None):
    request = {"schema": WORKER_SCHEMA, "mode": mode, "profile": profile,
               "source": None if source is None else str(Path(source).absolute()),
               "output": None if output is None else str(Path(output).absolute()),
               "execution_sources_sha256": digest(experiment.execution_source_inventory())}
    command = (sys.executable, "-I", "-B", "-X", "pycache_prefix=/dev/null", str(SCRIPT), "--native-worker")
    raw = canonical(request)
    process = run_bounded(command, cwd=ROOT, limits=NATIVE_LIMITS, input_bytes=raw)
    try:
        validate_process_record(process, command=command, limits=NATIVE_LIMITS, input_bytes=raw, success_codes=(0,))
    except ValueError as error:
        raise NativeStageError("native " + mode + " stage did not complete", process) from error
    response = decode(process["stdout"].encode())
    require(response.get("schema") == WORKER_SCHEMA and response.get("mode") == mode
            and response.get("request_sha256") == digest(request), "native response lost request binding")
    require(digest(experiment.execution_source_inventory()) == request["execution_sources_sha256"],
            "source changed after native stage")
    audit = {k: v for k, v in process.items() if k not in {"stdout", "stderr", "raw_output_base64"}}
    return response["result"], audit


def admission_worker(request):
    """One owned CPU stage; the review itself must already exist externally."""
    require(sys.flags.isolated and sys.dont_write_bytecode and sys.pycache_prefix == "/dev/null",
            "admission worker must use isolated uncached Python")
    require(resource.getrlimit(resource.RLIMIT_CPU) == (120, 121), "admission worker lacks exact CPU guard")
    experiment.keys(request, {"schema", "candidate_bundle", "expected_readiness_sha256",
        "review_file", "expected_review_sha256", "output_directory", "run_id",
        "execution_sources_sha256"}, "admission worker request")
    require(request["schema"] == ADMISSION_WORKER_SCHEMA, "unsupported admission worker schema")
    require(digest(experiment.execution_source_inventory()) == request["execution_sources_sha256"],
            "admission execution source changed")
    require(not {"torch", "transformers", "peft", "tokenizers"} & set(sys.modules),
            "admission worker cannot load model frameworks")
    from hydra_training_v5.peano_hydra.scaling_admission import prepare_admitted_pilot
    result = prepare_admitted_pilot(**{key: value for key, value in request.items()
        if key not in {"schema", "execution_sources_sha256"}})
    require(digest(experiment.execution_source_inventory()) == request["execution_sources_sha256"],
            "admission execution source changed during preparation")
    require(not {"torch", "transformers", "peft", "tokenizers"} & set(sys.modules),
            "admission worker imported model frameworks")
    return {"schema": ADMISSION_WORKER_SCHEMA, "request_sha256": digest(request), "result": result}


def prepare_pilot(candidate_bundle, *, expected_readiness_sha256, review_file,
                  expected_review_sha256, output_directory, run_id):
    """Prepare reviewed data under the fixed CPU envelope, never start a GPU."""
    candidate_bundle, review_file, output_directory = (
        Path(value).absolute() for value in (candidate_bundle, review_file, output_directory))
    fileio.guard_output(output_directory, protected=(*_protected(), candidate_bundle))
    read_json(candidate_bundle / "readiness.json", expected_readiness_sha256)
    sha(expected_review_sha256, "external canonical human review SHA")
    read_json(review_file)
    request = {"schema": ADMISSION_WORKER_SCHEMA, "candidate_bundle": str(candidate_bundle),
        "expected_readiness_sha256": expected_readiness_sha256, "review_file": str(review_file),
        "expected_review_sha256": expected_review_sha256, "output_directory": str(output_directory),
        "run_id": run_id, "execution_sources_sha256": digest(experiment.execution_source_inventory())}
    command = (sys.executable, "-I", "-B", "-X", "pycache_prefix=/dev/null", str(SCRIPT), "--admission-worker")
    raw = canonical(request)
    process = run_bounded(command, cwd=ROOT, limits=NATIVE_LIMITS, input_bytes=raw)
    validate_process_record(process, command=command, limits=NATIVE_LIMITS, input_bytes=raw, success_codes=(0,))
    response = decode(process["stdout"].encode())
    experiment.keys(response, {"schema", "request_sha256", "result"}, "admission worker response")
    require(response["schema"] == ADMISSION_WORKER_SCHEMA and response["request_sha256"] == digest(request),
            "admission response changed its request")
    require(digest(experiment.execution_source_inventory()) == request["execution_sources_sha256"],
            "admission source changed before result publication")
    audit = {key: value for key, value in process.items()
             if key not in {"stdout", "stderr", "raw_output_base64"}}
    write_json(output_directory / "admission-process.json", audit)
    write_json(output_directory / "preparation-result.json", response["result"])
    return response["result"]


def _baseline_exposure(directory, anchor, route_ids):
    """Authenticate declared baseline rows by bytes; do not redo old training."""
    manifest, raw_sha = read_json(Path(directory) / "manifest.json", anchor)
    families, lineages, statements, states = set(), set(), set(), set()
    rows = 0
    for row in source_rows(directory, expected_manifest_sha256=raw_sha):
        rows += 1
        require(row.get("epoch_sha256") == manifest["epoch_sha256"], "baseline source epoch differs")
        families.add(row["family"])
        lineages.add(sha(row["lineage_sha256"], "baseline lineage"))
        statements.add(hashlib.sha256(row["theorem"].encode()).hexdigest())
        require(row["state_sha256"] == digest(row["goals_before"]), "baseline state hash differs")
        states.add(row["state_sha256"])
    file_identity = {"sft.jsonl": {k: manifest["files"]["sft.jsonl"][k] for k in ("bytes", "sha256")},
                     "manifest.json": fileio.file_record(Path(directory) / "manifest.json")}
    exposure = {
        "exposure_id": "saved-corrected-training-source", "manifest_sha256": raw_sha,
        "files": file_identity, "files_sha256": lineage.canonical_sha256(file_identity),
        "row_count": rows, "covered_route_ids": route_ids, "complete": True,
        "families": sorted(families), "template_sha256s": [], "lineage_sha256s": sorted(lineages),
        "statement_sha256s": sorted(statements), "intermediate_statement_sha256s": [],
        "intermediate_state_sha256s": sorted(states),
    }
    return manifest, exposure


def candidate_lineage_inventory(summary, *, baseline_source=None, baseline_source_sha256=None,
                                source_state=None):
    """Join new templates to declared historical parents without inventing novelty."""
    require((baseline_source is None) == (baseline_source_sha256 is None), "baseline source needs its external raw SHA")
    files = experiment.execution_source_inventory()
    plan = summary["source_plan"]
    source_sha = files["training/peano_hydra/frontier_curriculum.py"]["sha256"]
    route_ids = [item["route"]["name"] for item in summary["lineage_records"]]
    old, exposure = None, None
    if baseline_source is not None:
        old, exposure = _baseline_exposure(baseline_source, baseline_source_sha256, route_ids)
    old_families = {} if old is None else {f["id"]: f for f in old["composition"]["plan"]["families"]}
    families = {f["id"]: f for f in plan["families"]}
    parent_refs = sorted({p for f in families.values() for p in f["parent_families"]})
    parents, parent_hashes = [], {}
    for ref in parent_refs:
        prefix, name = ref.split(":", 1)
        historical = old_families.get(name)
        key = historical["lineage_sha256"] if historical is not None else digest({"unresolved_parent": ref})
        parent_hashes[ref] = key
        old_sources = {} if old is None else old["composition"]["plan"]["source_identity"]["files"]
        generator = "training/peano_hydra/" + ("composition_scale.py" if prefix == "scale" else "witness_repair.py")
        parent_source = old_sources.get(generator)
        parents.append({
            "lineage_sha256": key, "source_sha256": parent_source or digest({"unresolved_generator": generator}),
            "epoch_sha256": summary["epoch_sha256"] if old is None else old["epoch_sha256"],
            "authority_sha256": summary["authority_sha256"] if old is None else digest(old["authority"]),
            "parent_lineages": [], "provenance_complete": historical is not None and parent_source is not None,
        })
    records = []
    for item in summary["lineage_records"]:
        route = item["route"]
        records.append({
            "route_id": route["name"], "family": route["family"],
            "template_sha256": digest({"generator_sha256": source_sha, "family": families[route["family"]]}),
            "statement_sha256": route["statement_sha256"], "lineage_sha256": route["lineage_sha256"],
            "parent_lineages": [parent_hashes[p] for p in route["parent_families"]],
            "dependency_ids": [], "equivalent_ids": [],
            "intermediate_statement_sha256s": item["intermediate_statement_sha256s"],
            "intermediate_state_sha256s": item["intermediate_state_sha256s"],
            "source_sha256": source_sha, "epoch_sha256": summary["epoch_sha256"],
            "authority_sha256": summary["authority_sha256"], "seed": route["generator_seed"],
            "provenance_complete": True,
        })
    # No historical source is silently assumed clean when its inventory is absent.
    expected_exposure = baseline_source_sha256 or digest({"missing": "saved-corrected-training-source"})
    excluded = plan["excluded_targets"]
    target_hashes = sorted({hashlib.sha256(row["statement"].encode()).hexdigest() for row in excluded})
    if source_state is None:
        try:
            commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True,
                                    text=True, timeout=2).stdout.strip()
            dirty = bool(subprocess.run(["git", "status", "--porcelain=v1", "--untracked-files=normal"],
                                       cwd=ROOT, check=True, capture_output=True, text=True, timeout=2).stdout)
        except (OSError, subprocess.SubprocessError):
            commit, dirty = None, True
    else:
        # Reverification retains observed publication-time Git metadata while
        # rehashing every execution byte. It does not spawn Git descendants
        # inside a bounded native admission worker or attest current HEAD.
        experiment.keys(source_state, {"source_commit", "source_dirty"}, "recorded source state")
        commit, dirty = source_state["source_commit"], source_state["source_dirty"]
    return {
        "schema": lineage.INVENTORY_SCHEMA, "bounds_profile": "peano-hydra-scaling-lineage-pilot-v1",
        "source_commit": commit, "source_dirty": dirty, "source_files": files,
        "source_files_sha256": lineage.canonical_sha256(files),
        "epoch_sha256": summary["epoch_sha256"], "authority_sha256": summary["authority_sha256"],
        "canonicalization_sha256": files["training/peano_hydra/protocol.py"]["sha256"],
        "records": records, "parents": parents,
        "exposure_requirements": [{"exposure_id": "saved-corrected-training-source", "manifest_sha256": expected_exposure}],
        "exposures": [] if exposure is None else [exposure],
        "exclusions": {"manifest_sha256": digest(excluded), "complete": True,
                       "target_sha256s": target_hashes, "intermediate_state_sha256s": []},
    }


def proposed_allocations(inventory, summary):
    initial = lineage.build_lineage_proposal(inventory)
    splits = {item["route"]["name"]: item["route"]["split"] for item in summary["lineage_records"]}
    result = []
    for component in initial["components"]:
        values = {splits[name] for name in component["route_ids"]}
        split = next(iter(values)) if len(values) == 1 else "quarantine"
        result.append({"component_id": component["component_id"], "split": split, "diagnostic": split == "dev"})
    return result


def specification():
    return {
        "schema": "peano-hydra-five-step-scaling-specification-v1",
        "stages": ["lineage-review", "verified-frontier-curriculum", "matched-1.7b-pilot",
                   "train-only-native-harvesting", "explicit-sharded-scaling"],
        "profiles": ["smoke", "pilot"], "native_worker_limits": NATIVE_LIMITS.to_dict(),
        "pilot_total_row_cap": MAX_ROWS, "pilot_optimizer_update_cap": 2048,
        "scale_store_profile": shards.SCALE_100K_V1.to_dict(),
        "large_lineage_profile": "peano-hydra-scaling-lineage-large-v1",
        "model": {"model_id": experiment.MODEL_ID, "revision": experiment.MODEL_REVISION},
        "training_authorized": False, "transfer_authorized": False, "gpu_jobs_started": 0,
        "research_claim_eligible": False, "historical_source_or_limits_changed": False,
    }


def _evaluation_goals(summary):
    """Fixed balanced spread across declared DEV variants, chosen before inference."""
    dev_families = defaultdict(list)
    for route in summary["source_plan"]["routes"]:
        if route["split"] == "dev":
            dev_families[route["family"]].append(route)
    require(1 <= len(dev_families) <= 32, "candidate needs a bounded DEV family inventory")
    selected = []
    per_family = max(1, 32 // len(dev_families))
    for routes in dev_families.values():
        if len(routes) <= per_family:
            selected.extend(routes)
        elif per_family == 1:
            selected.append(routes[len(routes) // 2])
        else:
            selected.extend(routes[i * (len(routes) - 1) // (per_family - 1)] for i in range(per_family))
    return [{"name": r["name"], "source": r["source"], "statement": r["statement"],
             "statement_sha256": r["statement_sha256"], "lineage_sha256": r["lineage_sha256"]}
            for r in selected]


def build_bundle(output, *, profile="smoke", baseline_source=None, baseline_source_sha256=None):
    """Build and separately replay a fresh public candidate; never approve it."""
    require(profile in {"smoke", "pilot"}, "unknown source profile")
    require((baseline_source is None) == (baseline_source_sha256 is None),
            "baseline source needs its external raw SHA before any work")
    if baseline_source is not None:
        sha(baseline_source_sha256, "external baseline source SHA")
        read_json(Path(baseline_source) / "manifest.json", baseline_source_sha256)
    output = _fresh_directory(output, protected=() if baseline_source is None else (Path(baseline_source),))
    try:
        summary, build_audit = native_stage("build", profile=profile, output=output / "source")
    except NativeStageError as error:
        write_json(output / "source-build-failed-process.json", error.process)
        raise
    write_json(output / "source-build-process.json", build_audit)
    try:
        checked, verify_audit = native_stage("verify", profile=profile, source=output / "source")
    except NativeStageError as error:
        write_json(output / "source-verify-failed-process.json", error.process)
        raise
    write_json(output / "source-verify-process.json", verify_audit)
    require(canonical(summary) == canonical(checked), "separate source replay changed candidate evidence")
    write_json(output / "native-summary.json", summary)
    inventory = candidate_lineage_inventory(summary, baseline_source=baseline_source,
                                           baseline_source_sha256=baseline_source_sha256)
    proposal = lineage.build_lineage_proposal(inventory, proposed_allocations(inventory, summary))
    audit = lineage.audit_lineage(proposal, expected_proposal_sha256=proposal["proposal_sha256"])
    write_json(output / "lineage-proposal.json", proposal)
    write_json(output / "lineage-audit.json", audit)
    binding = shards.StoreBinding("peano-hydra-verified-transition-v1", summary["source_manifest_sha256"],
                                 summary["authority_sha256"], proposal["proposal_sha256"])
    store = shards.publish_store(output / "shards", _envelopes(output / "source", summary["source_manifest_sha256"]),
                                 binding=binding, profile=shards.DEFAULT_PROFILE)
    store_sha = shards.manifest_raw_sha256(store)
    structural = shards.validate_store(output / "shards", binding=binding, profile=shards.DEFAULT_PROFILE,
                                       expected_manifest_sha256=store_sha)
    projected = iter(shards.iter_rows(output / "shards", binding=binding, profile=shards.DEFAULT_PROFILE,
                                      expected_manifest_sha256=store_sha))
    joined = 0
    for expected in _envelopes(output / "source", summary["source_manifest_sha256"]):
        require(next(projected, None) == expected, "sharded candidate differs from independently replayed source rows")
        joined += 1
    require(next(projected, None) is None and joined == store["total_rows"], "sharded projection count differs")
    write_json(output / "shard-structural-check.json", structural)
    counts = {key: store["split_rows"][key] for key in ("train", "dev", "quarantine")}
    pilot = experiment.build_pilot_plan(
        run_id="frontier-" + profile + "-v1", source_manifest_sha256=summary["source_manifest_sha256"],
        shard_manifest_sha256=store_sha, lineage_proposal_sha256=proposal["proposal_sha256"],
        epoch_sha256=summary["epoch_sha256"], authority_sha256=summary["authority_sha256"],
        baseline_adapter_manifest_sha256=BASELINE_MANIFEST_SHA256, split_rows=counts, profile=profile)
    write_json(output / "pilot-plan.json", pilot)
    evaluation = experiment.build_evaluation_plan(
        goals=_evaluation_goals(summary), cohort="review-candidate-dev", epoch_sha256=summary["epoch_sha256"],
        authority_sha256=summary["authority_sha256"], lineage_proposal_sha256=proposal["proposal_sha256"],
        baseline_adapter_manifest_sha256=BASELINE_MANIFEST_SHA256,
        candidate_training_plan_sha256=pilot["plan_sha256"],
        source_files_sha256=experiment.digest(experiment.execution_source_inventory()))
    # This pre-preparation identity is deliberately not a claim that a model
    # handoff or trained candidate adapter already exists.
    write_json(output / "evaluation-plan.json", evaluation)
    review_request = {
        "schema": "peano-hydra-frontier-human-review-request-v1",
        "proposal_sha256": proposal["proposal_sha256"],
        "status": "awaiting-human-lineage-and-reference-review",
        "questions": [
            "Review declared template/parent components and exposure coverage; keep unknowns quarantined.",
            "Supply or independently own genuinely held-out new lineages; these authored candidates are public diagnostics.",
            "Review required semantic/reference evidence before a new-lineage model comparison.",
        ],
        "current_claim": "complete native candidate proofs, not a trustworthy sealed unseen benchmark",
        "human_review_record_created": False, "training_authorized": False, "gpu_execution_authorized": False,
    }
    write_json(output / "review-request.json", review_request)
    names = sorted(_BUNDLE_FILES)
    body = {
        "schema": BUNDLE_SCHEMA, "profile": profile, "status": "candidate-verified-review-pending",
        "source_manifest_sha256": summary["source_manifest_sha256"],
        "shard_manifest_sha256": store_sha, "lineage_proposal_sha256": proposal["proposal_sha256"],
        "files": {name: fileio.file_record(output / name) for name in names},
        "native_verified_routes": summary["native_verified_routes"],
        "native_verified_transitions": summary["native_verified_transitions"],
        "recovery_attempts": summary["recovery_attempts"], "projected_unique_rows": store["total_rows"],
        "duplicate_state_actions_removed": summary["native_verified_transitions"] - store["total_rows"],
        "split_rows": store["split_rows"], "native_source_to_shard_join_checked": True,
        "separate_process_source_reverification": True, "independent_process_per_route": False,
        "lineage_status": proposal["status"], "lineage_counts": proposal["counts"],
        "baseline_exposure_source": None if baseline_source is None else {
            "directory": str(Path(baseline_source).absolute()), "manifest_sha256": baseline_source_sha256},
        "source_files": experiment.execution_source_inventory(),
        "human_review_passed": False, "reference_readiness_passed": False,
        "training_preparation_created": False, "token_preflight_passed": False,
        "model_trained": False, "training_authorized": False, "transfer_authorized": False,
        "gpu_jobs_started": 0, "sealed_benchmark": False, "research_claim_eligible": False,
    }
    body["bundle_sha256"] = hashlib.sha256(canonical(body)).hexdigest()
    raw_sha = write_json(output / "readiness.json", body)
    return {"readiness": body, "readiness_raw_sha256": raw_sha, "output": str(output)}


def _check_bundle_metadata(directory, *, expected_readiness_sha256):
    """Recheck every source/projection/plan link without claiming native replay."""
    directory = Path(directory).absolute()
    ready, raw_sha = read_json(directory / "readiness.json", expected_readiness_sha256)
    expected_fields = {
        "schema", "profile", "status", "source_manifest_sha256", "shard_manifest_sha256",
        "lineage_proposal_sha256", "files", "native_verified_routes", "native_verified_transitions",
        "recovery_attempts", "projected_unique_rows", "duplicate_state_actions_removed", "split_rows",
        "native_source_to_shard_join_checked", "separate_process_source_reverification", "lineage_status",
        "lineage_counts", "baseline_exposure_source", "source_files", "gpu_jobs_started", "bundle_sha256",
        *_FALSE_CLAIMS,
    }
    experiment.keys(ready, expected_fields, "candidate readiness")
    require(ready["schema"] == BUNDLE_SCHEMA and ready["profile"] in {"smoke", "pilot"}
            and ready["status"] == "candidate-verified-review-pending"
            and ready["native_source_to_shard_join_checked"] is True
            and ready["separate_process_source_reverification"] is True
            and all(ready[key] is False for key in _FALSE_CLAIMS)
            and type(ready["gpu_jobs_started"]) is int and ready["gpu_jobs_started"] == 0
            and ready.get("bundle_sha256") == hashlib.sha256(canonical(
                {k: v for k, v in ready.items() if k != "bundle_sha256"})).hexdigest(),
            "candidate bundle changed its digest, counts or claim boundary")
    require(type(ready["files"]) is dict and set(ready["files"]) == _BUNDLE_FILES,
            "candidate bundle lost its exact metadata file inventory")
    expected_top = _BUNDLE_FILES | {"source", "shards", "readiness.json"}
    names = set()
    with os.scandir(directory) as entries:
        for entry in entries:
            require(entry.name in expected_top and not entry.is_symlink(), "extra/aliased candidate bundle entry")
            names.add(entry.name)
    require(names == expected_top, "candidate bundle inventory is incomplete")
    for field, maximum in (("native_verified_routes", 1152), ("native_verified_transitions", MAX_ROWS),
                           ("recovery_attempts", 1152), ("projected_unique_rows", MAX_ROWS),
                           ("duplicate_state_actions_removed", MAX_ROWS)):
        experiment.integer(ready[field], field, 0, maximum)
    require(ready["source_files"] == experiment.execution_source_inventory(), "candidate execution source changed")
    for name, identity in ready["files"].items():
        require(fileio.file_record(directory / name) == identity, "candidate bundle file changed")
    summary, _ = read_json(directory / "native-summary.json")
    require(type(summary.get("source_files")) is dict
            and set(summary["source_files"]) == {"epoch.json", "sft.jsonl", "preferences.jsonl", "discovery.jsonl", "manifest.json"},
            "native source summary lost exact file inventory")
    for name, identity in summary["source_files"].items():
        require(name in {"epoch.json", "sft.jsonl", "preferences.jsonl", "discovery.jsonl", "manifest.json"}
                and fileio.file_record(directory / "source" / name) == identity,
                "native source payload differs from the checked summary")
    source_names = set()
    with os.scandir(directory / "source") as entries:
        for entry in entries:
            require(entry.name in summary["source_files"] and not entry.is_symlink(),
                    "extra/aliased native source entry")
            source_names.add(entry.name)
    require(source_names == set(summary["source_files"]), "native source inventory differs")
    require(summary["source_manifest_sha256"] == ready["source_manifest_sha256"],
            "readiness changed source manifest identity")
    proposal, _ = read_json(directory / "lineage-proposal.json")
    audit = lineage.audit_lineage(proposal, expected_proposal_sha256=ready["lineage_proposal_sha256"])
    saved_audit, _ = read_json(directory / "lineage-audit.json")
    require(canonical(audit) == canonical(saved_audit), "saved lineage audit differs")
    exposure = ready["baseline_exposure_source"]
    if exposure is not None:
        experiment.keys(exposure, {"directory", "manifest_sha256"}, "baseline exposure input")
    inventory = candidate_lineage_inventory(summary,
        baseline_source=None if exposure is None else Path(exposure["directory"]),
        baseline_source_sha256=None if exposure is None else exposure["manifest_sha256"],
        source_state={k: proposal["inventory"][k] for k in ("source_commit", "source_dirty")})
    # The lineage builder normalizes record/parent order. Compare its complete
    # regenerated proposal below, not the pre-normalization route sequence.
    expected_proposal = lineage.build_lineage_proposal(inventory, proposed_allocations(inventory, summary))
    require(lineage.canonical_bytes(expected_proposal) == lineage.canonical_bytes(proposal),
            "candidate proposal changed its declared whole-component allocation")
    require(ready["lineage_counts"] == proposal["counts"] and ready["lineage_status"] == proposal["status"],
            "candidate lineage summary differs")
    binding = shards.StoreBinding("peano-hydra-verified-transition-v1", ready["source_manifest_sha256"],
                                 summary["authority_sha256"], ready["lineage_proposal_sha256"])
    structural = shards.validate_store(directory / "shards", binding=binding, profile=shards.DEFAULT_PROFILE,
                                       expected_manifest_sha256=ready["shard_manifest_sha256"])
    saved_structural, _ = read_json(directory / "shard-structural-check.json")
    require(canonical(structural) == canonical(saved_structural), "shard structural receipt differs")
    manifest, _ = read_json(directory / "shards" / "manifest.json", ready["shard_manifest_sha256"])
    projected = iter(shards.iter_rows(directory / "shards", binding=binding, profile=shards.DEFAULT_PROFILE,
                                      expected_manifest_sha256=ready["shard_manifest_sha256"]))
    joined = 0
    for expected in _envelopes(directory / "source", ready["source_manifest_sha256"]):
        require(next(projected, None) == expected, "shard row differs from exact native source projection")
        joined += 1
    require(next(projected, None) is None and joined == manifest["total_rows"] == ready["projected_unique_rows"],
            "source/shard projection inventory differs")
    require(ready["split_rows"] == manifest["split_rows"]
            and ready["native_verified_routes"] == summary["native_verified_routes"]
            and ready["native_verified_transitions"] == summary["native_verified_transitions"]
            and ready["recovery_attempts"] == summary["recovery_attempts"]
            and ready["duplicate_state_actions_removed"] == summary["native_verified_transitions"] - joined,
            "candidate proof/projection counts differ")
    pilot, _ = read_json(directory / "pilot-plan.json")
    evaluation, _ = read_json(directory / "evaluation-plan.json")
    experiment.validate_pilot_plan(pilot)
    experiment.validate_evaluation_plan(evaluation)
    for field in ("source_manifest_sha256", "shard_manifest_sha256", "lineage_proposal_sha256"):
        require(pilot[field] == ready[field], "pilot plan changed its candidate input binding")
    require(pilot["profile"] == ready["profile"] and pilot["epoch_sha256"] == summary["epoch_sha256"]
            and pilot["authority_sha256"] == summary["authority_sha256"]
            and pilot["split_rows"] == {k: manifest["split_rows"][k] for k in ("train", "dev", "quarantine")}
            and pilot["baseline_adapter_manifest_sha256"] == BASELINE_MANIFEST_SHA256,
            "pilot plan changed its native counts/epoch/authority/baseline")
    require(evaluation["candidate_training_plan_sha256"] == pilot["plan_sha256"]
            and evaluation["lineage_proposal_sha256"] == ready["lineage_proposal_sha256"]
            and evaluation["epoch_sha256"] == summary["epoch_sha256"]
            and evaluation["authority_sha256"] == summary["authority_sha256"]
            and evaluation["source_files_sha256"] == digest(ready["source_files"])
            and evaluation["baseline_adapter_manifest_sha256"] == BASELINE_MANIFEST_SHA256,
            "evaluation plan changed its candidate input binding")
    require(evaluation["cohort"] == "review-candidate-dev"
            and evaluation["goals"] == _evaluation_goals(summary),
            "evaluation changed its exact predeclared balanced DEV selection")
    require(read_json(directory / "readiness.json")[1] == raw_sha, "bundle changed during metadata verification")
    return ready, summary


def verify_bundle(directory, *, expected_readiness_sha256, replay=True):
    require(type(replay) is bool, "native replay choice must be explicit boolean")
    directory = Path(directory).absolute()
    ready, summary = _check_bundle_metadata(directory, expected_readiness_sha256=expected_readiness_sha256)
    audit = None
    if replay:
        checked, audit = native_stage("verify", profile=ready["profile"], source=directory / "source")
        require(canonical(summary) == canonical(checked), "fresh original-goal source replay differs")
    after, after_summary = _check_bundle_metadata(directory, expected_readiness_sha256=expected_readiness_sha256)
    require(canonical(ready) == canonical(after) and canonical(summary) == canonical(after_summary),
            "candidate inputs changed during verification")
    return {"schema": "peano-hydra-frontier-candidate-bundle-verification-v1",
            "status": "passed" if replay else "metadata-checked-native-replay-not-performed",
            "readiness_raw_sha256": expected_readiness_sha256, "native_replay_performed": replay,
            "native_process": audit, "training_authorized": False, "research_claim_eligible": False}


def authenticate_harvest_parent(directory, *, parent_readiness_sha256, review,
                                review_sha256, round_plan):
    """Authenticate actual TRAIN membership and reserved targets, not caller labels."""
    directory = Path(directory).absolute()
    # Full native verification is CPU-only and bounded. A candidate's asserted
    # dataset hash, split flag or empty exclusion list is never sufficient.
    verify_bundle(directory, expected_readiness_sha256=parent_readiness_sha256, replay=True)
    ready, _ = read_json(directory / "readiness.json", parent_readiness_sha256)
    summary, _ = read_json(directory / "native-summary.json")
    proposal, _ = read_json(directory / "lineage-proposal.json")
    checked_review = lineage.validate_review_record(
        review, proposal=proposal, expected_proposal_sha256=ready["lineage_proposal_sha256"],
        expected_review_sha256=review_sha256, required_scope=proposal["allocations"])
    require(checked_review["decision"] == "accept", "self-training requires accepted component review")
    require(round_plan["parent_dataset_sha256"] == ready["shard_manifest_sha256"]
            and round_plan["lineage_proposal_sha256"] == ready["lineage_proposal_sha256"]
            and round_plan["epoch_sha256"] == summary["epoch_sha256"]
            and round_plan["authority_sha256"] == summary["authority_sha256"],
            "self-training plan is not bound to this authenticated parent")
    routes = {r["name"]: r for r in summary["source_plan"]["routes"]}
    components = {name: component for component in proposal["components"] for name in component["route_ids"]}
    allocation = {a["component_id"]: a for a in checked_review["scope"]}
    eligible = set()
    for name, route in routes.items():
        component = components[name]
        selected = allocation.get(component["component_id"])
        if selected is not None and selected["split"] == "train" and route["split"] == "train":
            eligible.add(name)
    require(eligible, "no reviewed TRAIN targets available for harvesting")
    for registered in round_plan["goals"]:
        name = registered["goal_id"]
        require(name in eligible, "self-training goal is not in the authenticated reviewed TRAIN partition")
        route = routes[name]
        expected = {
            "goal_id": name, "source": route["source"], "statement": route["statement"],
            "statement_sha256": route["statement_sha256"], "family": route["family"],
            "lineage_sha256": route["lineage_sha256"], "split": "train",
        }
        require(canonical(registered) == canonical(expected), "registered TRAIN goal changed original source/provenance")
    excluded_targets = set(proposal["inventory"]["exclusions"]["target_sha256s"])
    excluded_lineages = set()
    for name, route in routes.items():
        if name not in eligible:
            excluded_targets.add(route["statement_sha256"])
            excluded_lineages.add(route["lineage_sha256"])
    # The native generator's 96+4 exact comparison exclusions are mandatory,
    # regardless of what the caller's round plan says.
    excluded_targets.update(hashlib.sha256(row["statement"].encode()).hexdigest()
                            for row in summary["source_plan"]["excluded_targets"])
    require(round_plan["excluded_statement_sha256s"] == sorted(excluded_targets)
            and round_plan["excluded_lineage_sha256s"] == sorted(excluded_lineages),
            "self-training omitted or changed authenticated held-out/intermediate exclusions")
    require(read_json(directory / "readiness.json")[1] == parent_readiness_sha256,
            "parent changed during self-training admission")
    return {"parent_readiness_raw_sha256": parent_readiness_sha256,
            "lineage_review_sha256": review_sha256, "training_authorized": False}
