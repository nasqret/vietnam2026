#!/usr/bin/env python3
"""Bounded HTTPS comparisons to accepted v35 staging; never proof authority."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
import os
from pathlib import Path
import signal
import subprocess
from threading import Event
from time import monotonic

import check_constructive_delivery_v34 as transport

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "_deploy/proofs-v35"
MANIFEST = "release-v35/manifest.json"
WORKERS = transport.WORKERS
BATCH_SECONDS = transport.BATCH_SECONDS
CLEANUP_SECONDS = transport.CLEANUP_SECONDS
SAMPLES = (
    "index.html", "grand-campaign/index.html", "grand-campaign/campaign.json",
    "grand-campaign/definitions.json", "grand-campaign/dag-audit.json",
    "quadratic-reciprocity/index.html", "quadratic-reciprocity/explorer/defined/tag/PA00A7.html",
    "bertrand-postulate/index.html", "two-squares/index.html", "lucas/index.html", "four-squares/index.html",
    "binary-length/index.html", "euclidean-gcd-transport/index.html", "binary-modular-execution/index.html",
    "polynomial-gcd-bezout/index.html", "congruence-arithmetic/index.html",
    "integer-linear-algebra/explorer/defined/tag/DL0071.html",
    "assets/defined-explorer.js", "assets/exact-explorer.js", "assets/lean-selector.js",
    "assets/defined-explorer.css", "assets/exact-explorer.css",
    "assets/proof-reader.css", "assets/proof-reader.js",
)


def read_file(path, maximum):
    """Read only bounded, owned ordinary files beneath ordinary ancestors."""
    name = transport.relative_path(path.relative_to(ROOT).as_posix())
    path = ROOT / name
    parents = [ROOT]
    for part in Path(name).parts[:-1]:
        parents.append(parents[-1] / part)

    def directory_ids():
        result = []
        for parent in parents:
            info = transport.ordinary(parent, directory=True)
            result.append((parent, tuple(getattr(info, key)
                          for key in ("st_dev", "st_ino", "st_mode", "st_uid"))))
        return result

    directories = directory_ids()
    before = transport.ordinary(path)
    if not 0 < before.st_size <= maximum:
        raise ValueError("empty or oversized delivery input")
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC), "rb") as stream:
        if transport.fingerprint(os.fstat(stream.fileno())) != transport.fingerprint(before):
            raise ValueError("delivery input changed before read")
        raw = stream.read(before.st_size + 1)
        if transport.fingerprint(os.fstat(stream.fileno())) != transport.fingerprint(before):
            raise ValueError("delivery input changed during read")
    if (len(raw) != before.st_size
            or transport.fingerprint(transport.ordinary(path)) != transport.fingerprint(before)
            or directory_ids() != directories):
        raise ValueError("delivery input or ancestor changed during read")
    return raw


def source_binding():
    files = {}
    for name in ("check_constructive_delivery_v35.py", "test_check_constructive_delivery_v35.py",
                 "check_constructive_delivery_v34.py", "test_check_constructive_delivery_v34.py"):
        path = ROOT / "scripts" / name
        raw = read_file(path, 1024 * 1024)
        files[path.relative_to(ROOT).as_posix()] = dict(bytes=len(raw), sha256=sha256(raw).hexdigest())
    return dict(sha256=transport.digest_value(files), files=files)


def valid_pin(value):
    return (type(value) is dict and set(value) == {"bytes", "sha256"}
            and type(value["bytes"]) is int and 0 < value["bytes"] <= transport.MAX_FILE
            and type(value["sha256"]) is str and len(value["sha256"]) == 64
            and all(c in "0123456789abcdef" for c in value["sha256"]))


def snapshot(accepted):
    if type(accepted) is not str or len(accepted) != 64 or any(c not in "0123456789abcdef" for c in accepted):
        raise ValueError("an exact accepted stage manifest SHA256 is required")
    raw = read_file(STAGE / MANIFEST, transport.MAX_MANIFEST)
    if sha256(raw).hexdigest() != accepted: raise ValueError("accepted stage changed")
    value = transport.strict_json(raw)
    if (type(value) is not dict or value.get("schema") != "peano-lab-alpha-v35-public-delivery-v1"
            or value.get("delivery_metadata_only") is not True
            or value.get("alpha_admission_performed") is not False
            or value.get("stable_admission_performed") is not False
            or value.get("current_alpha_version") != "v35"
            or value.get("current_alpha_checked_use_count") != 4318
            or value.get("stable_count") != 432 or value.get("new_theorem_count") != 95
            or value.get("source_owned_theorem_count") != 96 or value.get("source_alias_count") != 1
            or value.get("current_G008_proved") is not True
            or value.get("current_G091_proved") is not False
            or value.get("distinct_prime_product_formula_proved") is not False
            or value.get("family_count") != 69 or value.get("public_on_demand_builds") is not False
            or type(value.get("current_files")) is not dict
            or type(value.get("additions")) is not dict or type(value.get("changed_files")) is not dict):
        raise ValueError("wrong current delivery scope")
    files = dict(value["current_files"])
    if MANIFEST in files or value.get("current_file_count") != len(files):
        raise ValueError("wrong delivery inventory count")
    for name, expected in files.items():
        transport.relative_path(name)
        if not valid_pin(expected): raise ValueError("invalid delivery file pin")
    for name, expected in value["additions"].items():
        if files.get(name) != expected: raise ValueError("addition differs from current inventory")
    for name, change in value["changed_files"].items():
        if (type(change) is not dict or not valid_pin(change.get("before"))
                or files.get(name) != change.get("after")):
            raise ValueError("changed file differs from current inventory")
    files[MANIFEST] = dict(bytes=len(raw), sha256=accepted)
    names = sorted(set(value["additions"]) | set(value["changed_files"]) | set(SAMPLES) | {MANIFEST})
    if not set(names) <= files.keys(): raise ValueError("a required delivery route is absent")
    return files, names


def selected_snapshot(files, names):
    result = {}
    for name in names:
        raw = read_file(STAGE / transport.relative_path(name), transport.MAX_FILE)
        actual = dict(bytes=len(raw), sha256=sha256(raw).hexdigest())
        if actual != files[name]: raise ValueError("actual stage differs from accepted manifest: " + name)
        result[name] = actual
    return result


def run_batch(batch, accepted):
    start, stop = monotonic(), Event()
    result = dict(schema="peano-v35-https-observation-v1", proof_authority=False,
        admission_performed=False, stage_authority=False, batch=batch, requests=[], passed=False,
        accepted_stage_manifest_sha256=accepted,
        limits=dict(workers=WORKERS, request_seconds=transport.REQUEST_SECONDS,
                    batch_seconds_including_cleanup=BATCH_SECONDS, file_bytes=transport.MAX_FILE))
    try:
        binding = source_binding()
        result["source_binding"] = binding
        files, names = snapshot(accepted)
        batches = (len(names) + 15) // 16
        result.update(batches=batches, inventory_path_count=len(names))
        if type(batch) is not int or not 1 <= batch <= batches:
            raise ValueError(f"batch must be an integer in 1..{batches}")
        chosen = names[(batch-1)*16:batch*16]
        result["planned_request_count"] = len(chosen)
        before = selected_snapshot(files, chosen)
        result["stage_before"] = before
        executor = ThreadPoolExecutor(max_workers=WORKERS)
        jobs = []
        try:
            jobs = [executor.submit(transport.fetch,
                dict(stage_relative_path=name, https_path="/proofs/"+name), before[name], accepted,
                start+BATCH_SECONDS-CLEANUP_SECONDS, stop) for name in chosen]
            for job in jobs:
                result["requests"].append(job.result(timeout=max(0.001, start+BATCH_SECONDS-monotonic())))
        finally:
            if len(result["requests"]) != len(chosen): stop.set()
            for job in jobs: job.cancel()
            # The inherited transport owns its85s deadline and bounded kill/reap;
            # never wait implicitly for executor cleanup after a batch deadline.
            executor.shutdown(wait=False, cancel_futures=True)
        after, after_names = snapshot(accepted)
        result["stage_after"] = selected_snapshot(after, chosen)
        if (after != files or after_names != names or result["stage_after"] != before
                or binding != source_binding()):
            raise ValueError("stage or checker sources changed during HTTPS checks")
        if monotonic()-start > BATCH_SECONDS:
            raise TimeoutError("batch exceeded90seconds including cleanup")
        result["passed"] = bool(result["requests"]) and all(row["passed"] for row in result["requests"])
    except (OSError, ValueError, TimeoutError, TypeError, KeyError, RuntimeError, subprocess.SubprocessError) as error:
        stop.set()
        result["failure"] = type(error).__name__ + ": " + str(error)
    result["elapsed_seconds"] = monotonic()-start
    result["request_count"] = len(result["requests"])
    result["successful_requests"] = sum(row["passed"] for row in result["requests"])
    result["not_completed_count"] = result.get("planned_request_count", 0)-result["request_count"]
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--accepted-stage-manifest-sha256", required=True)
    parser.add_argument("--batch", type=int, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    def expired(*unused):
        raise TimeoutError("hard90second batch deadline")
    previous = signal.signal(signal.SIGALRM, expired)
    signal.alarm(BATCH_SECONDS)
    try:
        result = run_batch(args.batch, args.accepted_stage_manifest_sha256)
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)
    raw = json.dumps(result, sort_keys=True, indent=2).encode()+b"\n"
    if args.output:
        with args.output.open("xb") as stream: stream.write(raw)
    print(json.dumps({k:v for k,v in result.items() if k != "requests"},sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__": raise SystemExit(main())
