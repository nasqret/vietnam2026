"""Stage exact existing diagnostic metadata; separately finalize a clean snapshot.

No source/model transfer, remote writes, scheduler calls, model loading or
approval creation. The actual candidate origin receipt must already exist.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import sys

ROOT = Path('/Users/bnaskrecki/codex/peano')
ARCHIVE = ROOT / 'artifacts/hydra-model-test-2026-08-30'
WORK = ROOT / '_deploy/hydra-frontier-recovery-work-20260830'
FROZEN = ROOT / '_deploy/hydra-model-test-execution-20260830'
TRAINING = ROOT / '_deploy/hydra-frontier-training-execution-20260830'
TRAINING_ARCHIVE = ROOT / 'artifacts/frontier-training-2026-08-30'
BASELINE = ROOT / '_deploy/hydra-search-v2-build-20260829/_deploy/hydra-search-v2'
PACKAGE = '_deploy/hydra-frontier-diagnostic-v1'
MAX_TOTAL = 16 * 1024**2


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                     separators=(',', ':'), allow_nan=False).encode()


def descriptor(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def write_new(path, raw):
    if len(raw) > 4 * 1024**2:
        raise ValueError('Metadata file exceeds bound')
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(raw)


def checked_bytes(path, expected):
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 4 * 1024**2:
        raise ValueError('Unexpected metadata file: ' + str(path))
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError('External metadata hash differs: ' + str(path))
    json.loads(raw)
    return raw


def modules(source):
    sys.dont_write_bytecode = True
    sys.pycache_prefix = '/dev/null'
    sys.path[:0] = [str(source), str(source / 'peano-lab/py')]
    from training.peano_hydra import frontier_diagnostic_run as diagnostic
    from training.peano_hydra import frontier_diagnostic_launch as launch
    if diagnostic.ROOT != source or launch.ROOT != source:
        raise ValueError('Wrong diagnostic source root')
    return diagnostic, launch


def stage(candidate_sha):
    destination = WORK / PACKAGE
    receipt_path = ARCHIVE / 'package-stage-01.json'
    if destination.exists() or receipt_path.exists():
        raise ValueError('Staging requires fresh destinations')
    items = {
        'evaluation-plan.json': (ROOT / '_deploy/hydra-frontier-execution-20260830/_deploy/hydra-frontier-candidate-v1/evaluation-plan.json',
            'a8084683ea64e4128f4d34eea0753c67fc42a55772e1c698a5dbd62865878c4b'),
        'origins/baseline/source-manifest.json': (BASELINE / 'origin/source-manifest.json',
            '7cb1a9d35b078989991362a979c3ea0d6abac929fbfcf9ae1e457458a24e513d'),
        'origins/baseline/manifest.json': (BASELINE / 'model/manifest.json',
            '172a6928710192c5348dcd7b04f71e6d4d3f75dfa1ab0f7f5add601769704a7c'),
        'origins/baseline/origin-receipt.json': (BASELINE / 'origin/origin-receipt.json',
            '9f3509835a2dffeabf7590af8347aad9a622342f5131a20e26eaf0faa40ab7d1'),
        'origins/candidate/source-manifest.json': (TRAINING / '_deploy/frontier-training-origin-source.json',
            '346f9ac39c7d66ebb2c340922d77fc5dbef8a2e867cb1825dddcea92e616ca3b'),
        'origins/candidate/manifest.json': (TRAINING_ARCHIVE / 'completed-manifest-01.json',
            '5795d5a3d70f781f56f81e83c2295c887d0949795924f4208f45d26a3ef89b68'),
        'origins/candidate/origin-receipt.json': (ARCHIVE / 'candidate-origin-receipt-local-01.json', candidate_sha),
        'training-evidence/resource-request.json': (TRAINING / '_deploy/hydra-frontier-training-v1/resource-request.json',
            '02e8c485eaee56523b82ce015c0e7478dde19622528c813f9cdf4079eb141feb'),
        'training-evidence/resource-approval.json': (TRAINING / '_deploy/hydra-frontier-training-v1/approval.json',
            '9cc426c7829bba661db24df58d53f036d4f759e0c6548208ca5a25e9737150bd'),
        'training-evidence/launch-receipt.json': (TRAINING_ARCHIVE / 'launch-submit-01.json',
            '4515907b8f3c7adf361ce645cba564fb2149baba0b7013bfc883c38e0ab78fb0'),
        'training-evidence/terminal-observation.json': (TRAINING_ARCHIVE / 'observation-v2-05.json',
            '3b85a4ceb82e3bc816b795efbe296cd31d114363cd11299cb31d73c3c0828cae'),
    }
    payloads = {name: checked_bytes(path, sha) for name, (path, sha) in items.items()}
    if sum(map(len, payloads.values())) > MAX_TOTAL:
        raise ValueError('Metadata package exceeds aggregate bound')
    diagnostic, launch = modules(WORK)
    for name, raw in payloads.items():
        write_new(destination / name, raw)
    def desc(name):
        return {'path': PACKAGE + '/' + name, **descriptor(payloads[name])}
    request = diagnostic.request_template()
    request.update(status='ready-for-explicit-resource-approval',
                   evaluation_plan=desc('evaluation-plan.json'),
                   caller_sources=diagnostic.caller_sources())
    for key, role in [('baseline', 'saved-corrected'), ('candidate', 'new-frontier')]:
        prefix = 'origins/' + key + '/'
        origin = json.loads(payloads[prefix + 'origin-receipt.json'])
        request[key] = {'identity': origin['request'],
            'source_locations': launch.EXTERNAL_SOURCES[role],
            'source_manifest': desc(prefix + 'source-manifest.json'),
            'adapter_manifest': desc(prefix + 'manifest.json'),
            'receipt': desc(prefix + 'origin-receipt.json')}
    request['completed_training'] = {key: desc('training-evidence/' + name)
        for key, name in [('resource_request', 'resource-request.json'),
            ('resource_approval', 'resource-approval.json'), ('launch_receipt', 'launch-receipt.json'),
            ('terminal_observation', 'terminal-observation.json')]}
    request['request_sha256'] = diagnostic.digest({k:v for k,v in request.items() if k != 'request_sha256'})
    raw = canonical(request) + b'\n'
    write_new(destination / 'evaluation-request.json', raw)
    checked = diagnostic.check_request(destination / 'evaluation-request.json', descriptor(raw)['sha256'])
    payloads['evaluation-request.json'] = raw
    result = {'schema':'peano-hydra-diagnostic-metadata-stage-v1', 'status':'passed',
        'recorded_at_utc':datetime.now(timezone.utc).isoformat(), 'package_root':str(destination),
        'files':{name:descriptor(value) for name,value in sorted(payloads.items())},
        'files_count':len(payloads), 'total_bytes':sum(map(len,payloads.values())),
        'evaluation_request':descriptor(raw), 'semantic_check':checked.summary(),
        'new_gpu_or_transfer_approval_created':False, 'model_weights_copied_or_loaded':False,
        'native_validation_performed':False}
    write_new(receipt_path, canonical(result)+b'\n')
    return result


def finalize(commit, stage_sha):
    destination = FROZEN / PACKAGE
    receipt_path = ARCHIVE / 'package-final-01.json'
    if destination.exists() or receipt_path.exists():
        raise ValueError('Final package requires fresh destinations')
    staged = json.loads(checked_bytes(ARCHIVE / 'package-stage-01.json', stage_sha))
    if staged['status'] != 'passed' or staged['package_root'] != str(WORK / PACKAGE):
        raise ValueError('Staged package identity differs')
    if not 1 <= len(staged['files']) <= 16 or staged['total_bytes'] > MAX_TOTAL:
        raise ValueError('Staged package inventory exceeds bounds')
    payloads = {name:checked_bytes(WORK / PACKAGE / name, pin['sha256']) for name,pin in staged['files'].items()}
    if any(descriptor(payloads[name]) != pin for name,pin in staged['files'].items()):
        raise ValueError('Staged package bytes changed')
    diagnostic, launch = modules(FROZEN)
    for name, raw in payloads.items():
        write_new(destination/name,raw)
    request = launch.ready_request(commit)
    raw = canonical(request)+b'\n'
    write_new(destination/'resource-request.json',raw)
    launch.validate_request(request)
    result = {'schema':'peano-hydra-diagnostic-ready-package-v1','status':'ready-for-explicit-resource-approval',
        'recorded_at_utc':datetime.now(timezone.utc).isoformat(),'source_root':str(FROZEN),
        'source_commit':commit,'resource_request':descriptor(raw),
        'evaluation_request':staged['evaluation_request'],'source_files':len(request['source_files']),
        'source_bytes':sum(v['bytes'] for v in request['source_files'].values()),
        'payload_files':len(request['payloads']),'payload_bytes':sum(v['bytes'] for v in request['payloads'].values()),
        'reserved_gpu_seconds_proposed':900,'semantic_admission':request['semantic_admission'],
        'remote_artifact_byte_recheck_required':True,'gpu_or_transfer_approval_created':False,
        'model_weights_copied_or_loaded':False,'native_validation_performed':False}
    write_new(receipt_path,canonical(result)+b'\n')
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__,allow_abbrev=False)
    parser.add_argument('stage',choices=('stage','finalize'))
    parser.add_argument('--candidate-receipt-sha256')
    parser.add_argument('--source-commit')
    parser.add_argument('--stage-sha256')
    args=parser.parse_args()
    resource.setrlimit(resource.RLIMIT_CPU,(30,31))
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,4*1024**2))
    def timeout(*_): raise RuntimeError('Diagnostic package CPU/wall limit')
    signal.signal(signal.SIGALRM,timeout)
    signal.signal(signal.SIGXCPU,timeout)
    signal.alarm(60)
    if args.stage=='stage':
        if args.candidate_receipt_sha256 is None or args.source_commit or args.stage_sha256:
            parser.error('Stage needs only the actual candidate receipt raw SHA')
        result=stage(args.candidate_receipt_sha256)
    else:
        if args.candidate_receipt_sha256 or not args.source_commit or not args.stage_sha256:
            parser.error('Finalize needs the frozen commit and prior stage raw SHA')
        result=finalize(args.source_commit,args.stage_sha256)
    signal.alarm(0)
    print(json.dumps(result,sort_keys=True,allow_nan=False))


if __name__=='__main__':
    main()
