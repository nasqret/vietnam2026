"""Create a clean local source snapshot without touching the original Git tree.

This is a byte-level, synthetic source commit, not native proof verification,
human review, training approval, or a network operation. Complete declared code
scopes and the five selected epoch artifacts are copied; only Python/pytest
cache directories are omitted. No result archive, dataset, model or credential
location is selected. File contents are not a general-purpose secret scanner.

Every destination is fresh. On a failure the partial directory is retained and
must not be resumed or overwritten. Call this CPU-only utility under the
operator's resource guard; its only children are bounded local Git commands.
"""

from __future__ import annotations

from contextlib import ExitStack
import hashlib
import json
import os
from pathlib import Path
import re
import selectors
import stat
import subprocess
import time

from . import origin_bridge as bridge


PLAN_SCHEMA = "peano-hydra-scaling-source-freeze-plan-v1"
RECEIPT_SCHEMA = "peano-hydra-scaling-source-freeze-receipt-v1"
RESULT_SCHEMA = "peano-hydra-scaling-source-freeze-result-v1"
EXTRA_FILES = (".gitignore", "LICENSE", "requirements.txt")
CACHE_DIRECTORIES = frozenset(("__pycache__", ".pytest_cache"))
PROTECTED_DIRECTORIES = (
    ".git", ".agents", ".codex", "training", "scripts", "peano-lab", "book",
    "artifacts", "results", "docs", "slurm",
)
SOURCE_SUFFIXES = frozenset((".py", ".pyi", ".sh", ".toml", ".lock", ".json",
                             ".md", ".rst", ".txt", ".html", ".css", ".js"))
FORBIDDEN_NAMES = frozenset((
    "credentials.json", "credential.json", "secrets.json", "secret.json",
    "auth.json", "token.json", "tokens.json", "id_rsa", "id_ed25519",
    "results", "checkpoints", "_deploy", "node_modules",
))
SYNTHETIC_NAME = "Peano Hydra Synthetic Source Snapshot"
SYNTHETIC_EMAIL = "hydra-source-snapshot@invalid.example"
COMMIT_MESSAGE = "Synthetic Hydra source snapshot; not user review or training approval"
RECEIPT_PATH = "_deploy/scaling-freeze.json"
FAILURE_PATH = "_deploy/scaling-freeze-failed.json"
ORIGIN_PATH = "_deploy/scaling-origin-source.json"
MAX_SECONDS = 120
GIT_SECONDS = 10
MAX_GIT_BYTES = 4 * 1024**2
MAX_PROTECTED_INPUTS = 16
_READ_COMMANDS = frozenset(("rev-parse", "ls-tree"))
_OID = re.compile(r"[0-9a-f]{40}\Z")
_SAFE_PATH = re.compile(r"[A-Za-z0-9_./-]{1,1024}\Z")


class ScalingFreezeError(ValueError):
    """No successful snapshot was established; any partial output is retained."""

    def __init__(self, message, *, observation=None):
        super().__init__(message)
        self.observation = observation


def _require(condition, message):
    if not condition:
        raise ScalingFreezeError(message)


def _canonical(value):
    try:
        raw = json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False,
                         separators=(",", ":")).encode()
    except (TypeError, ValueError, UnicodeError, RecursionError) as error:
        raise ScalingFreezeError("invalid source-freeze metadata") from error
    _require(len(raw) <= bridge.MAX_RECEIPT_BYTES, "source-freeze metadata exceeds its bound")
    return raw


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _deadline(deadline):
    _require(time.monotonic() <= deadline, "local source freezing exceeded its wall bound")


def _path(name):
    bridge._relative(name)
    _require(_SAFE_PATH.fullmatch(name) is not None, "source path is not portable ASCII")
    return name


def _git_environment(*, synthetic):
    environment = {key: value for key, value in os.environ.items()
                   if not key.startswith(("GIT_", "LD_", "DYLD_"))}
    environment.update({
        "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_TERMINAL_PROMPT": "0", "GIT_OPTIONAL_LOCKS": "0",
        "GIT_NO_REPLACE_OBJECTS": "1", "GIT_NO_LAZY_FETCH": "1",
        "GIT_LITERAL_PATHSPECS": "1", "LC_ALL": "C",
    })
    if synthetic:
        environment.update({
            "GIT_AUTHOR_NAME": SYNTHETIC_NAME, "GIT_AUTHOR_EMAIL": SYNTHETIC_EMAIL,
            "GIT_COMMITTER_NAME": SYNTHETIC_NAME, "GIT_COMMITTER_EMAIL": SYNTHETIC_EMAIL,
        })
    return environment


