"""A deliberately small, untrusted Vampire boundary for Peano Hydra A3.

This module is *not* a proof rule.  It translates one closed Peano formula and
an explicitly selected subset of a caller-owned premise allow-list to a
deterministic classical TPTP FOF problem.  Vampire's bytes and SZS status are
retained only as inert search evidence.  Reconstruction is deliberately tiny:
a closed reflexive equality emits ``refl``; otherwise, exactly one explicitly
selected PA axiom emits ``apply NAME`` and exactly one explicitly selected
public theorem emits ``use NAME`` followed by ``apply NAME``.  One additional
shape is admitted: a top-level conjunction with exactly two selected PA axioms
emits ``split`` followed by one ``apply`` per branch, in selection order.  These
are only ordinary public commands.  Peano Lab's transactional macro runner
must execute them and freshly replay the resulting certificate against the
original goal before a QED can be admitted.

The subprocess boundary intentionally accepts a real executable path and an
exact argument tuple.  Tests use a tiny fake executable when Vampire is not
installed.  It is not yet registered directly with H0's frozen ``Dispatch``
host: that host permits exactly one process, while a source adapter that
translates/parses around a separate Vampire binary necessarily needs a broker
plus one solver process.  A later reviewed host-protocol amendment (or one
self-contained linked executable) must resolve that process topology; this
module does not weaken or silently reseal the H0.3 contract.

The translator covers the primitive closed PA formula grammar, but it makes no
constructive-validity claim: Vampire is a classical first-order prover.  Its
output may guide constructive proof search only through independently checked
ordinary Peano commands.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import shutil
import signal
import stat
import subprocess
import tempfile
import time

from peano_lab.kernel.formulas import (
    And,
    Bot,
    Eq,
    Exists,
    Forall,
    Formula,
    Imp,
    Or,
    ParseError,
    parse_formula_with_names,
    pretty_formula,
)
from peano_lab.kernel.terms import Add, Mul, Succ, Term, Var, Zero

from .macros import DISPATCH_RESPONSE_FORMAT, DISPATCH_RESPONSE_VERSION


VAMPIRE_PROBLEM_FORMAT = "peano-hydra-vampire-problem"
VAMPIRE_PROBLEM_VERSION = 1
VAMPIRE_TRANSLATION_CLASS = "closed-primitive-pa-to-classical-tptp-fof-v1"
VAMPIRE_RECONSTRUCTION_CLASS = (
    "closed-refl-single-premise-or-two-pa-axiom-and-to-public-commands-v3"
)

MAX_VAMPIRE_PROBLEM_BYTES = 4 * 1024 * 1024
MAX_VAMPIRE_OUTPUT_BYTES = 2 * 1024 * 1024
MAX_VAMPIRE_WALL_TIME_MS = 600_000
MAX_VAMPIRE_FORMULA_BYTES = 64 * 1024
MAX_VAMPIRE_EXECUTABLE_BYTES = 256 * 1024 * 1024
MAX_VAMPIRE_ARGUMENTS = 128
MAX_VAMPIRE_ARGUMENT_BYTES = 64 * 1024
MAX_PREMISES = 128

_PREMISE_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_']{0,127}\Z")
_SZS_STATUS = re.compile(
    rb"(?m)^%[ \t]+SZS[ \t]+status[ \t]+([A-Za-z][A-Za-z0-9_]*)"
)
_SZS_TO_DISPATCH = {
    "Theorem": "theorem",
    "Unsatisfiable": "unsat",
    "Satisfiable": "sat",
    "CounterSatisfiable": "sat",
    "Timeout": "resource-limit",
    "ResourceOut": "resource-limit",
    "MemoryOut": "resource-limit",
    "GaveUp": "unknown",
    "Unknown": "unknown",
}


class VampireAdapterError(ValueError):
    """A deterministic adapter input or bounded invocation is malformed."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_formula(source: object, *, label: str) -> tuple[str, Formula]:
    if type(source) is not str or not source:
        raise VampireAdapterError(f"{label} must be non-empty canonical Peano text")
    try:
        source_bytes = source.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise VampireAdapterError(f"{label} is not UTF-8: {exc}") from None
    if len(source_bytes) > MAX_VAMPIRE_FORMULA_BYTES:
        raise VampireAdapterError(f"{label} exceeds its byte bound")
    try:
        formula, free_names = parse_formula_with_names(source)
    except (ParseError, TypeError, ValueError, RecursionError) as exc:
        raise VampireAdapterError(f"{label} is not a Peano formula: {exc}") from None
    if free_names:
        raise VampireAdapterError(
            f"{label} is outside the closed-formula translation class; "
            f"free names: {', '.join(free_names)}"
        )
    canonical = pretty_formula(formula, [])
    if canonical != source:
        raise VampireAdapterError(
            f"{label} is not canonical; expected {canonical!r}"
        )
    return canonical, formula


