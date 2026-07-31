#!/usr/bin/env python3
"""Model-free terminal host for the current native Peano Lab source tree."""

from __future__ import annotations

import argparse
from collections.abc import Iterable, Sequence
import os
from pathlib import Path
import sys
from typing import TextIO


if sys.version_info < (3, 10):
    print(
        "pa native: Python 3.10 or newer is required "
        f"(found {sys.version_info.major}.{sys.version_info.minor})",
        file=sys.stderr,
    )
    raise SystemExit(2)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PEANO_PYTHON = REPOSITORY_ROOT / "peano-lab" / "py"
if str(PEANO_PYTHON) not in sys.path:
    sys.path.insert(0, str(PEANO_PYTHON))

import driver  # noqa: E402
from peano_lab.library.theorems import THEOREMS  # noqa: E402


EXIT_COMMANDS = frozenset({"quit", "exit", ":q", ":quit", ":exit"})


def _owner(session: object) -> object | None:
    """Read the browser driver's owner without weakening raw-line routing."""

    accessor = getattr(session, "session_owner", None)
    if accessor is None:
        accessor = getattr(session, "_session_owner", None)
    return accessor() if callable(accessor) else accessor


def _emit(text: object, stream: TextIO) -> None:
    value = str(text).replace("\r\n", "\n").replace("\r", "\n")
    if value:
        print(value, file=stream, flush=True)


def _silence_broken_pipe(stream: TextIO) -> None:
    """Prevent a second flush error after a downstream reader closes."""

    try:
        descriptor = stream.fileno()
    except (AttributeError, OSError):
        return
    devnull = os.open(os.devnull, os.O_WRONLY)
    try:
        os.dup2(devnull, descriptor)
    finally:
        os.close(devnull)


def dispatch(
    session: driver.LabSession,
    line: str,
    *,
    stdout: TextIO = sys.stdout,
) -> tuple[int, bool]:
    """Run one raw line and return ``(exit_code, close_shell)``.

    An active proof or tutorial receives the complete line before the host
    interprets exit words. This is the same ownership law as the browser and
    model shells.
    """

    if _owner(session) is None and line.strip().casefold() in EXIT_COMMANDS:
        _emit("Session closed.", stdout)
        return 0, True
    result = session.run_result(line)
    output = result.get("out", "")
    if output:
        _emit(output, stdout)
    return (1 if result.get("failed") is True else 0), False


def run_batch(
    lines: Iterable[str],
    *,
    stdout: TextIO = sys.stdout,
    stderr: TextIO = sys.stderr,
) -> int:
    """Run a fail-fast native command stream without prompts or a banner."""

    session = driver.LabSession()
    for raw_line in lines:
        line = raw_line.rstrip("\r\n")
        try:
            exit_code, close_shell = dispatch(session, line, stdout=stdout)
        except KeyboardInterrupt:
            _emit(
                "Native command interrupted; no new theorem was claimed.",
                stderr,
            )
            return 130
        except BrokenPipeError:
            _silence_broken_pipe(stdout)
            return 141
        if close_shell:
            return exit_code
        if exit_code != 0:
            return exit_code
    if _owner(session) is not None:
        _emit(
            "Native input ended with an active proof or tutorial; "
            "no unfinished theorem was claimed.",
            stderr,
        )
        return 1
    return 0


def run_interactive(
    *,
    read=input,
    stdout: TextIO = sys.stdout,
) -> int:
    """Run one persistent model-free terminal session."""

    session = driver.LabSession()
    _emit("PEANO LAB — NATIVE / MODEL-FREE", stdout)
    _emit(
        f"Current source exposes {len(THEOREMS)} theorem specifications; "
        "library proofs replay and kernel-check on demand.",
        stdout,
    )
    _emit("Type `pa lib`, `pa prove <formula>`, or `help`; Ctrl-D closes.", stdout)
    while True:
        try:
            line = read("pa> ")
        except EOFError:
            _emit("", stdout)
            if _owner(session) is not None:
                _emit("Session closed; the unfinished theorem was not claimed.", stdout)
            return 0
        except KeyboardInterrupt:
            _emit("\nSession interrupted; no new theorem was claimed.", stdout)
            return 130
        try:
            exit_code, close_shell = dispatch(session, line, stdout=stdout)
        except KeyboardInterrupt:
            _emit("\nSession interrupted; no new theorem was claimed.", stdout)
            return 130
        except BrokenPipeError:
            _silence_broken_pipe(stdout)
            return 141
        if close_shell:
            return exit_code


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pa native",
        description=(
            "Open the current model-free Peano Lab terminal. The native source "
            "is separate from the frozen model adapter authority."
        ),
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "-c",
        "--command",
        action="append",
        default=[],
        metavar="LINE",
        help="run one raw Peano Lab line; repeat for a complete proof",
    )
    mode.add_argument(
        "--version",
        action="store_true",
        help="print the current native theorem inventory size",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.version:
        print(
            f"Peano Lab native shell · {len(THEOREMS)} theorem specifications"
        )
        return 0
    if args.command:
        return run_batch(args.command)
    if not sys.stdin.isatty():
        return run_batch(sys.stdin)
    return run_interactive()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print(
            "Native command interrupted; no new theorem was claimed.",
            file=sys.stderr,
        )
        raise SystemExit(130) from None
    except BrokenPipeError:
        _silence_broken_pipe(sys.stdout)
        raise SystemExit(141) from None
