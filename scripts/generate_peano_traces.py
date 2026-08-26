#!/usr/bin/env python3
"""Generate deterministic, kernel-checked Peano Lab training traces.

The raw output is deliberately *only* the binding version-1 stream: tactic
records followed immediately by their four-field session footer.  Batch-only
provenance belongs in the separate JSON manifest, never in those records.

Five families are generated:

* one honest ``auto`` attempt for every theorem-ladder statement;
* one checked replay of every authored theorem-ladder script (dependencies are
  explicit implication hypotheses, exactly as in the library replay); and
* many seed-named reflexive arithmetic variants for scale;
* a smaller addition-commutativity tranche for richer search trajectories; and
* bounded closed-coefficient normalization examples for ``norm_num``.

Every generated proof is owned by :class:`ProofSession`.  Successful sessions
receive a ``qed: true`` footer only after ``checked_final`` has asked the
independent kernel to check the completed certificate against that owner's
original target.  Search failures are useful data and end with ``qed: false``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import random
import sys
import tempfile
import unicodedata
from collections import Counter
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any, Sequence, TextIO


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PYTHON_ROOT = REPOSITORY_ROOT / "peano-lab" / "py"
CHECKER_SOURCE = PYTHON_ROOT / "peano_lab" / "kernel" / "checker.py"
PEANO_PACKAGE_ROOT = PYTHON_ROOT / "peano_lab"
if str(PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_ROOT))

from peano_lab.engine.search import auto  # noqa: E402
from peano_lab.engine.state import ProofState, proof_size, start  # noqa: E402
from peano_lab.engine.tactics import (  # noqa: E402
    InvalidProof,
    TacticError,
    apply_tactic,
    checked_final,
)
from peano_lab.engine.trace import TRACE_VERSION, TraceLogger  # noqa: E402
from peano_lab.kernel.formulas import (  # noqa: E402
    Formula,
    parse_formula_with_names,
    pretty_formula,
)
from peano_lab.library.theorems import (  # noqa: E402
    THEOREMS,
    TheoremSpec,
    replay_target,
)
from peano_lab.ui.prove import ProofSession, ReplayStep  # noqa: E402


MANIFEST_FORMAT = "peano-lab-trace-generation-manifest"
MANIFEST_VERSION = 1
GENERATOR_VERSION = 2
DEFAULT_SEED = 0
DEFAULT_RENAMED = 1_500
DEFAULT_COMMUTED = 96
DEFAULT_NUMERIC = 96
MAX_NUMERIC = 96
DEFAULT_AUTO_DEPTH = 5
DEFAULT_AUTO_MAX_NODES = 5_000


class GenerationError(RuntimeError):
    """The batch generator violated a soundness or reproducibility invariant."""


@dataclass(frozen=True, slots=True)
class GenerationConfig:
    """Deterministic generation controls.

    The defaults deliberately clear ten thousand distinct transition records.
    ``renamed`` is the inexpensive bulk family; ``commuted`` is smaller because
    proving addition commutativity from cold explores a larger search tree.
    ``numeric`` exercises bounded certificate-producing normalization of closed
    coefficients beneath a leading universal binder.
    """

    seed: int = DEFAULT_SEED
    renamed: int = DEFAULT_RENAMED
    commuted: int = DEFAULT_COMMUTED
    numeric: int = DEFAULT_NUMERIC
    auto_depth: int = DEFAULT_AUTO_DEPTH
    auto_max_nodes: int = DEFAULT_AUTO_MAX_NODES
    ladder_auto: bool = True
    ladder_scripts: bool = True

    def __post_init__(self) -> None:
        for field in ("renamed", "commuted", "numeric"):
            value = getattr(self, field)
            if type(value) is not int or value < 0:
                raise ValueError(f"{field} must be a non-negative integer")
        if self.numeric > MAX_NUMERIC:
            raise ValueError(f"numeric must be at most {MAX_NUMERIC}")
        for field in ("auto_depth", "auto_max_nodes"):
            value = getattr(self, field)
            if type(value) is not int or value < 1:
                raise ValueError(f"{field} must be a positive integer")
        if type(self.seed) is not int:
            raise ValueError("seed must be an integer")
        if type(self.ladder_auto) is not bool or type(self.ladder_scripts) is not bool:
            raise ValueError("ladder generation switches must be booleans")


class _DigestingSink:
    """Forward text while measuring the exact UTF-8 raw artifact."""

    def __init__(self, sink: TextIO) -> None:
        if not callable(getattr(sink, "write", None)):
            raise TypeError("trace sink must provide write(text)")
        self.sink = sink
        self.digest = hashlib.sha256()
        self.bytes_written = 0

    def write(self, text: str) -> int:
        result = self.sink.write(text)
        if result is not None and (type(result) is not int or result != len(text)):
            raise GenerationError(
                "trace sink short write: "
                f"expected {len(text)} characters, accepted {result!r}"
            )
        encoded = text.encode("utf-8")
        self.digest.update(encoded)
        self.bytes_written += len(encoded)
        return len(text)


def _new_session(target: Formula, source: str, trace: TraceLogger) -> ProofSession:
    """Create one exact owner with no hidden theorem authority."""

    return ProofSession(
        state=start(target),
        original_target=target,
        original_names=(),
        target_source=source,
        classical=False,
        trace=trace,
    )


def _apply(owner: ProofSession, tactic: str, args: str = "") -> ProofSession:
    state = apply_tactic(
        owner.state,
        tactic,
        args,
        trace=owner.trace,
        classical=owner.classical,
    )
    return _replace_state(owner, state)


def _replace_state(owner: ProofSession, state: ProofState) -> ProofSession:
    """Keep the UI owner's replay journal aligned in programmatic batches."""

    old_count = len(owner.state.history)
    if state.history[:old_count] != owner.state.history:
        raise GenerationError("a generated tactic changed earlier proof history")
    additions = tuple(
        ReplayStep(f"{step.tactic} {step.args}".strip(), owner.classical)
        for step in state.history[old_count:]
    )
    return replace(
        owner,
        state=state,
        replay_steps=owner.replay_steps + additions,
    )


