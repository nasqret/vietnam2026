"""One-shot paired-search EVALUATION gate; login Python 3.6, stdlib only.

This is deliberately separate from every historical training/recovery ledger.
Metadata admission authenticates externally approved bytes before allocation;
the source-pinned evaluator repeats its full semantic checks before inference.
``expected_plan_sha256`` always means the RAW plan-file SHA, not plan_sha256.
No function here imports Hydra, a native kernel, a tokenizer, or an ML package.
"""

import argparse
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import selectors
import signal
import stat
import subprocess
import sys
import time


ROOT = Path(__file__).absolute().parents[2]
PROFILE = "peano-hydra-search-v2"
RUN_ID = "search-v2"
PACKAGE = "_deploy/hydra-search-v2"
PLAN = PACKAGE + "/plan.json"
ORIGIN = PACKAGE + "/origin/manifest.json"
APPROVAL = PACKAGE + "/approval.json"
SOURCE_ROOT = PACKAGE + "/origin-source"
ADAPTER_MANIFEST = PACKAGE + "/model/manifest.json"
LOCATIONS = {"source_root": SOURCE_ROOT, "adapter_manifest": ADAPTER_MANIFEST}
LEDGER = "logs/hydra-search-v2.jsonl"
LOCK = "logs/.hydra-search-v2.lock"
SUBMISSIONS = "logs/submissions.tsv"
SUBMISSION_HEADER = "timestamp\tjob_id\tscript\tdependency_job_id\tworkdir\tgit_commit\tgit_dirty\tsync_timestamp\tscript_sha256\n"
JOB = "slurm/peano_hydra_search_evaluate.sbatch"
JOB_NAME = "peano-hydra-search-v2-evaluate"
REMOTE_PARENT = "codex-control/projects/peano-lab-training"
REMOTE_CHILD = "experiments/search-v2"
ACCOUNT = "plgccaiautore2026-gpu-gh200"
PARTITION = "plgrid-gpu-gh200"
CONFIRM = "PEANO-HYDRA-EVALUATION"
SCHEMA = "peano-hydra-search-evaluation-ledger-v1"
APPROVAL_SCHEMA = "peano-hydra-search-evaluation-approval-v1"
PLAN_SCHEMA = "peano-hydra-paired-search-primary32-plan-v1"
RESERVATION = {"seconds": 1800, "gpus": 1, "cpus": 8, "memory_gib": 64}
RUNTIME_DEPENDENCIES = {
    "project": REMOTE_PARENT, "python": ".venv-helios/bin/python",
    "hf_home": ".cache/huggingface", "module": "ML-bundle/25.10",
    "python_version": "3.13.5", "machine": "aarch64",
    "requirements_sha256": "50315d5465ec6081517e1e3bb93096c3a990907020978a490295cde59a6c7871",
    "offline": True, "read_only": True, "install": False,
}
PINS = {
    "source_commit": "5a197363745c61156ce86d64a880fd47b5cb90e3",
    "preparation_relative_path": "_deploy/hydra-corrective-v2/preparation",
    "preparation_manifest_sha256": "b8e73c7063ce962bb1542c903ae8b441c69d254b2933548d8e89795cf25ca114",
    "adapter_manifest_sha256": "172a6928710192c5348dcd7b04f71e6d4d3f75dfa1ab0f7f5add601769704a7c",
    "epoch_sha256": "a96223a021edc556ed7620a87b4c00e5817ba169af4a1db093fa7a81847e082e",
    "authority_profile": "peano-authority-primitive-v1",
    "run_id": "corrective-v2",
    "model": {"model_id": "Qwen/Qwen3-1.7B-Base", "revision": "ea980cb0a6c2ae4b936e82123acc929f1cec04c1"},
    "artifact_sha256": {"adapter": "4ad0af7b07078a4812ac627b71941d4acec0f4fa9c8fe74723b6606ec2c27310",
                        "tokenizer": "2c5206dc7dda009d1a466348530a56c21f68d68057115142b2cd121838cf3f5e"},
}
MATCHED_BUDGET = {"max_depth": 16, "beam_width": 4, "candidates_per_state": 4,
    "max_model_calls": 8, "max_states": 64, "goal_count": 32,
    "max_model_calls_per_lane": 256, "max_new_tokens": 64, "seed": 20260826,
    "sampling": "deterministic batched candidate beam search"}
GOAL_SET_SHA256 = "e275a2ece955082c47f1dc1c74d93d3de43422fb0b7163b84c8d7bca54d3c88a"
REQUIRED_SOURCES = frozenset((
    "training/peano_hydra/search_launch.py", "scripts/helios_hydra_search.sh", JOB,
    "scripts/eval_peano_hydra_search.py", "training/peano_hydra/search_comparison.py",
    "training/peano_hydra/search_origin.py", "training/peano_hydra/paired_checkpoint.py",
    "training/peano_policy/search.py", "training/peano_policy/state_identity.py",
    "training/peano_hydra/runner.py", "training/peano_hydra/helios_runtime.py",
    "scripts/submit_slurm_job.sh", "scripts/helios_submit_job.sh",
    "training/peano_policy/requirements-helios.lock",
))
APPROVAL_FIELDS = frozenset((
    "schema", "profile", "run_id", "approved", "approval_reference", "source_commit", "source_files",
    "plan_file", "plan_file_sha256", "plan_sha256", "origin_reference_file", "origin_reference_sha256",
    "training_origin", "locations", "payloads", "payloads_sha256", "reservation",
    "maximum_aggregate_gpu_seconds", "maximum_concurrent_gpus", "evaluation_only", "training_authorized",
    "automatic_retry", "resume", "runtime_dependencies",
))
MAX_JSON = 4 * 1024**2
MAX_PAYLOAD = 512 * 1024**2
MAX_TOTAL = 2 * 1024**3
MAX_LEDGER = 256 * 1024
HEX = re.compile(r"[0-9a-f]{64}\Z")
COMMIT = re.compile(r"[0-9a-f]{40}\Z")
JOB_ID = re.compile(r"[1-9][0-9]{0,19}\Z")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def decode(raw):
    require(type(raw) is bytes and 0 < len(raw) <= MAX_JSON, "bounded metadata JSON required")
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "duplicate metadata field")
            result[key] = value
        return result
    def invalid(value):
        raise ValueError("nonfinite metadata number: " + value)
    def integer(value):
        require(len(value) <= 64, "oversized metadata integer")
        return int(value)
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs,
                           parse_constant=invalid, parse_int=integer)
        require(type(value) is dict, "metadata must be one object")
        canonical(value)
        return value
    except RecursionError:
        raise ValueError("metadata nesting exceeds the parser bound")


