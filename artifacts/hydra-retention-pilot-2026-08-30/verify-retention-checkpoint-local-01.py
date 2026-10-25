#!/usr/bin/env python3
"""Independently replay an actual collected retention checkpoint, once, locally.

The frozen CLI and its per-proof 30 CPU / 45 wall / 1 GiB / 1 MiB guards are
unchanged. This caller has a separately declared 600 CPU / 900 wall / 2 GiB
sampled whole-process-tree envelope for up to 256 records. It reuses the
reviewed PID/start-identity, sampling, wait4 and cleanup primitives without
changing their old Limits constructor or invoking a model or scheduler.

Every collection, raw HEAD, candidate manifest, authorization and approval
pin must come from actual retained evidence. A prefix is never promoted to
a complete report. Completion additionally requires the owner's zero exit
and successful owner-result.json; a worker file alone is not completion.
"""
import time
STARTED = time.monotonic()
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.abc
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import resource
import runpy
import selectors
import signal
import stat
import subprocess
import sys

WORKSPACE = Path('/Users/bnaskrecki/codex/peano')
ARCHIVE = WORKSPACE / 'artifacts/hydra-retention-pilot-2026-08-30'
HELPER = ARCHIVE / 'verify-retention-checkpoint-local-01.py'
FROZEN = WORKSPACE / '_deploy/hydra-retention-execution-20260830'
PACKAGE = '_deploy/hydra-retention-pilot-v1'
REMOTE = '/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/retention-pilot-v1'
COMMIT = '4aeae795c8cb5bfc622c9943359b5b38446089b9'
CLI = FROZEN / 'scripts/execute_peano_hydra_retention.py'
CLI_SHA = '7e435d11124fca0946ca74012329b1ee68dc19efb19cb8a05655b71dbd258518'
INPUT_SHA = '3df7953c0d405364aef689b5e67b083f5fc744492159643ca5b09e418a06a388'
EVALUATION_SHA = '7dd90249324b82846f6cbae6e157c5fef09e22e0b058b73822f11aae1b95f635'
TRAINING_PLAN_SHA = 'da26332740d587bdd946b12999fd37de73817115ed3da8983edf5004bd02abf0'
FREEZE = FROZEN / '_deploy/hydra-retention-execution-freeze.json'
FREEZE_SHA = '2cc7a302ac0156972acca3a2c7d0c4374426224c6e6493d2930a00855444bf52'
ORIGIN_SOURCE = FROZEN / '_deploy/hydra-retention-origin-source.json'
ORIGIN_SOURCE_SHA = '4f4fcbfcd51ff64b9674dfdde383b37337871d93f52792b3f6f9bedec6862665'
BASE = WORKSPACE / 'artifacts/hydra-model-test-2026-08-30/verify-diagnostic-local-02.py'
BASE_SHA = '7df14454b45ffd8b85d8d2ed4903fd968c0decc642b4b9e35f7255c6fa8bd155'
SUPERVISOR = WORKSPACE / 'artifacts/hydra-advancement-2026-08-30/run-v28-hotspots-supervised-v2.py'
SUPERVISOR_SHA = '1be34563858e2deba8e23ea47dc9f5966ffe092c3e0d23fe80a81a411b94af1c'
PYTHON = Path('/opt/homebrew/Cellar/python@3.11/3.11.12/Frameworks/Python.framework/Versions/3.11/bin/python3.11')
PYTHON_SHA = '4df3f520de9c3b86c4ae895c68921509ff29cfb9562656f7c31ed25591d68b29'
MODEL_COLLECTION = ARCHIVE / 'trained-model-collected-01'
EVALUATION_COLLECTION = ARCHIVE / 'evaluation-checkpoint-collected-01'
OUTPUT = ARCHIVE / 'evaluation-verification-01'
COLLECTORS = {
    'collect-retention-model-01.py': 'aac362e4b4ba4a42426f754568d34eec87428018e3f9e2f670911c59cd531e48',
    'collect-retention-model-remote-01.py': '0bf9321e211c2e60a450d8da1bbe8f3ef01e30497c397ffc2bafd7337df89257',
    'collect-retention-evaluation-01.py': '73ac2d88036972a3679923074132e69a54e79b4b7ca21704f15a73a6bf2cc233',
    'collect-retention-evaluation-remote-01.py': '69213e7759689e0d70f7033513dcd626a113ec5da28e8d9824f9ba82ec750fdc',
}
SCHEMA = 'peano-hydra-retention-local-checkpoint-verification-v1'
OWNER_SCHEMA = 'peano-hydra-retention-local-checkpoint-verification-owner-v1'
SUPERVISION_SCHEMA = 'peano-hydra-retention-local-replay-process-tree-v1'
LIMITS = {'whole_cpu_seconds': 600, 'whole_wall_seconds': 900,
    'sampled_parent_and_owned_tree_rss_bytes': 2 * 1024**3,
    'controller_cpu_seconds': 180, 'retained_output_bytes': 64 * 1024**2,
    'combined_pipe_bytes': 1024**2, 'output_file_bytes': 32 * 1024**2,
    'max_observed_processes': 2048, 'sample_interval_seconds': .05}
PROOF_LIMITS = {'wall_seconds': 45, 'cpu_seconds': 30,
    'rss_bytes': 1024**3, 'output_bytes': 1024**2}
FALSE_CLAIMS = {'model_loaded': False, 'model_outputs_regenerated': False,
    'gpu_allocated': False, 'network_contacted': False, 'scheduler_mutation_performed': False,
    'historical_gpu_inference_attested': False, 'original_resource_caps_changed': False,
    'benchmark_acceptance_eligible': False, 'self_training_readiness_eligible': False,
    'heldout_or_reserved_goals_scored': False, 'training_goals_scored': False,
    'new_original_origin_authentication_performed': False,
    'reservation_fabricated': False, 'automatic_retry': False, 'resume': False}
SHA = re.compile(r'[0-9a-f]{64}\Z')
PIN_FIELDS = ('helper_sha256', 'model_collection_sha256', 'evaluation_collection_sha256',
    'model_manifest_sha256', 'checkpoint_head_sha256', 'authorization_sha256',
    'approval_sha256', 'source_header_sha256')


def require(value, message):
    if not value: raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
        ensure_ascii=False, allow_nan=False).encode()


def digest(value): return hashlib.sha256(canonical(value)).hexdigest()


def load_module(path, expected, name):
    """Only raw-pinned local utilities; no old main/worker is invoked."""
    require(type(expected) is str and SHA.fullmatch(expected)
        and path.is_absolute() and path == path.resolve(strict=True), 'pinned canonical helper required')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_size <= 128 * 1024,
                'bounded regular helper required')
        raw = stream.read(128 * 1024 + 1)
        signature = lambda x: (x.st_dev, x.st_ino, x.st_mode, x.st_size, x.st_mtime_ns, x.st_ctime_ns, x.st_nlink)
        require(len(raw) == before.st_size and hashlib.sha256(raw).hexdigest() == expected
            and signature(before) == signature(os.fstat(stream.fileno())) == signature(path.lstat()),
            'reviewed helper changed during import')
    spec = importlib.util.spec_from_loader(name, loader=None)
    module = importlib.util.module_from_spec(spec)
    module.__file__ = str(path)
    sys.modules[name] = module
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module


def utilities():
    base = load_module(BASE, BASE_SHA, '_retention_replay_original_utilities')
    owner = load_module(SUPERVISOR, SUPERVISOR_SHA, '_retention_replay_original_ownership')
    require(owner.HELPER == SUPERVISOR and owner.Limits().__dict__ ==
        {'wall_seconds': 300, 'cpu_seconds': 180, 'rss_bytes': 2 * 1024**3, 'output_bytes': 64 * 1024**2}
        and owner.MAX_OBSERVED_PROCESSES == LIMITS['max_observed_processes']
        and owner.SAMPLE_SECONDS == LIMITS['sample_interval_seconds'], 'original utility limits changed')
    return base, owner


