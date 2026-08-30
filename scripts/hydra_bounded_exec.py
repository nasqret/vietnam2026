#!/usr/bin/env python3
"""Internal, shell-free OS limits for one owned Hydra review worker."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import resource
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cpu-seconds", type=int, required=True)
    parser.add_argument("--rss-bytes", type=int, required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if (not 1 <= args.cpu_seconds <= 120
        or not 128 * 1024**2 <= args.rss_bytes <= 2 * 1024**3
        or not command or len(command) > 1024 or not Path(command[0]).is_absolute()
        or any("\x00" in value or len(value.encode("utf-8")) > 16384 for value in command)):
        parser.error("invalid bounded executable or resource reservation")
    resource.setrlimit(resource.RLIMIT_CPU, (args.cpu_seconds, args.cpu_seconds + 1))
    if sys.platform.startswith("linux"):
        resource.setrlimit(resource.RLIMIT_AS, (args.rss_bytes, args.rss_bytes))
    elif sys.platform != "darwin":
        parser.error("this worker requires Linux or macOS resource accounting")
    os.execvpe(command[0], command, os.environ)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
