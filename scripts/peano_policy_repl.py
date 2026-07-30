#!/usr/bin/env python3
"""Keep one trained Peano policy loaded for kernel-guided theorem proving.

This is an interactive inference client, not a trusted prover.  Model output is
searched through Peano Lab's public tactic surface.  A proof is displayed and
saved only after a second, independent kernel replay against the theorem that
the user entered.

The module intentionally imports only the Python standard library at import
time.  In particular, ``--help`` and unit tests do not need torch,
transformers, or a GPU.  Model and Peano Lab imports happen in
``load_model_runtime`` after command-line validation.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
from importlib import metadata as importlib_metadata
import json
import math
import os
from pathlib import Path
import platform
import re
import secrets
import sys
import tempfile
from typing import Callable, Mapping
import unicodedata


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PEANO_PYTHON = REPOSITORY_ROOT / "peano-lab" / "py"
RESULTS_ROOT = REPOSITORY_ROOT / "results"
DEFAULT_RESULTS_DIR = RESULTS_ROOT / "peano-policy" / "interactive"
DEFAULT_ADAPTER = (
    RESULTS_ROOT / "peano-policy" / "qwen3-1.7b-lora-v3-library"
)
REPORT_FORMAT = "peano-policy-interactive-result"
REPORT_VERSION = 1
MAX_CANDIDATES = 16
MAX_BEAM_WIDTH = 64
MAX_MODEL_CALLS = 4_096
MAX_STATES = 65_536
MAX_NEW_TOKENS = 1_024
_STEM_RE = re.compile(r"[0-9A-Za-z._-]{1,160}")
_RUNTIME_PACKAGES = (
    "accelerate",
    "peft",
    "safetensors",
    "tokenizers",
    "torch",
    "transformers",
)


def _runtime_software_record() -> dict[str, object]:
    packages: dict[str, str | None] = {}
    for name in _RUNTIME_PACKAGES:
        try:
            packages[name] = importlib_metadata.version(name)
        except importlib_metadata.PackageNotFoundError:
            packages[name] = None
    return {
        "python": platform.python_version(),
        "machine": platform.machine(),
        "packages": packages,
    }


@dataclass(frozen=True, slots=True)
class SearchBudget:
    """User-facing bounds converted to the search module's authority object."""

    max_depth: int = 32
    beam_width: int = 4
    candidates_per_state: int = 4
    max_model_calls: int = 128
    max_states: int = 2_048

    def __post_init__(self) -> None:
        limits = {
            "max_depth": (self.max_depth, 32),
            "beam_width": (self.beam_width, MAX_BEAM_WIDTH),
            "candidates_per_state": (
                self.candidates_per_state,
                MAX_CANDIDATES,
            ),
            "max_model_calls": (self.max_model_calls, MAX_MODEL_CALLS),
            "max_states": (self.max_states, MAX_STATES),
        }
        for name, (value, maximum) in limits.items():
            if type(value) is not int or not 1 <= value <= maximum:
                raise ValueError(f"{name} must lie between 1 and {maximum}")

    def to_dict(self) -> dict[str, int]:
        return {
            "max_depth": self.max_depth,
            "beam_width": self.beam_width,
            "candidates_per_state": self.candidates_per_state,
            "max_model_calls": self.max_model_calls,
            "max_states": self.max_states,
        }


@dataclass(frozen=True, slots=True)
class ReplRuntime:
    """Loaded untrusted policy plus the independent execution authorities."""

    policy: object
    capabilities: object
    classical: bool
    adapter_identity: Mapping[str, object]
    search: Callable[..., object]
    verify: Callable[..., object]
    make_limits: Callable[..., object]
    runtime_identity: Mapping[str, object] | None = None


@dataclass(frozen=True, slots=True)
class CheckedAttempt:
    """One publishable result; ``proof_script`` exists only after replay."""

    report: dict[str, object]
    proof_script: str | None

    @property
    def proved(self) -> bool:
        return self.proof_script is not None


@dataclass(frozen=True, slots=True)
class SavedArtifacts:
    report: Path
    proof: Path | None