def relative(value):
    require(type(value) is str and 0 < len(value.encode("utf-8")) <= 4096, "invalid relative path")
    parts = value.split("/")
    require(len(parts) <= 64 and all(part not in ("", ".", "..") for part in parts)
            and not Path(value).is_absolute() and "\\" not in value
            and not any(ord(c) < 32 or ord(c) == 127 for c in value), "noncanonical project path")
    return value


def directory(path):
    path = Path(path).absolute()
    require(".." not in path.parts and 1 < len(path.parts) <= 64
            and len(str(path).encode()) <= 4096, "unsafe directory")
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


def fingerprint(name, maximum=MAX_PAYLOAD, retain=False):
    path = ROOT / relative(name)
    parent, fd = directory(path.parent), -1
    try:
        fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        before = os.fstat(fd)
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_size <= maximum,
                "input must be a bounded single-link regular file: " + name)
        sha, size, chunks = hashlib.sha256(), 0, []
        while True:
            block = os.read(fd, min(65536, maximum + 1 - size))
            if not block:
                break
            size += len(block)
            require(size <= maximum, "input grew beyond its bound")
            sha.update(block)
            if retain:
                chunks.append(block)
        after, named = os.fstat(fd), os.stat(path.name, dir_fd=parent, follow_symlinks=False)
        fields = ("st_dev", "st_ino", "st_size", "st_nlink", "st_mtime_ns", "st_ctime_ns")
        require(size == before.st_size and all(getattr(before, k) == getattr(after, k) == getattr(named, k)
                                             for k in fields), "input changed while reading: " + name)
        return {"bytes": size, "sha256": sha.hexdigest()}, b"".join(chunks)
    finally:
        if fd >= 0:
            os.close(fd)
        os.close(parent)


def read(name, maximum=MAX_JSON):
    return fingerprint(name, maximum, True)[1]


def exists(name):
    path = ROOT / relative(name)
    try:
        parent = directory(path.parent)
    except FileNotFoundError:
        return False
    try:
        try:
            os.stat(path.name, dir_fd=parent, follow_symlinks=False)
        except FileNotFoundError:
            return False
        return True
    finally:
        os.close(parent)


def inventory(name):
    """Closed staged data trees; no links, cache exceptions, or foreign leaves."""
    name = relative(name)
    pending, files, directories = [name], set(), 0
    while pending:
        current = pending.pop()
        directories += 1
        require(directories <= 2048, "input directory inventory exceeds its bound")
        fd = directory(ROOT / current)
        try:
            # fd-scandir is unavailable on older login Python versions. Linux
            # procfs names this already-open owned directory, not a user path;
            # it retains streaming bounds and does not bypass traversal checks.
            try:
                entries = os.scandir(fd)
            except TypeError:
                require(sys.platform == "linux", "this interpreter lacks bounded descriptor directory iteration")
                entries = os.scandir("/proc/self/fd/" + str(fd))
            with entries:
                for index, entry in enumerate(entries):
                    require(index < 8192 and not entry.is_symlink(), "unsafe/oversized input directory")
                    child = relative(current + "/" + entry.name)
                    if entry.is_dir(follow_symlinks=False):
                        pending.append(child)
                        require(len(pending) + directories <= 2048, "input directory queue exceeds bound")
                    else:
                        require(entry.is_file(follow_symlinks=False), "input tree contains a special file")
                        files.add(child)
                        require(len(files) <= 4096, "input file inventory exceeds its bound")
        finally:
            os.close(fd)
    return files


def _sealed(record, field):
    require(type(record) is dict and type(record.get(field)) is str and HEX.fullmatch(record[field])
            and record[field] == digest({k: v for k, v in record.items() if k != field}),
            "metadata semantic seal differs: " + field)


def _small(value):
    require(type(value) is dict and {"bytes", "sha256"} <= set(value)
            and type(value["bytes"]) is int and 0 <= value["bytes"] <= MAX_PAYLOAD
            and type(value["sha256"]) is str and HEX.fullmatch(value["sha256"]), "malformed file identity")
    return {key: value[key] for key in ("bytes", "sha256")}


def _source_files(plan):
    sources = plan.get("source_files")
    require(type(sources) is dict and REQUIRED_SOURCES <= set(sources) and len(sources) <= 256,
            "plan omits its guarded execution source inventory")
    for name, expected in sources.items():
        relative(name)
        require(type(expected) is str and HEX.fullmatch(expected)
                and fingerprint(name, 2 * 1024**2)[0]["sha256"] == expected,
                "planned execution source changed: " + name)
    require(sources["training/peano_policy/requirements-helios.lock"] == RUNTIME_DEPENDENCIES["requirements_sha256"],
            "plan changed the reviewed runtime package lock")
    return sources