@dataclass(frozen=True, slots=True)
class VampirePremise:
    """One closed premise that the caller explicitly permits Vampire to see."""

    name: str
    kind: str
    formula: str

    def __post_init__(self) -> None:
        if type(self.name) is not str or _PREMISE_NAME.fullmatch(self.name) is None:
            raise VampireAdapterError("premise name must be one bounded Peano identifier")
        if type(self.kind) is not str or self.kind not in {
            "pa-axiom",
            "public-theorem",
        }:
            raise VampireAdapterError(
                "premise kind must be exactly 'pa-axiom' or 'public-theorem'"
            )
        canonical, _ = _canonical_formula(
            self.formula, label=f"premise {self.name!r}"
        )
        object.__setattr__(self, "formula", canonical)


@dataclass(frozen=True, slots=True)
class VampireProblem:
    """Canonical TPTP bytes plus their complete source-symbol projection."""

    goal: str
    premises: tuple[VampirePremise, ...]
    requested_premises: tuple[str, ...]
    tptp_bytes: bytes
    symbol_map: tuple[tuple[str, str], ...]
    format: str = VAMPIRE_PROBLEM_FORMAT
    v: int = VAMPIRE_PROBLEM_VERSION
    translation_class: str = VAMPIRE_TRANSLATION_CLASS

    def __post_init__(self) -> None:
        if (
            type(self.format) is not str
            or self.format != VAMPIRE_PROBLEM_FORMAT
            or type(self.v) is not int
            or self.v != VAMPIRE_PROBLEM_VERSION
        ):
            raise VampireAdapterError("unsupported Vampire problem identity")
        if (
            type(self.translation_class) is not str
            or self.translation_class != VAMPIRE_TRANSLATION_CLASS
        ):
            raise VampireAdapterError("unsupported Vampire translation class")
        canonical, _ = _canonical_formula(self.goal, label="Vampire goal")
        if canonical != self.goal:
            raise VampireAdapterError("Vampire problem goal lost canonical form")
        if type(self.premises) is not tuple:
            raise VampireAdapterError("Vampire problem premises must be an exact tuple")
        if len(self.premises) > MAX_PREMISES or not all(
            type(item) is VampirePremise for item in self.premises
        ):
            raise VampireAdapterError("Vampire problem premises exceed their type/size bound")
        if type(self.requested_premises) is not tuple:
            raise VampireAdapterError(
                "Vampire requested premises must be an exact text tuple"
            )
        if len(self.requested_premises) > MAX_PREMISES or not all(
            type(item) is str for item in self.requested_premises
        ):
            raise VampireAdapterError(
                "Vampire requested premises exceed their type/size bound"
            )
        if tuple(item.name for item in self.premises) != self.requested_premises:
            raise VampireAdapterError(
                "Vampire problem premises disagree with requested premise order"
            )
        if type(self.tptp_bytes) is not bytes or not self.tptp_bytes.endswith(b"\n"):
            raise VampireAdapterError("Vampire TPTP problem must be LF-terminated bytes")
        if not 1 <= len(self.tptp_bytes) <= MAX_VAMPIRE_PROBLEM_BYTES:
            raise VampireAdapterError("Vampire TPTP problem exceeds its byte bound")
        try:
            self.tptp_bytes.decode("ascii")
        except UnicodeDecodeError:
            raise VampireAdapterError("Vampire TPTP problem must be ASCII") from None
        if type(self.symbol_map) is not tuple or not all(
            type(item) is tuple
            and len(item) == 2
            and all(type(part) is str and bool(part) for part in item)
            for item in self.symbol_map
        ):
            raise VampireAdapterError("Vampire symbol map must be an exact text-pair tuple")
        labels = tuple(item[0] for item in self.symbol_map)
        if len(labels) != len(set(labels)):
            raise VampireAdapterError("Vampire symbol-map labels must be unique")

    @property
    def sha256(self) -> str:
        return _sha256(self.tptp_bytes)


