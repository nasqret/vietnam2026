"""Three bounded, fork-only publication phases inheriting genuine live evidence.

The pipe transports file identities and resource measurements, not proof
authority.  No receipt loader or child CLI exists.  Every output is staged
privately, tested, rehashed by the parent and installed only after all phases
succeed.  Existing output directories are never replaced.
"""

from __future__ import annotations

from collections.abc import Mapping
import ctypes
from dataclasses import dataclass, replace
import json
import os
from pathlib import Path
import re
import resource
import secrets
import selectors
import signal
import sys
from tempfile import TemporaryDirectory
import time

import constructive_completed_lower_publication_v31 as publication


CPU_LIMITS = (170, 175)
WALL_SECONDS = 180
CLEANUP_SECONDS = 5
TIMEOUT_SECONDS = WALL_SECONDS + CLEANUP_SECONDS
MAX_RSS_BYTES = 1536 * 1024 * 1024
MAX_MESSAGE_BYTES = 8192
MAX_INVENTORY_BYTES = 2 * 1024 * 1024
MAX_FILE_BYTES = 64 * 1024 * 1024
MAX_FILES = 20000
SCHEMA = "peano-lab-alpha-v31-publication-process-v1"
PHASES = ("completed", "historical", "atlas")
OUTPUTS = {
    "completed": publication.ROOT / "book/_static" / publication.OUTPUT_NAME,
    "historical": publication.ROOT / "book/_static" / publication.HISTORICAL_OUTPUT_NAME,
    "atlas": publication.ROOT / "book/_static" / publication.ATLAS_NAME,
}
TESTS = {
    "completed": ("peano-lab/py/tests/test_constructive_completed_lower_explorer_v31.py", "not atlas"),
    "historical": ("peano-lab/py/tests/test_constructive_historical_publication_v31.py", None),
    "atlas": ("peano-lab/py/tests/test_constructive_completed_lower_explorer_v31.py", "atlas"),
}


class PublicationProcessError(ValueError):
    """A rendering, transport, live-source or output identity failed closed."""


@dataclass(frozen=True, slots=True)
class PhaseResult:
    phase: str
    directory: Path
    inventory: dict
    inventory_sha256: str
    peak_rss_bytes: int
    elapsed_seconds: float


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def _rss_bytes() -> int:
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    value = int(value if sys.platform == "darwin" else value * 1024)
    if not 0 < value <= MAX_RSS_BYTES:
        raise PublicationProcessError("publication exceeded the unchanged 1536 MiB RSS ceiling")
    return value


def _regular_directory(path: Path) -> None:
    path = Path(path)
    for parent in (*reversed(path.parents), path):
        if parent.is_symlink() or not parent.is_dir():
            raise PublicationProcessError("publication directory has an unsafe ancestor")


def _pin(payload: bytes) -> dict:
    return {"bytes": len(payload), "sha256": publication.digest(payload)}


def _validate_pin(pin: object, maximum: int) -> None:
    if (type(pin) is not dict or set(pin) != {"bytes", "sha256"}
            or type(pin["bytes"]) is not int or not 0 < pin["bytes"] <= maximum
            or type(pin["sha256"]) is not str or re.fullmatch(r"[0-9a-f]{64}", pin["sha256"]) is None):
        raise PublicationProcessError("invalid bounded publication file identity")


def _validate_inventory(inventory: object) -> None:
    if (type(inventory) is not dict or set(inventory) != {"files", "file_count", "html_count", "total_bytes"}
            or type(inventory["files"]) is not dict
            or type(inventory["file_count"]) is not int
            or not 0 < inventory["file_count"] <= MAX_FILES
            or inventory["file_count"] != len(inventory["files"])
            or type(inventory["html_count"]) is not int
            or inventory["html_count"] != sum(name.endswith(".html") for name in inventory["files"] if type(name) is str)
            or type(inventory["total_bytes"]) is not int
            or not 0 < inventory["total_bytes"] <= MAX_RSS_BYTES):
        raise PublicationProcessError("invalid bounded publication inventory")
    total = 0
    for name, pin in inventory["files"].items():
        if not publication.safe_relative(name) or "\x00" in name:
            raise PublicationProcessError("unsafe publication inventory path")
        _validate_pin(pin, MAX_FILE_BYTES)
        total += pin["bytes"]
    if total != inventory["total_bytes"]:
        raise PublicationProcessError("publication inventory byte accounting changed")