def _git(tree, *arguments, deadline, input_bytes=b"", synthetic=False, maximum=MAX_GIT_BYTES):
    """Only owned Git commands; held cwd, no hooks/config helpers or lazy fetch."""
    _deadline(deadline)
    _require(type(input_bytes) is bytes and len(input_bytes) <= 2 * 1024**2,
             "Git stdin exceeds its bound")
    _require(arguments and (synthetic or arguments[0] in _READ_COMMANDS),
             "original source Git access is read-only")
    _require(type(maximum) is int and 0 < maximum <= MAX_GIT_BYTES, "invalid Git output bound")
    tree.assert_unchanged()
    descriptor = tree.directory()
    command = [
        "git", "--no-replace-objects", "--no-optional-locks",
        "-c", "core.fsmonitor=false", "-c", "core.untrackedCache=false",
        "-c", "core.hooksPath=" + os.devnull, "-c", "core.autocrlf=false",
        "-c", "core.filemode=true", "-c", "core.excludesFile=" + os.devnull,
        "-c", "core.attributesFile=" + os.devnull, "-c", "gc.auto=0",
        "-c", "maintenance.auto=false", "-c", "pack.threads=1",
        "-c", "commit.gpgsign=false", "-c", "tag.gpgsign=false",
        "-c", "protocol.allow=never", "-c", "credential.helper=",
        *arguments,
    ]
    selector = selectors.DefaultSelector()
    buffers = {"stdout": bytearray(), "stderr": bytearray()}
    process = None
    stop = min(deadline, time.monotonic() + GIT_SECONDS)
    offset = 0
    try:
        environment = _git_environment(synthetic=synthetic)
        if arguments[0] == "check-ignore":
            # check-ignore accepts pathnames, not pathspec magic. Its fixed
            # internal probe paths need no literal-pathspec override; keep
            # that protection for add, ls-tree and every other Git command.
            environment.pop("GIT_LITERAL_PATHSPECS")
        # Only fchdir runs between fork/exec, to avoid re-resolving a renamed
        # destination path. This standalone Unix utility does not load threads,
        # models, credential helpers or user Git hooks.
        process = subprocess.Popen(
            command, stdin=subprocess.PIPE if input_bytes else subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env=environment, pass_fds=(descriptor,),
            preexec_fn=lambda: os.fchdir(descriptor),
        )
        for stream, label in ((process.stdout, "stdout"), (process.stderr, "stderr")):
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_READ, label)
        if input_bytes:
            os.set_blocking(process.stdin.fileno(), False)
            selector.register(process.stdin, selectors.EVENT_WRITE, "stdin")
        while selector.get_map():
            _require(time.monotonic() <= stop, "local Git command exceeded its time bound")
            for key, _ in selector.select(min(0.1, max(0, stop - time.monotonic()))):
                if key.data == "stdin":
                    offset += os.write(key.fileobj.fileno(), input_bytes[offset:offset + 65536])
                    if offset == len(input_bytes):
                        selector.unregister(key.fileobj)
                        key.fileobj.close()
                    continue
                chunk = os.read(key.fileobj.fileno(), 65536)
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                target = buffers[key.data]
                _require(len(target) + len(chunk) <= (maximum if key.data == "stdout" else 16384),
                         "local Git command exceeded its output bound")
                target.extend(chunk)
        remaining = stop - time.monotonic()
        _require(remaining > 0 and process.wait(timeout=remaining) == 0,
                 "local Git command failed: " + arguments[0])
        tree.assert_unchanged()
        return bytes(buffers["stdout"])
    except (OSError, subprocess.SubprocessError) as error:
        raise ScalingFreezeError("bounded local Git command failed: " + arguments[0]) from error
    finally:
        selector.close()
        if process is not None:
            if process.poll() is None:
                process.kill()
            process.wait()
            for stream in (process.stdin, process.stdout, process.stderr):
                if stream is not None:
                    stream.close()


