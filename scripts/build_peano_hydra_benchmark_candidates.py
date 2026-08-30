#!/usr/bin/env python3
"""Build/replay one bounded evaluation-only candidate bundle into a fresh path.

This does not train, admit a dataset, request GPU time, claim independent
ownership, or seal a benchmark. Every worker attempt receives a fresh process
receipt, and declarations/partial native evidence survive failures.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import traceback


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _encode(record: object) -> bytes:
    return json.dumps(record, sort_keys=True, ensure_ascii=False, allow_nan=False,
                      separators=(",", ":")).encode("utf-8") + b"\n"


def _write(path: Path, record: object) -> dict[str, object]:
    raw = _encode(record)
    with path.open("xb") as stream:
        stream.write(raw)
        stream.flush()
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def _safe_directory(path: Path, *, fresh: bool) -> Path:
    path = path.absolute()
    if ".." in path.parts or path.is_symlink() or any(parent.is_symlink() for parent in path.parents):
        raise ValueError("candidate output must have real directory ancestors")
    if not path.parent.is_dir() or (path.exists() if fresh else not path.is_dir()):
        raise ValueError("fresh candidate output required under an existing directory" if fresh else "candidate directory missing")
    return path


def _worker(request: dict[str, object]) -> None:
    sys.path[:0] = [str(ROOT / "peano-lab/py")]
    from training.peano_hydra import frontier_benchmark_candidates as candidate
    from training.peano_hydra.epoch import freeze_epoch
    if set(request) != {"mode", "output", "bundle"} or request["mode"] not in {"build", "verify"}:
        raise ValueError("unexpected candidate worker request")
    output = _safe_directory(Path(request["output"]), fresh=False)
    artifacts = {}
    proof_directory = output / "proofs"
    proof_directory.mkdir()
    def observe(kind, record):
        if kind == "plan":
            name = "plan.json"
        elif kind == "proof":
            name = f"proofs/{record['name']}.json"
        elif kind == "failure":
            name = f"proofs/FAILED-{record['route']['name']}.json"
        else:
            raise ValueError("unexpected candidate observation")
        artifacts[name] = _write(output / name, record)
    epoch = freeze_epoch(ROOT)
    bundle = candidate.build_candidate_bundle(epoch, observe=observe)
    artifacts["bundle.json"] = _write(output / "bundle.json", bundle)
    manifest = candidate.build_candidate_manifest(bundle, artifacts=artifacts)
    _write(output / "manifest.json", manifest)
    prior = None
    if request["mode"] == "verify":
        path = Path(request["bundle"])
        _safe_directory(path.parent, fresh=False)
        if path.name != "bundle.json" or path.is_symlink():
            raise ValueError("verification requires the exact saved regular bundle.json")
        raw = candidate._native()._read(path, maximum=candidate.MAX_BUNDLE_BYTES)
        saved = candidate._native()._decode(raw)
        if candidate._canonical(saved) != candidate._canonical(bundle):
            raise ValueError("independent native replay differs from the saved candidate bundle")
        prior = {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
    forbidden = sorted(name for name in sys.modules if name.split(".")[0] in {"torch", "transformers", "peft", "tokenizers"})
    if forbidden:
        raise RuntimeError("candidate worker unexpectedly loaded model code")
    result = {"schema": "peano-hydra-frontier-benchmark-candidate-worker-v1", "status": "verified",
              "mode": request["mode"], "manifest_sha256": manifest["manifest_sha256"],
              "bundle_sha256": bundle["bundle_sha256"], "verified_route_count": bundle["verified_route_count"],
              "verified_decisions": bundle["verified_decisions"], "primary_goal_count": len(bundle["primary_goals"]),
              "reserved_goal_count": len(bundle["reserved_goals"]), "prior_bundle": prior,
              "forbidden_model_modules": forbidden, "claims": manifest["claims"]}
    _write(output / "verification.json", result)
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("build", "verify"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--bundle", type=Path)
    args = parser.parse_args()
    if (args.mode == "verify") != (args.bundle is not None):
        parser.error("verify requires --bundle; build forbids it")
    output = _safe_directory(args.output, fresh=True)
    request = {"mode": args.mode, "output": str(output),
               "bundle": str(args.bundle.absolute()) if args.bundle is not None else None}
    payload = _encode(request)
    output.mkdir()
    _write(output / "invocation.json", request)
    from training.peano_hydra.review_runtime import ProcessLimits, run_bounded, validate_process_record
    limits = ProcessLimits(wall_seconds=150, cpu_seconds=120, rss_bytes=1024**3, output_bytes=128 * 1024)
    command = (sys.executable, "-I", "-B", "-X", "pycache_prefix=/dev/null", str(Path(__file__).resolve()), "--worker")
    source_names = ("training/peano_hydra/frontier_benchmark_candidates.py",
                    "scripts/build_peano_hydra_benchmark_candidates.py", "training/peano_hydra/review_runtime.py",
                    "scripts/hydra_bounded_exec.py")
    before = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in source_names}
    try:
        process = run_bounded(command, cwd=ROOT, limits=limits, input_bytes=payload)
        after = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in source_names}
        receipt = {"schema": "peano-hydra-frontier-benchmark-candidate-process-v1", "process": process,
                   "source_files_before": before, "source_files_after": after, "request": request,
                   "source_files_unchanged": before == after, "status": "failed"}
        try:
            validate_process_record(process, command=command, limits=limits, input_bytes=payload, success_codes=(0,))
            if before != after:
                raise ValueError("candidate worker source changed during execution")
            record = json.loads(process["stdout"])
            if record.get("status") != "verified" or record.get("verified_route_count") != 64:
                raise ValueError("candidate worker returned incomplete verification")
            receipt["status"] = "verified"
        except (ValueError, KeyError) as error:
            receipt["validation_error"] = type(error).__name__ + ": " + str(error)
        _write(output / "process.json", receipt)
        print(json.dumps({"status": receipt["status"], "output": str(output),
                          "reason": process["reason"], "returncode": process["returncode"],
                          "resources": process["resources"]}, sort_keys=True))
        return 0 if receipt["status"] == "verified" else 1
    except BaseException as error:
        if not (output / "process.json").exists():
            _write(output / "process.json", {"schema": "peano-hydra-frontier-benchmark-candidate-process-v1",
                "status": "controller_failed", "request": request, "source_files_before": before,
                "error": type(error).__name__ + ": " + str(error), "traceback": traceback.format_exc()[-16384:]})
        raise


if __name__ == "__main__":
    if sys.argv[1:] == ["--worker"]:
        try:
            raw = sys.stdin.buffer.read(16385)
            if len(raw) > 16384:
                raise ValueError("candidate worker input exceeds bound")
            _worker(json.loads(raw))
        except BaseException:
            traceback.print_exc()
            raise SystemExit(1)
    else:
        raise SystemExit(main())
