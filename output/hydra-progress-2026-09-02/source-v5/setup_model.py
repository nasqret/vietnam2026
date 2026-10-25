#!/usr/bin/env python3
"""Stream one exact public base checkpoint into a fresh local MLX 4-bit model.

--plan is read-only and imports no numerical framework. --convert is explicit,
requires externally supplied source/requirements pins, and never installs
packages. It makes one HTTP request (bounded HTTPS redirects only), never saves
the original checkpoint, never resumes, and preserves an unsuccessful attempt.
The caller must additionally own this process and observe its actual exit.
"""
from __future__ import annotations

import time
STARTED = time.monotonic()
import argparse
import ctypes
import gc
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import resource
import signal
import ssl
import stat
import struct
import sys
import urllib.parse
import urllib.request

HERE = Path(__file__).absolute().parent
SCRIPT = HERE / "setup_model.py"
REQUIREMENTS = HERE / "setup-requirements.txt"
RUNTIME = HERE / ".runtime"
VENV = RUNTIME / "venv"
STAGING = RUNTIME / "model-staging-01"
MODEL = RUNTIME / "model"
ATTEMPT = RUNTIME / "setup-attempt-01"
SCHEMA = "hydra-playground-local-quantized-model-v1"
MODEL_ID = "Qwen/Qwen3-1.7B-Base"
REVISION = "ea980cb0a6c2ae4b936e82123acc929f1cec04c1"
ORIGINAL_BYTES = 3_441_185_608
ORIGINAL_SHA = "6df85b39330e5a425ee36253d0f894e4387e4f0a15b9c53cb467d668e6b3a841"
URL = f"https://huggingface.co/{MODEL_ID}/resolve/{REVISION}/model.safetensors?download=true"
QUANTIZATION = {"bits": 4, "group_size": 64, "mode": "affine"}
TOKENIZER_MANIFEST = HERE.parent / "artifacts/hydra-retention-pilot-2026-08-30/tokenizer-runtime-02.json"
TOKENIZER_MANIFEST_SHA = "19d2d4e42ad2eaa49f4371c7403336d79eb5046ec086df6932b82508210f055b"
ASSETS = {
    "config.json": (727, "1bb33a92c3548fbc68b889b490e810440435253598835bd71dff0396060c12db"),
    "generation_config.json": (138, "8c970692323e3ea0e9b8b0a4dca79388d31226e41f83c9fd6014804280ebf6e8"),
    "merges.txt": (1671853, "8831e4f1a044471340f7c0a83d7bd71306a5b867e95fd870f74d0c5308a904d5"),
    "tokenizer.json": (7031645, "c0382117ea329cdf097041132f6d735924b697924d6f6fc3945713e96ce87539"),
    "tokenizer_config.json": (9678, "3c04ed3ca964ea2f6b2b5faf0dc4d31aec1cb1e8b4bcf63f402d295046b422b5"),
    "vocab.json": (2776833, "ca10d7e9fb3ed18575dd1e277a2579c16d108e32f27439684afa0e10b1440910"),
}
PACKAGES = {
    "certifi": "2025.7.14", "charset-normalizer": "3.4.2", "filelock": "3.18.0",
    "fsspec": "2025.5.1", "hf-xet": "1.1.5", "huggingface-hub": "0.33.4",
    "idna": "3.10", "jinja2": "3.1.6", "markupsafe": "3.0.2",
    "mlx": "0.29.4", "mlx-metal": "0.29.4", "mlx-lm": "0.28.3",
    "numpy": "2.3.1", "packaging": "25.0", "pip": "25.0.1",
    "protobuf": "5.29.5", "pyyaml": "6.0.2", "regex": "2024.11.6",
    "requests": "2.32.4", "safetensors": "0.5.3", "setuptools": "78.1.0",
    "tokenizers": "0.21.2", "tqdm": "4.67.1", "transformers": "4.53.3",
    "typing-extensions": "4.14.1", "urllib3": "2.5.0",
}
LIMITS = {
    "cpu_seconds": 600, "wall_seconds": 900,
    "observed_peak_rss_bytes": 4 * 1024**3,
    "network_body_bytes": 6_000_000_000,
    "new_runtime_bytes": 3 * 1024**3 // 2,
    "minimum_free_disk_bytes": 3 * 1024**3 // 2,
    "maximum_raw_tensor_bytes": 151936 * 2048 * 2,
    "maximum_header_bytes": 256 * 1024,
    "maximum_model_output_bytes": 1_020_000_000,
    "maximum_file_bytes": 256 * 1024**2,
    "maximum_json_bytes": 2 * 1024**2,
    "maximum_stdout_bytes": 256 * 1024,
    "maximum_runtime_entries": 20000,
    "https_redirects": 4, "socket_timeout_seconds": 30,
}
CHUNK = 1024 * 1024
OUTPUT_BYTES = 0


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                      allow_nan=False).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def descriptor(raw):
    return {"bytes": len(raw), "sha256": sha(raw)}