def _git_identity(tree, deadline):
    control = os.stat(".git", dir_fd=tree.directory(), follow_symlinks=False)
    _require(stat.S_ISDIR(control.st_mode) or
             (stat.S_ISREG(control.st_mode) and control.st_nlink == 1),
             "source Git control must be a no-follow directory or single-link gitdir file")
    if stat.S_ISDIR(control.st_mode):
        tree.directory(".git")
    else:
        tree.fingerprint(".git", maximum=8192)
    top = _git(tree, "rev-parse", "--show-toplevel", deadline=deadline, maximum=8192).decode().strip()
    _require(top == str(tree.root), "source root must be the exact Git working-tree root")
    head = _git(tree, "rev-parse", "--verify", "HEAD", deadline=deadline, maximum=80).decode().strip()
    _require(_OID.fullmatch(head) is not None, "source has no real SHA-1 Git commit")
    index_name = _git(tree, "rev-parse", "--git-path", "index", deadline=deadline,
                      maximum=8192).decode().strip()
    index = Path(index_name)
    if not index.is_absolute():
        index = tree.root / index
    index = bridge._absolute(index)
    with bridge._Tree(index.parent) as metadata:
        identity, _ = metadata.fingerprint(index.name, maximum=16 * 1024**2)
        signature = metadata.signatures[index.name]
        metadata.assert_unchanged()
    return {
        "head": head, "index_path": str(index), "index": identity,
        "index_file_identity": list(signature),
        "working_tree_status_executed": False,
    }


def _walk(tree, roots, *, deadline, caches=False, skip_git=False):
    files, entries, visited = set(), 0, 0

    def visit(relative, depth):
        nonlocal entries, visited
        _deadline(deadline)
        visited += 1
        _require(depth <= 16 and visited <= bridge.MAX_DIRECTORIES, "source directory bound exceeded")
        with os.scandir(tree.directory(relative)) as stream:
            for entry in stream:
                entries += 1
                _require(entries <= bridge.MAX_SOURCE_ENTRIES and len(entry.name.encode()) <= 256,
                         "source entry inventory exceeds its bound")
                child = relative + "/" + entry.name if relative else entry.name
                _path(child)
                info = entry.stat(follow_symlinks=False)
                _require(not stat.S_ISLNK(info.st_mode), "source or snapshot contains a symlink")
                if stat.S_ISDIR(info.st_mode):
                    if (caches and entry.name in CACHE_DIRECTORIES) or (skip_git and child == ".git"):
                        continue
                    visit(child, depth + 1)
                else:
                    _require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1,
                             "source or snapshot contains a nonregular or linked file")
                    files.add(child)
                    _require(len(files) <= bridge.MAX_SOURCE_FILES + 3, "source file count exceeds its bound")
    for root in roots:
        visit(root, 0)
    return files


def _namespace_absent(tree):
    for name in ("training.py", "training/__init__.py"):
        parent, _, leaf = name.rpartition("/")
        try:
            os.stat(leaf, dir_fd=tree.directory(parent), follow_symlinks=False)
        except FileNotFoundError:
            continue
        raise ScalingFreezeError("origin compatibility requires the unchanged training namespace")


def _selection(tree, deadline):
    _namespace_absent(tree)
    names = _walk(tree, bridge.SOURCE_SCOPES, deadline=deadline, caches=True)
    for name in names:
        parts = name.split("/")
        _require(not any(part.startswith(".") or part.lower() in FORBIDDEN_NAMES for part in parts)
                 and Path(name).suffix.lower() in SOURCE_SUFFIXES,
                 "unexpected non-code, private or generated input in source scope: " + name)
    _require(bridge.REQUIRED_SOURCE_FILES <= names, "required source files are missing")
    campaign = bridge._decode(tree.read(bridge.CAMPAIGN, 8 * 1024**2), 8 * 1024**2, "campaign")
    _require(campaign.get("schema") == "constructive-grand-campaign-v1"
             and type(campaign.get("meta")) is dict, "campaign does not select one epoch")
    version = campaign["meta"].get("current_alpha_version")
    epoch_paths = bridge._epoch_paths(version)
    names.update((*epoch_paths, *EXTRA_FILES))
    _require(len(names) <= bridge.MAX_SOURCE_FILES, "complete snapshot exceeds the source file bound")
    _require(len({name.casefold() for name in names}) == len(names), "portable paths collide by case")
    return version, names


