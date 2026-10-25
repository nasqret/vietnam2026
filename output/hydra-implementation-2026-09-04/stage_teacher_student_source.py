"""Stage one sealed additive derivative; do not allocate, prove, or train."""
from pathlib import Path
import ast
import hashlib
import json
import shlex
import subprocess
import time

from stage_p6_remote import SSH
from stage_p6_scheduler_v3 import REMOTE as REVIEWED_REMOTE
from p6_smoke_transport import run_ssh

HERE = Path(__file__).resolve().parent
BUNDLE = HERE / "teacher-student-source-bundle-01"
OUT = HERE / "teacher-student-transfer-01"
CAMPAIGN = "/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904"
MANIFEST_SHA = "69fd2873350245cfa9adf7095510fbfc6f993e165b35125eac18d7f737913e27"
ARCHIVE_SHA = "a2196f8dfff25e940c72937feccfaaa562ddb5aac6952bd64fd117137f22fb3d"
SEAL_SHA = "c8c898dafc55868d8ac768e6b11b751dd7c6c69af27393a273e103133836f8c3"
PARENT_SHA = "e874311f7561564f84a526cff226e497cd8e9c3dcc8122f13b9871cc96ecb031"

# Preserve the already executed bounded quota/upload/extraction protocol. The
# only remote changes are the new exclusive destination, exact count, and a
# stronger manifest binding. The original uploader and its receipts are intact.
assert REVIEWED_REMOTE.count("/bundles/source-data-07") == 1
assert REVIEWED_REMOTE.count("manifest['file_count']==1206") == 1
REMOTE = REVIEWED_REMOTE.replace("/bundles/source-data-07", "/bundles/teacher-student-source-01")
REMOTE = REMOTE.replace("manifest['file_count']==1206", "manifest['file_count']==1325")
REMOTE = REMOTE.replace("request=json.loads(header);manifest=request['manifest']",
    "request=json.loads(header);manifest=request['manifest']\n"
    "assert hashlib.sha256((json.dumps(manifest,sort_keys=True,separators=(',',':'),allow_nan=False)+'\\n').encode()).hexdigest()=='" + MANIFEST_SHA + "'\n"
    "assert manifest['archive_sha256']=='" + ARCHIVE_SHA + "' and manifest['archive_bytes']==11248493\n"
    "assert manifest['expanded_bytes']==112064116 and manifest['addition_count']==24")


def main():
    ast.parse(REMOTE, feature_version=(3, 6))
    seal_raw = (BUNDLE / "SEALED.json").read_bytes()
    assert hashlib.sha256(seal_raw).hexdigest() == SEAL_SHA
    seal = json.loads(seal_raw)
    assert seal["actual_build_exit_code"] == 0 and seal["actual_completion_chunk"] == "eb111f"
    manifest_raw = (BUNDLE / "manifest.json").read_bytes()
    assert hashlib.sha256(manifest_raw).hexdigest() == MANIFEST_SHA
    manifest = json.loads(manifest_raw)
    parent_raw = (HERE / "combined-source-bundle-01/manifest.json").read_bytes()
    assert hashlib.sha256(parent_raw).hexdigest() == PARENT_SHA
    parent = json.loads(parent_raw)
    assert len(manifest["files"]) == manifest["file_count"] == 1325
    assert all(manifest["files"][name] == value for name, value in parent["files"].items())
    assert set(manifest["files"]) - set(parent["files"]) == set(manifest["additions"])
    assert len(manifest["additions"]) == 24
    archive = (BUNDLE / "source-data.tar.gz").read_bytes()
    assert len(archive) == manifest["archive_bytes"] == 11248493
    assert hashlib.sha256(archive).hexdigest() == manifest["archive_sha256"] == ARCHIVE_SHA
    OUT.mkdir(exist_ok=False)
    request = {"authority": "HYDRA_EXPERIMENT_AUTHORITY.md",
        "directory": CAMPAIGN + "/bundles/teacher-student-source-01", "manifest": manifest,
        "local_manifest_sha256": MANIFEST_SHA, "local_seal_sha256": SEAL_SHA,
        "purpose": "One ordinary derived source root for the existing student controller and its separate teacher-exposure evaluation; unchanged original1301files plus24pinned additive files. No theorem execution, model loading, GPU allocation or training.",
        "automatic_retry": False}
    (OUT / "request.json").write_text(json.dumps(request, indent=2) + "\n")
    (OUT / "remote-script.py").write_text(REMOTE)
    start = time.monotonic()
    result = run_ssh(SSH + ["python3 -c " + shlex.quote(REMOTE)],
        input=json.dumps(request).encode() + b"\n" + archive,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=170,
        directory=OUT, phase="upload")
    (OUT / "stdout.json").write_bytes(result.stdout)
    (OUT / "stderr.txt").write_bytes(result.stderr)
    receipt = {"actual_ssh_exit_code": result.returncode, "elapsed_seconds": time.monotonic() - start,
        "archive_sha256": ARCHIVE_SHA, "archive_bytes": len(archive), "manifest_sha256": MANIFEST_SHA,
        "remote_directory": request["directory"], "gpu_allocations": 0, "model_calls": 0,
        "native_runs": 0, "automatic_retry": False}
    (OUT / "actual-completion.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(result.stdout.decode(), end="")
    print(result.stderr.decode(), end="")
    print(json.dumps(receipt), flush=True)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
