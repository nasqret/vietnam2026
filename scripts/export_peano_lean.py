#!/usr/bin/env python3
"""Export and optionally verify a completed Lean theorem from a Peano proof."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import signal
import subprocess
import sys
import tempfile
import time


ROOT = Path(__file__).resolve().parents[1]
PEANO_PYTHON = ROOT / "peano-lab" / "py"
if str(PEANO_PYTHON) not in sys.path:
    sys.path.insert(0, str(PEANO_PYTHON))

from peano_lab.library.lean_certified import (  # noqa: E402
    export_checked_bundle_theorem,
    export_checked_theorem,
)
from peano_lab.library.proof_bundle import (  # noqa: E402
    DEFAULT_BUNDLE_LIMITS,
    decode_proof_bundle,
)
from peano_lab.library.theorems import _closed_formula, get, replay  # noqa: E402


PACKAGE_MANIFEST_SCHEMA = "peano-lean-presentation-package-v1"
PRESENTATION_MANIFEST_SCHEMA = "peano-lab-lean-presentation-v1"
STRAND_PACKAGE_MANIFEST_SCHEMA = "peano-lean-proof-strand-package-v1"
STRAND_MANIFEST_SCHEMA = "peano-lab-lean-proof-strand-v1"
MAX_PACKAGE_MANIFEST_BYTES = 8 * 1024 * 1024
MAX_PACKAGE_PRESENTATIONS = 4_096
MAX_PACKAGE_MODULE_BYTES = 64 * 1024 * 1024
MAX_STRAND_TERMINAL_BYTES = 64 * 1024
DEFAULT_LIVE_URL_BYTES = 512 * 1024
MAX_LIVE_URL_BYTES = 1024 * 1024
MAX_PROGRESS_INLINE_URL_BYTES = 8 * 1024
MAX_LEAN_FAILURE_DIAGNOSTIC_BYTES = 128 * 1024
LEAN_VERIFIER_SOURCE_MEMORY_AMPLIFICATION = 2_048
_PACKAGE_TOKEN = re.compile(r"[A-Za-z][A-Za-z0-9_]*\Z")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_LEAN_ERROR_LOCATION = re.compile(
    r"^(?P<source>.+\.lean):(?P<line>[0-9]+):[0-9]+: error(?:\([A-Za-z][A-Za-z0-9_.]*\))?:",
    re.MULTILINE,
)
_STRAND_AUTHORITY_FIELDS = frozenset(
    {
        "lean_compiler_verified",
        "public_admission",
        "publication",
        "training",
        "final_evaluation",
    }
)
_LEAN_IMPORT_BOOTSTRAP = (
    "import os,sys; "
    "previous=os.environ.get('LEAN_PATH',''); "
    "os.environ['LEAN_PATH']=sys.argv[1]+"
    "(os.pathsep+previous if previous else ''); "
    "os.execv(sys.argv[2],sys.argv[2:])"
)
_ACTIVE_VERIFIER_PROCESS: subprocess.Popen[str] | None = None


class LeanVerificationError(ValueError):
    """A genuine Lean rejection, retaining bounded diagnostic coordinates."""

    def __init__(self, message: str, diagnostics: str) -> None:
        super().__init__(message)
        encoded = diagnostics.encode("utf-8")
        self.diagnostics = encoded[:MAX_LEAN_FAILURE_DIAGNOSTIC_BYTES].decode(
            "utf-8",
            errors="ignore",
        )
        self.diagnostics_truncated = len(encoded) > MAX_LEAN_FAILURE_DIAGNOSTIC_BYTES


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Translate one independently checked Peano theorem into a complete "
            "Lean 4 theorem through the verified certificate checker."
        )
    )
    parser.add_argument("theorem", help="exact public Peano theorem name")
    parser.add_argument(
        "--edition",
        choices=("stable", "alpha"),
        default="stable",
        help="select the public Stable library or an explicitly checked Alpha theorem",
    )
    parser.add_argument(
        "--format",
        choices=("full", "compact", "pretty", "exact", "outline", "strand", "live"),
        default="full",
        help=(
            "full: existing self-contained Lean source; compact: short checked "
            "facade; pretty: human-readable preview; exact: expanded proposition; "
            "outline: bounded dependency/proof preview without replay; strand: "
            "reconstruct the complete named constructive proof dependency chain; "
            "live: standalone readable-only Lean Live source with no private imports"
        ),
    )
    parser.add_argument(
        "--package-dir",
        type=Path,
        help=(
            "write the reusable notation, certificate, theorem facade, and "
            "deterministic manifest beneath this explicitly selected directory"
        ),
    )
    parser.add_argument(
        "--proof-bundle",
        type=Path,
        help="translate this complete canonical self-contained proof DAG instead",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="write the generated Lean module to this path; default prints stdout",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="allow replacement of an explicitly selected existing output file",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="typecheck the emitted complete theorem inside the Lean companion",
    )
    parser.add_argument(
        "--lean-project",
        type=Path,
        default=ROOT.parent / "peano-lab-lean",
        help="path to the separately verified Peano Lab Lean project",
    )
    parser.add_argument(
        "--lake",
        type=Path,
        help="explicit installed Lake executable; never downloads a toolchain",
    )
    parser.add_argument(
        "--no-axiom-audit",
        action="store_true",
        help="omit the final Lean axiom-dependency report",
    )
    parser.add_argument(
        "--max-memory-mib",
        type=int,
        default=1536,
        help=(
            "set Lean's internal memory limit and conservative source-size "
            "preflight in MiB; this is not an operating-system RSS cap (default: 1536)"
        ),
    )
    parser.add_argument(
        "--max-verify-seconds",
        type=int,
        default=180,
        help="terminate the complete Lean process group after this many seconds (default: 180)",
    )
    parser.add_argument(
        "--max-strand-nodes",
        type=int,
        default=2_048,
        help="maximum checked-use theorem nodes in an on-demand proof strand (default: 2048)",
    )
    parser.add_argument(
        "--max-strand-edges",
        type=int,
        default=8_192,
        help="maximum named prerequisite edges in an on-demand proof strand (default: 8192)",
    )
    parser.add_argument(
        "--max-strand-depth",
        type=int,
        default=128,
        help="maximum named-prerequisite depth in an on-demand proof strand (default: 128)",
    )
    parser.add_argument(
        "--max-proof-steps",
        type=int,
        default=4_096,
        help="maximum authored tactic steps for each individual strand theorem (default: 4096)",
    )
    parser.add_argument(
        "--strict-readable",
        action="store_true",
        help="reject a strand unless every named theorem has a fully translated Lean proof",
    )
    parser.add_argument(
        "--max-proof-repairs",
        type=int,
        default=16,
        help=(
            "maximum compiler-guided conversions of unsupported readable "
            "steps into independently checked local certificates (default: 16)"
        ),
    )
    parser.add_argument(
        "--max-chunk-kib",
        type=int,
        default=192,
        help=(
            "maximum source size in KiB for each independently compiled "
            "dependency-topological proof-strand module (default: 192)"
        ),
    )
    parser.add_argument(
        "--progress-json",
        action="store_true",
        help="write factual bounded per-node progress as flushed JSON lines on stderr",
    )
    parser.add_argument(
        "--live-lean-output",
        type=Path,
        help="also write standalone readable-only Lean source and its exact live.json receipt",
    )
    parser.add_argument(
        "--max-live-url-bytes",
        type=int,
        default=DEFAULT_LIVE_URL_BYTES,
        help="maximum exact UTF-8 bytes of a Lean Live share URL (default: 524288)",
    )
    parser.add_argument(
        "--max-live-source-kib",
        type=int,
        default=1_024,
        help="maximum standalone Lean Live source size in KiB (default: 1024)",
    )
    return parser


def _progress_callback(args: argparse.Namespace):
    """Emit machine-readable progress without changing theorem-source stdout."""

    if not getattr(args, "progress_json", False):
        return None

    def send(event: dict[str, object]) -> None:
        print(
            json.dumps(event, ensure_ascii=True, sort_keys=True, separators=(",", ":")),
            file=sys.stderr,
            flush=True,
        )

    return send


def _emit_cli_progress(
    args: argparse.Namespace,
    *,
    stage: str,
    completed: int,
    total: int,
    **metadata: object,
) -> None:
    callback = _progress_callback(args)
    if callback is None:
        return
    live_url = metadata.get("live_url")
    if type(live_url) is str:
        encoded_url = live_url.encode("utf-8")
        if len(encoded_url) > MAX_PROGRESS_INLINE_URL_BYTES:
            metadata = {
                **metadata,
                "live_url": None,
                "live_url_omitted": True,
                "live_url_bytes": len(encoded_url),
                "live_url_sha256": sha256(encoded_url).hexdigest(),
            }
    callback(
        {
            "kind": "lean_strand_progress",
            "stage": stage,
            "completed": completed,
            "total": total,
            **metadata,
        }
    )


def _cancel_active_verifier(signum: int, _frame: object) -> None:
    """Forward service cancellation into the private nested Lean process group."""

    process = _ACTIVE_VERIFIER_PROCESS
    if process is not None and process.poll() is None:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                pass
    raise SystemExit(128 + signum)


def _lake_binary(project: Path, explicit: Path | None) -> Path:
    if explicit is not None:
        candidate = explicit.expanduser().resolve()
        if not candidate.is_file():
            raise ValueError(f"Lake executable does not exist: {candidate}")
        return candidate

    installed = Path.home() / ".elan" / "toolchains"
    pinned = project / "lean-toolchain"
    preferred: list[Path] = []
    if pinned.is_file():
        identity = pinned.read_text(encoding="utf-8").strip()
        encoded = identity.replace("/", "--").replace(":", "---")
        preferred.append(installed / encoded / "bin" / "lake")

    def version_key(path: Path) -> tuple[int, int, int, int]:
        match = re.search(r"v(\d+)\.(\d+)\.(\d+)(?:-rc(\d+))?$", path.name)
        if match is None:
            return (-1, -1, -1, -1)
        major, minor, patch, release_candidate = match.groups()
        return (
            int(major),
            int(minor),
            int(patch),
            10_000 if release_candidate is None else int(release_candidate),
        )

    if installed.is_dir():
        for directory in sorted(installed.iterdir(), key=version_key, reverse=True):
            preferred.append(directory / "bin" / "lake")

    for candidate in preferred:
        if candidate.is_file():
            return candidate
    raise ValueError(
        "no installed Lean/Lake toolchain was found; install one or pass --lake"
    )


def _require_lean_verifier_source_budget(
    module: Path,
    *,
    max_memory_mib: int,
) -> None:
    """Fail closed before launching Lean for sources with unsafe size margins."""

    try:
        source_bytes = module.stat().st_size
    except OSError as error:
        raise ValueError(
            f"Lean verification source cannot be inspected before launch: {module}"
        ) from error

    maximum_source_bytes = (
        max_memory_mib * 1024 * 1024 // LEAN_VERIFIER_SOURCE_MEMORY_AMPLIFICATION
    )
    if source_bytes <= maximum_source_bytes:
        return

    estimated_memory_mib = (
        source_bytes * LEAN_VERIFIER_SOURCE_MEMORY_AMPLIFICATION + 1024 * 1024 - 1
    ) // (1024 * 1024)
    raise ValueError(
        "Lean verification refused before launching any compiler: "
        f"source {module} has {source_bytes:,} bytes, exceeding the "
        f"{maximum_source_bytes:,}-byte conservative source ceiling for its "
        f"{max_memory_mib}-MiB budget "
        f"({LEAN_VERIFIER_SOURCE_MEMORY_AMPLIFICATION:,}x source-to-memory "
        f"safety factor; estimated reviewed budget {estimated_memory_mib:,} MiB). "
        "Lean's internal -M flag is not an operating-system RSS cap; export "
        "without --verify and use the independently compiled bundle verifier "
        "for large canonical artifacts."
    )


def _verify(
    module: Path,
    project: Path,
    lake: Path,
    *,
    max_memory_mib: int,
    max_verify_seconds: int,
    package_root: Path | None = None,
    output_olean: Path | None = None,
    import_root: Path | None = None,
    emit_failed_diagnostics: bool = True,
) -> None:
    global _ACTIVE_VERIFIER_PROCESS
    if not project.is_dir() or not (project / "PeanoLab" / "Codec.lean").is_file():
        raise ValueError(
            "the Lean project must contain the separately verified PeanoLab.Codec"
        )
    _require_lean_verifier_source_budget(module, max_memory_mib=max_memory_mib)
    lean_arguments = ["-M", str(max_memory_mib), "-j", "1"]
    environment: dict[str, str] | None = None
    if package_root is not None:
        lean_arguments.extend(("-R", str(package_root)))
    if output_olean is not None:
        lean_arguments.extend(("-o", str(output_olean)))
    lean_arguments.append(str(module))

    if import_root is None:
        command = [str(lake), "env", "lean", *lean_arguments]
    else:
        lean = lake.parent / "lean"
        if not lean.is_file():
            raise ValueError(f"Lean executable beside Lake does not exist: {lean}")
        command = [
            str(lake),
            "env",
            sys.executable,
            "-c",
            _LEAN_IMPORT_BOOTSTRAP,
            str(import_root),
            str(lean),
            *lean_arguments,
        ]

    process = subprocess.Popen(
        command,
        cwd=project,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    _ACTIVE_VERIFIER_PROCESS = process
    try:
        stdout, stderr = process.communicate(timeout=max_verify_seconds)
    except subprocess.TimeoutExpired as exc:
        # Lake is a wrapper around the actual Lean process. Killing only Lake
        # would leave an unbounded orphan behind, so this session is private.
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            process.communicate(timeout=2)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.communicate()
        raise ValueError(
            f"Lean verification exceeded its {max_verify_seconds}-second limit"
        ) from exc
    finally:
        if _ACTIVE_VERIFIER_PROCESS is process:
            _ACTIVE_VERIFIER_PROCESS = None

    if process.returncode != 0:
        error = LeanVerificationError("Lean rejected the generated theorem", stdout + stderr)
        if emit_failed_diagnostics:
            print(error.diagnostics, file=sys.stderr, end="")
            if error.diagnostics_truncated:
                print("\n[Lean diagnostics truncated at the reviewed safety limit]", file=sys.stderr)
        raise error
    output = stdout + stderr
    if "sorryAx" in output:
        raise ValueError(
            "the generated Lean theorem depends on an incomplete proof (sorryAx)"
        )
    if "Lean.trustCompiler" in output:
        raise ValueError(
            "the generated Lean theorem unexpectedly trusts native code "
            "(Lean.trustCompiler)"
        )
    if stdout:
        print(stdout, file=sys.stderr, end="")
    if stderr:
        print(stderr, file=sys.stderr, end="")


def _atomic_write_text(destination: Path, content: str) -> None:
    """Replace one explicitly selected file only after its complete text is ready."""

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=destination.parent,
            prefix=".peano-lean-",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _safe_package_destination(root: Path, relative: str) -> Path:
    """Reject traversal, absolute paths, foreign roots, and symlinked parents."""

    if type(relative) is not str or not relative or "\\" in relative:
        raise ValueError("Lean package path must be a nonempty canonical POSIX path")
    parts = relative.split("/")
    candidate = PurePosixPath(relative)
    if (
        candidate.is_absolute()
        or any(part in ("", ".", "..") for part in parts)
        or parts[0] != "PeanoLab"
        or candidate.suffix != ".lean"
    ):
        raise ValueError(f"unsafe generated Lean package path: {relative!r}")

    destination = root.joinpath(*parts)
    parent = destination.parent
    while parent != root:
        if parent.is_symlink():
            raise ValueError(f"generated Lean package parent must not be a symlink: {parent}")
        parent = parent.parent
    if destination.is_symlink():
        raise ValueError(f"generated Lean package output must not be a symlink: {destination}")
    return destination


def _presentation_files(presentation: object, root: Path) -> list[tuple[Path, str]]:
    """Validate the complete package before any destination is changed."""

    files: list[tuple[Path, str]] = []
    seen: set[Path] = set()
    for relative, content in presentation.files():  # type: ignore[attr-defined]
        destination = _safe_package_destination(root, relative)
        if destination in seen:
            raise ValueError(f"duplicate generated Lean package path: {relative}")
        if type(content) is not str:
            raise ValueError(f"generated Lean package content is not text: {relative}")
        if not content.endswith("\n"):
            raise ValueError(f"generated Lean package source has no final newline: {relative}")
        if len(content.encode("utf-8")) > MAX_PACKAGE_MODULE_BYTES:
            raise ValueError(
                f"generated Lean package source exceeds its reviewed byte limit: {relative}"
            )
        files.append((destination, content))
        seen.add(destination)

    return files


def _canonical_manifest(record: dict[str, object]) -> str:
    encoded = json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if len(encoded.encode("utf-8")) > MAX_PACKAGE_MANIFEST_BYTES:
        raise ValueError("Lean package manifest exceeds its reviewed byte limit")
    return encoded


def _bounded_existing_text(path: Path, *, maximum: int, label: str) -> str:
    if path.stat().st_size > maximum:
        raise ValueError(f"{label} exceeds its reviewed byte limit")
    return path.read_text(encoding="utf-8")


def _file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(65_536), b""):
            digest.update(block)
    return digest.hexdigest()


def _validate_existing_presentation(token: str, record: object, root: Path) -> None:
    """Preserve only exact independently content-bound prior package entries."""

    if (
        type(record) is not dict
        or record.get("schema") != PRESENTATION_MANIFEST_SCHEMA
        or type(record.get("name")) is not str
        or type(record.get("edition")) is not str
        or type(record.get("identity_sha256")) is not str
        or _SHA256.fullmatch(record["identity_sha256"]) is None
        or not token.endswith("_" + record["identity_sha256"][:16])
        or type(record.get("files")) is not list
        or len(record["files"]) != 3
    ):
        raise ValueError(f"existing Lean package entry has invalid identity: {token}")

    manifest_directory = root / "manifests"
    if manifest_directory.is_symlink():
        raise ValueError("existing Lean package manifest directory is a symlink")
    entry_manifest = manifest_directory / (token + ".json")
    if entry_manifest.is_symlink() or not entry_manifest.is_file():
        raise ValueError(f"existing Lean package entry has no safe theorem manifest: {token}")
    actual = _bounded_existing_text(
        entry_manifest,
        maximum=MAX_PACKAGE_MANIFEST_BYTES,
        label="existing Lean theorem manifest",
    )
    if actual != _canonical_manifest(record):
        raise ValueError(f"existing Lean package entry manifest has been altered: {token}")

    expected_modules = {
        "PeanoLab.Presentation": "PeanoLab/Presentation.lean",
        f"PeanoLab.Generated.{token}.Certificate": (
            f"PeanoLab/Generated/{token}/Certificate.lean"
        ),
        f"PeanoLab.Generated.{token}.Theorem": (
            f"PeanoLab/Generated/{token}/Theorem.lean"
        ),
    }
    observed: set[str] = set()
    for item in record["files"]:
        if (
            type(item) is not dict
            or set(item) != {"module", "relative_path", "sha256", "bytes"}
            or type(item.get("module")) is not str
            or item["module"] not in expected_modules
            or item.get("relative_path") != expected_modules[item["module"]]
            or type(item.get("sha256")) is not str
            or _SHA256.fullmatch(item["sha256"]) is None
            or type(item.get("bytes")) is not int
            or not 0 < item["bytes"] <= MAX_PACKAGE_MODULE_BYTES
        ):
            raise ValueError(f"existing Lean package entry has invalid source records: {token}")
        source = _safe_package_destination(root, item["relative_path"])
        if (
            not source.is_file()
            or source.stat().st_size != item["bytes"]
            or _file_sha256(source) != item["sha256"]
        ):
            raise ValueError(f"existing Lean package entry source has been altered: {token}")
        observed.add(item["module"])
    if observed != set(expected_modules):
        raise ValueError(f"existing Lean package entry has incomplete source records: {token}")


def _presentation_token(presentation: object) -> str:
    module = presentation.certificate_module  # type: ignore[attr-defined]
    if type(module) is not str:
        raise ValueError("generated certificate module must have an exact module name")
    parts = module.split(".")
    if (
        len(parts) != 4
        or parts[:2] != ["PeanoLab", "Generated"]
        or parts[-1] != "Certificate"
        or _PACKAGE_TOKEN.fullmatch(parts[2]) is None
    ):
        raise ValueError(f"unsafe generated certificate module: {module!r}")
    return parts[2]


def _package_manifests(
    presentation: object,
    root: Path,
    *,
    force: bool,
) -> list[tuple[Path, str]]:
    """Preserve every prior package entry while adding one authenticated theorem."""

    token = _presentation_token(presentation)
    notation = presentation.notation_module  # type: ignore[attr-defined]
    if type(notation) is not str or notation != "PeanoLab.Presentation":
        raise ValueError("generated package has an unexpected shared notation module")
    individual = presentation.manifest  # type: ignore[attr-defined]
    if type(individual) is not dict:
        raise ValueError("generated theorem manifest must be an exact JSON object")

    manifest = root / "manifest.json"
    if manifest.is_symlink():
        raise ValueError(f"generated Lean package manifest must not be a symlink: {manifest}")
    if manifest.exists():
        if not manifest.is_file():
            raise ValueError(f"generated Lean package manifest is not a file: {manifest}")
        raw = _bounded_existing_text(
            manifest,
            maximum=MAX_PACKAGE_MANIFEST_BYTES,
            label="existing Lean package manifest",
        )
        try:
            previous = json.loads(raw)
        except (TypeError, ValueError) as error:
            raise ValueError("existing Lean package manifest is not valid JSON") from error
        if (
            type(previous) is not dict
            or set(previous)
            != {"schema", "notation_module", "presentation_count", "presentations"}
            or previous.get("schema") != PACKAGE_MANIFEST_SCHEMA
            or previous.get("notation_module") != notation
            or type(previous.get("presentations")) is not dict
            or type(previous.get("presentation_count")) is not int
            or not 0 <= previous["presentation_count"] <= MAX_PACKAGE_PRESENTATIONS
            or previous["presentation_count"] != len(previous["presentations"])
            or raw != _canonical_manifest(previous)
        ):
            raise ValueError("existing Lean package manifest is not a canonical presentation catalog")
        entries = dict(previous["presentations"])
        if any(
            type(key) is not str
            or _PACKAGE_TOKEN.fullmatch(key) is None
            or type(value) is not dict
            for key, value in entries.items()
        ):
            raise ValueError("existing Lean package manifest contains an unsafe theorem entry")
        for key, value in entries.items():
            _validate_existing_presentation(key, value, root)
    else:
        entries = {}

    if token not in entries and len(entries) >= MAX_PACKAGE_PRESENTATIONS:
        raise ValueError("Lean package exceeds its reviewed theorem-count limit")
    if token in entries and entries[token] != individual and not force:
        raise ValueError(
            f"Lean package already contains a different manifest for {token}; "
            "use --force to replace it"
        )
    entries[token] = individual
    aggregate: dict[str, object] = {
        "schema": PACKAGE_MANIFEST_SCHEMA,
        "notation_module": notation,
        "presentation_count": len(entries),
        "presentations": entries,
    }

    manifest_directory = root / "manifests"
    if manifest_directory.is_symlink():
        raise ValueError(
            f"generated Lean package manifest directory must not be a symlink: {manifest_directory}"
        )
    theorem_manifest = manifest_directory / (token + ".json")
    if theorem_manifest.is_symlink():
        raise ValueError(
            f"generated Lean theorem manifest must not be a symlink: {theorem_manifest}"
        )
    return [
        (theorem_manifest, _canonical_manifest(individual)),
        (manifest, _canonical_manifest(aggregate)),
    ]


def _write_presentation_package(
    presentation: object,
    directory: Path,
    *,
    force: bool,
) -> Path:
    """Write three deterministic Lean modules and their audited manifest."""

    chosen = directory.expanduser()
    if chosen.is_symlink():
        raise ValueError(f"Lean package directory must not be a symlink: {chosen}")
    root = chosen.resolve()
    if root.exists() and not root.is_dir():
        raise ValueError(f"Lean package destination is not a directory: {root}")

    files = _presentation_files(presentation, root)
    manifests = _package_manifests(presentation, root, force=force)
    aggregate_path = root / "manifest.json"
    files.extend(manifests)
    for destination, content in files:
        if destination.exists():
            if not destination.is_file():
                raise ValueError(f"Lean package destination is not a file: {destination}")
            maximum = (
                MAX_PACKAGE_MANIFEST_BYTES
                if destination.suffix == ".json"
                else MAX_PACKAGE_MODULE_BYTES
            )
            existing = _bounded_existing_text(
                destination,
                maximum=maximum,
                label="existing Lean package output",
            )
            if (
                destination != aggregate_path
                and existing != content
                and not force
            ):
                raise ValueError(
                    f"output already exists: {destination}; use --force to replace it"
                )

    root.mkdir(parents=True, exist_ok=True)
    for destination, content in files:
        if not destination.exists() or _bounded_existing_text(
            destination,
            maximum=(
                MAX_PACKAGE_MANIFEST_BYTES
                if destination.suffix == ".json"
                else MAX_PACKAGE_MODULE_BYTES
            ),
            label="existing Lean package output",
        ) != content:
            _atomic_write_text(destination, content)
    return root


def _strand_token(package: object) -> str:
    """Validate the semantic, content-addressed module identity of one strand."""

    module = package.module_name  # type: ignore[attr-defined]
    if type(module) is not str:
        raise ValueError("generated proof strand must have an exact module name")
    parts = module.split(".")
    if (
        len(parts) != 4
        or parts[:2] != ["PeanoLab", "Generated"]
        or parts[-1] != "Strand"
        or _PACKAGE_TOKEN.fullmatch(parts[2]) is None
    ):
        raise ValueError(f"unsafe generated proof-strand module: {module!r}")
    return parts[2]


def _strand_record_identity(record: dict[str, object]) -> str:
    """Recompute the exact release/source identity; manifests cannot grant trust."""

    root = record.get("name")
    edition = record.get("edition")
    version = record.get("edition_version")
    edition_digest = record.get("edition_identity_sha256")
    rows = record.get("nodes")
    if (
        type(root) is not str
        or _PACKAGE_TOKEN.fullmatch(root) is None
        or type(edition) is not str
        or edition not in {"stable", "alpha"}
        or type(version) is not str
        or (edition == "stable" and version != "stable")
        or (edition == "alpha" and re.fullmatch(r"v[1-9][0-9]*", version) is None)
        or type(edition_digest) is not str
        or _SHA256.fullmatch(edition_digest) is None
        or type(rows) is not list
        or not 1 <= len(rows) <= MAX_PACKAGE_PRESENTATIONS
    ):
        raise ValueError("proof-strand manifest has an invalid root or release identity")

    identity_rows: list[dict[str, str]] = []
    seen: set[str] = set()
    translated = 0
    fallback = 0
    edges = 0
    for row in rows:
        if type(row) is not dict:
            raise ValueError("proof-strand manifest has a non-object theorem node")
        name = row.get("name")
        specification_digest = row.get("specification_sha256")
        source_digest = row.get("source_sha256")
        evidence = row.get("evidence")
        dependencies = row.get("dependencies")
        status = row.get("proof_status")
        if (
            type(name) is not str
            or _PACKAGE_TOKEN.fullmatch(name) is None
            or name in seen
            or type(specification_digest) is not str
            or _SHA256.fullmatch(specification_digest) is None
            or type(source_digest) is not str
            or _SHA256.fullmatch(source_digest) is None
            or type(evidence) is not str
            or evidence not in {"stable_closed", "alpha_closed"}
            or (edition == "stable" and evidence != "stable_closed")
            or type(dependencies) is not list
            or any(type(item) is not str or item not in seen for item in dependencies)
            or len(set(dependencies)) != len(dependencies)
            or type(status) is not str
            or status not in {"readable_lean", "local_checked_certificate"}
        ):
            raise ValueError("proof-strand manifest has invalid theorem provenance")
        edges += len(dependencies)
        translated += int(status == "readable_lean")
        fallback += int(status == "local_checked_certificate")
        seen.add(name)
        identity_rows.append(
            {
                "name": name,
                "specification_sha256": specification_digest,
                "source_sha256": source_digest,
                "evidence": evidence,
            }
        )
    if (
        identity_rows[-1]["name"] != root
        or type(record.get("node_count")) is not int
        or record["node_count"] != len(identity_rows)
        or type(record.get("edge_count")) is not int
        or record["edge_count"] != edges
        or type(record.get("translated_node_count")) is not int
        or record["translated_node_count"] != translated
        or type(record.get("fallback_node_count")) is not int
        or record["fallback_node_count"] != fallback
    ):
        raise ValueError("proof-strand manifest has inconsistent root or proof-status totals")

    identity = {
        "root": root,
        "edition": edition,
        "edition_version": version,
        "edition_identity_sha256": edition_digest,
        "nodes": identity_rows,
    }
    encoded = json.dumps(
        identity,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(encoded.encode("utf-8")).hexdigest()


def _strand_source_records(
    record: dict[str, object],
    token: str,
    root: Path,
    *,
    expected_sources: dict[str, str] | None = None,
    require_existing: bool,
) -> None:
    """Validate every contiguous chunk and every theorem-to-source mapping."""

    chunks = record.get("chunk_count")
    ceiling = record.get("maximum_chunk_bytes")
    entries = record.get("files")
    if (
        type(chunks) is not int
        or not 0 <= chunks <= MAX_PACKAGE_PRESENTATIONS
        or type(ceiling) is not int
        or not 1 <= ceiling <= MAX_PACKAGE_MODULE_BYTES
        or type(entries) is not list
        or len(entries) != chunks + 2
    ):
        raise ValueError(f"proof strand has incomplete bounded source records: {token}")

    prefix = f"PeanoLab.Generated.{token}"
    modules = [
        "PeanoLab.Presentation",
        *(f"{prefix}.Chunks.C{index:03d}" for index in range(chunks)),
        f"{prefix}.Strand",
    ]
    module_indices: dict[str, int] = {}
    total = 0
    for index, (item, expected_module) in enumerate(zip(entries, modules, strict=True)):
        if (
            type(item) is not dict
            or set(item) != {"module", "relative_path", "sha256", "bytes"}
            or item.get("module") != expected_module
            or type(item.get("relative_path")) is not str
            or item["relative_path"] != expected_module.replace(".", "/") + ".lean"
            or type(item.get("sha256")) is not str
            or _SHA256.fullmatch(item["sha256"]) is None
            or type(item.get("bytes")) is not int
            or not 0 < item["bytes"] <= MAX_PACKAGE_MODULE_BYTES
            or (index > 0 and item["bytes"] > ceiling)
        ):
            raise ValueError(f"proof strand has invalid contiguous source records: {token}")
        path = _safe_package_destination(root, item["relative_path"])
        if expected_sources is not None:
            source = expected_sources.get(item["relative_path"])
            if type(source) is not str:
                raise ValueError(f"proof strand has no exact generated source: {token}")
            payload = source.encode("utf-8")
            if len(payload) != item["bytes"] or sha256(payload).hexdigest() != item["sha256"]:
                raise ValueError(f"proof-strand generated source digest is invalid: {token}")
        if require_existing and (
            not path.is_file()
            or path.stat().st_size != item["bytes"]
            or _file_sha256(path) != item["sha256"]
        ):
            raise ValueError(f"existing proof-strand source has been altered: {token}")
        if index:
            total += item["bytes"]
        module_indices[expected_module] = index
    if total > MAX_PACKAGE_MODULE_BYTES:
        raise ValueError(f"proof strand exceeds its total bounded source budget: {token}")
    if expected_sources is not None and set(expected_sources) != {
        item["relative_path"] for item in entries
    }:
        raise ValueError(f"proof strand includes unmanifested generated modules: {token}")

    previous = 0
    for node in record["nodes"]:
        module = node.get("generated_module")
        relative = node.get("generated_relative_path")
        first = node.get("source_line_start")
        last = node.get("source_line_end")
        position = module_indices.get(module) if type(module) is str else None
        if (
            position is None
            or position == 0
            or (chunks and position == len(modules) - 1)
            or position < previous
            or type(relative) is not str
            or relative != module.replace(".", "/") + ".lean"
            or type(first) is not int
            or type(last) is not int
            or not 1 <= first <= last
        ):
            raise ValueError(f"proof strand has an unsafe theorem-to-module mapping: {token}")
        previous = position


def _validate_existing_strand(token: str, record: object, root: Path) -> None:
    """Reject tampered metadata, authority claims, or generated Lean modules."""

    if (
        _PACKAGE_TOKEN.fullmatch(token) is None
        or type(record) is not dict
        or record.get("schema") != STRAND_MANIFEST_SCHEMA
        or record.get("module_name") != f"PeanoLab.Generated.{token}.Strand"
        or record.get("relative_path")
        != f"PeanoLab/Generated/{token}/Strand.lean"
        or type(record.get("identity_sha256")) is not str
        or _SHA256.fullmatch(record["identity_sha256"]) is None
        or not token.endswith("_" + record["identity_sha256"][:16])
        or type(record.get("node_count")) is not int
        or not 1 <= record["node_count"] <= MAX_PACKAGE_PRESENTATIONS
        or type(record.get("nodes")) is not list
        or len(record["nodes"]) != record["node_count"]
        or type(record.get("translated_node_count")) is not int
        or type(record.get("fallback_node_count")) is not int
        or record["translated_node_count"] < 0
        or record["fallback_node_count"] < 0
        or record["translated_node_count"] + record["fallback_node_count"]
        != record["node_count"]
        or type(record.get("authority")) is not dict
        or set(record["authority"]) != _STRAND_AUTHORITY_FIELDS
        or any(value is not False for value in record["authority"].values())
    ):
        raise ValueError(f"existing proof-strand entry has invalid identity: {token}")
    if _strand_record_identity(record) != record["identity_sha256"]:
        raise ValueError(f"existing proof-strand source/release identity was altered: {token}")

    directory = root / "strand-manifests"
    if directory.is_symlink():
        raise ValueError("existing proof-strand manifest directory is a symlink")
    manifest = directory / (token + ".json")
    if manifest.is_symlink() or not manifest.is_file():
        raise ValueError(f"existing proof strand has no safe individual manifest: {token}")
    actual = _bounded_existing_text(
        manifest,
        maximum=MAX_PACKAGE_MANIFEST_BYTES,
        label="existing proof-strand manifest",
    )
    if actual != _canonical_manifest(record):
        raise ValueError(f"existing proof-strand manifest has been altered: {token}")

    _strand_source_records(record, token, root, require_existing=True)


def _strand_manifests(
    package: object,
    root: Path,
    *,
    force: bool,
) -> list[tuple[Path, str]]:
    """Add one fully content-bound strand without destroying existing strands."""

    token = _strand_token(package)
    individual = package.manifest  # type: ignore[attr-defined]
    if (
        type(individual) is not dict
        or individual.get("schema") != STRAND_MANIFEST_SCHEMA
        or individual.get("module_name") != package.module_name  # type: ignore[attr-defined]
        or individual.get("relative_path") != package.relative_path  # type: ignore[attr-defined]
        or type(individual.get("identity_sha256")) is not str
        or _SHA256.fullmatch(individual["identity_sha256"]) is None
        or not token.endswith("_" + individual["identity_sha256"][:16])
        or type(individual.get("authority")) is not dict
        or set(individual["authority"]) != _STRAND_AUTHORITY_FIELDS
        or any(value is not False for value in individual["authority"].values())
    ):
        raise ValueError("generated proof strand has an invalid authoritative manifest")
    if _strand_record_identity(individual) != individual["identity_sha256"]:
        raise ValueError("generated proof strand changed its checked source/release identity")
    sources: dict[str, str] = {}
    for relative, source in package.files():  # type: ignore[attr-defined]
        if type(relative) is not str or relative in sources or type(source) is not str:
            raise ValueError("generated proof strand has duplicate or invalid module sources")
        sources[relative] = source
    _strand_source_records(
        individual,
        token,
        root,
        expected_sources=sources,
        require_existing=False,
    )

    manifest = root / "manifest.json"
    if manifest.is_symlink():
        raise ValueError(f"generated proof-strand manifest must not be a symlink: {manifest}")
    if manifest.exists():
        if not manifest.is_file():
            raise ValueError(f"generated proof-strand manifest is not a file: {manifest}")
        raw = _bounded_existing_text(
            manifest,
            maximum=MAX_PACKAGE_MANIFEST_BYTES,
            label="existing proof-strand package manifest",
        )
        try:
            previous = json.loads(raw)
        except (TypeError, ValueError) as error:
            raise ValueError("existing proof-strand package manifest is not valid JSON") from error
        if (
            type(previous) is not dict
            or set(previous)
            != {"schema", "notation_module", "strand_count", "strands"}
            or previous.get("schema") != STRAND_PACKAGE_MANIFEST_SCHEMA
            or previous.get("notation_module") != "PeanoLab.Presentation"
            or type(previous.get("strands")) is not dict
            or type(previous.get("strand_count")) is not int
            or not 0 <= previous["strand_count"] <= MAX_PACKAGE_PRESENTATIONS
            or previous["strand_count"] != len(previous["strands"])
            or raw != _canonical_manifest(previous)
        ):
            raise ValueError(
                "existing package is not a canonical proof-strand catalog; "
                "choose a separate directory for proof strands"
            )
        entries = dict(previous["strands"])
        for existing_token, record in entries.items():
            if type(existing_token) is not str:
                raise ValueError("existing proof-strand catalog has an invalid token")
            _validate_existing_strand(existing_token, record, root)
    else:
        entries = {}

    if token in entries and entries[token] != individual and not force:
        raise ValueError(f"proof strand already exists: {token}; use --force to replace it")
    entries[token] = individual
    if len(entries) > MAX_PACKAGE_PRESENTATIONS:
        raise ValueError("proof-strand package exceeds its reviewed entry limit")

    directory = root / "strand-manifests"
    if directory.is_symlink():
        raise ValueError("generated proof-strand manifest directory must not be a symlink")
    individual_path = directory / (token + ".json")
    if individual_path.is_symlink():
        raise ValueError(f"generated proof-strand manifest must not be a symlink: {individual_path}")

    aggregate: dict[str, object] = {
        "schema": STRAND_PACKAGE_MANIFEST_SCHEMA,
        "notation_module": "PeanoLab.Presentation",
        "strand_count": len(entries),
        "strands": dict(sorted(entries.items())),
    }
    return [
        (individual_path, _canonical_manifest(individual)),
        (manifest, _canonical_manifest(aggregate)),
    ]


def _write_strand_package(package: object, directory: Path, *, force: bool) -> Path:
    """Atomically publish the shared notation and complete named proof strand."""

    chosen = directory.expanduser()
    if chosen.is_symlink():
        raise ValueError(f"proof-strand package directory must not be a symlink: {chosen}")
    root = chosen.resolve()
    if root.exists() and not root.is_dir():
        raise ValueError(f"proof-strand package destination is not a directory: {root}")

    files = _presentation_files(package, root)
    manifests = _strand_manifests(package, root, force=force)
    aggregate = root / "manifest.json"
    outputs = files + manifests
    for destination, content in outputs:
        if not destination.exists():
            continue
        if not destination.is_file():
            raise ValueError(f"proof-strand package destination is not a file: {destination}")
        maximum = (
            MAX_PACKAGE_MANIFEST_BYTES
            if destination.suffix == ".json"
            else MAX_PACKAGE_MODULE_BYTES
        )
        existing = _bounded_existing_text(
            destination,
            maximum=maximum,
            label="existing proof-strand package output",
        )
        if destination != aggregate and existing != content and not force:
            raise ValueError(f"output already exists: {destination}; use --force to replace it")

    root.mkdir(parents=True, exist_ok=True)
    for destination, content in outputs:
        if not destination.exists() or _bounded_existing_text(
            destination,
            maximum=(
                MAX_PACKAGE_MANIFEST_BYTES
                if destination.suffix == ".json"
                else MAX_PACKAGE_MODULE_BYTES
            ),
            label="existing proof-strand package output",
        ) != content:
            _atomic_write_text(destination, content)
    return root


def _verify_presentation_package(
    presentation: object,
    root: Path,
    project: Path,
    lake: Path,
    *,
    max_memory_mib: int,
    max_verify_seconds: int,
    emit_failed_diagnostics: bool = True,
    progress: object | None = None,
) -> None:
    """Compile imports in dependency order without creating concurrent workers."""

    # Inspect every generated module first: compiling a small notation prelude
    # must not start any compiler if its later certificate is already unsafe.
    for relative, _content in presentation.files():  # type: ignore[attr-defined]
        _require_lean_verifier_source_budget(
            _safe_package_destination(root, relative),
            max_memory_mib=max_memory_mib,
        )

    deadline = time.monotonic() + max_verify_seconds
    with tempfile.TemporaryDirectory(prefix="peano-lean-import-overlay-") as directory:
        import_root = Path(directory)
        companion = (project / ".lake" / "build" / "lib" / "lean").resolve()
        modules = companion / "PeanoLab"
        codec = modules / "Codec.olean"
        if not codec.is_file():
            raise ValueError(
                "the independently verified Lean companion must be built before package verification"
            )

        imported = [
            source
            for source in sorted(modules.rglob("*.olean"))
            if source.is_file()
        ]
        root_module = companion / "PeanoLab.olean"
        if root_module.is_file():
            imported.append(root_module)
        for source in imported:
            resolved = source.resolve()
            try:
                resolved.relative_to(companion)
            except ValueError as error:
                raise ValueError(
                    f"compiled Lean companion module escapes its trusted project: {source}"
                ) from error
            destination = import_root / source.relative_to(companion)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.symlink_to(resolved)

        for relative, _content in presentation.files():  # type: ignore[attr-defined]
            source = _safe_package_destination(root, relative)
            output_olean = source.with_suffix(".olean")
            if output_olean.is_symlink():
                raise ValueError(
                    f"compiled Lean package output must not be a symlink: {output_olean}"
                )
            overlay = import_root / Path(relative).with_suffix(".olean")
            if overlay.is_symlink() or overlay.exists():
                raise ValueError(
                    f"generated Lean module collides with the trusted companion: {relative}"
                )
            overlay.parent.mkdir(parents=True, exist_ok=True)
            overlay.symlink_to(output_olean)

        generated = presentation.files()  # type: ignore[attr-defined]
        for index, (relative, _content) in enumerate(generated, 1):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise ValueError(
                    f"Lean package verification exceeded its {max_verify_seconds}-second limit"
                )
            source = _safe_package_destination(root, relative)
            if callable(progress):
                progress(
                    {
                        "kind": "lean_strand_progress",
                        "stage": "compile",
                        "completed": index - 1,
                        "total": len(generated),
                        "module": relative,
                    }
                )
            _verify(
                source,
                project,
                lake,
                max_memory_mib=max_memory_mib,
                max_verify_seconds=max(1, math.ceil(remaining)),
                package_root=root,
                output_olean=source.with_suffix(".olean"),
                import_root=import_root,
                emit_failed_diagnostics=emit_failed_diagnostics,
            )
            if callable(progress):
                progress(
                    {
                        "kind": "lean_strand_progress",
                        "stage": "compile",
                        "completed": index,
                        "total": len(generated),
                        "module": relative,
                    }
                )


def _selected_presentation_text(presentation: object, style: str) -> str:
    if style == "pretty":
        return presentation.preview  # type: ignore[attr-defined]
    if style == "exact":
        return presentation.exact_statement  # type: ignore[attr-defined]
    return presentation.presentation_code  # type: ignore[attr-defined]


def _checked_output_path(path: Path, *, force: bool) -> Path:
    chosen = path.expanduser()
    if chosen.is_symlink():
        raise ValueError(f"Lean output must not be a symlink: {chosen}")
    output = chosen.resolve()
    if output.exists() and not force:
        raise ValueError(f"output already exists: {output}; use --force to replace it")
    if output.exists() and not output.is_file():
        raise ValueError(f"Lean output is not a file: {output}")
    return output


def _write_selected_output(path: Path | None, text: str, *, force: bool) -> None:
    if path is None:
        print(text.rstrip("\n"))
        return
    output = _checked_output_path(path, force=force)
    _atomic_write_text(output, text.rstrip("\n") + "\n")
    print(f"Presentation: {output}", file=sys.stderr)


def _lightweight_preview(args: argparse.Namespace, specification: object) -> int:
    """Render immutable checked-use metadata without replaying its certificate."""

    from peano_lab.kernel.formulas import parse_formula
    from peano_lab.library.lean import formula_to_lean
    from peano_lab.library.lean_presentation import preview_checked_presentation

    formula = parse_formula(specification.statement)  # type: ignore[attr-defined]
    if args.format == "exact":
        text = formula_to_lean(formula)
    else:
        text = preview_checked_presentation(
            specification.name,  # type: ignore[attr-defined]
            formula,
            source_statement=specification.statement,  # type: ignore[attr-defined]
            script=specification.script,  # type: ignore[attr-defined]
            dependencies=specification.dependencies,  # type: ignore[attr-defined]
            summary=specification.summary,  # type: ignore[attr-defined]
            edition=args.edition,
        )
        text += "\n-- Preview only: no fresh kernel or Lean proof replay."
    _write_selected_output(args.output, text, force=args.force)
    print("Preview only: no fresh kernel or Lean proof replay.", file=sys.stderr)
    return 0


def _load_selected_specification(args: argparse.Namespace) -> tuple[object | None, object | None]:
    """Load Alpha only when explicitly requested; body-only rows fail closed."""

    if args.edition == "stable":
        return get(args.theorem), None

    from peano_lab.library import editions_v27

    if not editions_v27.EXPECTED_ALPHA_V27_COUNT:
        raise ValueError("Alpha v27 is not sealed for checked use")
    item = editions_v27.entry(args.theorem, edition="alpha")
    if item is None:
        return None, editions_v27
    if not item.checked_use:
        raise ValueError(
            f"Alpha theorem {args.theorem!r} has evidence {item.evidence.value!r}; "
            "a complete export requires independently checked-use authority"
        )
    return item.spec, editions_v27


def _repairable_strand_nodes(
    error: LeanVerificationError,
    package: object,
    root: Path,
) -> tuple[str, ...]:
    """Map bounded compiler diagnostics to authenticated dependency-order nodes."""

    candidates: set[str] = set()
    for match in _LEAN_ERROR_LOCATION.finditer(error.diagnostics):
        try:
            observed = Path(match.group("source")).expanduser().resolve()
        except (OSError, RuntimeError, ValueError):
            continue
        line_number = int(match.group("line"))
        for node in package.manifest["nodes"]:  # type: ignore[attr-defined]
            if (
                node.get("proof_status") == "readable_lean"
                and type(node.get("generated_relative_path")) is str
                and observed
                == _safe_package_destination(root, node["generated_relative_path"])
                and type(node.get("source_line_start")) is int
                and type(node.get("source_line_end")) is int
                and node["source_line_start"] <= line_number <= node["source_line_end"]
                and type(node.get("name")) is str
            ):
                candidates.add(node["name"])
                break
    return tuple(
        node["name"]
        for node in package.manifest["nodes"]  # type: ignore[attr-defined]
        if node.get("name") in candidates
    )


def _repairable_strand_node(
    error: LeanVerificationError,
    package: object,
    root: Path,
) -> str | None:
    """Retain the single-node diagnostic API for callers and focused audits."""

    candidates = _repairable_strand_nodes(error, package, root)
    return candidates[0] if candidates else None


def _summarize_failed_lean(error: LeanVerificationError) -> str:
    """Avoid exposing thousands of cascading errors from a rejected candidate."""

    summary = next(
        (line for line in error.diagnostics.splitlines() if _LEAN_ERROR_LOCATION.match(line)),
        "Lean rejected a generated proof candidate.",
    )
    encoded = summary.encode("utf-8")
    if len(encoded) > 512:
        summary = encoded[:500].decode("utf-8", errors="ignore") + " [truncated]"
    return summary


def _verify_strand_package(
    plan: object,
    package: object,
    root: Path,
    args: argparse.Namespace,
) -> object:
    """Compile once at a time, repairing genuine local Lean failures transparently."""

    from peano_lab.library.lean_proof_strand import build_proof_strand

    project = args.lean_project.expanduser().resolve()
    lake = _lake_binary(project, args.lake)
    deadline = time.monotonic() + args.max_verify_seconds
    repaired: set[str] = set()
    callback = _progress_callback(args)
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise ValueError(
                f"Lean proof-strand verification exceeded its "
                f"{args.max_verify_seconds}-second limit"
            )
        try:
            _verify_presentation_package(
                package,
                root,
                project,
                lake,
                max_memory_mib=args.max_memory_mib,
                max_verify_seconds=max(1, math.ceil(remaining)),
                emit_failed_diagnostics=False,
                progress=callback,
            )
            return package
        except LeanVerificationError as error:
            if args.strict_readable:
                print(_summarize_failed_lean(error), file=sys.stderr)
                raise
            candidates = tuple(
                name
                for name in _repairable_strand_nodes(error, package, root)
                if name not in repaired
            )
            if not candidates:
                print(_summarize_failed_lean(error), file=sys.stderr)
                raise
            allowance = args.max_proof_repairs - len(repaired)
            if allowance <= 0:
                raise ValueError(
                    "Lean proof strand exhausted its "
                    f"{args.max_proof_repairs}-attempt local certificate repair budget"
                ) from error
            selected = candidates[: min(4, allowance)]
            repaired.update(selected)
            _emit_cli_progress(
                args,
                stage="repair",
                completed=len(repaired),
                total=plan.node_count,  # type: ignore[attr-defined]
                theorem=selected[0],
                message="checking only compiler-rejected dependency-relative proof bodies",
            )
            labels = ", ".join(repr(name) for name in selected)
            print(
                f"Lean rejected readable candidate proof(s) for {labels}; "
                "retrying with independently checked dependency-relative bodies.",
                file=sys.stderr,
            )
            package = build_proof_strand(
                plan,
                max_steps=args.max_proof_steps,
                chunk_max_bytes=args.max_chunk_kib * 1024,
                include_axiom_audit=not args.no_axiom_audit,
                force_fallback_names=frozenset(repaired),
                progress=callback,
            )
            root = _write_strand_package(package, root, force=True)


def _write_live_output(
    args: argparse.Namespace,
    plan: object,
    package: object,
    *,
    deadline: float | None,
) -> tuple[object | None, str]:
    """Write and optionally check standalone source without replaying a proof."""

    if args.live_lean_output is None:
        return None, "not_requested"
    if package.manifest["fallback_node_count"]:  # type: ignore[attr-defined]
        print(
            "Lean Live unavailable: local checked certificate fallback requires the "
            "independently installed private Lean companion.",
            file=sys.stderr,
        )
        return None, "unavailable"
    from peano_lab.library.lean_proof_strand import build_live_export

    live = build_live_export(
        plan,  # type: ignore[arg-type]
        package,  # type: ignore[arg-type]
        max_source_bytes=args.max_live_source_kib * 1024,
        max_url_bytes=args.max_live_url_bytes,
    )
    requested = args.live_lean_output.expanduser()
    if requested.suffix != ".lean":
        raise ValueError("standalone Lean Live output must have an exact .lean extension")
    source = _checked_output_path(requested, force=args.force)
    receipt = _checked_output_path(source.with_suffix(".json"), force=args.force)
    if args.output is not None and source == args.output.expanduser().resolve():
        raise ValueError("standalone Lean Live output must differ from the strand module output")
    _atomic_write_text(source, live.source)
    local_verified = False
    if args.verify:
        if deadline is None:
            raise ValueError("standalone Lean verification requires the shared package deadline")
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise ValueError("the shared Lean verification deadline expired before standalone source")
        _emit_cli_progress(
            args,
            stage="compile",
            completed=0,
            total=1,
            module=str(source),
            message="independently checking standalone core Lean Live source",
        )
        project = args.lean_project.expanduser().resolve()
        _verify(
            source,
            project,
            _lake_binary(project, args.lake),
            max_memory_mib=args.max_memory_mib,
            max_verify_seconds=max(1, math.ceil(remaining)),
        )
        local_verified = True
        _emit_cli_progress(
            args,
            stage="compile",
            completed=1,
            total=1,
            module=str(source),
            message="standalone core Lean source compiled successfully",
        )
    manifest = {**live.manifest, "local_source_verified": local_verified}
    _atomic_write_text(receipt, _canonical_manifest(manifest))
    print(f"Standalone Lean Live source: {source}\nLean Live receipt: {receipt}", file=sys.stderr)
    if live.url is None:
        print(
            "Lean Live share URL unavailable: exact source exceeds the "
            f"{args.max_live_url_bytes}-byte URL bound; use the downloadable source.",
            file=sys.stderr,
        )
    else:
        if args.progress_json and live.url_bytes > MAX_PROGRESS_INLINE_URL_BYTES:
            print(
                f"Lean Live share URL: {live.url_bytes:,} bytes; "
                f"the exact authenticated URL is recorded in {receipt}.",
                file=sys.stderr,
            )
        else:
            print(f"Lean Live share URL: {live.url}", file=sys.stderr)
    return live, live.url_status


def _export_proof_strand(args: argparse.Namespace) -> int:
    """Generate a complete named constructive proof without closed-root replay."""

    from peano_lab.library.lean_proof_strand import (
        build_live_export,
        build_proof_strand,
        plan_proof_strand,
        preview_proof_strand,
    )

    if args.proof_bundle is not None:
        raise ValueError(
            "proof strands use authenticated named release dependencies, "
            "not externally supplied proof bundles"
        )
    if not 1 <= args.max_strand_nodes <= MAX_PACKAGE_PRESENTATIONS:
        raise ValueError("proof-strand node bound must be between 1 and 4096")
    if not 0 <= args.max_strand_edges <= 65_536:
        raise ValueError("proof-strand edge bound must be between 0 and 65536")
    if not 1 <= args.max_strand_depth <= 256:
        raise ValueError("proof-strand depth bound must be between 1 and 256")
    if not 1 <= args.max_proof_steps <= 65_536:
        raise ValueError("per-theorem proof-step bound must be between 1 and 65536")
    if not 0 <= args.max_proof_repairs <= 256:
        raise ValueError("proof-strand repair bound must be between 0 and 256")
    if not 8 <= args.max_chunk_kib <= 65_536:
        raise ValueError("proof-strand chunk bound must be between 8 and 65536 KiB")
    if not 128 <= args.max_live_url_bytes <= MAX_LIVE_URL_BYTES:
        raise ValueError(
            f"Lean Live URL bound must be between 128 and {MAX_LIVE_URL_BYTES} bytes"
        )
    if not 1 <= args.max_live_source_kib <= 65_536:
        raise ValueError("Lean Live source bound must be between 1 and 65536 KiB")

    if args.format == "outline":
        if args.verify:
            raise ValueError("a metadata-only proof outline cannot claim Lean verification")
        if args.package_dir is not None:
            raise ValueError("a metadata-only proof outline does not generate a Lean package")
        if args.strict_readable:
            raise ValueError("strict readability requires generating a proof strand")
        if args.live_lean_output is not None:
            raise ValueError("a metadata-only proof outline cannot generate Lean Live source")

    if args.format == "live":
        if args.package_dir is not None:
            raise ValueError(
                "standalone Lean Live source is one file; use --format strand "
                "with --live-lean-output to also retain its checked package"
            )
        if args.live_lean_output is not None:
            raise ValueError("use --output, not --live-lean-output, for direct Lean Live format")

    if args.output is not None and args.package_dir is not None:
        destination = _checked_output_path(args.output, force=args.force)
        requested_root = args.package_dir.expanduser().resolve()
        if destination == requested_root or requested_root in destination.parents:
            raise ValueError("selected proof-strand output must not be inside its Lean package")

    plan = plan_proof_strand(
        args.theorem,
        edition=args.edition,
        max_nodes=args.max_strand_nodes,
        max_edges=args.max_strand_edges,
        max_depth=args.max_strand_depth,
        progress=_progress_callback(args),
    )
    if args.format == "outline":
        _write_selected_output(args.output, preview_proof_strand(plan), force=args.force)
        print(
            "Proof outline only: no fresh Peano proof replay and no Lean compilation.",
            file=sys.stderr,
        )
        return 0

    package = build_proof_strand(
        plan,
        max_steps=args.max_proof_steps,
        chunk_max_bytes=args.max_chunk_kib * 1024,
        include_axiom_audit=not args.no_axiom_audit,
        strict_readable=args.strict_readable or args.format == "live",
        progress=_progress_callback(args),
    )
    if args.format == "live":
        live = build_live_export(
            plan,
            package,
            max_source_bytes=args.max_live_source_kib * 1024,
            max_url_bytes=args.max_live_url_bytes,
        )
        if args.output is None and live.source_bytes > MAX_STRAND_TERMINAL_BYTES:
            raise ValueError("standalone Lean Live source exceeds its safe terminal-output budget")
        if args.verify:
            with tempfile.TemporaryDirectory(prefix="peano-lean-live-") as directory:
                source = Path(directory) / "Standalone.lean"
                _atomic_write_text(source, live.source)
                _emit_cli_progress(
                    args,
                    stage="compile",
                    completed=0,
                    total=1,
                    module=str(source),
                )
                project = args.lean_project.expanduser().resolve()
                _verify(
                    source,
                    project,
                    _lake_binary(project, args.lake),
                    max_memory_mib=args.max_memory_mib,
                    max_verify_seconds=args.max_verify_seconds,
                )
                _emit_cli_progress(
                    args,
                    stage="compile",
                    completed=1,
                    total=1,
                    module=str(source),
                )
            print("Independent standalone Lean compilation: PASSED.", file=sys.stderr)
        _write_selected_output(args.output, live.source, force=args.force)
        if live.url is None:
            print(
                f"Lean Live share unavailable: exact URL exceeds {args.max_live_url_bytes} bytes.",
                file=sys.stderr,
            )
        else:
            print(f"Lean Live share URL: {live.url}", file=sys.stderr)
        _emit_cli_progress(
            args,
            stage="complete",
            completed=plan.node_count,
            total=plan.node_count,
            theorem=plan.root,
            live_url=live.url,
            share_encoding=live.manifest["share_encoding"],
            live_status=live.url_status,
            remote_compilation="not_run",
            local_source_verified=args.verify,
        )
        return 0

    fallback_count = package.manifest["fallback_node_count"]
    translated_count = package.manifest["translated_node_count"]
    if args.strict_readable and fallback_count:
        raise ValueError(
            "strict-readable strand rejected: "
            f"{fallback_count} of {plan.node_count} theorem(s) require "
            "explicit independently checked local certificate fallback"
        )
    if package.manifest["chunk_count"] and args.package_dir is None:
        raise ValueError(
            "a segmented proof strand requires --package-dir; "
            "its named prerequisite modules cannot be discarded or emitted as one file"
        )
    if (
        args.package_dir is None
        and args.output is None
        and len(package.code.encode("utf-8")) > MAX_STRAND_TERMINAL_BYTES
    ):
        raise ValueError(
            "proof strand exceeds its safe terminal-output budget; "
            "choose --package-dir or --output explicitly"
        )

    if args.package_dir is not None:
        root = _write_strand_package(package, args.package_dir, force=args.force)
        deadline = time.monotonic() + args.max_verify_seconds if args.verify else None
        if args.verify:
            package = _verify_strand_package(plan, package, root, args)
        live, live_status = _write_live_output(args, plan, package, deadline=deadline)
        fallback_count = package.manifest["fallback_node_count"]
        translated_count = package.manifest["translated_node_count"]
        print(
            f"Exported complete {args.edition} Peano proof strand "
            f"{args.theorem!r}: {plan.node_count} named theorem(s), "
            f"{plan.edge_count} prerequisite edge(s), "
            f"{translated_count} readable Lean proof(s), "
            f"{fallback_count} independently checked local fallback(s).\n"
            f"Package: {root}\nManifest: {root / 'manifest.json'}",
            file=sys.stderr,
        )
        if args.verify:
            print("Independent Lean compilation: PASSED.", file=sys.stderr)
        _emit_cli_progress(
            args,
            stage="complete",
            completed=plan.node_count,
            total=plan.node_count,
            theorem=plan.root,
            live_url=None if live is None else live.url,
            share_encoding=None if live is None else live.manifest["share_encoding"],
            live_status=live_status,
            remote_compilation="not_run",
            local_source_verified=bool(live is not None and args.verify),
        )
        if args.output is None:
            preview = package.preview.rstrip("\n")
            if args.verify:
                preview = preview.replace(
                    "Lean verification: NOT RUN",
                    "Lean verification: PASSED",
                )
            print(preview)
        else:
            _write_selected_output(args.output, package.code, force=args.force)
        return 0

    deadline = time.monotonic() + args.max_verify_seconds if args.verify else None
    if args.verify:
        with tempfile.TemporaryDirectory(prefix="peano-lean-proof-strand-") as directory:
            root = _write_strand_package(package, Path(directory), force=False)
            package = _verify_strand_package(plan, package, root, args)
        print("Independent Lean compilation: PASSED.", file=sys.stderr)
    live, live_status = _write_live_output(args, plan, package, deadline=deadline)
    _emit_cli_progress(
        args,
        stage="complete",
        completed=plan.node_count,
        total=plan.node_count,
        theorem=plan.root,
        live_url=None if live is None else live.url,
        share_encoding=None if live is None else live.manifest["share_encoding"],
        live_status=live_status,
        remote_compilation="not_run",
        local_source_verified=bool(live is not None and args.verify),
    )
    _write_selected_output(args.output, package.code, force=args.force)
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    previous_termination_handler = None
    if args.progress_json:
        previous_termination_handler = signal.getsignal(signal.SIGTERM)
        signal.signal(signal.SIGTERM, _cancel_active_verifier)
    try:
        if args.progress_json and args.format not in {"outline", "strand", "live"}:
            raise ValueError("structured progress is available only for proof-strand exports")
        if args.live_lean_output is not None and args.format != "strand":
            raise ValueError("supplemental Lean Live output requires --format strand")
        if args.progress_json:
            _emit_cli_progress(
                args,
                stage="plan",
                completed=0,
                total=0,
                theorem=args.theorem,
                message="loading the exact checked-use release inventory",
            )
        specification, alpha = _load_selected_specification(args)
        if specification is None and (args.proof_bundle is None or args.edition == "alpha"):
            label = "public" if args.edition == "stable" else "Alpha"
            print(f"Unknown {label} Peano theorem: {args.theorem!r}", file=sys.stderr)
            return 2
        if not 64 <= args.max_memory_mib <= 16_384:
            raise ValueError("Lean memory bound must be between 64 and 16384 MiB")
        if not 1 <= args.max_verify_seconds <= 3_600:
            raise ValueError("Lean verification timeout must be between 1 and 3600 seconds")

        if args.format in {"outline", "strand", "live"}:
            return _export_proof_strand(args)
        if args.strict_readable:
            raise ValueError("strict readability is available only for proof strands")

        if (
            args.format in {"pretty", "exact"}
            and args.package_dir is None
            and not args.verify
            and args.proof_bundle is None
            and specification is not None
        ):
            return _lightweight_preview(args, specification)

        bundle = None
        certificate = None
        if args.proof_bundle is None:
            assert specification is not None
            theorem = (
                replay(specification.name)
                if alpha is None
                else alpha.replay(specification.name, edition="alpha")
            )
            formula = theorem.formula
            certificate = theorem.certificate
            script = specification.script
            dependencies = specification.dependencies
            theorem_name = specification.name
            proof_description = f"{theorem.proof_nodes} proof nodes"
        else:
            source = args.proof_bundle.expanduser().resolve()
            if source.stat().st_size > DEFAULT_BUNDLE_LIMITS.max_payload_bytes:
                raise ValueError("proof bundle exceeds its reviewed canonical byte limit")
            bundle, formula = decode_proof_bundle(source.read_text(encoding="utf-8"))
            if specification is not None:
                if _closed_formula(specification.statement) != formula:
                    raise ValueError(
                        "proof-bundle target disagrees with the named public theorem"
                    )
                script = specification.script
                dependencies = specification.dependencies
                theorem_name = specification.name
            else:
                script = ()
                dependencies = ()
                theorem_name = args.theorem
            proof_description = f"{len(bundle.nodes)} independently checked bundle nodes"

        package_mode = args.format != "full" or args.package_dir is not None
        if package_mode:
            from peano_lab.library.lean_presentation import build_checked_presentation

            effective_edition = args.edition if specification is not None else "external-bundle"
            presentation = build_checked_presentation(
                theorem_name,
                formula,
                certificate,
                source_statement=None if specification is None else specification.statement,
                script=script,
                dependencies=dependencies,
                summary="" if specification is None else specification.summary,
                bundle=bundle,
                include_axiom_audit=not args.no_axiom_audit,
                edition=effective_edition,
            )
            selected = _selected_presentation_text(presentation, args.format)
            if args.output is not None:
                output = _checked_output_path(args.output, force=args.force)
                if args.package_dir is not None:
                    requested_root = args.package_dir.expanduser().resolve()
                    if output == requested_root or requested_root in output.parents:
                        raise ValueError(
                            "selected presentation output must not be inside its Lean package"
                        )
            if args.package_dir is not None:
                package_root = _write_presentation_package(
                    presentation, args.package_dir, force=args.force
                )
                if args.verify:
                    project = args.lean_project.expanduser().resolve()
                    _verify_presentation_package(
                        presentation,
                        package_root,
                        project,
                        _lake_binary(project, args.lake),
                        max_memory_mib=args.max_memory_mib,
                        max_verify_seconds=args.max_verify_seconds,
                    )
                print(
                    f"Exported checked Peano theorem {theorem_name!r} "
                    f"({proof_description}) as a reusable Lean package: {package_root}\n"
                    f"Manifest: {package_root / 'manifest.json'}",
                    file=sys.stderr,
                )
                if effective_edition == "external-bundle":
                    print(
                        "Release membership: external proof bundle only; "
                        "not a Stable or Alpha library admission.",
                        file=sys.stderr,
                    )
            elif args.verify:
                with tempfile.TemporaryDirectory(prefix="peano-lean-package-") as directory:
                    package_root = _write_presentation_package(
                        presentation, Path(directory), force=False
                    )
                    project = args.lean_project.expanduser().resolve()
                    _verify_presentation_package(
                        presentation,
                        package_root,
                        project,
                        _lake_binary(project, args.lake),
                        max_memory_mib=args.max_memory_mib,
                        max_verify_seconds=args.max_verify_seconds,
                    )

            _write_selected_output(args.output, selected, force=args.force)
            return 0

        if bundle is None:
            exported = export_checked_theorem(
                theorem_name,
                formula,
                certificate,
                script,
                dependencies=dependencies,
                include_axiom_audit=not args.no_axiom_audit,
            )
        else:
            exported = export_checked_bundle_theorem(
                theorem_name,
                bundle,
                formula,
                script,
                dependencies=dependencies,
                include_axiom_audit=not args.no_axiom_audit,
            )

        if args.output is not None:
            output = _checked_output_path(args.output, force=args.force)
            _atomic_write_text(output, exported.code.rstrip("\n") + "\n")
            if args.verify:
                project = args.lean_project.expanduser().resolve()
                _verify(
                    output,
                    project,
                    _lake_binary(project, args.lake),
                    max_memory_mib=args.max_memory_mib,
                    max_verify_seconds=args.max_verify_seconds,
                )
            print(
                f"Exported checked Peano theorem {theorem_name!r} "
                f"({proof_description}) to {output}",
                file=sys.stderr,
            )
            return 0

        if args.verify:
            project = args.lean_project.expanduser().resolve()
            with tempfile.TemporaryDirectory(prefix="peano-lean-proof-") as directory:
                module = Path(directory) / "Exported.lean"
                module.write_text(exported.code + "\n", encoding="utf-8")
                _verify(
                    module,
                    project,
                    _lake_binary(project, args.lake),
                    max_memory_mib=args.max_memory_mib,
                    max_verify_seconds=args.max_verify_seconds,
                )
        print(exported.code)
        return 0
    except (OSError, RuntimeError, ValueError) as error:
        print(f"Peano-to-Lean conversion failed: {error}", file=sys.stderr)
        return 1
    finally:
        if previous_termination_handler is not None:
            signal.signal(signal.SIGTERM, previous_termination_handler)


if __name__ == "__main__":
    raise SystemExit(main())