@dataclass(frozen=True, slots=True)
class VampireEvidence:
    """Bounded inert solver transcript and host observations.

    ``status`` is a dispatch hint only.  Neither it nor ``szs_statuses`` can
    construct a proof or bypass public-command reconstruction.
    """

    raw_output: bytes
    status: str
    szs_statuses: tuple[str, ...]
    parse_error: str | None = None
    exit_code: int | None = None
    timed_out: bool = False
    output_limited: bool = False
    wall_time_ms: int | None = None
    executable_sha256: str | None = None
    arguments: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if type(self.raw_output) is not bytes:
            raise VampireAdapterError("Vampire raw output must be exact bytes")
        if len(self.raw_output) > MAX_VAMPIRE_OUTPUT_BYTES:
            raise VampireAdapterError("Vampire raw output exceeds its global bound")
        if type(self.status) is not str or self.status not in {
            "theorem",
            "unsat",
            "sat",
            "unknown",
            "resource-limit",
        }:
            raise VampireAdapterError("Vampire evidence has an unsupported status")
        if type(self.szs_statuses) is not tuple:
            raise VampireAdapterError("Vampire SZS statuses must be an exact text tuple")
        if len(self.szs_statuses) > 256 or not all(
            type(item) is str and bool(item) for item in self.szs_statuses
        ):
            raise VampireAdapterError("Vampire SZS statuses exceed their type/size bound")
        if len(self.szs_statuses) != len(set(self.szs_statuses)):
            raise VampireAdapterError("Vampire SZS statuses must be unique")
        if self.parse_error is not None and type(self.parse_error) is not str:
            raise VampireAdapterError("Vampire parse_error must be text or null")
        if self.exit_code is not None and type(self.exit_code) is not int:
            raise VampireAdapterError("Vampire exit_code must be an integer or null")
        if type(self.timed_out) is not bool or type(self.output_limited) is not bool:
            raise VampireAdapterError("Vampire limit observations must be Booleans")
        if self.wall_time_ms is not None and (
            type(self.wall_time_ms) is not int or self.wall_time_ms < 0
        ):
            raise VampireAdapterError("Vampire wall_time_ms must be non-negative or null")
        if self.executable_sha256 is not None and (
            type(self.executable_sha256) is not str
            or re.fullmatch(r"[0-9a-f]{64}", self.executable_sha256) is None
        ):
            raise VampireAdapterError("Vampire executable identity is malformed")
        if type(self.arguments) is not tuple or not all(
            type(item) is str for item in self.arguments
        ):
            raise VampireAdapterError("Vampire arguments must be an exact text tuple")

    @property
    def raw_sha256(self) -> str:
        return _sha256(self.raw_output)


