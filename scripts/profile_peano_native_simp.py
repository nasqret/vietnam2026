#!/usr/bin/env python3
"""Profile one explicitly supplied native simp diagnostic, without any model.

Read-only by default: bounded child-process results are printed as JSON.
A diagnostic tactic path is not autonomous search or a completed benchmark.
"""
from __future__ import annotations

import argparse
import cProfile
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import pstats
import resource
import stat
import sys
import time


_MAX_SOURCE_FILE_BYTES = 2 * 1024**2
_MAX_NATIVE_SOURCE_BYTES = 8 * 1024**2
_MAX_NATIVE_FILES = 128
_MAX_NATIVE_ENTRIES = 256
_MAX_NATIVE_DIRECTORIES = 32


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _directory(path):
    path = Path(path).absolute()
    if ".." in path.parts or len(path.parts) > 64 or len(str(path).encode()) > 4096:
        raise ValueError("source directory must have a bounded lexical path")
    access = getattr(os, "O_PATH", os.O_RDONLY) if sys.platform == "linux" else os.O_RDONLY
    descriptor = os.open(path.anchor, access | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for index, part in enumerate(path.parts[1:], 1):
            flags = os.O_RDONLY if index == len(path.parts) - 1 else access
            child = os.open(part, flags | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        result, descriptor = descriptor, -1
        return result
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def _read_at(parent, name):
    if not name or "/" in name or name in {".", ".."}:
        raise ValueError("source filename must be one component")
    descriptor = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or before.st_size > _MAX_SOURCE_FILE_BYTES:
            raise ValueError("source must be a bounded regular file")
        chunks, size = [], 0
        while True:
            block = os.read(descriptor, min(65536, _MAX_SOURCE_FILE_BYTES + 1 - size))
            if not block:
                break
            size += len(block)
            if size > _MAX_SOURCE_FILE_BYTES:
                raise ValueError("source grew beyond its byte bound")
            chunks.append(block)
        after = os.fstat(descriptor)
        current = os.stat(name, dir_fd=parent, follow_symlinks=False)
        fields = ("st_dev", "st_ino", "st_nlink", "st_size", "st_mtime_ns", "st_ctime_ns")
        if size != before.st_size or any(getattr(before, f) != getattr(after, f)
                                        or getattr(before, f) != getattr(current, f) for f in fields):
            raise ValueError("source changed while reading")
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _source_bytes(path):
    parent = _directory(path.parent)
    try:
        return _read_at(parent, path.name)
    finally:
        os.close(parent)


def _inventory(root):
    result = {}
    total_bytes = entries = directories = 0

    def visit(parent, relative, depth):
        nonlocal total_bytes, entries, directories
        directories += 1
        if directories > _MAX_NATIVE_DIRECTORIES or depth > 8:
            raise ValueError("native source directory inventory exceeds diagnostic bound")
        with os.scandir(parent) as listing:
            for entry in listing:
                entries += 1
                if entries > _MAX_NATIVE_ENTRIES or len(entry.name.encode()) > 256:
                    raise ValueError("native source entry inventory exceeds diagnostic bound")
                observed = entry.stat(follow_symlinks=False)
                if stat.S_ISLNK(observed.st_mode):
                    raise ValueError("native source cannot contain symlinks")
                name = relative / entry.name
                if stat.S_ISDIR(observed.st_mode):
                    if entry.name == "__pycache__":
                        continue
                    child = os.open(entry.name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
                    try:
                        visit(child, name, depth + 1)
                    finally:
                        os.close(child)
                elif entry.name.endswith(".py"):
                    if len(result) >= _MAX_NATIVE_FILES:
                        raise ValueError("native source file inventory exceeds diagnostic bound")
                    raw = _read_at(parent, entry.name)
                    total_bytes += len(raw)
                    if total_bytes > _MAX_NATIVE_SOURCE_BYTES:
                        raise ValueError("native source bytes exceed diagnostic bound")
                    result[str(name)] = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}

    for package in ("engine", "kernel"):
        relative = Path("peano-lab/py/peano_lab") / package
        parent = _directory(root / relative)
        try:
            visit(parent, relative, 0)
        finally:
            os.close(parent)
    if not result or "peano-lab/py/peano_lab/engine/rewrite.py" not in result:
        raise ValueError("source root has no native engine")
    return dict(sorted(result.items()))


def _expected_started(coefficient, case, rewrite_sha256):
    variable = "n" if case == "direct_simp" else "0"
    before = [f"({variable} + {coefficient}) · 2 = {variable} · 2 + {2 * coefficient}"]
    if case == "induction_zero_simp":
        before.append(f"(S n + {coefficient}) · 2 = S n · 2 + {2 * coefficient}")
    return {"stage": "started", "source": f"forall n. (n + {coefficient}) * 2 = n * 2 + {2 * coefficient}",
            "case": case, "commands": ["intro n" if case == "direct_simp" else "induction n", "simp"],
            "goals_before": before, "rewrite_sha256": rewrite_sha256}


def _require_worker_cpu_limit():
    soft, hard = resource.getrlimit(resource.RLIMIT_CPU)
    if type(soft) is not int or not 2 <= soft <= 10 or hard != soft + 1:
        raise ValueError("internal native worker requires its inherited bounded CPU reservation")


def _worker(root, coefficient, case):
    _require_worker_cpu_limit()
    sys.path.insert(0, str(root / "peano-lab/py"))
    from peano_lab.engine.state import start
    from peano_lab.engine.tactics import TacticError, apply_tactic
    from peano_lab.engine import rewrite
    from peano_lab.kernel.formulas import parse_formula, pretty_formula

    source = f"forall n. (n + {coefficient}) * 2 = n * 2 + {2 * coefficient}"
    target = parse_formula(source)
    commands = ["intro n"] if case == "direct_simp" else ["induction n"]
    state = start(target)
    for command in commands:
        name, argument = command.split(" ", 1)
        state = apply_tactic(state, name, argument)
    rewrite_source = Path(rewrite.__file__).read_bytes()
    before = [pretty_formula(goal.target, list(goal.variables)) for goal in state.goals]
    print(_json({"stage": "started", "source": source, "case": case, "commands": commands + ["simp"],
                 "goals_before": before, "rewrite_sha256": hashlib.sha256(rewrite_source).hexdigest()}), flush=True)
    profile = cProfile.Profile()
    error = None
    cpu, wall = time.process_time(), time.monotonic()
    profile.enable()
    try:
        result = apply_tactic(state, "simp")
    except TacticError as failure:
        error = {"type": type(failure).__name__, "message": str(failure)}
        result = state
    finally:
        profile.disable()
    cpu, wall = time.process_time() - cpu, time.monotonic() - wall
    statistics = pstats.Stats(profile)
    functions = []
    for (filename, line, name), (primitive, total, internal, cumulative, _callers) in statistics.stats.items():
        try:
            filename = str(Path(filename).relative_to(root))
        except ValueError:
            filename = Path(filename).name
        functions.append({"file": filename, "line": line, "function": name, "primitive_calls": primitive,
                          "total_calls": total, "internal_seconds": internal, "cumulative_seconds": cumulative})
    functions.sort(key=lambda item: (-item["cumulative_seconds"], item["file"], item["line"], item["function"]))
    assert not {"torch", "transformers", "peft"} & set(sys.modules)
    print(_json({"stage": "finished", "profiled_tactic_cpu_seconds": cpu,
                 "profiled_tactic_wall_seconds": wall, "tactic_error": error,
                 "goals_after": [pretty_formula(goal.target, list(goal.variables)) for goal in result.goals],
                 "goal_closed": result.is_done(), "autonomous_proof_claimed": False,
                 "top_cumulative_functions": functions[:25],
                 "rewrite_functions": [item for item in functions
                                       if item["file"] == "peano-lab/py/peano_lab/engine/rewrite.py"],
                 "model_frameworks_imported": False}), flush=True)
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--source-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--coefficient", type=int, choices=range(4, 13), default=8)
    parser.add_argument("--case", choices=("direct_simp", "induction_zero_simp"), default="direct_simp")
    parser.add_argument("--cpu-seconds", type=int, choices=range(2, 11), default=5)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    root = args.source_root.absolute()
    directory = _directory(root)
    os.close(directory)
    if args.worker:
        return _worker(root, args.coefficient, args.case)
    before = _inventory(root)
    runtime_path = root / "training/peano_hydra/review_runtime.py"
    guard_path = root / "scripts/hydra_bounded_exec.py"
    script_path = Path(__file__).absolute()
    runtime_raw = _source_bytes(runtime_path)
    guard_raw = _source_bytes(guard_path)
    script_raw = _source_bytes(script_path)
    spec = importlib.util.spec_from_file_location("_native_simp_profile_guard", runtime_path)
    runtime = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = runtime
    # Execute the captured Python source, not a possibly stale .pyc file.
    exec(compile(runtime_raw, str(runtime_path), "exec"), runtime.__dict__)
    limits = runtime.ProcessLimits(cpu_seconds=args.cpu_seconds, wall_seconds=args.cpu_seconds + 5,
                                   rss_bytes=512 * 1024**2, output_bytes=128 * 1024)
    command = (sys.executable, "-I", "-B", "-X", "pycache_prefix=/dev/null", str(script_path), "--worker",
               "--source-root", str(root), "--coefficient", str(args.coefficient), "--case", args.case)
    process = runtime.run_bounded(command, cwd=root, limits=limits)
    if (_inventory(root) != before or _source_bytes(runtime_path) != runtime_raw
            or _source_bytes(guard_path) != guard_raw or _source_bytes(script_path) != script_raw):
        raise ValueError("source changed during diagnostic")
    rows = [json.loads(line) for line in process["stdout"].splitlines()]
    if len(rows) > 2 or any(type(row) is not dict for row in rows):
        raise ValueError("unexpected diagnostic output")
    expected = _expected_started(args.coefficient, args.case,
                                 before["peano-lab/py/peano_lab/engine/rewrite.py"]["sha256"])
    if rows and rows[0] != expected:
        raise ValueError("started diagnostic does not match its exact request/source")
    complete = process["reason"] == "exited" and process["returncode"] == 0
    if complete and (len(rows) != 2 or [row.get("stage") for row in rows] != ["started", "finished"]):
        raise ValueError("successful worker did not finish the exact diagnostic")
    if not complete and (len(rows) > 1 or rows and rows[0].get("stage") != "started"):
        raise ValueError("incomplete worker published unexpected completed output")
    result = {
        "schema": "peano-native-simp-bounded-profile-v1", "source_root": str(root),
        "native_source_files": before,
        "native_source_files_sha256": hashlib.sha256(_json(before).encode()).hexdigest(),
        "guard_source_sha256": hashlib.sha256(runtime_raw).hexdigest(),
        "os_guard_source_sha256": hashlib.sha256(guard_raw).hexdigest(),
        "profiler_source_sha256": hashlib.sha256(script_raw).hexdigest(),
        "standard_bytecode_cache_bypassed": True,
        "python_cache_prefix": "/dev/null",
        "bytecode_writes_disabled": True,
        "source_coverage": "enumerated native engine/kernel Python sources and diagnostic guards; not all transitive imports or hardware attestation",
        "case": args.case, "coefficient": args.coefficient, "completed": complete,
        "observations": rows, "process": process, "gpu_used": False, "model_generation_performed": False,
        "claim_boundary": "Engineer-supplied single-tactic diagnostic; not a new model score, repaired checkpoint, proof discovery or end-to-end GPU speedup. Timings include profiling overhead.",
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError) as error:
        print(f"Native simp profile failed: {error}", file=sys.stderr)
        raise SystemExit(2)