def _plan_record(plan):
    _sealed(plan, "plan_sha256")
    require(plan.get("schema") == PLAN_SCHEMA and plan.get("lanes") == ["legacy", "context-alpha"]
            and type(plan.get("goal_count_per_lane")) is int and plan["goal_count_per_lane"] == 32
            and type(plan.get("total_goal_records")) is int and plan["total_goal_records"] == 64
            and type(plan.get("max_model_calls_total")) is int and plan["max_model_calls_total"] == 512
            and type(plan.get("goals")) is list and len(plan["goals"]) == 32
            and plan.get("goal_set_sha256") == GOAL_SET_SHA256
            and canonical(plan.get("matched_budget")) == canonical(MATCHED_BUDGET)
            and plan.get("order") == "lane-primary-goal"
            and plan.get("model_loading") == "sequential-fresh-base-corrected-lora-legacy-unload-context-alpha-unload",
            "plan changed the fixed paired evaluation or budgets")
    profiles = plan.get("search_profiles")
    require(type(profiles) is dict and set(profiles) == {"legacy", "context-alpha"}
            and profiles["legacy"] is None and type(profiles["context-alpha"]) is dict
            and profiles["context-alpha"].get("name") == "context-alpha-v1", "plan changed its two search contracts")
    _sealed(profiles["context-alpha"], "contract_sha256")
    require(plan.get("research_claim_eligible") is False
            and type(plan.get("execution_binding")) is dict and bool(plan["execution_binding"])
            and type(plan.get("execution_contract")) is dict and bool(plan["execution_contract"]),
            "plan lost its execution binding or claim boundary")
    return _source_files(plan)