def decode(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "duplicate JSON key")
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite JSON")))


def directory(path):
    path = Path(path)
    require(path.is_absolute() and path.resolve() == path, "physical absolute directory required")
    return os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)


def fresh_directory(path):
    parent = directory(path.parent)
    try:
        os.mkdir(path.name, 0o700, dir_fd=parent)
        fd = os.open(path.name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
        os.fsync(parent)
        return fd
    finally:
        os.close(parent)


def fingerprint(path, maximum, budget=None, retain=False):
    path = Path(path)
    parent = directory(path.parent)
    try:
        fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        try:
            before = os.fstat(fd)
            require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1
                    and 0 <= before.st_size <= maximum, "bounded single-link regular file required")
            digest, count, chunks = hashlib.sha256(), 0, []
            while True:
                if budget:
                    budget.check()
                part = os.read(fd, min(CHUNK, maximum + 1 - count))
                if not part:
                    break
                count += len(part)
                require(count <= maximum, "file exceeds byte bound")
                digest.update(part)
                if retain:
                    chunks.append(part)
            after = os.fstat(fd)
            observed = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
            fields = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns, s.st_nlink)
            require(fields(before) == fields(after) == fields(observed) and count == before.st_size,
                    "file changed during read")
            return {"bytes": count, "sha256": digest.hexdigest()}, b"".join(chunks) if retain else None
        finally:
            os.close(fd)
    finally:
        os.close(parent)


def tree_identity(root, *, hash_files=False, budget=None):
    fd = directory(root)
    os.close(fd)
    files, logical, allocated, count = {}, 0, 0, 0
    for parent, dirs, names in os.walk(root, followlinks=False):
        dirs.sort()
        names.sort()
        for name in (*dirs, *names):
            path = Path(parent) / name
            item = path.lstat()
            count += 1
            require(count <= LIMITS["maximum_runtime_entries"], "runtime entry cap")
            logical += 0 if stat.S_ISDIR(item.st_mode) else item.st_size
            allocated += item.st_blocks * 512
            require(max(logical, allocated) <= LIMITS["new_runtime_bytes"], "runtime disk cap")
            relative = path.relative_to(root).as_posix()
            if stat.S_ISLNK(item.st_mode):
                require(relative in {"bin/python", "bin/python3", "bin/python3.11",
                                     "venv/bin/python", "venv/bin/python3", "venv/bin/python3.11"},
                        "unexpected runtime symlink")
                files[relative] = {"symlink": os.readlink(path)}
            elif stat.S_ISDIR(item.st_mode):
                continue
            else:
                require(stat.S_ISREG(item.st_mode) and item.st_nlink == 1, "unsafe runtime entry")
                if hash_files:
                    files[relative] = fingerprint(path, LIMITS["maximum_file_bytes"], budget)[0]
        if budget:
            budget.check(refresh=False)
    return {"logical_bytes": logical, "allocated_bytes": allocated, "entries": count,
            "files_sha256": sha(canonical(files)) if hash_files else None}


