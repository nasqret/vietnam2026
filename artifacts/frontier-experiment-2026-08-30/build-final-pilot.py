"""Build the final CPU candidate once from the new immutable execution source."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
from datetime import datetime, timezone

ROOT = Path("/Users/bnaskrecki/codex/peano/_deploy/hydra-frontier-execution-20260830")
ARCHIVE = Path(__file__).absolute().parent
OUTPUT = ROOT / "_deploy/hydra-frontier-candidate-v1"
BASELINE = Path("/Users/bnaskrecki/codex/peano/_deploy/hydra-search-v2-build-20260829/_deploy/hydra-search-v2/origin-source/_deploy/hydra-corrective-v2/source")
COMMAND = ["/opt/homebrew/bin/python3.11", "-I", "-B", "-X", "pycache_prefix=/dev/null",
           "scripts/prepare_peano_hydra_scaling.py", "--build", "--profile", "pilot", "--output", str(OUTPUT),
           "--baseline-source", str(BASELINE), "--expected-baseline-source-sha256",
           "3e7fccb43804f5272a61282005c961b492ef891dbb37998f1c4a81ee9dfb4ef4"]


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    paths = {key: ARCHIVE / ("pilot-build-final-01." + suffix) for key, suffix in
             (("stdout", "stdout.log"), ("stderr", "stderr.log"), ("invocation", "json"))}
    if OUTPUT.exists() or any(path.exists() for path in paths.values()):
        raise SystemExit("fresh output and invocation paths required; no retries or overwrite")
    environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    environment.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL="/dev/null", GIT_NO_REPLACE_OBJECTS="1",
                       GIT_OPTIONAL_LOCKS="0", GIT_NO_LAZY_FETCH="1", PYTHONDONTWRITEBYTECODE="1",
                       PYTHONPYCACHEPREFIX="/dev/null")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, env=environment, text=True).strip()
    if commit != "278d80552ab55b080365ddbae0d1d49be2fdc396" or subprocess.check_output(
            ["git", "status", "--porcelain=v1", "--untracked-files=all"], cwd=ROOT, env=environment):
        raise SystemExit("final execution source is not the exact clean frozen commit")
    source = json.loads((ROOT / "_deploy/frontier-origin-source.json").read_bytes())
    before = {name: sha(ROOT / name) for name in source["files"]}
    for stage in ("train", "evaluate"):
        name = "slurm/peano_hydra_frontier_" + stage + ".sbatch"
        before[name] = sha(ROOT / name)
    started = datetime.now(timezone.utc).isoformat()
    with paths["stdout"].open("xb") as stdout, paths["stderr"].open("xb") as stderr:
        result = subprocess.run(COMMAND, cwd=ROOT, env=environment, stdout=stdout, stderr=stderr, check=False)
    after = {name: sha(ROOT / name) for name in before}
    ready_path = OUTPUT / "readiness.json"
    record = {"schema": "peano-hydra-frontier-final-pilot-invocation-v1", "command": COMMAND,
        "source_commit": commit, "source_manifest_sha256": sha(ROOT / "_deploy/frontier-origin-source.json"),
        "started_utc": started, "finished_utc": datetime.now(timezone.utc).isoformat(), "returncode": result.returncode,
        "native_worker_limits": {"cpu_seconds": 120, "wall_seconds": 180, "rss_bytes": 2 * 1024**3},
        "source_bytes_unchanged": before == after,
        "source_still_clean": not subprocess.check_output(["git", "status", "--porcelain=v1", "--untracked-files=all"], cwd=ROOT, env=environment),
        "output": str(OUTPUT), "readiness_raw_sha256": sha(ready_path) if ready_path.is_file() else None,
        "logs": {key: {"path": str(paths[key]), "bytes": paths[key].stat().st_size, "sha256": sha(paths[key])}
                 for key in ("stdout", "stderr")},
        "training_authorized": False, "model_training_performed": False, "gpu_jobs_started": 0}
    with paths["invocation"].open("xb") as stream:
        stream.write((json.dumps(record, sort_keys=True, indent=2) + "\n").encode())
    print(json.dumps(record, sort_keys=True), flush=True)
    raise SystemExit(0 if result.returncode == 0 and record["source_bytes_unchanged"] and record["source_still_clean"] else 2)


if __name__ == "__main__": main()