def current_cpu():
    own, children = resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)
    return own.ru_utime + own.ru_stime + children.ru_utime + children.ru_stime


def parent_peak():
    own = resource.getrusage(resource.RUSAGE_SELF)
    return int(own.ru_maxrss if sys.platform == 'darwin' else own.ru_maxrss * 1024)


def relative(name):
    require(type(name) is str and re.fullmatch(r'[A-Za-z0-9_./-]{1,1024}', name)
        and all(part not in ('', '.', '..') for part in name.split('/')), 'unsafe retained relative path')
    return name


def pin_of(descriptor): return {key: descriptor[key] for key in ('bytes', 'sha256')}


def source_inputs(base, approval_sha, *, deadline):
    """All frozen files plus the actual final23 controls/payload inventory."""
    freeze, _ = base.read_json(FREEZE, FREEZE_SHA)
    inventory = freeze['files']
    require(freeze['git_commit'] == COMMIT and freeze['snapshot_root'] == str(FROZEN)
        and freeze['snapshot_clean'] is True and freeze['file_count'] == len(inventory) == 886
        and sum(item['bytes'] for item in inventory.values()) == 91043396,
        'wrong complete frozen retention source inventory')
    for name, item in inventory.items():
        require(base.fingerprint(FROZEN / relative(name), maximum=64 * 1024**2, deadline=deadline)[0] == pin_of(item),
                'frozen source/data bytes changed')
    require(base.fingerprint(ORIGIN_SOURCE, deadline=deadline)[0]['sha256'] == ORIGIN_SOURCE_SHA
        and base.fingerprint(CLI, deadline=deadline)[0]['sha256'] == CLI_SHA
        and base.fingerprint(PYTHON, deadline=deadline)[0]['sha256'] == PYTHON_SHA,
        'frozen provenance, original CLI or canonical local Python changed')
    approval, _ = base.read_json(FROZEN / PACKAGE / 'approval.json', approval_sha)
    request, _ = base.read_json(FROZEN / PACKAGE / 'resource-request.json', approval['request_file_sha256'])
    require(request.get('source_commit') == COMMIT and type(request.get('payloads')) is dict
        and len(request['payloads']) == 21 and digest(request['payloads']) == request['payloads_sha256'],
        'exact final package payloads required; bootstrap18 is insufficient')
    expected = set(request['payloads']) | {PACKAGE + '/approval.json', PACKAGE + '/resource-request.json'}
    observed, pending = set(), [FROZEN / PACKAGE]
    count = 0
    while pending:
        with os.scandir(pending.pop()) as entries:
            for entry in entries:
                count += 1
                require(count <= 128 and not entry.is_symlink(), 'final package traversal bound')
                path = Path(entry.path)
                if entry.is_dir(follow_symlinks=False): pending.append(path)
                else:
                    require(entry.is_file(follow_symlinks=False), 'special final package entry')
                    observed.add(str(path.relative_to(FROZEN)))
    require(observed == expected, 'closed final package file inventory changed')
    total = 0
    for name, item in request['payloads'].items():
        require(relative(name).startswith(PACKAGE + '/'), 'payload escaped fixed package')
        actual = base.fingerprint(FROZEN / name, maximum=128 * 1024**2, deadline=deadline)[0]
        require(actual == item, 'actual approved payload changed')
        total += actual['bytes']
        require(total <= 128 * 1024**2, 'approved payload aggregate cap')
    require(request['payloads'][PACKAGE + '/inputs.json']['sha256'] == INPUT_SHA
        and request['payloads'][PACKAGE + '/evaluation-plan.json']['sha256'] == EVALUATION_SHA,
        'preregistered input/evaluation plan changed')
    for name, item in request['source_files'].items():
        require(name in inventory and item == pin_of(inventory[name]), 'resource source pin differs from real freeze')
    return {'source_commit': COMMIT, 'freeze_sha256': FREEZE_SHA, 'source_files_sha256': freeze['files_sha256'],
        'source_files': 886, 'source_bytes': 91043396, 'approval_sha256': approval_sha,
        'resource_request_sha256': approval['request_file_sha256'], 'payloads_sha256': request['payloads_sha256'],
        'package_files': len(observed), 'payload_bytes': total}


def collected_tree(base, directory, index, *, checkpoint=False, deadline):
    """Rehash every collected original file; do not filter or repair anything."""
    require(base.exact_path(directory) == directory, 'canonical actual collection directory required')
    files = index['files']
    total = 0
    for name, item in files.items():
        actual = base.fingerprint(directory / relative(name), maximum=128 * 1024**2, deadline=deadline)[0]
        require(actual == pin_of(item), 'actual collected input changed: ' + name)
        total += actual['bytes']
    require(total == index['total_file_bytes'], 'collected aggregate bytes changed')
    # Retain the transport/owner records without treating them as scientific
    # input. No foreign local entry may be added to this actual collected copy.
    allowed_files = set(files) | {'collection-index.json', 'collection-receipt.json', 'started.json', 'transfer.tar', 'stderr.log'}
    allowed_directories = set(index.get('directories', []))
    for name in files:
        parts = name.split('/')
        allowed_directories.update('/'.join(parts[:length]) for length in range(1, len(parts)))
    found_files, found_directories, pending = set(), set(), [directory]
    while pending:
        with os.scandir(pending.pop()) as entries:
            for entry in entries:
                require(len(found_files) + len(found_directories) <= 600 and not entry.is_symlink(), 'collection root inventory/link cap')
                path = Path(entry.path); name = str(path.relative_to(directory))
                if entry.is_dir(follow_symlinks=False):
                    require(name in allowed_directories, 'foreign collected directory')
                    found_directories.add(name); pending.append(path)
                else:
                    require(entry.is_file(follow_symlinks=False) and name in allowed_files, 'foreign collected file')
                    found_files.add(name)
    require(found_files == allowed_files and found_directories == allowed_directories, 'actual local collection inventory changed')
    if checkpoint:
        require(index['checkpoint_root_present'] is True and index['checkpoint_original_lock_collected'] is True,
                'an actual checkpoint with its original lock is required')
        expected = index['checkpoint_entry_inventory']
        actual, pending = {}, [directory / 'checkpoint']
        while pending:
            with os.scandir(pending.pop()) as entries:
                for entry in entries:
                    require(len(actual) < 264 and not entry.is_symlink(), 'checkpoint traversal count/link cap')
                    path = Path(entry.path)
                    name = str(path.relative_to(directory / 'checkpoint'))
                    if entry.is_dir(follow_symlinks=False):
                        actual[name] = 'directory'; pending.append(path)
                    else:
                        require(entry.is_file(follow_symlinks=False), 'special retained checkpoint entry')
                        actual[name] = 'file'
        require(actual == {name: item['kind'] for name, item in expected.items()},
                'checkpoint inventory was filtered, repaired, or extended')
    else:
        expected = {name for name in files if name.startswith('model/')}
        actual, pending = set(), [directory / 'model']
        entries_seen = 0
        while pending:
            with os.scandir(pending.pop()) as entries:
                for entry in entries:
                    entries_seen += 1
                    require(entries_seen <= 20 and not entry.is_symlink(), 'model artifact traversal count/link cap')
                    path = Path(entry.path)
                    if entry.is_dir(follow_symlinks=False): pending.append(path)
                    else:
                        require(entry.is_file(follow_symlinks=False), 'special retained model entry')
                        actual.add(str(path.relative_to(directory)))
        require(actual == expected, 'collected model contains missing or additional files')