def _plan(tree, deadline):
    initial_git = _git_identity(tree, deadline)
    version, names = _selection(tree, deadline)
    files, total = {}, 0
    for name in sorted(names):
        _deadline(deadline)
        maximum = min(bridge.MAX_PYTHON_BYTES if name.endswith(".py") else bridge.MAX_SOURCE_FILE_BYTES,
                      bridge.MAX_SOURCE_TOTAL_BYTES - total)
        identity, _ = tree.fingerprint(name, maximum=maximum)
        total += identity["bytes"]
        files[name] = identity
    _require(total <= bridge.MAX_SOURCE_TOTAL_BYTES, "source bytes exceed the origin source ceiling")
    # Do not silently patch an original ignore file into another source input.
    ignore = tree.read(".gitignore", 1024**2).decode("utf-8")
    lines = {line.strip() for line in ignore.splitlines()}
    _require(any(line in lines for line in ("/_deploy/", "_deploy/")),
             "source .gitignore must already exclude _deploy/")
    _require(any(line in lines for line in ("/results/", "results/"))
             or all(any(line in lines for line in (name, "/" + name))
                    for name in ("results/peano-hydra/", "results/peano-policy/")),
             "source .gitignore must already exclude Hydra/policy results")
    _require(_selection(tree, deadline) == (version, names), "source selection changed during planning")
    tree.assert_unchanged()
    _require(_git_identity(tree, deadline) == initial_git, "original Git state changed during planning")
    committed = _git_tree_record(_git(
        tree, "ls-tree", "-r", "-z", "HEAD", "--", *bridge.SOURCE_SCOPES,
        *bridge._epoch_paths(version), *EXTRA_FILES, deadline=deadline,
    ), allow_empty=True)
    selected_dirty = committed != {
        name: (item["mode"], item["git_blob"]) for name, item in files.items()
    }
    tree.assert_unchanged()
    record = {
        "schema": PLAN_SCHEMA, "source_root": str(tree.root), "source_git": initial_git,
        "selected_working_bytes_differ_from_head": selected_dirty,
        "scopes": list(bridge.SOURCE_SCOPES), "epoch_version": version,
        "epoch_paths": list(bridge._epoch_paths(version)), "extra_files": list(EXTRA_FILES),
        "excluded_cache_directories": sorted(CACHE_DIRECTORIES),
        "files": files, "file_count": len(files), "total_bytes": total,
        "native_epoch_verified": False, "proofs_replayed": 0,
        "whole_repository_snapshot": False, "original_repository_mutated": False,
        "model_or_dataset_payloads_selected": False, "training_authorized": False,
        "gpu_execution_authorized": False, "network_transfer_authorized": False,
    }
    return {**record, "plan_sha256": _sha(_canonical(record))}


def plan_scaling_freeze(source_root: Path):
    """Read-only inventory of dirty working bytes, never a proof/data admission."""
    deadline = time.monotonic() + MAX_SECONDS
    with bridge._Tree(bridge._absolute(source_root)) as source:
        return _plan(source, deadline)


