#!/usr/bin/env python3
"""Collect one terminal pilot without overwriting old evidence or submitting jobs."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
import shlex
import subprocess

SSH = ("ssh", "-T", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
    "-o", "UpdateHostKeys=no", "-o", "ConnectTimeout=15", "-o", "ClearAllForwardings=yes")
REMOTE_ROOT = "/work/bnaskrecki/peano-lab-training/tmp/sqrt2-pilots"
OBS = "source/research/arithmetic-library/sqrt2-power/observations/"
TERMINAL = {"COMPLETED", "FAILED", "TIMEOUT", "CANCELLED", "NODE_FAIL", "OUT_OF_MEMORY", "PREEMPTED", "BOOT_FAIL"}


def collect(snapshot, job_id, output):
    if not re.fullmatch(r"[0-9a-f]{64}", snapshot) or not re.fullmatch(r"[1-9][0-9]*", job_id):
        raise ValueError("exact snapshot hash and numeric job id required")
    if output.exists() or output.is_symlink():
        raise ValueError("new collection directory required")
    query = f"sacct -n -X -j {job_id} --format=JobIDRaw,State,ExitCode,Elapsed,TotalCPU,AllocCPUS,ReqMem,NodeList -P"
    accounting = subprocess.run((*SSH, "wmicluster", query), check=True, capture_output=True,
        text=True, timeout=30).stdout.strip()
    rows = [row.split("|") for row in accounting.splitlines() if row.strip()]
    if len(rows) != 1 or rows[0][0] != job_id or rows[0][1].split()[0] not in TERMINAL:
        raise ValueError("requested job is not uniquely terminal")
    remote = f"{REMOTE_ROOT}/{snapshot}"
    inventory_code = '''import hashlib,json,pathlib,sys
root=pathlib.Path(sys.argv[1]); job=sys.argv[2]
names=["snapshot-manifest.json","submission.tsv","schedule-adjustments.tsv","statement-metadata-process.json","evidence",f"slurm-{job}.out",f"slurm-{job}.err",
"source/research/arithmetic-library/sqrt2-power/observations/shared-wave-fixed-half-log-root-v1",
"source/research/arithmetic-library/sqrt2-power/observations/shared-wave-fixed-half-log-root-lean-wmi-v1",
"source/research/arithmetic-library/sqrt2-power/observations/shared-wave-fixed-half-log-root-lean-wmi-v2",
"source/research/arithmetic-library/sqrt2-power/observations/shared-wave-fixed-half-log-root-witness-v1",
"source/research/arithmetic-library/sqrt2-power/observations/shared-wave-fixed-half-log-root-witness-lean-wmi-v1",
"source/research/arithmetic-library/sqrt2-power/observations/shared-wave-fixed-half-log-fine-root-v1",
"source/research/arithmetic-library/sqrt2-power/observations/shared-wave-fixed-half-log-fine-root-lean-wmi-v1",
"source/research/arithmetic-library/sqrt2-power/observations/shared-wave-log-root-half-argument-v1",
"source/research/arithmetic-library/sqrt2-power/observations/shared-wave-log-root-half-argument-lean-wmi-v1",
"source/research/arithmetic-library/sqrt2-power/observations/shared-wave-exp-log-root-half-transport-v1",
"source/research/arithmetic-library/sqrt2-power/observations/shared-wave-exp-log-root-half-transport-lean-wmi-v1",
"source/research/arithmetic-library/sqrt2-power/observations/shared-wave-requested-half-transport-v1",
"source/research/arithmetic-library/sqrt2-power/observations/shared-wave-requested-half-transport-lean-wmi-v1"]
files={}; selected=[]; total=0
for name in names:
    p=root/name
    if not p.exists(): continue
    selected.append(name)
    for f in sorted(p.rglob("*") if p.is_dir() else [p]):
        if f.is_symlink(): raise ValueError("artifact symlink")
        if not f.is_file(): continue
        size=f.stat().st_size
        if size>32*1024**2: raise ValueError("oversized artifact")
        total+=size
        if total>128*1024**2 or len(files)>3000: raise ValueError("artifact boundary exceeded")
        files[str(f.relative_to(root))]={"bytes":size,"sha256":hashlib.sha256(f.read_bytes()).hexdigest()}
print(json.dumps(dict(selected=selected,files=files),sort_keys=True))
'''
    inventory = json.loads(subprocess.run((*SSH, "wmicluster", f"python3 - {remote} {job_id}"),
        input=inventory_code, text=True, check=True, capture_output=True, timeout=30).stdout)
    output.mkdir(parents=True)
    for name in inventory["selected"]:
        # All names originate in the literal remote inventory above. Validate
        # again before interpolation into rsync's remote command boundary.
        if not re.fullmatch(r"[A-Za-z0-9_./-]+", name) or ".." in Path(name).parts:
            raise ValueError("unsafe artifact name")
        destination = output / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(("rsync", "-az", "--safe-links", "-e", shlex.join(SSH),
            f"wmicluster:{remote}/{name}", str(destination.parent) + "/"), check=True, timeout=60)
    observed = {}
    for path in output.rglob("*"):
        if path.is_symlink():
            raise ValueError("downloaded artifact symlink")
        if path.is_file():
            raw = path.read_bytes()
            observed[str(path.relative_to(output))] = dict(bytes=len(raw), sha256=sha256(raw).hexdigest())
    if observed != inventory["files"]:
        raise ValueError("downloaded bytes differ from remote artifact manifest")
    submission = (output/"submission.tsv").read_text().strip().split("\t")
    if len(submission) != 3 or submission[1:] != [job_id, snapshot]:
        raise ValueError("remote submission identity changed")
    report_path = output/"evidence/pilot-report.json"
    pilot = json.loads(report_path.read_bytes()) if report_path.exists() else None
    if pilot is not None and (pilot.get("job_id") != job_id or pilot.get("source_snapshot_sha256") != snapshot):
        raise ValueError("pilot report identity changed")
    receipt = dict(schema="sqrt2-power-wmi-collection-v1", job_id=job_id, snapshot_sha256=snapshot,
        remote_stage=remote, accounting=accounting, remote_artifact_manifest=inventory["files"],
        downloaded_bytes_match=True, pilot_status=None if pilot is None else pilot["status"],
        authority="transport_and_scheduler_evidence_not_proof", library_admissions=0)
    with (output/"collection.json").open("xb") as stream:
        stream.write(json.dumps(receipt, sort_keys=True, indent=2).encode()+b"\n")
    return {k: receipt[k] for k in ("job_id", "pilot_status", "accounting", "downloaded_bytes_match")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot")
    parser.add_argument("job_id")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    print(json.dumps(collect(args.snapshot, args.job_id, args.output), sort_keys=True))
