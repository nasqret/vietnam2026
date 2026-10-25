"""Stage the isolated JSON comparison correction; no allocation or training."""
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
BUNDLE = HERE / "p6-source-bundle-07"
OUT = HERE / "p6-transfer-07"
CAMPAIGN = "/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904"
MANIFEST_SHA = "0cf4cce57f8e4793d09c6283b33dfe81400a3d9653e994116c9899f23da737a3"
ARCHIVE_SHA = "fdb49807ac5defc7d9be8e079a9cef2438a602ca632971e9abc4ac022fa0a0e2"
SEAL_SHA = "2e2a4876096e0fc6b30bde28261b860a8d972a00c17702fa20f335b1d766aaaf"
PARENT_SHA = "e1f5518231eaa04469d39c830bd480ec11ff4ed891907772d48aeab67da18f96"
TRAINER_SHA = "b0701a1c337fb33e904e6f721b450aa7d541b72ae38b2c2cfaf54e790bc192b7"

assert REVIEWED_REMOTE.count("/bundles/source-data-07") == 1
REMOTE = REVIEWED_REMOTE.replace("/bundles/source-data-07", "/bundles/source-data-08")
assert REMOTE.count("request=json.loads(header);manifest=request['manifest']") == 1
REMOTE = REMOTE.replace("request=json.loads(header);manifest=request['manifest']",
    "request=json.loads(header);manifest=request['manifest']\n"
    "assert hashlib.sha256((json.dumps(manifest,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)+'\\n').encode()).hexdigest()=='" + MANIFEST_SHA + "'\n"
    "assert manifest['archive_sha256']=='" + ARCHIVE_SHA + "' and manifest['archive_bytes']==10257469\n"
    "assert manifest['expanded_bytes']==108048497\n"
    "assert manifest['training_controller_sha256']=='" + TRAINER_SHA + "'")


def main():
    ast.parse(REMOTE, feature_version=(3, 6))
    seal_raw = (BUNDLE / "local-seal.json").read_bytes()
    assert hashlib.sha256(seal_raw).hexdigest() == SEAL_SHA
    seal = json.loads(seal_raw)
    assert seal["status"] == "SEALED"
    actual_raw = (BUNDLE / "actual-completion.json").read_bytes()
    assert hashlib.sha256(actual_raw).hexdigest() == seal["actual_completion"]["sha256"]
    actual = json.loads(actual_raw)
    assert actual["actual_exit_code"] == 0 and actual["completed"] is True
    assert actual["completion_chunk"] == "8e6ac2"
    manifest_raw = (BUNDLE / "manifest.json").read_bytes()
    assert hashlib.sha256(manifest_raw).hexdigest() == MANIFEST_SHA
    manifest = json.loads(manifest_raw)
    old_raw = (HERE / "p6-source-bundle-06/manifest.json").read_bytes()
    assert hashlib.sha256(old_raw).hexdigest() == PARENT_SHA
    old = json.loads(old_raw)
    assert len(manifest["files"]) == manifest["file_count"] == 1206
    assert set(manifest["files"]) == set(old["files"])
    assert {name for name in old["files"] if old["files"][name] != manifest["files"][name]} == {
        "output/p6-prototype/remote_training_pilot.py"}
    assert manifest["training_controller_sha256"] == TRAINER_SHA
    archive = (BUNDLE / "source-data.tar.gz").read_bytes()
    assert len(archive) == manifest["archive_bytes"] == 10257469
    assert hashlib.sha256(archive).hexdigest() == manifest["archive_sha256"] == ARCHIVE_SHA
    OUT.mkdir(exist_ok=False)
    request = {"authority": "HYDRA_EXPERIMENT_AUTHORITY.md",
        "directory": CAMPAIGN + "/bundles/source-data-08", "manifest": manifest,
        "local_manifest_sha256": MANIFEST_SHA, "local_seal_sha256": SEAL_SHA,
        "purpose": "One isolated canonical-JSON post-save comparison correction for a new4B run. The other1205source files, all plans/data/objectives/providers, failed1.7job and its saved artifact remain unchanged.",
        "automatic_retry": False}
    (OUT / "request.json").write_text(json.dumps(request, indent=2) + "\n")
    (OUT / "remote-script.py").write_text(REMOTE)
    started = time.monotonic()
    result = run_ssh(SSH + ["python3 -c " + shlex.quote(REMOTE)],
        input=json.dumps(request).encode() + b"\n" + archive,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=170,
        directory=OUT, phase="upload")
    (OUT / "stdout.json").write_bytes(result.stdout)
    (OUT / "stderr.txt").write_bytes(result.stderr)
    receipt = {"actual_ssh_exit_code": result.returncode, "elapsed_seconds": time.monotonic() - started,
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