class Budget:
    def __init__(self):
        self.last_scan = 0.0
        self.base_disk = self.written = 0
        self.network_bytes = 0
        self.minimum_free = None
        self.peak_disk = 0

    def check(self, write_bytes=0, *, refresh=True, tail=False):
        usage = resource.getrusage(resource.RUSAGE_SELF)
        cpu = usage.ru_utime + usage.ru_stime
        wall = time.monotonic() - STARTED
        require(cpu < LIMITS["cpu_seconds"] - (10 if tail else 0), "conversion CPU deadline")
        require(wall < LIMITS["wall_seconds"] - (30 if tail else 0), "conversion wall deadline")
        require(usage.ru_maxrss <= LIMITS["observed_peak_rss_bytes"], "conversion observed RSS cap")
        require(self.network_bytes <= LIMITS["network_body_bytes"], "conversion network cap")
        disk = os.statvfs(HERE)
        free = disk.f_bavail * disk.f_frsize
        self.minimum_free = free if self.minimum_free is None else min(self.minimum_free, free)
        require(free >= LIMITS["minimum_free_disk_bytes"] + write_bytes, "free disk reserve")
        if refresh and time.monotonic() - self.last_scan >= 1:
            # No numerical framework or installer may write concurrently here.
            identity = tree_identity(RUNTIME)
            self.base_disk = max(identity["logical_bytes"], identity["allocated_bytes"])
            self.written = 0
            self.last_scan = time.monotonic()
        self.peak_disk = max(self.peak_disk, self.base_disk + self.written)
        require(self.base_disk + self.written + write_bytes <= LIMITS["new_runtime_bytes"],
                "all-new runtime disk cap")

    def measurements(self):
        usage = resource.getrusage(resource.RUSAGE_SELF)
        return {"cpu_seconds": usage.ru_utime + usage.ru_stime,
                "wall_seconds": time.monotonic() - STARTED, "observed_peak_rss_bytes": usage.ru_maxrss,
                "network_body_bytes": self.network_bytes, "minimum_observed_free_disk_bytes": self.minimum_free,
                "maximum_accounted_runtime_bytes": self.peak_disk}


def emit(value):
    global OUTPUT_BYTES
    raw = canonical(value) + b"\n"
    OUTPUT_BYTES += len(raw)
    require(OUTPUT_BYTES <= LIMITS["maximum_stdout_bytes"], "setup output cap")
    sys.stdout.buffer.write(raw)
    sys.stdout.buffer.flush()


def write_chunks(path, chunks, total, budget):
    require(type(total) is int and 0 <= total <= LIMITS["maximum_file_bytes"], "output file cap")
    budget.check(write_bytes=total + 8192)
    parent = directory(path.parent)
    digest, count = hashlib.sha256(), 0
    try:
        fd = os.open(path.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=parent)
        budget.written += 8192  # Conservative inode/block overhead until next scan.
        try:
            for chunk in chunks:
                view = memoryview(chunk).cast("B")
                offset = 0
                while offset < len(view):
                    part = view[offset:offset + CHUNK]
                    budget.check(write_bytes=len(part))
                    written = os.write(fd, part)
                    require(written > 0, "short output write")
                    digest.update(part[:written])
                    offset += written
                    count += written
                    budget.written += written
                    require(count <= total, "output exceeded declared bytes")
            require(count == total and os.fstat(fd).st_size == total, "output size mismatch")
            os.fsync(fd)
        finally:
            os.close(fd)
        os.fsync(parent)
    finally:
        os.close(parent)
    expected = {"bytes": count, "sha256": digest.hexdigest()}
    require(fingerprint(path, total, budget)[0] == expected, "written output failed readback")
    return expected


def write_json(path, value, budget):
    raw = canonical(value) + b"\n"
    require(len(raw) <= LIMITS["maximum_json_bytes"], "metadata byte cap")
    return write_chunks(path, (raw,), len(raw), budget)


