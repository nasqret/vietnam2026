#!/usr/bin/env python3
"""Run the checked Peano Hydra assistant in a small terminal session.

The terminal is only a host.  Qwen responses and Vampire statuses remain
untrusted proposals; state changes still pass through the public Peano tactic
surface and a closed proof still needs the independent kernel replay.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PEANO_PYTHON = REPOSITORY_ROOT / "peano-lab" / "py"
for import_root in (REPOSITORY_ROOT, PEANO_PYTHON):
    while str(import_root) in sys.path:
        sys.path.remove(str(import_root))
sys.path[:0] = [str(PEANO_PYTHON), str(REPOSITORY_ROOT)]

from peano_lab.kernel.formulas import pretty_formula  # noqa: E402
from training.peano_hydra.interactive_assistant import (  # noqa: E402
    HydraAssistantAccepted,
    HydraAssistantError,
    HydraAssistantRejected,
    HydraAssistantSession,
    apply_qwen_macros,
    attach_qwen_response,
    current_script,
    discard_qwen,
    prepare_qwen_request,
    qwen_prompt,
    render_hydra_state,
    resolve_qwen_premises,
    run_manual_tactic,
    run_vampire_assistance,
    start_hydra_assistant,
)
from training.peano_hydra.vampire_live import (  # noqa: E402
    VAMPIRE_LIVE_MODE,
    VampireLiveBounds,
    VampireLiveSolver,
)


ReadLine = Callable[[str], str]
WriteLine = Callable[[str], object]

DEFAULT_WALL_TIME_MS = 5_000
DEFAULT_CPU_TIME_SECONDS = 3
DEFAULT_MEMORY_BYTES = 512 * 1024 * 1024
DEFAULT_OUTPUT_BYTES = 64 * 1024

# The underlying preview supports larger research runs.  The teaching console
# intentionally exposes a much smaller envelope.
CONSOLE_MAX_WALL_TIME_MS = 30_000
CONSOLE_MAX_CPU_TIME_SECONDS = 15
CONSOLE_MAX_MEMORY_BYTES = 2 * 1024 * 1024 * 1024
CONSOLE_MAX_OUTPUT_BYTES = 256 * 1024

HELP = """Hydra commands
  :goals                 show the current checked proof state
  :script                show the replayable Peano Lab script
  :qwen NAME...          prepare and print the exact model prompt
  :model STRICT_JSON     attach one validated, inert model response
  :accept                transact the pending typed macros
  :resolve               send the pending Qwen premise list to Vampire
  :vampire NAME...       try Vampire with an explicit premise list
  :discard               discard pending Qwen data
  :undo                  restore the exact preceding immutable session
  :help                  show this help
  :quit                  close without claiming an unfinished theorem

