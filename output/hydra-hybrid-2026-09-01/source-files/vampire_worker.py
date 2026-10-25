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
from vampire_process import ENVIRONMENT, SOLVER_ARGS, package

if __name__ == "__main__":
    if not sys.flags.isolated or not sys.dont_write_bytecode or sys.argv[1:] not in ([], ["--version"]):
        raise SystemExit("The Vampire helper requires -I -B and no solver-controlled arguments.")
    resource.setrlimit(resource.RLIMIT_CPU, (2, 2))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))
    resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
    signal.signal(signal.SIGALRM, signal.SIG_DFL)
    signal.setitimer(signal.ITIMER_REAL, 3)
    binary, _, _ = package(verify_binary=True, require_ready=False)
    options = ["--version"] if sys.argv[1:] else SOLVER_ARGS
    os.execve(str(binary), [str(binary), *options], dict(ENVIRONMENT))
