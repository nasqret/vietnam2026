#!/usr/bin/env python3
"""Seal Peano Hydra H0 with semantic, macro, and cross-language checks.

The production command requires explicit paths to the clean pinned Lean source
tree and its verifier, native Rust shadow, Node executable, and committed WASM
module.  Python remains the QED authority; Lean is the primary independently
implemented reference.  Rust and its WASM build are diagnostic implementations
of one shared Rust core.  Their pre-registered resource envelopes are reported
explicitly and are never confused with a logical disagreement.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable, Iterable, Sequence
from concurrent.futures import ThreadPoolExecutor
import json
import math
import os
from pathlib import Path
import select
import signal
import struct
import subprocess
import sys
import tempfile
from threading import Event
from time import monotonic_ns, perf_counter_ns


ROOT = Path(__file__).resolve().parents[1]
PEANO_PYTHON = ROOT / "peano-lab" / "py"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(PEANO_PYTHON) not in sys.path:
    sys.path.insert(0, str(PEANO_PYTHON))

from peano_lab.kernel.formulas import Eq  # noqa: E402
from peano_lab.kernel.proofs import EqRefl  # noqa: E402
from peano_lab.kernel.terms import Zero  # noqa: E402
from peano_lab.library import theorems as theorem_library  # noqa: E402
from training.peano_hydra.conformance import (  # noqa: E402
    ArtifactCase,
    CONFORMANCE_FORMAT,
    CONFORMANCE_VERSION,
    ConformanceError,
    FULL_LIBRARY_COUNT,
    FULL_POSITIVE_COUNT,
    GENERATED_COUNT,
    artifact_case_row,
    assert_full_positive_corpus,
    assert_public_constructor_coverage,
    canonical_json_bytes,
    digest_bytes,
    digest_json,
    expected_intuitionistic_constructor_names,
    generated_positive_cases,
    library_positive_cases,
    mutation_artifact_cases,
    positive_row,
    proof_constructor_names,
    semantic_profile_sha256,
    validate_boundary_mutations,
    validate_positive_with_python,
)
from training.peano_hydra.h0_macro_evidence import (  # noqa: E402
    build_h0_macro_evidence,
)
from training.peano_hydra.result_schema import (  # noqa: E402
    HydraResultSchemaError,
    build_checked_proved_evidence,
    build_unknown_evidence,
    result_schema_identity,
    validate_checked_proved_result,
    validate_result,
    validate_result_preimages,
)


REPORT_FORMAT = "peano-hydra-h0-validation"
REPORT_VERSION = 2
COLD_REPLAY_FORMAT = "peano-hydra-h0-cold-replay"
COLD_REPLAY_VERSION = 1
DEFAULT_TIMEOUT_SECONDS = 120.0
DEFAULT_CAMPAIGN_TIMEOUT_SECONDS = 14_400.0
LEAN_BATCH_SIZE = 128
MACRO_FOCUSED_TESTS = (
    "tests/test_peano_hydra_macros.py",
    "tests/test_peano_hydra_macro_runner.py",
)
EXPECTED_MACRO_FOCUSED_TEST_COUNT = 110

# This is the independently reviewed Cut-aware Lean reference, not a
# caller-selected executable.  The source root is content-bound as well as
# commit-bound because an ignored/stale build directory is not Git provenance.
REVIEWED_LEAN_SOURCE_COMMIT = "05b6acd6e5295dbcb45fd23e96c3c112351c2e5b"
REVIEWED_LEAN_SOURCE_MANIFEST_SHA256 = (
    "8c187b0078c836968287bb978632caa2bc114a533bc17fe89f7804a762454939"
)
REVIEWED_LEAN_TOOLCHAIN = "leanprover/lean4:v4.31.0\n"
REVIEWED_LEAN_TOOLCHAIN_SHA256 = (
    "efac0b94923b2d8b6840cd35be9177ad0fc5ab2332f4f4311c98712cee92fdee"
)
REVIEWED_LEAN_VERIFIER_RELATIVE_PATH = ".lake/build/bin/peano_lab_verify"
REVIEWED_LEAN_VERIFIER_BYTES = 98_805_536
REVIEWED_LEAN_VERIFIER_SHA256 = (
    "c3f6eae40e1d60f1ed2d89c1ea47bc761c5d5fcb5a1df1e2b4cc2b5ba2cbfb98"
)

RUST_MAX_BYTES = 512 * 1024 * 1024
RUST_MAX_NODES = 4_000_000
RUST_MAX_DEPTH = 256
RUST_MAX_CHECK_STEPS = 64_000_000
RUST_MAX_WIRE_NAT = 0xFFFF_FFFF
WASM_MAX_BYTES = 16 * 1024 * 1024
WASM_MAX_NODES = 1_000_000
WASM_MAX_DEPTH = 192
WASM_MAX_CHECK_STEPS = 64_000_000
WASM_MAX_WIRE_NAT = 0xFFFF_FFFF
WASM_MAX_PORTABLE_INDEX = 0xFFFF_FFFF - 256

REQUIRED_REGRESSION_TESTS = (
    "tests/test_kernel.py::test_kernel_import_hygiene",
    "tests/test_kernel.py::test_checker_stays_small_enough_to_read_in_one_sitting",
    "tests/test_soundness.py::test_original_target_is_not_rewritten_by_tactic_substitution",
    "tests/test_soundness.py::test_forged_closed_state_is_checked_against_original_goal",
    "tests/test_engine_state.py::test_history_is_transactional_and_undo_restores_exact_snapshot",
    "tests/test_tactics.py::test_failed_tactics_are_transactional",
    "tests/test_tactics.py::test_undo_restores_the_exact_pre_tactic_state",
    "tests/test_batch.py::test_traced_batch_qed_is_independently_checked_against_original_goal",
    "tests/test_batch.py::test_failure_is_transactional_traced_and_never_claims_qed",
)

SOURCE_PATHS = (
    Path("peano-lab/py/tests/test_peano_hydra_conformance.py"),
    Path("peano-lab/py/tests/test_peano_hydra_macro_runner.py"),
    Path("peano-lab/py/tests/test_peano_hydra_macros.py"),
    Path("training/peano_hydra/__init__.py"),
    Path("training/peano_hydra/conformance.py"),
    Path("training/peano_hydra/h0_macro_evidence.py"),
    Path("training/peano_hydra/macros.py"),
    Path("training/peano_hydra/macro_runner.py"),
    Path("training/peano_hydra/macro-protocol-v1.json"),
    Path("training/peano_hydra/policy.py"),
    Path("training/peano_hydra/profile.py"),
    Path("training/peano_hydra/profile_theorem_v1.py"),
    Path("training/peano_hydra/semantic-profile-v1.json"),
    Path("training/peano_hydra/semantic-profile-v2.json"),
    Path("training/peano_hydra/result_schema.py"),
    Path("training/peano_hydra/result-schema-v1.json"),
    Path("training/peano_policy/__init__.py"),
    Path("training/peano_policy/library_identity.py"),
    Path("training/peano_policy/prompt.py"),
    Path("training/peano_policy/search.py"),
    Path("peano-lab/peano_kernel_shadow.wasm"),
    Path("scripts/validate_peano_hydra_h0.py"),
    Path("scripts/wasm_shadow_batch_runner.js"),
)


class H0ValidationError(RuntimeError):
    """The H0 campaign failed closed."""


def _load_strict_json(path: Path) -> object:
    def strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate key {key!r}")
            result[key] = value
        return result

    def reject_constant(value: str) -> object:
        raise ValueError(f"non-finite number {value!r}")

    try:
        return json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=strict_object,
            parse_constant=reject_constant,
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        raise H0ValidationError(f"cannot load cold replay result: {error}") from error


def _atomic_write_json(path: Path, value: object) -> None:
    body = json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        indent=2,
        sort_keys=True,
    ) + "\n"
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(path.name + ".tmp")
        with temporary.open("w", encoding="utf-8", newline="") as stream:
            stream.write(body)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    except OSError as error:
        raise H0ValidationError(f"cannot publish H0 report atomically: {error}") from error


def _require_executable(path: Path, label: str) -> Path:
    resolved = path.expanduser().resolve()
    if not resolved.is_file() or not os.access(resolved, os.X_OK):
        raise H0ValidationError(f"{label} must be an executable regular file")
    return resolved


def _require_file(path: Path, label: str) -> Path:
    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        raise H0ValidationError(f"{label} must be a regular file")
    return resolved


def _binary_identity(path: Path, role: str) -> dict[str, object]:
    data = path.read_bytes()
    return {
        "bytes": len(data),
        "role": role,
        "sha256": digest_bytes(data),
    }


def _deadline_ns(seconds: float, label: str) -> int:
    if (
        type(seconds) not in (int, float)
        or not math.isfinite(seconds)
        or not seconds > 0
    ):
        raise H0ValidationError(f"{label} must be positive")
    return monotonic_ns() + int(float(seconds) * 1_000_000_000)


def _remaining_seconds(deadline_ns: int, label: str) -> float:
    remaining_ns = deadline_ns - monotonic_ns()
    if remaining_ns <= 0:
        raise H0ValidationError(f"{label} exceeded the total campaign deadline")
    return remaining_ns / 1_000_000_000


def _inspect_lean_source_identity(
    source_root: Path, verifier: Path
) -> dict[str, object]:
    """Inspect one clean source tree without declaring it reviewed."""

    root = source_root.expanduser().resolve()
    if not root.is_dir() or not (root / ".git").exists():
        raise H0ValidationError("Lean source root must be a Git working tree")
    try:
        verifier_relative = verifier.relative_to(root)
    except ValueError:
        raise H0ValidationError(
            "Lean verifier must be built inside the explicit Lean source root"
        ) from None

    def git(*arguments: str) -> str:
        result = subprocess.run(
            ["git", *arguments],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0 or result.stderr:
            raise H0ValidationError("cannot establish Lean source Git identity")
        return result.stdout.strip()

    commit = git("rev-parse", "HEAD")
    if len(commit) != 40 or any(
        character not in "0123456789abcdef" for character in commit
    ):
        raise H0ValidationError("Lean source commit is not one exact Git SHA-1")
    if git("status", "--porcelain=v1", "--untracked-files=all"):
        raise H0ValidationError("Lean reference source tree must be clean")

    essential = (
        Path("PeanoLab.lean"),
        *(
            Path("PeanoLab") / name
            for name in (
                "Syntax.lean",
                "Substitution.lean",
                "Semantics.lean",
                "Derivation.lean",
                "Checker.lean",
                "Soundness.lean",
                "Codec.lean",
                "Verify.lean",
            )
        ),
    )
    fixed = (Path("lean-toolchain"), Path("lakefile.toml"), Path("lake-manifest.json"))
    for relative in (*essential, *fixed):
        if not (root / relative).is_file():
            raise H0ValidationError(
                f"Lean reference source is missing {relative.as_posix()}"
            )
    paths = sorted(
        {
            *fixed,
            Path("PeanoLab.lean"),
            *(
                path.relative_to(root)
                for path in (root / "PeanoLab").rglob("*.lean")
            ),
        },
        key=lambda item: item.as_posix(),
    )
    rows: list[dict[str, object]] = []
    for relative in paths:
        path = root / relative
        if path.is_symlink() or not path.is_file():
            raise H0ValidationError("Lean reference manifest contains an unsafe file")
        data = path.read_bytes()
        rows.append(
            {
                "bytes": len(data),
                "path": relative.as_posix(),
                "sha256": digest_bytes(data),
            }
        )
    toolchain_bytes = (root / "lean-toolchain").read_bytes()
    try:
        toolchain_text = toolchain_bytes.decode("utf-8")
    except UnicodeDecodeError as error:
        raise H0ValidationError("Lean toolchain pin is not UTF-8") from error
    return {
        "clean": True,
        "commit": commit,
        "manifest": {
            "files": rows,
            "root_contract": "sha256 of canonical JSON files array",
            "root_sha256": digest_json(rows),
        },
        "toolchain": {
            "bytes": len(toolchain_bytes),
            "content_utf8": toolchain_text,
            "sha256": digest_bytes(toolchain_bytes),
        },
        "verifier_relative_path": verifier_relative.as_posix(),
    }


def _reviewed_lean_registration() -> dict[str, object]:
    return {
        "commit": REVIEWED_LEAN_SOURCE_COMMIT,
        "manifest_root_sha256": REVIEWED_LEAN_SOURCE_MANIFEST_SHA256,
        "status": "exact-pre-registered-independent-reference",
        "toolchain_content_utf8": REVIEWED_LEAN_TOOLCHAIN,
        "toolchain_sha256": REVIEWED_LEAN_TOOLCHAIN_SHA256,
        "verifier_bytes": REVIEWED_LEAN_VERIFIER_BYTES,
        "verifier_relative_path": REVIEWED_LEAN_VERIFIER_RELATIVE_PATH,
        "verifier_sha256": REVIEWED_LEAN_VERIFIER_SHA256,
    }


def _lean_source_identity(source_root: Path, verifier: Path) -> dict[str, object]:
    """Require the exact independently reviewed Lean source and executable."""

    identity = _inspect_lean_source_identity(source_root, verifier)
    binary = _binary_identity(verifier, "verified-lean-reference")
    expected = {
        "commit": REVIEWED_LEAN_SOURCE_COMMIT,
        "manifest_root": REVIEWED_LEAN_SOURCE_MANIFEST_SHA256,
        "toolchain": REVIEWED_LEAN_TOOLCHAIN,
        "toolchain_sha256": REVIEWED_LEAN_TOOLCHAIN_SHA256,
        "verifier_relative_path": REVIEWED_LEAN_VERIFIER_RELATIVE_PATH,
        "verifier_bytes": REVIEWED_LEAN_VERIFIER_BYTES,
        "verifier_sha256": REVIEWED_LEAN_VERIFIER_SHA256,
    }
    observed = {
        "commit": identity["commit"],
        "manifest_root": identity["manifest"]["root_sha256"],
        "toolchain": identity["toolchain"]["content_utf8"],
        "toolchain_sha256": identity["toolchain"]["sha256"],
        "verifier_relative_path": identity["verifier_relative_path"],
        "verifier_bytes": binary["bytes"],
        "verifier_sha256": binary["sha256"],
    }
    if observed != expected:
        raise H0ValidationError(
            "Lean reference does not match the exact independently reviewed identity"
        )
    return identity


def _source_manifest() -> dict[str, object]:
    fixed = list(SOURCE_PATHS)
    fixed.extend(
        path.relative_to(ROOT)
        for path in sorted((ROOT / "peano-lab/py/peano_lab").rglob("*.py"))
    )
    for crate in ("peano-kernel-shadow", "peano-kernel-shadow-wasm"):
        crate_root = ROOT / "peano-lab/rust" / crate
        fixed.extend(
            path.relative_to(ROOT)
            for source_root in (crate_root / "src", crate_root / "tests")
            if source_root.is_dir()
            for path in sorted(source_root.rglob("*.rs"))
        )
        fixed.extend(
            path.relative_to(ROOT)
            for name in (
                "Cargo.toml",
                "Cargo.lock",
                "rust-toolchain.toml",
                "build.rs",
            )
            if (path := crate_root / name).is_file()
        )
    unique = sorted(set(fixed), key=lambda item: item.as_posix())
    rows: list[dict[str, object]] = []
    for relative in unique:
        path = ROOT / relative
        if path.is_symlink() or not path.is_file():
            raise H0ValidationError(
                f"required H0 source is absent or unsafe: {relative.as_posix()}"
            )
        data = path.read_bytes()
        rows.append(
            {
                "bytes": len(data),
                "path": relative.as_posix(),
                "sha256": digest_bytes(data),
            }
        )
    return {
        "files": rows,
        "root_contract": "sha256 of canonical JSON files array",
        "root_sha256": digest_json(rows),
    }


def _git_identity(*, require_clean: bool) -> dict[str, object]:
    def git(*arguments: str) -> str:
        result = subprocess.run(
            ["git", *arguments],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0 or result.stderr:
            raise H0ValidationError("cannot establish repository identity")
        return result.stdout.strip()

    commit = git("rev-parse", "HEAD")
    status = git("status", "--porcelain=v1", "--untracked-files=all")
    clean = status == ""
    if require_clean and not clean:
        raise H0ValidationError(
            "a retained H0 report requires a clean committed repository"
        )
    return {"clean": clean, "commit": commit}


def _require_unchanged_repository(
    initial_repository: dict[str, object],
    initial_sources: dict[str, object],
    final_repository: dict[str, object],
    final_sources: dict[str, object],
) -> None:
    if final_repository != initial_repository or final_sources != initial_sources:
        raise H0ValidationError(
            "repository identity or H0 implementation sources changed during validation"
        )


def _campaign_eligibility(
    *, require_clean: bool, run_regressions: bool
) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if not require_clean:
        reasons.append("dirty-worktree-development-mode")
    if not run_regressions:
        reasons.append("required-regressions-skipped")
    return not reasons, reasons


def _envelope_reason(
    case: ArtifactCase,
    *,
    max_bytes: int,
    max_nodes: int,
    max_depth: int,
    max_wire_nat: int | None = None,
    max_portable_index: int | None = None,
) -> str | None:
    if len(case.artifact) > max_bytes:
        return f"artifact_bytes>{max_bytes}"
    if case.decoder_nodes is not None and case.decoder_nodes > max_nodes:
        return f"decoder_nodes>{max_nodes}"
    if case.decoder_depth is not None and case.decoder_depth > max_depth:
        return f"decoder_depth>{max_depth}"
    if (
        max_wire_nat is not None
        and case.wire_nat_max is not None
        and case.wire_nat_max > max_wire_nat
    ):
        return f"wire_nat>{max_wire_nat}"
    if (
        max_portable_index is not None
        and case.portable_index_max is not None
        and case.portable_index_max > max_portable_index
    ):
        return f"portable_index>{max_portable_index}"
    return None


class ExternalVerifierSuite:
    """Drive Lean, native Rust, and the committed WASM process boundary."""

    def __init__(
        self,
        *,
        lean_verifier: Path,
        rust_cli: Path,
        node: Path,
        wasm: Path,
        timeout_seconds: float,
        lean_source_root: Path | None = None,
        campaign_deadline_ns: int | None = None,
    ) -> None:
        self.lean_verifier = _require_executable(lean_verifier, "Lean verifier")
        self.rust_cli = _require_executable(rust_cli, "Rust shadow")
        self.node = _require_executable(node, "Node executable")
        self.wasm = _require_file(wasm, "WASM module")
        if (
            type(timeout_seconds) not in (int, float)
            or not math.isfinite(timeout_seconds)
            or not timeout_seconds > 0
        ):
            raise H0ValidationError("timeout must be positive")
        self.timeout_seconds = float(timeout_seconds)
        self.campaign_deadline_ns = campaign_deadline_ns
        runner = _require_file(
            ROOT / "scripts/wasm_shadow_batch_runner.js", "WASM batch runner"
        )
        self.runner = runner
        self._lean_source_root = (
            None if lean_source_root is None else lean_source_root.expanduser().resolve()
        )
        self.lean_source_identity = (
            None
            if self._lean_source_root is None
            else _lean_source_identity(self._lean_source_root, self.lean_verifier)
        )
        self._temp = tempfile.TemporaryDirectory(prefix="peano-h0-artifacts-")
        self._pending: list[tuple[ArtifactCase, Path, dict[str, object]]] = []
        self._lean_duration_ns = 0
        self._rust_wasm_duration_ns = 0
        try:
            self._wasm_process = subprocess.Popen(
                [str(self.node), str(self.runner), str(self.wasm)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except OSError as error:
            self._temp.cleanup()
            raise H0ValidationError(f"cannot start WASM diagnostic: {error}") from error

    def _operation_timeout(self, label: str) -> float:
        if self.campaign_deadline_ns is None:
            return self.timeout_seconds
        return min(
            self.timeout_seconds,
            _remaining_seconds(self.campaign_deadline_ns, label),
        )

    @property
    def identity(self) -> dict[str, object]:
        result: dict[str, object] = {
            "lean": _binary_identity(self.lean_verifier, "verified-lean-reference"),
            "node": _binary_identity(self.node, "wasm-runtime"),
            "rust": _binary_identity(self.rust_cli, "native-rust-shadow"),
            "wasm": _binary_identity(self.wasm, "rust-shadow-wasm"),
            "wasm_runner": _binary_identity(self.runner, "committed-wasm-runner"),
        }
        if self.lean_source_identity is not None:
            if self._lean_source_root is None:  # pragma: no cover
                raise H0ValidationError("Lean source identity lost its source root")
            current_source_identity = _lean_source_identity(
                self._lean_source_root, self.lean_verifier
            )
            if current_source_identity != self.lean_source_identity:
                raise H0ValidationError(
                    "Lean reference source identity changed during verification"
                )
            result["lean_source"] = self.lean_source_identity
            result["lean_reviewed_registration"] = _reviewed_lean_registration()
        return result

    @staticmethod
    def _expected_semantic(case: ArtifactCase) -> str:
        if case.expected == "accept":
            return "accept"
        if case.expected == "certificate_rejected":
            return "certificate_rejected"
        return "input_rejected"

    @property
    def timing(self) -> dict[str, object]:
        return {
            "clock": "time.perf_counter_ns",
            "lean_batch_duration_ns": self._lean_duration_ns,
            "native_rust_and_wasm_submission_duration_ns": (
                self._rust_wasm_duration_ns
            ),
        }

    def _run_rust(self, case: ArtifactCase) -> dict[str, object]:
        reason = _envelope_reason(
            case,
            max_bytes=RUST_MAX_BYTES,
            max_nodes=RUST_MAX_NODES,
            max_depth=RUST_MAX_DEPTH,
            max_wire_nat=RUST_MAX_WIRE_NAT,
        )
        try:
            result = subprocess.run(
                [str(self.rust_cli)],
                input=case.artifact,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=self._operation_timeout("native Rust verification"),
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as error:
            raise H0ValidationError(
                f"native Rust failed during {case.case_id!r}: {error}"
            ) from error
        if result.returncode == 0 and result.stdout == b"ACCEPT\n" and not result.stderr:
            observed = "accept"
        elif result.returncode == 1 and result.stdout == b"REJECT\n" and not result.stderr:
            observed = "certificate_rejected"
        elif (
            result.returncode == 2
            and not result.stdout
            and result.stderr.startswith(b"ERROR: ")
            and result.stderr.endswith(b"\n")
            and result.stderr.count(b"\n") == 1
        ):
            observed = "input_rejected"
        else:
            raise H0ValidationError(
                f"native Rust protocol mismatch during {case.case_id!r}"
            )
        if reason is None:
            if observed != self._expected_semantic(case):
                raise H0ValidationError(
                    f"native Rust disagreed on portable case {case.case_id!r}"
                )
            return {"disposition": observed, "portable": True}
        if observed != "input_rejected":
            raise H0ValidationError(
                f"native Rust did not enforce its envelope for {case.case_id!r}"
            )
        return {
            "disposition": "out_of_envelope",
            "observed": observed,
            "portable": False,
            "reason": reason,
        }

    def _run_wasm(self, case: ArtifactCase) -> dict[str, object]:
        stdin = self._wasm_process.stdin
        stdout = self._wasm_process.stdout
        if stdin is None or stdout is None:
            raise H0ValidationError("WASM process pipes are unavailable")
        if len(case.artifact) > 0xFFFF_FFFF:
            raise H0ValidationError("artifact exceeds the WASM frame length domain")
        try:
            stdin.write(struct.pack(">BI", 0, len(case.artifact)))
            stdin.write(case.artifact)
            stdin.flush()
            operation_deadline = _deadline_ns(
                self._operation_timeout("WASM verification"),
                "WASM per-case deadline",
            )
            response_bytes = bytearray()
            while not response_bytes.endswith(b"\n"):
                remaining = _remaining_seconds(
                    operation_deadline, "WASM verification"
                )
                readable, _, _ = select.select([stdout], [], [], remaining)
                if not readable:
                    raise H0ValidationError(
                        f"WASM diagnostic timed out during {case.case_id!r}"
                    )
                chunk = os.read(stdout.fileno(), 1)
                if not chunk:
                    raise H0ValidationError(
                        f"WASM diagnostic closed during {case.case_id!r}"
                    )
                response_bytes.extend(chunk)
                if len(response_bytes) > 2:
                    raise H0ValidationError(
                        f"WASM protocol mismatch during {case.case_id!r}"
                    )
            response = bytes(response_bytes)
        except (BrokenPipeError, OSError) as error:
            raise H0ValidationError(
                f"WASM diagnostic failed during {case.case_id!r}: {error}"
            ) from error
        verdicts = {
            b"1\n": "accept",
            b"2\n": "certificate_rejected",
            b"3\n": "input_rejected",
        }
        observed = verdicts.get(response)
        if observed is None:
            raise H0ValidationError(
                f"WASM protocol mismatch during {case.case_id!r}"
            )
        reason = _envelope_reason(
            case,
            max_bytes=WASM_MAX_BYTES,
            max_nodes=WASM_MAX_NODES,
            max_depth=WASM_MAX_DEPTH,
            max_wire_nat=WASM_MAX_WIRE_NAT,
            max_portable_index=WASM_MAX_PORTABLE_INDEX,
        )
        if reason is None:
            if observed != self._expected_semantic(case):
                raise H0ValidationError(
                    f"WASM disagreed on portable case {case.case_id!r}"
                )
            return {"disposition": observed, "portable": True}
        if observed != "input_rejected":
            raise H0ValidationError(
                f"WASM did not enforce its envelope for {case.case_id!r}"
            )
        return {
            "disposition": "out_of_envelope",
            "observed": observed,
            "portable": False,
            "reason": reason,
        }

    def submit(self, case: ArtifactCase) -> None:
        index = len(self._pending)
        path = Path(self._temp.name) / f"case-{index:06d}.json"
        path.write_bytes(case.artifact)
        result = artifact_case_row(case)
        started = perf_counter_ns()
        result["rust"] = self._run_rust(case)
        result["wasm"] = self._run_wasm(case)
        self._rust_wasm_duration_ns += perf_counter_ns() - started
        self._pending.append((case, path, result))

    def _run_lean_batch(
        self, pending: Sequence[tuple[ArtifactCase, Path, dict[str, object]]]
    ) -> None:
        paths = [path for _, path, _ in pending]
        started = perf_counter_ns()
        try:
            result = subprocess.run(
                [str(self.lean_verifier), *(str(path) for path in paths)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=self._operation_timeout("Lean batch verification"),
                check=False,
                text=True,
            )
        except (OSError, subprocess.SubprocessError) as error:
            raise H0ValidationError(f"Lean verifier process failed: {error}") from error
        self._lean_duration_ns += perf_counter_ns() - started

        path_map = {str(path): (case, row) for case, path, row in pending}
        observed: dict[str, str] = {}
        for line in result.stdout.splitlines():
            parts = line.split("\t", 2)
            if len(parts) != 3 or parts[0] not in {"ACCEPT", "REJECT"}:
                raise H0ValidationError("Lean verifier emitted malformed stdout")
            disposition = (
                "accept" if parts[0] == "ACCEPT" else "certificate_rejected"
            )
            if parts[1] not in path_map or parts[1] in observed:
                raise H0ValidationError("Lean verifier emitted an unknown/duplicate path")
            observed[parts[1]] = disposition
        for line in result.stderr.splitlines():
            parts = line.split("\t", 2)
            if len(parts) != 3 or parts[0] != "DECODE_ERROR":
                raise H0ValidationError("Lean verifier emitted malformed stderr")
            if parts[1] not in path_map or parts[1] in observed:
                raise H0ValidationError("Lean verifier emitted an unknown/duplicate path")
            observed[parts[1]] = "input_rejected"
        if set(observed) != set(path_map):
            raise H0ValidationError("Lean verifier omitted one or more artifact results")
        expected_code = max(
            0
            if self._expected_semantic(case) == "accept"
            else 1
            if self._expected_semantic(case) == "certificate_rejected"
            else 2
            for case, _, _ in pending
        )
        if result.returncode != expected_code:
            raise H0ValidationError("Lean verifier exit status violated its protocol")
        for path, (case, row) in path_map.items():
            disposition = observed[path]
            if disposition != self._expected_semantic(case):
                raise H0ValidationError(
                    f"Lean reference disagreed on {case.case_id!r}"
                )
            row["lean"] = {"disposition": disposition, "portable": True}

    def finish(self) -> tuple[dict[str, object], ...]:
        try:
            for offset in range(0, len(self._pending), LEAN_BATCH_SIZE):
                self._run_lean_batch(self._pending[offset : offset + LEAN_BATCH_SIZE])
            if self._wasm_process.stdin is not None:
                self._wasm_process.stdin.close()
            try:
                return_code = self._wasm_process.wait(
                    timeout=self._operation_timeout("WASM shutdown")
                )
            except subprocess.TimeoutExpired as error:
                self._wasm_process.kill()
                raise H0ValidationError("WASM diagnostic did not terminate") from error
            stderr = (
                b""
                if self._wasm_process.stderr is None
                else self._wasm_process.stderr.read()
            )
            if return_code != 0 or stderr:
                raise H0ValidationError("WASM diagnostic terminated abnormally")
            return tuple(row for _, _, row in self._pending)
        finally:
            self._temp.cleanup()

    def abort(self) -> None:
        if self._wasm_process.poll() is None:
            self._wasm_process.kill()
            try:
                self._wasm_process.wait(timeout=1.0)
            except subprocess.TimeoutExpired:
                pass
        self._temp.cleanup()


def cold_library_replay(
    names: Sequence[str],
    *,
    external: ExternalVerifierSuite | None = None,
    require_complete_library: bool,
) -> dict[str, object]:
    """Replay one library selection from initially empty in-process caches."""

    replay_cache = theorem_library.replay.cache_info()
    specs_cache = theorem_library._specs_by_name.cache_info()
    if replay_cache.currsize or specs_cache.currsize:
        raise H0ValidationError("cold replay worker did not start with empty caches")

    rows: list[dict[str, object]] = []
    observed_constructors: set[str] = set()
    external_results: tuple[dict[str, object], ...] = ()
    try:
        for case in library_positive_cases(names):
            validated = validate_positive_with_python(case)
            rows.append(positive_row(case, validated))
            observed_constructors.update(proof_constructor_names(case.proof))
            if external is not None:
                external.submit(validated[0])
                external.submit(validated[1])
        if external is not None:
            external_results = external.finish()
    except Exception:
        if external is not None:
            external.abort()
        raise

    formula_hashes = [str(row["formula_sha256"]) for row in rows]
    if len(set(formula_hashes)) != len(formula_hashes):
        raise H0ValidationError("cold replay contains duplicate public formulas")
    expected_constructors = expected_intuitionistic_constructor_names()
    if require_complete_library:
        if len(rows) != FULL_LIBRARY_COUNT:
            raise H0ValidationError(
                f"complete cold replay expected {FULL_LIBRARY_COUNT} theorems"
            )
        assert_public_constructor_coverage(observed_constructors)
    cold_payload = {
        "constructor_coverage": {
            "expected": list(expected_constructors),
            "observed": sorted(observed_constructors),
            "required_complete": require_complete_library,
        },
        "format": COLD_REPLAY_FORMAT,
        "library_count": len(rows),
        "profile_sha256": semantic_profile_sha256(),
        "rows": rows,
        "v": COLD_REPLAY_VERSION,
    }
    return {
        "cold": {
            **cold_payload,
            "root_contract": "sha256 of canonical JSON over this object without root fields",
            "root_sha256": digest_json(cold_payload),
        },
        "external_identity": None if external is None else external.identity,
        "external_results": list(external_results),
        "external_timing": None if external is None else external.timing,
    }


def _worker_names(requested: Sequence[str] | None) -> tuple[str, ...]:
    if not requested:
        return theorem_library.names()
    names = tuple(requested)
    for name in names:
        spec = theorem_library.get(name)
        if spec is None or spec.name != name:
            raise H0ValidationError(f"worker theorem name is not canonical: {name!r}")
    if len(set(names)) != len(names):
        raise H0ValidationError("worker theorem selection contains duplicates")
    return names


def _spawn_cold_worker(
    *,
    output: Path,
    names: Sequence[str],
    external_paths: dict[str, Path] | None,
    timeout_seconds: float,
    campaign_timeout_seconds: float,
    cancel_event: Event | None = None,
) -> dict[str, object]:
    command = [
        sys.executable,
        "-B",
        str(Path(__file__).resolve()),
        "--cold-worker",
        "--output",
        str(output),
        "--timeout-seconds",
        str(timeout_seconds),
    ]
    complete = tuple(names) == theorem_library.names()
    if complete:
        command.append("--require-complete-library")
    else:
        for name in names:
            command.extend(("--theorem", name))
    if external_paths is not None:
        command.extend(
            (
                "--lean-verifier",
                str(external_paths["lean_verifier"]),
                "--lean-source-root",
                str(external_paths["lean_source_root"]),
                "--rust-cli",
                str(external_paths["rust_cli"]),
                "--node",
                str(external_paths["node"]),
                "--wasm",
                str(external_paths["wasm"]),
            )
        )
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONHASHSEED"] = "0"
    try:
        process = subprocess.Popen(
            command,
            cwd=ROOT,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
    except OSError as error:
        raise H0ValidationError(f"cold replay worker failed: {error}") from error

    deadline = _deadline_ns(campaign_timeout_seconds, "cold replay worker timeout")

    def stop_worker() -> None:
        if process.poll() is not None:
            return
        try:
            os.killpg(process.pid, signal.SIGTERM)
            process.wait(timeout=1.0)
        except (OSError, subprocess.TimeoutExpired):
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except OSError:
                pass
            try:
                process.wait(timeout=1.0)
            except subprocess.TimeoutExpired:
                pass

    try:
        while True:
            if cancel_event is not None and cancel_event.is_set():
                stop_worker()
                raise H0ValidationError("cold replay peer failed; worker cancelled")
            remaining = _remaining_seconds(deadline, "cold replay worker")
            try:
                stdout, stderr = process.communicate(timeout=min(0.25, remaining))
                break
            except subprocess.TimeoutExpired:
                continue
    except Exception:
        stop_worker()
        raise
    if process.returncode != 0 or stdout or stderr or not output.is_file():
        raise H0ValidationError(
            "cold replay worker did not publish one clean successful report"
        )
    loaded = _load_strict_json(output)
    if type(loaded) is not dict:
        raise H0ValidationError("cold replay worker result is not an object")
    return loaded


def run_cold_replay_pair(
    *,
    temp: Path,
    names: Sequence[str],
    external_paths: dict[str, Path],
    timeout_seconds: float,
    campaign_timeout_seconds: float,
    worker: Callable[..., dict[str, object]] | None = None,
) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    """Launch both isolated replay workers concurrently and fail closed."""

    run_worker = _spawn_cold_worker if worker is None else worker
    cancel_event = Event()

    def measured(
        *, output: Path, with_external: bool
    ) -> tuple[dict[str, object], int]:
        started = perf_counter_ns()
        try:
            payload = run_worker(
                output=output,
                names=names,
                external_paths=external_paths if with_external else None,
                timeout_seconds=timeout_seconds,
                campaign_timeout_seconds=campaign_timeout_seconds,
                cancel_event=cancel_event,
            )
        except Exception:
            cancel_event.set()
            raise
        return payload, perf_counter_ns() - started

    wall_started = perf_counter_ns()
    with ThreadPoolExecutor(max_workers=2, thread_name_prefix="peano-h0-cold") as pool:
        first_future = pool.submit(
            measured, output=temp / "pass-1.json", with_external=False
        )
        second_future = pool.submit(
            measured, output=temp / "pass-2.json", with_external=True
        )
        first, first_duration = first_future.result()
        second, second_duration = second_future.result()
    timing = {
        "clock": "time.perf_counter_ns",
        "concurrent_wall_duration_ns": perf_counter_ns() - wall_started,
        "pass_1_python_duration_ns": first_duration,
        "pass_2_python_and_external_duration_ns": second_duration,
    }
    return first, second, timing


def compare_cold_replays(
    first: dict[str, object], second: dict[str, object]
) -> dict[str, object]:
    first_cold = first.get("cold")
    second_cold = second.get("cold")
    if type(first_cold) is not dict or type(second_cold) is not dict:
        raise H0ValidationError("cold worker omitted its deterministic payload")
    if first_cold != second_cold:
        raise H0ValidationError("the two fresh-process cold replay roots differ")
    return {
        "identical": True,
        "library_count": first_cold["library_count"],
        "pass_count": 2,
        "root_sha256": first_cold["root_sha256"],
        "worker_isolation": "two fresh CPython processes with empty replay caches",
    }


def _run_required_regressions(*, timeout_seconds: float) -> dict[str, object]:
    command = [sys.executable, "-B", "-m", "pytest", "-q", *REQUIRED_REGRESSION_TESTS]
    try:
        result = subprocess.run(
            command,
            cwd=PEANO_PYTHON,
            check=False,
            capture_output=True,
            timeout=timeout_seconds,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise H0ValidationError(f"required regression tests failed to run: {error}") from error
    if result.returncode != 0:
        raise H0ValidationError("required H0.2 regression tests failed")
    return {
        "command": ["python", "-B", "-m", "pytest", "-q", *REQUIRED_REGRESSION_TESTS],
        "exit_code": 0,
        "stderr_sha256": digest_bytes(result.stderr),
        "stdout_sha256": digest_bytes(result.stdout),
        "tests": list(REQUIRED_REGRESSION_TESTS),
    }


def _run_macro_focused_tests(*, timeout_seconds: float) -> dict[str, object]:
    command = [sys.executable, "-B", "-m", "pytest", "-q", *MACRO_FOCUSED_TESTS]
    environment = dict(os.environ)
    environment.update(
        PYTHONDONTWRITEBYTECODE="1",
        PYTHONHASHSEED="0",
        PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
    )
    try:
        result = subprocess.run(
            command,
            cwd=PEANO_PYTHON,
            env=environment,
            check=False,
            capture_output=True,
            timeout=timeout_seconds,
        )
        stdout, stderr = result.stdout.decode("utf-8"), result.stderr.decode("utf-8")
    except (OSError, UnicodeDecodeError, subprocess.SubprocessError) as error:
        raise H0ValidationError(
            f"focused H0.3 macro tests failed to run: {error}"
        ) from error
    lines = stdout.splitlines()
    prefix = f"{EXPECTED_MACRO_FOCUSED_TEST_COUNT} passed in "
    if (
        result.returncode != 0
        or stderr
        or not lines
        or not lines[-1].startswith(prefix)
        or not lines[-1].endswith("s")
    ):
        raise H0ValidationError(
            "focused H0.3 macro tests did not produce the exact green result"
        )
    try:
        duration = float(lines[-1][len(prefix) : -1])
    except ValueError as error:
        raise H0ValidationError("focused H0.3 pytest summary is malformed") from error
    if not math.isfinite(duration) or duration < 0:
        raise H0ValidationError("focused H0.3 pytest duration is malformed")

    def preimage(content: str) -> dict[str, object]:
        raw = content.encode("utf-8")
        return {
            "bytes": len(raw),
            "content_utf8": content,
            "encoding": "utf-8",
            "sha256": digest_bytes(raw),
        }

    return {
        "command": {
            "argv": ["python", "-B", "-m", "pytest", "-q", *MACRO_FOCUSED_TESTS],
            "cwd": "peano-lab/py",
            "environment": {
                "PYTHONDONTWRITEBYTECODE": "1",
                "PYTHONHASHSEED": "0",
                "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
            },
        },
        "result": {
            "exit_code": 0,
            "passed": EXPECTED_MACRO_FOCUSED_TEST_COUNT,
            "stderr": preimage(stderr),
            "stdout": preimage(stdout),
            "summary": lines[-1],
        },
    }


def _macro_protocol_controls(*, timeout_seconds: float) -> dict[str, object]:
    """Build exact H0.3 evidence; never return a partial passing record."""

    try:
        focused_pytest = _run_macro_focused_tests(timeout_seconds=timeout_seconds)
        controls = {
            **build_h0_macro_evidence(),
            "focused_pytest": focused_pytest,
        }
    except Exception as error:
        raise H0ValidationError(f"H0.3 macro evidence failed: {error}") from error
    canonical_json_bytes(controls)
    if str(ROOT) in json.dumps(controls, ensure_ascii=False):
        raise H0ValidationError("H0.3 evidence retained a local filesystem path")
    return controls


def _schema_controls() -> dict[str, object]:
    """Build checked, reconstructable schema fixtures, not benchmark rows."""

    formula = Eq(Zero(), Zero())
    proof = EqRefl(Zero())
    proved_evidence = build_checked_proved_evidence(
        formula,
        proof,
        run_id="peano-hydra-h0-schema-proved-control",
    )
    proved = proved_evidence.result
    certificate_artifact = proved_evidence.certificate_artifact
    kernel_identity = proved_evidence.kernel_identity
    replay_evidence = proved_evidence.replay_evidence
    proved_run_evidence = proved_evidence.run_evidence
    if (
        certificate_artifact is None
        or kernel_identity is None
        or replay_evidence is None
    ):
        raise H0ValidationError("checked proved control omitted a positive preimage")
    validate_checked_proved_result(
        proved,
        formula,
        proof,
        run_evidence=proved_run_evidence,
        kernel_identity=kernel_identity,
        replay_evidence=replay_evidence,
    )
    # Retain the exact artifact as UTF-8.  Re-encoding this string reconstructs
    # the hash preimage byte-for-byte, including the mandatory terminal LF.
    try:
        certificate_artifact_utf8 = certificate_artifact.decode("utf-8")
    except UnicodeDecodeError as error:  # pragma: no cover - codec contract drift
        raise H0ValidationError(
            "checked certificate artifact is unexpectedly not UTF-8"
        ) from error
    if certificate_artifact_utf8.encode("utf-8") != certificate_artifact:
        raise H0ValidationError("certificate artifact did not round-trip exactly")

    unknown_evidence = build_unknown_evidence(
        "0 = 0",
        reason="search-exhausted",
        run_id="peano-hydra-h0-schema-unknown-control",
    )
    unknown = unknown_evidence.result
    unknown_run_evidence = unknown_evidence.run_evidence
    validate_result_preimages(unknown, run_evidence=unknown_run_evidence)

    forbidden_kind = dict(unknown)
    forbidden_kind["kind"] = "not_theorem"
    forbidden_field = dict(unknown)
    forbidden_field["negative_evidence_sha256"] = "0" * 64
    rejected_attempts: list[dict[str, object]] = []
    for attempted in (forbidden_kind, forbidden_field):
        try:
            validate_result(attempted)
        except HydraResultSchemaError as error:
            rejected_attempts.append(
                {
                    "attempted_record": attempted,
                    "case_id": (
                        "mutation-negative-kind"
                        if attempted is forbidden_kind
                        else "mutation-negative-field"
                    ),
                    "disposition": "schema_rejected",
                    "rejection": str(error),
                }
            )
        else:  # pragma: no cover - false acceptance is campaign-stopping
            raise H0ValidationError("result schema accepted negative theoremhood evidence")
    return {
        "interpretation": "schema controls only; not benchmark outcomes",
        "proved": {
            "preimages": {
                "certificate_artifact": {
                    "bytes": len(certificate_artifact),
                    "content_utf8": certificate_artifact_utf8,
                    "encoding": "utf-8",
                },
                "kernel_identity": kernel_identity,
                "replay_evidence": replay_evidence,
                "run_evidence": proved_run_evidence,
            },
            "record": proved,
        },
        "rejected_negative_attempts": rejected_attempts,
        "result_schema": result_schema_identity(),
        "unknown": {
            "preimages": {"run_evidence": unknown_run_evidence},
            "record": unknown,
        },
    }


def _portable_counts(results: Iterable[dict[str, object]]) -> dict[str, object]:
    rows = tuple(results)
    return {
        backend: {
            "out_of_envelope": sum(
                type(row.get(backend)) is dict
                and row[backend].get("disposition") == "out_of_envelope"
                for row in rows
            ),
            "portable": sum(
                type(row.get(backend)) is dict
                and row[backend].get("portable") is True
                for row in rows
            ),
        }
        for backend in ("lean", "rust", "wasm")
    }


def validate_campaign(
    *,
    lean_verifier: Path,
    lean_source_root: Path,
    rust_cli: Path,
    node: Path,
    wasm: Path,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    campaign_timeout_seconds: float = DEFAULT_CAMPAIGN_TIMEOUT_SECONDS,
    require_clean: bool = True,
    run_regressions: bool = True,
) -> dict[str, object]:
    """Run and return the complete retained H0 evidence object."""

    campaign_deadline_ns = _deadline_ns(
        campaign_timeout_seconds, "total campaign deadline"
    )
    external_paths = {
        "lean_verifier": _require_executable(lean_verifier, "Lean verifier"),
        "lean_source_root": lean_source_root.expanduser().resolve(),
        "rust_cli": _require_executable(rust_cli, "Rust shadow"),
        "node": _require_executable(node, "Node executable"),
        "wasm": _require_file(wasm, "WASM module"),
    }
    repository = _git_identity(require_clean=require_clean)
    implementation_sources = _source_manifest()
    names = theorem_library.names()
    if len(names) != FULL_LIBRARY_COUNT:
        raise H0ValidationError(
            f"H0.2 is frozen for {FULL_LIBRARY_COUNT} public theorems, found {len(names)}"
        )

    with tempfile.TemporaryDirectory(prefix="peano-h0-cold-") as temp_name:
        temp = Path(temp_name)
        first, second, cold_timing = run_cold_replay_pair(
            temp=temp,
            names=names,
            external_paths=external_paths,
            timeout_seconds=timeout_seconds,
            campaign_timeout_seconds=_remaining_seconds(
                campaign_deadline_ns, "cold replay pair"
            ),
        )
    cold_summary = compare_cold_replays(first, second)
    cold_payload = first["cold"]
    if type(cold_payload) is not dict:
        raise H0ValidationError("first cold replay payload is malformed")
    library_rows = cold_payload["rows"]
    if type(library_rows) is not list:
        raise H0ValidationError("cold replay rows are malformed")

    forbidden_hashes = [str(row["formula_sha256"]) for row in library_rows]
    generated = generated_positive_cases(
        forbidden_formula_sha256=forbidden_hashes,
        count=GENERATED_COUNT,
    )
    all_formula_hashes = assert_full_positive_corpus(library_rows, generated)

    generated_rows: list[dict[str, object]] = []
    generated_started = perf_counter_ns()
    suite = ExternalVerifierSuite(
        lean_verifier=external_paths["lean_verifier"],
        lean_source_root=external_paths["lean_source_root"],
        rust_cli=external_paths["rust_cli"],
        node=external_paths["node"],
        wasm=external_paths["wasm"],
        timeout_seconds=timeout_seconds,
        campaign_deadline_ns=campaign_deadline_ns,
    )
    try:
        for case in generated:
            _remaining_seconds(campaign_deadline_ns, "generated conformance")
            validated = validate_positive_with_python(case)
            generated_rows.append(positive_row(case, validated))
            suite.submit(validated[0])
            suite.submit(validated[1])
        mutations = mutation_artifact_cases()
        for mutation in mutations:
            suite.submit(mutation)
        generated_external = suite.finish()
        generated_external_timing = suite.timing
    except Exception:
        suite.abort()
        raise

    if second.get("external_identity") != suite.identity:
        raise H0ValidationError("external verifier identity changed during the campaign")
    library_external = second.get("external_results")
    if type(library_external) is not list:
        raise H0ValidationError("second cold pass omitted external results")
    external_results = tuple(library_external) + generated_external
    generated_duration_ns = perf_counter_ns() - generated_started
    schema_controls = _schema_controls()
    macro_controls = _macro_protocol_controls(
        timeout_seconds=_remaining_seconds(
            campaign_deadline_ns, "focused H0.3 macro conformance"
        )
    )
    unknown_control = schema_controls["unknown"]
    if type(unknown_control) is not dict:
        raise H0ValidationError("unknown result-schema control is malformed")
    unknown_record = unknown_control["record"]
    if type(unknown_record) is not dict:
        raise H0ValidationError("unknown result-schema record is malformed")
    boundary_results = validate_boundary_mutations(
        result_validator=validate_result,
        valid_unknown_result=unknown_record,
    )

    positive_rows = tuple(library_rows) + tuple(generated_rows)
    if len(positive_rows) != FULL_POSITIVE_COUNT:
        raise H0ValidationError("H0.2 did not retain exactly 1,024 positive rows")
    paired_rows = [
        row
        for row in external_results
        if row.get("category") in {"positive", "wrong-target"}
    ]
    if len(paired_rows) != 2 * FULL_POSITIVE_COUNT:
        raise H0ValidationError("every positive needs one exact wrong-target pair")
    if any(
        row.get("expected") == "certificate_rejected"
        and row.get("python_disposition") != "certificate_rejected"
        for row in paired_rows
    ):
        raise H0ValidationError("a wrong-target pair lost its safe classification")

    regressions = _run_required_regressions(
        timeout_seconds=_remaining_seconds(
            campaign_deadline_ns, "required regression tests"
        )
    ) if run_regressions else {
        "skipped": True,
        "tests": list(REQUIRED_REGRESSION_TESTS),
    }
    artifact_rows = [
        {
            key: value
            for key, value in row.items()
            if key not in {"duration_ns", "path"}
        }
        for row in external_results
    ]
    final_repository = _git_identity(require_clean=require_clean)
    final_sources = _source_manifest()
    _remaining_seconds(campaign_deadline_ns, "final campaign sealing")
    _require_unchanged_repository(
        repository,
        implementation_sources,
        final_repository,
        final_sources,
    )
    eligible, ineligibility_reasons = _campaign_eligibility(
        require_clean=require_clean,
        run_regressions=run_regressions,
    )
    report = {
        "boundary_mutations": list(boundary_results),
        "claim_boundary": {
            "decision_claim": False,
            "negative_theoremhood_claims": 0,
            "published_kinds": ["proved", "unknown"],
            "wrong_target_meaning": (
                "the retained certificate was rejected for that target; no "
                "claim about theoremhood of the target"
            ),
        },
        "cold_replay": cold_summary,
        "conformance": {
            "artifact_case_count": len(artifact_rows),
            "artifact_case_root_contract": "sha256 of canonical JSON artifact_cases",
            "artifact_case_root_sha256": digest_json(artifact_rows),
            "artifact_cases": artifact_rows,
            "formula_root_contract": (
                "sha256 of canonical JSON array of positive formula SHA-256 values "
                "in public-then-generated order"
            ),
            "formula_root_sha256": digest_json(list(all_formula_hashes)),
            "generated_count": GENERATED_COUNT,
            "library_count": FULL_LIBRARY_COUNT,
            "mutation_count": len(mutations),
            "positive_count": FULL_POSITIVE_COUNT,
            "positive_rows": list(positive_rows),
            "wrong_target_count": FULL_POSITIVE_COUNT,
        },
        "external_envelopes": {
            "lean": "all campaign artifacts",
            "rust": {
                "max_bytes": RUST_MAX_BYTES,
                "max_check_steps": RUST_MAX_CHECK_STEPS,
                "max_depth": RUST_MAX_DEPTH,
                "max_nodes": RUST_MAX_NODES,
                "max_wire_nat": RUST_MAX_WIRE_NAT,
            },
            "wasm": {
                "max_bytes": WASM_MAX_BYTES,
                "max_check_steps": WASM_MAX_CHECK_STEPS,
                "max_depth": WASM_MAX_DEPTH,
                "max_nodes": WASM_MAX_NODES,
                "max_portable_index": WASM_MAX_PORTABLE_INDEX,
                "max_wire_nat": WASM_MAX_WIRE_NAT,
            },
            "coverage": _portable_counts(artifact_rows),
            "probes": {
                "checker_path_fuel": "mutation-zero-checker-fuel",
                "wasm_portable_index": (
                    "mutation-wasm-portable-index-envelope"
                ),
                "wire_nat": "mutation-wire-nat-envelope",
            },
            "interpretation": (
                "Rust/WASM out_of_envelope is a pre-registered resource boundary, "
                "not a semantic disagreement or profile limit. The exact global "
                "checker-step ceilings are implementation-identity declarations; "
                "the retained zero-fuel case probes bounded-checker enforcement."
            ),
        },
        "format": REPORT_FORMAT,
        "implementation_sources": implementation_sources,
        "macro_protocol_controls": macro_controls,
        "profile_sha256": semantic_profile_sha256(),
        "reference_identity": second["external_identity"],
        "regressions": regressions,
        "repository": repository,
        "result_schema_controls": schema_controls,
        "semantic_conformance_format": CONFORMANCE_FORMAT,
        "semantic_conformance_v": CONFORMANCE_VERSION,
        "timing": {
            **cold_timing,
            "generated_and_mutation_external_duration_ns": generated_duration_ns,
            "generated_external_components": generated_external_timing,
            "library_external_components": second.get("external_timing"),
            "interpretation": "observational only; excluded from every semantic root",
        },
        "campaign_eligible": eligible,
        "ineligibility_reasons": ineligibility_reasons,
        "validation_passed": eligible,
        "v": REPORT_VERSION,
    }
    # This final round trip also ensures no Path or byte object escaped into
    # the retained evidence.
    canonical_json_bytes(report)
    _remaining_seconds(campaign_deadline_ns, "canonical report construction")
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--lean-verifier", type=Path)
    parser.add_argument("--lean-source-root", type=Path)
    parser.add_argument("--rust-cli", type=Path)
    parser.add_argument("--node", type=Path)
    parser.add_argument("--wasm", type=Path)
    parser.add_argument(
        "--timeout-seconds", type=float, default=DEFAULT_TIMEOUT_SECONDS
    )
    parser.add_argument(
        "--campaign-timeout-seconds",
        type=float,
        default=DEFAULT_CAMPAIGN_TIMEOUT_SECONDS,
    )
    parser.add_argument("--cold-worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--require-complete-library", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--theorem", action="append", help=argparse.SUPPRESS)
    parser.add_argument("--allow-dirty", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--skip-regressions", action="store_true", help=argparse.SUPPRESS)
    return parser


def _external_from_args(args: argparse.Namespace) -> ExternalVerifierSuite | None:
    values = (
        args.lean_verifier,
        args.lean_source_root,
        args.rust_cli,
        args.node,
        args.wasm,
    )
    if all(value is None for value in values):
        return None
    if any(value is None for value in values):
        raise H0ValidationError(
            "external checking requires explicit Lean source/verifier, Rust, Node, and WASM paths"
        )
    return ExternalVerifierSuite(
        lean_verifier=args.lean_verifier,
        lean_source_root=args.lean_source_root,
        rust_cli=args.rust_cli,
        node=args.node,
        wasm=args.wasm,
        timeout_seconds=args.timeout_seconds,
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.cold_worker:
            names = _worker_names(args.theorem)
            payload = cold_library_replay(
                names,
                external=_external_from_args(args),
                require_complete_library=args.require_complete_library,
            )
        else:
            if any(
                value is None
                for value in (
                    args.lean_verifier,
                    args.lean_source_root,
                    args.rust_cli,
                    args.node,
                    args.wasm,
                )
            ):
                raise H0ValidationError(
                    "full H0 validation requires explicit --lean-source-root, "
                    "--lean-verifier, --rust-cli, --node, and --wasm paths"
                )
            payload = validate_campaign(
                lean_verifier=args.lean_verifier,
                lean_source_root=args.lean_source_root,
                rust_cli=args.rust_cli,
                node=args.node,
                wasm=args.wasm,
                timeout_seconds=args.timeout_seconds,
                campaign_timeout_seconds=args.campaign_timeout_seconds,
                require_clean=not args.allow_dirty,
                run_regressions=not args.skip_regressions,
            )
        _atomic_write_json(args.output, payload)
    except (ConformanceError, H0ValidationError) as error:
        print(f"H0_VALIDATION_ERROR: {error}", file=sys.stderr)
        return 1
    if not args.cold_worker and payload.get("validation_passed") is True:
        print(
            f"H0 PASS: {payload['conformance']['positive_count']} positives, "
            f"cold root {payload['cold_replay']['root_sha256']}"
        )
    elif not args.cold_worker:
        print(
            "H0 DEVELOPMENT REPORT: campaign-ineligible ("
            + ", ".join(payload["ineligibility_reasons"])
            + ")"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
