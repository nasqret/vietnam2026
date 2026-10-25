"""Fresh, source-bound Lean reference builds for native certificate conformance.

The reference is a separate checked implementation, never a Python mirror or
an imported prebuilt companion. Compilation uses an explicitly selected local
Lean executable; this module neither downloads toolchains nor changes them.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

from .frontier import digest, read_bytes
from .review_runtime import (
    ProcessLimits, ReviewRuntimeError, hash_file, run_bounded, validate_process_record,
)
from .review_sources import ReviewSourceError, bounded_git


SCHEMA = "peano-hydra-lean-reference-review-v1"
RESULTS_SCHEMA = "peano-hydra-reference-conformance-results-v1"
MODULES = (
    "PeanoLab/Syntax.lean", "PeanoLab/Substitution.lean",
    "PeanoLab/Semantics.lean", "PeanoLab/Derivation.lean",
    "PeanoLab/Checker.lean", "PeanoLab/Soundness.lean",
    "PeanoLab/Codec.lean", "PeanoLab/Verify.lean",
)
EXTERNAL_IMPORTS = frozenset({"Lean.Data.Json", "Lean.Elab.Tactic.Omega"})
AUDIT_DECLARATIONS = (
    "PeanoLab.check_derives", "PeanoLab.checkClosed_sound",
    "PeanoLab.Artifact.check_derives", "PeanoLab.Artifact.check_sound",
)
AUDIT_SOURCE = "import PeanoLab.Codec\n\n" + "\n".join(
    f"#print axioms {name}" for name in AUDIT_DECLARATIONS
) + "\n"
ALLOWED_AXIOMS = frozenset({"propext", "Classical.choice", "Quot.sound"})
BUILD_LIMITS = ProcessLimits(wall_seconds=120, cpu_seconds=90)
CHECK_LIMITS = ProcessLimits(wall_seconds=45, cpu_seconds=30)
MAX_SOURCE_BYTES = 2 * 1024**2
MAX_CASE_BYTES = 256 * 1024
MAX_CASES = 8192
MAX_SUITE_BYTES = 32 * 1024**2
BATCH_SIZE = 64
CLAIM_BOUNDARY = "certificate acceptance and Nat soundness; not HA theoremhood decidability or a sealed H0 review"
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")


class ReferenceReviewError(ValueError):
    """Reference identity, fresh compilation, or exact output did not verify."""


def _keys(value: object, fields: set[str], label: str) -> None:
    if type(value) is not dict or set(value) != fields:
        raise ReferenceReviewError(f"{label} has missing or unknown fields")


def _descriptor(value: object, label: str, *, maximum: int = 512 * 1024**2,
                extra_fields: tuple[str, ...] = ()) -> None:
    _keys(value, {"bytes", "sha256", *extra_fields}, label)
    if (type(value["bytes"]) is not int or not 1 <= value["bytes"] <= maximum
        or type(value["sha256"]) is not str or _DIGEST.fullmatch(value["sha256"]) is None):
        raise ReferenceReviewError(f"{label} hash descriptor is malformed")


def _sealed_digest(value: dict[str, object], field: str, label: str) -> None:
    unsigned = dict(value)
    claimed = unsigned.pop(field, None)
    if type(claimed) is not str or _DIGEST.fullmatch(claimed) is None:
        raise ReferenceReviewError(f"{label} digest is malformed")
    try:
        actual = digest(unsigned)
    except (TypeError, ValueError, RecursionError, OverflowError) as error:
        raise ReferenceReviewError(f"{label} is not bounded JSON evidence") from error
    if claimed != actual:
        raise ReferenceReviewError(f"{label} digest differs")


def _absolute_path(value: object, label: str) -> Path:
    if type(value) is not str or not value or len(value) > 16384 or any(ord(c) < 32 for c in value):
        raise ReferenceReviewError(f"{label} is not one canonical absolute path")
    path = Path(value)
    if not path.is_absolute() or str(path) != value or ".." in path.parts:
        raise ReferenceReviewError(f"{label} is not one canonical absolute path")
    return path


def _fixed_limits(value: object, expected: ProcessLimits, label: str) -> None:
    fields = expected.to_dict()
    _keys(value, set(fields), label)
    if any(type(value[name]) is not int or value[name] != bound for name, bound in fields.items()):
        raise ReferenceReviewError(f"{label} differs from the exact resource contract")


def _process(record: dict[str, object], *, command: tuple[str, ...], limits: ProcessLimits,
             success_codes: tuple[int, ...], extra_fields: tuple[str, ...] = ()) -> None:
    try:
        validate_process_record(record, command=command, limits=limits,
                                success_codes=success_codes, extra_fields=extra_fields)
    except ReviewRuntimeError as error:
        raise ReferenceReviewError(f"reference process receipt is invalid: {error}") from error


def _git(project: Path, *arguments: str) -> str:
    try:
        return bounded_git(project, *arguments, maximum=4 * 1024**2).decode("utf-8").strip()
    except (ReviewSourceError, UnicodeError) as error:
        raise ReferenceReviewError("bounded reference Git metadata is unavailable") from error


def _source(path: Path) -> bytes:
    data = read_bytes(path, limit=MAX_SOURCE_BYTES)
    text = data.decode("utf-8")
    # This is an additional tripwire, not a proof of safety. Fresh Lean checks
    # and the complete axiom audit remain required before accepting a build.
    if re.search(r"\b(sorry|sorryAx|admit|unsafe)\b|Lean\.trustCompiler|^\s*axiom\s", text, re.MULTILINE):
        raise ReferenceReviewError(f"reference contains an unreviewed trust shortcut: {path.name}")
    return data


def _compiler_version(executable: Path) -> str:
    environment = {key: value for key, value in os.environ.items()
                   if not key.startswith(("LD_", "DYLD_"))}
    for name in ("LEAN_PATH", "LEAN_SRC_PATH", "LEAN_SYSROOT", "LEAN_OPTS"):
        environment.pop(name, None)
    try:
        output = subprocess.run([str(executable), "--version"], check=True,
                                capture_output=True, text=True, timeout=10, env=environment).stdout
    except (OSError, subprocess.SubprocessError, UnicodeError) as error:
        raise ReferenceReviewError("selected local Lean compiler version is unavailable") from error
    if type(output) is not str or len(output) > 1024:
        raise ReferenceReviewError("local compiler did not identify itself as Lean")
    version = output.strip()
    if re.fullmatch(r"Lean \(version ([^, )\r\n]{1,100})[^\r\n]{0,400}\)", version) is None:
        raise ReferenceReviewError("local compiler did not identify itself as Lean")
    return version


def _validate_current_toolchain(identity: dict[str, object]) -> Path:
    executable = Path(identity["compiler"]["path"])
    inputs = ((executable, identity["compiler"]),
              (executable.parent.parent / identity["runtime_library"]["relative_to_toolchain"], identity["runtime_library"]))
    # Check bytes before executing even --version, and again afterwards so a
    # persistent change during the probe cannot publish a valid live identity.
    for before_probe in (True, False):
        for path, record in inputs:
            if hash_file(path) != {key: record[key] for key in ("bytes", "sha256")}:
                raise ReferenceReviewError("reference compiler/runtime changed from its recorded identity")
        if before_probe and _compiler_version(executable) != identity["compiler_version"]:
            raise ReferenceReviewError("selected Lean compiler version differs from its recorded identity")
    return executable


def inspect_reference(project: Path, lean_binary: Path) -> dict[str, object]:
    """Read sources and local compiler identity; no source writes or compilation."""
    project = project.resolve(strict=True)
    executable = lean_binary.resolve(strict=True)
    if executable.name != "lean":
        raise ReferenceReviewError("select the actual local Lean executable, not an elan shim")
    version = _compiler_version(executable)
    files = {}
    available = set()
    for relative in MODULES:
        data = _source(project / relative)
        imports = []
        for line in data.decode("utf-8").splitlines():
            if re.match(r"^\s*import(?:\s|$)", line):
                match = re.fullmatch(r"import ([A-Za-z0-9_.]+)\s*", line)
                if match is None:
                    raise ReferenceReviewError(f"reference import is not one canonical module: {relative}")
                imports.append(match.group(1))
        if any(name not in available and name not in EXTERNAL_IMPORTS for name in imports):
            raise ReferenceReviewError(f"reference has an unexpected or unordered import: {relative}")
        files[relative] = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
        available.add(relative.removesuffix(".lean").replace("/", "."))
    pinned = read_bytes(project / "lean-toolchain", limit=4096).decode("utf-8").strip()
    shared_name = "libleanshared.dylib" if executable.parent.parent.joinpath("lib/lean/libleanshared.dylib").is_file() else "libleanshared.so"
    shared = executable.parent.parent / "lib" / "lean" / shared_name
    if not shared.is_file():
        raise ReferenceReviewError("local Lean runtime library is missing")
    record = {
        "schema": SCHEMA, "project_git_commit": _git(project, "rev-parse", "HEAD"),
        "project_git_dirty": bool(_git(project, "status", "--porcelain", "--untracked-files=all")),
        "project_toolchain_pin": pinned, "compiler_version": version,
        "compiler": {"path": str(executable), **hash_file(executable)},
        "runtime_library": {"relative_to_toolchain": f"lib/lean/{shared_name}", **hash_file(shared)},
        "matches_project_toolchain_pin": (
            pinned.removeprefix("leanprover/lean4:").removeprefix("v")
            == re.search(r"version ([^, )]+)", version).group(1)
        ),
        "files": files, "source_root_sha256": digest(files),
        "audit_source_sha256": hashlib.sha256(AUDIT_SOURCE.encode()).hexdigest(),
        "fresh_build_required": True, "prebuilt_companion_imports_allowed": False,
        "allowed_axioms": sorted(ALLOWED_AXIOMS), "audit_declarations": list(AUDIT_DECLARATIONS),
        "build_limits": BUILD_LIMITS.to_dict(), "check_limits": CHECK_LIMITS.to_dict(),
        "lean_options": ["-j1", "-M768"], "batch_size": BATCH_SIZE,
        "claim_boundary": CLAIM_BOUNDARY,
        "h0_complete": False, "research_claim_eligible": False,
    }
    record["reference_sha256"] = digest(record)
    return record


def validate_reference_identity(record: dict[str, object]) -> None:
    fields = {
        "schema", "project_git_commit", "project_git_dirty", "project_toolchain_pin",
        "compiler_version", "compiler", "runtime_library", "matches_project_toolchain_pin",
        "files", "source_root_sha256", "audit_source_sha256", "fresh_build_required",
        "prebuilt_companion_imports_allowed", "allowed_axioms", "audit_declarations",
        "build_limits", "check_limits", "lean_options", "batch_size", "claim_boundary",
        "h0_complete", "research_claim_eligible", "reference_sha256",
    }
    _keys(record, fields, "reference identity")
    _descriptor(record["compiler"], "reference compiler", extra_fields=("path",))
    _descriptor(record["runtime_library"], "reference runtime", extra_fields=("relative_to_toolchain",))
    executable = _absolute_path(record["compiler"]["path"], "reference compiler")
    if (executable.name != "lean"
        or type(record["runtime_library"]["relative_to_toolchain"]) is not str
        or record["runtime_library"]["relative_to_toolchain"] not in {
            "lib/lean/libleanshared.dylib", "lib/lean/libleanshared.so"}
        or type(record["project_git_dirty"]) is not bool
        or type(record["project_git_commit"]) is not str
        or re.fullmatch(r"[0-9a-f]{40}", record["project_git_commit"]) is None
        or type(record["compiler_version"]) is not str
        or re.fullmatch(r"Lean \(version ([^, )\r\n]{1,100})[^\r\n]{0,400}\)", record["compiler_version"]) is None
        or type(record["project_toolchain_pin"]) is not str
        or len(record["project_toolchain_pin"]) > 256
        or re.fullmatch(r"leanprover/lean4:v[0-9]+\.[0-9]+\.[0-9]+(?:-[a-z0-9.]+)?", record["project_toolchain_pin"]) is None):
        raise ReferenceReviewError("reference compiler/source identity is malformed")
    match_pin = (record["project_toolchain_pin"].removeprefix("leanprover/lean4:").removeprefix("v")
                 == re.search(r"version ([^, )]+)", record["compiler_version"]).group(1))
    if type(record["matches_project_toolchain_pin"]) is not bool or record["matches_project_toolchain_pin"] != match_pin:
        raise ReferenceReviewError("reference compiler pin claim differs")
    _keys(record["files"], set(MODULES), "reference source inventory")
    for relative, item in record["files"].items():
        _descriptor(item, f"reference source {relative}", maximum=MAX_SOURCE_BYTES)
    _fixed_limits(record["build_limits"], BUILD_LIMITS, "reference build limits")
    _fixed_limits(record["check_limits"], CHECK_LIMITS, "reference check limits")
    if (record["schema"] != SCHEMA
        or record["source_root_sha256"] != digest(record["files"])
        or record["audit_source_sha256"] != hashlib.sha256(AUDIT_SOURCE.encode()).hexdigest()
        or type(record["audit_declarations"]) is not list or record["audit_declarations"] != list(AUDIT_DECLARATIONS)
        or type(record["allowed_axioms"]) is not list or record["allowed_axioms"] != sorted(ALLOWED_AXIOMS)
        or type(record["batch_size"]) is not int or record["batch_size"] != BATCH_SIZE
        or type(record["lean_options"]) is not list or record["lean_options"] != ["-j1", "-M768"]
        or record["claim_boundary"] != CLAIM_BOUNDARY
        or record["h0_complete"] is not False or record["research_claim_eligible"] is not False
        or record["fresh_build_required"] is not True
        or record["prebuilt_companion_imports_allowed"] is not False):
        raise ReferenceReviewError("reference contract changed")
    _sealed_digest(record, "reference_sha256", "reference identity")


def _historical_blob(project: Path, commit: str, relative: str, *, maximum: int) -> bytes:
    """Read only a size-checked historical blob, never a checkout or a filter."""
    spec = f"{commit}:{relative}"
    if _git(project, "cat-file", "-t", spec) != "blob":
        raise ReferenceReviewError(f"reference historical input is not a Git blob: {relative}")
    size_text = _git(project, "cat-file", "-s", spec)
    if re.fullmatch(r"[0-9]{1,12}", size_text) is None or not 1 <= int(size_text) <= maximum:
        raise ReferenceReviewError(f"reference historical input exceeds its reservation: {relative}")
    try:
        data = bounded_git(project, "cat-file", "blob", spec, maximum=maximum)
    except ReviewSourceError as error:
        raise ReferenceReviewError(f"bounded reference historical Git blob is unavailable: {relative}") from error
    if type(data) is not bytes or len(data) != int(size_text):
        raise ReferenceReviewError(f"reference historical blob size changed: {relative}")
    return data


def validate_reference_provenance(project: Path, identity: dict[str, object]) -> None:
    """Bind a saved identity to committed Git blobs, independently of current HEAD.

    This is an origin check, not execution attestation or a claim that arbitrary
    historical source is safe. Fresh compilation and axiom auditing remain
    required. No saved compiler/worker command is executed here.
    """
    validate_reference_identity(identity)
    if identity["project_git_dirty"] is not False:
        raise ReferenceReviewError("executed reference plans require a clean recorded companion commit")
    try:
        project = project.resolve(strict=True)
        commit = identity["project_git_commit"]
        if _git(project, "rev-parse", "--verify", f"{commit}^{{commit}}") != commit:
            raise ReferenceReviewError("reference historical commit does not match the recorded identity")
        for relative in MODULES:
            data = _historical_blob(project, commit, relative, maximum=MAX_SOURCE_BYTES)
            if {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()} != identity["files"][relative]:
                raise ReferenceReviewError(f"reference historical source differs: {relative}")
        pin = _historical_blob(project, commit, "lean-toolchain", maximum=4096)
        expected = identity["project_toolchain_pin"].encode("utf-8")
        if pin not in (expected, expected + b"\n"):
            raise ReferenceReviewError("reference historical toolchain pin differs from its recorded claim")
    except (OSError, subprocess.SubprocessError, UnicodeError) as error:
        raise ReferenceReviewError(f"reference historical Git provenance is unavailable: {error}") from error


def stage_reference(project: Path, destination: Path, identity: dict[str, object]) -> None:
    validate_reference_identity(identity)
    if destination.exists() or destination.is_symlink():
        raise ReferenceReviewError("fresh reference directory required")
    destination = destination.resolve()
    destination.mkdir(parents=True, mode=0o700)
    for relative in MODULES:
        data = _source(project / relative)
        if {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()} != identity["files"][relative]:
            raise ReferenceReviewError("reference source changed after planning")
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(data)
    with (destination / "HydraAxiomAudit.lean").open("xb") as stream:
        stream.write(AUDIT_SOURCE.encode())


def parse_axiom_audit(output: str) -> dict[str, list[str]]:
    entries = {}
    pattern = r"'([^']+)'\s+(?:depends on axioms:\s*\[([^\]]*)\]|does not depend on any axioms)"
    cursor = 0
    for match in re.finditer(pattern, output):
        if output[cursor:match.start()].strip():
            raise ReferenceReviewError("unexpected output in the reference axiom audit")
        cursor = match.end()
        name, axioms = match.groups()
        if name in entries or name not in AUDIT_DECLARATIONS:
            raise ReferenceReviewError("unexpected or duplicate axiom-audit declaration")
        values = [] if axioms is None else [value.strip() for value in axioms.split(",") if value.strip()]
        if not set(values) <= ALLOWED_AXIOMS or len(values) != len(set(values)):
            raise ReferenceReviewError("reference axiom footprint contains an unreviewed axiom")
        entries[name] = sorted(values)
    if set(entries) != set(AUDIT_DECLARATIONS) or output[cursor:].strip():
        raise ReferenceReviewError("incomplete reference axiom audit")
    if "sorryAx" in output or "Lean.trustCompiler" in output or re.search(r"\berror\b", output, re.IGNORECASE):
        raise ReferenceReviewError("reference axiom audit contains errors or trust shortcuts")
    return entries


def _compiled_inventory(destination: Path) -> dict[str, object]:
    allowed_stems = {str(Path(name).with_suffix("")) for name in MODULES}
    inventory = {}
    for path in sorted(destination.rglob("*")):
        if not path.is_file() and not path.is_symlink():
            continue
        relative = path.relative_to(destination).as_posix()
        if relative.endswith(".lean") or relative.startswith("cases/"):
            continue
        stem, separator, suffix = relative.partition(".olean")
        if not separator or stem not in allowed_stems or suffix not in {"", ".private", ".server"}:
            raise ReferenceReviewError(f"unreviewed compiled reference input: {relative}")
        inventory[relative] = hash_file(path)
    required = {str(Path(name).with_suffix(".olean")) for name in MODULES}
    if not required <= set(inventory) or len(inventory) > 3 * len(MODULES):
        raise ReferenceReviewError("compiled reference inventory is incomplete")
    return inventory


def _validate_compiled_inventory(inventory: object) -> None:
    required = {str(Path(name).with_suffix(".olean")) for name in MODULES}
    allowed = required | {name + suffix for name in required for suffix in (".private", ".server")}
    if (type(inventory) is not dict or not len(required) <= len(inventory) <= len(allowed)
        or not required <= set(inventory) <= allowed):
        raise ReferenceReviewError("compiled reference inventory is incomplete or has unreviewed paths")
    for name, descriptor in inventory.items():
        _descriptor(descriptor, f"compiled reference {name}")


def validate_build_receipt(
    identity: dict[str, object], build: dict[str, object], *, build_directory: Path | None = None,
) -> None:
    """Check saved build metadata without reading or executing its recorded paths.

    All compile commands must name one canonical absolute staging directory.
    Omit ``build_directory`` when an archive has moved: the historical root is
    inferred lexically, not resolved against the current filesystem. This is
    receipt consistency, not hardware attestation that the processes ran.
    """
    validate_reference_identity(identity)
    fields = {"schema", "status", "reference_sha256", "fresh_source_build", "compile_rows",
              "axiom_audit", "axiom_footprint", "h0_complete", "research_claim_eligible",
              "compiled_files", "compiled_root_sha256", "build_sha256"}
    _keys(build, fields, "reference build receipt")
    _validate_compiled_inventory(build["compiled_files"])
    if (build["schema"] != SCHEMA or build["status"] != "built-and-audited" or build["fresh_source_build"] is not True
        or build["h0_complete"] is not False or build["research_claim_eligible"] is not False
        or build["reference_sha256"] != identity["reference_sha256"]
        or build["compiled_root_sha256"] != digest(build["compiled_files"])):
        raise ReferenceReviewError("reference build lost its exact fresh-build contract")
    if type(build["compile_rows"]) is not list or len(build["compile_rows"]) != len(MODULES):
        raise ReferenceReviewError("reference build lacks all eight ordered compile receipts")
    first = build["compile_rows"][0]
    if type(first) is not dict or type(first.get("command")) is not list or len(first["command"]) != 6:
        raise ReferenceReviewError("reference build cannot identify its exact staging directory")
    first_output = _absolute_path(first["command"][4], "reference compiled output")
    first_relative = Path(MODULES[0]).with_suffix(".olean")
    suffix_length = len(first_relative.parts)
    if first_output.parts[-suffix_length:] != first_relative.parts:
        raise ReferenceReviewError("reference first compiled output does not match its module")
    destination = first_output.parents[suffix_length - 1]
    if destination == Path(destination.anchor):
        raise ReferenceReviewError("reference staging directory may not be a filesystem root")
    if build_directory is not None:
        if not isinstance(build_directory, Path):
            raise ReferenceReviewError("expected an explicit absolute build-directory Path")
        if destination != _absolute_path(str(build_directory), "reference build directory"):
            raise ReferenceReviewError("reference build receipt names a different staging directory")
    executable_text = identity["compiler"]["path"]
    for relative, row in zip(MODULES, build["compile_rows"]):
        output = str(Path(relative).with_suffix(".olean"))
        _process(row, command=(executable_text, "-j1", "-M768", "-o", str(destination / output), relative),
                 limits=BUILD_LIMITS, success_codes=(0,), extra_fields=("module", "compiled_olean"))
        _descriptor(row["compiled_olean"], "compiled module receipt")
        if row["module"] != relative or row["compiled_olean"] != build["compiled_files"][output]:
            raise ReferenceReviewError("reference module/output identity differs from its compile receipt")
    _process(build["axiom_audit"], command=(executable_text, "-j1", "-M768", "HydraAxiomAudit.lean"),
             limits=BUILD_LIMITS, success_codes=(0,))
    _keys(build["axiom_footprint"], set(AUDIT_DECLARATIONS), "reference axiom footprint")
    for values in build["axiom_footprint"].values():
        if (type(values) is not list or len(values) > len(ALLOWED_AXIOMS)
            or any(type(value) is not str or value not in ALLOWED_AXIOMS for value in values)):
            raise ReferenceReviewError("reference axiom footprint is malformed")
    if parse_axiom_audit(build["axiom_audit"]["stdout"] + build["axiom_audit"]["stderr"]) != build["axiom_footprint"]:
        raise ReferenceReviewError("reference build lost its exact axiom footprint")
    _sealed_digest(build, "build_sha256", "reference build receipt")


def validate_build(destination: Path, identity: dict[str, object], build: dict[str, object]) -> None:
    """Validate the receipt and the current on-disk compiler, source and outputs."""
    destination = destination.resolve(strict=True)
    validate_build_receipt(identity, build, build_directory=destination)
    if build["compiled_files"] != _compiled_inventory(destination):
        raise ReferenceReviewError("reference compiled bytes changed after their fresh build")
    _validate_current_toolchain(identity)
    for relative in MODULES:
        if hash_file(destination / relative) != identity["files"][relative]:
            raise ReferenceReviewError("reference source changed after compilation")
    if read_bytes(destination / "HydraAxiomAudit.lean", limit=MAX_SOURCE_BYTES) != AUDIT_SOURCE.encode():
        raise ReferenceReviewError("reference axiom audit source changed after compilation")


def build_reference(destination: Path, identity: dict[str, object], *, progress=None) -> dict[str, object]:
    validate_reference_identity(identity)
    destination = destination.resolve(strict=True)
    expected_stage = set(MODULES) | {"HydraAxiomAudit.lean"}
    actual_stage = {path.relative_to(destination).as_posix() for path in destination.rglob("*")
                    if path.is_file() or path.is_symlink()}
    if actual_stage != expected_stage:
        raise ReferenceReviewError("reference build requires only pristine staged source files, with no prebuilt sidecars")
    executable = _validate_current_toolchain(identity)
    rows = []
    for relative in MODULES:
        target = destination / relative
        if hash_file(target) != identity["files"][relative]:
            raise ReferenceReviewError("staged source differs from the planned reference")
        output = target.with_suffix(".olean")
        if output.exists() or output.is_symlink():
            raise ReferenceReviewError("reference may not reuse prebuilt modules")
        command = (str(executable), "-j1", "-M768", "-o", str(output), relative)
        row = run_bounded(command, cwd=destination, limits=BUILD_LIMITS, lean_path=destination)
        row["module"] = relative
        rows.append(row)
        if progress:
            progress("reference_compile", len(rows), len(MODULES) + 1, relative)
        if row["reason"] != "exited" or row["returncode"] != 0 or not output.is_file():
            raise ReferenceReviewError(f"fresh Lean reference compilation failed: {relative}: {row['reason']} {row['stderr']} {row['stdout']}")
        row["compiled_olean"] = hash_file(output)
    audit_path = destination / "HydraAxiomAudit.lean"
    if read_bytes(audit_path, limit=MAX_SOURCE_BYTES) != AUDIT_SOURCE.encode():
        raise ReferenceReviewError("staged axiom audit changed")
    audit = run_bounded((str(executable), "-j1", "-M768", audit_path.name),
                        cwd=destination, limits=BUILD_LIMITS, lean_path=destination)
    if audit["reason"] != "exited" or audit["returncode"] != 0:
        raise ReferenceReviewError("fresh Lean axiom audit failed: " + audit["stdout"] + audit["stderr"])
    footprint = parse_axiom_audit(audit["stdout"] + audit["stderr"])
    if progress:
        progress("reference_compile", len(MODULES) + 1, len(MODULES) + 1, "axiom audit")
    result = {"schema": SCHEMA, "status": "built-and-audited", "reference_sha256": identity["reference_sha256"],
              "fresh_source_build": True, "compile_rows": rows, "axiom_audit": audit,
              "axiom_footprint": footprint, "h0_complete": False, "research_claim_eligible": False}
    result["compiled_files"] = _compiled_inventory(destination)
    result["compiled_root_sha256"] = digest(result["compiled_files"])
    result["build_sha256"] = digest(result)
    validate_build(destination, identity, result)
    return result


def parse_verifier_output(result: dict[str, object], expected_paths: tuple[str, ...]) -> dict[str, str]:
    """Require exactly one reference decision per exact path, with no status inference."""
    if (type(result) is not dict or result.get("reason") != "exited"
        or type(result.get("returncode")) is not int
        or any(type(result.get(stream)) is not str or len(result[stream]) > CHECK_LIMITS.output_bytes
               for stream in ("stdout", "stderr"))):
        raise ReferenceReviewError("reference worker exceeded a declared resource bound")
    if (type(expected_paths) is not tuple or not 1 <= len(expected_paths) <= BATCH_SIZE
        or any(type(path) is not str or not path for path in expected_paths)
        or len(set(expected_paths)) != len(expected_paths)):
        raise ReferenceReviewError("reference decisions require one exact bounded path batch")
    decisions = {}
    for line in (result["stdout"] + result["stderr"]).splitlines():
        fields = line.split("\t")
        if (len(fields) < 3 or fields[0] not in {"ACCEPT", "REJECT", "DECODE_ERROR"}
            or fields[1] not in expected_paths or fields[1] in decisions):
            raise ReferenceReviewError("unexpected, missing, or duplicate verifier output")
        if fields[0] in {"ACCEPT", "REJECT"} and (len(fields) != 3 or not re.fullmatch(r"fuel=(?:0|[1-9][0-9]*)", fields[2])):
            raise ReferenceReviewError("malformed reference acceptance/rejection receipt")
        if fields[0] == "DECODE_ERROR" and not "\t".join(fields[2:]).strip():
            raise ReferenceReviewError("reference decode failure lacks its explicit diagnostic")
        decisions[fields[1]] = fields[0]
    if set(decisions) != set(expected_paths):
        raise ReferenceReviewError("reference did not return every requested case")
    expected_code = max({"ACCEPT": 0, "REJECT": 1, "DECODE_ERROR": 2}[value] for value in decisions.values())
    if result["returncode"] != expected_code:
        raise ReferenceReviewError("reference exit code disagrees with its exact decisions")
    return decisions


def _validate_case_inputs(cases: tuple) -> None:
    from .conformance import ConformanceCase

    if type(cases) is not tuple or not 1 <= len(cases) <= MAX_CASES:
        raise ReferenceReviewError("conformance set must be one bounded nonempty tuple")
    total = 0
    identifiers = set()
    for case in cases:
        if (type(case) is not ConformanceCase or type(case.case_id) is not str
            or re.fullmatch(r"[a-z][a-z0-9_-]{0,95}", case.case_id) is None
            or case.case_id in identifiers
            or type(case.expected_lean) is not str or case.expected_lean not in {"ACCEPT", "REJECT", "DECODE_ERROR"}
            or type(case.artifact) is not bytes or not 1 <= len(case.artifact) <= MAX_CASE_BYTES):
            raise ReferenceReviewError("conformance inputs lost their exact bounded case identity")
        identifiers.add(case.case_id)
        total += len(case.artifact)
        if total > MAX_SUITE_BYTES:
            raise ReferenceReviewError("conformance set exceeds its whole-run reservation")


def _validate_reported_fuel(row: dict[str, object], cases: tuple, paths: tuple[str, ...]) -> None:
    """Bind reported fuel to the original inert wire envelope, not a guessed default."""
    by_path = dict(zip(paths, cases))
    for line in (row["stdout"] + row["stderr"]).splitlines():
        fields = line.split("\t")
        if fields[0] not in {"ACCEPT", "REJECT"}:
            continue
        try:
            envelope = json.loads(by_path[fields[1]].artifact)
        except (UnicodeError, ValueError, RecursionError) as error:
            raise ReferenceReviewError("reference claims to check an artifact without a readable fuel envelope") from error
        if (type(envelope) is not list or len(envelope) != 4 or type(envelope[1]) is not int
            or envelope[1] < 0 or fields[2] != f"fuel={envelope[1]}"):
            raise ReferenceReviewError("reference reported fuel differs from the original artifact")


def validate_reference_results(identity: dict[str, object], result: dict[str, object], cases: tuple) -> None:
    """Validate a saved result against original authored cases without executing Lean.

    A valid ``failed`` result remains a failure. Recomputing a digest or an
    aggregate count cannot turn a different observed decision into a match.
    The caller must separately validate its fresh-build receipt and provenance.
    """
    validate_reference_identity(identity)
    _validate_case_inputs(cases)
    fields = {"schema", "reference_sha256", "status", "cases", "worker_rows", "mismatches",
              "case_count", "model_calls", "solver_calls", "negative_theorem_claims",
              "h0_complete", "research_claim_eligible", "results_sha256"}
    _keys(result, fields, "reference conformance results")
    if (result["schema"] != RESULTS_SCHEMA or result["reference_sha256"] != identity["reference_sha256"]
        or type(result["case_count"]) is not int or result["case_count"] != len(cases)
        or type(result["model_calls"]) is not int or result["model_calls"] != 0
        or type(result["solver_calls"]) is not int or result["solver_calls"] != 0
        or result["negative_theorem_claims"] is not False or result["h0_complete"] is not False
        or result["research_claim_eligible"] is not False
        or type(result["cases"]) is not list or len(result["cases"]) != len(cases)
        or type(result["worker_rows"]) is not list
        or len(result["worker_rows"]) != (len(cases) + BATCH_SIZE - 1) // BATCH_SIZE):
        raise ReferenceReviewError("reference results changed their exact schema, counts or claim boundary")
    outcomes = []
    for number, start in enumerate(range(0, len(cases), BATCH_SIZE)):
        selected = cases[start:start + BATCH_SIZE]
        paths = tuple(f"cases/case-{index:05d}.json" for index in range(start, start + len(selected)))
        row = result["worker_rows"][number]
        command = (identity["compiler"]["path"], "-j1", "-M768", "--run", "PeanoLab/Verify.lean", *paths)
        _process(row, command=command, limits=CHECK_LIMITS, success_codes=(0, 1, 2), extra_fields=("case_ids",))
        if type(row["case_ids"]) is not list or row["case_ids"] != [case.case_id for case in selected]:
            raise ReferenceReviewError("reference worker batch lost its exact ordered case IDs")
        decisions = parse_verifier_output(row, paths)
        _validate_reported_fuel(row, selected, paths)
        for relative, case in zip(paths, selected):
            outcomes.append({"case_id": case.case_id, "artifact_sha256": hashlib.sha256(case.artifact).hexdigest(),
                             "expected": case.expected_lean, "observed": decisions[relative],
                             "agrees": decisions[relative] == case.expected_lean})
    for saved, expected in zip(result["cases"], outcomes):
        _keys(saved, {"case_id", "artifact_sha256", "expected", "observed", "agrees"}, "reference case outcome")
        if type(saved["agrees"]) is not bool or saved != expected:
            raise ReferenceReviewError("reference outcome differs from its original case and exact worker decision")
    mismatches = [row["case_id"] for row in outcomes if row["agrees"] is False]
    if (type(result["mismatches"]) is not list or result["mismatches"] != mismatches
        or result["status"] != ("failed" if mismatches else "passed")):
        raise ReferenceReviewError("reference aggregate status differs from its exact case outcomes")
    _sealed_digest(result, "results_sha256", "reference conformance results")


def check_reference_cases(destination: Path, identity: dict[str, object], build: dict[str, object], cases: tuple, *, progress=None) -> dict[str, object]:
    destination = destination.resolve(strict=True)
    validate_build(destination, identity, build)
    _validate_case_inputs(cases)
    directory = destination / "cases"
    directory.mkdir(mode=0o700)
    files = []
    for index, case in enumerate(cases):
        if len(case.artifact) > MAX_CASE_BYTES:
            raise ReferenceReviewError("conformance artifact exceeds its reservation")
        relative = f"cases/case-{index:05d}.json"
        with (destination / relative).open("xb") as stream:
            stream.write(case.artifact)
        files.append(relative)
    rows, outcomes = [], []
    for start in range(0, len(cases), BATCH_SIZE):
        paths = tuple(files[start:start + BATCH_SIZE])
        command = (str(identity["compiler"]["path"]), "-j1", "-M768", "--run", "PeanoLab/Verify.lean", *paths)
        row = run_bounded(command, cwd=destination, limits=CHECK_LIMITS, lean_path=destination)
        row["case_ids"] = [case.case_id for case in cases[start:start + BATCH_SIZE]]
        _process(row, command=command, limits=CHECK_LIMITS, success_codes=(0, 1, 2), extra_fields=("case_ids",))
        decisions = parse_verifier_output(row, paths)
        rows.append(row)
        for relative, case in zip(paths, cases[start:start + BATCH_SIZE]):
            outcomes.append({"case_id": case.case_id, "artifact_sha256": hashlib.sha256(case.artifact).hexdigest(),
                             "expected": case.expected_lean, "observed": decisions[relative],
                             "agrees": decisions[relative] == case.expected_lean})
        if progress:
            progress("reference_cases", min(start + BATCH_SIZE, len(cases)), len(cases), "independent Lean decisions")
    mismatches = [row["case_id"] for row in outcomes if not row["agrees"]]
    validate_build(destination, identity, build)
    result = {"schema": RESULTS_SCHEMA, "reference_sha256": identity["reference_sha256"],
              "status": "passed" if not mismatches else "failed", "cases": outcomes, "worker_rows": rows,
              "mismatches": mismatches, "case_count": len(cases), "model_calls": 0, "solver_calls": 0,
              "negative_theorem_claims": False, "h0_complete": False, "research_claim_eligible": False}
    result["results_sha256"] = digest(result)
    validate_reference_results(identity, result, cases)
    return result