def collections(base, request, *, deadline):
    for name, expected in COLLECTORS.items():
        require(base.fingerprint(ARCHIVE / name, deadline=deadline)[0]['sha256'] == expected,
                'reviewed collection source changed: ' + name)
    model_protocol = load_module(ARCHIVE / 'collect-retention-model-remote-01.py',
        COLLECTORS['collect-retention-model-remote-01.py'], '_retention_model_collection_validation')
    eval_protocol = load_module(ARCHIVE / 'collect-retention-evaluation-remote-01.py',
        COLLECTORS['collect-retention-evaluation-remote-01.py'], '_retention_evaluation_collection_validation')
    values = {}
    for kind, directory, mode, status in (
        ('model', MODEL_COLLECTION, 'model', 'model-bytes-collected-not-semantically-admitted'),
        ('evaluation', EVALUATION_COLLECTION, 'checkpoint', 'collected-not-proof-verified')):
        receipt, _ = base.read_json(directory / 'collection-receipt.json', request[kind + '_collection_sha256'])
        stem = 'collect-retention-' + kind
        job = request['train_job_id' if kind == 'model' else 'evaluation_job_id']
        require(receipt['schema'] == 'peano-hydra-retention-' + kind + '-collection-v1'
            and receipt['status'] == status and receipt['mode'] == mode and receipt['job_id'] == job
            and receipt['approval_sha256'] == request['approval_sha256']
            and receipt['local_helper_sha256'] == COLLECTORS[stem + '-01.py']
            and receipt['remote_helper_sha256'] == COLLECTORS[stem + '-remote-01.py']
            and receipt['returncode'] == 0 and receipt['reason'] == 'exited' and receipt['error'] is None
            and receipt['output_directory'] == str(directory), 'actual successful pinned collection required')
        index, index_raw = base.read_json(directory / 'collection-index.json', receipt['index']['sha256'])
        require(len(index_raw) == receipt['index']['bytes'] and receipt['files'] == index['files']
            and receipt['binding'] == index['binding'] and receipt['accounting'] == index['accounting'],
            'collection receipt and original index differ')
        require(receipt['read_only'] is True and all(receipt[key] is False for key in
            ('model_loaded', 'proofs_independently_verified', 'scheduler_mutation_performed', 'remote_files_written', 'automatic_retry')),
            'collection changed its read-only evidence scope')
        for name, key, maximum in (('started.json', 'started', 4 * 1024**2),
                ('stderr.log', 'stderr', 64 * 1024),
                ('transfer.tar', 'transport', (130 if kind == 'model' else 66) * 1024**2)):
            require(base.fingerprint(directory / name, maximum=maximum, deadline=deadline)[0] == pin_of(receipt[key]),
                    'retained collection transport/start/stderr changed')
        if kind == 'model':
            model_protocol.validate_index(index, mode, job, request['approval_sha256'], request['model_manifest_sha256'])
        else:
            eval_protocol.validate_index(index, mode, job, request['approval_sha256'], request['source_header_sha256'],
                request['checkpoint_head_sha256'], request['model_manifest_sha256'])
            require(receipt['checkpoint_entry_inventory'] == index['checkpoint_entry_inventory']
                and receipt['checkpoint_head'] == index['checkpoint_head']
                and receipt['checkpoint_all_actual_entries_collected'] is True
                and receipt['checkpoint_original_lock_collected'] is True
                and receipt['checkpoint_debris_filtered'] is False and receipt['checkpoint_files_modified'] is False,
                'full original checkpoint collection flags differ')
        collected_tree(base, directory, index, checkpoint=kind == 'evaluation', deadline=deadline)
        values[kind] = {'receipt': receipt, 'index': index}
    old, new = values['model']['index'], values['evaluation']['index']
    require(old['binding']['job_id'] == new['binding']['train_job_id'] == request['train_job_id']
        and old['binding']['manifest'] == new['binding']['model_manifest']
        and pin_of(old['files']['model/manifest.json']) == pin_of(new['files']['model-manifest.json'])
        and pin_of(old['files']['metadata/train-ledger.jsonl']) == pin_of(new['files']['train-ledger.jsonl']),
        'model collection and actual evaluation reserved different completed training')
    require(all(old['binding'][key] == new['binding'][key] for key in
        ('approval_sha256', 'resource_request_sha256', 'source_commit', 'training_request_sha256'))
        and old['binding']['source_files_sha256'] == new['binding']['execution_identity']['source_files_sha256']
        and old['binding']['payloads_sha256'] == new['binding']['execution_identity']['payloads_sha256'],
        'model and evaluation collections changed source/resource/scientific identities')
    manifest, _ = base.read_json(MODEL_COLLECTION / 'model/manifest.json', request['model_manifest_sha256'])
    require(model_protocol.manifest_artifacts(manifest, request['train_job_id'], request['approval_sha256'])
        == old['declared_artifact_files'], 'actual manifest changed the collected adapter/tokenizer declaration')
    return values


def held_snapshot(snapshot, stage, job, gate):
    """Original held-barrier predicates with the explicitly declared remote root.

    gate.snapshot binds gate.ROOT (the local frozen root here). Do not change
    that global or invent a local ledger to make a historical snapshot pass.
    """
    raw = snapshot['raw']
    require(set(snapshot) == {'raw', 'raw_sha256', 'fields', 'allocation_elapsed_seconds'}
        and type(raw) is str and 0 < len(raw.encode()) <= 65536 and len(raw.strip().splitlines()) == 1
        and snapshot['raw_sha256'] == hashlib.sha256(raw.encode()).hexdigest(), 'held snapshot raw pin changed')
    keys = {'JobId', 'JobName', 'WorkDir', 'JobState', 'Reason', 'Priority', 'Dependency', 'Requeue',
        'Account', 'Partition', 'TimeLimit', 'NumNodes', 'NumCPUs', 'ReqTRES', 'RunTime'}
    fields = {}
    for match in re.finditer(r'(?:^|\s)([A-Za-z][A-Za-z0-9]*)=(\S*)', raw):
        key, value = match.groups()
        if key in keys:
            require(key not in fields, 'duplicate held scheduler field')
            fields[key] = value
    require(set(fields) == keys and fields == snapshot['fields']
        and fields['JobId'] == job and fields['JobName'] == gate.JOB_NAMES[stage] and fields['WorkDir'] == REMOTE
        and fields['Dependency'] in ('(null)', '(null)(unfulfilled)') and fields['Requeue'] == '0'
        and fields['Account'] == gate.ACCOUNT and fields['Partition'] == gate.PARTITION
        and fields['TimeLimit'] == gate.WALL[stage] and fields['NumNodes'] in ('1', '1-1') and fields['NumCPUs'] == '8'
        and fields['JobState'] == 'PENDING' and fields['Reason'] == 'JobHeldUser' and fields['Priority'] == '0'
        and gate._elapsed(fields['RunTime']) == snapshot['allocation_elapsed_seconds'] == 0,
        'original held job/resource/restart scope differs')
    tres = {}
    for item in fields['ReqTRES'].split(','):
        key, sep, value = item.partition('=')
        require(sep and key and value and key not in tres, 'ambiguous held requested resources')
        tres[key] = value
    require(tres.get('cpu') == '8' and tres.get('node') == '1' and tres.get('gres/gpu') == '1'
        and tres.get('mem') in ('64G', '65536M', '67108864K')
        and all(v == '1' for k, v in tres.items() if k.startswith('gres/gpu:')), 'held resource reservation changed')


