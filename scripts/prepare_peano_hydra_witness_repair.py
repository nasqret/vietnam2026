#!/usr/bin/env python3
"""Plan, build, or audit the separate CPU-only witness correction.

The default only declares the plan. Every operation uses an owned bounded
child; no mode loads weights, trains, evaluates a model, or submits a job.
Historical preparation auditing checks bytes and coverage, not native replay.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = Path(__file__).resolve()
RUN_SCHEMA = "peano-hydra-witness-repair-run-v1"


def _runtime():
    path = ROOT / "training/peano_hydra/review_runtime.py"
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), "rb") as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_size > 2 * 1024**2:
            raise ValueError("guard source is not a bounded regular file")
        raw = stream.read(2 * 1024**2 + 1)
        after = os.fstat(stream.fileno())
    if (len(raw) != before.st_size or
        (before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) !=
        (after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns)):
        raise ValueError("guard source changed while reading")
    module = types.ModuleType("_witness_repair_runtime")
    module.__file__ = str(path)
    module.__loaded_source_sha256__ = hashlib.sha256(raw).hexdigest()
    sys.modules[module.__name__] = module
    exec(compile(raw, str(path), "exec"), module.__dict__)
    return module


def _raw(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False,
                      separators=(",", ":")).encode()


def _fresh_file(path: Path) -> Path:
    path = path.absolute()
    if (any(part == ".." for part in path.parts) or path.exists() or path.is_symlink()
        or any(parent.is_symlink() for parent in path.parents)):
        raise ValueError("report requires a fresh file without symlink ancestors")
    return path


def _directory_identity(path: Path) -> tuple[int, int]:
    if ".." in path.parts:
        raise ValueError("protected inputs require existing directories reached by direct paths")
    identity = None
    for component in (path, *path.parents):
        try:
            value = component.lstat()
        except (FileNotFoundError, NotADirectoryError) as error:
            raise ValueError("protected inputs require existing directories reached by direct paths") from error
        if not stat.S_ISDIR(value.st_mode):
            raise ValueError("protected inputs require existing directories reached by direct paths without symlinks")
        if component == path:
            identity = (value.st_dev, value.st_ino)
    assert identity is not None
    return identity


def _outside_protected(path: Path, protected: tuple[tuple[Path, tuple[int, int]], ...]) -> None:
    identities = set()
    for directory, identity in protected:
        if _directory_identity(directory) != identity:
            raise ValueError("protected input directory changed during the operation")
        identities.add(identity)
        if path == directory or directory in path.parents:
            raise ValueError("receipt must stay outside both read-only inputs and the immutable fixture directory")
    for ancestor in path.parents:
        try:
            value = ancestor.lstat()
        except FileNotFoundError:
            continue
        if not stat.S_ISDIR(value.st_mode):
            raise ValueError("report ancestors must be direct directories")
        if (value.st_dev, value.st_ino) in identities:
            raise ValueError("receipt must stay outside both read-only inputs and the immutable fixture directory")


def _write(path: Path, value: dict, *, protected: tuple[tuple[Path, tuple[int, int]], ...] = ()) -> None:
    path = _fresh_file(path)
    _outside_protected(path, protected)
    raw = (json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False, indent=2) + "\n").encode()
    if len(raw) > 4 * 1024**2:
        raise ValueError("run receipt exceeds byte bound")
    path.parent.mkdir(parents=True, exist_ok=True)
    _fresh_file(path)
    _outside_protected(path, protected)
    with path.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def _worker() -> int:
    import resource

    soft, hard = resource.getrlimit(resource.RLIMIT_CPU)
    if (type(soft) is not int or type(hard) is not int or (soft, hard) != (30, 31)
        or not sys.dont_write_bytecode or sys.pycache_prefix != "/dev/null"):
        raise ValueError("worker requires the exact inherited 30/31 CPU limits and source-only bytecode barrier")
    if any(name in sys.modules for name in ("torch", "transformers", "peft")):
        raise ValueError("witness worker must remain model-free")
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "peano-lab/py"))
    import peano_lab
    if Path(peano_lab.__file__).resolve() != ROOT / "peano-lab/py/peano_lab/__init__.py":
        raise ValueError("worker imported a different native proof library")
    from training.peano_hydra import witness_repair as repair

    raw = sys.stdin.buffer.read(32769)
    if len(raw) > 32768:
        raise ValueError("worker request exceeds byte bound")
    request = repair._decode(raw)
    if set(request) != {"mode", "output_dir", "preparation_dir", "source_dir", "expected_manifest_sha256"}:
        raise ValueError("worker request has unexpected fields")
    if request["mode"] == "plan":
        result = repair.build_witness_repair_plan()
    elif request["mode"] == "build":
        output = repair._directory(Path(request["output_dir"]), fresh=True)
        source = repair.build_witness_repair_source()
        repair.publish_witness_repair_source(source, output)
        result = {"schema": repair.SOURCE_SCHEMA, "status": "published-checked-corrective-fixture",
                  "output_directory": str(output), "route_count": source.manifest["route_count"],
                  "transition_count": source.manifest["transition_count"],
                  "split_route_counts": source.manifest["split_route_counts"],
                  "split_transition_counts": source.manifest["split_transition_counts"],
                  "plan_sha256": source.plan["plan_sha256"],
                  "source_identity": source.plan["source_identity"],
                  "manifest_sha256": hashlib.sha256(source.payloads["manifest.json"]).hexdigest(),
                  "coverage_sha256": source.manifest["coverage_sha256"],
                  "publication_recheck": "same-bounded-worker; fresh-native-sessions",
                  "publication_route_replays": 16, "independent_process_verification": False,
                  "claims": source.manifest["claims"]}
    elif request["mode"] == "audit":
        result = repair.audit_witness_coverage(Path(request["preparation_dir"]),
                    source_directory=Path(request["source_dir"]),
                    expected_manifest_sha256=request["expected_manifest_sha256"])
    else:
        raise ValueError("unknown witness worker mode")
    if any(name in sys.modules for name in ("torch", "transformers", "peft")):
        raise ValueError("witness operation imported a model framework")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, allow_nan=False))
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    modes = result.add_mutually_exclusive_group()
    modes.add_argument("--plan", action="store_true", help="declare the fixed fixtures without proving them (default)")
    modes.add_argument("--build", action="store_true", help="check and publish only the small corrective fixture")
    modes.add_argument("--audit-preparation", type=Path, metavar="DIRECTORY", help="partial hash/coverage audit, no corpus replay")
    modes.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    result.add_argument("--output-dir", type=Path, help="fresh fixture directory; required by --build")
    result.add_argument("--source-dir", type=Path, help="exact original source directory; required by --audit-preparation")
    result.add_argument("--expected-manifest-sha256", help="optional independently obtained raw preparation-manifest pin")
    result.add_argument("--output", type=Path, help="optional fresh JSON run/guard receipt; never overwrites")
    return result


def main(argv: list[str] | None = None) -> int:
    arguments = parser().parse_args(argv)
    if arguments.worker:
        return _worker()
    if arguments.build != (arguments.output_dir is not None):
        raise ValueError("--build and --output-dir must be supplied together")
    if bool(arguments.audit_preparation) != (arguments.source_dir is not None):
        raise ValueError("--audit-preparation requires an explicit --source-dir; other modes forbid it")
    if arguments.expected_manifest_sha256 is not None and arguments.audit_preparation is None:
        raise ValueError("manifest pin applies only to --audit-preparation")
    protected = ()
    if arguments.audit_preparation is not None:
        input_directories = (arguments.audit_preparation.absolute(), arguments.source_dir.absolute())
        protected = tuple((directory, _directory_identity(directory)) for directory in input_directories)
    output = _fresh_file(arguments.output) if arguments.output is not None else None
    if output is not None:
        _outside_protected(output, protected)
    if arguments.output_dir is not None:
        target = arguments.output_dir.absolute()
        if target.exists() or target.is_symlink() or any(p.is_symlink() for p in target.parents):
            raise ValueError("fixture output must be fresh and have no symlink ancestors")
        if output is not None and (output == target or target in output.parents):
            raise ValueError("run receipt must stay outside the immutable fixture directory")
    mode = "build" if arguments.build else "audit" if arguments.audit_preparation is not None else "plan"
    request = {"mode": mode,
               "output_dir": str(arguments.output_dir.absolute()) if arguments.output_dir else None,
               "preparation_dir": str(arguments.audit_preparation.absolute()) if arguments.audit_preparation else None,
               "source_dir": str(arguments.source_dir.absolute()) if arguments.source_dir else None,
               "expected_manifest_sha256": arguments.expected_manifest_sha256}
    runtime = _runtime()
    limits = runtime.ProcessLimits(cpu_seconds=30, wall_seconds=45, rss_bytes=1024**3, output_bytes=2 * 1024**2)
    command = (sys.executable, "-B", "-X", "pycache_prefix=/dev/null", str(SCRIPT), "--worker")
    record = runtime.run_bounded(command, cwd=ROOT, limits=limits, input_bytes=_raw(request))
    runtime.validate_process_record(record, command=command, limits=limits, input_bytes=_raw(request))
    success = record["reason"] == "exited" and record["returncode"] == 0
    result = {"schema": RUN_SCHEMA, "mode": mode, "status": "completed" if success else "failed",
              "process": record, "model_generation_performed": False, "gpu_used": False,
              "model_weights_repaired": False, "training_authorized": False,
              "import_scope": "source-bytecode barrier and checked native package path; normal configured dependencies, not transitive-import authentication",
              "guard_source_sha256": runtime.__loaded_source_sha256__}
    if success:
        runtime.validate_process_record(record, command=command, limits=limits, input_bytes=_raw(request), success_codes=(0,))
        result["evidence"] = json.loads(record["stdout"])
        if (result["evidence"]["source_identity"]["files"]["training/peano_hydra/review_runtime.py"]
            != runtime.__loaded_source_sha256__):
            raise ValueError("worker source inventory differs from the guard source actually executed")
    if output is not None:
        if arguments.output_dir is not None and target.exists():
            protected += ((target, _directory_identity(target)),)
        _write(output, result, protected=protected)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, allow_nan=False))
    return 0 if success else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, TypeError) as error:
        print(f"Witness repair failed: {error}", file=sys.stderr)
        raise SystemExit(1)
