"""Fixed diagnostic receiver; definitions only until explicitly invoked.

Standard-library metadata/decompression/file-copy only. Uses the successful
training receiver v2 directory anchoring and exclusive write implementation.
Only a fresh fixed destination is written; no subprocess, received-source
import, model load, installer, scheduler call, overwrite, deletion or retry.
"""
import datetime
import gzip
import hashlib
import io
import json
import os
import re
import resource
import signal
import stat
import struct
import sys
import time

REMOTE_ROOT = "/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/frontier-diagnostic-v1"
LOCAL_ROOT = "/Users/bnaskrecki/codex/peano/_deploy/hydra-model-test-execution-20260830"
PROFILE = "peano-hydra-frontier-diagnostic-v1"
RUN_ID = "frontier-diagnostic-v1"
PACKAGE = "_deploy/hydra-frontier-diagnostic-v1"
REQUEST = PACKAGE + "/resource-request.json"
APPROVAL = PACKAGE + "/approval.json"
PROVENANCE = ".peano-source-provenance.tsv"
SOURCE_COMMIT = "612d1ea9e4905dfe2af104696924a19bc5883752"
PLAN_SHA = "49b74b02f9a3186149a42a08657904215d5be7652f9e592a861c715fbddd47c5"
PLAN_BYTES = 176847
REQUEST_SHA = "49117e3c7d62f9fd50931a84abfcbf3ce2c24d50fff672ae78d7b526c7b5354b"
REQUEST_BYTES = 136415
APPROVAL_SHA = "10873068c69239375587420c47194efd09895006a3b6ef719c513860eacdc66e"
APPROVAL_BYTES = 627
DIRECTIVE_SHA = "04ac3b5997b4f2a78c4ce41642b9e596d63abf1c82ec2441ab240b0f78fd5778"
BUNDLE_SHA = "5c4947ae1a84855334a5a57becaa78ea915ed03e8166465cab0d9ac1ffc9b8b7"
BUNDLE_BYTES = 14264369
SELECTED_FILES = 890
SELECTED_BYTES = 97723530
MAX_FILES = 892
MAX_FILE = 64 * 1024**2
MAX_TOTAL = 97728650
MAX_JSON = 1024**2
MAX_HEADER = 65536
MAX_APPROVAL = 4096
MAX_PROVENANCE = 1024
MAGIC = b"HYDRA-DIAGNOSTIC-TAR-TRANSFER-V1\n"
HEX = re.compile(r"[0-9a-f]{64}\Z")
FORBIDDEN = frozenset((".git", ".cache", ".venv", "__pycache__", "node_modules",
                       "results", "logs", "checkpoints", "id_rsa", "id_ed25519",
                       "credentials.json", "secrets.json", "auth.json"))
LIMITS = {"remote_cpu_seconds":45, "remote_wall_seconds":55,
          "remote_address_space_bytes":320 * 1024**2,
          "remote_max_file_bytes":MAX_FILE, "remote_max_files":MAX_FILES,
          "remote_max_selected_bytes":MAX_TOTAL, "ssh_wall_seconds":60,
          "ssh_stdout_bytes":65536, "ssh_stderr_bytes":65536,
          "local_cpu_seconds":60, "local_wall_seconds":90,
          "local_checked_rss_bytes":512 * 1024**2,
          "receipt_file_bytes":4 * 1024**2, "automatic_retry":False}

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



def validate_plan(raw):
    require(len(raw) == PLAN_BYTES and sha(raw) == PLAN_SHA, "pinned transfer plan changed")
    plan = decode(raw)
    require(plan.get("schema") == "peano-hydra-diagnostic-transfer-plan-v1"
            and plan.get("source_root") == LOCAL_ROOT and plan.get("source_commit") == SOURCE_COMMIT
            and plan.get("destination_directory") == REMOTE_ROOT
            and plan.get("destination_host") == "plgnasqret@helios.cyfronet.pl"
            and plan.get("resource_request_sha256") == REQUEST_SHA
            and plan.get("file_count") == SELECTED_FILES
            and plan.get("selected_uncompressed_bytes") == SELECTED_BYTES
            and plan.get("maximum_selected_bytes_including_controls") == MAX_TOTAL
            and plan.get("model_weights_in_bundle") is False
            and plan.get("approval_in_bundle") is False
            and plan.get("automatic_retry") is False, "transfer plan scope changed")
    bundle = plan.get("bundle", {})
    require(bundle.get("bytes") == BUNDLE_BYTES and bundle.get("sha256") == BUNDLE_SHA,
            "approved tar identity changed")
    files = plan.get("selected_files")
    require(type(files) is dict and len(files) == SELECTED_FILES
            and APPROVAL not in files and PROVENANCE not in files, "selected file inventory changed")
    total = 0
    for name, item in files.items():
        relative(name)
        require(type(item) is dict and set(item) == {"bytes", "sha256", "mode"}
                and type(item["bytes"]) is int and 0 <= item["bytes"] <= MAX_FILE
                and type(item["sha256"]) is str and HEX.fullmatch(item["sha256"])
                and item["mode"] in ("0644", "0755"), "selected descriptor changed")
        total += item["bytes"]
        parts = name.split("/")
        require(all("/".join(parts[:i]) not in files for i in range(1, len(parts))),
                "selected file/directory prefix collision")
    require(total == SELECTED_BYTES and files[REQUEST]["bytes"] == REQUEST_BYTES
            and files[REQUEST]["sha256"] == REQUEST_SHA, "selected totals or request changed")
    return plan