def expected_tensors():
    result = {"model.embed_tokens.weight": [151936, 2048], "model.norm.weight": [2048]}
    projections = {"q_proj": [2048, 2048], "k_proj": [1024, 2048],
                   "v_proj": [1024, 2048], "o_proj": [2048, 2048]}
    for layer in range(28):
        prefix = f"model.layers.{layer}."
        for name, shape in projections.items():
            result[prefix + "self_attn." + name + ".weight"] = shape
        for name in ("q_norm", "k_norm"):
            result[prefix + "self_attn." + name + ".weight"] = [128]
        for name in ("gate_proj", "up_proj"):
            result[prefix + "mlp." + name + ".weight"] = [6144, 2048]
        result[prefix + "mlp.down_proj.weight"] = [2048, 6144]
        for name in ("input_layernorm", "post_attention_layernorm"):
            result[prefix + name + ".weight"] = [2048]
    return result


def parse_header(raw):
    require(0 < len(raw) <= LIMITS["maximum_header_bytes"], "safetensors header cap")
    value = decode(raw)
    require(type(value) is dict, "safetensors header must be an object")
    metadata = value.pop("__metadata__", {})
    require(type(metadata) is dict and all(type(k) is str and type(v) is str for k, v in metadata.items()),
            "invalid safetensors metadata")
    expected = expected_tensors()
    require(set(value) == set(expected) and len(value) == 310, "exact Qwen3-1.7B-Base tensor inventory required")
    rows = []
    for name, item in value.items():
        require(type(item) is dict and set(item) == {"dtype", "shape", "data_offsets"}
                and item["dtype"] == "BF16" and item["shape"] == expected[name],
                "unexpected original tensor name/dtype/shape")
        shape, offsets = item["shape"], item["data_offsets"]
        require(all(type(n) is int and n > 0 for n in shape)
                and type(offsets) is list and len(offsets) == 2
                and all(type(n) is int and n >= 0 for n in offsets), "invalid tensor bounds")
        size = math.prod(shape) * 2
        require(0 < size <= LIMITS["maximum_raw_tensor_bytes"] and offsets[1] - offsets[0] == size,
                "raw tensor allocation bound")
        rows.append({"name": name, "shape": shape, "bytes": size, "start": offsets[0], "end": offsets[1]})
    rows.sort(key=lambda row: row["start"])
    cursor = 0
    for row in rows:
        require(row["start"] == cursor, "tensor offsets overlap or contain holes")
        cursor = row["end"]
    require(cursor + len(raw) + 8 == ORIGINAL_BYTES, "original tensor extent differs from pinned file")
    return rows


class Stream:
    def __init__(self, response, budget):
        self.response, self.budget = response, budget
        self.digest = hashlib.sha256()
        self.count = 0

    def read_exact(self, count):
        require(type(count) is int and 0 < count <= LIMITS["maximum_raw_tensor_bytes"],
                "bounded raw allocation required")
        self.budget.check(tail=True)
        result = bytearray(count)
        cursor = 0
        while cursor < count:
            self.budget.check(tail=True)
            part = self.response.read(min(CHUNK, count - cursor))
            require(bool(part), "original HTTP stream ended early")
            cursor += len(part)
            require(cursor <= count and self.count + len(part) <= ORIGINAL_BYTES, "oversized HTTP body")
            result[cursor - len(part):cursor] = part
            self.digest.update(part)
            self.count += len(part)
            self.budget.network_bytes += len(part)
        return result


class Redirects(urllib.request.HTTPRedirectHandler):
    def __init__(self):
        self.count = 0

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        self.count += 1
        parsed = urllib.parse.urlsplit(newurl)
        host = parsed.hostname or ""
        require(self.count <= LIMITS["https_redirects"] and parsed.scheme == "https"
                and parsed.port in (None, 443) and not parsed.username and not parsed.password
                and (host == "huggingface.co" or host.endswith(".hf.co")),
                "unapproved public checkpoint redirect")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def save_arrays(path, arrays, mx, np, budget):
    """Write standard safetensors through an exclusive, no-follow descriptor."""
    mx.eval(*arrays.values())
    host, header, cursor = {}, {"__metadata__": {"format": "mlx"}}, 0
    for name in sorted(arrays):
        value = arrays[name]
        if value.dtype == mx.uint32:
            dtype, array = "U32", np.asarray(value)
            require(array.dtype == np.dtype("uint32"), "quantized weight dtype changed")
        else:
            require(value.dtype == mx.bfloat16, "vectors/scales/biases must retain explicit BF16")
            dtype, array = "BF16", np.asarray(value.view(mx.uint16))
            require(array.dtype == np.dtype("uint16"), "BF16 bit view changed")
        array = np.ascontiguousarray(array)
        host[name] = array
        header[name] = {"dtype": dtype, "shape": list(value.shape),
                        "data_offsets": [cursor, cursor + array.nbytes]}
        cursor += array.nbytes
    raw = canonical(header)
    raw += b" " * (-len(raw) % 8)
    prefix = struct.pack("<Q", len(raw)) + raw
    item = write_chunks(path, (part for part in (prefix, *(host[k] for k in sorted(host)))),
                        len(prefix) + cursor, budget)
    return item, cursor, sorted(arrays)


