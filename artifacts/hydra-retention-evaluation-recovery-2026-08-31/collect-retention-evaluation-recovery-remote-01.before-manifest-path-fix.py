"""Retain actual terminal retention-evaluation evidence, never proof scores.

File traversal/hash/USTAR primitives are copied unchanged from reviewed model
and diagnostic collectors. Only the genuine frozen recovery gate authenticates the new job/ledger,
separate fully consumed original jobs, and the completed candidate manifest. Inspection omits
proof rows; full collection requires externally observed HEAD/manifest pins.
"""
import time
STARTED = time.monotonic()
import datetime
import fcntl
import hashlib
import importlib
import importlib.abc
import io
import json
import os
from pathlib import Path
import re
import resource
import signal
import stat
import sys
import tarfile

# All read paths are relative to this one fixed ancestor. The new deployment
# and original producer history remain explicitly separate, immutable scopes.
ROOT = '/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training'
PREFIX = 'experiments/retention-evaluation-recovery-v1'
EXECUTION_ROOT = ROOT + '/' + PREFIX
PRODUCER_PREFIX = 'experiments/retention-pilot-v1'
PROFILE, RUN_ID = 'peano-hydra-retention-evaluation-recovery-v1', 'retention-evaluation-recovery-v1'
PACKAGE_NAME = '_deploy/hydra-retention-evaluation-recovery-v1'
PACKAGE = PREFIX + '/' + PACKAGE_NAME
RESULT = PREFIX + '/results/peano-hydra/evaluations/retention-evaluation-recovery-v1'
MODEL = PRODUCER_PREFIX + '/results/peano-hydra/qwen3-1.7b-authority-primitive-retention-pilot-v1'
CHECKPOINT = RESULT + '/checkpoint'
PRODUCER_COMMIT = '4aeae795c8cb5bfc622c9943359b5b38446089b9'
TRAINING_JOB, FAILED_EVALUATION_JOB = '21456251', '21457058'
MODEL_MANIFEST = {'bytes': 191597, 'sha256': 'cdacbda7777568120029b671374aaf16e994f2da2a54b867a00c81ece086d6ca'}
EVALUATION_PLAN = {'path': PACKAGE_NAME + '/evaluation-plan.json', 'bytes': 110574,
    'sha256': '7dd90249324b82846f6cbae6e157c5fef09e22e0b058b73822f11aae1b95f635'}
TRAINING_INPUTS_SHA = 'e78399c688a1cf255567b15d6e130e478ba10a4c1d79f60775f55d477ef9aa3d'
PRODUCER_REFERENCE = {
    'schema': 'peano-hydra-preserved-retention-producer-v1', 'source_commit': PRODUCER_COMMIT,
    'source_manifest_sha256': '4f4fcbfcd51ff64b9674dfdde383b37337871d93f52792b3f6f9bedec6862665',
    'inputs_sha256': '3df7953c0d405364aef689b5e67b083f5fc744492159643ca5b09e418a06a388',
    'training_plan_sha256': 'da26332740d587bdd946b12999fd37de73817115ed3da8983edf5004bd02abf0',
    'trainer_sha256': 'd6529651c031fce3fe535f7b8b9ccbbb3396125083640184f7125065b9e26725',
    'evaluation_source_sha256': '1f42a76f0c1127b7edd2ce171c0e238b5846941a40b1c5cd185f676b9dc5bf92'}
PRODUCER = {
    'source_commit': PRODUCER_COMMIT, 'training_job_id': TRAINING_JOB, 'failed_evaluation_job_id': FAILED_EVALUATION_JOB,
    'model_manifest': MODEL_MANIFEST, 'approval_sha256': '556cef2186a2003bf90ea327b927cc6cb3ea6ec0bd57f65e421bb6841e74d233',
    'resource_request_sha256': '67e0be409cf42ac90048029632479328e9b98b19c4f44f637f1fab6b5392f361',
    'source_header_sha256': '224ad02b154eb32a64e07cfd02710f81020cb4b108c83d6514b2dcf918802333',
    'training_ledger_sha256': '3d1b5fa3114c4e7bbe0cbb7f6fee526bd46ecc99bd9a470aefcdd0b95e53ecb6',
    'failed_evaluation_ledger_sha256': 'acdde37ddabdca99602b937939ba33848ba2946fa104367595ceb71a086049b3',
    'reserved_gpu_seconds': 10800, 'reservations_fully_consumed': True, 'reservation_reuse_allowed': False, 'refunds': False}
RESERVATION = {'seconds': 3600, 'gpus': 1, 'cpus': 8, 'memory_gib': 64}
INDEX_SCHEMA = 'peano-hydra-retention-evaluation-recovery-collection-index-v1'
MAX_JSON, MAX_TOTAL, MAX_CHECKPOINT_FILE = 4 * 1024**2, 64 * 1024**2, 4 * 1024**2
MAX_CHECKPOINT_ENTRIES, MAX_DATA_FILES, MAX_CHECKPOINT_DEPTH = 264, 288, 8
CPU, WALL, ADDRESS_SPACE = 20, 120, 320 * 1024**2
BOOTSTRAP_SOURCES = {
    'training/peano_hydra/__init__.py': 'b1decc860e0951b02bd1f175078a1a0ff0e3b59b41aa9ce6d6de8cc65473f298',
    'training/peano_hydra/retention_evaluation_recovery_launch.py': 'dfe56aef1ba17c1fa49473858070d89d6e34bd5f0b0316351546cf5d2e14e88d',
    'training/peano_hydra/search_launch.py': '3d393ceb547c5199297748af647c7c6c51c67bf176011dcd68b257dc6d3f97ca'}
TERMINAL = {'COMPLETED', 'FAILED', 'TIMEOUT', 'CANCELLED', 'OUT_OF_MEMORY',
            'NODE_FAIL', 'PREEMPTED', 'BOOT_FAIL', 'DEADLINE', 'REVOKED'}
MANDATORY = {'model-manifest.json', 'evaluate-ledger.jsonl', 'producer-train-ledger.jsonl',
    'producer-failed-evaluate-ledger.jsonl', 'producer-approval.json', 'producer-resource-request.json',
    'producer-source-provenance.tsv', 'approval.json', 'resource-request.json', 'evaluate-request.json',
    'inputs.json', 'preflight.json', 'admission.json', 'evaluation-plan.json'}
INSPECTION_ENTRIES = ('HEAD.json', 'header.json', '.lock')

def require(value, message):
    if not value: raise ValueError(message)

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()