def _input_payloads(plan_raw, reference_raw):
    plan, reference = decode(plan_raw), decode(reference_raw)
    sources = _plan_record(plan)
    expected_ref = {"schema", "status", "reference", "locations", "files", "witness_origin",
                    "origin_sha256", "claims", "manifest_sha256"}
    require(set(reference) == expected_ref
            and reference["schema"] == "peano-hydra-corrected-search-origin-reference-v1"
            and reference["status"] == "validated-original-origin", "origin reference is incomplete or foreign")
    _sealed(reference, "manifest_sha256")
    identity = reference["reference"]
    require(type(identity) is dict and set(identity) == {"schema", "request", "receipt_sha256"}
            and identity["schema"] == "peano-hydra-corrected-search-origin-identity-v1"
            and canonical(plan.get("origin_reference")) == canonical(identity), "plan relabelled its preserved origin")
    request = identity["request"]
    request_fields = {"schema", "source_manifest_sha256", "source_commit", "preparation_relative_path",
                      "preparation_manifest_sha256", "adapter_manifest_sha256", "authority_profile"}
    require(type(request) is dict and set(request) == request_fields
            and request["schema"] == "peano-hydra-preserved-origin-request-v1"
            and all(request[key] == PINS[key] for key in request_fields - {"schema", "source_manifest_sha256"}),
            "corrected training origin pins changed")
    require(type(reference["claims"]) is dict and bool(reference["claims"])
            and all(value is False for value in reference["claims"].values()), "origin reference invented compute/novelty authority")
    payloads = {PLAN: {"bytes": len(plan_raw), "sha256": hashlib.sha256(plan_raw).hexdigest()},
                ORIGIN: {"bytes": len(reference_raw), "sha256": hashlib.sha256(reference_raw).hexdigest()}}
    def add(name, expected):
        name, expected = relative(name), _small(expected)
        require(name not in payloads or payloads[name] == expected, "conflicting staged file identity")
        payloads[name] = expected
        require(len(payloads) <= 4096, "payload inventory exceeds its bound")
    ref_files = reference["files"]
    require(type(ref_files) is dict and set(ref_files) == {"source-manifest.json", "origin-receipt.json"},
            "reference omitted its exact source/receipt files")
    for name, descriptor in ref_files.items():
        require(set(descriptor) == {"bytes", "sha256"}, "reference file descriptor differs")
        add(PACKAGE + "/origin/" + name, descriptor)
    require(ref_files["source-manifest.json"]["sha256"] == request["source_manifest_sha256"]
            and ref_files["origin-receipt.json"]["sha256"] == identity["receipt_sha256"], "external origin anchors disagree")
    source_raw, receipt_raw = read(PACKAGE + "/origin/source-manifest.json"), read(PACKAGE + "/origin/origin-receipt.json")
    require(hashlib.sha256(source_raw).hexdigest() == request["source_manifest_sha256"]
            and hashlib.sha256(receipt_raw).hexdigest() == identity["receipt_sha256"], "preserved origin metadata bytes changed")
    source, receipt = decode(source_raw), decode(receipt_raw)
    require(source.get("schema") == "peano-hydra-origin-source-bundle-v1"
            and source.get("git_commit") == PINS["source_commit"]
            and type(source.get("files")) is dict and 1 <= len(source["files"]) <= 2048
            and source.get("files_sha256") == digest(source["files"]), "original code inventory differs")
    require(receipt.get("schema") == "peano-hydra-preserved-origin-receipt-v1"
            and canonical(receipt.get("request")) == canonical(request)
            and canonical(receipt.get("source_manifest")) == canonical(source), "origin receipt is for other code or data")
    for name, descriptor in source["files"].items():
        require(set(descriptor) == {"bytes", "sha256", "git_blob", "mode"}
                and type(descriptor["git_blob"]) is str and COMMIT.fullmatch(descriptor["git_blob"])
                and descriptor["mode"] in ("100644", "100755"), "original Git file identity differs")
        add(SOURCE_ROOT + "/" + relative(name), descriptor)
    inputs = receipt.get("inputs")
    require(type(inputs) is dict and set(inputs) == {"preparation", "source", "artifacts", "adapter_manifest"},
            "origin receipt omitted its input inventories")
    preparation = inputs["preparation"]
    require(type(preparation) is dict and set(preparation) == {"manifest", "files"}
            and type(preparation["files"]) is dict and set(preparation["files"]) ==
            {"config.toml", "train.jsonl", "dev.jsonl", "quarantine.jsonl", "preferences.jsonl", "discovery.jsonl"}
            and preparation["manifest"]["sha256"] == PINS["preparation_manifest_sha256"], "preserved preparation differs")
    prep_root = SOURCE_ROOT + "/" + PINS["preparation_relative_path"]
    add(prep_root + "/manifest.json", preparation["manifest"])
    for name, descriptor in preparation["files"].items():
        add(prep_root + "/" + name, descriptor)
    teacher = inputs["source"]
    require(type(teacher) is dict and set(teacher) == {"directory", "files"}
            and teacher["directory"] == "_deploy/hydra-corrective-v2/source"
            and type(teacher["files"]) is dict and set(teacher["files"]) ==
            {"epoch.json", "manifest.json", "sft.jsonl", "preferences.jsonl", "discovery.jsonl"}, "preserved source data differs")
    for name, descriptor in teacher["files"].items():
        add(SOURCE_ROOT + "/" + teacher["directory"] + "/" + name, descriptor)
    witness = reference["witness_origin"]
    require(type(witness) is dict and set(witness) == {"directory", "files"}
            and witness["directory"] == "artifacts/peano-hydra/native-search-repair-2026-08-28/witness-fixture-02"
            and type(witness["files"]) is dict and set(witness["files"]) ==
            {"plan.json", "manifest.json", "coverage.json", "proofs.json", "sft.jsonl"}, "witness-origin inventory differs")
    for name, descriptor in witness["files"].items():
        add(SOURCE_ROOT + "/" + witness["directory"] + "/" + name, descriptor)
    require(inputs["adapter_manifest"]["sha256"] == PINS["adapter_manifest_sha256"], "saved corrected adapter pin differs")
    add(ADAPTER_MANIFEST, inputs["adapter_manifest"])
    require(type(inputs["artifacts"]) is dict and set(inputs["artifacts"]) == {"adapter", "tokenizer"},
            "model artifact roles differ")
    for kind, group in inputs["artifacts"].items():
        require(type(group) is dict and set(group) == {"identity", "files"}
                and type(group["files"]) is dict and 1 <= len(group["files"]) <= 128, "model file inventory differs")
        model_identity = group["identity"]
        require(type(model_identity) is dict and set(model_identity) == {"root", "sha256", "files"}
                and model_identity["root"] == kind and model_identity["sha256"] == PINS["artifact_sha256"][kind]
                and model_identity["sha256"] == digest(model_identity["files"])
                and set(model_identity["files"]) == set(group["files"]), "saved model tree identity differs")
        for name, descriptor in group["files"].items():
            require(relative(name).startswith(kind + "/") and descriptor["sha256"] == model_identity["files"][name],
                    "model artifact escapes its declared role or hash")
            add(PACKAGE + "/model/" + name, descriptor)
    require(type(receipt.get("worker")) is dict, "origin receipt omitted its worker record")
    origin = receipt["worker"].get("origin")
    _sealed(origin, "origin_sha256")
    require(origin.get("training_source_commit") == PINS["source_commit"] and origin.get("run_id") == PINS["run_id"]
            and origin.get("epoch_sha256") == PINS["epoch_sha256"]
            and origin.get("preparation_manifest_sha256") == PINS["preparation_manifest_sha256"]
            and origin.get("adapter_manifest_sha256") == PINS["adapter_manifest_sha256"]
            and origin.get("training_authority_profile") == PINS["authority_profile"]
            and origin.get("model") == PINS["model"] and origin.get("research_claim_eligible") is False
            and reference["origin_sha256"] == origin["origin_sha256"]
            and canonical(plan.get("training_origin")) == canonical(origin), "plan relabelled the saved corrected model")
    total = 0
    for name, expected in payloads.items():
        require(fingerprint(name)[0] == expected, "approved staged input changed: " + name)
        total += expected["bytes"]
        require(total <= MAX_TOTAL, "staged package exceeds its aggregate byte bound")
    for name in (SOURCE_ROOT, PACKAGE + "/model", PACKAGE + "/origin"):
        require(inventory(name) == {item for item in payloads if item.startswith(name + "/")},
                "staged tree has missing or extra input files: " + name)
    require(_source_files(plan) == sources, "execution source changed during input verification")
    return plan, reference, payloads


def run(arguments, environment=None):
    """Bounded argv-only metadata command, with owned-process-group cleanup."""
    child = subprocess.Popen(arguments, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, start_new_session=True, env=environment)
    selector, output, deadline = selectors.DefaultSelector(), {"stdout": bytearray(), "stderr": bytearray()}, time.monotonic() + 25
    try:
        for name, stream in (("stdout", child.stdout), ("stderr", child.stderr)):
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_READ, name)
        while selector.get_map():
            require(time.monotonic() < deadline, "metadata command timed out; any reservation remains charged")
            for key, _ in selector.select(min(0.1, max(0, deadline - time.monotonic()))):
                block = os.read(key.fileobj.fileno(), 65536)
                if not block:
                    selector.unregister(key.fileobj)
                    continue
                output[key.data].extend(block)
                require(len(output[key.data]) <= (MAX_JSON if key.data == "stdout" else 65536),
                        "metadata command output exceeded its bound")
        code = child.wait(timeout=max(0.01, deadline - time.monotonic()))
        require(code == 0, "metadata command failed; reservation remains charged: " + output["stderr"].decode("utf-8", "replace")[:500])
        return output["stdout"].decode("utf-8")
    except BaseException:
        try:
            os.killpg(child.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        child.wait()
        raise
    finally:
        selector.close()
        child.stdout.close()
        child.stderr.close()


def _execution_commit(expected, sources):
    require(type(expected) is str and COMMIT.fullmatch(expected), "a real frozen execution commit is required")
    if exists(".git"):
        environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
        environment.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL="/dev/null", GIT_NO_REPLACE_OBJECTS="1",
                           GIT_NO_LAZY_FETCH="1", GIT_OPTIONAL_LOCKS="0")
        def git(*args):
            return run(["git", "-C", str(ROOT)] + list(args), environment)
        require(git("rev-parse", "--show-toplevel").strip() == str(ROOT)
                and git("rev-parse", "--verify", "HEAD").strip() == expected
                and git("status", "--porcelain", "--untracked-files=all") == "",
                "execution is not the actual clean frozen checkout")
        tracked = git("ls-files", "--error-unmatch", "--", *sorted(sources)).splitlines()
        require(set(tracked) == set(sources), "execution includes untracked source files")
        return None
    raw = read(".peano-source-provenance.tsv", 1024)
    match = re.fullmatch(rb"([0-9a-f]{40})\tfalse\t([0-9TZ:+-]{1,40})\n", raw)
    require(match is not None and match.group(1).decode() == expected, "clean staged source provenance differs")
    return match.group(2).decode()


