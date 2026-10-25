"""Explicit local solver policies and bounded, advisory termination evidence.

The installed package's original smoke record covers only ``standard``.
These profiles authorize fixed runtime arguments; they are not solver proofs
or claims that the higher profiles have already passed a live experiment.
"""
from __future__ import annotations

import re
import signal
from types import MappingProxyType

RUNTIME_POLICY = "hydra-playground-vampire-runtime-policy-v2"
PROFILE_NAMES = ("standard", "deep", "research")
_PROFILES = MappingProxyType({
    # Solver seconds, CPU seconds, wall seconds, internal MiB, sampled RSS MiB.
    # Advanced profiles reserve RSS headroom above Vampire's internal budget.
    "standard": (1, 2, 3, 256, 256),
    "deep": (5, 6, 8, 256, 512),
    "research": (15, 16, 18, 256, 512),
})
MAX_INPUT = 64 * 1024
MAX_OUTPUT = 256 * 1024
MAX_EVIDENCE_LINES = 8
MAX_EVIDENCE_CHARACTERS = 240


def solver_limits(profile="standard"):
    """Return a fresh copy of the fixed bounds, never arbitrary overrides.

    RSS is sampled by the owning HTTP parent. Vampire's internal ``-m`` budget
    is distinct from process RSS, which also includes executable/runtime
    overhead. The helper enforces CPU and wall time separately.
    """
    if type(profile) is not str or profile not in _PROFILES:
        raise ValueError("Vampire profile must be standard, deep, or research.")
    solver, cpu, wall, internal_memory, sampled_rss = _PROFILES[profile]
    return {"profile": profile, "solver_seconds": solver, "cpu_seconds": cpu,
            "wall_seconds": wall, "solver_memory_mib": internal_memory,
            "sampled_rss_bytes": sampled_rss * 1024**2,
            "input_bytes": MAX_INPUT, "output_bytes": MAX_OUTPUT,
            "max_simultaneous_children": 1}


def solver_args(profile="standard"):
    limits = solver_limits(profile)
    return ["--mode", "vampire", "--input_syntax", "tptp", "--proof", "tptp",
            "--output_axiom_names", "on", "-t", str(limits["solver_seconds"]),
            "-m", str(limits["solver_memory_mib"])]


def helper_arguments(profile="standard"):
    solver_limits(profile)  # Strict enum validation even for false-like values.
    return [] if profile == "standard" else ["--profile", profile]


def parse_helper_arguments(arguments):
    """Only canonical profile commands, plus the existing operator probe."""
    if type(arguments) is not list or any(type(item) is not str for item in arguments):
        raise ValueError("Invalid fixed Vampire helper arguments.")
    if arguments == ["--version"]:
        return "standard", True
    for profile in PROFILE_NAMES:
        if arguments == helper_arguments(profile):
            return profile, False
    raise ValueError("Only the exact fixed Vampire profile command is permitted.")


_SZS = re.compile(r"^%\s*SZS status ([A-Za-z]+)\b")
_TIME = re.compile(r"^%\s*(?:Time limit reached!?|Termination reason:\s*Time limit)\s*$")
_TERMINATION = re.compile(r"^%\s*Termination (?:reason|phase):")
_TIMEOUT_STATUSES = frozenset({"Timeout", "CPUTimeout", "WCTimeout"})
_RESOURCE_STATUSES = frozenset({"MemoryOut", "ResourceOut"})
_ERROR_STATUSES = frozenset({"Error", "OSError", "InputError", "SyntaxError",
                             "SemanticError", "TypeError", "UsageError"})


def classify_termination(stdout, stderr, *, exit_code, wall_timed_out=False, output_limited=False):
    """Recognize resource stops from captured output or an owned watchdog.

    Classification only explains a stop. In particular, ``completed`` requires
    an actual zero exit and does not mean that the native theorem was proved.
    The SZS resource names follow https://tptp.org/UserDocs/SZSOntology/ .
    The two ``Time limit`` markers also occur in the preserved local 5.0.1
    Fermat diagnostic, which exits 1 without any SZS status line.
    """
    if type(stdout) is not str or type(stderr) is not str:
        raise ValueError("Vampire termination output must be text.")
    if len(stdout.encode("utf-8")) + len(stderr.encode("utf-8")) > MAX_OUTPUT:
        raise ValueError("Vampire termination output exceeds its capture bound.")
    statuses, evidence, fallback = set(), [], []
    time_marker = False
    evidence_truncated = False
    for stream, output in (("stdout", stdout), ("stderr", stderr)):
        for line in output.splitlines():
            match = _SZS.match(line)
            if match:
                statuses.add(match.group(1))
            timed = _TIME.fullmatch(line) is not None
            time_marker = time_marker or timed
            item = {"stream": stream, "text": line[:MAX_EVIDENCE_CHARACTERS]}
            if match or timed or _TERMINATION.match(line):
                if len(evidence) < MAX_EVIDENCE_LINES:
                    evidence.append(item)
                else:
                    evidence_truncated = True
                evidence_truncated = evidence_truncated or len(line) > MAX_EVIDENCE_CHARACTERS
            elif line.strip() and len(fallback) < 2:
                fallback.append(item)
    szs_status = next(iter(statuses)) if len(statuses) == 1 else None
    status, reason = ("completed", "exit_zero") if type(exit_code) is int and exit_code == 0 else ("failed", "process_exit")
    if output_limited:
        status, reason = "output_limit", "captured_output_limit"
    elif wall_timed_out:
        status, reason = "timeout", "outer_wall_watchdog"
    elif len(statuses) > 1:
        status, reason = "failed", "conflicting_szs_statuses"
    elif time_marker:
        status, reason = "timeout", "solver_time_limit"
    elif szs_status in _TIMEOUT_STATUSES:
        status, reason = "timeout", "szs_" + szs_status
    elif szs_status in _RESOURCE_STATUSES:
        status, reason = "resource_limit", "szs_" + szs_status
    elif szs_status in _ERROR_STATUSES:
        status, reason = "failed", "szs_" + szs_status
    elif type(exit_code) is int and exit_code == -signal.SIGALRM:
        status, reason = "timeout", "helper_wall_alarm"
    elif type(exit_code) is int and exit_code == -signal.SIGXCPU:
        status, reason = "timeout", "cpu_limit_signal"
    elif type(exit_code) is int and exit_code < 0:
        # SIGKILL alone does not identify a CPU, memory or cancellation cause.
        status, reason = "failed", "process_signal"
    return {"status": status, "timed_out": status == "timeout",
            "resource_limited": status == "resource_limit", "output_limited": bool(output_limited),
            "termination": {"reason": reason, "szs_status": szs_status,
                            "szs_status_conflict": len(statuses) > 1,
                            "evidence": evidence or (fallback if status != "completed" else []),
                            "evidence_truncated": evidence_truncated}}
