"""Rehash the completed adapter in place and retrieve bounded complete logs."""
from datetime import datetime, timezone
import base64
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess

ARCHIVE = Path(__file__).absolute().parent
MANIFEST_SHA = '5795d5a3d70f781f56f81e83c2295c887d0949795924f4208f45d26a3ef89b68'
OBSERVER_SHA = 'd946b3a996a212a105e72e7736b6d26f05dfa952f610c266c51f93a66b7dd60c'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def write(path, raw):
    with path.open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def record(path, value):
    raw = (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()
    write(path, raw)
    return sha(raw)


def main():
    local_manifest = (ARCHIVE / 'completed-manifest-01.json').read_bytes()
    assert sha(local_manifest) == MANIFEST_SHA
    source = (ARCHIVE / 'observe-frontier-training-remote-v2.py').read_bytes()
    assert sha(source) == OBSERVER_SHA
    program = source.decode() + r'''
import base64
resource.setrlimit(resource.RLIMIT_CPU,(20,20))
resource.setrlimit(resource.RLIMIT_AS,(320*1024**2,320*1024**2))
resource.setrlimit(resource.RLIMIT_FSIZE,(0,0))
signal.alarm(35)
binding = bound_job('21438102','9cc426c7829bba661db24df58d53f036d4f759e0c6548208ca5a25e9737150bd')
raw, manifest_info = read(ADAPTER + '/manifest.json', MAX_JSON)
require(sha(raw) == '5795d5a3d70f781f56f81e83c2295c887d0949795924f4208f45d26a3ef89b68','final manifest changed')
manifest = decode(raw)
require(manifest.get('run_id') == RUN_ID and manifest.get('job',{}).get('job_id') == '21438102','foreign final manifest')
expected = {}
for group, names in [('adapter',{'adapter/README.md','adapter/adapter_config.json','adapter/adapter_model.safetensors'}),
                     ('tokenizer',{'tokenizer/added_tokens.json','tokenizer/chat_template.jinja','tokenizer/merges.txt','tokenizer/special_tokens_map.json','tokenizer/tokenizer.json','tokenizer/tokenizer_config.json','tokenizer/vocab.json'})]:
    require(set(manifest[group]['files']) == names,'unexpected saved artifact list')
    require(sha(canonical(manifest[group]['files'])) == manifest[group]['sha256'],'artifact root digest differs')
    expected.update(manifest[group]['files'])
files, total = {}, 0
for name in sorted(expected):
    parent_name, leaf = (ADAPTER + '/' + name).rsplit('/',1)
    parent = directory(ROOT + '/' + parent_name)
    fd = None
    try:
        fd = os.open(leaf,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=parent)
        before = os.fstat(fd)
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and 0 < before.st_size <= 128*1024**2,'unsafe or oversized saved artifact')
        total += before.st_size
        require(total <= 128*1024**2,'saved artifact aggregate bound')
        checksum, count = hashlib.sha256(), 0
        while True:
            block = os.read(fd,1024**2)
            if not block: break
            count += len(block)
            require(count <= before.st_size,'saved artifact grew during hashing')
            checksum.update(block)
        after = os.fstat(fd)
        require(count == before.st_size == after.st_size and before.st_mtime_ns == after.st_mtime_ns and before.st_ctime_ns == after.st_ctime_ns,'saved artifact changed during hashing')
        require(checksum.hexdigest() == expected[name],'saved artifact hash differs: ' + name)
        files[name] = {'bytes':count,'sha256':checksum.hexdigest()}
    finally:
        if fd is not None: os.close(fd)
        os.close(parent)
logs = {}
for suffix in ('out','err'):
    path = 'logs/' + JOB_NAME + '-21438102.' + suffix
    contents, info = read(path,1024**2)
    logs[suffix] = {'metadata':info,'base64':base64.b64encode(contents).decode('ascii')}
result = {'schema':'peano-hydra-completed-artifacts-verification-v1','status':'all-saved-artifact-hashes-verified',
    'observed_at_utc':datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),'binding':binding,
    'manifest_sha256':sha(raw),'artifact_root':ROOT+'/'+ADAPTER,'files':files,'artifact_bytes_hashed':total,
    'logs':logs,'read_only':True,'model_weights_downloaded':False,'model_frameworks_loaded':False,
    'job_submission_performed':False,'automatic_retry':False}
print(json.dumps(result,sort_keys=True,allow_nan=False),flush=True)
'''
    output = ARCHIVE / 'completed-artifacts-01'
    output.mkdir(exist_ok=False)
    started = datetime.now(timezone.utc).isoformat()
    record(output / 'started.json', {'schema':'peano-hydra-completed-artifacts-collection-start-v1',
        'started_at_utc':started,'manifest_sha256':MANIFEST_SHA,'remote_program_sha256':sha(program.encode()),
        'read_only':True,'automatic_retry':False,'model_weights_downloaded':False,
        'remote_limits':{'cpu_seconds':20,'wall_seconds':35,'address_space_bytes':320*1024**2,
                         'artifact_bytes':128*1024**2,'log_bytes_each':1024**2}})
    command = ['/usr/bin/ssh','-T','-o','BatchMode=yes','-o','ConnectTimeout=15',
        '-o','ServerAliveInterval=10','-o','ServerAliveCountMax=2','-o','ForwardAgent=no',
        '-o','ClearAllForwardings=yes','-o','StrictHostKeyChecking=yes','-o','UpdateHostKeys=no',
        '-o','ControlMaster=no','-o','ControlPath=none','--','plgnasqret@helios.cyfronet.pl',
        '/usr/bin/python3 -I -B -c ' + shlex.quote(program)]
    timeout = False
    try:
        result = subprocess.run(command,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,timeout=45)
        code, stdout, stderr = result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired as error:
        code, stdout, stderr, timeout = None, error.stdout or b'', error.stderr or b'', True
    assert len(stdout) <= 4*1024**2 and len(stderr) <= 65536
    write(output / 'remote-result.json',stdout)
    write(output / 'stderr.log',stderr)
    receipt = {'schema':'peano-hydra-completed-artifacts-collection-v1','started_at_utc':started,
        'finished_at_utc':datetime.now(timezone.utc).isoformat(),'returncode':code,'timed_out':timeout,
        'automatic_retry':False,'read_only':True,'model_weights_downloaded':False,
        'remote_program_sha256':sha(program.encode()),'remote_result_sha256':sha(stdout),
        'remote_result_bytes':len(stdout),'status':'failed-output-preserved'}
    if code == 0 and not timeout:
        remote = json.loads(stdout)
        assert remote['status'] == 'all-saved-artifact-hashes-verified' and remote['manifest_sha256'] == MANIFEST_SHA
        assert remote['binding']['job_id'] == '21438102' and remote['model_weights_downloaded'] is False
        receipt['logs'] = {}
        for suffix in ('out','err'):
            log = remote['logs'][suffix]
            raw = base64.b64decode(log['base64'],validate=True)
            assert len(raw) <= 1024**2 and sha(raw) == log['metadata']['captured_sha256']
            write(output / ('training.' + suffix + '.log'),raw)
            receipt['logs'][suffix] = {'bytes':len(raw),'sha256':sha(raw)}
        receipt.update(status='verified-and-logs-retrieved',artifact_files=remote['files'],
                       artifact_bytes_hashed=remote['artifact_bytes_hashed'])
    digest = record(output / 'receipt.json',receipt)
    print(json.dumps({'status':receipt['status'],'receipt':str(output/'receipt.json'),
                      'receipt_sha256':digest,'artifact_bytes_hashed':receipt.get('artifact_bytes_hashed')},sort_keys=True),flush=True)
    return 0 if receipt['status'] == 'verified-and-logs-retrieved' else 2


if __name__ == '__main__':
    raise SystemExit(main())
