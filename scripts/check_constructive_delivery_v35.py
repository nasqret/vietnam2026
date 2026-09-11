#!/usr/bin/env python3
"""Bounded HTTPS comparisons to accepted v35 staging; never proof authority."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
from pathlib import Path
from threading import Event
from time import monotonic

import check_constructive_delivery_v34 as transport

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "_deploy/proofs-v35"
MANIFEST = "release-v35/manifest.json"
SAMPLES = (
    "index.html", "grand-campaign/index.html", "grand-campaign/campaign.json",
    "grand-campaign/definitions.json", "grand-campaign/dag-audit.json",
    "quadratic-reciprocity/index.html", "quadratic-reciprocity/explorer/defined/tag/PA00A7.html",
    "bertrand/index.html", "two-squares/index.html", "lucas/index.html", "four-squares/index.html",
    "binary-length/index.html", "euclidean-gcd-transport/index.html", "binary-modular-execution/index.html",
    "polynomial-gcd-bezout/index.html", "congruence-arithmetic/index.html",
    "assets/defined-explorer.js", "assets/exact-explorer.js", "assets/lean-selector.js",
)


def snapshot(accepted):
    if len(accepted) != 64 or any(c not in "0123456789abcdef" for c in accepted):
        raise ValueError("an exact accepted stage manifest SHA256 is required")
    path = STAGE / MANIFEST
    if path.is_symlink() or not path.is_file(): raise ValueError("ordinary stage manifest required")
    raw = path.read_bytes()
    if sha256(raw).hexdigest() != accepted: raise ValueError("accepted stage changed")
    value = transport.strict_json(raw)
    if (value.get("schema") != "peano-lab-alpha-v35-public-delivery-v1"
            or value.get("current_alpha_checked_use_count") != 4318
            or value.get("family_count") != 69 or value.get("public_on_demand_builds") is not False):
        raise ValueError("wrong current delivery scope")
    files = dict(value["current_files"])
    files[MANIFEST] = dict(bytes=len(raw), sha256=accepted)
    names = sorted(set(value["additions"]) | set(SAMPLES) | {MANIFEST})
    if not set(names) <= files.keys(): raise ValueError("a required delivery route is absent")
    return files, names


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--accepted-stage-manifest-sha256", required=True)
    parser.add_argument("--batch", type=int, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    accepted = args.accepted_stage_manifest_sha256
    files, names = snapshot(accepted)
    batches = (len(names)+15)//16
    if not 1 <= args.batch <= batches: parser.error(f"batch must be in1..{batches}")
    chosen = names[(args.batch-1)*16:args.batch*16]
    before = {}
    for name in chosen:
        transport.relative_path(name)
        path = STAGE / name
        if path.is_symlink() or not path.is_file(): raise ValueError("ordinary stage file required")
        raw = path.read_bytes()
        actual = dict(bytes=len(raw), sha256=sha256(raw).hexdigest())
        if actual != files[name]: raise ValueError("actual stage differs from accepted manifest")
        before[name] = actual
    start, stop = monotonic(), Event()
    with ThreadPoolExecutor(max_workers=4) as executor:
        jobs = [executor.submit(transport.fetch,
            dict(stage_relative_path=name, https_path="/proofs/"+name), before[name], accepted,
            start+85, stop) for name in chosen]
        reports = [job.result(timeout=max(0.001, start+90-monotonic())) for job in jobs]
    after, after_names = snapshot(accepted)
    if after != files or after_names != names: raise ValueError("stage changed during HTTPS checks")
    for name in chosen:
        raw = (STAGE/name).read_bytes()
        if dict(bytes=len(raw), sha256=sha256(raw).hexdigest()) != before[name]:
            raise ValueError("stage file changed during HTTPS checks")
    result = dict(schema="peano-v35-https-observation-v1", proof_authority=False,
        admission_performed=False, stage_authority=False, batch=args.batch, batches=batches,
        inventory_path_count=len(names), request_count=len(reports), requests=reports,
        accepted_stage_manifest_sha256=accepted,
        passed=bool(reports) and all(row["passed"] for row in reports), elapsed_seconds=monotonic()-start)
    raw = json.dumps(result, sort_keys=True, indent=2).encode()+b"\n"
    if args.output:
        with args.output.open("xb") as stream: stream.write(raw)
    print(json.dumps({k:v for k,v in result.items() if k != "requests"},sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__": raise SystemExit(main())