def validate_controls(plan, request_raw, approval_raw):
    require(len(request_raw) == REQUEST_BYTES and sha(request_raw) == REQUEST_SHA,
            "resource request raw bytes changed")
    require(len(approval_raw) == APPROVAL_BYTES and len(approval_raw) <= MAX_APPROVAL
            and sha(approval_raw) == APPROVAL_SHA, "explicit approval raw bytes changed")
    request, approval = decode(request_raw), decode(approval_raw)
    require(request.get("schema") == "peano-hydra-frontier-diagnostic-resource-request-v1"
            and request.get("status") == "ready-for-explicit-resource-approval"
            and request.get("profile") == PROFILE and request.get("run_id") == RUN_ID
            and request.get("source_commit") == SOURCE_COMMIT
            and request.get("reservations") == {"evaluate":{"seconds":900, "gpus":1, "cpus":8, "memory_gib":64}}
            and request.get("maximum_aggregate_gpu_seconds") == 900
            and request.get("maximum_concurrent_gpus") == 1
            and request.get("automatic_retry") is False and request.get("resume") is False
            and request.get("refunds") is False and request.get("training_authorized") is False
            and request.get("self_training_authorized") is False, "resource scope changed")
    sources, payloads = request.get("source_files"), request.get("payloads")
    require(type(sources) is dict and len(sources) == 877
            and type(payloads) is dict and len(payloads) == 12
            and not set(sources).intersection(payloads), "source/payload closure changed")
    selected = {name:{"bytes":item["bytes"], "sha256":item["sha256"]}
                for name, item in plan["selected_files"].items()}
    joined = dict(sources)
    joined.update(payloads)
    joined[REQUEST] = {"bytes":len(request_raw), "sha256":sha(request_raw)}
    require(selected == joined and request["payloads_sha256"] == sha(canonical(payloads)),
            "tar inventory differs from the approved request")
    require(set(approval) == {"schema", "profile", "run_id", "approved", "approval_reference", "request_file_sha256"}
            and approval["schema"] == "peano-hydra-frontier-diagnostic-resource-approval-v1"
            and approval["profile"] == PROFILE and approval["run_id"] == RUN_ID
            and approval["approved"] is True and approval["request_file_sha256"] == REQUEST_SHA
            and type(approval["approval_reference"]) is str
            and 1 <= len(approval["approval_reference"]) <= 2048
            and approval["approval_reference"].strip() == approval["approval_reference"],
            "actual exact resource approval missing")


def validate_header(header):
    fields = {"schema", "plan_sha256", "request_sha256", "approval_sha256", "directive_sha256",
              "source_commit", "local_source_clean", "send_started_at_utc",
              "sender_sha256", "receiver_sha256", "limits"}
    require(type(header) is dict and set(header) == fields
            and header["schema"] == "peano-hydra-diagnostic-transfer-header-v1"
            and header["plan_sha256"] == PLAN_SHA and header["request_sha256"] == REQUEST_SHA
            and header["approval_sha256"] == APPROVAL_SHA and header["directive_sha256"] == DIRECTIVE_SHA
            and header["source_commit"] == SOURCE_COMMIT and header["local_source_clean"] is True
            and header["limits"] == LIMITS, "send controls changed")
    for name in ("sender_sha256", "receiver_sha256"):
        require(type(header[name]) is str and HEX.fullmatch(header[name]), "helper identity required")
    stamp = header["send_started_at_utc"]
    require(type(stamp) is str and re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", stamp),
            "actual send UTC timestamp required")
    datetime.datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ")
    return header


