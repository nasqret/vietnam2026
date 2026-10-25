"""One local admission of the actual transfer package, no tensor/model work."""
from pathlib import Path
import hashlib
import json
import os
import resource
import signal
import sys
import tarfile
import time

HERE = Path(__file__).resolve().parent / "p6-source-bundle-03"
SOURCE = HERE / "source"
MANIFEST = json.loads((HERE / "manifest.json").read_bytes())


def main():
    SOURCE.mkdir(exist_ok=False)
    archive = HERE / "source-data.tar.gz"
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == MANIFEST["archive_sha256"]
    with tarfile.open(archive, "r:gz") as tar:
        members = tar.getmembers()
        assert len(members) == MANIFEST["file_count"]
        for member in members:
            pin = MANIFEST["files"][member.name]
            path = Path(member.name)
            assert member.isfile() and not path.is_absolute() and ".." not in path.parts
            assert member.size == pin["bytes"]
            raw = tar.extractfile(member).read()
            assert hashlib.sha256(raw).hexdigest() == pin["sha256"]
            target = SOURCE / path
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as stream:
                stream.write(raw)
    os.chdir(SOURCE)
    sys.path[:0] = [str(SOURCE / "hydra-playground"),
                   str(SOURCE / "hydra-playground/native-v7"),
                   str(SOURCE / "hydra-playground/training-v5")]
    resource.setrlimit(resource.RLIMIT_CPU, (90, 90))
    signal.signal(signal.SIGALRM, lambda signum, frame: (_ for _ in ()).throw(TimeoutError("Admission ceiling")))
    signal.alarm(120)
    started = time.monotonic()
    record = {"schema": "hydra-p6-transfer-admission-v1", "archive_sha256": MANIFEST["archive_sha256"],
              "cpu_seconds_ceiling": 90, "wall_seconds_ceiling": 120,
              "model_calls": 0, "native_proof_replays": 0, "gpu_allocations": 0,
              "automatic_retry": False, "completed": False}
    try:
        # Match the remote smoke's engine-before-admission import order.
        import proof_planner
        from hydra_training_v5.decision_pilot import prepare
        plan = prepare(SOURCE / "hydra-playground/training-v5/configs/qwen3_4b_decisions_v2_pilot.toml",
            dataset_manifest="output/hydra-implementation-2026-09-04/decisions-v2-01/manifest.json",
            dataset_sha256=MANIFEST["dataset_manifest_sha256"])
        (HERE / "prepared-pilot.json").write_text(json.dumps(plan.record, indent=2) + "\n")
        record.update(completed=True, training_rows=plan.record["training_rows"],
                      expected_optimizer_steps=plan.record["expected_optimizer_steps"],
                      plan_sha256=plan.record["plan_sha256"])
    except BaseException as error:
        record["error"] = {"type": type(error).__name__, "detail": str(error)[:1000]}
        raise
    finally:
        signal.alarm(0)
        record["elapsed_seconds"] = time.monotonic() - started
        record["peak_rss_bytes_macos"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        (HERE / "admission.json").write_text(json.dumps(record, indent=2) + "\n")
        print(json.dumps(record), flush=True)


if __name__ == "__main__":
    main()
