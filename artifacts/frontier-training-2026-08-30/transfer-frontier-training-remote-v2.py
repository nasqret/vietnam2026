# Version 2 transport correction only. The v1 inventory/helper hashes retain
# their historical meaning; current transport identity is pinned separately.
# Actual Helios Python 3.6.8 starts at 265900 KiB VmSize, above v1's 256 MiB
# RLIMIT_AS despite approximately 13 MiB RSS. Keep finite 320 MiB AS headroom;
# all file/byte/CPU/wall bounds, SHA-256 backend and destination are unchanged.
"""Fixed Python 3.6 receiver; definitions only until main() is explicitly called.

The only writes are fresh directories/files beneath REMOTE_ROOT. No extraction,
subprocess, imports from the received tree, installation, or scheduler action.
"""
import datetime
import hashlib
import json
import os
import re
import resource
import signal
import stat
import struct
import sys

REMOTE_ROOT = "/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/frontier-training-v1"
LOCAL_ROOT = "/Users/bnaskrecki/codex/peano/_deploy/hydra-frontier-training-execution-20260830"
PROFILE = "peano-hydra-frontier-training-v1"
RUN_ID = "frontier-training-v1"
PACKAGE = "_deploy/hydra-frontier-training-v1"
REQUEST = PACKAGE + "/resource-request.json"
APPROVAL = PACKAGE + "/approval.json"
PROVENANCE = ".peano-source-provenance.tsv"
USER_INSTRUCTION_SHA256 = "7158689e94fd42e60710b15a134ec8a2a2f446da993ef0b52e9cd815138ed164"
SCHEMA = "peano-hydra-frontier-training-transfer-inventory-v1"
MAGIC = b"HYDRA-FRONTIER-TRAINING-TRANSFER-V1\n"
MAX_FILES = 4096
MAX_FILE = 64 * 1024**2
MAX_TOTAL = 512 * 1024**2
MAX_JSON = 4 * 1024**2
HEX = re.compile(r"[0-9a-f]{64}\Z")
COMMIT = re.compile(r"[0-9a-f]{40}\Z")
FORBIDDEN = frozenset((".git", ".cache", ".venv", "__pycache__", "node_modules",
                       "results", "logs", "checkpoints", "id_rsa", "id_ed25519",
                       "credentials.json", "secrets.json", "auth.json"))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def utc():
    return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def decode(raw):
    require(type(raw) is bytes and 0 < len(raw) <= MAX_JSON, "JSON byte bound")
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "duplicate JSON key")
            result[key] = value
        return result
    def invalid(value):
        raise ValueError("nonfinite JSON value")
    def integer(value):
        require(len(value) <= 32, "oversized JSON integer")
        return int(value)
    value = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs,
                       parse_constant=invalid, parse_int=integer)
    require(type(value) is dict, "JSON object required")
    return value


def relative(name):
    require(type(name) is str and re.fullmatch(r"[A-Za-z0-9_.\-/]{1,1024}", name), "unsafe path alphabet")
    parts = name.split("/")
    require(len(parts) <= 32 and all(part not in ("", ".", "..") for part in parts), "unsafe relative path")
    require(not (set(parts) & FORBIDDEN), "forbidden path component")
    require(not name.lower().endswith((".safetensors", ".bin", ".pt", ".pth", ".ckpt", ".pkl")), "model/binary payload forbidden")
    return name


def descriptor(value):
    require(type(value) is dict and set(value) == {"bytes", "sha256"}, "file descriptor fields")
    require(type(value["bytes"]) is int and 0 <= value["bytes"] <= MAX_FILE, "file byte bound")
    require(type(value["sha256"]) is str and HEX.fullmatch(value["sha256"]), "file SHA")
    return value


def file_map(value):
    require(type(value) is dict and 0 < len(value) <= MAX_FILES, "file count bound")
    total = 0
    for name, record in value.items():
        relative(name)
        descriptor(record)
        total += record["bytes"]
    require(total <= MAX_TOTAL, "total payload byte bound")
    return value


def expected_order(files):
    return [REQUEST, APPROVAL] + sorted(set(files) - {REQUEST, APPROVAL, PROVENANCE}) + [PROVENANCE]


