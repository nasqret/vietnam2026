"""One read-only retrieval of the exact completed job's bounded final manifest."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess

ARCHIVE = Path(__file__).absolute().parent
OBSERVER_SHA = 'd946b3a996a212a105e72e7736b6d26f05dfa952f610c266c51f93a66b7dd60c'
OBSERVATION_SHA = '3b85a4ceb82e3bc816b795efbe296cd31d114363cd11299cb31d73c3c0828cae'
MANIFEST_SHA = '5795d5a3d70f781f56f81e83c2295c887d0949795924f4208f45d26a3ef89b68'
APPROVAL_SHA = '9cc426c7829bba661db24df58d53f036d4f759e0c6548208ca5a25e9737150bd'
JOB = '21438102'


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
    observation_raw = (ARCHIVE / 'observation-v2-05.json').read_bytes()
    assert sha(observation_raw) == OBSERVATION_SHA
    observed = json.loads(observation_raw)['observation']
    rows = observed['scheduler_identity']['accounting_rows']
    exact = [row for row in rows if row[0] == JOB]
    assert len(exact) == 1 and exact[0][2:4] == ['COMPLETED', '0:0']
    assert not observed['scheduler_identity']['integrity_issues']
    assert observed['binding']['approval_sha256'] == APPROVAL_SHA
    assert observed['manifest']['captured_sha256'] == MANIFEST_SHA
    assert observed['manifest']['file_bytes_at_open'] == 3369364
    helper = (ARCHIVE / 'observe-frontier-training-remote-v2.py').read_bytes()
    assert sha(helper) == OBSERVER_SHA
    program = helper.decode() + r'''
require(sys.flags.isolated and sys.dont_write_bytecode, 'isolated read-only export required')
resource.setrlimit(resource.RLIMIT_CPU, (20,20))
resource.setrlimit(resource.RLIMIT_AS, (320*1024**2,320*1024**2))
resource.setrlimit(resource.RLIMIT_FSIZE, (0,0))
signal.alarm(30)
binding = bound_job('21438102', '9cc426c7829bba661db24df58d53f036d4f759e0c6548208ca5a25e9737150bd')
raw, info = read(ADAPTER + '/manifest.json', MAX_JSON)
require(len(raw) == 3369364 and sha(raw) == '5795d5a3d70f781f56f81e83c2295c887d0949795924f4208f45d26a3ef89b68', 'completed manifest bytes changed')
value = decode(raw)
require(value.get('run_id') == RUN_ID and value.get('job',{}).get('job_id') == '21438102', 'completed manifest identity differs')
sys.stderr.write(json.dumps({'schema':'peano-hydra-completed-manifest-export-v1','binding':binding,'manifest':info,'read_only':True,'model_weights_downloaded':False,'job_submission_performed':False}, sort_keys=True) + '\n')
sys.stderr.flush()
sys.stdout.buffer.write(raw)
sys.stdout.buffer.flush()
'''
    paths = {name: ARCHIVE / ('completed-manifest-01.' + suffix) for name, suffix in
             [('started', 'started.json'), ('manifest', 'json'), ('stderr', 'stderr.log'), ('receipt', 'receipt.json')]}
    assert all(not os.path.lexists(path) for path in paths.values()), 'fresh retrieval required; no overwrite or automatic retry'
    started = datetime.now(timezone.utc).isoformat()
    record(paths['started'], {'schema':'peano-hydra-completed-manifest-fetch-start-v1',
        'started_at_utc':started,'job_id':JOB,'observation_sha256':OBSERVATION_SHA,
        'expected_manifest_sha256':MANIFEST_SHA,'remote_program_sha256':sha(program.encode()),
        'read_only':True,'model_weights_downloaded':False,'automatic_retry':False})
    command = ['/usr/bin/ssh','-T','-o','BatchMode=yes','-o','ConnectTimeout=15',
        '-o','ServerAliveInterval=10','-o','ServerAliveCountMax=2','-o','ForwardAgent=no',
        '-o','ClearAllForwardings=yes','-o','StrictHostKeyChecking=yes','-o','UpdateHostKeys=no',
        '-o','ControlMaster=no','-o','ControlPath=none','--','plgnasqret@helios.cyfronet.pl',
        '/usr/bin/python3 -I -B -c ' + shlex.quote(program)]
    timed_out = False
    try:
        process = subprocess.run(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, timeout=40)
        code, stdout, stderr = process.returncode, process.stdout, process.stderr
    except subprocess.TimeoutExpired as error:
        code, stdout, stderr, timed_out = None, error.stdout or b'', error.stderr or b'', True
    assert len(stdout) <= 4*1024**2 and len(stderr) <= 65536, 'fixed read-only exporter exceeded its output bound'
    write(paths['manifest'], stdout)
    write(paths['stderr'], stderr)
    success = code == 0 and not timed_out and sha(stdout) == MANIFEST_SHA
    receipt = {'schema':'peano-hydra-completed-manifest-fetch-v1',
        'status':'retrieved-exact-manifest' if success else 'failed-output-preserved',
        'started_at_utc':started,'finished_at_utc':datetime.now(timezone.utc).isoformat(),
        'job_id':JOB,'returncode':code,'timed_out':timed_out,'read_only':True,
        'automatic_retry':False,'model_weights_downloaded':False,'job_submission_performed':False,
        'source_observation_sha256':OBSERVATION_SHA,'remote_observer_sha256':OBSERVER_SHA,
        'remote_program_sha256':sha(program.encode()),'manifest_file':str(paths['manifest']),
        'manifest_bytes':len(stdout),'manifest_sha256':sha(stdout),'stderr':stderr.decode('utf-8','replace')}
    receipt_sha = record(paths['receipt'], receipt)
    print(json.dumps({'status':receipt['status'],'receipt':str(paths['receipt']),
                      'receipt_sha256':receipt_sha,'manifest_sha256':sha(stdout)},sort_keys=True),flush=True)
    return 0 if success else 2


if __name__ == '__main__':
    raise SystemExit(main())