def _surface_capabilities(environment: object) -> object:
    from peano_lab.ui.prove import SurfaceCapabilities

    identity = getattr(environment, "capabilities", None)
    label = getattr(identity, "label", None)
    commands = getattr(identity, "allowed_commands", None)
    theorems = getattr(identity, "allowed_theorems", None)
    if label not in {"model-v2", "model-v3"}:
        raise ValueError(
            "the interactive client requires an attested model-v2/v3 adapter"
        )
    return SurfaceCapabilities(
        label=label,
        allowed_commands=None if commands is None else frozenset(commands),
        allowed_theorems=None if theorems is None else frozenset(theorems),
    )


def load_model_runtime(
    adapter_dir: Path,
    *,
    seed: int,
    max_new_tokens: int,
    sample: bool,
    temperature: float,
    top_p: float,
    diagnostic_mode: bool = False,
    device: str = "auto",
    dtype: str = "auto",
    local_files_only: bool | None = None,
    cache_dir: Path | None = None,
) -> ReplRuntime:
    """Validate and load one adapter once, after all lightweight CLI checks."""

    for import_root in (REPOSITORY_ROOT, PEANO_PYTHON):
        if str(import_root) not in sys.path:
            sys.path.insert(0, str(import_root))

    from peano_lab.batch import verify_proof
    from training.peano_policy.contract import attested_training_environment
    from training.peano_policy.generate import (
        PeanoPolicyAdapter,
        PeanoPolicyCandidateAdapter,
        adapter_provenance,
        load_adapter,
    )
    from training.peano_policy.search import SearchLimits, search

    absolute_adapter = adapter_dir.resolve(strict=True)
    if not absolute_adapter.is_dir():
        raise ValueError(f"adapter is not a directory: {absolute_adapter}")
    model, tokenizer, manifest = load_adapter(
        absolute_adapter,
        seed=seed,
        diagnostic_mode=diagnostic_mode,
        device=device,
        dtype=dtype,
        local_files_only=local_files_only,
        cache_dir=cache_dir,
    )
    environment = attested_training_environment(manifest)
    capabilities = _surface_capabilities(environment)
    provenance = adapter_provenance(absolute_adapter, manifest)
    base_policy = PeanoPolicyAdapter(
        model=model,
        tokenizer=tokenizer,
        environment=environment,
        name=f"peano-policy:{capabilities.label}-interactive",
        max_new_tokens=max_new_tokens,
        do_sample=sample,
        temperature=temperature,
        top_p=top_p,
        provenance=provenance,
    )
    policy = PeanoPolicyCandidateAdapter(base_policy, seed=seed)
    identity = {
        "directory": str(absolute_adapter),
        "policy": policy.evaluation_identity,
    }
    placement = getattr(model, "peano_runtime_placement", None)
    if callable(getattr(placement, "to_record", None)):
        runtime_identity = placement.to_record()
    elif isinstance(placement, Mapping):
        runtime_identity = dict(placement)
    else:
        runtime_identity = {
            "device": str(getattr(model, "device", "unknown")),
            "dtype": str(getattr(model, "dtype", "unknown")),
        }
    runtime_identity = dict(runtime_identity)
    runtime_identity["software"] = _runtime_software_record()
    diagnostic = manifest.get("diagnostic")
    tensor_audit = (
        diagnostic.get("adapter_tensor_audit")
        if isinstance(diagnostic, Mapping)
        else None
    )
    artifact_dtypes = (
        tensor_audit.get("dtypes") if isinstance(tensor_audit, Mapping) else None
    )
    if isinstance(artifact_dtypes, Mapping) and all(
        type(name) is str and type(count) is int
        for name, count in artifact_dtypes.items()
    ):
        runtime_identity["adapter_artifact_dtypes"] = dict(artifact_dtypes)
    return ReplRuntime(
        policy=policy,
        capabilities=capabilities,
        classical=False,
        adapter_identity=identity,
        search=search,
        verify=verify_proof,
        make_limits=SearchLimits,
        runtime_identity=runtime_identity,
    )


def _safe_one_line(value: object, *, label: str) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{label} must be non-empty text")
    if value.splitlines() != [value]:
        raise ValueError(f"{label} must fit on one line")
    if any(
        unicodedata.category(character) in {"Cc", "Cf", "Cs", "Zl", "Zp"}
        for character in value
    ):
        raise ValueError(f"{label} contains an unsafe control or format character")
    return value


