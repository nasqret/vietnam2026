"""One bounded local Cargo dependency/build attempt; never execute the helper."""
from pathlib import Path
import hashlib
import json
import os
import resource
import shutil
import signal
import subprocess
import time
import tomllib


HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "egg-build-01"
BUILD = OUTPUT / "source"
CACHE = OUTPUT / "cargo-home"
TARGET = OUTPUT / "target"
WALL = 300
DISK = 768 * 1024**2
CACHE_LIMIT = 96 * 1024**2
LOG_LIMIT = 8 * 1024**2


def pin(path):
    raw = path.read_bytes()
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def tree_size(path, maximum):
    total = 0
    for directory, _, files in os.walk(path, followlinks=False):
        for name in files:
            item = Path(directory) / name
            if not item.is_symlink():
                total += item.stat().st_size
                if total > maximum:
                    return total
    return total


def child_limits():
    resource.setrlimit(resource.RLIMIT_CPU, (180, 180))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_FSIZE, (64 * 1024**2, 64 * 1024**2))
    resource.setrlimit(resource.RLIMIT_NOFILE, (256, 256))


def run(argv, label, deadline, records):
    environment = {"PATH": "/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin", "LANG": "C", "LC_ALL": "C",
        "TMPDIR": str(OUTPUT / "tmp"), "CARGO_HOME": str(CACHE), "CARGO_TARGET_DIR": str(TARGET),
        "CARGO_BUILD_JOBS": "1", "CARGO_NET_RETRY": "0", "CARGO_HTTP_TIMEOUT": "20",
        "CARGO_REGISTRIES_CRATES_IO_PROTOCOL": "sparse", "RUSTC": "/opt/homebrew/bin/rustc",
        "RUSTFLAGS": "-C debuginfo=0", "CC": "/usr/bin/clang"}
    stdout = OUTPUT / (label + ".log")
    started = time.monotonic()
    process = None
    reason = "process_exit"
    print(json.dumps({"stage": label, "solver_executions": 0}), flush=True)
    try:
        with stdout.open("xb") as stream:
            process = subprocess.Popen(argv, cwd=BUILD, env=environment, stdin=subprocess.DEVNULL,
                stdout=stream, stderr=subprocess.STDOUT, close_fds=True, start_new_session=True,
                preexec_fn=child_limits)
            while process.poll() is None:
                if time.monotonic() >= deadline:
                    reason = "build_wall_limit"
                    raise TimeoutError(reason)
                if (stdout.stat().st_size > LOG_LIMIT or tree_size(CACHE, CACHE_LIMIT) > CACHE_LIMIT
                        or tree_size(OUTPUT, DISK) > DISK):
                    reason = "build_cache_output_or_disk_limit"
                    raise ValueError(reason)
                time.sleep(0.2)
            if process.returncode != 0:
                raise RuntimeError(f"{label} exited {process.returncode}; preserve its log.")
    finally:
        if process is not None:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait(timeout=2)
            records.append({"argv": argv, "label": label, "exit_code": process.returncode,
                            "elapsed_seconds": time.monotonic() - started, "termination": reason,
                            "leader_reaped": True, "log": pin(stdout)})


def locked_packages():
    packages = tomllib.loads((BUILD / "Cargo.lock").read_text())["package"]
    if not 1 < len(packages) <= 96:
        raise ValueError("Unexpected Cargo dependency count.")
    result = {}
    for package in packages:
        if package["name"] == "hydra-egg-adviser":
            if package.get("source") is not None:
                raise ValueError("Root helper must be the local source.")
            continue
        if (package.get("source") != "registry+https://github.com/rust-lang/crates.io-index"
                or len(package.get("checksum", "")) != 64):
            raise ValueError("Only checksum-pinned official registry dependencies are allowed.")
        result[f"{package['name']}-{package['version']}"] = package["checksum"]
    observed = json.loads((HERE / "dependency-metadata.json").read_bytes())
    for record in observed["crates"]:
        if result.get(f"{record['name']}-{record['version']}") != record["sha256"]:
            raise ValueError("A direct dependency differs from its independently observed checksum.")
    return result


def main():
    started = time.monotonic()
    OUTPUT.mkdir(exist_ok=False)
    (OUTPUT / "tmp").mkdir()
    CACHE.mkdir()
    for parent in HERE.parents:
        if any((parent / ".cargo" / name).exists() for name in ("config", "config.toml")):
            raise ValueError("Unexpected ancestor Cargo configuration; inspect before building.")
    shutil.copytree(HERE / "egg-helper", BUILD)
    source_pins = {str(path.relative_to(BUILD)): pin(path) for path in BUILD.rglob("*") if path.is_file()}
    base = ["/opt/homebrew/bin/cargo"]
    commands = [base + ["generate-lockfile"], base + ["fetch", "--locked", "--target", "aarch64-apple-darwin"],
                base + ["build", "--offline", "--locked", "--release", "--jobs", "1", "--target", "aarch64-apple-darwin"]]
    plan = {"schema": "hydra-p9-egg-build-plan-v1", "commands": commands, "source_pins": source_pins,
        "wall_seconds": WALL, "per_process_cpu_seconds": 180, "parallel_compilation_jobs": 1,
        "disk_bytes": DISK, "cache_bytes": CACHE_LIMIT, "per_command_log_bytes": LOG_LIMIT,
        "network_retries": 0, "global_install": False, "solver_executions": 0,
        "network_note": "Cargo HTTPS metadata/fetch only; build is offline. Cache and elapsed bounds are enforced, not a claimed network packet-byte cap."}
    (OUTPUT / "plan.json").write_text(json.dumps(plan, indent=2) + "\n")
    records, archives = [], {}
    status, detail, executable = "built-not-executed", None, None
    try:
        run(commands[0], "lock", started + WALL, records)
        packages = locked_packages()
        run(commands[1], "fetch", started + WALL, records)
        for archive in CACHE.glob("registry/cache/*/*.crate"):
            descriptor = pin(archive)
            if descriptor["sha256"] != packages.get(archive.name.removesuffix(".crate")):
                raise ValueError("Downloaded crate differs from Cargo.lock.")
            archives[archive.name] = descriptor
        run(commands[2], "build", started + WALL, records)
        executable = pin(TARGET / "aarch64-apple-darwin/release/hydra-egg-adviser")
        if executable["bytes"] > 16 * 1024**2:
            raise ValueError("Compiled egg helper exceeds its package bound.")
    except Exception as error:
        status, detail = "failed", f"{type(error).__name__}: {error}"
    result = {"schema": "hydra-p9-egg-build-result-v1", "status": status, "detail": detail,
        "commands": records, "executable": executable, "downloaded_crates": archives,
        "source_pins": source_pins, "cargo_lock": pin(BUILD / "Cargo.lock") if (BUILD / "Cargo.lock").exists() else None,
        "disk_bytes": tree_size(OUTPUT, DISK), "cache_bytes": tree_size(CACHE, CACHE_LIMIT),
        "elapsed_seconds": time.monotonic() - started, "solver_executions": 0}
    (OUTPUT / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({key: value for key, value in result.items() if key not in {"commands", "downloaded_crates"}}, indent=2))
    return 0 if status == "built-not-executed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
