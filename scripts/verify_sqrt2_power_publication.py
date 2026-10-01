#!/usr/bin/env python3
"""Compare every research-publication payload byte through public HTTPS.

This is a delivery check, not a proof check or an Alpha admission gate.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import gzip
import io
import json
from pathlib import Path
import time
from urllib.request import Request, urlopen

from stage_sqrt2_power_research import RELEASE, encode, inventory, pin, safe_path

BASE = "https://bnaskrecki.faculty.wmi.amu.edu.pl/proofs/"
MAX_BYTES = 32 * 1024**2


def fetch(name, expected, deadline):
    started = time.monotonic()
    remaining = deadline - started
    if remaining <= 0:
        return dict(path=name, passed=False, error="aggregate HTTP deadline")
    url = BASE + name + "?research=sqrt2-power-2026-10-01"
    try:
        request = Request(url, headers={"Accept-Encoding": "identity", "Cache-Control": "no-cache"})
        with urlopen(request, timeout=min(10, remaining)) as response:
            if response.status != 200 or response.url != url:
                raise ValueError("unexpected HTTP status or redirect")
            raw = response.read(MAX_BYTES+1)
            if len(raw) > MAX_BYTES:
                raise ValueError("oversized HTTP response")
            encoding = response.headers.get("Content-Encoding", "identity")
            if encoding == "gzip":
                with gzip.GzipFile(fileobj=io.BytesIO(raw)) as decoded:
                    raw = decoded.read(MAX_BYTES+1)
                if len(raw) > MAX_BYTES:
                    raise ValueError("oversized decoded HTTP response")
            elif encoding != "identity":
                raise ValueError("unsupported transfer encoding")
            actual = pin(raw)
            return dict(path=name, url=url, passed=actual == expected, actual=actual,
                expected=expected, status=response.status,
                content_type=response.headers.get("Content-Type"),
                cache_control=response.headers.get("Cache-Control"),
                transfer_encoding=encoding, wall_seconds=time.monotonic()-started)
    except (OSError, ValueError) as error:
        return dict(path=name, url=url, passed=False, error=str(error),
                    wall_seconds=time.monotonic()-started)


def verify(stage, output):
    if output.exists() or output.is_symlink():
        raise ValueError("new verification report required")
    manifest_raw = safe_path(stage, RELEASE).read_bytes()
    manifest = json.loads(manifest_raw)
    if (manifest.get("schema") != "sqrt2-power-research-delivery-v1"
        or manifest.get("authority") != "research_publication_not_library_admission"
        or manifest.get("new_library_admissions") != 0
        or manifest.get("payload_file_count") != 267):
        raise ValueError("unexpected research delivery scope")
    files = dict(manifest["files"])
    files[RELEASE] = pin(manifest_raw)
    inventory(stage, files)
    started = time.monotonic()
    # Network concurrency only: no proof/solver jobs or unbounded subprocesses.
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(lambda item: fetch(item[0], item[1], started+120), sorted(files.items())))
    report = dict(schema="sqrt2-power-public-https-observation-v1",
        authority="delivery_observation_not_proof", manifest=pin(manifest_raw),
        status="passed" if all(row["passed"] for row in rows) else "failed",
        files_checked=len(rows), files_passed=sum(row["passed"] for row in rows),
        max_http_workers=4, per_request_timeout_seconds=10, aggregate_deadline_seconds=120,
        wall_seconds=time.monotonic()-started, rows=rows)
    from run_sqrt2_power_pilot import save_new
    save_new(output, encode(report))
    return {name: report[name] for name in ("status", "files_checked", "files_passed", "wall_seconds")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = verify(args.stage, args.output)
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["status"] == "passed" else 1)