def _fixed_path(path, expected):
    value = Path(path)
    if value.is_absolute():
        require(value == ROOT / expected, "caller changed the fixed package path")
    else:
        require(relative(str(value)) == expected, "caller changed the fixed package path")


def approval_proposal(*, plan_path, expected_plan_sha256, origin_reference,
                      expected_origin_reference_sha256, source_commit):
    """Return an UNAPPROVED proposal; external plan/reference SHAs are raw bytes."""
    _fixed_path(plan_path, PLAN)
    _fixed_path(origin_reference, ORIGIN)
    require(type(expected_plan_sha256) is str and HEX.fullmatch(expected_plan_sha256)
            and type(expected_origin_reference_sha256) is str and HEX.fullmatch(expected_origin_reference_sha256),
            "external raw plan/reference anchors are required")
    plan_raw, reference_raw = read(PLAN), read(ORIGIN)
    require(hashlib.sha256(plan_raw).hexdigest() == expected_plan_sha256
            and hashlib.sha256(reference_raw).hexdigest() == expected_origin_reference_sha256,
            "external raw plan/reference file differs")
    plan, reference, payloads = _input_payloads(plan_raw, reference_raw)
    _execution_commit(source_commit, plan["source_files"])
    require(read(PLAN) == plan_raw and read(ORIGIN) == reference_raw, "plan/reference changed during admission")
    return {"schema": APPROVAL_SCHEMA, "profile": PROFILE, "run_id": RUN_ID,
            "approved": False, "approval_reference": None, "source_commit": source_commit,
            "source_files": plan["source_files"], "plan_file": PLAN, "plan_file_sha256": expected_plan_sha256,
            "plan_sha256": plan["plan_sha256"], "origin_reference_file": ORIGIN,
            "origin_reference_sha256": expected_origin_reference_sha256,
            "training_origin": plan["training_origin"], "locations": dict(LOCATIONS),
            "payloads": payloads, "payloads_sha256": digest(payloads), "reservation": dict(RESERVATION),
            "maximum_aggregate_gpu_seconds": 1800, "maximum_concurrent_gpus": 1,
            "evaluation_only": True, "training_authorized": False, "automatic_retry": False,
            "resume": False, "runtime_dependencies": dict(RUNTIME_DEPENDENCIES)}


def validate_metadata(expected_approval_sha256):
    """Return (approval dict, plan dict, parsed raw origin-reference dict)."""
    require(type(expected_approval_sha256) is str and HEX.fullmatch(expected_approval_sha256), "external raw approval SHA required")
    raw = read(APPROVAL)
    require(hashlib.sha256(raw).hexdigest() == expected_approval_sha256, "external approval bytes differ")
    approval = decode(raw)
    require(set(approval) == APPROVAL_FIELDS and approval.get("approved") is True
            and type(approval.get("approval_reference")) is str and 0 < len(approval["approval_reference"]) <= 2048,
            "a proposal is not explicit new GPU authorization")
    expected = approval_proposal(plan_path=PLAN, expected_plan_sha256=approval["plan_file_sha256"],
        origin_reference=ORIGIN, expected_origin_reference_sha256=approval["origin_reference_sha256"],
        source_commit=approval["source_commit"])
    expected.update(approved=True, approval_reference=approval["approval_reference"])
    require(canonical(approval) == canonical(expected), "approval changed its fixed inputs, scope or reservation")
    plan_raw, reference_raw = read(PLAN), read(ORIGIN)
    require(hashlib.sha256(plan_raw).hexdigest() == approval["plan_file_sha256"]
            and hashlib.sha256(reference_raw).hexdigest() == approval["origin_reference_sha256"]
            and read(APPROVAL) == raw, "approval/plan/reference changed during metadata admission")
    return approval, decode(plan_raw), decode(reference_raw)


def _identity(approval, expected_sha):
    synced = _execution_commit(approval["source_commit"], approval["source_files"])
    return {"approval_sha256": expected_sha, "source_commit": approval["source_commit"],
            "source_files_sha256": digest(approval["source_files"]), "synced_at": synced,
            "script_sha256": approval["source_files"][JOB], "plan_file_sha256": approval["plan_file_sha256"],
            "plan_sha256": approval["plan_sha256"], "origin_reference_sha256": approval["origin_reference_sha256"],
            "payloads_sha256": approval["payloads_sha256"], "training_origin_sha256": approval["training_origin"]["origin_sha256"]}