class _TptpEncoder:
    def __init__(self) -> None:
        self.next_variable = 0

    def term(self, value: Term, environment: tuple[str, ...]) -> str:
        if type(value) is Var:
            if not 0 <= value.index < len(environment):
                raise VampireAdapterError("formula contains an unbound de Bruijn variable")
            return environment[value.index]
        if type(value) is Zero:
            return "z"
        if type(value) is Succ:
            return f"s({self.term(value.term, environment)})"
        if type(value) is Add:
            return (
                f"add({self.term(value.left, environment)},"
                f"{self.term(value.right, environment)})"
            )
        if type(value) is Mul:
            return (
                f"mul({self.term(value.left, environment)},"
                f"{self.term(value.right, environment)})"
            )
        raise VampireAdapterError("formula contains an unsupported PA term")

    def formula(self, value: Formula, environment: tuple[str, ...] = ()) -> str:
        if type(value) is Eq:
            return (
                f"({self.term(value.left, environment)} = "
                f"{self.term(value.right, environment)})"
            )
        if type(value) is Bot:
            return "$false"
        if type(value) in {Imp, And, Or}:
            connective = {Imp: "=>", And: "&", Or: "|"}[type(value)]
            return (
                f"({self.formula(value.left, environment)} {connective} "
                f"{self.formula(value.right, environment)})"
            )
        if type(value) in {Forall, Exists}:
            variable = f"X{self.next_variable}"
            self.next_variable += 1
            quantifier = "!" if type(value) is Forall else "?"
            return (
                f"({quantifier} [{variable}] : "
                f"{self.formula(value.body, (variable,) + environment)})"
            )
        raise VampireAdapterError("formula contains an unsupported PA constructor")


def _encode_formula(formula: Formula) -> str:
    return _TptpEncoder().formula(formula)


def emit_tptp_problem(
    goal: str,
    allowed_premises: tuple[VampirePremise, ...],
    *,
    requested_premises: tuple[str, ...] | None = None,
) -> VampireProblem:
    """Emit one deterministic TPTP problem from an explicit premise authority.

    ``allowed_premises`` is the complete caller-supplied authority.  When
    ``requested_premises`` is supplied, every requested name must occur in
    that authority; a masked/unknown name fails before any problem bytes are
    built.  No ambient theorem catalog is consulted.
    """

    canonical_goal, goal_formula = _canonical_formula(goal, label="Vampire goal")
    if type(allowed_premises) is not tuple:
        raise VampireAdapterError("allowed_premises must be an exact VampirePremise tuple")
    if len(allowed_premises) > MAX_PREMISES:
        raise VampireAdapterError(f"at most {MAX_PREMISES} premises may be disclosed")
    if not all(type(item) is VampirePremise for item in allowed_premises):
        raise VampireAdapterError("allowed_premises must be an exact VampirePremise tuple")
    names = tuple(item.name for item in allowed_premises)
    if len(names) != len(set(names)):
        raise VampireAdapterError("allowed premise names must be unique")
    if requested_premises is None:
        requested = names
    else:
        if type(requested_premises) is not tuple:
            raise VampireAdapterError(
                "requested_premises must be an exact Peano-name tuple"
            )
        if len(requested_premises) > MAX_PREMISES or not all(
            type(item) is str and _PREMISE_NAME.fullmatch(item) is not None
            for item in requested_premises
        ):
            raise VampireAdapterError(
                "requested_premises must be an exact Peano-name tuple"
            )
        requested = requested_premises
    if len(requested) != len(set(requested)):
        raise VampireAdapterError("requested premise names must be unique")
    by_name = {item.name: item for item in allowed_premises}
    rejected = tuple(name for name in requested if name not in by_name)
    if rejected:
        raise VampireAdapterError(
            "requested premise is not in the explicit allow-list: "
            + ", ".join(rejected)
        )
    selected = tuple(by_name[name] for name in requested)

    lines = [
        "% peano-hydra-vampire-problem-v1",
        f"% translation {VAMPIRE_TRANSLATION_CLASS}",
    ]
    symbol_map: list[tuple[str, str]] = [
        ("z", "term:zero"),
        ("s", "term:successor"),
        ("add", "term:addition"),
        ("mul", "term:multiplication"),
    ]
    for index, premise in enumerate(selected):
        label = f"premise_{index:04d}"
        _, formula = _canonical_formula(
            premise.formula, label=f"premise {premise.name!r}"
        )
        lines.append(f"fof({label},axiom,{_encode_formula(formula)}).")
        symbol_map.append((label, f"{premise.kind}:{premise.name}"))
    lines.append(f"fof(goal,conjecture,{_encode_formula(goal_formula)}).")
    symbol_map.append(("goal", "conjecture:original-goal"))
    encoded = ("\n".join(lines) + "\n").encode("ascii")
    if len(encoded) > MAX_VAMPIRE_PROBLEM_BYTES:
        raise VampireAdapterError("emitted Vampire problem exceeds its byte bound")
    return VampireProblem(
        goal=canonical_goal,
        premises=selected,
        requested_premises=requested,
        tptp_bytes=encoded,
        symbol_map=tuple(symbol_map),
    )