def _protect_output(source, parent, output, protected_inputs=()):
    source.assert_unchanged()
    parent.assert_unchanged()
    _require(output.parent == parent.root and output != source.root and output not in source.root.parents,
             "snapshot output must be a fresh separate child")
    source_id = (os.fstat(source.directory()).st_dev, os.fstat(source.directory()).st_ino)
    ancestors = {(os.fstat(fd).st_dev, os.fstat(fd).st_ino) for fd in parent._fds}
    if source_id in ancestors:
        try:
            relative = output.relative_to(source.root)
        except ValueError as error:
            raise ScalingFreezeError("source-root aliases are not an output location") from error
        _require(len(relative.parts) == 2 and relative.parts[0] == "_deploy",
                 "an in-repository snapshot must be a direct fresh _deploy/ child")
    for name in PROTECTED_DIRECTORIES:
        protected = source.root / name
        _require(output != protected and protected not in output.parents,
                 "snapshot output is inside protected inputs")
        try:
            info = os.stat(name, dir_fd=source.directory(), follow_symlinks=False)
        except FileNotFoundError:
            continue
        _require(not stat.S_ISLNK(info.st_mode), "protected source root contains a symlink")
        if stat.S_ISDIR(info.st_mode):
            fd = source.directory(name)
            _require((os.fstat(fd).st_dev, os.fstat(fd).st_ino) not in ancestors,
                     "snapshot output aliases protected inputs")
    for protected in protected_inputs:
        protected.assert_unchanged()
        _require(output != protected.root and protected.root not in output.parents,
                 "snapshot output is inside an explicit protected input")
        info = os.fstat(protected.directory())
        _require((info.st_dev, info.st_ino) not in ancestors,
                 "snapshot output aliases an explicit protected input")
    try:
        os.stat(output.name, dir_fd=parent.directory(), follow_symlinks=False)
    except FileNotFoundError:
        return
    raise ScalingFreezeError("snapshot output already exists; no overwrite or resume")


def _new_file(tree, relative, raw, mode=0o644):
    relative = _path(relative)
    parent, _, name = relative.rpartition("/")
    current = ""
    for part in parent.split("/") if parent else ():
        previous, current = current, current + "/" + part if current else part
        try:
            os.stat(part, dir_fd=tree.directory(previous), follow_symlinks=False)
        except FileNotFoundError:
            os.mkdir(part, 0o700, dir_fd=tree.directory(previous))
            os.fsync(tree.directory(previous))
        tree.directory(current)
    tree.assert_unchanged()
    fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                 0o600, dir_fd=tree.directory(parent))
    try:
        offset = 0
        while offset < len(raw):
            offset += os.write(fd, raw[offset:offset + 1024**2])
        os.fchmod(fd, mode)
        os.fsync(fd)
        info = os.fstat(fd)
        named = os.stat(name, dir_fd=tree.directory(parent), follow_symlinks=False)
        _require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1
                 and bridge._signature(info) == bridge._signature(named),
                 "new snapshot file identity changed during publication")
    finally:
        os.close(fd)
    os.fsync(tree.directory(parent))
    tree.assert_unchanged()


def _check_files(tree, files, deadline):
    for name, expected in files.items():
        _deadline(deadline)
        actual, _ = tree.fingerprint(name, maximum=expected["bytes"])
        _require(actual == expected, "snapshot/source bytes or Git mode changed: " + name)
    tree.assert_unchanged()


def _git_tree_record(raw, *, allow_empty=False):
    _require((allow_empty and raw == b"") or raw.endswith(b"\0"),
             "snapshot commit inventory is incomplete")
    actual = {}
    entries = raw[:-1].split(b"\0") if raw else []
    _require(len(entries) <= bridge.MAX_SOURCE_FILES, "Git source inventory exceeds its bound")
    for entry in entries:
        try:
            info, path = entry.split(b"\t", 1)
            mode, kind, blob = info.decode("ascii").split()
            name = _path(path.decode("utf-8"))
        except (ValueError, UnicodeError) as error:
            raise ScalingFreezeError("snapshot commit inventory is malformed") from error
        _require(kind == "blob" and mode in ("100644", "100755")
                 and _OID.fullmatch(blob) is not None and name not in actual,
                 "snapshot commit contains an unexpected entry")
        actual[name] = (mode, blob)
    return actual


def _check_git_tree(raw, expected):
    actual = _git_tree_record(raw)
    _require(actual == {name: (item["mode"], item["git_blob"]) for name, item in expected.items()},
             "snapshot commit is not the exact copied file inventory")


