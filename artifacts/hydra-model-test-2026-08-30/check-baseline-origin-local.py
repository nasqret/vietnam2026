"""Revalidate an existing original-origin receipt; no native/model execution."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import resource
import signal
import sys
import time

ROOT = Path('/Users/bnaskrecki/codex/peano')
SOURCE = ROOT / '_deploy/hydra-advancement-execution-v2-20260830'
SAVED = ROOT / '_deploy/hydra-search-v2-build-20260829/_deploy/hydra-search-v2'
OUT = ROOT / 'artifacts/hydra-model-test-2026-08-30/baseline-origin-reuse-01.json'
START = time.monotonic()
EXPECTED = {
    'manifest.json': '081c9e8c56dd4589ef284e287d3f96d406fb083b3942a1cd615785069f6b708c',
    'source-manifest.json': '7cb1a9d35b078989991362a979c3ea0d6abac929fbfcf9ae1e457458a24e513d',
    'origin-receipt.json': '9f3509835a2dffeabf7590af8347aad9a622342f5131a20e26eaf0faa40ab7d1',
}


def main():
    if OUT.exists():
        raise ValueError('Fresh output required')
    resource.setrlimit(resource.RLIMIT_CPU, (15, 16))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_FSIZE, (65536, 65536))
    def timeout(*_):
        raise RuntimeError('Baseline receipt check resource limit')
    signal.signal(signal.SIGALRM, timeout)
    signal.signal(signal.SIGXCPU, timeout)
    signal.alarm(30)
    record = {
        'schema': 'peano-hydra-existing-baseline-origin-reuse-v1',
        'recorded_at_utc': datetime.now(timezone.utc).isoformat(),
        'source': str(SOURCE), 'preserved_bundle': str(SAVED),
        'limits': {'cpu_seconds': 15, 'wall_seconds': 30, 'output_bytes': 65536},
        'native_validation_repeated': False, 'model_inference_performed': False,
        'network_access_performed': False, 'preserved_inputs_modified': False,
        'gpu_authorization_created': False,
    }
    try:
        for name, expected in EXPECTED.items():
            path = SAVED / 'origin' / name
            if path.is_symlink() or path.stat().st_size > 4 * 1024**2:
                raise ValueError('Unexpected origin evidence file')
            if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                raise ValueError('Original origin evidence hash mismatch')
        reference = json.loads((SAVED / 'origin/manifest.json').read_bytes())
        sys.path[:0] = [str(SOURCE), str(SOURCE / 'peano-lab/py')]
        from training.peano_hydra import origin_bridge as bridge
        request = bridge._request(reference['reference']['request'], {
            'source_root': str(SAVED / 'origin-source'),
            'source_manifest': str(SAVED / 'origin/source-manifest.json'),
            'adapter_manifest': str(SAVED / 'model/manifest.json'),
        })
        handle = bridge.load_origin_receipt(SAVED / 'origin/origin-receipt.json',
            expected_receipt_sha256=EXPECTED['origin-receipt.json'], request=request)
        if {'torch', 'transformers', 'peft', 'tokenizers'} & set(sys.modules):
            raise ValueError('Model framework imported during metadata-only reuse')
        record.update(status='original-baseline-receipt-reused-after-byte-revalidation',
            receipt_sha256=handle.receipt_sha256, origin=handle.origin,
            request=request.to_dict(), locations={
                'source_root': str(request.source_root),
                'source_manifest': str(request.source_manifest),
                'adapter_manifest': str(request.adapter_manifest),
            })
    except Exception as error:
        record.update(status='incomplete', error_type=type(error).__name__, error=str(error)[:2048])
    finally:
        signal.alarm(0)
    usage = resource.getrusage(resource.RUSAGE_SELF)
    record['resources'] = {'wall_seconds': time.monotonic()-START,
        'cpu_seconds': usage.ru_utime+usage.ru_stime, 'peak_rss_bytes': usage.ru_maxrss}
    raw = (json.dumps(record, sort_keys=True, indent=2, allow_nan=False)+'\n').encode()
    if len(raw) > 65536:
        raise ValueError('Metadata output exceeds declared cap')
    with OUT.open('xb') as stream:
        stream.write(raw)
    print(json.dumps({'status':record['status'],'output':str(OUT),
        'sha256':hashlib.sha256(raw).hexdigest(),'resources':record['resources'],
        'error':record.get('error')}, sort_keys=True))
    return 0 if record['status'] != 'incomplete' else 1


if __name__ == '__main__':
    raise SystemExit(main())