def _validate_tree(tree: Path, inventory: dict) -> None:
    """Fresh exact file reads; a manifest or a report alone is not accepted."""
    _validate_inventory(inventory)
    _regular_directory(tree)
    actual = set()
    for path in tree.rglob("*"):
        if path.is_symlink() or not (path.is_dir() or path.is_file()):
            raise PublicationProcessError("publication output has a nonregular filesystem entry")
        if path.is_file():
            actual.add(path.relative_to(tree).as_posix())
            if len(actual) > MAX_FILES:
                raise PublicationProcessError("publication output exceeds its file count bound")
    if actual != set(inventory["files"]):
        raise PublicationProcessError("publication output has missing or unregistered files")
    for name, pin in inventory["files"].items():
        publication.read_pinned(tree / name, pin["bytes"], pin["sha256"])
    _rss_bytes()


def _validate_message(payload: bytes, *, nonce: str, phase: str, context, check: bool) -> dict:
    if (type(check) is not bool or phase not in PHASES
            or type(nonce) is not str or re.fullmatch(r"[0-9a-f]{64}", nonce) is None
            or type(payload) is not bytes or not 0 < len(payload) <= MAX_MESSAGE_BYTES):
        raise PublicationProcessError("invalid bounded publication transport input")
    value = publication.strict_json(payload)
    keys = {"schema", "nonce", "phase", "catalog_sha256", "source_binding_sha256", "check",
            "limits", "peak_rss_bytes", "inventory", "pytest_status"}
    if type(value) is not dict or set(value) != keys or _canonical(value) != payload:
        raise PublicationProcessError("noncanonical or unexpected publication result")
    expected = {
        "schema": SCHEMA, "nonce": nonce, "phase": phase,
        "catalog_sha256": context.catalog_sha256,
        "source_binding_sha256": context.source_binding_sha256, "check": check,
        "limits": {"cpu": list(CPU_LIMITS), "wall_seconds": WALL_SECONDS, "max_rss_bytes": MAX_RSS_BYTES},
        "pytest_status": 0,
    }
    if (_canonical({key: value[key] for key in expected}) != _canonical(expected)
            or type(value["pytest_status"]) is not int
            or any(type(getattr(context, key)) is not str or re.fullmatch(r"[0-9a-f]{64}", getattr(context, key)) is None
                   for key in ("catalog_sha256", "source_binding_sha256"))
            or type(value["peak_rss_bytes"]) is not int or not 0 < value["peak_rss_bytes"] <= MAX_RSS_BYTES):
        raise PublicationProcessError("stale, foreign, untested or over-budget publication result")
    _validate_pin(value["inventory"], MAX_INVENTORY_BYTES)
    return value


def _phase_entries(context, phase: str):
    if phase == "completed":
        from build_constructive_completed_lower_explorer_v31 import build_files_from_live
        return build_files_from_live(context).items()
    if phase == "historical":
        from upgrade_constructive_historical_publication_v31 import iter_files_from_live
        return iter_files_from_live(context)
    if phase == "atlas":
        from extend_constructive_completed_lower_campaign_v31 import build_files_from_live
        return build_files_from_live(context).items()
    raise PublicationProcessError("unknown publication phase")


def _run_phase_tests(context, phase: str, directory: Path, inventory: dict) -> int:
    import pytest

    class LivePublicationPlugin:
        def pytest_configure(self, config):
            config._alpha_v31_publication = {
                "phase": phase, "context": context, "directory": directory, "inventory": inventory,
            }

    filename, selector = TESTS[phase]
    args = ["-q", "--tb=short", str(publication.ROOT / filename)]
    if selector is not None:
        args.extend(("-k", selector))
    # The plugin carries the actual same-live capability, not a disk receipt.
    return int(pytest.main(args, plugins=[LivePublicationPlugin()]))


def _render_child(context, phase: str, *, work: Path, check: bool, nonce: str, write_fd: int) -> None:
    tree = work / "files"
    tree.mkdir()
    pins, total = {}, 0
    for name, payload in _phase_entries(context, phase):
        if (not publication.safe_relative(name) or "\x00" in name or name in pins
                or type(payload) is not bytes or not 0 < len(payload) <= MAX_FILE_BYTES):
            raise PublicationProcessError("unsafe, duplicate or oversized generated publication file")
        pins[name] = _pin(payload)
        total += len(payload)
        if len(pins) > MAX_FILES or total > MAX_RSS_BYTES:
            raise PublicationProcessError("publication exceeds its bounded output inventory")
        destination = tree / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("xb") as stream:
            stream.write(payload)
    inventory = {"files": pins, "file_count": len(pins), "html_count": sum(name.endswith(".html") for name in pins), "total_bytes": total}
    _validate_tree(tree, inventory)
    _rss_bytes()
    status = _run_phase_tests(context, phase, tree, inventory)
    if type(status) is not int or status != 0:
        raise PublicationProcessError("mandatory same-live publication tests failed")
    # Tests cannot silently rewrite a page after its initial identity was taken.
    _validate_tree(tree, inventory)
    context.require_unchanged()
    raw_inventory = _canonical(inventory)
    if len(raw_inventory) > MAX_INVENTORY_BYTES:
        raise PublicationProcessError("publication inventory exceeds the unchanged 2 MiB manifest bound")
    with (work / "inventory.json").open("xb") as stream:
        stream.write(raw_inventory)
    message = {
        "schema": SCHEMA, "nonce": nonce, "phase": phase,
        "catalog_sha256": context.catalog_sha256, "source_binding_sha256": context.source_binding_sha256,
        "check": check, "limits": {"cpu": list(resource.getrlimit(resource.RLIMIT_CPU)),
                                    "wall_seconds": WALL_SECONDS, "max_rss_bytes": MAX_RSS_BYTES},
        "peak_rss_bytes": _rss_bytes(), "inventory": _pin(raw_inventory), "pytest_status": status,
    }
    payload = _canonical(message)
    if len(payload) > MAX_MESSAGE_BYTES:
        raise PublicationProcessError("publication result exceeds its bounded pipe")
    with os.fdopen(write_fd, "wb", closefd=False) as stream:
        stream.write(payload)
        stream.flush()
    _rss_bytes()