def parse_vampire_output(raw: bytes) -> VampireEvidence:
    """Parse bounded raw Vampire bytes into inert SZS evidence.

    Unknown encodings, unknown statuses, and contradictory statuses are kept as
    ``unknown`` evidence.  Parsing never emits a proof or a public command.
    """

    if type(raw) is not bytes:
        raise VampireAdapterError("Vampire output must be exact bytes")
    if len(raw) > MAX_VAMPIRE_OUTPUT_BYTES:
        raise VampireAdapterError("Vampire output exceeds its global byte bound")
    matches: list[str] = []
    parse_error: str | None = None
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError:
        parse_error = "Vampire output is not UTF-8"
    else:
        for match in _SZS_STATUS.finditer(raw):
            status = match.group(1).decode("ascii")
            if status not in matches:
                matches.append(status)
    mapped = tuple(
        _SZS_TO_DISPATCH[item]
        for item in matches
        if item in _SZS_TO_DISPATCH
    )
    if parse_error is not None:
        status = "unknown"
    elif not mapped:
        status = "unknown"
        if matches:
            parse_error = "Vampire emitted no recognized SZS status"
    elif len(set(mapped)) != 1:
        status = "unknown"
        parse_error = "Vampire emitted contradictory SZS statuses"
    else:
        status = mapped[0]
    return VampireEvidence(
        raw_output=raw,
        status=status,
        szs_statuses=tuple(matches),
        parse_error=parse_error,
    )


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_arguments(arguments: object) -> tuple[str, ...]:
    if type(arguments) is not tuple:
        raise VampireAdapterError("Vampire arguments must be an exact text tuple")
    if len(arguments) > MAX_VAMPIRE_ARGUMENTS:
        raise VampireAdapterError("too many Vampire arguments")
    if not all(type(item) is str for item in arguments):
        raise VampireAdapterError("Vampire arguments must be an exact text tuple")
    encoded = 0
    for item in arguments:
        if not item or "\x00" in item:
            raise VampireAdapterError("Vampire arguments must be non-empty NUL-free text")
        encoded += len(item.encode("utf-8"))
    if encoded > MAX_VAMPIRE_ARGUMENT_BYTES:
        raise VampireAdapterError("Vampire arguments exceed their byte bound")
    return arguments


def _dispatch_status_after_host(
    parsed: VampireEvidence,
    *,
    exit_code: int,
    timed_out: bool,
    output_limited: bool,
) -> str:
    if timed_out or output_limited:
        return "resource-limit"
    if exit_code != 0:
        return "unknown"
    return parsed.status