def normalize_theorem_input(line: object) -> str:
    """Accept a bare formula or either Peano proof-command prefix."""

    source = _safe_one_line(line, label="input").strip()
    for prefix in ("pa prove-model ", "pa prove "):
        if source.startswith(prefix):
            source = source[len(prefix) :].strip()
            break
    if not source:
        raise ValueError("theorem must be non-empty text")
    if source in {"qed", "quit", "exit"} or source.startswith(":"):
        raise ValueError("enter a closed PA formula, not a proof-session command")
    return source


def _canonical_json_copy(value: object) -> object:
    return json.loads(
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    )


def _capability_record(capabilities: object) -> dict[str, object]:
    def names(field: str) -> list[str] | None:
        value = getattr(capabilities, field, None)
        return None if value is None else sorted(value)

    return {
        "label": getattr(capabilities, "label", None),
        "allowed_commands": names("allowed_commands"),
        "allowed_theorems": names("allowed_theorems"),
    }


def _search_record(result: object) -> dict[str, object]:
    to_dict = getattr(result, "to_dict", None)
    if not callable(to_dict):
        raise TypeError("search result does not provide a structured record")
    record = to_dict()
    copied = _canonical_json_copy(record)
    if type(copied) is not dict:
        raise TypeError("search result record must be a JSON object")
    return copied


def _verification_record(replay: object) -> dict[str, object]:
    to_dict = getattr(replay, "to_dict", None)
    if not callable(to_dict):
        raise TypeError("kernel replay does not provide a structured record")
    try:
        record = to_dict(include_trace=False)
    except TypeError:
        record = to_dict()
    copied = _canonical_json_copy(record)
    if type(copied) is not dict:
        raise TypeError("kernel replay record must be a JSON object")
    return copied


def run_checked_search(
    theorem: str,
    runtime: ReplRuntime,
    budget: SearchBudget,
    *,
    created_at: str | None = None,
    on_event: Callable[[Mapping[str, object]], object] | None = None,
) -> CheckedAttempt:
    """Search and, on success, independently replay before publication."""

    if on_event is not None and not callable(on_event):
        raise TypeError("on_event must be callable or None")
    # Keep weights resident, but reset per-theorem counters and the deterministic
    # call-index seed schedule when the concrete policy supports a fresh view.
    fresh = getattr(runtime.policy, "fresh", None)
    policy = fresh() if callable(fresh) else runtime.policy
    limits = runtime.make_limits(**budget.to_dict())
    search_options = {
        "capabilities": runtime.capabilities,
        "classical": runtime.classical,
        "limits": limits,
    }
    if on_event is not None:
        search_options["on_event"] = on_event
    result = runtime.search(theorem, policy, **search_options)
    status = getattr(result, "status", None)
    proved = getattr(result, "proved", None)
    commands = getattr(result, "commands", None)
    certificate_nodes = getattr(result, "certificate_nodes", None)
    canonical_theorem = getattr(result, "theorem", None)
    if (
        type(status) is not str
        or type(proved) is not bool
        or type(commands) is not tuple
        or not all(type(command) is str for command in commands)
        or type(canonical_theorem) is not str
    ):
        raise TypeError("search returned an incompatible result")
    if proved != (status == "proof"):
        raise RuntimeError("search proof status is internally inconsistent")

    replay_record: dict[str, object] | None = None
    proof_script: str | None = None
    if proved:
        if not commands or type(certificate_nodes) is not int:
            raise RuntimeError("search claimed a proof without certificate data")
        from training.peano_policy.events import emit_event

        emit_event(
            on_event,
            "independent_replay_started",
            theorem=canonical_theorem,
            path=commands,
        )
        request_hash = hashlib.sha256(theorem.encode("utf-8")).hexdigest()[:16]
        try:
            replay = runtime.verify(
                theorem,
                commands,
                request_id=f"interactive-{request_hash}",
                classical=runtime.classical,
                capabilities=runtime.capabilities,
            )
        except Exception as exc:
            message = " ".join(str(exc).split()) or type(exc).__name__
            emit_event(
                on_event,
                "independent_replay_finished",
                status="rejected",
                kernel_checked=False,
                proof_nodes=None,
                message=message[:1_000],
            )
            raise
        expected_surface = getattr(runtime.capabilities, "label", None)
        replay_mismatch = (
            getattr(replay, "status", None) != "proved"
            or getattr(replay, "kernel_checked", None) is not True
            or getattr(replay, "theorem", None) != canonical_theorem
            or getattr(replay, "proof_nodes", None) != certificate_nodes
            or getattr(replay, "tactics_applied", None) != len(commands)
            or getattr(replay, "failed_tactics", None) != 0
            or getattr(replay, "surface", None) != expected_surface
            or getattr(replay, "classical", None) is not runtime.classical
        )
        if replay_mismatch:
            emit_event(
                on_event,
                "independent_replay_finished",
                status="rejected",
                kernel_checked=(
                    getattr(replay, "kernel_checked", None) is True
                ),
                proof_nodes=(
                    getattr(replay, "proof_nodes", None)
                    if type(getattr(replay, "proof_nodes", None)) is int
                    else None
                ),
                message="independent replay did not exactly match searched proof",
            )
            raise RuntimeError(
                "refusing to publish: independent kernel replay did not "
                "exactly confirm the searched proof"
            )
        emit_event(
            on_event,
            "independent_replay_finished",
            status="accepted",
            kernel_checked=True,
            proof_nodes=certificate_nodes,
            message=None,
        )
        replay_record = _verification_record(replay)
        proof_script = "\n".join(
            (f"pa prove {canonical_theorem}", *commands, "qed", "")
        )

    timestamp = created_at or datetime.now(timezone.utc).replace(
        microsecond=0
    ).isoformat().replace("+00:00", "Z")
    _safe_one_line(timestamp, label="timestamp")
    publication: dict[str, object]
    if proof_script is None:
        publication = {"status": "no-checked-proof", "script_sha256": None}
    else:
        publication = {
            "status": "kernel-checked-proof",
            "script_sha256": hashlib.sha256(
                proof_script.encode("utf-8")
            ).hexdigest(),
        }
    report = {
        "format": REPORT_FORMAT,
        "v": REPORT_VERSION,
        "created_at": timestamp,
        "request": {
            "theorem_source": theorem,
            "canonical_theorem": canonical_theorem,
        },
        "adapter": _canonical_json_copy(dict(runtime.adapter_identity)),
        "runtime": (
            None
            if runtime.runtime_identity is None
            else _canonical_json_copy(dict(runtime.runtime_identity))
        ),
        "authority": {
            "classical": runtime.classical,
            "capabilities": _capability_record(runtime.capabilities),
        },
        "budget": budget.to_dict(),
        "generation": _canonical_json_copy(
            getattr(policy, "generation_provenance", None)
        ),
        "search": _search_record(result),
        "kernel_verification": replay_record,
        "publication": publication,
    }
    return CheckedAttempt(report, proof_script)


