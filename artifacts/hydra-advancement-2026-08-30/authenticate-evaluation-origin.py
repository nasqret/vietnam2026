#!/usr/bin/env python3
"""Explicit original-origin CPU authentication; no model inference or allocation.

Prepared helper, not an executed check or a resource approval. It requires the
actual source/data/adapter files on a compatible CPU host. A manifest and a
remote hash inventory alone cannot pass the unchanged original validator.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('--execution-root', type=Path, required=True)
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--expected-request-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True, help='fresh original receipt file outside all inputs')
    parser.add_argument('--authenticate', action='store_true', required=True)
    args = parser.parse_args()
    if sys.version_info < (3, 11):
        raise SystemExit('A compatible installed Python>=3.11 is required; do not install or replace libc.')
    root = args.execution_root.absolute()
    sys.dont_write_bytecode = True
    sys.pycache_prefix = '/dev/null'
    sys.path[:0] = [str(root), str(root / 'peano-lab/py')]
    from training.peano_hydra import origin_bridge as bridge
    from training.peano_hydra import corrective_workflow as files
    try:
        bridge._require(not os.environ.get('SLURM_JOB_ID'),
                        'this prepared helper is not an allocation entrypoint or a GPU-origin fallback')
        raw = bridge._read(args.request.absolute(), 1024**2)
        bridge._require(hashlib.sha256(raw).hexdigest() == args.expected_request_sha256,
                        'external raw CPU request pin differs')
        record = bridge._decode(raw, 1024**2, 'origin CPU request')
        bridge._keys(record, {'schema', 'status', 'role', 'origin_identity', 'locations', 'support_files',
            'runtime_library_paths', 'native_worker_limits', 'model_inference_authorized', 'training_authorized',
            'gpu_execution_authorized'}, 'origin CPU request')
        bridge._require(record['schema'] == 'peano-hydra-frontier-evaluation-origin-cpu-request-v1'
                        and record['status'] == 'ready-for-explicit-bounded-cpu-check'
                        and record['role'] in {'saved-corrected', 'new-frontier'}
                        and all(record[k] is False for k in ('model_inference_authorized', 'training_authorized',
                                                            'gpu_execution_authorized')),
                        'a draft or model/allocation authority cannot run this CPU helper')
        bridge._require(record['native_worker_limits'] == bridge.ORIGIN_LIMITS.to_dict(),
                        'the existing120CPU/180wall/1GiB/2MiB-output native child limits must remain unchanged')
        bridge._require(set(record['support_files']) == set(bridge.SUPPORT_FILES), 'bridge support coverage changed')
        with bridge._Tree(root) as tree:
            bridge._require(bridge._support(tree) == record['support_files'], 'frozen original-validator support changed')
        request = bridge._request(record['origin_identity'], record['locations'])
        libraries = record['runtime_library_paths']
        bridge._require(type(libraries) is list and all(type(p) is str for p in libraries),
                        'reviewed runtime library paths must be explicit; inherited LD_LIBRARY_PATH is not used')
        protected = (request.source_root, request.adapter_manifest.parent, request.source_manifest.parent,
                     args.request.absolute().parent)
        output = files.guard_output(args.output.absolute(), protected=protected)
        origin = bridge.authenticate_origin(request, python=Path(sys.executable), runtime_library_paths=tuple(libraries))
        files.write_new(output, origin.receipt_bytes, raw=True)
        bridge._require(not {'torch', 'transformers', 'peft', 'tokenizers'} & set(sys.modules),
                        'CPU original validation imported a model framework')
        print(json.dumps({'status': 'original-origin-authenticated', 'output': str(output),
            'receipt_file_sha256': origin.receipt_sha256, 'role': record['role'],
            'model_inference_performed': False, 'allocation_performed': False,
            'human_review_created': False, 'automatic_retry': False}, sort_keys=True))
        return 0
    except (ValueError, TypeError, KeyError, OSError, RuntimeError) as error:
        print('origin-cpu-preflight: ' + ' '.join(str(error).split())[:3000], file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
