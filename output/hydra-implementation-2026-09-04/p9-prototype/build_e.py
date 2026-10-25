"""Compile only the pinned E executable in a fresh, bounded local build tree.

No solver is launched and no make install target is used. The configuration
and compilation subprocesses have one owned group each and are killed on any
failure/timeout; build output and disk growth are bounded separately.
"""
from pathlib import Path
import hashlib
import json
import os
import resource
import shutil
import signal
import subprocess
import time


HERE = Path(__file__).resolve().parent
SOURCE_NAME = "eprover-2f87cc42aae7780f197398dca7e1bb092081f0ca"
SOURCE = HERE / "source-download-01/source" / SOURCE_NAME
OUTPUT = HERE / "e-build-01"
BUILD = OUTPUT / "source"
WALL = 180
DISK = 512 * 1024**2
LOG_LIMIT = 8 * 1024**2
LIBRARIES = ("CONTRIB", "BASICS", "INOUT", "TERMS", "ORDERINGS", "CLAUSES", "LEARN", "HEURISTICS", "CONTROL")


def pin(path):
    raw = path.read_bytes()
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def size_of_tree(path):
    total = 0
    for directory, _, files in os.walk(path, followlinks=False):
        for name in files:
            item = Path(directory) / name
            if not item.is_symlink():
                total += item.stat().st_size
                if total > DISK:
                    return total
    return total


def child_limits():
    # This preparation process has no threads/model imports.
    resource.setrlimit(resource.RLIMIT_CPU, (120, 120))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_FSIZE, (16 * 1024**2, 16 * 1024**2))
    resource.setrlimit(resource.RLIMIT_NOFILE, (128, 128))


def run(argv, label, deadline, records):
    started = time.monotonic()
    environment = {"PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "LANG": "C", "LC_ALL": "C",
                   "TMPDIR": str(OUTPUT / "tmp"), "CC": "/usr/bin/clang", "MAKEFLAGS": "-j1"}
    stdout = OUTPUT / (label + ".log")
    process = None
    reason = "process_exit"
    try:
        with stdout.open("xb") as stream:
            process = subprocess.Popen(argv, cwd=BUILD, env=environment, stdin=subprocess.DEVNULL,
                stdout=stream, stderr=subprocess.STDOUT, close_fds=True, start_new_session=True,
                preexec_fn=child_limits)
            while process.poll() is None:
                if time.monotonic() >= deadline:
                    reason = "build_wall_limit"
                    raise TimeoutError(reason)
                if stdout.stat().st_size > LOG_LIMIT or size_of_tree(OUTPUT) > DISK:
                    reason = "build_output_or_disk_limit"
                    raise ValueError(reason)
                time.sleep(0.2)
            if process.returncode != 0:
                raise RuntimeError(f"{label} ended with exit {process.returncode}; preserve the log.")
    finally:
        if process is not None:
            # The group was created by this exact Popen. A normal make waits
            # for its children; kill any remaining group member as well.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait(timeout=2)
            records.append({"argv": argv, "label": label, "exit_code": process.returncode,
                            "elapsed_seconds": time.monotonic() - started, "termination": reason,
                            "leader_reaped": True, "log": pin(stdout)})


def main():
    started = time.monotonic()
    OUTPUT.mkdir(exist_ok=False)
    (OUTPUT / "tmp").mkdir()
    downloaded = json.loads((HERE / "source-download-01/result.json").read_bytes())
    record = next(record for record in downloaded["sources"] if record["root"] == SOURCE_NAME)
    for name, descriptor in record["files"].items():
        if pin(SOURCE / name) != descriptor:
            raise ValueError("Pinned E source changed before the build.")
    shutil.copytree(SOURCE, BUILD, symlinks=False)
    commands = [["/bin/sh", "./configure"]]
    commands += [["/usr/bin/make", "-j1", "-C", name, "CC=/usr/bin/clang"] for name in LIBRARIES]
    commands += [["/usr/bin/make", "-j1", "-C", "PROVER", "eprover", "CC=/usr/bin/clang"]]
    plan = {"schema": "hydra-p9-e-build-plan-v1", "source": record["archive"],
            "commit": SOURCE_NAME.removeprefix("eprover-"), "commands": commands,
            "wall_seconds": WALL, "per_process_cpu_seconds": 120, "parallel_compilation_jobs": 1,
            "disk_bytes": DISK, "per_command_log_bytes": LOG_LIMIT,
            "make_install": False, "network": False, "solver_executions": 0}
    (OUTPUT / "plan.json").write_text(json.dumps(plan, indent=2) + "\n")
    records = []
    status, detail = "built-not-executed", None
    try:
        for index, command in enumerate(commands):
            run(command, f"command-{index:02d}", started + WALL, records)
        executable = pin(BUILD / "PROVER/eprover")
        if executable["bytes"] > 16 * 1024**2:
            raise ValueError("Compiled E executable exceeded its package bound.")
    except Exception as error:
        status, detail = "failed", f"{type(error).__name__}: {error}"
        executable = None
    result = {"schema": "hydra-p9-e-build-result-v1", "status": status, "detail": detail,
              "commands": records, "executable": executable, "disk_bytes": size_of_tree(OUTPUT),
              "elapsed_seconds": time.monotonic() - started, "solver_executions": 0,
              "source_archive": record["archive"], "source_commit": plan["commit"]}
    (OUTPUT / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({key: value for key, value in result.items() if key != "commands"}, indent=2))
    return 0 if status == "built-not-executed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