def sha(raw): return hashlib.sha256(raw).hexdigest()

def decode(raw):
    require(type(raw) is bytes and 0 < len(raw) <= MAX_JSON, 'metadata byte cap')
    def pairs(items):
        value = {}
        for key, item in items:
            require(key not in value, 'duplicate metadata key')
            value[key] = item
        return value
    value = json.loads(raw, object_pairs_hook=pairs,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite metadata')))
    require(type(value) is dict, 'metadata object required')
    canonical(value)
    return value

def path_name(name):
    require(type(name) is str and re.fullmatch(r'[A-Za-z0-9_./-]{1,1024}', name)
            and all(part not in ('', '.', '..') for part in name.split('/')), 'unsafe relative collection path')
    return name

def directory(path):
    path = Path(path)
    require(path.is_absolute() and '..' not in path.parts and len(path.parts) <= 64, 'unsafe directory')
    access = getattr(os, 'O_PATH', os.O_RDONLY)
    fd = os.open(path.anchor, access | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for number, part in enumerate(path.parts[1:], 1):
            flags = os.O_RDONLY if number == len(path.parts) - 1 else access
            child = os.open(part, flags | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd); fd = child
        result, fd = fd, -1
        return result
    finally:
        if fd >= 0: os.close(fd)

def signature(info):
    return (info.st_dev, info.st_ino, info.st_mode, info.st_size, info.st_mtime_ns, info.st_ctime_ns, info.st_nlink)

def opened(relative, maximum):
    path_name(relative)
    parent_name, leaf = (ROOT + '/' + relative).rsplit('/', 1)
    parent = directory(parent_name)
    try: fd = os.open(leaf, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
    finally: os.close(parent)
    stream = os.fdopen(fd, 'rb')
    before = os.fstat(fd)
    try:
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and 0 <= before.st_size <= maximum,
                'collection input is not a bounded single-link regular file')
    except BaseException:
        stream.close(); raise
    return stream, before

def read_file(relative, maximum, retain=False):
    stream, before = opened(relative, maximum)
    with stream:
        checksum, count, body = hashlib.sha256(), 0, bytearray()
        while True:
            require(time.monotonic() - STARTED < WALL, 'remote collection whole-call wall deadline')
            block = stream.read(65536)
            if not block: break
            count += len(block); checksum.update(block)
            require(count <= maximum, 'collection input grew beyond cap')
            if retain: body.extend(block)
        require(count == before.st_size and signature(before) == signature(os.fstat(stream.fileno())),
                'collection input changed during hashing')
    current, now = opened(relative, maximum)
    current.close()
    require(signature(now) == signature(before), 'collection input was replaced')
    return {'bytes': count, 'sha256': checksum.hexdigest()}, bytes(body), signature(before)

class NoFrameworks(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        require(fullname.split('.')[0] not in {'torch', 'transformers', 'peft', 'tokenizers', 'accelerate', 'datasets', 'vllm'},
                'collection cannot import a model/tokenizer framework')
        return None

def checkpoint_inventory():
    """Retain every bounded real entry; reject links/specials, never filter debris."""
    try:
        root_fd = directory(ROOT + '/' + CHECKPOINT)
    except FileNotFoundError:
        return {'present':False, 'root_signature':None, 'entries':{}}
    entries = {}
    root_before = signature(os.fstat(root_fd))
    def visit(fd, prefix, depth):
        require(depth <= MAX_CHECKPOINT_DEPTH, 'checkpoint directory depth cap')
        with os.scandir(fd) as stream:
            for entry in stream:
                name = prefix + entry.name
                require(re.fullmatch(r'[A-Za-z0-9_./-]{1,1024}', name)
                        and all(part not in ('', '.', '..') for part in name.split('/')),
                        'unsafe checkpoint entry name')
                require(name not in entries and len(entries) < MAX_CHECKPOINT_ENTRIES,
                        'checkpoint entry count or alias cap')
                info = entry.stat(follow_symlinks=False)
                require(not stat.S_ISLNK(info.st_mode), 'checkpoint symlink rejected without dereference')
                if stat.S_ISDIR(info.st_mode):
                    item = {'kind':'directory', 'source_signature':list(signature(info)),
                            'source_mode':stat.S_IMODE(info.st_mode)}
                else:
                    require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1
                            and 0 <= info.st_size <= MAX_CHECKPOINT_FILE,
                            'checkpoint entry is not bounded regular single-link data')
                    item = {'kind':'file', 'bytes':info.st_size,
                            'source_signature':list(signature(info)), 'source_mode':stat.S_IMODE(info.st_mode)}
                entries[name] = item
                # Validate USTAR representability before writing any transport bytes.
                test = tarfile.TarInfo('checkpoint/' + name + ('/' if item['kind'] == 'directory' else ''))
                test.type = tarfile.DIRTYPE if item['kind'] == 'directory' else tarfile.REGTYPE
                test.tobuf(format=tarfile.USTAR_FORMAT)
                if item['kind'] == 'directory':
                    child = os.open(entry.name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                    try:
                        require(signature(os.fstat(child)) == tuple(item['source_signature']),
                                'checkpoint subdirectory changed before inventory')
                        visit(child, name + '/', depth + 1)
                        require(signature(os.fstat(child)) == tuple(item['source_signature']),
                                'checkpoint subdirectory changed during inventory')
                    finally:
                        os.close(child)
                    require(signature(os.stat(entry.name, dir_fd=fd, follow_symlinks=False))
                            == tuple(item['source_signature']), 'checkpoint directory pathname changed')
    try:
        visit(root_fd, '', 0)
        require(signature(os.fstat(root_fd)) == root_before, 'checkpoint root changed during inventory')
    finally:
        os.close(root_fd)
    again = directory(ROOT + '/' + CHECKPOINT)
    try:
        require(signature(os.fstat(again)) == root_before, 'checkpoint root pathname changed')
    finally:
        os.close(again)
    return {'present':True, 'root_signature':list(root_before), 'entries':dict(sorted(entries.items()))}


def control_binding(read_payload, source_commit, approval_sha):
    """Raw control joins only; never invoke the historical scientific loader."""
    require(re.fullmatch(r'[0-9a-f]{40}', source_commit) and source_commit != PRODUCER_COMMIT,
            'actual new frozen source commit required')
    approval_raw, request_raw = read_payload('approval.json'), read_payload('resource-request.json')
    approval, request = decode(approval_raw), decode(request_raw)
    require(sha(approval_raw) == approval_sha
            and approval.get('schema') == 'peano-hydra-retention-evaluation-recovery-standing-resource-approval-v1'
            and approval.get('approved') is True and approval.get('profile') == PROFILE
            and approval.get('run_id') == RUN_ID and approval.get('request_file_sha256') == sha(request_raw)
            and approval.get('standing_authority_sha256') == '04ac3b5997b4f2a78c4ce41642b9e596d63abf1c82ec2441ab240b0f78fd5778',
            'actual new resource approval changed')
    require(request.get('schema') == 'peano-hydra-retention-evaluation-recovery-resource-request-v1'
            and request.get('status') == 'ready' and request.get('profile') == PROFILE and request.get('run_id') == RUN_ID
            and request.get('source_commit') == source_commit and request.get('producer') == PRODUCER
            and request.get('model_manifest') == MODEL_MANIFEST and request.get('evaluation_plan') == EVALUATION_PLAN
            and request.get('reservations') == {'evaluate': RESERVATION}
            and request.get('maximum_aggregate_gpu_seconds') == 3600 and request.get('maximum_concurrent_gpus') == 1
            and all(request.get(key) is False for key in
                ('training_authorized', 'automatic_retry', 'resume', 'refunds', 'historical_checkpoint_reuse_allowed'))
            and request.get('evaluation_scope') == 'old-dev32-and-frontier-dev32-at-8-and-16-calls'
            and set(request['scientific_inputs']) == {'evaluate'},
            'actual recovery source/model/producer/resource scope changed')
    payloads = request['payloads']
    require(request['payloads_sha256'] == sha(canonical(payloads)), 'actual recovery payload identity changed')
    def record(name, descriptor):
        require(type(descriptor) is dict and set(descriptor) == {'path', 'bytes', 'sha256'}
                and descriptor['path'] == PACKAGE_NAME + '/' + name
                and payloads.get(descriptor['path']) == {key: descriptor[key] for key in ('bytes', 'sha256')},
                'exact closed scientific payload descriptor changed')
        raw = read_payload(name)
        require({'bytes': len(raw), 'sha256': sha(raw)} == {key: descriptor[key] for key in ('bytes', 'sha256')},
                'actual scientific payload bytes changed')
        return decode(raw)
    stage_descriptor = request['scientific_inputs']['evaluate']
    stage = record('evaluate-request.json', stage_descriptor)
    fields = {'schema', 'profile', 'run_id', 'stage', 'inputs', 'preflight', 'evaluation_plan_sha256',
        'bound_evaluation_plan_sha256', 'model_manifest', 'producer_source_commit', 'training_job_id',
        'failed_evaluation_job_id', 'output', 'training_authorized', 'automatic_retry', 'resume',
        'historical_checkpoint_reuse_allowed'}
    require(set(stage) == fields and stage['schema'] == 'peano-hydra-retention-evaluation-recovery-stage-request-v1'
            and stage['profile'] == PROFILE and stage['run_id'] == RUN_ID and stage['stage'] == 'evaluate'
            and stage['model_manifest'] == MODEL_MANIFEST and stage['producer_source_commit'] == PRODUCER_COMMIT
            and stage['training_job_id'] == TRAINING_JOB and stage['failed_evaluation_job_id'] == FAILED_EVALUATION_JOB
            and stage['evaluation_plan_sha256'] == EVALUATION_PLAN['sha256']
            and stage['output'] == 'results/peano-hydra/evaluations/' + RUN_ID
            and all(stage[key] is False for key in ('training_authorized', 'automatic_retry', 'resume',
                                                     'historical_checkpoint_reuse_allowed')),
            'actual evaluation-only scientific request changed')
    inputs = record('inputs.json', stage['inputs'])
    preflight = record('preflight.json', stage['preflight'])
    admission = record('admission.json', request['historical_admission'])
    record('evaluation-plan.json', EVALUATION_PLAN)
    require(set(inputs) == {'schema', 'profile', 'run_id', 'candidate_reference', 'locations', 'evaluation_plan'}
            and inputs['schema'] == 'peano-hydra-retention-evaluation-recovery-inputs-v1'
            and inputs['profile'] == PROFILE and inputs['run_id'] == RUN_ID
            and inputs['evaluation_plan'] == EVALUATION_PLAN
            and set(inputs['locations']) == {'local', 'helios'}, 'actual recovery inputs changed')
    candidate = inputs['candidate_reference']
    require(type(candidate) is dict and set(candidate) == {'schema', 'manifest_sha256', 'training_inputs',
                                                          'producer', 'admission_receipt_sha256'}
            and candidate['schema'] == 'peano-hydra-preserved-retention-artifact-reference-v1'
            and candidate['manifest_sha256'] == MODEL_MANIFEST['sha256']
            and candidate['producer'] == PRODUCER_REFERENCE
            and sha(canonical(candidate['training_inputs'])) == TRAINING_INPUTS_SHA
            and candidate['admission_receipt_sha256'] == request['historical_admission']['sha256']
            and inputs['locations']['helios']['manifest_path'] == ROOT + '/' + MODEL
            and inputs['locations']['helios']['admission_receipt_path'] == EXECUTION_ROOT + '/' + PACKAGE_NAME + '/admission.json',
            'historical candidate/raw custody or actual remote model location changed')
    require(admission.get('schema') == 'peano-hydra-preserved-retention-admission-custody-v1'
            and admission.get('status') == 'completed-caller-admission', 'actual completed caller custody required')
    preflight_fields = {'schema', 'profile', 'run_id', 'inputs_sha256', 'candidate_reference', 'model_manifest',
        'evaluation_plan', 'bound_evaluation_plan', 'model_weights_loaded', 'gpu_allocated',
        'training_authorized', 'native_proof_replay_performed'}
    require(set(preflight) == preflight_fields
            and preflight['schema'] == 'peano-hydra-retention-evaluation-recovery-input-check-v1'
            and preflight['profile'] == PROFILE and preflight['run_id'] == RUN_ID
            and preflight['inputs_sha256'] == stage['inputs']['sha256']
            and preflight['candidate_reference'] == candidate and preflight['model_manifest'] == MODEL_MANIFEST
            and preflight['evaluation_plan'] == EVALUATION_PLAN
            and all(preflight[key] is False for key in
                ('model_weights_loaded', 'gpu_allocated', 'training_authorized', 'native_proof_replay_performed')),
            'actual metadata preflight changed its input/admission/model scope')
    plan = preflight['bound_evaluation_plan']
    require(plan['plan_sha256'] == stage['bound_evaluation_plan_sha256']
            and sha(canonical({key: value for key, value in plan.items() if key != 'plan_sha256'})) == plan['plan_sha256'],
            'actual preflight bound plan changed')
    authorization = {'schema': 'peano-hydra-retention-evaluation-authorization-v1',
        'authorization_id': RUN_ID + '-evaluation', 'plan_sha256': plan['plan_sha256'],
        'execution_binding_sha256': plan['execution_binding']['execution_binding_sha256'],
        'model_inference_authorized': True, 'gpu_count': 1, 'max_wall_seconds': 3300,
        'max_model_calls': 3072, 'max_goal_records': 256, 'external_hard_wall_limit_required': True,
        'training_authorized': False, 'upload_authorized': False, 'new_allocation_authorized': False,
        'automatic_retry': False, 'resume': False, 'historical_checkpoint_reuse_allowed': False}
    return {'approval_sha256': approval_sha, 'resource_request_sha256': sha(request_raw),
        'source_commit': source_commit, 'source_files_sha256': sha(canonical(request['source_files'])),
        'payloads_sha256': request['payloads_sha256'], 'producer_sha256': sha(canonical(PRODUCER)),
        'evaluation_request_sha256': stage_descriptor['sha256'],
        'inputs_sha256': stage['inputs']['sha256'], 'preflight_sha256': stage['preflight']['sha256'],
        'historical_admission_sha256': request['historical_admission']['sha256'],
        'historical_admission': request['historical_admission'], 'candidate_reference': candidate,
        'scientific_input': stage_descriptor, 'preflight': stage['preflight'],
        'bound_evaluation_plan_sha256': plan['plan_sha256'],
        'authorization': authorization, 'authorization_sha256': sha(canonical(authorization))}


def validate_execution_metadata(raw, binding):
    """Join the recorded caller, not run it or certify any evaluation row."""
    caller = decode(raw)
    fields = {'schema', 'scientific_input', 'reservation', 'authorization', 'authorization_sha256',
        'model_manifest', 'candidate_reference', 'preflight', 'automatic_retry', 'resume',
        'historical_checkpoint_reuse_allowed', 'training_authorized'}
    require(set(caller) == fields and caller['schema'] == 'peano-hydra-retention-evaluation-recovery-caller-v1'
            and caller['scientific_input'] == binding['scientific_input']
            and caller['authorization'] == binding['authorization']
            and caller['authorization_sha256'] == binding['authorization_sha256']
            and caller['model_manifest'] == MODEL_MANIFEST and caller['candidate_reference'] == binding['candidate_reference']
            and caller['preflight'] == binding['preflight']
            and all(caller[key] is False for key in
                ('automatic_retry', 'resume', 'historical_checkpoint_reuse_allowed', 'training_authorized')),
            'actual recovery execution binding changed its caller/candidate/admission/authorization')
    reservation = caller['reservation']
    expected = {'status': 'job-verified', 'profile': PROFILE, 'run_id': RUN_ID, 'stage': 'evaluate',
        'job_id': binding['job_id'],
        **{key: binding['execution_identity'][key] for key in ('approval_sha256', 'resource_request_sha256',
            'source_commit', 'source_files_sha256', 'payloads_sha256')},
        'reservation': RESERVATION, 'scientific_input': binding['scientific_input'],
        'model_manifest': MODEL_MANIFEST, 'producer_source_commit': PRODUCER_COMMIT,
        'training_job_id': TRAINING_JOB, 'failed_evaluation_job_id': FAILED_EVALUATION_JOB,
        'automatic_retry': False, 'resume': False}
    require(set(reservation) == set(expected) | {'allocation_elapsed_seconds', 'allocation_remaining_seconds'}
            and all(reservation[key] == value for key, value in expected.items())
            and type(reservation['allocation_elapsed_seconds']) is int
            and 0 <= reservation['allocation_elapsed_seconds'] < 3600
            and reservation['allocation_remaining_seconds'] == 3600 - reservation['allocation_elapsed_seconds'],
            'actual caller reservation differs from the new released job')


def validate_interruption_metadata(raw, binding):
    status = decode(raw)
    require(set(status) == {'schema', 'status', 'error_type', 'error', 'automatic_retry', 'resume',
                            'authorization_sha256', 'complete_comparison_claimed'}
            and status['schema'] == 'peano-hydra-retention-evaluation-recovery-interruption-v1'
            and status['status'] == 'incomplete-output-retained'
            and status['authorization_sha256'] == binding['authorization_sha256']
            and type(status['error_type']) is str and type(status['error']) is str and len(status['error']) <= 2048
            and all(status[key] is False for key in ('automatic_retry', 'resume', 'complete_comparison_claimed')),
            'recorded interruption changed its actual incomplete scope or authorization')


def no_head_claim(head, status):
    if head is not None: return 'head-present-unverified'
    require(status['state'].split()[0] != 'COMPLETED' or status['exit_code'] != '0:0',
            'a successful terminal job without HEAD cannot be collected as a completed evaluation')
    return 'head-absent-terminal-failure'


def bound_job(job, approval_sha, header_sha, source_commit):
    require(job not in (TRAINING_JOB, FAILED_EVALUATION_JOB), 'spent original jobs cannot be adopted by recovery')
    for relative, expected in BOOTSTRAP_SOURCES.items():
        require(read_file(PREFIX + '/' + relative, 65536)[0]['sha256'] == expected,
                'frozen recovery metadata gate bootstrap source changed')
    existing = sys.modules.get('training.peano_hydra.retention_evaluation_recovery_launch')
    require(not any(name == 'training' or name.startswith('training.') for name in sys.modules)
            or existing is not None and existing.ROOT == Path(EXECUTION_ROOT), 'foreign deployment already imported')
    sys.path.insert(0, EXECUTION_ROOT)
    gate = importlib.import_module('training.peano_hydra.retention_evaluation_recovery_launch')
    require(gate.ROOT == Path(EXECUTION_ROOT) and gate.STAGES == ('evaluate',), 'metadata gate came from another source/profile')
    approval, request = gate.validate_metadata(approval_sha)
    bound = gate.identity(approval, request, approval_sha)
    require(bound['source_commit'] == source_commit and source_commit != PRODUCER_COMMIT
            and sha(canonical(bound)) == header_sha, 'actual installed new source/request header changed')
    controls = control_binding(lambda name: read_file(PACKAGE + '/' + name, MAX_JSON, True)[1],
                               source_commit, approval_sha)
    require(all(controls[key] == bound[key] for key in ('approval_sha256', 'resource_request_sha256', 'source_commit',
        'source_files_sha256', 'payloads_sha256', 'producer_sha256', 'historical_admission_sha256')),
        'actual frozen gate differs from collected control identities')
    lock = gate._lock(False)
    try:
        fcntl.flock(lock, fcntl.LOCK_SH | fcntl.LOCK_NB)
        states = {stage: gate.load_ledger(stage, bound) for stage in gate.STAGES}
        gate._history(states, bound)
        evaluate = states['evaluate']
        require(evaluate['job_id'] == job and evaluate['phase'] == 'released'
                and len(evaluate['events']) == 6 and evaluate['gpu_seconds'] == 3600,
                'exact new released one-use evaluation ledger required')
        manifest = gate._producer_completed()
        require(manifest == MODEL_MANIFEST == evaluate['model_manifest'],
                'saved original model changed from the new evaluation reservation')
        evaluate_pin = read_file(PREFIX + '/' + gate.LEDGERS['evaluate'], 256 * 1024)[0]
    finally: os.close(lock)
    command = ['sacct', '-n', '-P', '-X', '-j', job,
        '--format=JobIDRaw,JobName%80,State%32,ExitCode,ElapsedRaw,TimelimitRaw,AllocCPUS,ReqMem,AllocTRES%256,WorkDir%4096,Account,Partition,User']
    output = gate.safe.run(command)
    rows = [line.split('|') for line in output.splitlines() if line.strip()]
    require(len(rows) == 1 and len(rows[0]) in (13, 14)
            and (len(rows[0]) == 13 or rows[0][13] == ''), 'unique terminal recovery evaluation accounting required')
    row = rows[0][:13]
    require(row[0:2] == [job, PROFILE + '-evaluate'] and row[2].split()[0] in TERMINAL
            and re.fullmatch(r'[0-9]+:[0-9]+', row[3]) and row[4].isdigit() and 0 <= int(row[4]) <= 604800
            and row[5:8] == ['60', '8', '64G'] and row[9:] == [EXECUTION_ROOT, gate.ACCOUNT, gate.PARTITION, 'plgnasqret'],
            'recovery evaluation must be terminal with its exact new scheduler identity/resources')
    binding = dict(controls, job_id=job, execution_identity=bound, source_header_sha256=header_sha,
        evaluation_ledger_sha256=evaluate_pin['sha256'], evaluation_ledger_events=6,
        reserved_gpu_seconds=3600, model_manifest=manifest, producer=PRODUCER,
        producer_source_commit=PRODUCER_COMMIT, training_job_id=TRAINING_JOB,
        failed_evaluation_job_id=FAILED_EVALUATION_JOB,
        original_reservations_fully_consumed=True, original_reservation_reuse_allowed=False,
        candidate_matches_new_evaluation_reservation=True, validated_by_frozen_producer_completed=True)
    status = {'command': command, 'stdout': output, 'top_row': row, 'state': row[2], 'exit_code': row[3],
              'elapsed_seconds': int(row[4]), 'returncode': 0}
    return binding, status


def fixed_metadata(job):
    result = {
        'model-manifest.json': (MODEL + '/manifest.json', MAX_JSON),
        'execution-binding.json': (RESULT + '/execution-binding.json', MAX_JSON),
        'execution-status.json': (RESULT + '/execution-status.json', MAX_JSON),
        'evaluation.json': (RESULT + '/evaluation.json', 48 * 1024**2),
        'evaluate-ledger.jsonl': (PREFIX + '/logs/hydra-retention-evaluation-recovery-v1-evaluate.jsonl', 256 * 1024),
        'producer-train-ledger.jsonl': (PRODUCER_PREFIX + '/logs/hydra-retention-pilot-v1-train.jsonl', 256 * 1024),
        'producer-failed-evaluate-ledger.jsonl': (PRODUCER_PREFIX + '/logs/hydra-retention-pilot-v1-evaluate.jsonl', 256 * 1024),
        'producer-approval.json': (PRODUCER_PREFIX + '/_deploy/hydra-retention-pilot-v1/approval.json', MAX_JSON),
        'producer-resource-request.json': (PRODUCER_PREFIX + '/_deploy/hydra-retention-pilot-v1/resource-request.json', MAX_JSON),
        'producer-source-provenance.tsv': (PRODUCER_PREFIX + '/.peano-source-provenance.tsv', 1024),
        'producer-train.out.log': (PRODUCER_PREFIX + '/logs/peano-hydra-retention-pilot-v1-train-' + TRAINING_JOB + '.out', MAX_JSON),
        'producer-train.err.log': (PRODUCER_PREFIX + '/logs/peano-hydra-retention-pilot-v1-train-' + TRAINING_JOB + '.err', MAX_JSON),
        'producer-failed-evaluate.out.log': (PRODUCER_PREFIX + '/logs/peano-hydra-retention-pilot-v1-evaluate-' + FAILED_EVALUATION_JOB + '.out', MAX_JSON),
        'producer-failed-evaluate.err.log': (PRODUCER_PREFIX + '/logs/peano-hydra-retention-pilot-v1-evaluate-' + FAILED_EVALUATION_JOB + '.err', MAX_JSON),
        'evaluate.out.log': (PREFIX + '/logs/' + PROFILE + '-evaluate-' + job + '.out', MAX_JSON),
        'evaluate.err.log': (PREFIX + '/logs/' + PROFILE + '-evaluate-' + job + '.err', MAX_JSON),
    }
    for name in ('approval.json', 'resource-request.json', 'evaluate-request.json',
                 'inputs.json', 'preflight.json', 'admission.json', 'evaluation-plan.json'):
        result[name] = (PACKAGE + '/' + name, MAX_JSON)
    return result


def optional_pin(relative):
    try: return read_file(relative, MAX_CHECKPOINT_FILE)[0]
    except FileNotFoundError: return None


def check_external_pins(mode, head, manifest, expected_head, expected_manifest):
    if mode == 'inspect':
        require(expected_head == expected_manifest == '-', 'inspection must not substitute previously invented pins')
    else:
        require(manifest['sha256'] == expected_manifest, 'actual candidate differs from external observed manifest pin')
        require((head is None and expected_head == 'absent') or
                (head is not None and head['sha256'] == expected_head), 'actual HEAD differs from external inspection')


def build_inventory(mode, binding, status, head):
    # Inspection exposes raw metadata only; it deliberately does not scan/read
    # goal rows. Full mode retains every actual entry, including lock and debris.
    if mode == 'checkpoint':
        snapshot = checkpoint_inventory()
    else:
        try:
            fd = directory(ROOT + '/' + CHECKPOINT)
            try: root_signature = list(signature(os.fstat(fd)))
            finally: os.close(fd)
            snapshot = {'present': True, 'root_signature': root_signature, 'entries': {}}
        except FileNotFoundError:
            snapshot = {'present': False, 'root_signature': None, 'entries': {}}
    wanted = fixed_metadata(binding['job_id'])
    if mode == 'inspect': wanted.pop('evaluation.json')
    entries = {name: dict(item) for name, item in snapshot['entries'].items()}
    if mode == 'checkpoint':
        for name, item in entries.items():
            if item['kind'] == 'file': wanted['checkpoint/' + name] = (CHECKPOINT + '/' + name, MAX_CHECKPOINT_FILE)
    else:
        for name in INSPECTION_ENTRIES: wanted['checkpoint/' + name] = (CHECKPOINT + '/' + name, MAX_CHECKPOINT_FILE)
    require(len(wanted) <= MAX_DATA_FILES, 'evaluation collection data-file cap')
    files, signatures, absent, total = {}, {}, [], 0
    for local, (remote, maximum) in sorted(wanted.items()):
        try: identity, _, before = read_file(remote, maximum)
        except FileNotFoundError:
            require(local not in MANDATORY and not (mode == 'checkpoint' and local.startswith('checkpoint/')),
                    'required input or inventoried checkpoint entry disappeared')
            absent.append(local); continue
        total += identity['bytes']
        require(total <= MAX_TOTAL, 'evaluation collection aggregate byte cap')
        files[local], signatures[local] = dict(identity, remote_path=remote), before
        if local.startswith('checkpoint/') and mode == 'checkpoint':
            item = entries[local[len('checkpoint/'):]]
            require(list(before) == item['source_signature'] and identity['bytes'] == item['bytes'], 'checkpoint entry changed')
            item['sha256'] = identity['sha256']
    directories = ['checkpoint'] if snapshot['present'] else []
    directories += ['checkpoint/' + name for name, item in entries.items() if item['kind'] == 'directory']
    directories.sort(key=lambda name: (name.count('/'), name))
    index = {'schema': INDEX_SCHEMA, 'mode': mode, 'binding': binding, 'accounting': status,
        'observed_at_utc': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
        'files': files, 'directories': directories, 'absent_files': sorted(absent), 'total_file_bytes': total,
        'checkpoint_head': head, 'model_manifest': binding['model_manifest'],
        'remote_read_root': ROOT, 'execution_root': EXECUTION_ROOT, 'producer_root': ROOT + '/' + PRODUCER_PREFIX,
        'checkpoint_observation': no_head_claim(head, status),
        'checkpoint_root_present': snapshot['present'], 'checkpoint_root_signature': snapshot['root_signature'],
        'checkpoint_entry_inventory': entries if mode == 'checkpoint' else None,
        'checkpoint_goal_records_collected': mode == 'checkpoint',
        'checkpoint_all_actual_entries_collected': mode == 'checkpoint',
        'checkpoint_original_lock_collected': 'checkpoint/.lock' in files,
        'checkpoint_debris_filtered': False, 'checkpoint_files_modified': False,
        'checkpoint_metadata_is_not_verified_proof_evidence': True, 'proofs_independently_verified': False,
        'read_only': True, 'model_artifact_directories_read': False, 'model_frameworks_imported': False,
        'scheduler_mutation_performed': False, 'automatic_retry': False,
        'limits': {'checkpoint_entries': MAX_CHECKPOINT_ENTRIES, 'data_files': MAX_DATA_FILES,
                   'checkpoint_file_bytes': MAX_CHECKPOINT_FILE, 'aggregate_file_bytes': MAX_TOTAL}}
    return index, wanted, signatures, snapshot


def source_signature(item, kind):
    value = item['source_signature']
    require(type(value) is list and len(value) == 7 and all(type(x) is int for x in value)
            and all(value[i] >= 0 for i in (0, 1, 3)) and value[6] >= 1,
            'invalid checkpoint source signature')
    require((stat.S_ISDIR(value[2]) if kind == 'directory' else stat.S_ISREG(value[2]))
            and item['source_mode'] == stat.S_IMODE(value[2]), 'checkpoint source kind or mode changed')
    if kind == 'file': require(value[6] == 1 and value[3] == item['bytes'], 'checkpoint file size or links changed')


def validate_index(index, mode, job, approval_sha, header_sha, source_commit, expected_head='-', expected_manifest='-'):
    require(index.get('schema') == INDEX_SCHEMA and index.get('mode') == mode and mode in ('inspect', 'checkpoint'),
            'wrong retention evaluation collection index')
    binding = index['binding']
    identity = binding['execution_identity']
    require(binding['job_id'] == job and job not in (TRAINING_JOB, FAILED_EVALUATION_JOB)
            and binding['approval_sha256'] == approval_sha and binding['source_commit'] == source_commit
            and source_commit != PRODUCER_COMMIT and re.fullmatch(r'[0-9a-f]{40}', source_commit)
            and binding['source_header_sha256'] == header_sha
            and identity['approval_sha256'] == approval_sha and identity['source_commit'] == source_commit
            and binding['resource_request_sha256'] == identity['resource_request_sha256']
            and sha(canonical(identity)) == header_sha and binding['producer'] == PRODUCER
            and binding['producer_source_commit'] == PRODUCER_COMMIT and binding['training_job_id'] == TRAINING_JOB
            and binding['failed_evaluation_job_id'] == FAILED_EVALUATION_JOB
            and binding['reserved_gpu_seconds'] == 3600 and binding['evaluation_ledger_events'] == 6
            and binding['original_reservations_fully_consumed'] is True
            and binding['original_reservation_reuse_allowed'] is False
            and binding['candidate_matches_new_evaluation_reservation'] is True
            and binding['validated_by_frozen_producer_completed'] is True,
            'actual released recovery/producer identity changed')
    require(all(binding[key] == identity[key] for key in ('source_files_sha256', 'payloads_sha256',
                'producer_sha256', 'historical_admission_sha256'))
            and binding['producer_sha256'] == sha(canonical(PRODUCER))
            and binding['candidate_reference']['admission_receipt_sha256'] == binding['historical_admission_sha256']
            and binding['candidate_reference']['producer'] == PRODUCER_REFERENCE
            and binding['candidate_reference']['manifest_sha256'] == MODEL_MANIFEST['sha256']
            and sha(canonical(binding['authorization'])) == binding['authorization_sha256']
            and binding['authorization']['plan_sha256'] == binding['bound_evaluation_plan_sha256'],
            'collected candidate/custody/authorization identity changed')
    accounting, top = index['accounting'], index['accounting']['top_row']
    rows = [line.split('|') for line in accounting['stdout'].splitlines() if line.strip()]
    require(len(rows) == 1 and len(rows[0]) in (13, 14) and (len(rows[0]) == 13 or rows[0][13] == '')
            and rows[0][:13] == top and top[:2] == [job, PROFILE + '-evaluate'] and top[2].split()[0] in TERMINAL
            and accounting['returncode'] == 0 and accounting['state'] == top[2] and accounting['exit_code'] == top[3]
            and re.fullmatch(r'[0-9]+:[0-9]+', top[3]) and top[4].isdigit() and 0 <= int(top[4]) <= 604800
            and accounting['elapsed_seconds'] == int(top[4]) and top[5:8] == ['60', '8', '64G']
            and top[9:] == [EXECUTION_ROOT, 'plgccaiautore2026-gpu-gh200', 'plgrid-gpu-gh200', 'plgnasqret'],
            'actual terminal accounting changed')
    for key in ('checkpoint_metadata_is_not_verified_proof_evidence', 'read_only'):
        require(index[key] is True, 'collection inflated its evidence scope')
    for key in ('checkpoint_debris_filtered', 'checkpoint_files_modified', 'proofs_independently_verified',
                'model_artifact_directories_read', 'model_frameworks_imported', 'scheduler_mutation_performed', 'automatic_retry'):
        require(index[key] is False, 'collection altered evidence or work scope')
    require(index['checkpoint_goal_records_collected'] is (mode == 'checkpoint')
            and index['checkpoint_all_actual_entries_collected'] is (mode == 'checkpoint')
            and index['limits'] == {'checkpoint_entries': MAX_CHECKPOINT_ENTRIES, 'data_files': MAX_DATA_FILES,
                'checkpoint_file_bytes': MAX_CHECKPOINT_FILE, 'aggregate_file_bytes': MAX_TOTAL}, 'collection caps or completeness scope changed')
    present, entries = index['checkpoint_root_present'], index['checkpoint_entry_inventory']
    require(type(present) is bool, 'checkpoint presence must be observed')
    if present:
        source_signature({'source_signature': index['checkpoint_root_signature'],
                          'source_mode': stat.S_IMODE(index['checkpoint_root_signature'][2])}, 'directory')
    else: require(index['checkpoint_root_signature'] is None, 'absent checkpoint has a directory signature')
    wanted = fixed_metadata(job)
    if mode == 'inspect': wanted.pop('evaluation.json')
    directories = ['checkpoint'] if present else []
    if mode == 'checkpoint':
        require(type(entries) is dict and len(entries) <= MAX_CHECKPOINT_ENTRIES and (present or not entries),
                'checkpoint entry inventory changed')
        for name, item in entries.items():
            path_name(name)
            require(type(item) is dict and item.get('kind') in ('file', 'directory'), 'unknown checkpoint entry kind')
            kind = item['kind']; source_signature(item, kind)
            require(len(name.split('/')) <= (8 if kind == 'directory' else 9), 'checkpoint nesting cap')
            fields = {'kind', 'source_signature', 'source_mode'}
            if kind == 'file':
                fields |= {'bytes', 'sha256'}
                require(type(item['bytes']) is int and 0 <= item['bytes'] <= MAX_CHECKPOINT_FILE
                        and re.fullmatch(r'[0-9a-f]{64}', item['sha256']), 'checkpoint file declaration changed')
                wanted['checkpoint/' + name] = (CHECKPOINT + '/' + name, MAX_CHECKPOINT_FILE)
            else: directories.append('checkpoint/' + name)
            require(set(item) == fields, 'unexpected checkpoint entry fields')
            if '/' in name:
                parent = name.rsplit('/', 1)[0]
                require(parent in entries and entries[parent]['kind'] == 'directory', 'checkpoint directory parent missing')
    else:
        require(entries is None, 'inspection must not invent a complete checkpoint inventory')
        for name in INSPECTION_ENTRIES: wanted['checkpoint/' + name] = (CHECKPOINT + '/' + name, MAX_CHECKPOINT_FILE)
    directories.sort(key=lambda name: (name.count('/'), name))
    require(index['directories'] == directories, 'checkpoint directory inventory changed')
    files = index['files']
    require(type(files) is dict and len(files) <= MAX_DATA_FILES and MANDATORY <= set(files) <= set(wanted)
            and index['absent_files'] == sorted(set(wanted) - set(files)), 'missing or foreign collected files')
    if mode == 'checkpoint':
        require({name for name in files if name.startswith('checkpoint/')} ==
                {'checkpoint/' + name for name, item in entries.items() if item['kind'] == 'file'},
                'actual checkpoint entries were filtered or fabricated')
    total = 0
    for name, item in files.items():
        path_name(name)
        require(type(item) is dict and set(item) == {'bytes', 'sha256', 'remote_path'}
                and type(item['bytes']) is int and 0 <= item['bytes'] <= wanted[name][1]
                and re.fullmatch(r'[0-9a-f]{64}', item['sha256']) and item['remote_path'] == wanted[name][0],
                'collected file declaration changed')
        if name.startswith('checkpoint/'):
            require(present, 'absent checkpoint cannot contain files')
            if mode == 'checkpoint':
                require(all(item[key] == entries[name[len('checkpoint/'):]][key] for key in ('bytes', 'sha256')),
                        'checkpoint file differs from complete inventory')
        total += item['bytes']
    require(total == index['total_file_bytes'] and total <= MAX_TOTAL, 'evaluation aggregate collection bound')
    for name, key in (('approval.json', 'approval_sha256'), ('resource-request.json', 'resource_request_sha256'),
            ('evaluate-request.json', 'evaluation_request_sha256'), ('evaluate-ledger.jsonl', 'evaluation_ledger_sha256'),
            ('inputs.json', 'inputs_sha256'), ('preflight.json', 'preflight_sha256'), ('admission.json', 'historical_admission_sha256')):
        require(files[name]['sha256'] == binding[key], 'raw recovery control/ledger pin differs from released binding')
    for name, key in (('producer-approval.json', 'approval_sha256'), ('producer-resource-request.json', 'resource_request_sha256'),
            ('producer-train-ledger.jsonl', 'training_ledger_sha256'),
            ('producer-failed-evaluate-ledger.jsonl', 'failed_evaluation_ledger_sha256')):
        require(files[name]['sha256'] == PRODUCER[key], 'separate original consumed producer evidence changed')
    require({key: files['producer-source-provenance.tsv'][key] for key in ('bytes', 'sha256')} ==
            {'bytes': 68, 'sha256': '784781d6bf88f52ff66cf4edcc2a61ad31da6a63529a7f77528461d976a503e7'},
            'original producer source provenance changed')
    require({key: files['evaluation-plan.json'][key] for key in ('bytes', 'sha256')} ==
            {key: EVALUATION_PLAN[key] for key in ('bytes', 'sha256')}, 'preregistered DEV proposal changed')
    manifest = {key: files['model-manifest.json'][key] for key in ('bytes', 'sha256')}
    head = None if 'checkpoint/HEAD.json' not in files else {key: files['checkpoint/HEAD.json'][key] for key in ('bytes', 'sha256')}
    require(manifest == binding['model_manifest'] == index['model_manifest'] and head == index['checkpoint_head'],
            'collected raw HEAD/candidate pin differs')
    require(index['checkpoint_original_lock_collected'] is ('checkpoint/.lock' in files), 'original lock collection claim differs')
    require(index['remote_read_root'] == ROOT and index['execution_root'] == EXECUTION_ROOT
            and index['producer_root'] == ROOT + '/' + PRODUCER_PREFIX
            and index['checkpoint_observation'] == no_head_claim(head, accounting), 'collection roots or absent-HEAD scope changed')
    require(head is None or 'execution-binding.json' in files, 'actual HEAD requires its original recovery caller binding')
    check_external_pins(mode, head, manifest, expected_head, expected_manifest)


def emit_archive(index, wanted, signatures, stream):
    header = canonical(index) + b'\n'
    require(len(header) <= 1024**2, 'checkpoint collection index cap')
    with tarfile.open(fileobj=stream, mode='w|', format=tarfile.USTAR_FORMAT) as archive:
        member = tarfile.TarInfo('collection-index.json'); member.size, member.mode = len(header), 0o600
        archive.addfile(member, io.BytesIO(header))
        for name in index['directories']:
            member = tarfile.TarInfo(name + '/'); member.type, member.mode = tarfile.DIRTYPE, 0o700
            archive.addfile(member)
        for local, item in sorted(index['files'].items()):
            source, before = opened(item['remote_path'], wanted[local][1])
            with source:
                require(signature(before) == signatures[local], 'collected entry changed before streaming')
                member = tarfile.TarInfo(local); member.size, member.mode = item['bytes'], 0o600
                archive.addfile(member, source)
                require(signature(before) == signature(os.fstat(source.fileno())), 'collected entry changed during streaming')
            again, current = opened(item['remote_path'], wanted[local][1]); again.close()
            require(signature(current) == signatures[local], 'collected pathname changed during streaming')


def main():
    require(sys.flags.isolated and sys.dont_write_bytecode and sys.platform == 'linux' and len(sys.argv) == 8
            and not os.environ.get('SLURM_JOB_ID'), 'isolated terminal login collection required')
    mode, job, approval_sha, header_sha, source_commit, expected_head, expected_manifest = sys.argv[1:]
    require(mode in ('inspect', 'checkpoint') and re.fullmatch(r'[1-9][0-9]{0,19}', job)
            and job not in (TRAINING_JOB, FAILED_EVALUATION_JOB)
            and re.fullmatch(r'[0-9a-f]{40}', source_commit) and source_commit != PRODUCER_COMMIT
            and re.fullmatch(r'[0-9a-f]{64}', approval_sha) and re.fullmatch(r'[0-9a-f]{64}', header_sha),
            'invalid exact evaluation collection identity')
    require((mode == 'inspect' and expected_head == expected_manifest == '-') or
            (mode == 'checkpoint' and (expected_head == 'absent' or re.fullmatch(r'[0-9a-f]{64}', expected_head))
                and re.fullmatch(r'[0-9a-f]{64}', expected_manifest)), 'full collection requires external inspected HEAD/manifest pins')
    resource.setrlimit(resource.RLIMIT_CPU, (CPU, CPU + 1))
    resource.setrlimit(resource.RLIMIT_AS, (ADDRESS_SPACE, ADDRESS_SPACE))
    resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0)); resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('remote evaluation collection wall cap')))
    signal.setitimer(signal.ITIMER_REAL, max(.001, WALL - (time.monotonic() - STARTED)))
    sys.meta_path.insert(0, NoFrameworks())
    binding, status = bound_job(job, approval_sha, header_sha, source_commit)
    head = optional_pin(CHECKPOINT + '/HEAD.json')
    check_external_pins(mode, head, binding['model_manifest'], expected_head, expected_manifest)
    index, wanted, signatures, snapshot = build_inventory(mode, binding, status, head)
    validate_index(index, mode, job, approval_sha, header_sha, source_commit, expected_head, expected_manifest)
    if 'execution-binding.json' in index['files']:
        validate_execution_metadata(read_file(RESULT + '/execution-binding.json', MAX_JSON, True)[1], binding)
    if 'execution-status.json' in index['files']:
        validate_interruption_metadata(read_file(RESULT + '/execution-status.json', MAX_JSON, True)[1], binding)
    emit_archive(index, wanted, signatures, sys.stdout.buffer)
    if mode == 'checkpoint': require(checkpoint_inventory() == snapshot, 'actual checkpoint entries changed through export')
    for local, item in sorted(index['files'].items()):
        actual, _, after = read_file(item['remote_path'], wanted[local][1])
        require(actual == {key: item[key] for key in ('bytes', 'sha256')} and after == signatures[local],
                'collected bytes changed through export')
    for local in index['absent_files']:
        try: unexpected, _ = opened(wanted[local][0], wanted[local][1])
        except FileNotFoundError: continue
        unexpected.close(); raise ValueError('previously absent metadata appeared during export')
    after, _ = bound_job(job, approval_sha, header_sha, source_commit)
    require(after == binding and optional_pin(CHECKPOINT + '/HEAD.json') == head,
            'source/job/candidate/HEAD changed during collection')
    sys.stdout.buffer.flush()
    require(time.monotonic() - STARTED < WALL, 'remote evaluation collection publication deadline')
    signal.setitimer(signal.ITIMER_REAL, 0)


if __name__ == '__main__':
    main()