def freeze_scaling_source(source_root: Path, output_directory: Path, *,
                          expected_plan_sha256=None, protected_inputs: tuple[Path, ...] = ()):
    """Copy once, commit only the fresh destination, and mint a portable manifest."""
    _require(os.name == "posix", "source freezing requires held Unix directory descriptors")
    deadline = time.monotonic() + MAX_SECONDS
    output = bridge._absolute(output_directory)
    _require(output.name not in ("", ".", "..", ".git") and _SAFE_PATH.fullmatch(output.name),
             "snapshot output needs one safe dedicated name")
    _require(type(protected_inputs) is tuple and len(protected_inputs) <= MAX_PROTECTED_INPUTS
             and all(isinstance(path, Path) for path in protected_inputs),
             "protected inputs must be a bounded tuple of explicit directory Paths")
    if expected_plan_sha256 is not None:
        bridge._hash(expected_plan_sha256, "expected freeze plan")
    state = {"status": "incomplete", "output_directory": str(output), "copied_files": 0,
             "phase": "preflight", "partial_output_retained": False}
    destination = None
    with ExitStack() as stack:
        source = stack.enter_context(bridge._Tree(bridge._absolute(source_root)))
        parent = stack.enter_context(bridge._Tree(output.parent))
        protected = tuple(stack.enter_context(bridge._Tree(bridge._absolute(path)))
                          for path in protected_inputs)
        try:
            _protect_output(source, parent, output, protected)
            plan = _plan(source, deadline)
            if expected_plan_sha256 is not None:
                _require(plan["plan_sha256"] == expected_plan_sha256, "externally pinned source plan changed")
            _protect_output(source, parent, output, protected)
            os.mkdir(output.name, 0o700, dir_fd=parent.directory())
            os.fsync(parent.directory())
            state["partial_output_retained"] = True
            created = os.stat(output.name, dir_fd=parent.directory(), follow_symlinks=False)
            destination = stack.enter_context(bridge._Tree(output))
            opened = os.fstat(destination.directory())
            _require((created.st_dev, created.st_ino) == (opened.st_dev, opened.st_ino),
                     "fresh snapshot directory was replaced")
            state["phase"] = "copy"
            for name, expected in plan["files"].items():
                _deadline(deadline)
                actual, raw = source.fingerprint(name, maximum=expected["bytes"], retain=True)
                _require(actual == expected, "source changed before its exact copy: " + name)
                _new_file(destination, name, raw, 0o755 if expected["mode"] == "100755" else 0o644)
                state["copied_files"] += 1
            _require(_walk(destination, ("",), deadline=deadline) == set(plan["files"]),
                     "fresh snapshot has unexpected pre-Git entries")
            _check_files(source, plan["files"], deadline)
            _check_files(destination, plan["files"], deadline)
            _require(_selection(source, deadline) == (plan["epoch_version"], set(plan["files"])),
                     "source inventory changed before commit")
            state["phase"] = "local-git"
            _git(destination, "init", "--quiet", "--template=", "--object-format=sha1",
                 "--initial-branch=hydra-source-snapshot", deadline=deadline, synthetic=True)
            destination.directory(".git")
            ignored = (RECEIPT_PATH, FAILURE_PATH, ORIGIN_PATH,
                       "results/peano-hydra/ignore-probe", "results/peano-policy/ignore-probe")
            ignore_input = b"".join(name.encode() + b"\0" for name in ignored)
            _require(_git(destination, "check-ignore", "--no-index", "-z", "--stdin", deadline=deadline,
                          input_bytes=ignore_input, synthetic=True) == ignore_input,
                     "copied ignore rules do not exclude deployment receipts/results")
            path_input = b"".join(name.encode() + b"\0" for name in sorted(plan["files"]))
            _git(destination, "add", "--force", "--pathspec-from-file=-", "--pathspec-file-nul",
                 deadline=deadline, input_bytes=path_input, synthetic=True)
            _git(destination, "commit", "--quiet", "--no-gpg-sign", "--no-verify", "-m", COMMIT_MESSAGE,
                 deadline=deadline, synthetic=True)
            commit = _git(destination, "rev-parse", "--verify", "HEAD", deadline=deadline,
                          maximum=80, synthetic=True).decode().strip()
            _require(_OID.fullmatch(commit) is not None, "synthetic snapshot has no real commit")
            _check_git_tree(_git(destination, "ls-tree", "-r", "-z", "HEAD",
                                 deadline=deadline, synthetic=True), plan["files"])
            _require(_git(destination, "status", "--porcelain=v1", "-z", "--untracked-files=all",
                          deadline=deadline, synthetic=True) == b"", "snapshot is not clean")
            state["phase"] = "portable-origin"
            for tree in protected:
                tree.assert_unchanged()
            origin = bridge.freeze_origin_sources(output, expected_commit=commit)
            origin_record = bridge._decode(origin, bridge.MAX_BUNDLE_MANIFEST_BYTES, "snapshot source bundle")
            _require(origin_record["files"] == {name: item for name, item in plan["files"].items()
                                                if name not in EXTRA_FILES},
                     "portable source manifest differs from copied origin scopes")
            _new_file(destination, ORIGIN_PATH, origin)
            _check_files(source, plan["files"], deadline)
            _check_files(destination, plan["files"], deadline)
            _require(_selection(source, deadline) == (plan["epoch_version"], set(plan["files"]))
                     and _git_identity(source, deadline) == plan["source_git"],
                     "original repository changed during source freezing")
            receipt = {
                "schema": RECEIPT_SCHEMA, "status": "complete", "source_plan": plan,
                "snapshot_root": str(output), "git_commit": commit,
                "synthetic_author": {"name": SYNTHETIC_NAME, "email": SYNTHETIC_EMAIL},
                "commit_message": COMMIT_MESSAGE,
                "protected_inputs": [
                    {"path": str(tree.root), "device": os.fstat(tree.directory()).st_dev,
                     "inode": os.fstat(tree.directory()).st_ino} for tree in protected
                ],
                "origin_source_manifest": {"path": ORIGIN_PATH, "bytes": len(origin), "sha256": _sha(origin)},
                "source_bytes_unchanged": True, "original_git_state_unchanged": True,
                "snapshot_clean": True, "native_epoch_verified": False, "proofs_replayed": 0,
                "model_or_dataset_payloads_copied": False, "training_authorized": False,
                "gpu_execution_authorized": False, "network_transfer_authorized": False,
                "coverage": "exact declared code/config/epoch bytes and Git blobs; not native proof or runtime verification",
            }
            raw_receipt = _canonical(receipt) + b"\n"
            _require(_walk(destination, ("",), deadline=deadline, skip_git=True)
                     == set(plan["files"]) | {ORIGIN_PATH},
                     "completed snapshot contains unexpected payloads")
            _require(_git(destination, "status", "--porcelain=v1", "-z", "--untracked-files=all",
                          deadline=deadline, synthetic=True) == b"", "receipt publication dirtied the snapshot")
            source.assert_unchanged()
            destination.assert_unchanged()
            parent.assert_unchanged()
            for tree in protected:
                tree.assert_unchanged()
            # Publish the completion receipt only after every source/commit/
            # inventory check passed; an earlier failure has no success file.
            _new_file(destination, RECEIPT_PATH, raw_receipt)
            return {
                "schema": RESULT_SCHEMA, "status": "complete", "snapshot_root": str(output),
                "git_commit": commit, "plan_sha256": plan["plan_sha256"],
                "receipt_path": str(output / RECEIPT_PATH), "receipt_sha256": _sha(raw_receipt),
                "origin_source_manifest_path": str(output / ORIGIN_PATH),
                "origin_source_manifest_sha256": _sha(origin),
                "file_count": plan["file_count"], "total_bytes": plan["total_bytes"],
                "native_epoch_verified": False, "proofs_replayed": 0,
                "training_authorized": False, "gpu_execution_authorized": False,
            }
        except (OSError, ValueError, UnicodeError, subprocess.SubprocessError) as error:
            state["error"] = " ".join(str(error).split())[:1024]
            state["failure_receipt_path"] = None
            if destination is not None:
                try:
                    destination.assert_unchanged()
                    for tree in protected:
                        tree.assert_unchanged()
                    _new_file(destination, FAILURE_PATH, _canonical({"schema": RECEIPT_SCHEMA, **state}) + b"\n")
                    state["failure_receipt_path"] = str(output / FAILURE_PATH)
                except (OSError, ValueError):
                    # An unsafe/replaced destination is never followed to write
                    # a diagnostic. The caller still receives this observation.
                    pass
            raise ScalingFreezeError(
                "source snapshot incomplete; original repository was not staged or committed",
                observation=state,
            ) from error


__all__ = ["ScalingFreezeError", "PLAN_SCHEMA", "RECEIPT_SCHEMA", "RESULT_SCHEMA",
           "plan_scaling_freeze", "freeze_scaling_source"]