def _fork_phase(context, phase: str, *, output: Path, check: bool) -> PhaseResult:
    """Private transport seam.  Public entry first requires the real capability."""
    if type(check) is not bool or phase not in PHASES:
        raise PublicationProcessError("invalid publication phase or Boolean option")
    if not hasattr(os, "fork") or not hasattr(os, "setsid"):
        raise PublicationProcessError("bounded live-capability publication requires POSIX fork")
    output = Path(output)
    _regular_directory(output.parent)
    if output.exists() or output.is_symlink():
        raise PublicationProcessError("refusing to replace an existing private render tree")
    nonce = secrets.token_hex(32)
    with TemporaryDirectory(prefix=".alpha-v31-render-", dir=output.parent) as temporary:
        work = Path(temporary)
        read_fd, write_fd = os.pipe()
        sys.stdout.flush(); sys.stderr.flush()
        started = time.monotonic()
        try:
            pid = os.fork()
        except BaseException:
            os.close(read_fd); os.close(write_fd)
            raise
        if pid == 0:
            status = 1
            os.close(read_fd)
            try:
                os.setsid()
                resource.setrlimit(resource.RLIMIT_CPU, CPU_LIMITS)
                signal.signal(signal.SIGALRM, signal.SIG_DFL)
                signal.alarm(WALL_SECONDS)
                _render_child(context, phase, work=work, check=check, nonce=nonce, write_fd=write_fd)
                status = 0
            except BaseException as error:
                print(f"v31 {phase} rendering failed: {type(error).__name__}: {str(error)[:1024]}", file=sys.stderr, flush=True)
            finally:
                os.close(write_fd)
                sys.stdout.flush(); sys.stderr.flush()
                os._exit(status)
        os.close(write_fd)
        result, child_status, eof, group_cleaned = bytearray(), None, False, False
        deadline, cleanup_limit = started + WALL_SECONDS, started + TIMEOUT_SECONDS
        try:
            os.set_blocking(read_fd, False)
            with selectors.DefaultSelector() as selector:
                selector.register(read_fd, selectors.EVENT_READ)
                while not (child_status is not None and eof):
                    if time.monotonic() >= deadline:
                        raise PublicationProcessError("publication child exceeded its original 180-second window")
                    if selector.select(min(0.1, max(0, deadline - time.monotonic()))):
                        chunk = os.read(read_fd, MAX_MESSAGE_BYTES - len(result) + 1)
                        if chunk:
                            result.extend(chunk)
                            if len(result) > MAX_MESSAGE_BYTES:
                                raise PublicationProcessError("publication child returned an oversized result")
                        else:
                            eof = True
                            selector.unregister(read_fd)
                    if child_status is None:
                        waited, status = os.waitpid(pid, os.WNOHANG)
                        if waited:
                            child_status = status
                            group_cleaned = True
                            try: os.killpg(pid, signal.SIGKILL)
                            except ProcessLookupError: pass
                            if not os.WIFEXITED(status) or os.WEXITSTATUS(status) != 0:
                                raise PublicationProcessError("publication child did not exit successfully")
            if time.monotonic() >= deadline:
                raise PublicationProcessError("publication child exited after its original deadline")
            message = _validate_message(bytes(result), nonce=nonce, phase=phase, context=context, check=check)
            pin = message["inventory"]
            raw = publication.read_pinned(work / "inventory.json", pin["bytes"], pin["sha256"])
            inventory = publication.strict_json(raw)
            if _canonical(inventory) != raw:
                raise PublicationProcessError("publication inventory is not canonical JSON")
            _validate_tree(work / "files", inventory)
            context.require_unchanged()
            if time.monotonic() >= deadline:
                raise PublicationProcessError("publication validation exceeded its original bounded phase")
            _rename_new(work / "files", output)
            return PhaseResult(phase, output, inventory, publication.digest(raw), message["peak_rss_bytes"], time.monotonic() - started)
        finally:
            os.close(read_fd)
            try:
                if not group_cleaned:
                    if child_status is None:
                        try: os.kill(pid, signal.SIGKILL)
                        except ProcessLookupError: pass
                    group_cleaned = True
                    try: os.killpg(pid, signal.SIGKILL)
                    except ProcessLookupError: pass
            finally:
                # EPERM is not ignored or retried; exact owned leader reaping
                # still occurs, within the original five-second cleanup budget.
                if child_status is None:
                    until = min(cleanup_limit, time.monotonic() + CLEANUP_SECONDS)
                    while not os.waitpid(pid, os.WNOHANG)[0]:
                        if time.monotonic() >= until:
                            raise PublicationProcessError("stopped publication child exceeded its cleanup deadline")
                        time.sleep(0.01)