class LimitedBundle:
    """Hash exactly the approved compressed body without retaining it in memory."""
    def __init__(self, stream):
        self.stream, self.count, self.hasher = stream, 0, hashlib.sha256()
    def read(self, count=-1):
        remaining = BUNDLE_BYTES - self.count
        if remaining == 0 or count == 0:
            return b""
        count = min(65536 if count < 0 else count, remaining)
        raw = self.stream.read(count)
        require(bool(raw), "truncated compressed tar")
        self.count += len(raw)
        self.hasher.update(raw)
        return raw
    def tell(self):
        return self.count
    def seekable(self):
        return False


def tar_text(field):
    first, separator, rest = field.partition(b"\0")
    require(not separator or not any(rest), "nonzero bytes after tar string terminator")
    return first.decode("ascii")


def tar_octal(field):
    raw = field.strip(b" \0")
    require(raw and len(raw) <= 12 and all(48 <= c <= 55 for c in raw), "non-octal tar number")
    return int(raw, 8)


def tar_member(header):
    require(len(header) == 512 and any(header), "missing expected tar member")
    require(tar_octal(header[148:156]) == sum(header[:148]) + 8 * 32 + sum(header[156:]),
            "tar header checksum changed")
    require(header[156:157] == b"0" and not any(header[157:257])
            and header[257:263] == b"ustar\0" and header[263:265] == b"00",
            "only ordinary USTAR files are accepted; no links, PAX or special entries")
    name, prefix = tar_text(header[:100]), tar_text(header[345:500])
    name = relative(prefix + "/" + name if prefix else name)
    return name, tar_octal(header[124:136]), tar_octal(header[100:108])


