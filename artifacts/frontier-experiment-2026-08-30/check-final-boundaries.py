"""Check the preserved real baseline and the current draft's closed GPU gate."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path("/Users/bnaskrecki/codex/peano/_deploy/hydra-frontier-execution-20260830")
OUT = Path(__file__).absolute().parent
OLD = Path("/Users/bnaskrecki/codex/peano/_deploy/hydra-search-v2-build-20260829/_deploy/hydra-search-v2")
sys.path[:0] = [str(ROOT), str(ROOT / "peano-lab/py")]
from training.peano_hydra import frontier_benchmark_run as run
from training.peano_hydra import origin_bridge as bridge


def save(path, value):
    raw = bridge._canonical(value) + b"\n"
    with path.open("xb") as stream: stream.write(raw)
    return hashlib.sha256(raw).hexdigest()


def main():
    draft_path, result_path = OUT / "evaluation-request-draft-01.json", OUT / "boundary-check-01.json"
    if draft_path.exists() or result_path.exists(): raise SystemExit("fresh outputs required")
    reference = json.loads((OLD / "origin/manifest.json").read_bytes())
    request = bridge._request(reference["reference"]["request"], {
        "source_root": str(OLD / "origin-source"), "source_manifest": str(OLD / "origin/source-manifest.json"),
        "adapter_manifest": str(OLD / "model/manifest.json")})
    assert request.adapter_manifest_sha256 == run.BASELINE_SHA
    receipt_sha = "9f3509835a2dffeabf7590af8347aad9a622342f5131a20e26eaf0faa40ab7d1"
    assert reference["reference"]["receipt_sha256"] == receipt_sha
    baseline = bridge.load_origin_receipt(OLD / "origin/origin-receipt.json",
                                         expected_receipt_sha256=receipt_sha, request=request)
    assert baseline.origin["origin_sha256"] == "84157795ceae439fc3f0440438d1e0a19e40975d1f37a80df4f43c08db0de5b5"
    draft = {"schema": run.SCHEMA, "status": "draft-pending-human-reference-review-and-production-preflight",
        "profile": "peano-hydra-frontier-v1", "run_id": "frontier-v1", "benchmark_manifest": None,
        "benchmark_audit": None, "benchmark_review": None, "cohorts": None, "admitted_inputs": None,
        "baseline": None, "candidate": None, "acceptance_protocol": None, "limits": run.LIMITS,
        "gpu_execution_authorized": False, "sealed_benchmark": False, "research_claim_eligible": False}
    draft["request_sha256"] = bridge._digest(draft)
    pin = save(draft_path, draft)
    command = [sys.executable, "-I", "-B", str(ROOT / "scripts/eval_peano_hydra_frontier_benchmark.py"),
               "--check", "--request", str(draft_path), "--expected-request-sha256", pin]
    check = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=15, check=False)
    assert check.returncode == 2 and "still a draft" in check.stderr and check.stdout == ""
    forbidden = [name for name in sys.modules if name.split(".")[0] in {"torch", "transformers", "peft", "tokenizers"}]
    assert not forbidden
    result = {"schema": "peano-hydra-frontier-final-boundary-check-v1", "status": "passed",
        "frozen_execution_commit": "278d80552ab55b080365ddbae0d1d49be2fdc396",
        "baseline": {"receipt_raw_sha256": receipt_sha, "origin_sha256": baseline.origin["origin_sha256"],
                     "adapter_manifest_sha256": request.adapter_manifest_sha256,
                     "check": "original receipt metadata and all pinned source/preparation/adapter bytes rechecked; no native replay"},
        "draft": {"path": str(draft_path), "raw_sha256": pin},
        "cli_guard": {"command": command, "returncode": check.returncode, "stdout": check.stdout, "stderr": check.stderr},
        "model_frameworks_imported": forbidden, "model_generation_performed": False,
        "proof_execution_performed": False, "gpu_jobs_started": 0, "new_human_review_created": False}
    receipt_pin = save(result_path, result)
    print(json.dumps({"status": result["status"], "baseline_origin": baseline.origin["origin_sha256"],
                      "draft_rejected_before_inputs_or_execution": True, "receipt_raw_sha256": receipt_pin}, sort_keys=True))


if __name__ == "__main__": main()
