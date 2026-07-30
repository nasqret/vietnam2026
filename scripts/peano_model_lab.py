#!/usr/bin/env python3
"""Native Peano Lab shell with one resident, untrusted tactic model.

Run without a positional command for the persistent ``pa>`` shell, or use
``prove-model FORMULA`` for a one-shot attempt.  The browser Peano Lab remains
model-free; this process is the host-side shell that can load PyTorch once and
reuse the model for many independent theorem requests.

Model output is never proof authority.  Every proposed line is compiled and
freshly replayed by Peano Lab, and a successful search is published only after
the policy REPL's independent verification pass.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
import inspect
import math
import os
from pathlib import Path
import re
import sys
import unicodedata
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PEANO_PYTHON = REPOSITORY_ROOT / "peano-lab" / "py"
RESULTS_ROOT = REPOSITORY_ROOT / "results"
DEFAULT_ADAPTER = RESULTS_ROOT / "peano-policy" / "qwen3-1.7b-lora-v3-library"
DEFAULT_RESULTS_DIR = RESULTS_ROOT / "peano-policy" / "interactive-local"

MAX_EVENT_TEXT = 1_000
MAX_EVENT_ITEMS = 16
MAX_TERMINAL_TEXT = 100_000
LIVE_MODES = ("concise", "full", "off")
DEVICE_CHOICES = ("auto", "cuda", "mps", "cpu")
DTYPE_CHOICES = ("auto", "bfloat16", "float16", "float32")

_PROVE_MODEL = re.compile(
    r"[ \t]*pa[ \t]+prove-model(?:[ \t]+(.*?))?[ \t]*\Z",
    re.IGNORECASE,
)
_UNSAFE_CATEGORIES = frozenset({"Cc", "Cf", "Cs", "Zl", "Zp"})


def _plain_string(value: object) -> str:
    try:
        return str(value)
    except Exception:
        return f"<{type(value).__name__}>"


def _escaped_text(
    value: object,
    *,
    multiline: bool,
    max_chars: int,
) -> str:
    """Render terminal text without allowing control or format sequences."""

    source = _plain_string(value)
    truncated = len(source) > max_chars
    if truncated:
        source = source[:max_chars]
    source = source.replace("\r\n", "\n")
    rendered: list[str] = []
    for character in source:
        code = ord(character)
        if character == "\n" and multiline:
            rendered.append(character)
        elif unicodedata.category(character) not in _UNSAFE_CATEGORIES:
            rendered.append(character)
        elif code <= 0xFF:
            rendered.append(f"\\x{code:02x}")
        elif code <= 0xFFFF:
            rendered.append(f"\\u{code:04x}")
        else:
            rendered.append(f"\\U{code:08x}")
    if truncated:
        rendered.append("…")
    return "".join(rendered)


def _safe_inline(value: object, *, max_chars: int = MAX_EVENT_TEXT) -> str:
    return _escaped_text(value, multiline=False, max_chars=max_chars)


def _safe_block(value: object, *, max_chars: int = MAX_TERMINAL_TEXT) -> str:
    return _escaped_text(value, multiline=True, max_chars=max_chars)


def _event_value(event: Mapping[str, object], *names: str) -> object | None:
    for name in names:
        if name in event:
            return event[name]
    return None


def _event_items(value: object) -> tuple[object, ...]:
    if isinstance(value, (str, bytes, bytearray)) or not isinstance(
        value, Sequence
    ):
        return ()
    return tuple(value[:MAX_EVENT_ITEMS])


def _event_goals(event: Mapping[str, object]) -> tuple[object, ...]:
    value = _event_value(
        event,
        "goals_after",
        "goals_before",
        "goals",
        "state_goals",
    )
    return _event_items(value)


@dataclass(slots=True)
class LiveEventRenderer:
    """Best-effort renderer for versioned search events.

    Event presentation is deliberately non-authoritative.  A malformed event
    or a broken output sink must never change search, replay, or publication.
    """

    mode: str = "concise"
    write: Callable[[str], object] = print

    def __post_init__(self) -> None:
        if self.mode not in LIVE_MODES:
            raise ValueError(f"live mode must be one of: {', '.join(LIVE_MODES)}")

    def __call__(self, event: object) -> None:
        if self.mode == "off":
            return
        try:
            lines = self.render(event)
            for line in lines:
                try:
                    display_limit = (
                        MAX_TERMINAL_TEXT
                        if self.mode == "full"
                        else MAX_EVENT_TEXT * 4
                    )
                    self.write(_safe_block(line, max_chars=display_limit))
                except Exception:
                    return
        except Exception:
            # Live text is never allowed to become a new failure mode for the
            # proof search.  Full mode still gives a bounded marker when the
            # event itself is structurally hostile.
            if self.mode == "full":
                try:
                    self.write("[live event unavailable]")
                except Exception:
                    pass

    def render(self, event: object) -> tuple[str, ...]:
        if not isinstance(event, Mapping):
            if self.mode == "full":
                return (f"[live malformed] {_safe_inline(event)}",)
            return ()

        kind = _safe_inline(event.get("kind", "event"), max_chars=80)
        version = event.get("v")
        command = _event_value(event, "command", "candidate", "tactic")
        message = _event_value(event, "message", "error", "reason")
        status = _event_value(event, "status", "result")
        depth = _event_value(event, "depth", "search_depth")
        call = _event_value(event, "model_call", "call", "call_index")
        rank = _event_value(event, "rank", "candidate_rank", "proposal_rank")
        rank_display = rank + 1 if type(rank) is int and rank >= 0 else rank

        lowered = kind.casefold().replace("-", "_")
        if lowered == "search_started":
            headline = "[search] started"
        elif lowered == "state_selected":
            headline = "[state] selected"
            if depth is not None:
                headline += f" · depth={_safe_inline(depth, max_chars=40)}"
            frontier_rank = event.get("frontier_rank")
            frontier_size = event.get("frontier_size")
            if frontier_rank is not None and frontier_size is not None:
                frontier_display = (
                    frontier_rank + 1
                    if type(frontier_rank) is int and frontier_rank >= 0
                    else frontier_rank
                )
                headline += (
                    f" · frontier {_safe_inline(frontier_display, max_chars=40)}"
                    f"/{_safe_inline(frontier_size, max_chars=40)}"
                )
        elif lowered == "model_prompt":
            headline = "[prompt"
            if call is not None:
                headline += f" #{_safe_inline(call, max_chars=40)}"
            headline += "]"
            prompt_chars = event.get("prompt_chars")
            requested = event.get("requested_candidates")
            if prompt_chars is not None:
                headline += f" · {_safe_inline(prompt_chars, max_chars=40)} chars"
            if requested is not None:
                headline += f" · requesting {_safe_inline(requested, max_chars=40)}"
        elif lowered == "model_output":
            accepted = len(_event_items(event.get("candidates")))
            rejected = len(_event_items(event.get("rejections")))
            headline = f"[model] {accepted} valid candidate(s)"
            if rejected:
                headline += f" · {rejected} malformed rejected"
        elif lowered == "proposal_received":
            headline = "[model] proposals received"
            returned = event.get("returned")
            authorized = event.get("authorized")
            if returned is not None and authorized is not None:
                headline += (
                    f" · returned={_safe_inline(returned, max_chars=40)}"
                    f" · authorized={_safe_inline(authorized, max_chars=40)}"
                )
        elif lowered == "model_error":
            headline = "[model error]"
            if call is not None:
                headline += f" call #{_safe_inline(call, max_chars=40)}"
            if message is not None:
                headline += f" — {_safe_inline(message)}"
        elif lowered == "policy_error":
            headline = "[policy error]"
            if call is not None:
                headline += f" call #{_safe_inline(call, max_chars=40)}"
            if depth is not None:
                headline += f" · depth={_safe_inline(depth, max_chars=40)}"
            if message is not None:
                headline += f" — {_safe_inline(message)}"
        elif lowered == "candidate_result":
            disposition = _event_value(event, "disposition", "status")
            status_text = _safe_inline(status, max_chars=80).casefold()
            disposition_text = _safe_inline(disposition, max_chars=80).casefold()
            accepted = status_text in {"ok", "accepted", "success"} and (
                disposition_text != "rejected"
            )
            headline = (
                "[compile + fresh replay] accepted"
                if accepted
                else "[compile + fresh replay] rejected"
            )
            if command is not None:
                headline += f": {_safe_inline(command)}"
            if accepted and disposition_text not in {"", "admitted"}:
                headline += f" · {disposition_text}"
            if not accepted and message is not None:
                headline += f" — {_safe_inline(message)}"
        elif "candidate" in lowered and any(
            token in lowered for token in ("start", "propos", "try")
        ):
            prefix = "[model]"
            if rank_display is not None:
                prefix += f" #{_safe_inline(rank_display, max_chars=40)}"
            headline = prefix + (
                f" {_safe_inline(command)}" if command is not None else " candidate"
            )
        elif "candidate" in lowered and any(
            token in lowered for token in ("reject", "fail", "invalid")
        ):
            headline = "[compile + fresh replay] rejected"
            if command is not None:
                headline += f": {_safe_inline(command)}"
            if message is not None:
                headline += f" — {_safe_inline(message)}"
        elif "candidate" in lowered and any(
            token in lowered for token in ("accept", "success", "advance")
        ):
            headline = "[compile + fresh replay] accepted"
            if command is not None:
                headline += f": {_safe_inline(command)}"
        elif "model" in lowered or "policy" in lowered or "prompt" in lowered:
            headline = "[prompt"
            if call is not None:
                headline += f" #{_safe_inline(call, max_chars=40)}"
            headline += "]"
            if depth is not None:
                headline += f" depth={_safe_inline(depth, max_chars=40)}"
            if message is not None:
                headline += f" {_safe_inline(message)}"
        elif "independent" in lowered or "verification" in lowered:
            headline = f"[independent replay] {kind}"
        elif "kernel" in lowered:
            headline = f"[kernel] {kind}"
        elif "beam" in lowered or "frontier" in lowered:
            headline = f"[beam] {kind}"
        elif lowered == "search_start":
            headline = "[search] started"
        elif lowered in {"search_finish", "search_finished", "search_complete"}:
            headline = "[search] finished"
        else:
            headline = f"[{kind}]"

        details: list[str] = []
        if status is not None and _safe_inline(status) not in headline:
            details.append(f"status={_safe_inline(status)}")
        if message is not None and _safe_inline(message) not in headline:
            details.append(_safe_inline(message))
        if command is not None and _safe_inline(command) not in headline:
            details.append(f"tactic={_safe_inline(command)}")
        if details:
            headline += " · " + " · ".join(details)

        lines = [headline]
        if lowered == "model_prompt" and isinstance(event.get("prompt"), str):
            prompt_header = event["prompt"].splitlines()[:2]
            for prompt_line in prompt_header:
                lines.append(f"  {_safe_inline(prompt_line)}")
            lines.append("  generating…")
        for index, goal in enumerate(_event_goals(event), start=1):
            safe_goal = _safe_block(goal, max_chars=MAX_EVENT_TEXT)
            goal_lines = safe_goal.splitlines() or [""]
            lines.append(f"  Goal {index}: {goal_lines[0]}")
            lines.extend(f"          {line}" for line in goal_lines[1:])

        show_candidate_batch = lowered in {
            "model_output",
            "model_candidates",
            "candidates_generated",
        } or (self.mode == "full" and lowered == "proposal_received")
        candidates = (
            _event_items(
                _event_value(event, "candidates", "proposals", "commands")
            )
            if show_candidate_batch
            else ()
        )
        for index, candidate in enumerate(candidates, start=1):
            lines.append(f"  Candidate {index}: {_safe_inline(candidate)}")

        if self.mode == "full":
            shown = {
                "kind",
                "v",
                "command",
                "candidate",
                "tactic",
                "message",
                "error",
                "reason",
                "status",
                "result",
                "depth",
                "search_depth",
                "model_call",
                "call",
                "call_index",
                "rank",
                "candidate_rank",
                "proposal_rank",
                "goals_after",
                "goals_before",
                "goals",
                "state_goals",
                "candidates",
                "proposals",
                "commands",
            }
            version_text = "missing" if version is None else _safe_inline(version)
            lines[0] += f" · event-v={version_text}"
            for name in sorted((_safe_inline(key, max_chars=80) for key in event)):
                # Find the original key without assuming all Mapping keys are
                # strings.  Extra fields are diagnostic display only.
                original = next(
                    (key for key in event if _safe_inline(key, max_chars=80) == name),
                    None,
                )
                if original is None or original in shown:
                    continue
                if name == "prompt":
                    lines.append("  prompt:")
                    prompt_lines = _safe_block(
                        event[original], max_chars=MAX_TERMINAL_TEXT
                    ).splitlines()
                    lines.extend(f"    {line}" for line in prompt_lines)
                else:
                    lines.append(
                        f"  {name}={_safe_inline(event[original], max_chars=MAX_EVENT_TEXT)}"
                    )
        return tuple(lines)


@dataclass(frozen=True, slots=True)
class ShellOutcome:
    model_command: bool
    exit_code: int
    close_shell: bool = False


class PeanoModelShell:
    """Route native Peano commands around one already-loaded model runtime."""

    def __init__(
        self,
        *,
        lab_session: object,
        runtime: object,
        budget: object,
        results_dir: Path,
        normalize_theorem: Callable[[object], str],
        run_checked_search: Callable[..., object],
        save_attempt: Callable[[object, Path], object],
        live_mode: str = "concise",
        write: Callable[[str], object] = print,
    ) -> None:
        self.lab_session = lab_session
        self.runtime = runtime
        self.budget = budget
        self.results_dir = results_dir
        self.normalize_theorem = normalize_theorem
        self.run_checked_search = run_checked_search
        self.save_attempt = save_attempt
        self.live_mode = live_mode
        self.write = write

    def _emit(self, value: object) -> None:
        self.write(_safe_block(value))

    def _owner(self) -> object | None:
        owner = getattr(self.lab_session, "session_owner", None)
        if owner is None:
            # The browser driver intentionally keeps this implementation
            # detail private and content-addressed.  The native host shell may
            # inspect it read-only to preserve the same raw-input ownership law.
            owner = getattr(self.lab_session, "_session_owner", None)
        return owner() if callable(owner) else owner

    def _run_lab(self, line: object) -> ShellOutcome:
        runner = getattr(self.lab_session, "run_result", None)
        if not callable(runner):
            raise TypeError("lab session does not provide run_result")
        result = runner(line)
        if not isinstance(result, Mapping):
            raise TypeError("lab session returned an invalid command result")
        output = result.get("out", "")
        if output:
            self._emit(output)
        return ShellOutcome(False, 1 if result.get("failed") is True else 0)

    def dispatch(self, line: object) -> ShellOutcome:
        # Peano Lab's ownership law comes first: a manual proof or tutorial
        # consumes the complete raw line before this shell inspects it.
        if self._owner() is not None:
            return self._run_lab(line)
        if not isinstance(line, str):
            return self._run_lab(line)

        if line.strip().casefold() in {"quit", "exit", ":quit", ":q", ":exit"}:
            self._emit("Session closed.")
            return ShellOutcome(False, 0, True)

        match = _PROVE_MODEL.fullmatch(line)
        if match is None:
            return self._run_lab(line)
        theorem_source = match.group(1)
        if theorem_source is None or not theorem_source.strip():
            self._emit("Usage: pa prove-model <closed-formula>")
            return ShellOutcome(True, 2)
        return self._run_model(theorem_source)

    def _run_model(self, theorem_source: str) -> ShellOutcome:
        try:
            theorem = self.normalize_theorem(theorem_source)
            self._emit(f"[request] {_safe_inline(theorem, max_chars=4_000)}")
            renderer = LiveEventRenderer(self.live_mode, self._emit)
            observer = None if self.live_mode == "off" else renderer
            attempt = self.run_checked_search(
                theorem,
                self.runtime,
                self.budget,
                on_event=observer,
            )
        except KeyboardInterrupt:
            self._emit("Search interrupted; no proof was published.")
            return ShellOutcome(True, 130)
        except Exception as exc:
            message = " ".join(_plain_string(exc).split()) or type(exc).__name__
            self._emit(f"ERROR — no proof was published: {_safe_inline(message)}")
            return ShellOutcome(True, 2)

        proved = getattr(attempt, "proved", False) is True
        proof_script = getattr(attempt, "proof_script", None)
        if proved and (not isinstance(proof_script, str) or not proof_script):
            self._emit("ERROR — checked result did not contain a proof script.")
            return ShellOutcome(True, 2)

        # Publication receives exactly the CheckedAttempt returned by the
        # checked-search boundary.  The saver publishes a proof before its
        # companion report so it never leaves a report that points to a
        # missing proof; a crash can therefore leave one uniquely named orphan
        # proof.  Report that possibility honestly rather than claiming that
        # no filesystem entry could have appeared.
        try:
            artifacts = self.save_attempt(attempt, self.results_dir)
        except KeyboardInterrupt:
            if proved:
                self._emit(
                    "Publication interrupted; a uniquely named checked-proof "
                    "orphan may remain, but no complete result was announced."
                )
            else:
                self._emit("Publication interrupted; no result was announced.")
            return ShellOutcome(True, 130)
        except Exception as exc:
            message = " ".join(_plain_string(exc).split()) or type(exc).__name__
            if proved:
                prefix = (
                    "ERROR — checked search succeeded, but publication was "
                    "incomplete; a uniquely named proof orphan may remain"
                )
            else:
                prefix = "ERROR — result report was not published"
            self._emit(f"{prefix}: {_safe_inline(message)}")
            return ShellOutcome(True, 2)

        report_path = getattr(artifacts, "report", None)
        proof_path = getattr(artifacts, "proof", None)
        if proved:
            self._emit("KERNEL-CHECKED PROOF")
            self._emit(proof_script)
            if proof_path is not None:
                self._emit(f"Proof:  {_safe_inline(proof_path, max_chars=4_000)}")
            if report_path is not None:
                self._emit(f"Report: {_safe_inline(report_path, max_chars=4_000)}")
            return ShellOutcome(True, 0)

        self._emit("NO KERNEL-CHECKED PROOF within the configured bounds.")
        report = getattr(attempt, "report", None)
        search = report.get("search") if isinstance(report, Mapping) else None
        if isinstance(search, Mapping):
            fields = (
                f"status={_safe_inline(search.get('status'))}",
                f"depth={_safe_inline(search.get('depth_reached'))}",
                f"model calls={_safe_inline(search.get('model_calls'))}",
            )
            self._emit("; ".join(fields))
        if report_path is not None:
            self._emit(f"Report: {_safe_inline(report_path, max_chars=4_000)}")
        return ShellOutcome(True, 1)


def run_interactive(
    shell: PeanoModelShell,
    *,
    read: Callable[[str], str] = input,
) -> int:
    shell._emit("Peano Model Lab — model loaded once; every success is kernel checked.")
    shell._emit("Type `pa prove-model <formula>`; Ctrl-D closes the shell.")
    while True:
        try:
            line = read("pa> ")
        except EOFError:
            shell._emit("")
            return 0
        except KeyboardInterrupt:
            shell._emit("\nSession closed.")
            return 130
        outcome = shell.dispatch(line)
        if outcome.close_shell:
            return outcome.exit_code


def _bounded_int(label: str, minimum: int, maximum: int) -> Callable[[str], int]:
    def parse(value: str) -> int:
        try:
            result = int(value)
        except ValueError:
            raise argparse.ArgumentTypeError(f"{label} must be an integer") from None
        if not minimum <= result <= maximum:
            raise argparse.ArgumentTypeError(
                f"{label} must lie between {minimum} and {maximum}"
            )
        return result

    return parse


def _positive_float(label: str, *, at_most_one: bool = False) -> Callable[[str], float]:
    def parse(value: str) -> float:
        try:
            result = float(value)
        except ValueError:
            raise argparse.ArgumentTypeError(f"{label} must be a number") from None
        if not math.isfinite(result) or result <= 0 or (at_most_one and result > 1):
            suffix = " in (0, 1]" if at_most_one else " positive and finite"
            raise argparse.ArgumentTypeError(f"{label} must be{suffix}")
        return result

    return parse


def _parser() -> argparse.ArgumentParser:
    # The reviewed ``pa`` launcher injects a fixed adapter and cache before
    # forwarding user arguments.  Disabling argparse's prefix matching keeps
    # spellings such as ``--adapt`` or ``--cache`` from becoming aliases that
    # can override those sealed inputs.
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--adapter", type=Path, default=DEFAULT_ADAPTER)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--diagnostic", action="store_true")
    parser.add_argument("--device", choices=DEVICE_CHOICES, default="auto")
    parser.add_argument("--dtype", choices=DTYPE_CHOICES, default="auto")
    parser.add_argument(
        "--local-files-only",
        action="store_true",
        default=None,
        help="refuse network access while resolving the pinned base snapshot",
    )
    parser.add_argument("--cache-dir", type=Path)
    parser.add_argument("--live", choices=LIVE_MODES, default="concise")
    parser.add_argument("--seed", type=int, default=20260731)
    parser.add_argument(
        "--max-new-tokens",
        type=_bounded_int("max-new-tokens", 1, 1_024),
        default=64,
    )
    parser.add_argument("--sample", action="store_true")
    parser.add_argument(
        "--temperature", type=_positive_float("temperature"), default=0.8
    )
    parser.add_argument(
        "--top-p",
        type=_positive_float("top-p", at_most_one=True),
        default=0.95,
    )
    parser.add_argument(
        "--depth", type=_bounded_int("depth", 1, 32), default=16
    )
    parser.add_argument(
        "--beam", type=_bounded_int("beam", 1, 64), default=1
    )
    parser.add_argument(
        "--candidates", type=_bounded_int("candidates", 1, 16), default=1
    )
    parser.add_argument(
        "--model-calls", type=_bounded_int("model-calls", 1, 4_096), default=32
    )
    parser.add_argument(
        "--states", type=_bounded_int("states", 1, 65_536), default=256
    )
    parser.add_argument("command", nargs="?", choices=("prove-model",))
    parser.add_argument(
        "theorem",
        nargs="*",
        help="closed PA formula (quote it to preserve shell punctuation)",
    )
    return parser


def _load_components() -> tuple[object, object]:
    for import_root in (REPOSITORY_ROOT, PEANO_PYTHON):
        if str(import_root) not in sys.path:
            sys.path.insert(0, str(import_root))
    import driver
    import scripts.peano_policy_repl as policy_repl

    return driver, policy_repl


def _load_runtime(loader: Callable[..., object], args: argparse.Namespace) -> object:
    """Call old or placement-aware runtime loaders without hiding requests."""

    required: dict[str, object] = {
        "seed": args.seed,
        "max_new_tokens": args.max_new_tokens,
        "sample": args.sample,
        "temperature": args.temperature,
        "top_p": args.top_p,
    }
    optional = {
        "diagnostic_mode": (args.diagnostic, False),
        "device": (args.device, "auto"),
        "dtype": (args.dtype, "auto"),
        "local_files_only": (args.local_files_only, None),
        "cache_dir": (args.cache_dir, None),
    }
    signature = inspect.signature(loader)
    accepts_any = any(
        parameter.kind is inspect.Parameter.VAR_KEYWORD
        for parameter in signature.parameters.values()
    )
    for name, (value, default) in optional.items():
        if accepts_any or name in signature.parameters:
            required[name] = value
        elif value != default:
            raise RuntimeError(
                f"installed policy runtime does not support requested --{name.replace('_', '-')}"
            )
    return loader(args.adapter, **required)


def _runtime_summary(runtime: object) -> str:
    identity = getattr(runtime, "adapter_identity", None)
    placement = getattr(runtime, "runtime_identity", None)
    if placement is None:
        placement = getattr(runtime, "placement", None)
    if placement is None and isinstance(identity, Mapping):
        placement = identity.get("placement")
    if isinstance(placement, Mapping):
        device = placement.get("resolved_device", placement.get("device", "?"))
        dtype = placement.get("resolved_dtype", placement.get("dtype", "?"))
        summary = (
            f"device={_safe_inline(device)} · base dtype={_safe_inline(dtype)}"
        )
        adapter_dtypes = placement.get("adapter_artifact_dtypes")
        if isinstance(adapter_dtypes, Mapping) and adapter_dtypes:
            labels = ", ".join(
                f"{_safe_inline(name, max_chars=80)}×{_safe_inline(count, max_chars=40)}"
                for name, count in sorted(adapter_dtypes.items(), key=lambda item: str(item[0]))
            )
            summary += f" · adapter artifact={labels}"
        return summary
    return "runtime placement recorded in the result report"


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if args.command is None and args.theorem:
        parser.error("a theorem requires the positional `prove-model` command")
    if args.command == "prove-model" and not args.theorem:
        parser.error("prove-model requires a closed PA theorem")

    driver, policy_repl = _load_components()
    try:
        results_dir = policy_repl._validated_results_dir(args.results_dir)
        budget = policy_repl.SearchBudget(
            max_depth=args.depth,
            beam_width=args.beam,
            candidates_per_state=args.candidates,
            max_model_calls=args.model_calls,
            max_states=args.states,
        )
    except (TypeError, ValueError) as exc:
        raise SystemExit(f"invalid local shell configuration: {_safe_inline(exc)}") from None

    if args.diagnostic:
        print("PEANO MODEL LAB — DIAGNOSTIC / NOT PRODUCTION", flush=True)
    print(f"Loading attested Peano adapter once from {args.adapter} …", flush=True)
    try:
        runtime = _load_runtime(policy_repl.load_model_runtime, args)
    except Exception as exc:
        message = " ".join(_plain_string(exc).split()) or type(exc).__name__
        raise SystemExit(f"could not load the attested adapter: {_safe_inline(message)}") from None
    print(f"Model ready · {_runtime_summary(runtime)}", flush=True)

    shell = PeanoModelShell(
        lab_session=driver.LabSession(),
        runtime=runtime,
        budget=budget,
        results_dir=results_dir,
        normalize_theorem=policy_repl.normalize_theorem_input,
        run_checked_search=policy_repl.run_checked_search,
        save_attempt=policy_repl.save_attempt,
        live_mode=args.live,
    )
    if args.command == "prove-model":
        theorem = " ".join(args.theorem)
        return shell.dispatch(f"pa prove-model {theorem}").exit_code
    return run_interactive(shell)


if __name__ == "__main__":
    raise SystemExit(main())