def released_ledger(raw, stage, job, identity, manifest, gate):
    lines = raw.splitlines(keepends=True)
    require(raw.endswith(b'\n') and len(lines) == 6 and len(raw) <= 256 * 1024, 'complete original released ledger required')
    kinds = ('header', 'reserve', 'accepted', 'held-validated', 'release-authorized', 'released')
    previous, values = '0' * 64, []
    for number, line in enumerate(lines):
        event = gate.decode(line)
        require(set(event) == {'index', 'previous_sha256', 'payload', 'sha256'}
            and type(event['index']) is int and event['index'] == number and event['previous_sha256'] == previous
            and event['sha256'] == gate.digest({k: event[k] for k in ('index', 'previous_sha256', 'payload')})
            and gate.canonical(event) + b'\n' == line and type(event['payload']) is dict
            and event['payload'].get('kind') == kinds[number], 'released ledger chain/order changed')
        values.append(event['payload']); previous = event['sha256']
    header, reserve, accepted, held, barrier, released = values
    require(header == gate._header(stage, identity), 'captured ledger changed source/approval/stage identity')
    require(set(reserve) == {'kind', 'reservation', 'created_at', 'model_manifest'}
        and reserve['reservation'] == gate.RESERVATIONS[stage]
        and reserve['model_manifest'] == (None if stage == 'train' else manifest)
        and type(reserve['created_at']) is str
        and re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z', reserve['created_at'])
        and accepted == {'kind': 'accepted', 'job_id': job}
        and barrier == {'kind': 'release-authorized', 'job_id': job}
        and released == {'kind': 'released', 'job_id': job} and set(held) == {'kind', 'snapshot'},
        'captured reservation/actual job/release differs')
    held_snapshot(held['snapshot'], stage, job, gate)
    return {'job_id': job, 'stage': stage, 'ledger_sha256': hashlib.sha256(raw).hexdigest(),
        'ledger_events': 6, 'held_snapshot_sha256': held['snapshot']['raw_sha256'],
        'reserved_gpu_seconds': gate.RESERVATIONS[stage]['seconds'], 'reservation_fabricated': False}


def scientific_join(base, request, collected, api):
    gate, training = api['gate'], api['training']
    from training.peano_hydra import retention_evaluation as evaluation
    require(gate.ROOT == training.ROOT == evaluation.ROOT == FROZEN
        and evaluation.capacity.REPLAY_LIMITS.to_dict() == PROOF_LIMITS, 'wrong source root or original proof limits')
    evaluation.paired._model_free()
    approval, resource_request = gate.validate_metadata(request['approval_sha256'])
    local_identity = gate.identity(approval, resource_request, request['approval_sha256'], local=True)
    index = collected['evaluation']['index']
    remote_identity = index['binding']['execution_identity']
    require(set(remote_identity) == set(local_identity) and local_identity['synced_at'] is None
        and {k: v for k, v in remote_identity.items() if k != 'synced_at'} ==
            {k: v for k, v in local_identity.items() if k != 'synced_at'}
        and type(remote_identity['synced_at']) is str and re.fullmatch(r'[0-9TZ:+-]{1,40}', remote_identity['synced_at'])
        and digest(remote_identity) == request['source_header_sha256'], 'actual remote and local source/control identities differ')
    for name in ('approval.json', 'resource-request.json', 'train-request.json', 'evaluate-request.json',
                 'inputs.json', 'token-preflight.json', 'evaluation-plan.json'):
        require(base.fingerprint(FROZEN / PACKAGE / name)[0] == pin_of(index['files'][name]),
                'collected actual controls differ from final local package: ' + name)
    stages = {}
    for stage in gate.STAGES:
        descriptor = resource_request['scientific_inputs'][stage]
        record, plan, tokens = api['check_stage_request'](FROZEN / descriptor['path'], descriptor['sha256'])
        require(record['stage'] == stage and plan.to_dict()['training_plan_sha256'] == TRAINING_PLAN_SHA,
                'scientific request changed the genuine pretraining mixed plan')
        stages[stage] = (record, plan, tokens)
    require(stages['train'][1].to_dict() == stages['evaluate'][1].to_dict(), 'stage training inputs differ')
    inputs = api['load_inputs'](FROZEN / PACKAGE / 'inputs.json', INPUT_SHA)
    candidate = training.TrainingArtifactReference(MODEL_COLLECTION / 'model/manifest.json', request['model_manifest_sha256'], inputs)
    bound = evaluation.bind_evaluation(inputs.evaluation_plan_path,
        expected_evaluation_plan_sha256=inputs.evaluation_plan_sha256, baseline=inputs.baseline, candidate=candidate)
    manifest, _ = base.read_json(MODEL_COLLECTION / 'model/manifest.json', request['model_manifest_sha256'])
    expected_train_observation = {'status': 'job-verified', 'profile': gate.PROFILE, 'run_id': gate.RUN_ID,
        'stage': 'train', 'job_id': request['train_job_id'],
        **{k: remote_identity[k] for k in ('approval_sha256', 'resource_request_sha256', 'source_commit',
            'source_files_sha256', 'payloads_sha256')}, 'reservation': gate.RESERVATIONS['train'],
        'scientific_input': resource_request['scientific_inputs']['train'], 'model_manifest': None,
        'automatic_retry': False, 'resume': False}
    for key in ('reservation', 'final_reservation'):
        require(training._reservation(manifest[key], manifest['authorization'], live=False) == expected_train_observation,
                'completed mixed model does not join the actual approved training/source/token request')
    train_authorization = api['training_authorization'](stages['train'][1], stages['train'][2], manifest['reservation'])
    require(manifest['authorization'] == train_authorization and manifest['authorization_sha256'] == digest(train_authorization)
        and manifest['token_preflight'] == stages['train'][2], 'completed training changed the exact original token/authorization join')
    protected = (*api['output_protections'](inputs), MODEL_COLLECTION, EVALUATION_COLLECTION, FROZEN)
    api['files'].guard_output(OUTPUT / 'verification.json', protected=protected)
    api['files'].guard_output(OUTPUT / 'checkpoint-verification.json', protected=protected)
    ledgers = {}
    for stage, job in (('train', request['train_job_id']), ('evaluate', request['evaluation_job_id'])):
        _, raw = base.fingerprint(EVALUATION_COLLECTION / (stage + '-ledger.jsonl'), maximum=256 * 1024, retain=True)
        ledgers[stage] = released_ledger(raw, stage, job, remote_identity, index['model_manifest'], gate)
        key = 'training_ledger_sha256' if stage == 'train' else 'evaluation_ledger_sha256'
        require(ledgers[stage]['ledger_sha256'] == index['binding'][key], 'captured ledger pin differs from actual collection')
    require('execution-binding.json' in index['files'], 'actual evaluation execution binding is missing')
    execution, _ = base.read_json(EVALUATION_COLLECTION / 'execution-binding.json', index['files']['execution-binding.json']['sha256'])
    require(set(execution) == {'schema', 'scientific_input', 'reservation', 'authorization', 'authorization_sha256',
        'model_manifest', 'automatic_retry', 'resume'} and execution['schema'] == 'peano-hydra-retention-evaluation-caller-v1'
        and execution['automatic_retry'] is False and execution['resume'] is False
        and execution['scientific_input'] == resource_request['scientific_inputs']['evaluate']
        and execution['model_manifest'] == index['model_manifest'], 'saved execution caller changed its exact input/model')
    reservation = execution['reservation']
    immutable = evaluation._reservation(reservation)
    expected = {'status': 'job-verified', 'profile': gate.PROFILE, 'run_id': gate.RUN_ID, 'stage': 'evaluate',
        'job_id': request['evaluation_job_id'],
        **{k: remote_identity[k] for k in ('approval_sha256', 'resource_request_sha256', 'source_commit',
            'source_files_sha256', 'payloads_sha256')}, 'reservation': gate.RESERVATIONS['evaluate'],
        'scientific_input': resource_request['scientific_inputs']['evaluate'], 'model_manifest': index['model_manifest'],
        'automatic_retry': False, 'resume': False}
    require(immutable == expected, 'saved live observation does not join the actual released job')
    authorization = api['evaluation_authorization'](bound)
    require(execution['authorization'] == authorization and execution['authorization_sha256'] == digest(authorization)
        == request['authorization_sha256'], 'externally pinned actual evaluation authorization changed')
    evaluation.validate_execution_authorization(bound, execution['authorization'],
        expected_authorization_sha256=request['authorization_sha256'])
    if 'execution-status.json' in index['files']:
        interrupted, _ = base.read_json(EVALUATION_COLLECTION / 'execution-status.json', index['files']['execution-status.json']['sha256'])
        require(interrupted.get('schema') == 'peano-hydra-retention-evaluation-interruption-v1'
            and interrupted.get('status') == 'incomplete-output-retained'
            and interrupted.get('authorization_sha256') == request['authorization_sha256']
            and all(interrupted.get(k) is False for k in ('automatic_retry', 'resume', 'complete_comparison_claimed'))
            and 'evaluation.json' not in index['files'], 'incompatible retained interruption/final-report claims')
    report_check, report = None, None
    if 'evaluation.json' in index['files']:
        report, _ = base.read_json(EVALUATION_COLLECTION / 'evaluation.json', index['files']['evaluation.json']['sha256'],
                                  maximum=evaluation.MAX_REPORT_BYTES)
        # A saved completed report is metadata-checked BEFORE any native replay.
        report_check = evaluation.verify_result(bound, report,
            expected_authorization_sha256=request['authorization_sha256'], replay=False)
    joined = {'local_identity': local_identity, 'actual_remote_identity': remote_identity,
        'actual_released_ledgers': ledgers, 'training_plan_sha256': TRAINING_PLAN_SHA,
        'training_authorization_sha256': manifest['authorization_sha256'],
        'bound_evaluation_plan_sha256': bound.to_dict()['plan_sha256'],
        'authorization_sha256': request['authorization_sha256'],
        'execution_binding_raw_sha256': index['files']['execution-binding.json']['sha256'],
        'baseline_reference': bound.baseline.to_dict(), 'candidate_reference': candidate.to_dict()}
    return bound, joined, report, report_check, protected