def _inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _validated_results_dir(path: Path) -> Path:
    lexical = Path(os.path.abspath(os.fspath(path)))
    lexical_root = Path(os.path.abspath(os.fspath(RESULTS_ROOT)))
    if not _inside(lexical, lexical_root):
        raise ValueError(f"result directory must live below {lexical_root}")
    resolved_root = lexical_root.resolve(strict=False)
    resolved = lexical.resolve(strict=False)
    if not _inside(resolved, resolved_root):
        raise ValueError("result directory escapes results/ through a symlink")
    return lexical


def _ensure_plain_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    repository = REPOSITORY_ROOT.resolve()
    current = path
    while True:
        if current.is_symlink() or not current.is_dir():
            raise ValueError(f"result directory is not plain: {current}")
        if current.resolve() == repository:
            break
        if current.parent == current:
            raise ValueError("result directory is outside the repository")
        current = current.parent


def _atomic_create_text(path: Path, text: str) -> None:
    """Publish complete UTF-8 text without replacing any directory entry."""

    if os.path.lexists(path):
        raise FileExistsError(f"refusing to replace result artifact: {path}")
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError:
            raise FileExistsError(
                f"refusing to replace result artifact: {path}"
            ) from None
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if temporary.exists():
            temporary.unlink()


def _result_stem(attempt: CheckedAttempt) -> str:
    request = attempt.report.get("request")
    theorem = request.get("canonical_theorem") if type(request) is dict else ""
    theorem_hash = hashlib.sha256(str(theorem).encode("utf-8")).hexdigest()[:12]
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{timestamp}-{theorem_hash}-{secrets.token_hex(4)}"