def convert_tensor(path, name, shape, raw, mx, np, budget):
    source = np.frombuffer(raw, dtype="<u2").reshape(shape)
    value = mx.array(source, dtype=mx.uint16).view(mx.bfloat16)
    if len(shape) == 2:
        weight, scales, biases = mx.quantize(value, group_size=64, bits=4, mode="affine", stream=mx.cpu)
        require(weight.dtype == mx.uint32 and scales.dtype == biases.dtype == mx.bfloat16,
                "unexpected MLX affine output dtype")
        require(list(weight.shape) == [shape[0], shape[1] // 8]
                and list(scales.shape) == list(biases.shape) == [shape[0], shape[1] // 64],
                "unexpected MLX affine output shape")
        arrays = {name: weight, name.removesuffix(".weight") + ".scales": scales,
                  name.removesuffix(".weight") + ".biases": biases}
    else:
        arrays = {name: value}
    # Eager materialization is mandatory before saving or releasing the input.
    mx.eval(*arrays.values())
    budget.check(tail=True)
    return save_arrays(path, arrays, mx, np, budget)


def package_identity(budget):
    require(Path(sys.prefix).resolve() == VENV and sys.version_info[:2] == (3, 11),
            "run conversion with the fresh configured Python3.11 virtual environment")
    versions = {}
    for distribution in importlib.metadata.distributions():
        name = distribution.metadata["Name"].lower().replace("_", "-")
        require(name not in versions, "duplicate installed package")
        versions[name] = distribution.version
    require(versions == PACKAGES, "runtime packages differ from the exact reviewed versions")
    tree = tree_identity(VENV, hash_files=True, budget=budget)
    return {"versions": versions, "runtime_prefix": str(VENV), **tree}


def tokenizer_reference(budget=None):
    item, raw = fingerprint(TOKENIZER_MANIFEST, 2 * 1024**2, budget, retain=True)
    require(item["sha256"] == TOKENIZER_MANIFEST_SHA, "authentic preserved tokenizer reference changed")
    record = decode(raw)
    require(record["model_id"] == MODEL_ID and record["revision"] == REVISION,
            "tokenizer reference belongs to another base")
    for name, (size, digest) in ASSETS.items():
        require(record["tokenizer_files"][name]["bytes"] == size
                and record["tokenizer_files"][name]["sha256"] == digest, "base tokenizer pin changed")
    return record, {"path": str(TOKENIZER_MANIFEST), **item}


def publish_exclusive_directory(source, destination):
    """Darwin's RENAME_EXCL atomically publishes without replacing any target."""
    require(sys.platform == "darwin" and source.parent == destination.parent, "fixed same-filesystem publication required")
    parent = directory(source.parent)
    try:
        libc = ctypes.CDLL(None, use_errno=True)
        rename = libc.renameatx_np
        rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
        rename.restype = ctypes.c_int
        if rename(parent, os.fsencode(source.name), parent, os.fsencode(destination.name), 0x00000004) != 0:
            code = ctypes.get_errno()
            raise OSError(code, os.strerror(code))
        os.fsync(parent)
    finally:
        os.close(parent)


def proposal():
    arrays = expected_tensors()
    output_bytes = sum(math.prod(shape) * 9 // 16 if len(shape) == 2 else math.prod(shape) * 2
                       for shape in arrays.values())
    return {"schema": "hydra-playground-local-model-setup-plan-v1",
            "original_model": {"model_id": MODEL_ID, "revision": REVISION,
                               "bytes": ORIGINAL_BYTES, "sha256": ORIGINAL_SHA},
            "public_url": URL, "quantization": QUANTIZATION, "vectors_dtype": "bfloat16",
            "raw_tensor_count": len(arrays), "quantized_matrix_count": sum(len(s) == 2 for s in arrays.values()),
            "predicted_tensor_data_bytes": output_bytes,
            "tokenizer_asset_bytes": sum(x[0] for x in ASSETS.values()),
            "packages": PACKAGES, "limits": LIMITS,
            "converter": {"path": str(SCRIPT), **fingerprint(SCRIPT, 128 * 1024)[0]},
            "requirements": {"path": str(REQUIREMENTS), **fingerprint(REQUIREMENTS, 65536)[0]},
            "output_directory": str(MODEL), "staging_directory": str(STAGING),
            "attempt_directory": str(ATTEMPT), "automatic_retry": False,
            "original_checkpoint_saved": False, "training_performed": False,
            "model_inference_performed": False, "numerical_equivalence_to_training": False,
            "completion_requires": "successful setup output plus the caller-observed actual process exit zero"}


def convert(args):
    require(sys.platform == "darwin" and platform.machine() == "arm64" and sys.byteorder == "little",
            "reviewed Apple silicon host required")
    require(sys.flags.isolated and sys.dont_write_bytecode and HERE.resolve() == HERE
            and not any(k.startswith(("SLURM_", "SBATCH_", "DYLD_", "LD_")) for k in os.environ),
            "isolated bytecode-free local process required")
    resource.setrlimit(resource.RLIMIT_CPU, (600, 600))
    resource.setrlimit(resource.RLIMIT_FSIZE, (LIMITS["maximum_file_bytes"], LIMITS["maximum_file_bytes"]))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError("setup900-second deadline")))
    signal.setitimer(signal.ITIMER_REAL, max(.001, 900 - (time.monotonic() - STARTED)))
    plan = proposal()
    require(plan["converter"]["sha256"] == args.expected_helper_sha256
            and plan["requirements"]["sha256"] == args.expected_requirements_sha256,
            "actual converter/requirements differ from external pins")
    os.close(directory(VENV))
    for path in (MODEL, STAGING, ATTEMPT):
        require(not os.path.lexists(path), "setup destination or attempt already exists; no resume/overwrite")
    budget = Budget()
    budget.check(write_bytes=LIMITS["maximum_model_output_bytes"])
    reference, reference_pin = tokenizer_reference(budget)
    python_pin = fingerprint(Path(sys.executable).resolve(), 2 * 1024**2, budget)[0]
    require(python_pin["sha256"] == reference["python"]["sha256"], "configured interpreter bytes changed")
    dependencies = package_identity(budget)
    os.close(fresh_directory(ATTEMPT))
    os.close(fresh_directory(STAGING))
    write_json(ATTEMPT / "started.json", {"status": "started", "plan": plan,
               "tokenizer_reference": reference_pin, "dependencies": dependencies,
               "python": {"path": str(Path(sys.executable).resolve()), **python_pin}}, budget)
    files, weight_map = {}, {}
    stream, completed = None, 0
    try:
        # Only numerical arrays are used here: no language-model construction.
        import mlx.core as mx
        import numpy as np
        mx.set_default_device(mx.cpu)
        mx.set_cache_limit(0)
        mx.set_memory_limit(3 * 1024**3)
        probe = np.arange(128, dtype=np.float32).reshape(2, 64)
        probe_bits = (probe.view(np.uint32) >> 16).astype(np.uint16)
        probe_pin, _, _ = convert_tensor(ATTEMPT / "api-probe.safetensors", "probe.weight", [2, 64],
                                         bytearray(probe_bits.tobytes()), mx, np, budget)
        loaded = mx.load(str(ATTEMPT / "api-probe.safetensors"))
        mx.eval(*loaded.values())
        require(set(loaded) == {"probe.weight", "probe.scales", "probe.biases"}
                and loaded["probe.weight"].dtype == mx.uint32
                and loaded["probe.scales"].dtype == loaded["probe.biases"].dtype == mx.bfloat16,
                "actual installed MLX could not read the bounded probe")
        del loaded, probe, probe_bits
        gc.collect()
        mx.clear_cache()
        original_config = None
        for name, (size, digest) in ASSETS.items():
            raw_pin, raw = fingerprint(Path(reference["tokenizer_files"][name]["resolved_path"]), size, budget, retain=True)
            require(raw_pin == {"bytes": size, "sha256": digest}, "preserved authentic tokenizer bytes changed")
            output_name = "original-config.json" if name == "config.json" else name
            files[output_name] = write_chunks(STAGING / output_name, (raw,), size, budget)
            if name == "config.json":
                original_config = decode(raw)
            del raw
        require(original_config["model_type"] == "qwen3" and original_config["hidden_size"] == 2048
                and original_config["num_hidden_layers"] == 28 and original_config["tie_word_embeddings"] is True
                and original_config["torch_dtype"] == "bfloat16"
                and "quantization" not in original_config and "quantization_config" not in original_config,
                "unexpected pinned base configuration")
        config = {**original_config, "quantization": QUANTIZATION, "quantization_config": QUANTIZATION}
        files["config.json"] = write_json(STAGING / "config.json", config, budget)
        import certifi
        redirects = Redirects()
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), redirects,
            urllib.request.HTTPSHandler(context=ssl.create_default_context(cafile=certifi.where())))
        request = urllib.request.Request(URL, headers={"Accept-Encoding": "identity",
                                                     "User-Agent": "Hydra-local-exact-base-converter/1"})
        budget.check(tail=True)
        with opener.open(request, timeout=LIMITS["socket_timeout_seconds"]) as response:
            require(response.status == 200 and response.headers.get("Content-Encoding", "identity") == "identity",
                    "full unencoded original checkpoint response required")
            length = response.headers.get("Content-Length")
            require(length is None or int(length) == ORIGINAL_BYTES, "HTTP checkpoint size changed")
            stream = Stream(response, budget)
            header_size = struct.unpack("<Q", stream.read_exact(8))[0]
            require(0 < header_size <= LIMITS["maximum_header_bytes"], "upstream header exceeds cap")
            header_raw = stream.read_exact(header_size)
            tensors = parse_header(header_raw)
            original_header = descriptor(header_raw)
            del header_raw
            total_tensor_bytes = 0
            for number, tensor in enumerate(tensors, 1):
                raw = stream.read_exact(tensor["bytes"])
                filename = f"model-{number:05d}-of-{len(tensors):05d}.safetensors"
                item, tensor_bytes, keys = convert_tensor(STAGING / filename, tensor["name"], tensor["shape"],
                                                          raw, mx, np, budget)
                files[filename] = item
                total_tensor_bytes += tensor_bytes
                for key in keys:
                    require(key not in weight_map, "duplicate output weight key")
                    weight_map[key] = filename
                # Do not retain any raw buffer, float array, or lazy graph.
                del raw
                gc.collect()
                mx.clear_cache()
                completed = number
                budget.check(tail=True)
                if number == 1 or number % 20 == 0 or number == len(tensors):
                    emit({"status": "converting", "tensors": number, "total_tensors": len(tensors),
                          "original_bytes_received": stream.count})
            extra = response.read(1)
            budget.network_bytes += len(extra)
            require(not extra and stream.count == ORIGINAL_BYTES and stream.digest.hexdigest() == ORIGINAL_SHA,
                    "full original checkpoint SHA256/length verification failed")
        require(total_tensor_bytes == plan["predicted_tensor_data_bytes"], "converted tensor size changed")
        index = {"metadata": {"total_size": total_tensor_bytes,
                              "total_parameters": sum(math.prod(t["shape"]) for t in tensors)},
                 "weight_map": dict(sorted(weight_map.items()))}
        files["model.safetensors.index.json"] = write_json(STAGING / "model.safetensors.index.json", index, budget)
        require(sum(x["bytes"] for x in files.values()) <= LIMITS["maximum_model_output_bytes"],
                "quantized model output cap")
        require(set(p.name for p in STAGING.iterdir()) == set(files), "unexpected staging output")
        for name, item in files.items():
            require(fingerprint(STAGING / name, LIMITS["maximum_file_bytes"], budget)[0] == item,
                    "quantized file failed whole-directory readback")
        require(package_identity(budget) == dependencies, "installed dependency bytes changed during conversion")
        require(proposal() == plan and tokenizer_reference(budget)[1] == reference_pin,
                "converter/requirements/reference changed during conversion")
        budget.check(refresh=True, tail=True)
        manifest = {"schema": SCHEMA, "status": "complete", "original_model": plan["original_model"],
            "quantization": QUANTIZATION, "vectors_dtype": "bfloat16",
            "files": dict(sorted(files.items())), "original_config": {"path": "original-config.json", **files["original-config.json"]},
            "original_header": original_header, "converter": plan["converter"], "requirements": plan["requirements"],
            "dependencies": dependencies, "python": {"path": str(Path(sys.executable).resolve()), **python_pin},
            "tokenizer_reference": reference_pin, "api_probe": probe_pin,
            "input_tensors": len(tensors), "quantized_matrices": 197, "output_tensors": len(weight_map),
            "tensor_data_bytes": total_tensor_bytes, "limits": LIMITS, "measurements_before_publication": budget.measurements(),
            "full_original_sha256_verified": True, "all_output_files_rehashed": True,
            "raw_checkpoint_saved": False, "automatic_retry": False, "training_performed": False,
            "model_inference_performed": False, "conversion_device": "cpu",
            "numerical_equivalence_to_training": False,
            "claim_boundary": "Exact original download verified; lossy local quantization, not numerical or benchmark equivalence.",
            "resource_measurement": "Process rusage plus checks before/after bounded I/O; no control over unrelated disk writers."}
        manifest_pin = write_json(STAGING / "manifest.json", manifest, budget)
        budget.check(tail=True)
        publish_exclusive_directory(STAGING, MODEL)
        result = {"status": "complete", "manifest": {"path": str(MODEL / "manifest.json"), **manifest_pin},
                  "measurements": budget.measurements(), "automatic_retry": False}
        write_json(ATTEMPT / "result.json", result, budget)
        emit(result)
        budget.check()
        signal.setitimer(signal.ITIMER_REAL, 0)
        return 0
    except BaseException as failure:
        result = {"status": "failed-no-automatic-retry", "error": type(failure).__name__ + ": " + str(failure)[:1200],
                  "completed_tensors": completed, "original_bytes_received": stream.count if stream else 0,
                  "measurements": budget.measurements(), "partial_files_preserved": True,
                  "automatic_retry": False, "model_inference_performed": False, "raw_checkpoint_saved": False}
        try:
            write_json(ATTEMPT / "failure.json", result, budget)
            emit(result)
        except BaseException:
            pass
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--plan", action="store_true")
    mode.add_argument("--convert", action="store_true")
    parser.add_argument("--expected-helper-sha256")
    parser.add_argument("--expected-requirements-sha256")
    args = parser.parse_args()
    if args.plan:
        require(args.expected_helper_sha256 is None and args.expected_requirements_sha256 is None,
                "plan mode does not accept conversion authorization pins")
        emit(proposal())
        return 0
    for value in (args.expected_helper_sha256, args.expected_requirements_sha256):
        require(type(value) is str and len(value) == 64 and all(c in "0123456789abcdef" for c in value),
                "conversion requires both externally reviewed raw SHA256 pins")
    return convert(args)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, RuntimeError, TimeoutError, ImportError, KeyError, TypeError, KeyboardInterrupt) as exc:
        print("setup-model: " + type(exc).__name__ + ": " + " ".join(str(exc).split())[:1200], file=sys.stderr)
        raise SystemExit(2)