def install_worker_guards(source_names):
    """Deny frameworks/network and admit only reviewed Git/ps/native commands.

    This Python guard is additional defense for reviewed source, not an OS
    sandbox. Native workers themselves are the original source-pinned entry
    points under their unchanged OS limits; the outer owner tracks them all.
    """
    forbidden = {'torch', 'transformers', 'peft', 'accelerate', 'tensorflow', 'jax', 'flax', 'safetensors', 'tokenizers'}
    require(not any(name.split('.')[0] in forbidden for name in sys.modules), 'model/tokenizer frameworks already imported')
    failures = {'forbidden_imports': [], 'network_events': [], 'subprocess_events': []}
    counts = {'git_reads': 0, 'native_guard_processes': 0, 'native_process_samplers': 0}
    git_commands = {
        ('git', '-C', str(FROZEN), 'rev-parse', '--show-toplevel'),
        ('git', '-C', str(FROZEN), 'rev-parse', '--verify', 'HEAD'),
        ('git', '-C', str(FROZEN), 'status', '--porcelain', '--untracked-files=all'),
        ('git', '-C', str(FROZEN), 'ls-files', '--error-unmatch', '--', *sorted(source_names)),
    }
    proof = (str(PYTHON), str(FROZEN / 'scripts/hydra_bounded_exec.py'), '--cpu-seconds', '30',
        '--rss-bytes', str(1024**3), '--', str(PYTHON), str(FROZEN / 'scripts/eval_peano_hydra_capacity.py'), '--replay-worker')
    ps = ('/bin/ps', '-axo', 'pid=,pgid=,rss=')
    def deny(kind, value):
        if len(failures[kind]) < 32: failures[kind].append(str(value)[:256])
        raise RuntimeError('read-only replay guard rejected ' + kind + ': ' + str(value)[:256])
    class NoFrameworks(importlib.abc.MetaPathFinder):
        def find_spec(self, fullname, path=None, target=None):
            if fullname.split('.')[0] in forbidden: deny('forbidden_imports', fullname)
            return None
    sys.meta_path.insert(0, NoFrameworks())
    def audit(event, args):
        if event == 'import' and str(args[0]).split('.')[0] in forbidden:
            deny('forbidden_imports', args[0])
        if event.startswith('socket.'):
            deny('network_events', event)
        if event == 'subprocess.Popen':
            command = tuple(str(value) for value in args[1]) if isinstance(args[1], (list, tuple)) else ()
            if command in git_commands:
                counts['git_reads'] += 1
            elif command == proof and str(args[2]) == str(FROZEN):
                counts['native_guard_processes'] += 1
                require(counts['native_guard_processes'] <= 256, 'more than one fresh proof replay per prescribed record')
            elif command == ps:
                counts['native_process_samplers'] += 1
            else: deny('subprocess_events', event)
        if event in ('os.system', 'os.exec', 'os.posix_spawn'):
            deny('subprocess_events', event)
    sys.addaudithook(audit)
    return failures, counts


def validate_external_request(request):
    for name in PIN_FIELDS:
        require(type(request.get(name)) is str and SHA.fullmatch(request[name]), 'real external raw/canonical pin required: ' + name)
    for name in ('train_job_id', 'evaluation_job_id'):
        require(type(request.get(name)) is str and re.fullmatch(r'[1-9][0-9]{0,15}', request[name]),
                'externally observed actual job ID required: ' + name)
    require(request['train_job_id'] != request['evaluation_job_id'], 'training and evaluation require distinct actual jobs')