def _remote_root():
    scratch = os.environ.get("SCRATCH")
    require(type(scratch) is str and scratch.startswith("/") and ".." not in Path(scratch).parts,
            "configured SCRATCH is required")
    parent = Path(scratch) / REMOTE_PARENT
    require(ROOT == parent / REMOTE_CHILD, "evaluation must use its fresh fixed experiment subdirectory")
    fd = directory(ROOT)
    os.close(fd)
    return parent


def _header(identity):
    return {"kind": "header", "schema": SCHEMA, "profile": PROFILE, "run_id": RUN_ID,
            "identity": identity, "reservation": RESERVATION, "maximum_aggregate_gpu_seconds": 1800,
            "maximum_concurrent_gpus": 1, "evaluation_only": True, "training_authorized": False,
            "automatic_retry": False, "resume": False, "refunds": False}


def _snapshot(raw, job_id):
    require(type(raw) is str and 0 < len(raw.encode()) <= 65536 and len(raw.strip().splitlines()) == 1,
            "held controller record exceeds its bound")
    keys = {"JobId", "JobName", "WorkDir", "JobState", "Reason", "Priority", "Dependency", "Requeue",
            "Account", "Partition", "TimeLimit", "NumNodes", "NumCPUs", "ReqTRES"}
    fields = {}
    for match in re.finditer(r"(?:^|\s)([A-Za-z][A-Za-z0-9]*)=(\S*)", raw):
        key, value = match.groups()
        if key in keys:
            require(key not in fields, "duplicate guarded controller field")
            fields[key] = value
    require(set(fields) == keys and fields["JobId"] == job_id and fields["JobName"] == JOB_NAME
            and fields["WorkDir"] == str(ROOT) and fields["JobState"] == "PENDING"
            and fields["Reason"] == "JobHeldUser" and fields["Priority"] == "0"
            and fields["Dependency"] == "(null)" and fields["Requeue"] == "0"
            and fields["Account"] == ACCOUNT and fields["Partition"] == PARTITION
            and fields["TimeLimit"] == "00:30:00" and fields["NumNodes"] in ("1", "1-1") and fields["NumCPUs"] == "8",
            "controller changed the held evaluation identity, resources, dependency or restart policy")
    tres = {}
    for item in fields["ReqTRES"].split(","):
        key, separator, value = item.partition("=")
        require(separator and key not in tres and key and value, "ambiguous controller resource inventory")
        tres[key] = value
    require(tres.get("cpu") == "8" and tres.get("node") == "1" and tres.get("gres/gpu") == "1"
            and tres.get("mem") in ("64G", "65536M", "67108864K")
            and all(value == "1" for key, value in tres.items() if key.startswith("gres/gpu:")),
            "controller changed the one-GPU/64GiB reservation")
    return {"fields": fields, "raw": raw, "raw_sha256": hashlib.sha256(raw.encode()).hexdigest()}


def load_ledger(identity):
    state = {"events": [], "job_id": None, "gpu_seconds": 0, "phase": "empty", "created_at": None}
    if not exists(LEDGER):
        return state
    raw = read(LEDGER, MAX_LEDGER)
    lines = raw.splitlines(keepends=True)
    require(raw.endswith(b"\n") and 1 <= len(lines) <= 6, "one-shot ledger is truncated or extended")
    previous = "0" * 64
    for index, line in enumerate(lines):
        event = decode(line)
        require(set(event) == {"index", "previous_sha256", "payload", "sha256"}
                and type(event["index"]) is int and event["index"] == index
                and event["previous_sha256"] == previous
                and event["sha256"] == digest({k: event[k] for k in ("index", "previous_sha256", "payload")})
                and canonical(event) + b"\n" == line, "ledger canonical hash chain differs")
        payload = event["payload"]
        require(type(payload) is dict, "ledger payload must be an object")
        if index == 0:
            require(canonical(payload) == canonical(_header(identity)), "ledger belongs to other approval/source; no reset")
            state["phase"] = "header"
        elif index == 1:
            require(set(payload) == {"kind", "reservation", "script_sha256", "created_at"}
                    and payload["kind"] == "reserve" and canonical(payload["reservation"]) == canonical(RESERVATION)
                    and payload["script_sha256"] == identity["script_sha256"]
                    and type(payload["created_at"]) is str
                    and re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z", payload["created_at"]),
                    "exact1800s reservation must precede allocation")
            state.update(gpu_seconds=1800, created_at=payload["created_at"], phase="reserved")
        elif index == 2:
            require(set(payload) == {"kind", "job_id", "dependency_job_id"} and payload["kind"] == "accepted"
                    and type(payload["job_id"]) is str and JOB_ID.fullmatch(payload["job_id"])
                    and payload["dependency_job_id"] is None, "one accepted held job without dependencies is required")
            state.update(job_id=payload["job_id"], phase="accepted")
        elif index == 3:
            require(set(payload) == {"kind", "snapshot"} and payload["kind"] == "held-validated"
                    and type(payload["snapshot"]) is dict
                    and canonical(payload["snapshot"]) == canonical(_snapshot(payload["snapshot"].get("raw"), state["job_id"])),
                    "held job lacks its exact controller readback")
            state["phase"] = "held-validated"
        else:
            kind = "release-authorized" if index == 4 else "released"
            require(set(payload) == {"kind", "job_id"} and payload["kind"] == kind
                    and payload["job_id"] == state["job_id"], "release must follow the durable held-job admission")
            state["phase"] = kind
        state["events"].append(event)
        previous = event["sha256"]
    return state


def append_event(state, payload):
    event = {"index": len(state["events"]), "previous_sha256": state["events"][-1]["sha256"] if state["events"] else "0" * 64,
             "payload": payload}
    event["sha256"] = digest(event)
    before = b"".join(canonical(row) + b"\n" for row in state["events"])
    added = canonical(event) + b"\n"
    _append(LEDGER, before, added, MAX_LEDGER)