def consume_tar(stream, files, consume):
    """Bounded exact USTAR framing; never call an archive extraction API."""
    limited = LimitedBundle(stream)
    payload_blocks = sum(512 + ((item["bytes"] + 511) // 512) * 512 for item in files.values())
    expected_tar_bytes = ((payload_blocks + 1024 + 10239) // 10240) * 10240
    with gzip.GzipFile(fileobj=limited, mode="rb") as expanded:
        consumed = 0
        for expected_name in sorted(files):
            name, size, mode = tar_member(exact(expanded, 512))
            item = files[expected_name]
            require(name == expected_name and size == item["bytes"] and mode == int(item["mode"], 8),
                    "tar member order/name/size/mode differs from the pinned plan")
            consume(name, item, expanded)
            padding = (-size) % 512
            require(not any(exact(expanded, padding)), "tar file padding changed")
            consumed += 512 + size + padding
            require(consumed <= payload_blocks, "expanded tar exceeds selected member bound")
        require(consumed == payload_blocks, "expanded tar body length changed")
        tail = expected_tar_bytes - consumed
        require(1024 <= tail <= 11264 and not any(exact(expanded, tail)),
                "tar end records or padding changed")
        require(expanded.read(1) == b"", "extra decompressed tar data")
    require(limited.count == BUNDLE_BYTES and limited.hasher.hexdigest() == BUNDLE_SHA,
            "compressed tar raw identity changed")
    return {"compressed_bytes":limited.count, "compressed_sha256":limited.hasher.hexdigest(),
            "expanded_tar_bytes":expected_tar_bytes}


def receive(stream, expected_header_sha, progress):
    require(type(expected_header_sha) is str and HEX.fullmatch(expected_header_sha), "external send-header SHA required")
    require(exact(stream, len(MAGIC)) == MAGIC, "transfer framing magic changed")
    length = struct.unpack(">Q", exact(stream, 8))[0]
    require(0 < length <= MAX_HEADER, "send-header byte bound")
    raw = exact(stream, length)
    require(sha(raw) == expected_header_sha, "send-header raw pin changed")
    header = validate_header(decode(raw))
    plan = validate_plan(exact(stream, PLAN_BYTES))
    request_raw, approval_raw = exact(stream, REQUEST_BYTES), exact(stream, APPROVAL_BYTES)
    validate_controls(plan, request_raw, approval_raw)
    # The receiver creates this timestamp at the actual transfer. No local
    # source provenance file is fabricated during preparation.
    stamp = utc()
    provenance = (SOURCE_COMMIT + "\tfalse\t" + stamp + "\n").encode("ascii")
    require(len(provenance) <= MAX_PROVENANCE, "provenance byte cap")
    files = {name:{"bytes":item["bytes"], "sha256":item["sha256"]}
             for name, item in plan["selected_files"].items()}
    files[APPROVAL] = {"bytes":len(approval_raw), "sha256":sha(approval_raw)}
    files[PROVENANCE] = {"bytes":len(provenance), "sha256":sha(provenance)}
    require(len(files) == MAX_FILES and sum(item["bytes"] for item in files.values()) <= MAX_TOTAL,
            "installed file/byte limits changed")
    modes = {name:(0o700 if item["mode"] == "0755" else 0o600)
             for name, item in plan["selected_files"].items()}
    modes.update({APPROVAL:0o600, PROVENANCE:0o600})
    progress.update(header_sha256=sha(raw), transfer_started_at_utc=stamp, source_commit=SOURCE_COMMIT,
                    plan_sha256=PLAN_SHA, request_sha256=REQUEST_SHA, approval_sha256=APPROVAL_SHA)
    parent_path, leaf = REMOTE_ROOT.rsplit("/", 1)
    parent = Tree(parent_path)
    try:
        parent.anchored()
        os.mkdir(leaf, 0o700, dir_fd=parent.fd)
        progress["destination_created"] = True
        made = os.stat(leaf, dir_fd=parent.fd, follow_symlinks=False)
        tree = Tree(REMOTE_ROOT)
        try:
            require((made.st_dev, made.st_ino) == tree.root_identity, "fresh destination replaced")
            create_directories(tree, files)
            def consume(name, item, expanded):
                write_stream_file(tree, name, files[name], modes[name], expanded)
                progress["files_written"] += 1
                progress["bytes_written"] += item["bytes"]
                require(progress["files_written"] <= SELECTED_FILES
                        and progress["bytes_written"] <= SELECTED_BYTES, "selected write cap exceeded")
            archive_result = consume_tar(stream, plan["selected_files"], consume)
            require(stream.read(1) == b"", "trailing wire bytes")
            for name, payload in ((APPROVAL, approval_raw), (PROVENANCE, provenance)):
                write_stream_file(tree, name, files[name], modes[name], io.BytesIO(payload))
                progress["files_written"] += 1
                progress["bytes_written"] += len(payload)
            require(tree.files() == set(files), "destination file inventory changed")
            for name, pin in files.items():
                actual, _, info = tree.fingerprint(name)
                require(actual == pin and stat.S_IMODE(info[2]) == modes[name],
                        "installed bytes or private mode changed: " + name)
            require(tree.fingerprint(PROVENANCE, retain=True)[1] == provenance,
                    "installed provenance changed")
            tree.anchored()
            parent.anchored()
            os.fsync(tree.fd)
        finally:
            tree.close()
        os.fsync(parent.fd)
    finally:
        parent.close()
    return {"status":"transferred-and-rehashed", "file_count":len(files),
            "total_bytes":sum(item["bytes"] for item in files.values()),
            "exact_inventory_checked":True, "all_file_hashes_rechecked":True,
            "bundle":archive_result, "source_provenance":provenance.decode("ascii"),
            "source_provenance_sha256":sha(provenance),
            "mode_policy":"original executable status preserved with private0600/0700 permissions"}


def main():
    require(sys.flags.isolated and sys.dont_write_bytecode and len(sys.argv) == 2,
            "isolated no-bytecode Python and one external header SHA required")
    os.umask(0o077)
    resource.setrlimit(resource.RLIMIT_CPU, (45, 45))
    resource.setrlimit(resource.RLIMIT_AS, (320 * 1024**2, 320 * 1024**2))
    resource.setrlimit(resource.RLIMIT_FSIZE, (MAX_FILE, MAX_FILE))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    def deadline(signum, frame):
        raise TimeoutError("remote diagnostic receiver55-second wall deadline")
    signal.signal(signal.SIGALRM, deadline)
    signal.alarm(55)
    started = time.monotonic()
    result = {"schema":"peano-hydra-diagnostic-transfer-remote-result-v1", "started_at_utc":utc(),
              "remote_root":REMOTE_ROOT, "destination_created":False,
              "files_written":0, "bytes_written":0, "limits":LIMITS,
              "job_submission_performed":False, "installation_performed":False,
              "model_loaded":False, "automatic_retry":False, "partial_outputs_preserved":True}
    code = 2
    try:
        result.update(receive(sys.stdin.buffer, sys.argv[1], result))
        code = 0
    except BaseException as error:
        result.update(status="failed-partial-output-preserved", error=(type(error).__name__ + ": " + str(error))[:2000])
    finally:
        signal.alarm(0)
        usage = resource.getrusage(resource.RUSAGE_SELF)
        result.update(finished_at_utc=utc(), wall_seconds=time.monotonic()-started,
                      cpu_seconds=usage.ru_utime+usage.ru_stime,
                      peak_rss_bytes=int(usage.ru_maxrss * (1 if sys.platform == "darwin" else 1024)))
        raw = canonical(result)
        require(len(raw) <= 65536, "receiver output byte bound")
        print(raw.decode("utf-8"), flush=True)
    raise SystemExit(code)