def worker(request_path, expected_sha):
    base, _ = utilities()
    request, _ = base.read_json(request_path, expected_sha)
    validate_external_request(request)
    require(set(request) == set(PIN_FIELDS) | {'schema', 'supervisor_pid', 'output_directory',
        'train_job_id', 'evaluation_job_id', 'created_at_utc'}
        and request['schema'] == OWNER_SCHEMA and request_path == OUTPUT / 'reservation.json'
        and request['output_directory'] == str(OUTPUT) and os.getppid() == request['supervisor_pid']
        and sys.flags.isolated and sys.dont_write_bytecode and Path(sys.executable) == PYTHON
        and sys.platform == 'darwin' and 'SLURM_JOB_ID' not in os.environ,
        'worker requires the actual one-use owner reservation and fixed isolated local Python')
    require(base.fingerprint(HELPER)[0]['sha256'] == request['helper_sha256'], 'worker helper raw pin differs')
    before_source = source_inputs(base, request['approval_sha256'], deadline=STARTED + 900)
    before_collection = collections(base, request, deadline=STARTED + 900)
    resource_request, _ = base.read_json(FROZEN / PACKAGE / 'resource-request.json', before_source['resource_request_sha256'])
    failures, guard_counts = install_worker_guards(resource_request['source_files'])
    sys.dont_write_bytecode = True
    sys.pycache_prefix = '/dev/null'
    api = runpy.run_path(str(CLI), run_name='_retention_checkpoint_original_cli')
    from training.peano_hydra import retention_evaluation as evaluation
    bound, joined, report, report_check, protected = scientific_join(base, request, before_collection, api)
    cli_output = OUTPUT / 'checkpoint-verification.json'
    argv = ['--verify-checkpoint', str(EVALUATION_COLLECTION / 'checkpoint'),
        '--inputs', str(FROZEN / PACKAGE / 'inputs.json'), '--expected-inputs-sha256', INPUT_SHA,
        '--model-manifest', str(MODEL_COLLECTION / 'model/manifest.json'),
        '--expected-model-manifest-sha256', request['model_manifest_sha256'],
        '--expected-authorization-sha256', request['authorization_sha256'],
        '--expected-checkpoint-head-sha256', request['checkpoint_head_sha256'], '--output', str(cli_output)]
    # The same original metadata-only checkpoint API checks ALL rows before the
    # unchanged CLI may replay any proof. Keep this shared read lock throughout.
    with evaluation.EvaluationCheckpoint(EVALUATION_COLLECTION / 'checkpoint', bound,
        expected_authorization_sha256=request['authorization_sha256'], verify_only=True, replay_proofs=False) as saved:
        rows = saved.rows
        if report is not None:
            require(report['rows'] == rows and report['provider_runtime'] == saved.header['provider_runtime']
                and report['authorization'] == saved.header['authorization'] and len(rows) == 256
                and saved.head['inflight'] is None, 'completed report does not match the entire actual checkpoint')
        sys.argv = [str(CLI), *argv]
        # Actual original CLI main and exact public arguments; no replacement
        # BoundEvaluation, origin receipt, replay implementation or callback.
        code = api['main'](argv)
        require(code == 0, 'unchanged frozen checkpoint verification CLI did not succeed')
        verification_pin, raw = base.fingerprint(cli_output, maximum=api['training'].MAX_METADATA, retain=True)
        verification = json.loads(raw)
        require(verification['schema'] == evaluation.VERIFY_SCHEMA
            and verification['status'] == 'native-prefix-verified' and verification['proof_replay_performed'] is True
            and verification['plan_sha256'] == bound.to_dict()['plan_sha256']
            and verification['checkpoint_head_sha256'] == saved.head['head_sha256']
            and verification['completed_goal_records'] == len(rows) and verification['total_goal_records'] == 256,
            'original replay receipt changed the exact saved prefix identity')
        expected_positive = []
        for slot, row in zip(bound.proposal['ordered_slots'], rows):
            if row['kernel_checked']:
                expected_positive.append({'role': slot['role'], 'max_model_calls': slot['max_model_calls'],
                    'goal': slot['goal'], 'commands_sha256': row['commands_sha256'], 'proof_nodes': row['proof_nodes']})
        replayed = verification['independently_replayed_proofs']
        require([{k: item[k] for k in ('role', 'max_model_calls', 'goal', 'commands_sha256', 'proof_nodes')}
            for item in replayed] == expected_positive
            and guard_counts['native_guard_processes'] == len(expected_positive),
            'each committed positive needs exactly one fresh unchanged native proof replay')
        metrics = evaluation.summarize_outcomes(bound, rows)
        saved.assert_unchanged()
    # Metadata-only report verification above is joined to these same freshly
    # replayed rows. Do not execute a duplicate second round of native proofs.
    report_matches = report is not None and verification['verification_complete'] is True
    require(not any(failures.values()), 'forbidden worker action was attempted')
    evaluation.paired._model_free()
    after_bound, after_joined, after_report, after_report_check, _ = scientific_join(base, request, before_collection, api)
    require(after_bound.to_dict() == bound.to_dict() and after_joined == joined
        and after_report == report and after_report_check == report_check,
        'actual inputs, original receipts, model bytes or scientific binding changed during replay')
    require(collections(base, request, deadline=STARTED + 900) == before_collection
        and source_inputs(base, request['approval_sha256'], deadline=STARTED + 900) == before_source
        and base.fingerprint(HELPER)[0]['sha256'] == request['helper_sha256'],
        'collected proof/model bytes, source or controls changed during replay')
    result = {'schema': SCHEMA,
        'status': 'complete-artifacts-independently-verified' if report_matches else 'committed-prefix-independently-verified',
        **{key: request[key] for key in (*PIN_FIELDS, 'train_job_id', 'evaluation_job_id')},
        'source_commit': COMMIT, 'source_inputs': before_source, 'scientific_binding': joined,
        'checkpoint_verification': dict(verification_pin, path=str(cli_output)), 'verification': verification,
        'checkpoint_raw_head_sha256': request['checkpoint_head_sha256'],
        'checkpoint_raw_header_sha256': before_collection['evaluation']['index']['files']['checkpoint/header.json']['sha256'],
        'committed_rows_sha256': digest(rows),
        'committed_row_files': {f'{number:06d}.goal.json': pin_of(before_collection['evaluation']['index']['files'][
            f'checkpoint/{number:06d}.goal.json']) for number in range(1, len(rows) + 1)},
        'metrics': metrics, 'completed_report_metadata_verification': report_check,
        'complete_report_matches_verified_checkpoint': report_matches,
        'all256_checkpoint_records_independently_verified': verification['verification_complete'],
        'full_comparison_verification_complete': report_matches,
        'completed_report_raw_sha256': None if report is None else before_collection['evaluation']['index']['files']['evaluation.json']['sha256'],
        'original_cli_arguments': argv, 'original_cli_sha256': CLI_SHA, 'original_cli_returncode': code,
        'original_proof_worker_limits': PROOF_LIMITS,
        'original_receipts_and_model_bytes_reauthenticated_after_replay': True,
        'all_collected_entries_retained_and_rechecked': True,
        'guard_attempts': failures, 'guard_counts': guard_counts,
        'python_guard_is_not_an_OS_sandbox': True,
        'whole_call_completion_requires': 'successful owner-result.json AND actual owner process exit zero',
        'claim_boundary': evaluation.CLAIM, **evaluation.CLAIMS, **FALSE_CLAIMS}
    api['files'].guard_output(OUTPUT / 'verification.json', protected=protected)
    base.write_new(OUTPUT / 'verification.json', result)
    require(not any(failures.values()), 'forbidden action during final publication')
    print(json.dumps({'status': result['status'], 'completed_goal_records': len(rows),
        'independently_replayed_proofs': len(replayed), 'whole_call_receipt_required': True}, sort_keys=True), flush=True)
    return 0