def run_vampire(
    executable: str | Path,
    problem: VampireProblem,
    *,
    arguments: tuple[str, ...] = (),
    wall_time_ms: int,
    output_bytes: int,
) -> VampireEvidence:
    """Invoke a real Vampire-compatible executable without a shell.

    The exact deterministic problem is written to one temporary ``problem.p``
    and its path is appended after the caller's pinned arguments.  Wall time
    is enforced by the parent and stdout+stderr size by ``RLIMIT_FSIZE`` on a
    regular temporary file.  The executable remains untrusted and its result
    is returned only as :class:`VampireEvidence`.
    """

    if type(problem) is not VampireProblem:
        raise VampireAdapterError("run_vampire needs an exact VampireProblem")
    checked_arguments = _validate_arguments(arguments)
    if type(wall_time_ms) is not int or not 1 <= wall_time_ms <= MAX_VAMPIRE_WALL_TIME_MS:
        raise VampireAdapterError("Vampire wall_time_ms is outside its bound")
    if type(output_bytes) is not int or not 1 <= output_bytes <= MAX_VAMPIRE_OUTPUT_BYTES:
        raise VampireAdapterError("Vampire output_bytes is outside its bound")
    try:
        path = Path(executable).resolve(strict=True)
        metadata = path.stat()
    except OSError as exc:
        raise VampireAdapterError(f"cannot inspect Vampire executable: {exc}") from None
    if (
        not stat.S_ISREG(metadata.st_mode)
        or not 1 <= metadata.st_size <= MAX_VAMPIRE_EXECUTABLE_BYTES
        or not os.access(path, os.X_OK)
    ):
        raise VampireAdapterError("Vampire executable must be one non-empty executable file")
    executable_sha256 = _file_sha256(path)

    def limit_output() -> None:
        resource.setrlimit(resource.RLIMIT_FSIZE, (output_bytes, output_bytes))
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))

    started = time.monotonic()
    timed_out = False
    exit_code: int
    with tempfile.TemporaryDirectory(prefix="peano-hydra-vampire-") as directory:
        root = Path(directory)
        invoked_path = root / "vampire"
        try:
            shutil.copyfile(path, invoked_path)
            invoked_path.chmod(0o500)
        except OSError as exc:
            raise VampireAdapterError(
                f"cannot prepare detached Vampire executable: {exc}"
            ) from None
        if _file_sha256(invoked_path) != executable_sha256:
            raise VampireAdapterError("copied Vampire executable identity mismatch")
        problem_path = root / "problem.p"
        problem_path.write_bytes(problem.tptp_bytes)
        output_path = root / "vampire.out"
        with output_path.open("w+b") as output:
            try:
                process = subprocess.Popen(
                    [str(invoked_path), *checked_arguments, str(problem_path)],
                    stdin=subprocess.DEVNULL,
                    stdout=output,
                    stderr=subprocess.STDOUT,
                    close_fds=True,
                    start_new_session=True,
                    preexec_fn=limit_output,
                )
            except OSError as exc:
                raise VampireAdapterError(f"cannot execute Vampire: {exc}") from None
            try:
                exit_code = process.wait(timeout=wall_time_ms / 1_000)
            except subprocess.TimeoutExpired:
                timed_out = True
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except (ProcessLookupError, PermissionError):
                    process.kill()
                exit_code = process.wait()
            output.flush()
            output.seek(0)
            raw = output.read(output_bytes + 1)
    wall_observed = max(0, int((time.monotonic() - started) * 1_000))
    signal_exit = -exit_code if exit_code < 0 else None
    # Treat an exactly full file as exhausted too.  This can reject the rare
    # legitimate transcript whose size equals the ceiling, but it prevents a
    # partial write at RLIMIT_FSIZE from masquerading as complete evidence.
    output_limited = len(raw) >= output_bytes or signal_exit == getattr(signal, "SIGXFSZ", 25)
    if len(raw) > output_bytes:
        raw = raw[:output_bytes]
    parsed = parse_vampire_output(raw)
    return replace(
        parsed,
        status=_dispatch_status_after_host(
            parsed,
            exit_code=exit_code,
            timed_out=timed_out,
            output_limited=output_limited,
        ),
        exit_code=exit_code,
        timed_out=timed_out,
        output_limited=output_limited,
        wall_time_ms=wall_observed,
        executable_sha256=executable_sha256,
        arguments=checked_arguments,
    )


