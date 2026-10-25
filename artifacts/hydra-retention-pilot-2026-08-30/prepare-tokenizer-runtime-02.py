"""Fetch only six public pinned tokenizer/config files into a new local cache.

This setup does not load a tokenizer, model, training input, or GPU framework.
The fresh environment was installed from tokenizer-runtime-requirements-02.txt.
Its exact installed files and the authentic revision cache are recorded here.
"""
import datetime
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import resource
import signal
import sys
import time

STARTED = time.monotonic()
ARCHIVE = Path('/Users/bnaskrecki/codex/peano/artifacts/hydra-retention-pilot-2026-08-30')
RUNTIME = Path('/private/tmp/hydra-retention-tokenizer-runtime-20260831-02')
CACHE = RUNTIME / 'hf-cache'
MODEL = 'Qwen/Qwen3-1.7B-Base'
REVISION = 'ea980cb0a6c2ae4b936e82123acc929f1cec04c1'
NAMES = ('config.json', 'generation_config.json', 'merges.txt', 'tokenizer.json', 'tokenizer_config.json', 'vocab.json')
RECEIPT = ARCHIVE / 'tokenizer-runtime-02.json'


def pin(path):
    size = path.stat().st_size
    assert size <= 64 * 1024**2, 'unexpected setup file size'
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return {'bytes': size, 'sha256': h.hexdigest()}


def main():
    assert sys.flags.isolated and sys.dont_write_bytecode and Path(sys.prefix) == RUNTIME
    assert not RECEIPT.exists() and not CACHE.exists(), 'no setup overwrite'
    resource.setrlimit(resource.RLIMIT_CPU, (60, 61))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    def stopped(*_):
        raise TimeoutError('tokenizer cache setup wall deadline')
    signal.signal(signal.SIGALRM, stopped)
    signal.alarm(180)
    os.environ['HF_HUB_DISABLE_IMPLICIT_TOKEN'] = '1'
    os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
    os.environ['HF_HUB_DISABLE_XET'] = '1'
    os.environ['HF_HUB_DISABLE_PROGRESS_BARS'] = '1'
    os.environ['HF_HOME'] = str(RUNTIME / 'hf-home')
    os.environ['HF_HUB_CACHE'] = str(CACHE)
    from huggingface_hub import hf_hub_download
    files = {}
    for name in NAMES:
        path = Path(hf_hub_download(MODEL, name, revision=REVISION, cache_dir=str(CACHE), token=False, etag_timeout=15))
        expected = CACHE / 'models--Qwen--Qwen3-1.7B-Base/snapshots' / REVISION / name
        assert path == expected and path.resolve().is_relative_to(CACHE.resolve())
        files[name] = {'path': str(path), 'resolved_path': str(path.resolve()), **pin(path)}
    site = RUNTIME / 'lib/python3.11/site-packages'
    packages = {d.metadata['Name'].lower().replace('_', '-'): d.version
                for d in importlib.metadata.distributions(path=[str(site)])}
    expected_packages = dict(line.strip().lower().split('==') for line in
                             (ARCHIVE / 'tokenizer-runtime-requirements-02.txt').read_text().splitlines() if line.strip())
    assert all(packages.get(name) == version for name, version in expected_packages.items())
    absent = ('torch', 'tensorflow', 'flax', 'jax', 'peft', 'accelerate', 'datasets', 'vllm')
    assert not (set(absent) & packages.keys())
    runtime_files = {}
    for path in sorted(site.rglob('*')):
        if '__pycache__' in path.parts or path.is_dir():
            continue
        assert path.is_file() and not path.is_symlink()
        runtime_files[path.relative_to(RUNTIME).as_posix()] = pin(path)
    python = Path(sys.executable).resolve(strict=True)
    value = {'schema': 'peano-hydra-retention-local-tokenizer-runtime-v1', 'status': 'ready',
        'created_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'runtime': str(RUNTIME), 'site_packages': str(site), 'cache_root': str(CACHE),
        'python': {'path': str(python), **pin(python)}, 'python_version': sys.version,
        'model_id': MODEL, 'revision': REVISION, 'requirements': {'path': str(ARCHIVE / 'tokenizer-runtime-requirements-02.txt'),
            **pin(ARCHIVE / 'tokenizer-runtime-requirements-02.txt')},
        'packages': packages, 'required_packages': expected_packages, 'runtime_files': runtime_files,
        'runtime_files_bytes': sum(v['bytes'] for v in runtime_files.values()),
        'tokenizer_files': files, 'public_download_allowlist': list(NAMES),
        'framework_packages_absent': list(absent), 'model_weights_downloaded': False,
        'tokenizer_loaded': False, 'gpu_allocated': False, 'project_data_uploaded': False,
        'setup_helper': {'path': str(Path(__file__)), **pin(Path(__file__))},
        'wall_seconds': time.monotonic() - STARTED}
    raw = (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()
    assert len(raw) <= 4 * 1024**2
    with RECEIPT.open('xb') as f:
        f.write(raw); f.flush(); os.fsync(f.fileno())
    print(json.dumps({'status': 'ready', 'receipt': {'path': str(RECEIPT), **pin(RECEIPT)},
        'runtime_files': len(runtime_files), 'runtime_bytes': value['runtime_files_bytes'],
        'tokenizer_files': files}, sort_keys=True))
    signal.alarm(0)


if __name__ == '__main__':
    main()