def supervise_tree(original, base, command, *, cpu_allowance, deadline, metadata):
    """New declared256-record envelope using unchanged ownership primitives.

    This is deliberately not original.supervise() with a forged/enlarged
    Limits value. The original constructor and all native per-proof guards
    remain unchanged. Only this new caller declares a larger aggregate.
    """
    require(type(command) is tuple and 0 < cpu_allowance <= 600
        and deadline <= STARTED + 880 and time.monotonic() < deadline - 5,
        'finite remaining aggregate allowance and postcheck/cleanup reserve required')
    run_deadline, data_cap = deadline - 5, LIMITS['retained_output_bytes'] - 1024**2
    process = ownership = None
    selector, logs, descriptors = selectors.DefaultSelector(), {}, {}
    reason, error, usage, cleanup_record = 'exited', None, None, None
    baseline_self, baseline_children = resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)
    sampled_cpu = accounted_cpu = streamed_bytes = next_sample = 0
    controller_usage_removed = 0
    def account():
        own, children = resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)
        own_cpu = own.ru_utime + own.ru_stime - baseline_self.ru_utime - baseline_self.ru_stime
        sampler_cpu = max(0.0, children.ru_utime + children.ru_stime
            - baseline_children.ru_utime - baseline_children.ru_stime - controller_usage_removed)
        return max(sampled_cpu, controller_usage_removed) + own_cpu + sampler_cpu, own_cpu, sampler_cpu
    try:
        original.snapshot()  # macOS visibility must work BEFORE any target runs.
        for label in ('stdout', 'stderr'):
            logs[label] = os.open(OUTPUT / (label + '.log'),
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        environment = original._environment()
        environment.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', HF_DATASETS_OFFLINE='1',
            USE_TORCH='0', USE_TF='0', USE_FLAX='0', TOKENIZERS_PARALLELISM='false',
            CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1')
        process = subprocess.Popen((str(PYTHON), '-I', '-B', str(SUPERVISOR), '--owned-entry'),
            cwd=FROZEN, env=environment, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, start_new_session=True, close_fds=True)
        ownership = original.Ownership(process.pid)
        ownership.update(original.snapshot())
        process.stdin.write(canonical({'command': list(command), 'cwd': str(FROZEN),
            'cpu_seconds': LIMITS['controller_cpu_seconds']}))
        process.stdin.close()
        for label, stream in (('stdout', process.stdout), ('stderr', process.stderr)):
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_READ, label)
        while True:
            now = time.monotonic()
            if now >= run_deadline:
                reason = 'whole-wall-precleanup-boundary'; break
            reaped = original._reap(process)
            if reaped is not None:
                usage, controller_usage_removed = reaped, reaped['cpu_seconds']
            if now >= next_sample:
                sampled_cpu, combined_rss = ownership.update(original.snapshot(), controller_exited=process.returncode is not None)
                accounted_cpu, _, _ = account()
                if accounted_cpu >= cpu_allowance:
                    reason = 'sampled-aggregate-cpu-limit'; break
                if combined_rss >= LIMITS['sampled_parent_and_owned_tree_rss_bytes']:
                    reason = 'sampled-combined-rss-limit'; break
                if original.retained_bytes(OUTPUT) >= data_cap:
                    reason = 'retained-output-limit'; break
                next_sample = time.monotonic() + original.SAMPLE_SECONDS
            for key, _ in selector.select(.02):
                block = os.read(key.fileobj.fileno(), 65536)
                if not block:
                    selector.unregister(key.fileobj); continue
                room = max(0, min(data_cap - original.retained_bytes(OUTPUT), LIMITS['combined_pipe_bytes'] - streamed_bytes))
                kept = block[:room]
                while kept:
                    wrote = os.write(logs[key.data], kept)
                    require(wrote > 0, 'owned log write did not progress')
                    kept = kept[wrote:]
                streamed_bytes += len(block)
                if len(block) > room:
                    reason = 'retained-or-pipe-output-limit'; break
            if reason != 'exited': break
            if process.returncode is not None and not ownership.live and not selector.get_map(): break
        if reason == 'exited' and process.returncode != 0: reason = 'controller-failed'
    except BaseException as failure:
        reason, error = 'guard-failed', type(failure).__name__ + ': ' + ' '.join(str(failure).split())[:2000]
    finally:
        if process is not None:
            # Ownership is constructed immediately after Popen. Its unchanged
            # cleanup handles even an unobserved child/sampler failure safely.
            if ownership is None: ownership = original.Ownership(process.pid)
            cleanup_record, cleanup_usage = original.cleanup(process, ownership, deadline=deadline)
            usage = usage or cleanup_usage
            for stream in (process.stdin, process.stdout, process.stderr):
                if stream is not None and not stream.closed: stream.close()
        selector.close()
        for fd in logs.values():
            os.fsync(fd); os.close(fd)
    for label in logs:
        descriptors[label] = base.fingerprint(OUTPUT / (label + '.log'), maximum=LIMITS['combined_pipe_bytes'])[0]
    retained = original.retained_bytes(OUTPUT)  # scan BEFORE final CPU/RSS sample
    sampled_cpu = 0 if ownership is None else sum(row['cpu_seconds'] for row in ownership.records.values())
    controller_usage_removed = 0 if usage is None else usage['cpu_seconds']
    accounted_cpu, own_cpu, sampler_cpu = account()
    live = [] if ownership is None else sorted(ownership.live)
    peak = max(parent_peak(), 0 if ownership is None else ownership.peak_rss,
        0 if usage is None else usage['peak_rss_bytes'])
    quiescent = (process is not None and process.returncode is not None and cleanup_record is not None
        and cleanup_record['controller_reaped'] and not cleanup_record['remaining_live_owned_pids']
        and not cleanup_record['errors'] and not live)
    success = (reason == 'exited' and process is not None and process.returncode == 0 and quiescent
        and time.monotonic() <= deadline and accounted_cpu < cpu_allowance
        and peak < LIMITS['sampled_parent_and_owned_tree_rss_bytes'] and retained < data_cap
        and streamed_bytes <= LIMITS['combined_pipe_bytes'])
    return {'schema': SUPERVISION_SCHEMA, 'status': 'completed-with-open-gates' if success else 'stopped-or-failed',
        'reason': reason, 'error': error, 'command': list(command), 'cwd': str(FROZEN),
        'original_ownership_helper_sha256': SUPERVISOR_SHA, 'original_limits_constructor_changed': False,
        'new_whole_envelope': LIMITS, 'remaining_tree_cpu_allowance_seconds': cpu_allowance,
        'tree_deadline_seconds_from_helper_entry': deadline - STARTED, 'wall_seconds_from_helper_entry': time.monotonic() - STARTED,
        'returncode': None if process is None else process.returncode, 'owned_group_quiescent': quiescent,
        'accounted_cpu_lower_bound_seconds': accounted_cpu, 'sampled_owned_process_cpu_seconds': sampled_cpu,
        'supervisor_self_cpu_seconds': own_cpu, 'waited_sampler_cpu_seconds': sampler_cpu,
        'peak_sampled_combined_rss_bytes': peak,
        'max_observed_live_owned_processes': 0 if ownership is None else ownership.max_live,
        'post_controller_exit_live_samples': 0 if ownership is None else ownership.post_controller_exit_samples,
        'observed_processes': [] if ownership is None else list(ownership.records.values()),
        'controller_wait4': usage, 'cleanup': cleanup_record, 'remaining_live_owned_pids': live,
        'logs': descriptors, 'pipe_bytes_observed': streamed_bytes, 'retained_bytes_before_receipt': retained,
        'metadata': metadata, 'measurement': {
            'cpu': 'max of sampled owned PID CPU and controller wait4, plus parent and waited sampler CPU',
            'cpu_is_exact_aggregate': False, 'rss_is_instantaneous_hard_cap': False,
            'ownership': 'unchanged PID/start identity with ancestry tracked across reparenting and sessions',
            'limitations': 'short-lived processes and between-sample tails may be missed; ps birth identity has one-second precision; no hostile-daemon sandbox'},
        **FALSE_CLAIMS}


