#!/usr/bin/env python3
"""Bounded, read-only HTTPS observations; never proof or stage authority."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
import os
from pathlib import Path, PurePosixPath
import re
import selectors
import signal
import stat
import subprocess
from threading import Event
from time import monotonic

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "_deploy/proofs-v34"
INVENTORY = ROOT / "research/arithmetic-library/working/alpha-v34-release-v1/https-smoke-path-inventory-v1.json"
INVENTORY_SHA256 = "a17c4a4096ddb54e27709d89b2f57a229b9f4d1fd3684cea0f283bb2653d2b41"
ORIGIN = "https://bnaskrecki.faculty.wmi.amu.edu.pl"
MANIFEST = "release-v34/manifest.json"
MAX_FILE = 64 * 1024 * 1024
MAX_MANIFEST = 4 * 1024 * 1024
MAX_HEADERS = MAX_STDERR = 64 * 1024
WORKERS, REQUEST_SECONDS, BATCH_SECONDS, CLEANUP_SECONDS = 4, 20, 90, 5
MARKER = b"\nPEANO_V34_HTTP "


class DeliveryError(ValueError):
    pass


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise DeliveryError("duplicate JSON key")
            result[key] = value
        return result
    def constant(value):
        raise DeliveryError("nonfinite JSON number")
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)


def digest_value(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def relative_path(value):
    if (type(value) is not str or not value or "\\" in value or "%" in value
            or "?" in value or "#" in value or any(ord(c) < 32 for c in value)):
        raise DeliveryError("unsafe relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or str(path) != value:
        raise DeliveryError("noncanonical relative path")
    return value


def fingerprint(info):
    return tuple(getattr(info, key) for key in
                 ("st_dev", "st_ino", "st_mode", "st_uid", "st_size", "st_mtime_ns", "st_ctime_ns"))


def ordinary(path, *, directory=False):
    info = path.lstat()
    if info.st_uid != os.getuid() or not (stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode)):
        raise DeliveryError("linked, foreign-owned or nonordinary input: " + str(path))
    return info


def bounded_source(path, maximum=1024 * 1024):
    if ROOT not in path.parents:
        raise DeliveryError("checker source escaped repository")
    parents = tuple(dict.fromkeys(parent if parent.is_absolute() else ROOT / parent
                    for parent in (ROOT, *reversed(path.relative_to(ROOT).parents))))
    def identities():
        result = []
        for parent in parents:
            info = ordinary(parent, directory=True)
            result.append((parent, tuple(getattr(info, key) for key in ("st_dev", "st_ino", "st_mode", "st_uid"))))
        return result
    directory_ids = identities()
    before = ordinary(path)
    if not 0 < before.st_size <= maximum:
        raise DeliveryError("oversized checker input")
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC), "rb") as stream:
        if fingerprint(os.fstat(stream.fileno())) != fingerprint(before):
            raise DeliveryError("checker input changed before read")
        raw = stream.read(before.st_size + 1)
        if fingerprint(os.fstat(stream.fileno())) != fingerprint(before):
            raise DeliveryError("checker input changed during read")
    if len(raw) != before.st_size or fingerprint(ordinary(path)) != fingerprint(before):
        raise DeliveryError("checker input path changed")
    if identities() != directory_ids:
        raise DeliveryError("checker source ancestor changed")
    return raw


def read_stage(name, *, collect=False, maximum=MAX_FILE):
    path = STAGE / relative_path(name)
    ancestors = [STAGE.parent, STAGE]
    ancestors.extend(path.parents[i] for i in reversed(range(len(path.parents)))
                     if path.parents[i] != STAGE and STAGE in path.parents[i].parents)
    directories = [(p, fingerprint(ordinary(p, directory=True))) for p in ancestors]
    before = ordinary(path)
    if not 0 < before.st_size <= maximum:
        raise DeliveryError("empty or oversized stage input")
    h, chunks, size = sha256(), [], 0
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC), "rb") as stream:
        if fingerprint(os.fstat(stream.fileno())) != fingerprint(before):
            raise DeliveryError("stage file changed before read")
        while True:
            block = stream.read(min(1024 * 1024, maximum + 1 - size))
            if not block:
                break
            size += len(block)
            if size > maximum:
                raise DeliveryError("stage read exceeds bound")
            h.update(block)
            if collect:
                chunks.append(block)
        if fingerprint(os.fstat(stream.fileno())) != fingerprint(before):
            raise DeliveryError("stage file changed during read")
    if size != before.st_size or fingerprint(ordinary(path)) != fingerprint(before):
        raise DeliveryError("stage path changed during read")
    if any(fingerprint(ordinary(p, directory=True)) != pin for p, pin in directories):
        raise DeliveryError("stage directory changed during read")
    return {"bytes": size, "sha256": h.hexdigest(), "fingerprint": fingerprint(before)}, b"".join(chunks)


def validate_inventory(data):
    if type(data) is not dict or data.get("path_count") != 230 or data.get("family_count") != 68:
        raise DeliveryError("wrong inventory scope")
    rows = data.get("paths")
    if type(rows) is not list or len(rows) != 230:
        raise DeliveryError("missing inventory rows")
    seen = set()
    for row in rows:
        if type(row) is not dict:
            raise DeliveryError("malformed inventory row")
        name = relative_path(row.get("stage_relative_path"))
        if name in seen or row.get("https_path") != "/proofs/" + name:
            raise DeliveryError("duplicate or conflicting inventory route")
        seen.add(name)
    return rows


def load_inventory():
    raw = bounded_source(INVENTORY)
    if sha256(raw).hexdigest() != INVENTORY_SHA256:
        raise DeliveryError("inventory identity changed")
    return validate_inventory(strict_json(raw))


def stage_snapshot(names, accepted_sha256):
    if type(accepted_sha256) is not str or not re.fullmatch(r"[0-9a-f]{64}", accepted_sha256):
        raise DeliveryError("explicit accepted stage manifest SHA256 required")
    pin, raw = read_stage(MANIFEST, collect=True, maximum=MAX_MANIFEST)
    if pin["sha256"] != accepted_sha256:
        raise DeliveryError("accepted stage manifest does not match")
    manifest = strict_json(raw)
    files = manifest.get("current_files")
    if (manifest.get("schema") != "peano-lab-alpha-v34-public-delivery-v1"
            or manifest.get("delivery_metadata_only") is not True
            or manifest.get("alpha_admission_performed") is not False
            or manifest.get("stable_admission_performed") is not False
            or manifest.get("alpha_version") != "v34" or manifest.get("checked_use_count") != 4223
            or manifest.get("stable_count") != 432 or type(files) is not dict):
        raise DeliveryError("wrong stage manifest scope")
    result = {MANIFEST: pin}
    for name in names:
        actual, _ = read_stage(name)
        expected = files.get(name)
        if (type(expected) is not dict or type(expected.get("bytes")) is not int
                or {k: actual[k] for k in ("bytes", "sha256")} != expected):
            raise DeliveryError("selected stage bytes disagree with manifest: " + name)
        result[name] = actual
    return result


def source_binding():
    pins = {}
    for path in (Path(__file__), ROOT / "scripts/test_check_constructive_delivery_v34.py", INVENTORY):
        raw = bounded_source(path)
        pins[path.relative_to(ROOT).as_posix()] = {"bytes": len(raw), "sha256": sha256(raw).hexdigest()}
    return {"sha256": digest_value(pins), "files": pins}


def curl_command(url, headers, seconds):
    return ["curl", "-q", "--proto", "=https", "--proto-redir", "=https",
            "--max-redirs", "0", "--silent", "--show-error", "--connect-timeout", "10",
            "--max-time", str(seconds), "--header", "Accept-Encoding: identity",
            "--user-agent", "Peano-v34-delivery-observation/1", "--dump-header", str(headers),
            "--write-out", "%{stderr}\\nPEANO_V34_HTTP %{http_code} %{url_effective}\\n", url]


def fetch(row, expected, accepted_sha256, batch_deadline, stop=None):
    start = monotonic()
    url = ORIGIN + row["https_path"] + "?v=" + accepted_sha256[:12]
    result = {"stage_relative_path": row["stage_relative_path"], "url": url,
              "status": None, "effective_url": None, "headers": "", "stderr": "",
              "body_bytes": 0, "body_sha256": None, "curl_exit": None,
              "passed": False, "failure": None, "expected": {k: expected[k] for k in ("bytes", "sha256")}}
    h, errors, header_bytes, process = sha256(), bytearray(), bytearray(), None
    header_read = header_write = None
    try:
        deadline = min(start + REQUEST_SECONDS, batch_deadline)
        if stop is not None and stop.is_set():
            raise DeliveryError("batch cleanup failure forbids further requests")
        if deadline <= start:
            raise TimeoutError("batch request deadline reached before launch")
        header_read, header_write = os.pipe()
        try:
            command = curl_command(url, "/dev/fd/" + str(header_write), deadline - start)
            result["command"] = command
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       pass_fds=(header_write,))
            os.close(header_write)
            header_write = None
            with selectors.DefaultSelector() as selected:
                selected.register(process.stdout, selectors.EVENT_READ, "body")
                selected.register(process.stderr, selectors.EVENT_READ, "stderr")
                selected.register(header_read, selectors.EVENT_READ, "headers")
                while selected.get_map():
                    if stop is not None and stop.is_set():
                        raise DeliveryError("batch stopped after a child cleanup failure")
                    if monotonic() >= deadline:
                        raise TimeoutError("HTTPS request deadline exceeded")
                    for key, _ in selected.select(min(0.05, max(0, deadline - monotonic()))):
                        remaining = {"body": expected["bytes"] - result["body_bytes"],
                                     "stderr": MAX_STDERR - len(errors),
                                     "headers": MAX_HEADERS - len(header_bytes)}[key.data]
                        descriptor = key.fileobj if type(key.fileobj) is int else key.fileobj.fileno()
                        block = os.read(descriptor, min(65536, remaining + 1))
                        if not block:
                            selected.unregister(key.fileobj)
                        elif key.data == "body":
                            result["body_bytes"] += len(block)
                            h.update(block)
                            if result["body_bytes"] > expected["bytes"]:
                                raise DeliveryError("HTTPS body exceeds expected byte bound")
                        elif key.data == "stderr":
                            if len(errors) + len(block) > MAX_STDERR:
                                raise DeliveryError("curl diagnostics exceed bound")
                            errors.extend(block)
                        else:
                            if len(header_bytes) + len(block) > MAX_HEADERS:
                                raise DeliveryError("HTTPS headers exceed bound")
                            header_bytes.extend(block)
            process.wait(timeout=max(0.001, deadline - monotonic()))
            result["curl_exit"] = process.returncode
            result["headers"] = header_bytes.decode("latin1")
            if MARKER not in errors:
                raise DeliveryError("missing actual curl status metadata")
            _, metadata = bytes(errors).rsplit(MARKER, 1)
            if len(metadata) > 4096:
                raise DeliveryError("curl metadata exceeds bound")
            status, effective = metadata.rstrip(b"\n").split(b" ", 1)
            result["status"] = status.decode("ascii")
            result["effective_url"] = effective.decode("utf-8")
            if process.returncode != 0 or result["status"] != "200" or result["effective_url"] != url:
                raise DeliveryError("curl failed, redirected or returned a non-200 response")
            statuses = re.findall(r"(?m)^HTTP/(?:1\.[01]|2|3) ([0-9]{3})[^\r\n]*\r?$", result["headers"])
            if not statuses or statuses[-1] != "200":
                raise DeliveryError("actual response headers do not end in HTTP200")
            if re.search(r"(?im)^content-encoding:\s*(?!identity\s*$)\S+", result["headers"]):
                raise DeliveryError("unexpected content encoding")
            if result["body_bytes"] != expected["bytes"] or h.hexdigest() != expected["sha256"]:
                raise DeliveryError("HTTPS bytes differ from accepted staging")
            result["passed"] = True
        finally:
            for descriptor in (header_read, header_write):
                if descriptor is not None:
                    os.close(descriptor)
    except (OSError, ValueError, TimeoutError, subprocess.SubprocessError) as error:
        result["failure"] = type(error).__name__ + ": " + str(error)
    finally:
        if process is not None:
            try:
                if process.poll() is None:
                    process.kill()
                process.wait(timeout=min(CLEANUP_SECONDS, max(0.001, batch_deadline + CLEANUP_SECONDS - monotonic())))
            except (OSError, subprocess.SubprocessError) as error:
                if stop is not None:
                    stop.set()
                result["passed"] = False
                result["failure"] = "curl cleanup failed: " + str(error)
            result["curl_exit"] = process.returncode
            process.stdout.close()
            process.stderr.close()
        result["body_sha256"] = h.hexdigest()
        result["headers"] = header_bytes.decode("latin1")
        result["stderr"] = bytes(errors).decode("latin1")
        result["stderr_encoding"] = "latin1_lossless"
        result["stderr_bytes"] = len(errors)
        result["elapsed_seconds"] = monotonic() - start
    return result


def run_batch(batch, accepted_sha256):
    if type(batch) is not int or not 1 <= batch <= 15:
        raise DeliveryError("batch must be an integer in1..15")
    start = monotonic()
    report = {"schema": "peano-v34-https-delivery-observations-v1", "proof_authority": False,
              "admission_performed": False, "stage_authority": False, "batch": batch,
              "accepted_stage_manifest_sha256": accepted_sha256, "requests": [], "passed": False,
              "limits": {"workers": WORKERS, "request_seconds": REQUEST_SECONDS,
                         "batch_seconds_including_cleanup": BATCH_SECONDS, "file_bytes": MAX_FILE}}
    try:
        rows = load_inventory()[(batch - 1) * 16:batch * 16]
        assert len(rows) == (6 if batch == 15 else 16)
        report["planned_request_count"] = len(rows)
        binding = source_binding()
        report["source_binding"] = binding
        names = [row["stage_relative_path"] for row in rows]
        before = stage_snapshot(names, accepted_sha256)
        report["stage_before"] = before
        deadline = start + BATCH_SECONDS - CLEANUP_SECONDS
        executor = ThreadPoolExecutor(max_workers=WORKERS)
        stop = Event()
        futures = []
        try:
            futures = [executor.submit(fetch, row, before[row["stage_relative_path"]], accepted_sha256, deadline, stop) for row in rows]
            for future in futures:
                report["requests"].append(future.result(timeout=max(0.001, start + BATCH_SECONDS - monotonic())))
        finally:
            if len(report["requests"]) != len(rows):
                stop.set()
            for future in futures:
                future.cancel()
            # No implicit unbounded __exit__ join on a deadline/error. Running
            # children retain their earlier85s deadline and bounded cleanup.
            executor.shutdown(wait=False, cancel_futures=True)
        after = stage_snapshot(names, accepted_sha256)
        report["stage_after"] = after
        if before != after or binding != source_binding():
            raise DeliveryError("stage or checker sources changed during requests")
        if monotonic() - start > BATCH_SECONDS:
            raise TimeoutError("batch exceeded90seconds including cleanup")
        report["passed"] = all(item["passed"] for item in report["requests"])
    except (OSError, ValueError, TimeoutError, AssertionError, subprocess.SubprocessError) as error:
        report["failure"] = type(error).__name__ + ": " + str(error)
    report["elapsed_seconds"] = monotonic() - start
    report["request_count"] = len(report["requests"])
    report["successful_requests"] = sum(item["passed"] for item in report["requests"])
    report["not_completed_count"] = report.get("planned_request_count", 0) - report["request_count"]
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch", type=int, required=True)
    parser.add_argument("--accepted-stage-manifest-sha256", required=True)
    args = parser.parse_args(argv)
    def expired(*unused):
        raise TimeoutError("hard90second batch deadline")
    previous = signal.signal(signal.SIGALRM, expired)
    signal.alarm(BATCH_SECONDS)
    try:
        report = run_batch(args.batch, args.accepted_stage_manifest_sha256)
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)
    print(json.dumps(report, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