def _checked_reconstruction_premises(
    problem: VampireProblem,
) -> tuple[VampirePremise, ...]:
    """Revalidate every command-bearing premise field at the last boundary."""

    if type(problem.premises) is not tuple or len(problem.premises) > MAX_PREMISES:
        raise VampireAdapterError(
            "reconstruction premises must be one bounded exact tuple"
        )
    checked: list[VampirePremise] = []
    for premise in problem.premises:
        if type(premise) is not VampirePremise:
            raise VampireAdapterError(
                "reconstruction premise must be an exact VampirePremise"
            )
        # Frozen dataclasses are not treated as a substitute for validating the
        # exact name which will be interpolated into public surface text.
        if (
            type(premise.name) is not str
            or _PREMISE_NAME.fullmatch(premise.name) is None
        ):
            raise VampireAdapterError("reconstruction premise name is malformed")
        if premise.kind not in {"pa-axiom", "public-theorem"}:
            raise VampireAdapterError("reconstruction premise kind is unsupported")
        _canonical_formula(
            premise.formula, label=f"reconstruction premise {premise.name!r}"
        )
        checked.append(premise)
    names = tuple(premise.name for premise in checked)
    if len(names) != len(set(names)):
        raise VampireAdapterError("reconstruction premise names must be unique")
    if type(problem.requested_premises) is not tuple or problem.requested_premises != names:
        raise VampireAdapterError(
            "reconstruction premises are not exactly the explicitly requested premises"
        )
    return tuple(checked)


def reconstruct_public_commands(
    problem: VampireProblem,
    evidence: VampireEvidence,
) -> tuple[str, ...]:
    """Return only independently reconstructable ordinary Peano commands.

    A theorem-like status is only a hint to try a deterministic public plan.
    The reflexivity test and premise identity come from the original checked
    :class:`VampireProblem`, never from solver text.  Beyond ``refl``, the v3
    class admits only one explicitly selected premise: PA axioms are tried by
    ``apply``; public theorems are first imported by ``use`` and then applied.
    It also admits one ordered two-premise shape for a top-level conjunction,
    but only when both selected premises are PA axioms.  Every other
    multi-premise problem remains commandless.
    Whether any command is relevant is decided solely by transactional public
    execution and, on closure, a fresh original-goal kernel replay.
    """

    if type(problem) is not VampireProblem or type(evidence) is not VampireEvidence:
        raise VampireAdapterError("reconstruction needs exact problem and evidence values")
    if evidence.status not in {"theorem", "unsat"}:
        return ()
    premises = _checked_reconstruction_premises(problem)
    _, formula = _canonical_formula(problem.goal, label="Vampire goal")
    if type(formula) is Eq and formula.left == formula.right:
        return ("refl",)

    if len(premises) == 1:
        premise = premises[0]
        if premise.kind == "pa-axiom":
            return (f"apply {premise.name}",)
        return (f"use {premise.name}", f"apply {premise.name}")
    if (
        type(formula) is And
        and len(premises) == 2
        and all(premise.kind == "pa-axiom" for premise in premises)
    ):
        return (
            "split",
            f"apply {premises[0].name}",
            f"apply {premises[1].name}",
        )
    return ()


def dispatch_response(problem: VampireProblem, evidence: VampireEvidence) -> bytes:
    """Build the frozen Dispatch response; its commands still require replay."""

    commands = reconstruct_public_commands(problem, evidence)
    record = {
        "format": DISPATCH_RESPONSE_FORMAT,
        "public_commands": list(commands),
        "status": evidence.status,
        "steps_used": len(commands),
        "v": DISPATCH_RESPONSE_VERSION,
    }
    return json.dumps(
        record,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


__all__ = [
    "VAMPIRE_PROBLEM_FORMAT",
    "VAMPIRE_PROBLEM_VERSION",
    "VAMPIRE_TRANSLATION_CLASS",
    "VAMPIRE_RECONSTRUCTION_CLASS",
    "MAX_VAMPIRE_PROBLEM_BYTES",
    "MAX_VAMPIRE_OUTPUT_BYTES",
    "MAX_VAMPIRE_WALL_TIME_MS",
    "MAX_VAMPIRE_FORMULA_BYTES",
    "MAX_VAMPIRE_EXECUTABLE_BYTES",
    "VampireAdapterError",
    "VampirePremise",
    "VampireProblem",
    "VampireEvidence",
    "emit_tptp_problem",
    "parse_vampire_output",
    "run_vampire",
    "reconstruct_public_commands",
    "dispatch_response",
]