def main(argv=None):
    if argv is None and len(sys.argv) == 4 and sys.argv[1] == '--worker':
        return worker(Path(sys.argv[2]), sys.argv[3])
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    for name in PIN_FIELDS:
        parser.add_argument('--' + name.replace('_', '-'), required=True)
    parser.add_argument('--train-job-id', required=True)
    parser.add_argument('--evaluation-job-id', required=True)
    args = parser.parse_args(argv)
    values = vars(args)
    validate_external_request(values)
    require(sys.flags.isolated and sys.dont_write_bytecode and sys.platform == 'darwin'
        and Path(sys.executable) == PYTHON and Path(__file__).absolute() == HELPER
        and sys.version_info[:2] == (3, 11)
        and not any(name.startswith(('SLURM_', 'SBATCH_', 'LD_', 'DYLD_')) for name in os.environ),
        'exact isolated local owner Python outside allocations required')
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_CPU, (180, 181))
    resource.setrlimit(resource.RLIMIT_FSIZE, (LIMITS['output_file_bytes'], LIMITS['output_file_bytes']))
    def wall_limit(*_): raise TimeoutError('whole900-second local replay wall boundary')
    signal.signal(signal.SIGALRM, wall_limit)
    signal.setitimer(signal.ITIMER_REAL, max(.001, 900 - (time.monotonic() - STARTED)))
    base, original = utilities()
    require(base.fingerprint(HELPER)[0]['sha256'] == args.helper_sha256
        and base.fingerprint(PYTHON)[0]['sha256'] == PYTHON_SHA, 'externally reviewed caller/Python pin differs')
    require(base.exact_path(OUTPUT, exists=False) == OUTPUT and OUTPUT.parent == ARCHIVE
        and not os.path.lexists(OUTPUT), 'fresh fixed one-use verification directory required')
    os.mkdir(OUTPUT, 0o700)
    reservation = {'schema': OWNER_SCHEMA, 'supervisor_pid': os.getpid(), 'output_directory': str(OUTPUT),
        **values, 'created_at_utc': datetime.now(timezone.utc).isoformat()}
    reservation_pin = base.write_new(OUTPUT / 'reservation.json', reservation)
    process = process_pin = verification = verification_pin = before = collection_before = None
    prefix_cpu = returned_cpu = None
    failure = None
    try:
        before = source_inputs(base, args.approval_sha256, deadline=STARTED + 875)
        collection_before = collections(base, values, deadline=STARTED + 875)
        prefix_cpu = current_cpu()
        require(prefix_cpu < 598 and parent_peak() < LIMITS['sampled_parent_and_owned_tree_rss_bytes'],
                'initial metadata exhausted whole-call allowance')
        command = (str(PYTHON), '-I', '-B', str(HELPER), '--worker', str(OUTPUT / 'reservation.json'), reservation_pin['sha256'])
        process = supervise_tree(original, base, command, cpu_allowance=598 - prefix_cpu, deadline=STARTED + 880,
            metadata={'reservation_sha256': reservation_pin['sha256'], 'helper_sha256': args.helper_sha256,
                'purpose': 'independent original native replay of actual retention DEV checkpoint; no inference'})
        returned_cpu = current_cpu()
        process_pin = base.write_new(OUTPUT / 'supervision.json', process)
        require(process['status'] == 'completed-with-open-gates' and process['returncode'] == 0
            and process['owned_group_quiescent'] is True and not process['remaining_live_owned_pids'],
            'independent replay did not finish within its owned process envelope')
        require(source_inputs(base, args.approval_sha256, deadline=STARTED + 900) == before
            and collections(base, values, deadline=STARTED + 900) == collection_before,
            'frozen source/actual controls/original collected bytes changed during verification')
        verification_pin, raw = base.fingerprint(OUTPUT / 'verification.json', maximum=LIMITS['output_file_bytes'], retain=True,
                                                 deadline=STARTED + 900)
        verification = json.loads(raw)
        require(verification['schema'] == SCHEMA
            and verification['status'] in ('complete-artifacts-independently-verified', 'committed-prefix-independently-verified')
            and all(verification[key] == values[key] for key in (*PIN_FIELDS, 'train_job_id', 'evaluation_job_id'))
            and verification['original_cli_returncode'] == 0
            and verification['original_receipts_and_model_bytes_reauthenticated_after_replay'] is True
            and verification['all_collected_entries_retained_and_rechecked'] is True
            and not any(verification['guard_attempts'].values()), 'worker result does not bind the actual external pins')
        require(base.fingerprint(OUTPUT / 'checkpoint-verification.json')[0] == pin_of(verification['checkpoint_verification'])
            and base.fingerprint(HELPER)[0]['sha256'] == args.helper_sha256
            and base.fingerprint(BASE)[0]['sha256'] == BASE_SHA
            and base.fingerprint(SUPERVISOR)[0]['sha256'] == SUPERVISOR_SHA, 'verification output or reviewed callers changed')
    except (ValueError, OSError, KeyError, TypeError, RuntimeError, TimeoutError, KeyboardInterrupt) as error:
        failure = type(error).__name__ + ': ' + ' '.join(str(error).split())[:2048]
    retained = original.retained_bytes(OUTPUT)
    current = current_cpu()
    accounted = current if process is None or returned_cpu is None else base.whole_cpu_lower_bound(
        prefix_cpu, process['accounted_cpu_lower_bound_seconds'], returned_cpu, current)
    peak = max(parent_peak(), 0 if process is None else process['peak_sampled_combined_rss_bytes'])
    elapsed = time.monotonic() - STARTED
    if accounted >= 600: failure = failure or 'whole-call CPU boundary reached'
    if peak >= LIMITS['sampled_parent_and_owned_tree_rss_bytes']: failure = failure or 'whole-call observed RSS boundary reached'
    if retained >= LIMITS['retained_output_bytes'] - 1024**2: failure = failure or 'no bounded final receipt space remains'
    if elapsed >= 900: failure = failure or 'whole-call wall boundary reached'
    complete = failure is None and verification['complete_report_matches_verified_checkpoint'] is True
    result = {'schema': OWNER_SCHEMA, 'status': 'incomplete' if failure is not None else
            ('complete-artifacts-verified-within-envelope' if complete else 'prefix-verified-within-envelope'),
        'error': failure, **values, 'source_commit': COMMIT, 'source_inputs': before,
        'reservation_file': reservation_pin, 'supervision_file': process_pin, 'verification_file': verification_pin,
        'checkpoint_verification_file': None if verification is None else verification['checkpoint_verification'],
        'original_ownership_helper_sha256': SUPERVISOR_SHA, 'original_utility_helper_sha256': BASE_SHA,
        'whole_limits': LIMITS, 'original_proof_worker_limits': PROOF_LIMITS,
        'measurements': {'accounted_whole_cpu_lower_bound_seconds': accounted, 'whole_wall_seconds': elapsed,
            'parent_peak_rss_bytes': parent_peak(), 'peak_sampled_parent_plus_tree_rss_bytes': peak,
            'post_supervision_accounted_cpu_seconds': None if returned_cpu is None else current - returned_cpu,
            'retained_output_bytes_before_owner_result': retained},
        'owned_group_quiescent': process is not None and process['owned_group_quiescent'] is True,
        'worker_returncode': None if process is None else process['returncode'],
        'remaining_live_owned_pids': None if process is None else process['remaining_live_owned_pids'],
        'completed_goal_records': None if verification is None else verification['verification']['completed_goal_records'],
        'all256_checkpoint_records_independently_verified': failure is None and verification['all256_checkpoint_records_independently_verified'],
        'complete_report_matches_verified_checkpoint': complete, 'full_comparison_verification_complete': complete,
        'cpu_is_exact_aggregate': False, 'rss_is_instantaneous_hard_cap': False,
        'whole_call_completion_requires': 'this receipt successful AND the actual owner process exit zero',
        **FALSE_CLAIMS}
    require(retained + len(canonical(result)) + 1 <= LIMITS['retained_output_bytes'], 'owner receipt exceeds retained output cap')
    result_pin = base.write_new(OUTPUT / 'owner-result.json', result)
    # Include publication CPU, RSS, output scan and wall tail. A late failure
    # never overwrites its receipt; the nonzero owner exit makes it ineligible.
    final_retained = original.retained_bytes(OUTPUT)
    final_cpu = current_cpu()
    final_accounted = final_cpu if process is None or returned_cpu is None else base.whole_cpu_lower_bound(
        prefix_cpu, process['accounted_cpu_lower_bound_seconds'], returned_cpu, final_cpu)
    require(final_accounted < 600 and time.monotonic() - STARTED < 900
        and parent_peak() < LIMITS['sampled_parent_and_owned_tree_rss_bytes']
        and final_retained <= LIMITS['retained_output_bytes'], 'whole-call boundary during final owner publication')
    print(json.dumps({'status': result['status'], 'output_directory': str(OUTPUT), 'owner_result': result_pin,
        'completed_goal_records': result['completed_goal_records'], 'full_comparison_verification_complete': complete}, sort_keys=True), flush=True)
    signal.setitimer(signal.ITIMER_REAL, 0)
    return 0 if failure is None else 2


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError, TypeError, RuntimeError, TimeoutError, KeyboardInterrupt) as error:
        print('local-retention-checkpoint-verification: ' + ' '.join(str(error).split())[:2048], file=sys.stderr, flush=True)
        raise SystemExit(2)