def _rename_new(source: Path, destination: Path) -> None:
    """Atomic no-replace directory rename; never overwrite a concurrent target."""
    library = ctypes.CDLL(None, use_errno=True)
    old, new = os.fsencode(source), os.fsencode(destination)
    if sys.platform == "darwin" and hasattr(library, "renamex_np"):
        function = library.renamex_np
        function.argtypes = (ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint)
        function.restype = ctypes.c_int
        result = function(old, new, 0x00000004)  # RENAME_EXCL, SDK sys/stdio.h.
    elif sys.platform.startswith("linux") and hasattr(library, "renameat2"):
        function = library.renameat2
        function.argtypes = (ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint)
        function.restype = ctypes.c_int
        result = function(-100, old, -100, new, 1)  # AT_FDCWD, RENAME_NOREPLACE.
    else:
        raise PublicationProcessError("atomic non-overwriting publication is unavailable on this platform")
    if result:
        number = ctypes.get_errno()
        raise OSError(number, os.strerror(number), str(destination))


def _install_results(results: tuple[PhaseResult, ...], *, check: bool) -> None:
    if type(check) is not bool or tuple(row.phase for row in results) != PHASES:
        raise PublicationProcessError("all three exact publication phases are required")
    for row in results:
        _validate_inventory(row.inventory)
        if publication.digest(_canonical(row.inventory)) != row.inventory_sha256:
            raise PublicationProcessError("publication inventory changed after the child tested it")
        target = OUTPUTS[row.phase]
        _regular_directory(target.parent)
        if check:
            _validate_tree(target, row.inventory)
        elif target.exists() or target.is_symlink():
            raise PublicationProcessError("refusing to replace an existing publication tree")
    if check:
        return
    moved = []
    try:
        for row in results:
            _validate_tree(row.directory, row.inventory)
            identity = row.directory.stat()
            _rename_new(row.directory, OUTPUTS[row.phase])
            moved.append((row, identity.st_dev, identity.st_ino))
        _rss_bytes()
    except BaseException:
        for row, device, inode in reversed(moved):
            target = OUTPUTS[row.phase]
            if (target.is_symlink() or not target.is_dir()
                    or (target.stat().st_dev, target.stat().st_ino) != (device, inode)):
                raise PublicationProcessError("publication rollback refused a changed or foreign directory")
            _rename_new(target, row.directory)
        raise


def publish_from_live_context(context, check: bool) -> tuple[PhaseResult, ...]:
    """Mandatory fresh capability + all three mandatory same-live UI gates."""
    publication.require_live(context)
    if type(check) is not bool:
        raise PublicationProcessError("publication check must be an explicit Boolean")
    for target in OUTPUTS.values():
        _regular_directory(target.parent)
        if (not check and (target.exists() or target.is_symlink())) or (check and not target.is_dir()):
            raise PublicationProcessError("publication target does not match exclusive-write/check mode")
    with TemporaryDirectory(prefix=".alpha-v31-publication-", dir=publication.ROOT / "book/_static") as temporary:
        results = []
        for phase in PHASES:
            print(f"Alpha v31 pure publication: start {phase} (180s original window)", file=sys.stderr, flush=True)
            result = _fork_phase(context, phase, output=Path(temporary) / phase, check=check)
            results.append(result)
            print(f"Alpha v31 pure publication: PASS {phase}; {result.inventory['file_count']} files; RSS {result.peak_rss_bytes}B; {result.elapsed_seconds:.3f}s", file=sys.stderr, flush=True)
        context.require_unchanged()
        _rss_bytes()
        _install_results(tuple(results), check=check)
        return tuple(replace(row, directory=OUTPUTS[row.phase]) for row in results)