Any other non-empty line is one ordinary Peano Lab tactic.  This console never
loads a model or contacts a network service."""


def _error_text(error: object) -> str:
    return " ".join(str(error).split())[:2_000] or type(error).__name__


def _emit(write: WriteLine, text: object) -> None:
    write(str(text).replace("\r\n", "\n").replace("\r", "\n"))


@dataclass(frozen=True, slots=True)
class ConsoleHistory:
    """Persistent snapshots; popping restores the very same session object."""

    sessions: tuple[HydraAssistantSession, ...]

    def __post_init__(self) -> None:
        if (
            type(self.sessions) is not tuple
            or not self.sessions
            or not all(type(item) is HydraAssistantSession for item in self.sessions)
        ):
            raise TypeError("console history needs a non-empty exact session tuple")

    @property
    def current(self) -> HydraAssistantSession:
        return self.sessions[-1]

    def push(self, session: HydraAssistantSession) -> "ConsoleHistory":
        if type(session) is not HydraAssistantSession:
            raise TypeError("console history can store only exact assistant sessions")
        return ConsoleHistory((*self.sessions, session))

    def undo(self) -> tuple["ConsoleHistory", bool]:
        if len(self.sessions) == 1:
            return self, False
        return ConsoleHistory(self.sessions[:-1]), True


def _script(session: HydraAssistantSession) -> str:
    theorem = pretty_formula(
        session.owner.original_target,
        list(session.owner.original_names),
    )
    lines = [f"pa prove {theorem}", *current_script(session)]
    if session.kernel_accepted:
        lines.append("qed")
    return "\n".join(lines)


def _accepted(
    history: ConsoleHistory,
    transition: HydraAssistantAccepted | HydraAssistantRejected,
    write: WriteLine,
) -> ConsoleHistory:
    if type(transition) is HydraAssistantRejected:
        _emit(write, f"REJECTED [{transition.channel}]: {transition.error}")
        _emit(write, "Proof state unchanged.")
        return history
    if type(transition) is not HydraAssistantAccepted:
        raise RuntimeError("assistant returned an unknown transition type")
    _emit(write, f"ACCEPTED [{transition.channel}]")
    for command in transition.public_commands:
        _emit(write, f"  {command}")
    if transition.proposal_sha256 is not None:
        _emit(write, f"  proposal-sha256: {transition.proposal_sha256}")
    if transition.solver_trace_sha256 is not None:
        _emit(write, f"  solver-trace-sha256: {transition.solver_trace_sha256}")
    _emit(write, render_hydra_state(transition.session))
    return history.push(transition.session)


def _names(tail: str) -> tuple[str, ...]:
    if not tail:
        return ()
    words = tail.split(" ")
    if any(not word for word in words):
        raise HydraAssistantError("premise names must use one separating space")
    return tuple(words)


def dispatch(
    history: ConsoleHistory,
    line: str,
    *,
    solver: VampireLiveSolver | None,
    write: WriteLine,
) -> tuple[ConsoleHistory, bool]:
    """Process one complete physical line and return ``(history, quit)``."""

    if type(history) is not ConsoleHistory or type(line) is not str:
        raise TypeError("console dispatch needs exact history and text")
    if solver is not None and type(solver) is not VampireLiveSolver:
        raise TypeError("console solver must be exact VampireLiveSolver or null")
    if not line:
        return history, False

    head, separator, tail = line.partition(" ")
    session = history.current

    if head == ":quit":
        if separator:
            _emit(write, "ERROR: :quit takes no arguments")
            return history, False
        _emit(
            write,
            "Session closed."
            if session.kernel_accepted
            else "Session closed; the unfinished theorem was not claimed.",
        )
        return history, True

    if head == ":help":
        if separator:
            _emit(write, "ERROR: :help takes no arguments")
        else:
            _emit(write, HELP)
        return history, False

    if head == ":goals":
        if separator:
            _emit(write, "ERROR: :goals takes no arguments")
        else:
            _emit(write, render_hydra_state(session))
        return history, False

    if head == ":script":
        if separator:
            _emit(write, "ERROR: :script takes no arguments")
        else:
            _emit(write, _script(session))
        return history, False

    if head == ":undo":
        if separator:
            _emit(write, "ERROR: :undo takes no arguments")
            return history, False
        restored, changed = history.undo()
        if not changed:
            _emit(write, "Nothing to undo.")
            return history, False
        _emit(write, "Restored the preceding immutable session.")
        _emit(write, render_hydra_state(restored.current))
        return restored, False

    if head == ":discard":
        if separator:
            _emit(write, "ERROR: :discard takes no arguments")
            return history, False
        successor = discard_qwen(session)
        if successor is session:
            _emit(write, "No pending Qwen request or proposal.")
            return history, False
        _emit(write, "Pending Qwen data discarded; proof owner unchanged.")
        return history.push(successor), False

    if head == ":qwen":
        try:
            successor = prepare_qwen_request(session, _names(tail if separator else ""))
            prompt = qwen_prompt(successor)
        except Exception as error:
            _emit(write, f"REJECTED [qwen]: {_error_text(error)}")
            _emit(write, "Proof state unchanged.")
            return history, False
        _emit(write, "Prepared an inert Qwen request. Exact prompt follows:")
        _emit(write, prompt)
        return history.push(successor), False

    if head == ":model":
        if not separator or not tail or not tail.lstrip().startswith("{"):
            _emit(write, "REJECTED [qwen]: :model requires one strict JSON object")
            _emit(write, "Proof state unchanged.")
            return history, False
        try:
            successor = attach_qwen_response(session, tail)
        except Exception as error:
            _emit(write, f"REJECTED [qwen]: {_error_text(error)}")
            _emit(write, "Proof state unchanged.")
            return history, False
        assert successor.pending_qwen is not None
        proposal = successor.pending_qwen.proposal
        assert proposal is not None
        _emit(
            write,
            "Attached inert Qwen proposal: "
            f"{len(proposal.premises)} premise(s), "
            f"{len(proposal.macro_lines)} typed macro(s), "
            f"sha256={proposal.raw_sha256}",
        )
        return history.push(successor), False

    if head == ":accept":
        if separator:
            _emit(write, "ERROR: :accept takes no arguments")
            return history, False
        return _accepted(history, apply_qwen_macros(session), write), False

    if head in {":resolve", ":vampire"}:
        if head == ":resolve" and separator:
            _emit(write, "ERROR: :resolve takes no arguments")
            return history, False
        if solver is None:
            _emit(
                write,
                "Vampire unavailable: configure both --vampire and "
                "--vampire-sha256. Proof state unchanged.",
            )
            return history, False
        if head == ":resolve":
            transition = resolve_qwen_premises(session, solver)
        else:
            try:
                premise_names = _names(tail if separator else "")
                transition = run_vampire_assistance(session, premise_names, solver)
            except Exception as error:
                _emit(write, f"REJECTED [vampire]: {_error_text(error)}")
                _emit(write, "Proof state unchanged.")
                return history, False
        return _accepted(history, transition, write), False

    if head.startswith(":"):
        _emit(write, f"ERROR: unknown Hydra command {head!r}; use :help")
        return history, False

    return _accepted(history, run_manual_tactic(session, line), write), False


def run_repl(
    theorem: str | None = None,
    *,
    solver: VampireLiveSolver | None = None,
    read: ReadLine = input,
    write: WriteLine = print,
) -> int:
    """Run one persistent session with injectable terminal I/O."""

    _emit(write, "PEANO HYDRA — CHECKED INTERACTIVE PREVIEW")
    _emit(
        write,
        "Qwen and Vampire propose only; public tactics and the independent kernel decide.",
    )
    if theorem is None:
        try:
            theorem = read("theorem> ")
        except EOFError:
            _emit(write, "No theorem supplied; session closed.")
            return 0
        except KeyboardInterrupt:
            _emit(write, "Session interrupted; no theorem was claimed.")
            return 130
    try:
        initial = start_hydra_assistant(theorem)
    except Exception as error:
        _emit(write, f"Cannot start theorem: {_error_text(error)}")
        return 2
    history = ConsoleHistory((initial,))
    _emit(write, render_hydra_state(initial))
    _emit(write, "Type :help for assistant commands.")

    while True:
        try:
            line = read("hydra> ")
        except EOFError:
            _emit(
                write,
                "Session closed."
                if history.current.kernel_accepted
                else "Session closed; the unfinished theorem was not claimed.",
            )
            return 0
        except KeyboardInterrupt:
            _emit(write, "Session interrupted; no new theorem was claimed.")
            return 130
        try:
            history, close = dispatch(history, line, solver=solver, write=write)
        except KeyboardInterrupt:
            _emit(write, "Session interrupted; no new theorem was claimed.")
            return 130
        if close:
            return 0


def _bounded_int(label: str, maximum: int) -> Callable[[str], int]:
    def parse(value: str) -> int:
        try:
            result = int(value)
        except ValueError:
            raise argparse.ArgumentTypeError(f"{label} must be an integer") from None
        if isinstance(result, bool) or not 1 <= result <= maximum:
            raise argparse.ArgumentTypeError(
                f"{label} must be between 1 and {maximum}"
            )
        return result

    return parse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog=(
            "Omit --theorem to receive a theorem> prompt. Leading-dash Vampire "
            "arguments use --vampire-arg=VALUE. No model or network is loaded."
        ),
    )
    parser.add_argument("--theorem", help="closed intuitionistic PA theorem")
    parser.add_argument("--vampire", metavar="ABSOLUTE_PATH")
    parser.add_argument("--vampire-sha256", metavar="HEX64")
    parser.add_argument(
        "--vampire-arg",
        action="append",
        default=None,
        metavar="ARG",
        help="exact argument; repeated values replace the '--mode vampire' default",
    )
    parser.add_argument(
        "--vampire-wall-time-ms",
        type=_bounded_int("Vampire wall time", CONSOLE_MAX_WALL_TIME_MS),
        default=DEFAULT_WALL_TIME_MS,
    )
    parser.add_argument(
        "--vampire-cpu-time-seconds",
        type=_bounded_int("Vampire CPU time", CONSOLE_MAX_CPU_TIME_SECONDS),
        default=DEFAULT_CPU_TIME_SECONDS,
    )
    parser.add_argument(
        "--vampire-memory-bytes",
        type=_bounded_int("Vampire memory", CONSOLE_MAX_MEMORY_BYTES),
        default=DEFAULT_MEMORY_BYTES,
    )
    parser.add_argument(
        "--vampire-output-bytes",
        type=_bounded_int("Vampire output", CONSOLE_MAX_OUTPUT_BYTES),
        default=DEFAULT_OUTPUT_BYTES,
    )
    return parser


def configured_solver(args: argparse.Namespace) -> VampireLiveSolver | None:
    """Construct a solver only from a complete, user-pinned configuration."""

    has_path = args.vampire is not None
    has_sha = args.vampire_sha256 is not None
    if has_path != has_sha:
        raise ValueError("--vampire and --vampire-sha256 must be supplied together")
    if not has_path:
        if args.vampire_arg is not None:
            raise ValueError("--vampire-arg requires a pinned Vampire executable")
        return None
    assert type(args.vampire) is str and type(args.vampire_sha256) is str
    if not Path(args.vampire).is_absolute():
        raise ValueError("--vampire must be an absolute path")
    arguments = VAMPIRE_LIVE_MODE if args.vampire_arg is None else tuple(args.vampire_arg)
    bounds = VampireLiveBounds(
        max_wall_time_ms=args.vampire_wall_time_ms,
        max_cpu_time_seconds=args.vampire_cpu_time_seconds,
        max_memory_bytes=args.vampire_memory_bytes,
        max_output_bytes=args.vampire_output_bytes,
    )
    return VampireLiveSolver(
        args.vampire,
        args.vampire_sha256,
        arguments,
        bounds,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        solver = configured_solver(args)
    except (TypeError, ValueError) as error:
        parser.error(_error_text(error))
    return run_repl(args.theorem, solver=solver)


if __name__ == "__main__":
    raise SystemExit(main())