def save_attempt(
    attempt: CheckedAttempt,
    results_dir: Path,
    *,
    stem: str | None = None,
) -> SavedArtifacts:
    """Save a report and optional checked proof, never replacing prior work."""

    directory = _validated_results_dir(results_dir)
    _ensure_plain_directory(directory)
    artifact_stem = stem or _result_stem(attempt)
    if type(artifact_stem) is not str or _STEM_RE.fullmatch(artifact_stem) is None:
        raise ValueError("result stem must be one safe filename token")
    report_path = directory / f"{artifact_stem}.json"
    proof_path = (
        directory / f"{artifact_stem}.pa" if attempt.proof_script is not None else None
    )
    for path in (report_path, proof_path):
        if path is not None and os.path.lexists(path):
            raise FileExistsError(f"refusing to replace result artifact: {path}")

    record = _canonical_json_copy(attempt.report)
    if type(record) is not dict:  # pragma: no cover - CheckedAttempt invariant
        raise TypeError("attempt report must be a JSON object")
    record["artifacts"] = {
        "report": report_path.name,
        "proof": None if proof_path is None else proof_path.name,
    }
    report_text = json.dumps(
        record,
        ensure_ascii=False,
        allow_nan=False,
        indent=2,
        sort_keys=True,
    ) + "\n"

    if proof_path is not None:
        _atomic_create_text(proof_path, attempt.proof_script or "")
    # Never delete an entry during publication.  A process crash or an
    # adversarial race can at worst leave the uniquely named proof as an
    # orphan; it cannot replace an old artifact or make the REPL announce an
    # unsaved success.
    _atomic_create_text(report_path, report_text)
    return SavedArtifacts(report_path, proof_path)


def _diagnostic_summary(report: Mapping[str, object]) -> str:
    search_record = report.get("search")
    if type(search_record) is not dict:
        return "search statistics unavailable"
    return (
        f"status={search_record.get('status')}; "
        f"depth={search_record.get('depth_reached')}; "
        f"model calls={search_record.get('model_calls')}; "
        f"candidates={search_record.get('candidates_executed')}"
    )


def _help_text() -> str:
    return "\n".join(
        (
            "Enter one closed Peano-arithmetic formula, for example:",
            "  forall n. n + 0 = n",
            "You may also paste the first line as: pa prove FORMULA",
            "",
            ":help   show this help",
            ":quit   leave the session (aliases: :q, :exit)",
            "",
            "The model proposes tactics; Peano Lab executes every branch.",
            "Only an independently kernel-replayed proof is printed or saved.",
        )
    )


def run_repl(
    runtime: ReplRuntime,
    budget: SearchBudget,
    results_dir: Path,
    *,
    read: Callable[[str], str] = input,
    write: Callable[[str], object] = print,
    save: Callable[[CheckedAttempt, Path], SavedArtifacts] = save_attempt,
) -> int:
    """Run the formula loop with injectable terminal I/O for focused tests."""

    write("Peano Policy REPL — model loaded once; every success is kernel checked.")
    write("Enter :help for examples or :quit to leave.")
    while True:
        try:
            line = read("peano> ")
        except EOFError:
            write("")
            return 0
        except KeyboardInterrupt:
            write("\nSession closed.")
            return 130
        command = line.strip()
        if not command:
            continue
        if command in {":quit", ":q", ":exit"}:
            write("Session closed.")
            return 0
        if command == ":help":
            write(_help_text())
            continue
        if command.startswith(":"):
            write(f"Unknown command {command!r}; enter :help.")
            continue
        try:
            theorem = normalize_theorem_input(line)
            write("Searching bounded tactic branches …")
            attempt = run_checked_search(theorem, runtime, budget)
            artifacts = save(attempt, results_dir)
        except KeyboardInterrupt:
            write("Search interrupted; no proof was published.")
            continue
        except Exception as exc:
            message = " ".join(str(exc).split()) or type(exc).__name__
            write(f"ERROR — no proof was published: {message}")
            continue

        if attempt.proved:
            publication = attempt.report.get("publication")
            if (
                type(publication) is not dict
                or publication.get("status") != "kernel-checked-proof"
            ):
                raise RuntimeError("verified proof lost its publication marker")
            write("KERNEL CHECKED PROOF")
            write(attempt.proof_script or "")
            if artifacts.proof is None:  # pragma: no cover - saver invariant
                raise RuntimeError("verified proof was not saved")
            write(f"Proof:  {artifacts.proof}")
        else:
            write("NO KERNEL-CHECKED PROOF within the configured bounds.")
            write(_diagnostic_summary(attempt.report))
        write(f"Report: {artifacts.report}")