def _append(name, before, added, maximum):
    parent = directory((ROOT / relative(name)).parent)
    flags = os.O_WRONLY | os.O_NOFOLLOW | os.O_NONBLOCK
    flags |= os.O_APPEND if before else os.O_CREAT | os.O_EXCL
    fd = os.open(Path(name).name, flags, 0o600, dir_fd=parent)
    try:
        info = os.fstat(fd)
        require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_size == len(before)
                and (read(name, maximum) == before if before else info.st_size == 0)
                and len(before) + len(added) <= maximum, "durable append target changed or exceeds its bound")
        with os.fdopen(fd, "ab", closefd=False) as stream:
            stream.write(added)
            stream.flush()
            os.fsync(fd)
        os.fsync(parent)
        named = os.stat(Path(name).name, dir_fd=parent, follow_symlinks=False)
        require((named.st_dev, named.st_ino) == (info.st_dev, info.st_ino)
                and read(name, maximum) == before + added, "append lost its exact named durable file")
    finally:
        os.close(fd)
        os.close(parent)


def _submissions():
    if not exists(SUBMISSIONS):
        return [], b""
    raw = read(SUBMISSIONS)
    require(raw.startswith(SUBMISSION_HEADER.encode()) and raw.endswith(b"\n"), "project submission log is malformed")
    rows = [line.split("\t") for line in raw.decode().splitlines()[1:]]
    require(len(rows) <= 16384 and all(len(row) == 9 and JOB_ID.fullmatch(row[1]) for row in rows)
            and len({row[1] for row in rows}) == len(rows), "project submission rows are ambiguous")
    return rows, raw


def _submission_row(state, identity):
    return [state["created_at"], state["job_id"], JOB, "", str(ROOT), identity["source_commit"],
            "false", identity["synced_at"], identity["script_sha256"]]


def check_history(state, identity):
    rows, _ = _submissions()
    own = [row for row in rows if row[2] == JOB or row[1] == state["job_id"]]
    require(own == ([_submission_row(state, identity)] if state["job_id"] else []),
            "submission history differs from charged evaluation; no adoption/reset")


def _queue_history(state):
    parent = _remote_root()
    user = os.environ.get("USER", "")
    require(re.fullmatch(r"[A-Za-z0-9._-]{1,64}", user), "scheduler user is not declared")
    accepted = {state["job_id"]} if state["job_id"] else set()
    active = set()
    for line in run(["squeue", "-h", "-u", user, "-o", "%i|%Z|%j|%T"]).splitlines():
        fields = line.split("|")
        require(len(fields) == 4 and JOB_ID.fullmatch(fields[0]), "ambiguous scheduler queue record")
        job, workdir, name, _ = fields
        if workdir == str(parent) or workdir.startswith(str(parent) + "/") or name == JOB_NAME:
            require(job in accepted and workdir == str(ROOT) and name == JOB_NAME and job not in active,
                    "another project allocation is active; no concurrent GPU/source access")
            active.add(job)
    seen = set()
    args = ["sacct", "-n", "-P", "-X", "-u", user, "--starttime=2026-08-29", "--name=" + JOB_NAME,
            "--format=JobIDRaw,JobName%80,WorkDir%4096"]
    for line in run(args).splitlines():
        if not line.strip():
            continue
        fields = line.split("|")
        require(len(fields) in (3, 4) and (len(fields) == 3 or fields[3] == ""), "ambiguous accounting record")
        job, name, workdir = fields[:3]
        require(job in accepted and job not in seen and name == JOB_NAME and workdir == str(ROOT),
                "accounting shows an unrecorded allocation; missing ledger is not a refund")
        seen.add(job)
    require(seen | active == accepted, "accepted job is absent from queue/accounting; manual review required")


def _await_lock(fd, operation):
    deadline = time.monotonic() + 30
    while True:
        try:
            fcntl.flock(fd, operation | fcntl.LOCK_NB)
            return
        except BlockingIOError:
            require(time.monotonic() < deadline, "reservation ledger is busy; no automatic allocation retry")
            time.sleep(0.05)


def check_job_reservation(expected_approval_sha256):
    """Read-only scheduled gate; own release ACK may race legitimate startup."""
    _remote_root()
    job_id = os.environ.get("SLURM_JOB_ID", "")
    require(JOB_ID.fullmatch(job_id) and os.environ.get("SLURM_RESTART_COUNT", "0") == "0"
            and os.environ.get("PEANO_JOB_SCRIPT") == JOB and os.environ.get("PEANO_HYDRA_PROFILE") == PROFILE
            and os.environ.get("SLURM_SUBMIT_DIR") == str(ROOT), "scheduled evaluation identity/restart differs")
    approval, _, _ = validate_metadata(expected_approval_sha256)
    identity = _identity(approval, expected_approval_sha256)
    parent = directory(ROOT / "logs")
    try:
        fd = os.open(Path(LOCK).name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
    finally:
        os.close(parent)
    try:
        info = os.fstat(fd)
        require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_size == 0, "unsafe reservation lock")
        _await_lock(fd, fcntl.LOCK_SH)
        state = load_ledger(identity)
        require(state["phase"] in ("release-authorized", "released") and state["job_id"] == job_id
                and state["gpu_seconds"] == 1800, "job is not the one durably authorized evaluation")
        check_history(state, identity)
    finally:
        os.close(fd)


def _outputs(job_id):
    prefix = "results/peano-hydra/evaluations/search-v2-" + job_id
    return {"report": prefix + ".json", "checkpoint": prefix + ".checkpoints", "plan": prefix + "-plan.json"}


