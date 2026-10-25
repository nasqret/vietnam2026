"""Nonlaunching retention bootstrap receiver; definitions until explicit main().

This distinct recovery transfer includes finalized evaluation controls and genuine
admission/preflight records. It never runs them or authorizes compute. Only a
fresh fixed destination is written. Standard-library framing, gzip and file-copy only: no subprocess, imported received source, model, installer,
scheduler, overwrite, deletion, retry, or synthetic compute approval.
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

REMOTE_ROOT = "/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/retention-evaluation-recovery-v1"
LOCAL_ROOT = "/Users/bnaskrecki/codex/peano/_deploy/hydra-retention-evaluation-recovery-execution-20260831"
ARCHIVE_ROOT = "/Users/bnaskrecki/codex/peano/artifacts/hydra-retention-evaluation-recovery-2026-08-31"
HOST = "plgnasqret@helios.cyfronet.pl"
PROFILE = "peano-hydra-retention-evaluation-recovery-v1"
RUN_ID = "retention-evaluation-recovery-v1"
PACKAGE = "_deploy/hydra-retention-evaluation-recovery-v1"
AUTHORITY = PACKAGE + "/authority.json"
FREEZE_RECEIPT = "_deploy/hydra-retention-evaluation-recovery-execution-freeze.json"
ORIGIN_MANIFEST = "_deploy/hydra-retention-evaluation-recovery-source.json"
PROVENANCE = ".peano-source-provenance.tsv"
REMOTE_RECEIPT = ".peano-retention-evaluation-recovery-transfer-receipt.json"
BUNDLE_NAME = "retention-evaluation-recovery-source-inputs-01.tar.gz"
DIRECTIVE_SHA = "04ac3b5997b4f2a78c4ce41642b9e596d63abf1c82ec2441ab240b0f78fd5778"
FORBIDDEN_CONTROLS = frozenset(("token-preflight.json", "train-request.json"))
MAX_FILES = 2048
MAX_FILE = 64 * 1024**2
MAX_TOTAL = 256 * 1024**2
MAX_BUNDLE = 64 * 1024**2
MAX_JSON = 1024**2
MAX_FREEZE = 2 * 1024**2
MAX_AUTHORITY = 16384
MAX_HEADER = 65536
MAX_PROVENANCE = 1024
MAX_PREFIX = MAX_HEADER + MAX_JSON + MAX_FREEZE + MAX_AUTHORITY + 128
MAGIC = b"HYDRA-RETENTION-EVALUATION-RECOVERY-TRANSFER-V1\n"
HEX = re.compile(r"[0-9a-f]{64}\Z")
OID = re.compile(r"[0-9a-f]{40}\Z")
FORBIDDEN = frozenset((".git", ".cache", ".venv", "__pycache__", "node_modules",
                       "results", "logs", "checkpoints", "id_rsa", "id_ed25519",
                       "credentials.json", "secrets.json", "auth.json"))
LIMITS = {"remote_cpu_seconds":45, "remote_wall_seconds":55,
          "remote_address_space_bytes":320 * 1024**2,
          "remote_max_file_bytes":MAX_FILE, "remote_max_files":MAX_FILES,
          "remote_max_installed_bytes":MAX_TOTAL,
          "maximum_compressed_bytes":MAX_BUNDLE,
          "maximum_remote_receipt_bytes":MAX_JSON,
          "ssh_wall_seconds":60, "ssh_stdout_bytes":65536, "ssh_stderr_bytes":65536,
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


def decode(raw, maximum=MAX_JSON):
    require(type(raw) is bytes and 0 < len(raw) <= maximum, "JSON byte bound")
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



def descriptor(item, *, mode=True, maximum=MAX_FILE):
    fields = {"bytes", "sha256", "mode"} if mode else {"bytes", "sha256"}
    require(type(item) is dict and set(item) == fields
            and type(item["bytes"]) is int and 0 <= item["bytes"] <= maximum
            and type(item["sha256"]) is str and HEX.fullmatch(item["sha256"]),
            "bounded raw descriptor required")
    if mode:
        require(item["mode"] in ("0600", "0644", "0700", "0755"), "unsafe declared file mode")
    return item


def validate_plan(raw, expected_sha):
    require(type(expected_sha) is str and HEX.fullmatch(expected_sha)
            and sha(raw) == expected_sha, "external raw transfer-plan pin changed")
    plan = decode(raw)
    fields = {"schema", "status", "profile", "run_id", "source_root", "source_commit",
              "destination_directory", "destination_host", "freeze_receipt", "source_files",
              "source_files_sha256", "bootstrap_files", "bootstrap_files_sha256", "selected_files",
              "selected_files_sha256", "file_count", "selected_uncompressed_bytes", "bundle",
              "directive_sha256", "maximum_installed_files", "maximum_installed_bytes",
              "model_weights_in_bundle", "resource_request_in_bundle", "approval_in_bundle",
              "gpu_job_submitted", "native_or_model_work_performed", "remote_transfer_performed",
              "automatic_retry", "resume", "limits"}
    require(set(plan) == fields and plan["schema"] == "peano-hydra-retention-evaluation-recovery-transfer-plan-v1"
            and plan["status"] == "prepared-evaluation-recovery-local-only"
            and plan["profile"] == PROFILE and plan["run_id"] == RUN_ID
            and plan["source_root"] == LOCAL_ROOT
            and type(plan["source_commit"]) is str and OID.fullmatch(plan["source_commit"])
            and plan["destination_directory"] == REMOTE_ROOT and plan["destination_host"] == HOST
            and plan["directive_sha256"] == DIRECTIVE_SHA and plan["limits"] == LIMITS,
            "bootstrap transfer plan scope changed")
    for key in ("model_weights_in_bundle", "gpu_job_submitted",
                "native_or_model_work_performed", "remote_transfer_performed", "automatic_retry", "resume"):
        require(plan[key] is False, "bootstrap cannot authorize compute or retry: " + key)
    bundle = plan["bundle"]
    require(type(bundle) is dict and set(bundle) == {"path", "bytes", "sha256"}
            and bundle["path"] == ARCHIVE_ROOT + "/" + BUNDLE_NAME, "fixed bundle path required")
    descriptor({k:bundle[k] for k in ("bytes", "sha256")}, mode=False, maximum=MAX_BUNDLE)
    require(bundle["bytes"] > 0, "empty compressed bundle")
    files, sources, bootstrap = plan["selected_files"], plan["source_files"], plan["bootstrap_files"]
    require(all(type(value) is dict and value for value in (files, sources, bootstrap))
            and type(plan["file_count"]) is int and 0 < len(files) == plan["file_count"] <= MAX_FILES - 2
            and not set(sources).intersection(bootstrap), "bounded disjoint source/bootstrap inventory required")
    require(files == {**sources, **bootstrap}, "tar must equal the exact source and bootstrap union")
    total = 0
    for name, item in files.items():
        relative(name)
        descriptor(item)
        require(name not in (PROVENANCE, REMOTE_RECEIPT)
                and name.rsplit("/", 1)[-1] not in FORBIDDEN_CONTROLS,
                "training controls or generated remote metadata cannot enter this recovery transfer")
        require((name.startswith(PACKAGE + "/")) == (name in bootstrap), "source/package partition changed")
        total += item["bytes"]
        parts = name.split("/")
        require(all("/".join(parts[:i]) not in files for i in range(1, len(parts))),
                "selected file/directory prefix collision")
    for key in ("source_files", "bootstrap_files", "selected_files"):
        require(plan[key + "_sha256"] == sha(canonical(plan[key])), "inventory digest changed: " + key)
    require(type(plan["selected_uncompressed_bytes"]) is int
            and total == plan["selected_uncompressed_bytes"]
            and type(plan["maximum_installed_files"]) is int
            and plan["maximum_installed_files"] == len(files) + 2 <= MAX_FILES
            and type(plan["maximum_installed_bytes"]) is int
            and plan["maximum_installed_bytes"] == total + MAX_PROVENANCE + MAX_JSON <= MAX_TOTAL,
            "bootstrap aggregate file/byte bound changed")
    required_controls = {PACKAGE + '/' + name for name in
        ('resource-request.json', 'approval.json', 'inputs.json', 'admission.json',
         'evaluate-request.json', 'preflight.json', 'evaluation-plan.json')}
    require(plan['resource_request_in_bundle'] is True and plan['approval_in_bundle'] is True
            and required_controls <= set(bootstrap),
            'this new transfer requires complete frozen evaluation controls and actual admission/preflight files')
    require(AUTHORITY in bootstrap and bootstrap[AUTHORITY]["sha256"] == DIRECTIVE_SHA
            and 0 < bootstrap[AUTHORITY]["bytes"] <= MAX_AUTHORITY,
            "actual standing directive is required; no compute approval substitution")
    freeze = plan["freeze_receipt"]
    require(type(freeze) is dict and set(freeze) == {"path", "bytes", "sha256"}
            and freeze["path"] == FREEZE_RECEIPT and FREEZE_RECEIPT in sources
            and ORIGIN_MANIFEST in sources, "actual frozen-source receipts are required")
    descriptor({k:freeze[k] for k in ("bytes", "sha256")}, mode=False, maximum=MAX_FREEZE)
    require(0 < freeze["bytes"] and {k:sources[FREEZE_RECEIPT][k] for k in ("bytes", "sha256")}
            == {k:freeze[k] for k in ("bytes", "sha256")}, "freeze receipt pin differs from tar")
    return plan


def validate_freeze(plan, raw):
    pin = plan["freeze_receipt"]
    require(len(raw) == pin["bytes"] and sha(raw) == pin["sha256"], "raw freeze receipt changed")
    frozen = decode(raw, MAX_FREEZE)
    require(frozen.get("schema") == "peano-hydra-retention-evaluation-recovery-source-freeze-v1"
            and frozen.get("status") == "complete" and frozen.get("snapshot_root") == LOCAL_ROOT
            and frozen.get("git_commit") == plan["source_commit"]
            and frozen.get("snapshot_clean") is True
            and frozen.get("all_selected_files_and_jobs_committed") is True
            and frozen.get("all_declared_ancillary_files_committed") is True
            and frozen.get("source_bytes_unchanged") is True
            and frozen.get("data_bytes_unchanged") is True,
            "completed genuine frozen-source receipt required")
    declared = frozen.get("files")
    require(type(declared) is dict and declared and len(declared) <= MAX_FILES - 4
            and frozen.get("files_sha256") == sha(canonical(declared))
            and type(frozen.get("file_count")) is int and frozen["file_count"] == len(declared),
            "frozen source inventory changed")
    joined = {}
    for name, item in declared.items():
        relative(name)
        require(type(item) is dict and set(item) == {"bytes", "sha256", "mode", "git_blob"}
                and item["mode"] in ("100644", "100755")
                and type(item["git_blob"]) is str and OID.fullmatch(item["git_blob"]),
                "frozen Git source descriptor changed")
        joined[name] = {"bytes":item["bytes"], "sha256":item["sha256"], "mode":"0" + item["mode"][-3:]}
        descriptor(joined[name])
    require(frozen.get("total_bytes") == sum(item["bytes"] for item in joined.values()),
            "frozen total bytes changed")
    origin = frozen.get("origin_source_manifest")
    require(type(origin) is dict and set(origin) == {"path", "bytes", "sha256"}
            and origin["path"] == ORIGIN_MANIFEST, "frozen origin-source receipt changed")
    descriptor({k:origin[k] for k in ("bytes", "sha256")}, mode=False, maximum=MAX_JSON)
    require(FREEZE_RECEIPT not in joined and ORIGIN_MANIFEST not in joined
            and {k:plan["source_files"][ORIGIN_MANIFEST][k] for k in ("bytes", "sha256")}
            == {k:origin[k] for k in ("bytes", "sha256")}, "origin-source raw identity changed")
    joined[ORIGIN_MANIFEST] = plan["source_files"][ORIGIN_MANIFEST]
    joined[FREEZE_RECEIPT] = plan["source_files"][FREEZE_RECEIPT]
    require(joined == plan["source_files"], "transfer source closure differs from actual freeze")
    return frozen


def validate_authority(plan, raw):
    require(0 < len(raw) <= MAX_AUTHORITY and sha(raw) == DIRECTIVE_SHA
            and len(raw) == plan["bootstrap_files"][AUTHORITY]["bytes"], "actual standing directive changed")
    decode(raw, MAX_AUTHORITY)


def validate_header(header, plan=None):
    fields = {"schema", "plan_sha256", "plan_bytes", "directive_sha256", "source_commit",
              "local_source_clean", "send_started_at_utc", "sender_sha256", "receiver_sha256", "limits"}
    require(type(header) is dict and set(header) == fields
            and header["schema"] == "peano-hydra-retention-evaluation-recovery-transfer-header-v1"
            and type(header["plan_bytes"]) is int and 0 < header["plan_bytes"] <= MAX_JSON
            and header["directive_sha256"] == DIRECTIVE_SHA
            and type(header["source_commit"]) is str and OID.fullmatch(header["source_commit"])
            and header["local_source_clean"] is True and header["limits"] == LIMITS,
            "bootstrap send header changed")
    for name in ("plan_sha256", "sender_sha256", "receiver_sha256"):
        require(type(header[name]) is str and HEX.fullmatch(header[name]), "raw helper/plan identity required")
    stamp = header["send_started_at_utc"]
    require(type(stamp) is str and re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", stamp),
            "actual send UTC timestamp required")
    datetime.datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ")
    if plan is not None:
        require(header["source_commit"] == plan["source_commit"], "source/header identity differs")
    return header


class LimitedBundle:
    """Hash exactly the approved compressed body without retaining it in memory."""
    def __init__(self, stream, bundle):
        self.stream, self.count, self.hasher = stream, 0, hashlib.sha256()
        self.bundle = bundle
    def read(self, count=-1):
        remaining = self.bundle["bytes"] - self.count
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


def consume_tar(stream, files, consume, bundle):
    """Bounded exact USTAR framing; never call an archive extraction API."""
    limited = LimitedBundle(stream, bundle)
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
    require(limited.count == bundle["bytes"] and limited.hasher.hexdigest() == bundle["sha256"],
            "compressed tar raw identity changed")
    return {"compressed_bytes":limited.count, "compressed_sha256":limited.hasher.hexdigest(),
            "expanded_tar_bytes":expected_tar_bytes}


def receipt_record(plan, header, header_sha, stamp, provenance, archive_result):
    """Pure expected durable record; shared by sender and fixed receiver."""
    files = {name:{"bytes":item["bytes"], "sha256":item["sha256"]}
             for name, item in plan["selected_files"].items()}
    files[PROVENANCE] = {"bytes":len(provenance), "sha256":sha(provenance)}
    modes = {name:(0o700 if int(item["mode"], 8) & 0o111 else 0o600)
             for name, item in plan["selected_files"].items()}
    modes[PROVENANCE] = 0o600
    return {
        "schema":"peano-hydra-retention-evaluation-recovery-transfer-receipt-v1", "status":"transferred-and-rehashed",
        "profile":PROFILE, "run_id":RUN_ID, "remote_root":REMOTE_ROOT,
        "plan_sha256":header["plan_sha256"], "header_sha256":header_sha,
        "source_root":LOCAL_ROOT, "source_commit":plan["source_commit"], "local_source_clean":True,
        "freeze_receipt":plan["freeze_receipt"], "directive_sha256":DIRECTIVE_SHA,
        "source_files_sha256":plan["source_files_sha256"],
        "bootstrap_files_sha256":plan["bootstrap_files_sha256"],
        "selected_files_sha256":plan["selected_files_sha256"],
        "sender_sha256":header["sender_sha256"], "receiver_sha256":header["receiver_sha256"],
        "transfer_started_at_utc":stamp, "source_provenance":provenance.decode("ascii"),
        "source_provenance_sha256":sha(provenance), "bundle":archive_result,
        "files":files, "files_sha256":sha(canonical(files)),
        "private_modes":{name:format(mode, "04o") for name, mode in modes.items()},
        "file_count":len(files), "total_bytes":sum(item["bytes"] for item in files.values()),
        "receipt_excluded_from_own_inventory":True,
        "exact_inventory_checked":True, "all_file_hashes_rechecked":True,
        "resource_request_present":True, "approval_present":True,
        "job_submission_performed":False, "installation_performed":False,
        "model_loaded":False, "native_work_performed":False,
        "external_remote_source_and_model_inputs_verified":False,
        "automatic_retry":False, "resume":False, "limits":LIMITS,
    }


def receive(stream, expected_header_sha, progress):
    require(type(expected_header_sha) is str and HEX.fullmatch(expected_header_sha), "external send-header SHA required")
    require(exact(stream, len(MAGIC)) == MAGIC, "transfer framing magic changed")
    length = struct.unpack(">Q", exact(stream, 8))[0]
    require(0 < length <= MAX_HEADER, "send-header byte bound")
    raw = exact(stream, length)
    require(sha(raw) == expected_header_sha, "send-header raw pin changed")
    header = validate_header(decode(raw))
    plan_raw = exact(stream, header["plan_bytes"])
    plan = validate_plan(plan_raw, header["plan_sha256"])
    validate_header(header, plan)
    freeze_raw = exact(stream, plan["freeze_receipt"]["bytes"])
    authority_raw = exact(stream, plan["bootstrap_files"][AUTHORITY]["bytes"])
    validate_freeze(plan, freeze_raw)
    validate_authority(plan, authority_raw)
    stamp = utc()
    provenance = (plan["source_commit"] + "\tfalse\t" + stamp + "\n").encode("ascii")
    require(len(provenance) <= MAX_PROVENANCE, "actual provenance byte cap")
    files = {name:{"bytes":item["bytes"], "sha256":item["sha256"]}
             for name, item in plan["selected_files"].items()}
    files[PROVENANCE] = {"bytes":len(provenance), "sha256":sha(provenance)}
    modes = {name:(0o700 if int(item["mode"], 8) & 0o111 else 0o600)
             for name, item in plan["selected_files"].items()}
    modes[PROVENANCE] = 0o600
    progress.update(header_sha256=sha(raw), transfer_started_at_utc=stamp,
                    source_commit=plan["source_commit"], plan_sha256=header["plan_sha256"],
                    directive_sha256=DIRECTIVE_SHA)
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
                require(progress["files_written"] <= plan["file_count"]
                        and progress["bytes_written"] <= plan["selected_uncompressed_bytes"],
                        "selected write cap exceeded")
            archive_result = consume_tar(stream, plan["selected_files"], consume, plan["bundle"])
            require(stream.read(1) == b"", "trailing wire bytes")
            write_stream_file(tree, PROVENANCE, files[PROVENANCE], 0o600, io.BytesIO(provenance))
            progress["files_written"] += 1
            progress["bytes_written"] += len(provenance)
            require(tree.files() == set(files), "destination input inventory changed")
            for name, item in files.items():
                actual, _, info = tree.fingerprint(name)
                require(actual == item and stat.S_IMODE(info[2]) == modes[name],
                        "installed bytes or private mode changed: " + name)
            require(tree.fingerprint(PROVENANCE, retain=True)[1] == provenance
                    and tree.fingerprint(AUTHORITY, retain=True)[1] == authority_raw
                    and tree.fingerprint(FREEZE_RECEIPT, retain=True)[1] == freeze_raw,
                    "installed source/directive/provenance metadata changed")
            durable = receipt_record(plan, header, sha(raw), stamp, provenance, archive_result)
            receipt_raw = canonical(durable) + b"\n"
            require(len(receipt_raw) <= MAX_JSON
                    and len(files) + 1 == plan["maximum_installed_files"]
                    and durable["total_bytes"] + len(receipt_raw) <= plan["maximum_installed_bytes"],
                    "durable receipt exceeds installed bounds")
            receipt_pin = {"bytes":len(receipt_raw), "sha256":sha(receipt_raw)}
            write_stream_file(tree, REMOTE_RECEIPT, receipt_pin, 0o600, io.BytesIO(receipt_raw))
            progress["files_written"] += 1
            progress["bytes_written"] += len(receipt_raw)
            require(tree.files() == set(files) | {REMOTE_RECEIPT}
                    and tree.fingerprint(REMOTE_RECEIPT)[0] == receipt_pin,
                    "final bootstrap receipt/inventory changed")
            tree.anchored()
            parent.anchored()
            os.fsync(tree.fd)
        finally:
            tree.close()
        os.fsync(parent.fd)
    finally:
        parent.close()
    return {"status":"transferred-and-rehashed", "file_count":len(files)+1,
            "total_bytes":durable["total_bytes"]+len(receipt_raw),
            "input_file_count":len(files), "input_total_bytes":durable["total_bytes"],
            "exact_inventory_checked":True, "all_file_hashes_rechecked":True,
            "files_sha256":durable["files_sha256"], "bundle":archive_result,
            "source_files_sha256":plan["source_files_sha256"],
            "bootstrap_files_sha256":plan["bootstrap_files_sha256"],
            "source_provenance":provenance.decode("ascii"), "source_provenance_sha256":sha(provenance),
            "remote_receipt":{"path":REMOTE_RECEIPT, **receipt_pin},
            "resource_request_present":True, "approval_present":True,
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
        raise TimeoutError("remote retention bootstrap receiver55-second wall deadline")
    signal.signal(signal.SIGALRM, deadline)
    signal.alarm(55)
    started = time.monotonic()
    result = {"schema":"peano-hydra-retention-evaluation-recovery-transfer-remote-result-v1", "started_at_utc":utc(),
              "remote_root":REMOTE_ROOT, "destination_created":False,
              "files_written":0, "bytes_written":0, "limits":LIMITS,
              "job_submission_performed":False, "installation_performed":False,
              "model_loaded":False, "native_work_performed":False, "automatic_retry":False,
              "partial_outputs_preserved":True}
    code = 2
    try:
        result.update(receive(sys.stdin.buffer, sys.argv[1], result))
        usage = resource.getrusage(resource.RUSAGE_SELF)
        require(time.monotonic()-started < 55 and usage.ru_utime+usage.ru_stime < 45
                and usage.ru_maxrss * (1 if sys.platform == "darwin" else 1024) <= 320 * 1024**2,
                "receiver final wall/CPU/RSS boundary reached")
        code = 0
    except BaseException as error:
        result.update(status="failed-partial-output-preserved", error=(type(error).__name__ + ": " + str(error))[:2000])
    finally:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        result.update(finished_at_utc=utc(), wall_seconds=time.monotonic()-started,
                      cpu_seconds=usage.ru_utime+usage.ru_stime,
                      peak_rss_bytes=int(usage.ru_maxrss * (1 if sys.platform == "darwin" else 1024)))
        raw = canonical(result)
        require(len(raw) <= 65536, "receiver output byte bound")
        print(raw.decode("utf-8"), flush=True)
        signal.alarm(0)
    raise SystemExit(code)