def _bounded_int(label: str, minimum: int, maximum: int) -> Callable[[str], int]:
    def parse(value: str) -> int:
        try:
            parsed = int(value)
        except ValueError:
            raise argparse.ArgumentTypeError(f"{label} must be an integer") from None
        if not minimum <= parsed <= maximum:
            raise argparse.ArgumentTypeError(
                f"{label} must lie between {minimum} and {maximum}"
            )
        return parsed

    return parse


def _positive_float(label: str, *, at_most_one: bool = False) -> Callable[[str], float]:
    def parse(value: str) -> float:
        try:
            parsed = float(value)
        except ValueError:
            raise argparse.ArgumentTypeError(f"{label} must be a number") from None
        if not math.isfinite(parsed) or parsed <= 0 or (at_most_one and parsed > 1):
            bound = " in (0, 1]" if at_most_one else " positive and finite"
            raise argparse.ArgumentTypeError(f"{label} must be{bound}")
        return parsed

    return parse


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adapter", type=Path, default=DEFAULT_ADAPTER)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument(
        "--diagnostic",
        action="store_true",
        help=(
            "explicitly admit an adapter whose signed manifest marks it as "
            "completed diagnostic, never production"
        ),
    )
    parser.add_argument(
        "--device",
        choices=("auto", "cpu", "mps", "cuda"),
        default="auto",
        help="inference device (auto prefers CUDA, then Apple MPS, then CPU)",
    )
    parser.add_argument(
        "--dtype",
        choices=("auto", "bfloat16", "float16", "float32"),
        default="auto",
        help="inference tensor type; auto is validated for the selected device",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="require the pinned base-model snapshot to exist in the local cache",
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=None,
        help="optional Hugging Face cache root for the pinned base snapshot",
    )
    parser.add_argument("--seed", type=int, default=20260729)
    parser.add_argument(
        "--max-new-tokens",
        type=_bounded_int("max-new-tokens", 1, MAX_NEW_TOKENS),
        default=96,
    )
    parser.add_argument(
        "--temperature",
        type=_positive_float("temperature"),
        default=0.8,
    )
    parser.add_argument(
        "--top-p",
        type=_positive_float("top-p", at_most_one=True),
        default=0.95,
    )
    parser.add_argument(
        "--sample",
        action="store_true",
        help="sample each candidate batch (default: deterministic beam decoding)",
    )
    parser.add_argument(
        "--depth", type=_bounded_int("depth", 1, 32), default=32
    )
    parser.add_argument(
        "--beam",
        type=_bounded_int("beam", 1, MAX_BEAM_WIDTH),
        default=4,
    )
    parser.add_argument(
        "--candidates",
        type=_bounded_int("candidates", 1, MAX_CANDIDATES),
        default=4,
    )
    parser.add_argument(
        "--model-calls",
        type=_bounded_int("model-calls", 1, MAX_MODEL_CALLS),
        default=128,
    )
    parser.add_argument(
        "--states",
        type=_bounded_int("states", 1, MAX_STATES),
        default=2_048,
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    budget = SearchBudget(
        max_depth=args.depth,
        beam_width=args.beam,
        candidates_per_state=args.candidates,
        max_model_calls=args.model_calls,
        max_states=args.states,
    )
    try:
        results_dir = _validated_results_dir(args.results_dir)
    except ValueError as exc:
        raise SystemExit(f"invalid --results-dir: {exc}") from None
    print(f"Loading attested Peano adapter once from {args.adapter} …", flush=True)
    try:
        runtime = load_model_runtime(
            args.adapter,
            seed=args.seed,
            max_new_tokens=args.max_new_tokens,
            sample=args.sample,
            temperature=args.temperature,
            top_p=args.top_p,
            diagnostic_mode=args.diagnostic,
            device=args.device,
            dtype=args.dtype,
            local_files_only=args.offline,
            cache_dir=args.cache_dir,
        )
    except Exception as exc:
        message = " ".join(str(exc).split()) or type(exc).__name__
        raise SystemExit(f"could not load the attested adapter: {message}") from None
    return run_repl(runtime, budget, results_dir)


if __name__ == "__main__":
    raise SystemExit(main())