def validate_inventory(record):
    fields = {"schema", "profile", "run_id", "local_root", "remote_root", "source_commit",
              "request_sha256", "approval_sha256", "user_instruction_sha256", "created_at_utc",
              "files", "file_modes", "order", "file_count", "total_bytes", "provenance",
              "source_files", "payloads", "helper_sha256", "remote_helper_sha256", "limits"}
    require(type(record) is dict and set(record) == fields, "inventory fields")
    require(record["schema"] == SCHEMA and record["profile"] == PROFILE and record["run_id"] == RUN_ID,
            "foreign transfer profile")
    require(record["local_root"] == LOCAL_ROOT and record["remote_root"] == REMOTE_ROOT, "fixed endpoints changed")
    require(type(record["source_commit"]) is str and COMMIT.fullmatch(record["source_commit"]), "commit pin")
    for field in ("request_sha256", "approval_sha256", "helper_sha256", "remote_helper_sha256"):
        require(type(record[field]) is str and HEX.fullmatch(record[field]), field)
    require(record["user_instruction_sha256"] == USER_INSTRUCTION_SHA256, "authorization sidecar changed")
    stamp = record["created_at_utc"]
    require(type(stamp) is str and re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z", stamp), "UTC stamp")
    datetime.datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ")
    require(record["limits"] == {"files": MAX_FILES, "file_bytes": MAX_FILE, "total_bytes": MAX_TOTAL,
                                 "ssh_wall_seconds": 60, "automatic_retry": False}, "transfer limits changed")
    sources, payloads, files = (file_map(record[key]) for key in ("source_files", "payloads", "files"))
    require(not (set(sources) & set(payloads)), "source/payload inventory overlap")
    require(all(not name.startswith("_deploy/") for name in sources), "deployment file in source inventory")
    require(all(name.startswith(PACKAGE + "/") for name in payloads), "payload outside fixed package")
    require(not ({REQUEST, APPROVAL, PROVENANCE} & (set(sources) | set(payloads))), "reserved transport file collision")
    require(set(files) == set(sources) | set(payloads) | {REQUEST, APPROVAL, PROVENANCE}, "transfer union differs")
    require(all(files[name] == item for mapping in (sources, payloads) for name, item in mapping.items()), "union descriptor differs")
    require(files[REQUEST]["sha256"] == record["request_sha256"] and files[APPROVAL]["sha256"] == record["approval_sha256"], "raw approval/request pin differs")
    require(files[REQUEST]["bytes"] <= MAX_JSON and files[APPROVAL]["bytes"] <= MAX_JSON, "control JSON bound")
    provenance = record["source_commit"] + "\tfalse\t" + stamp + "\n"
    require(record["provenance"] == provenance and files[PROVENANCE] == {"bytes": len(provenance.encode()), "sha256": sha(provenance.encode())}, "source provenance differs")
    require(record["order"] == expected_order(files), "transfer order differs")
    require(type(record["file_count"]) is int and record["file_count"] == len(files)
            and type(record["total_bytes"]) is int and record["total_bytes"] == sum(item["bytes"] for item in files.values()), "transfer totals differ")
    require(type(record["file_modes"]) is dict and set(record["file_modes"]) == set(files)
            and all(type(mode) is int and mode in (0o600, 0o700) for mode in record["file_modes"].values()), "private file modes differ")
    for name in files:
        parts = name.split("/")
        require(all("/".join(parts[:index]) not in files for index in range(1, len(parts))), "file/directory prefix collision")
    return record


def validate_control(record, request_raw, approval_raw):
    for name, raw in ((REQUEST, request_raw), (APPROVAL, approval_raw)):
        require({"bytes": len(raw), "sha256": sha(raw)} == record["files"][name], "control bytes changed")
    request, approval = decode(request_raw), decode(approval_raw)
    require(request.get("schema") == "peano-hydra-frontier-training-resource-request-v1"
            and request.get("status") == "ready-for-explicit-resource-approval"
            and request.get("profile") == PROFILE and request.get("run_id") == RUN_ID
            and request.get("source_commit") == record["source_commit"], "request identity differs")
    require(request.get("source_files") == record["source_files"] and request.get("payloads") == record["payloads"]
            and request.get("payloads_sha256") == sha(canonical(record["payloads"])), "request closed inventories differ")
    require(request.get("reservations") == {"train": {"seconds": 7200, "gpus": 1, "cpus": 8, "memory_gib": 64}}
            and request.get("maximum_aggregate_gpu_seconds") == 7200 and request.get("maximum_concurrent_gpus") == 1
            and request.get("automatic_retry") is False and request.get("resume") is False
            and request.get("refunds") is False and "evaluation" not in request, "request resource scope differs")
    require(set(approval) == {"schema", "profile", "run_id", "approved", "approval_reference", "request_file_sha256"}
            and approval["schema"] == "peano-hydra-frontier-training-resource-approval-v1"
            and approval["profile"] == PROFILE and approval["run_id"] == RUN_ID
            and approval["approved"] is True and approval["request_file_sha256"] == record["request_sha256"]
            and type(approval["approval_reference"]) is str and 1 <= len(approval["approval_reference"]) <= 2048,
            "exact supplied resource approval missing")
    return request, approval


def directory(path):
    require(type(path) is str and path.startswith("/") and ".." not in path.split("/"), "absolute directory required")
    parts = path.split("/")[1:]
    require(all(parts) and len(parts) <= 64, "directory components")
    # Match the frozen search_launch.directory contract: Linux ancestors need
    # search permission, not directory-list permission. The leaf stays readable.
    access = getattr(os, "O_PATH", os.O_RDONLY) if sys.platform == "linux" else os.O_RDONLY
    fd = os.open("/", access | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for index, part in enumerate(parts, 1):
            flags = os.O_RDONLY if index == len(parts) else access
            child = os.open(part, flags | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
        result, fd = fd, -1
        return result
    finally:
        if fd >= 0:
            os.close(fd)


def identity(info):
    return (info.st_dev, info.st_ino, info.st_mode, info.st_nlink, info.st_size,
            info.st_mtime_ns, info.st_ctime_ns)


class Tree:
    def __init__(self, path):
        self.path = path
        self.fd = directory(path)
        self.root_identity = (os.fstat(self.fd).st_dev, os.fstat(self.fd).st_ino)

    def close(self):
        os.close(self.fd)

    def anchored(self):
        other = directory(self.path)
        try:
            info = os.fstat(other)
            require((info.st_dev, info.st_ino) == self.root_identity, "root directory replaced")
        finally:
            os.close(other)

    def parent(self, name):
        relative(name)
        fd = os.dup(self.fd)
        try:
            for part in name.split("/")[:-1]:
                child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                os.close(fd)
                fd = child
            result, fd = fd, -1
            return result
        finally:
            if fd >= 0:
                os.close(fd)

    def open_file(self, name):
        parent = self.parent(name)
        try:
            fd = os.open(name.split("/")[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        finally:
            os.close(parent)
        info = os.fstat(fd)
        if not (stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and 0 <= info.st_size <= MAX_FILE):
            os.close(fd)
            raise ValueError("bounded single-link regular file required: " + name)
        return fd, identity(info)

    def fingerprint(self, name, retain=False):
        self.anchored()
        fd, before = self.open_file(name)
        chunks, count, hasher = [], 0, hashlib.sha256()
        try:
            while True:
                block = os.read(fd, 65536)
                if not block:
                    break
                count += len(block)
                require(count <= MAX_FILE, "file grew past cap")
                hasher.update(block)
                if retain:
                    chunks.append(block)
            require(identity(os.fstat(fd)) == before, "file changed during read")
        finally:
            os.close(fd)
        check, after = self.open_file(name)
        os.close(check)
        require(before == after, "path changed during read")
        self.anchored()
        return {"bytes": count, "sha256": hasher.hexdigest()}, (b"".join(chunks) if retain else None), before

    def files(self):
        result, stack, entries = set(), [("", os.dup(self.fd))], 0
        try:
            while stack:
                prefix, fd = stack.pop()
                try:
                    for part in os.listdir(fd):
                        name = prefix + part
                        relative(name)
                        entries += 1
                        require(entries <= MAX_FILES * 3, "directory entry bound")
                        info = os.stat(part, dir_fd=fd, follow_symlinks=False)
                        if stat.S_ISDIR(info.st_mode):
                            stack.append((name + "/", os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)))
                        else:
                            require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1, "link or special file in tree")
                            result.add(name)
                            require(len(result) <= MAX_FILES, "tree file bound")
                finally:
                    os.close(fd)
            self.anchored()
            return result
        finally:
            for _, fd in stack:
                os.close(fd)


def exact(stream, count):
    chunks, remaining = [], count
    while remaining:
        block = stream.read(min(65536, remaining))
        require(bool(block), "truncated transfer stream")
        chunks.append(block)
        remaining -= len(block)
    return b"".join(chunks)


def create_directories(tree, names):
    directories = set()
    for name in names:
        parts = name.split("/")
        directories.update("/".join(parts[:index]) for index in range(1, len(parts)))
    require(len(directories) <= MAX_FILES * 2, "new directory count bound")
    for name in sorted(directories, key=lambda item: (item.count("/"), item)):
        parent = tree.parent(name)
        try:
            os.mkdir(name.split("/")[-1], 0o700, dir_fd=parent)
        finally:
            os.close(parent)
    tree.anchored()


def write_stream_file(tree, name, pin, mode, stream):
    parent = tree.parent(name)
    fd = -1
    try:
        fd = os.open(name.split("/")[-1], os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                     mode, dir_fd=parent)
        opened = os.fstat(fd)
        require(stat.S_ISREG(opened.st_mode) and opened.st_nlink == 1, "created file identity")
        remaining, hasher = pin["bytes"], hashlib.sha256()
        while remaining:
            block = exact(stream, min(65536, remaining))
            hasher.update(block)
            view = memoryview(block)
            while view:
                count = os.write(fd, view)
                require(count > 0, "short file write")
                view = view[count:]
            remaining -= len(block)
        require(hasher.hexdigest() == pin["sha256"], "received file SHA differs: " + name)
        os.fsync(fd)
        actual = os.stat(name.split("/")[-1], dir_fd=parent, follow_symlinks=False)
        require((actual.st_dev, actual.st_ino) == (opened.st_dev, opened.st_ino)
                and actual.st_size == pin["bytes"] and stat.S_IMODE(actual.st_mode) == mode, "written path changed")
    finally:
        if fd >= 0:
            os.close(fd)
        os.close(parent)
    tree.anchored()


def receive(stream, expected_inventory_sha256, progress):
    import io
    require(type(expected_inventory_sha256) is str and HEX.fullmatch(expected_inventory_sha256), "external inventory SHA")
    require(exact(stream, len(MAGIC)) == MAGIC, "stream magic differs")
    length = struct.unpack(">Q", exact(stream, 8))[0]
    require(0 < length <= MAX_JSON, "inventory frame bound")
    raw = exact(stream, length)
    require(sha(raw) == expected_inventory_sha256, "external inventory bytes differ")
    record = validate_inventory(decode(raw))
    progress.update(inventory_sha256=sha(raw), source_commit=record["source_commit"],
                    request_sha256=record["request_sha256"], approval_sha256=record["approval_sha256"])
    controls = {name: exact(stream, record["files"][name]["bytes"]) for name in (REQUEST, APPROVAL)}
    validate_control(record, controls[REQUEST], controls[APPROVAL])
    parent_path, leaf = REMOTE_ROOT.rsplit("/", 1)
    parent = Tree(parent_path)
    try:
        parent.anchored()
        os.mkdir(leaf, 0o700, dir_fd=parent.fd)  # no existing destination, of any kind, can pass
        progress["destination_created"] = True
        made = os.stat(leaf, dir_fd=parent.fd, follow_symlinks=False)
        tree = Tree(REMOTE_ROOT)
        try:
            require((made.st_dev, made.st_ino) == tree.root_identity, "fresh destination replaced")
            create_directories(tree, record["files"])
            for name in record["order"]:
                source = io.BytesIO(controls[name]) if name in controls else stream
                write_stream_file(tree, name, record["files"][name], record["file_modes"][name], source)
                progress["files_written"] += 1
                progress["bytes_written"] += record["files"][name]["bytes"]
            require(stream.read(1) == b"", "unexpected trailing stream bytes")
            require(tree.files() == set(record["files"]), "destination is not the exact file inventory")
            for name, pin in record["files"].items():
                actual, _, info = tree.fingerprint(name)
                require(actual == pin and stat.S_IMODE(info[2]) == record["file_modes"][name], "post-copy bytes/mode differ")
            require(tree.fingerprint(PROVENANCE, retain=True)[1] == record["provenance"].encode(), "post-copy provenance differs")
            tree.anchored()
            parent.anchored()
            os.fsync(tree.fd)
        finally:
            tree.close()
        os.fsync(parent.fd)
    finally:
        parent.close()
    return {"status": "transferred-and-rehashed", "file_count": record["file_count"],
            "total_bytes": record["total_bytes"], "exact_inventory_checked": True,
            "all_file_hashes_rechecked": True, "source_provenance": record["provenance"]}


def main():
    require(sys.flags.isolated and sys.dont_write_bytecode, "isolated no-bytecode Python required")
    require(len(sys.argv) == 2, "one external inventory SHA required")
    os.umask(0o077)
    resource.setrlimit(resource.RLIMIT_CPU, (45, 45))
    resource.setrlimit(resource.RLIMIT_AS, (320 * 1024**2, 320 * 1024**2))
    resource.setrlimit(resource.RLIMIT_FSIZE, (MAX_FILE, MAX_FILE))
    def deadline(signum, frame):
        raise TimeoutError("remote receiver 55-second wall deadline")
    signal.signal(signal.SIGALRM, deadline)
    signal.alarm(55)
    result = {"schema": "peano-hydra-frontier-training-transfer-remote-result-v2", "started_at_utc": utc(),
              "remote_root": REMOTE_ROOT, "destination_created": False, "files_written": 0,
              "bytes_written": 0, "job_submission_performed": False, "installation_performed": False,
              "automatic_retry": False, "partial_outputs_preserved": True}
    code = 2
    try:
        result.update(receive(sys.stdin.buffer, sys.argv[1], result))
        code = 0
    except BaseException as error:
        result.update(status="failed-partial-output-preserved", error=(type(error).__name__ + ": " + str(error))[:2000])
    finally:
        signal.alarm(0)
        result["finished_at_utc"] = utc()
        print(json.dumps(result, sort_keys=True, allow_nan=False), flush=True)
    raise SystemExit(code)