def _controlled_failure(
    owner: ProofSession, tactic: str, args: str = ""
) -> tuple[ProofSession, str]:
    """Record one guaranteed transactional failure and verify the contract."""

    before = owner.state
    try:
        _apply(owner, tactic, args)
    except TacticError as exc:
        if owner.state != before:
            raise GenerationError("a failed tactic mutated its ProofSession state")
        return owner, str(exc)
    raise GenerationError(f"controlled failure unexpectedly succeeded: {tactic} {args}".strip())


def _qed(owner: ProofSession) -> int:
    """Emit the only successful footer path: independent checked finalization."""

    try:
        certificate = checked_final(
            owner.state,
            owner.original_target,
            classical=owner.classical,
        )
    except InvalidProof as exc:
        raise GenerationError(f"the independent kernel rejected generated QED: {exc}") from exc
    nodes = proof_size(certificate)
    owner.trace.footer(
        qed=True,
        theorem=owner.original_target,
        proof_size=nodes,
        names=owner.original_names,
    )
    return nodes


def _not_qed(owner: ProofSession) -> None:
    owner.trace.footer(
        qed=False,
        theorem=owner.original_target,
        proof_size=proof_size(owner.state.partial),
        names=owner.original_names,
    )


def _record_summary(
    owner: ProofSession,
    *,
    kind: str,
    family: str,
    source: str,
    target_mode: str,
    result: str,
    kernel_checked: bool,
    controlled_failures: int,
    proof_nodes: int | None = None,
    error: str | None = None,
    theorem: str | None = None,
    variant: int | None = None,
    names: Sequence[str] = (),
    template: str | None = None,
) -> dict[str, Any]:
    records = owner.trace.records
    transition_records = sum(1 for record in records if record.get("v") == TRACE_VERSION)
    failure_records = sum(1 for record in records if record.get("status") == "error")
    return {
        "session": owner.trace.session_id,
        "kind": kind,
        "family": family,
        "theorem": theorem,
        "template": template,
        "variant": variant,
        "source": source,
        "target_mode": target_mode,
        "surface_names": list(names),
        "result": result,
        "kernel_checked": kernel_checked,
        "proof_nodes": proof_nodes,
        "transition_records": transition_records,
        "failure_records": failure_records,
        "controlled_failures": controlled_failures,
        "error": error,
    }


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(128 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _semantic_tree_provenance() -> dict[str, Any]:
    """Fingerprint every Peano Lab Python source that can affect generation."""

    digest = hashlib.sha256()
    sources = sorted(PEANO_PACKAGE_ROOT.rglob("*.py"))
    for path in sources:
        relative = path.relative_to(REPOSITORY_ROOT).as_posix().encode("utf-8")
        content_digest = bytes.fromhex(_sha256_file(path))
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        digest.update(content_digest)
    return {
        "root": "peano-lab/py/peano_lab",
        "pattern": "**/*.py",
        "files": len(sources),
        "sha256": digest.hexdigest(),
    }


def _source_provenance() -> dict[str, Any]:
    """Identify the exact generator and trusted checker used for this run."""

    generator_source = Path(__file__).resolve()
    return {
        "sources": {
            "generator": {
                "path": "scripts/generate_peano_traces.py",
                "sha256": _sha256_file(generator_source),
            },
            "trusted_checker": {
                "path": "peano-lab/py/peano_lab/kernel/checker.py",
                "sha256": _sha256_file(CHECKER_SOURCE),
            },
        },
        "semantic_source_tree": _semantic_tree_provenance(),
        "runtime": {
            "implementation": platform.python_implementation(),
            "version": platform.python_version(),
        },
    }


def _generation_fingerprint(
    config: GenerationConfig,
    theorems: Sequence[TheoremSpec],
    provenance: dict[str, Any],
) -> str:
    """Name a run by every input which can change its trace stream.

    A seed alone is not a run identity: two configurations with the same seed
    otherwise produce colliding session IDs and cannot be collated.  Source,
    checker, runtime, complete semantic configuration, and theorem fixtures
    are all included in this canonical digest.
    """

    payload = {
        "format": MANIFEST_FORMAT,
        "generator_version": GENERATOR_VERSION,
        "trace_version": TRACE_VERSION,
        "config": asdict(config),
        "provenance": provenance,
        "theorems": [
            {
                "name": spec.name,
                "statement": spec.statement,
                "dependencies": list(spec.dependencies),
                "script": list(spec.script),
            }
            for spec in theorems
        ],
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class _Batch:
    def __init__(
        self,
        config: GenerationConfig,
        sink: _DigestingSink,
        theorems: Sequence[TheoremSpec],
    ) -> None:
        self.config = config
        self.sink = sink
        self.theorems = tuple(theorems)
        self.provenance = _source_provenance()
        self.run_fingerprint = _generation_fingerprint(
            config, self.theorems, self.provenance
        )
        self.rng = random.Random(config.seed)
        self.serial = 0
        self.sessions: list[dict[str, Any]] = []

    def _trace(self) -> TraceLogger:
        session_id = f"peano-{self.run_fingerprint[:24]}-{self.serial:06d}"
        self.serial += 1
        return TraceLogger(self.sink, session_id=session_id)

    def _token(self, label: str, variant: int) -> str:
        return f"{label}_{variant}_{self.rng.getrandbits(48):012x}"

    def ladder_auto(self, spec: TheoremSpec) -> None:
        target, free_names = parse_formula_with_names(spec.statement)
        if free_names:
            raise GenerationError(f"ladder statement {spec.name!r} is not closed")
        owner = _new_session(target, spec.statement, self._trace())
        missing = f"missing_auto_{spec.name}"
        owner, _ = _controlled_failure(owner, "exact", missing)
        typed_depth = str(self.config.auto_depth)
        try:
            state = auto(
                owner.state,
                typed_depth,
                trace=owner.trace,
                classical=False,
                max_nodes=self.config.auto_max_nodes,
            )
        except TacticError as exc:
            _not_qed(owner)
            self.sessions.append(
                _record_summary(
                    owner,
                    kind="ladder_auto",
                    family=spec.name,
                    theorem=spec.name,
                    source=spec.statement,
                    target_mode="original_statement",
                    result="search_failure",
                    kernel_checked=False,
                    controlled_failures=1,
                    error=str(exc),
                )
            )
            return
        owner = _replace_state(owner, state)
        nodes = _qed(owner)
        self.sessions.append(
            _record_summary(
                owner,
                kind="ladder_auto",
                family=spec.name,
                theorem=spec.name,
                source=spec.statement,
                target_mode="original_statement",
                result="qed",
                kernel_checked=True,
                controlled_failures=1,
                proof_nodes=nodes,
            )
        )

    def ladder_script(self, spec: TheoremSpec) -> None:
        """Trace the same dependency-curried script that M7 checks in CI."""

        target = replay_target(spec)
        source = pretty_formula(target, [])
        owner = _new_session(target, source, self._trace())
        owner, _ = _controlled_failure(
            owner, "exact", f"missing_script_{spec.name}"
        )
        try:
            for dependency in spec.dependencies:
                owner = _apply(owner, "intro", dependency)
            for command in spec.script:
                pieces = command.split(maxsplit=1)
                owner = _apply(
                    owner,
                    pieces[0],
                    pieces[1] if len(pieces) == 2 else "",
                )
        except TacticError as exc:
            raise GenerationError(
                f"checked library script {spec.name!r} stopped replaying: {exc}"
            ) from exc
        nodes = _qed(owner)
        self.sessions.append(
            _record_summary(
                owner,
                kind="ladder_script",
                family=spec.name,
                theorem=spec.name,
                source=source,
                target_mode="dependency_curried_statement",
                result="qed",
                kernel_checked=True,
                controlled_failures=1,
                proof_nodes=nodes,
            )
        )

    def renamed_variant(self, variant: int) -> None:
        name = self._token("a", variant)
        missing = self._token("missing", variant)
        source = (
            f"forall {name}. {name} = {name} /\\ "
            f"{name} + 0 = {name} /\\ S {name} = S {name}"
        )
        target, free_names = parse_formula_with_names(source)
        if free_names:
            raise GenerationError("a renamed generated theorem unexpectedly has free names")
        owner = _new_session(target, source, self._trace())
        owner, _ = _controlled_failure(owner, "exact", missing)
        owner = _apply(owner, "intro", name)
        try:
            state = auto(
                owner.state,
                str(self.config.auto_depth),
                trace=owner.trace,
                classical=False,
                max_nodes=self.config.auto_max_nodes,
            )
        except TacticError as exc:
            raise GenerationError(f"renamed variant {variant} failed auto: {exc}") from exc
        owner = _replace_state(owner, state)
        nodes = _qed(owner)
        self.sessions.append(
            _record_summary(
                owner,
                kind="variant_renamed",
                family="generated_reflexive_arithmetic",
                template="reflexive_arithmetic_conjunction",
                variant=variant,
                source=source,
                target_mode="generated_statement",
                result="qed",
                kernel_checked=True,
                controlled_failures=1,
                proof_nodes=nodes,
                names=(name,),
            )
        )

    def commuted_variant(self, variant: int) -> None:
        left_name = self._token("a", variant)
        right_name = self._token("b", variant)
        missing = self._token("missing", variant)
        reverse = bool(self.rng.getrandbits(1))
        if reverse:
            equation = f"{right_name} + {left_name} = {left_name} + {right_name}"
            template = "add_comm_reversed"
        else:
            equation = f"{left_name} + {right_name} = {right_name} + {left_name}"
            template = "add_comm_forward"
        source = f"forall {left_name} {right_name}. {equation}"
        target, free_names = parse_formula_with_names(source)
        if free_names:
            raise GenerationError("a commuted generated theorem unexpectedly has free names")
        owner = _new_session(target, source, self._trace())
        owner, _ = _controlled_failure(owner, "exact", missing)
        # Retaining the seeded surface name in the goal makes alpha-renamed
        # traces distinct even though the kernel correctly erases binder names.
        owner = _apply(owner, "intro", left_name)
        try:
            state = auto(
                owner.state,
                str(self.config.auto_depth),
                trace=owner.trace,
                classical=False,
                max_nodes=self.config.auto_max_nodes,
            )
        except TacticError as exc:
            raise GenerationError(f"commuted variant {variant} failed auto: {exc}") from exc
        owner = _replace_state(owner, state)
        nodes = _qed(owner)
        self.sessions.append(
            _record_summary(
                owner,
                kind="variant_commuted",
                family="add_comm",
                template=template,
                variant=variant,
                source=source,
                target_mode="generated_statement",
                result="qed",
                kernel_checked=True,
                controlled_failures=1,
                proof_nodes=nodes,
                names=(left_name, right_name),
            )
        )

    def numeric_variant(self, variant: int) -> None:
        """Trace checked normalization of one bounded closed coefficient."""

        name = self._token("n", variant)
        left = 2 + variant % 8
        right = 2 + (variant // 8) % 4
        # The complete 8 x 4 x 3 grid gives the 96 distinct allowed shapes.
        # Its maximum value 9 * 5 + 2 = 47 leaves room for the unary numeral
        # beneath the surrounding multiplication inside the depth-64 limit.
        offset = (variant // 32) % 3
        value = left * right + offset
        source = (
            f"forall {name}. ({left} * {right} + {offset}) * {name} = "
            f"{value} * {name}"
        )
        target, free_names = parse_formula_with_names(source)
        if free_names:
            raise GenerationError(
                "a numeric generated theorem unexpectedly has free names"
            )
        owner = _new_session(target, source, self._trace())
        # Pin both the zero-argument grammar and transactional failure record.
        owner, _ = _controlled_failure(owner, "norm_num", "now")
        try:
            owner = _apply(owner, "norm_num")
        except TacticError as exc:
            raise GenerationError(
                f"numeric variant {variant} failed norm_num: {exc}"
            ) from exc
        nodes = _qed(owner)
        self.sessions.append(
            _record_summary(
                owner,
                kind="variant_numeric",
                family="generated_closed_coefficients",
                template="closed_coefficient_normalization",
                variant=variant,
                source=source,
                target_mode="generated_statement",
                result="qed",
                kernel_checked=True,
                controlled_failures=1,
                proof_nodes=nodes,
                names=(name,),
            )
        )

    def run(self) -> dict[str, Any]:
        if self.config.ladder_auto:
            for spec in self.theorems:
                self.ladder_auto(spec)
        if self.config.ladder_scripts:
            for spec in self.theorems:
                self.ladder_script(spec)

        schedule = [
            *(("renamed", index) for index in range(self.config.renamed)),
            *(("commuted", index) for index in range(self.config.commuted)),
            *(("numeric", index) for index in range(self.config.numeric)),
        ]
        self.rng.shuffle(schedule)
        for kind, variant in schedule:
            if kind == "renamed":
                self.renamed_variant(variant)
            elif kind == "commuted":
                self.commuted_variant(variant)
            elif kind == "numeric":
                self.numeric_variant(variant)
            else:  # pragma: no cover - schedule construction is local and exact
                raise GenerationError(f"unknown generated family {kind!r}")

        kinds = Counter(str(session["kind"]) for session in self.sessions)
        results = Counter(str(session["result"]) for session in self.sessions)
        transitions = sum(int(session["transition_records"]) for session in self.sessions)
        failures = sum(int(session["failure_records"]) for session in self.sessions)
        controlled = sum(int(session["controlled_failures"]) for session in self.sessions)
        checked = sum(bool(session["kernel_checked"]) for session in self.sessions)
        return {
            "format": MANIFEST_FORMAT,
            "version": MANIFEST_VERSION,
            "generator_version": GENERATOR_VERSION,
            "trace_version": TRACE_VERSION,
            "run_fingerprint": self.run_fingerprint,
            "seed": self.config.seed,
            "config": asdict(self.config),
            "provenance": self.provenance,
            "theorem_ladder": [spec.name for spec in self.theorems],
            "counts": {
                "sessions": len(self.sessions),
                "transition_records": transitions,
                "footer_records": len(self.sessions),
                "failure_records": failures,
                "controlled_failure_records": controlled,
                "kernel_checked_sessions": checked,
                "sessions_by_kind": dict(sorted(kinds.items())),
                "sessions_by_result": dict(sorted(results.items())),
            },
            "raw": {
                "encoding": "utf-8",
                "bytes": self.sink.bytes_written,
                "sha256": self.sink.digest.hexdigest(),
            },
            "sessions": self.sessions,
        }


def generate(
    sink: TextIO,
    config: GenerationConfig = GenerationConfig(),
    *,
    theorems: Sequence[TheoremSpec] = THEOREMS,
) -> dict[str, Any]:
    """Stream a raw corpus to ``sink`` and return its deterministic manifest."""

    if not theorems:
        raise ValueError("generation needs at least one theorem-ladder specification")
    digesting = _DigestingSink(sink)
    return _Batch(config, digesting, theorems).run()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        required=True,
        help="raw concatenated v1 JSONL path, or - for standard output",
    )
    parser.add_argument(
        "--manifest",
        help="provenance JSON path (default: OUTPUT.manifest.json)",
    )
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--renamed", type=int, default=DEFAULT_RENAMED)
    parser.add_argument("--commuted", type=int, default=DEFAULT_COMMUTED)
    parser.add_argument("--numeric", type=int, default=DEFAULT_NUMERIC)
    parser.add_argument("--auto-depth", type=int, default=DEFAULT_AUTO_DEPTH)
    parser.add_argument(
        "--auto-max-nodes", type=int, default=DEFAULT_AUTO_MAX_NODES
    )
    parser.add_argument(
        "--ladder-auto",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="include one honest auto attempt per ladder theorem",
    )
    parser.add_argument(
        "--ladder-scripts",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="include checked dependency-curried authored replays",
    )
    return parser


def _manifest_path(output: str, explicit: str | None) -> Path:
    if explicit:
        return Path(explicit)
    if output == "-":
        raise ValueError("--manifest is required when --output is -")
    return Path(output + ".manifest.json")


def _same_output(path_a: Path, path_b: Path) -> bool:
    try:
        if path_a.resolve(strict=False) == path_b.resolve(strict=False):
            return True
    except (OSError, RuntimeError):
        pass
    try:
        name_a = unicodedata.normalize("NFC", path_a.name).casefold()
        name_b = unicodedata.normalize("NFC", path_b.name).casefold()
        if (
            name_a == name_b
            and os.path.samefile(path_a.parent, path_b.parent)
        ):
            return True
    except OSError:
        pass
    try:
        return path_a.exists() and path_b.exists() and os.path.samefile(path_a, path_b)
    except OSError:
        return False


def _canonical_parts(path: Path) -> tuple[str, ...]:
    try:
        absolute = path.resolve(strict=False)
    except (OSError, RuntimeError):
        absolute = path.absolute()
    return tuple(
        unicodedata.normalize("NFC", part).casefold() for part in absolute.parts
    )


def _nested_outputs(path_a: Path, path_b: Path) -> bool:
    parts_a = _canonical_parts(path_a)
    parts_b = _canonical_parts(path_b)
    return (
        len(parts_a) < len(parts_b) and parts_a == parts_b[: len(parts_a)]
    ) or (
        len(parts_b) < len(parts_a) and parts_b == parts_a[: len(parts_b)]
    )


def _preflight_destination(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if os.path.lexists(path) and not os.path.isfile(path):
        raise ValueError(f"output artifact must be a regular file or absent: {path}")


def _temporary_text_path(destination: Path) -> tuple[TextIO, Path]:
    stream = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="\n",
        prefix=f".{destination.name}.",
        suffix=".tmp",
        dir=destination.parent,
        delete=False,
    )
    return stream, Path(stream.name)


def _finish_text_file(stream: TextIO) -> None:
    stream.flush()
    os.fsync(stream.fileno())
    stream.close()


def _atomic_write_text(destination: Path, text: str) -> None:
    stream, temporary = _temporary_text_path(destination)
    try:
        stream.write(text)
        _finish_text_file(stream)
        os.replace(temporary, destination)
    except BaseException:
        if not stream.closed:
            stream.close()
        temporary.unlink(missing_ok=True)
        raise


def _reserved_backup_path(path: Path) -> Path:
    descriptor, name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".bak", dir=path.parent
    )
    os.close(descriptor)
    reserved = Path(name)
    reserved.unlink()
    return reserved


def _publish_temporary_set(artifacts: Sequence[tuple[Path, Path]]) -> None:
    """Publish durable temporary files together, restoring old files on error."""

    pending = {destination: temporary for destination, temporary in artifacts}
    backups: dict[Path, Path] = {}
    installed: list[Path] = []
    try:
        for destination, _ in artifacts:
            if os.path.lexists(destination):
                backup = _reserved_backup_path(destination)
                backups[destination] = backup
                os.replace(destination, backup)

        for destination, temporary in artifacts:
            installed.append(destination)
            os.replace(temporary, destination)
            pending.pop(destination)
    except BaseException as original:
        rollback_errors: list[str] = []
        rollback_exceptions: list[BaseException] = []
        for destination in reversed(installed):
            try:
                destination.unlink(missing_ok=True)
            except BaseException as exc:
                rollback_exceptions.append(exc)
                if destination not in backups and os.path.lexists(destination):
                    rollback_errors.append(f"remove {destination}: {exc}")
        for destination, backup in reversed(tuple(backups.items())):
            if not os.path.lexists(backup):
                if os.path.lexists(destination):
                    backups.pop(destination)
                else:
                    rollback_errors.append(
                        f"restore {destination}: both destination and backup are missing"
                    )
                continue
            try:
                os.replace(backup, destination)
                backups.pop(destination)
            except BaseException as exc:
                rollback_exceptions.append(exc)
                if not os.path.lexists(backup) and os.path.lexists(destination):
                    backups.pop(destination)
                else:
                    rollback_errors.append(f"restore {destination}: {exc}")
        if rollback_errors:
            preserved = tuple(
                backup for backup in backups.values() if os.path.lexists(backup)
            )
            backups.clear()
            raise RuntimeError(
                "trace generation failed and rollback was incomplete: "
                + "; ".join(rollback_errors)
                + "; backups preserved at "
                + ", ".join(str(path) for path in preserved)
            ) from original
        if rollback_exceptions:
            raise rollback_exceptions[0] from original
        raise
    finally:
        for temporary in (*pending.values(), *backups.values()):
            temporary.unlink(missing_ok=True)


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        config = GenerationConfig(
            seed=args.seed,
            renamed=args.renamed,
            commuted=args.commuted,
            numeric=args.numeric,
            auto_depth=args.auto_depth,
            auto_max_nodes=args.auto_max_nodes,
            ladder_auto=args.ladder_auto,
            ladder_scripts=args.ladder_scripts,
        )
        manifest_path = _manifest_path(args.output, args.manifest)
    except ValueError as exc:
        parser.error(str(exc))

    if args.output == "-":
        try:
            _preflight_destination(manifest_path)
        except (OSError, ValueError) as exc:
            parser.error(str(exc))
        manifest = generate(sys.stdout, config)
        _atomic_write_text(
            manifest_path,
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        )
    else:
        output_path = Path(args.output)
        if _same_output(output_path, manifest_path):
            parser.error("--output and --manifest must name different files")
        if _nested_outputs(output_path, manifest_path):
            parser.error("--output and --manifest must not contain one another")
        try:
            _preflight_destination(manifest_path)
            _preflight_destination(output_path)
        except (OSError, ValueError) as exc:
            parser.error(str(exc))
        raw_stream, raw_temporary = _temporary_text_path(output_path)
        manifest_temporary: Path | None = None
        try:
            stream = raw_stream
            manifest = generate(stream, config)
            _finish_text_file(raw_stream)
            manifest_text = (
                json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
            )
            manifest_stream, manifest_temporary = _temporary_text_path(manifest_path)
            manifest_stream.write(manifest_text)
            _finish_text_file(manifest_stream)

            # Generation and both durable temporary writes succeeded.  The
            # publication helper rolls the pair back on an ordinary failure.
            _publish_temporary_set(
                (
                    (output_path, raw_temporary),
                    (manifest_path, manifest_temporary),
                )
            )
            raw_temporary = None
            manifest_temporary = None
        except BaseException:
            if not raw_stream.closed:
                raw_stream.close()
            if raw_temporary is not None:
                raw_temporary.unlink(missing_ok=True)
            if manifest_temporary is not None:
                manifest_temporary.unlink(missing_ok=True)
            raise
    counts = manifest["counts"]
    print(
        "generated "
        f"{counts['transition_records']} transitions in {counts['sessions']} sessions; "
        f"{counts['kernel_checked_sessions']} kernel-checked QEDs; "
        f"manifest {manifest_path}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