def _submission_options(approval_sha256):
    return ["sbatch", "--parsable", "--hold", "--no-requeue", "--account=" + ACCOUNT,
            "--partition=" + PARTITION, "--nodes=1", "--ntasks=1", "--cpus-per-task=8", "--mem=64G",
            "--gres=gpu:1", "--time=00:30:00", "--chdir=" + str(ROOT), "--export=ALL", "--job-name=" + JOB_NAME,
            "--output=logs/" + JOB_NAME + "-%j.out", "--error=logs/" + JOB_NAME + "-%j.err", JOB, approval_sha256]


def launch(expected_approval_sha256, *, submit=False, expected_commit=None):
    require(type(submit) is bool and "SLURM_JOB_ID" not in os.environ, "launch cannot nest in a scheduled job")
    require(not any(name.startswith("SBATCH_") for name in os.environ), "SBATCH overrides are unauthorized")
    _remote_root()
    approval, _, _ = validate_metadata(expected_approval_sha256)
    identity = _identity(approval, expected_approval_sha256)
    require(expected_commit == identity["source_commit"] and identity["synced_at"] is not None,
            "launch needs the exact approved staged execution source")
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
                fd = os.open(Path(LOCK).name, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600, dir_fd=parent)
            finally:
                os.close(parent)
            info = os.fstat(fd)
            require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_size == 0, "unsafe allocation lock")
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        state = load_ledger(identity)
        require(not state["events"], "evaluation was already opened/charged; no retry/resume/reset/refund")
        check_history(state, identity)
        _queue_history(state)
        if not submit:
            return {"status": "test-only", "allocation_performed": False, "scheduler_submission_tested": False,
                    "approval_sha256": expected_approval_sha256, "reservation": RESERVATION,
                    "evaluation_only": True, "automatic_retry": False, "resume": False}
        require(_identity(validate_metadata(expected_approval_sha256)[0], expected_approval_sha256) == identity,
                "approved inputs/source changed before reservation")
        def record(payload):
            append_event(state, payload)
            return load_ledger(identity)
        state = record(_header(identity))
        state = record({"kind": "reserve", "reservation": RESERVATION, "script_sha256": identity["script_sha256"],
                        "created_at": datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"})
        # The entire new reservation is durable before the ONLY sbatch call.
        raw = run(_submission_options(expected_approval_sha256)).strip()
        require(re.fullmatch(r"[1-9][0-9]{0,19}(?:;[A-Za-z0-9_-]{1,64})?", raw),
                "ambiguous submission;1800seconds remain charged and no automatic release/retry is allowed")
        job_id = raw.split(";", 1)[0]
        state = record({"kind": "accepted", "job_id": job_id, "dependency_job_id": None})
        rows, before = _submissions()
        require(job_id not in {row[1] for row in rows}, "accepted job already exists in project history")
        added = ((SUBMISSION_HEADER if not before else "") + "\t".join(_submission_row(state, identity)) + "\n").encode()
        _append(SUBMISSIONS, before, added, MAX_JSON)
        check_history(state, identity)
        _queue_history(state)
        for output in _outputs(job_id).values():
            require(not exists(output), "evaluation output/checkpoint already exists; no adoption")
        snapshot = _snapshot(run(["scontrol", "-o", "show", "job", job_id]), job_id)
        state = record({"kind": "held-validated", "snapshot": snapshot})
        require(_identity(validate_metadata(expected_approval_sha256)[0], expected_approval_sha256) == identity,
                "approved bytes changed before release; job remains held/charged")
        state = record({"kind": "release-authorized", "job_id": job_id})
        # Startup may read this durable barrier before the release RPC returns.
        fcntl.flock(fd, fcntl.LOCK_UN)
        run(["scontrol", "release", job_id])
        _await_lock(fd, fcntl.LOCK_EX)
        state = record({"kind": "released", "job_id": job_id})
        return {"status": "submitted", "profile": PROFILE, "run_id": RUN_ID, "job_id": job_id,
                "approval_sha256": expected_approval_sha256, "reservation": RESERVATION,
                "cumulative_gpu_seconds": state["gpu_seconds"], "maximum_concurrent_gpus": 1,
                "evaluation_only": True, "training_authorized": False, "automatic_retry": False,
                "resume": False, "ledger": LEDGER, "outputs": _outputs(job_id)}
    finally:
        if fd >= 0:
            os.close(fd)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--approval-sha256", required=True)
    parser.add_argument("--source-commit")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--check", action="store_true")
    modes.add_argument("--check-job", action="store_true")
    modes.add_argument("--test-only", action="store_true")
    modes.add_argument("--submit", action="store_true")
    parser.add_argument("--confirm")
    args = parser.parse_args(argv)
    try:
        require(args.confirm == CONFIRM if args.submit else args.confirm is None,
                "real allocation requires its new explicit evaluation-only confirmation")
        if args.check or args.check_job:
            require(args.source_commit is None, "metadata/job check accepts no source override")
            if args.check_job:
                check_job_reservation(args.approval_sha256)
            approval, plan, reference = validate_metadata(args.approval_sha256)
            result = {"status": "job-verified" if args.check_job else "metadata-verified",
                      "approval_sha256": args.approval_sha256, "plan_file_sha256": approval["plan_file_sha256"],
                      "plan_sha256": plan["plan_sha256"], "origin_reference_sha256": approval["origin_reference_sha256"],
                      "origin_sha256": reference["origin_sha256"], "allocation_performed": False}
        else:
            result = launch(args.approval_sha256, submit=args.submit, expected_commit=args.source_commit)
        print(json.dumps(result, sort_keys=True, allow_nan=False), flush=True)
        return 0
    except (ValueError, TypeError, KeyError, IndexError, OSError, RuntimeError, subprocess.SubprocessError) as error:
        print("search-evaluation-launch: " + " ".join(str(error).split())[:2000], file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
