#!/usr/bin/env python3
"""Fixed solver launcher: limits are established in a fresh Python process.

Do not use preexec_fn in the MLX process: it can already have native threads.
This helper then execs Vampire, retaining its PID, process group and OS limits.
"""
from pathlib import Path
import os
import resource
import signal
import sys

APP = Path(__file__).resolve().parent
sys.path.insert(0, str(APP))
from vampire_limits import parse_helper_arguments, solver_args, solver_limits
from vampire_process import ENVIRONMENT, package


def main():
    if not sys.flags.isolated or not sys.dont_write_bytecode:
        raise SystemExit("The Vampire helper requires -I -B and no solver-controlled arguments.")
    try:
        profile, version_probe = parse_helper_arguments(sys.argv[1:])
    except ValueError as error:
        raise SystemExit(str(error)) from error
    limits = solver_limits(profile)
    resource.setrlimit(resource.RLIMIT_CPU, (limits["cpu_seconds"], limits["cpu_seconds"]))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))
    resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
    signal.signal(signal.SIGALRM, signal.SIG_DFL)
    signal.setitimer(signal.ITIMER_REAL, limits["wall_seconds"])
    binary, _, _ = package(verify_binary=True, require_ready=False)
    options = ["--version"] if version_probe else solver_args(profile)
    os.execve(str(binary), [str(binary), *options], dict(ENVIRONMENT))


if __name__ == "__main__":
    main()
