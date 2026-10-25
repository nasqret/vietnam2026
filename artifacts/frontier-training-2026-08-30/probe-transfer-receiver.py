"""Read-only probe of the actual receiver failure; no project writes or jobs."""
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
from datetime import datetime, timezone

ARCHIVE = Path(__file__).absolute().parent
PROBE = r'''
import traceback
def memory():
    with open('/proc/self/status') as stream:
        values = dict(line.strip().split(':', 1) for line in stream if ':' in line)
    return {name: values.get(name, '').strip() for name in ('VmSize', 'VmRSS', 'VmData', 'VmPeak', 'Threads')}
result = {'schema': 'peano-hydra-transfer-receiver-read-only-probe-v1',
          'python': sys.version.split()[0], 'memory_before_limit': memory(),
          'address_space_limit_before': list(resource.getrlimit(resource.RLIMIT_AS)),
          'destination_exists': os.path.lexists(REMOTE_ROOT),
          'model_modules_present': sorted(set(sys.modules) & {'torch','numpy','transformers','peft'}),
          'writes_performed': False, 'job_submission_performed': False}
phase = 'before-limit'
resource.setrlimit(resource.RLIMIT_CPU, (20,20))
try:
    resource.setrlimit(resource.RLIMIT_AS, (256 * 1024**2, 256 * 1024**2))
    phase = 'read-inventory-only'
    raw = sys.stdin.buffer.read(MAX_JSON + 1)
    require(len(raw) <= MAX_JSON and sha(raw) == 'e25aeab7944c65c98d4c476db2208070bce6a7e8f29069092874eab9c1eee061', 'probe inventory pin')
    result['memory_after_inventory_read'] = memory()
    phase = 'decode-inventory'
    record = decode(raw)
    result['memory_after_decode'] = memory()
    phase = 'validate-inventory'
    validate_inventory(record)
    result['memory_after_validation'] = memory()
    phase = 'open-parent-directory-read-only'
    parent = directory(REMOTE_ROOT.rsplit('/',1)[0])
    os.close(parent)
    result['status'] = 'read-only-metadata-check-passed'
except BaseException as error:
    result['status'] = 'failure-reproduced-without-writes'
    result['error'] = type(error).__name__ + ': ' + str(error)
    result['traceback'] = traceback.format_exc(limit=8)
    result['memory_at_failure'] = memory()
result['last_phase'] = phase
result['destination_exists_after'] = os.path.lexists(REMOTE_ROOT)
print(json.dumps(result,sort_keys=True),flush=True)
'''


def main():
    output = ARCHIVE / 'transfer-receiver-probe-01.json'
    assert not output.exists()
    source = (ARCHIVE / 'transfer-frontier-training-remote.py').read_bytes()
    assert hashlib.sha256(source).hexdigest() == '175b1580fed0156c343224c88fe8376e780e357cbaea1ad224cb3adaaa7d772c'
    raw = (ARCHIVE / 'transfer-01/inventory.json').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == 'e25aeab7944c65c98d4c476db2208070bce6a7e8f29069092874eab9c1eee061'
    code = source.decode() + PROBE
    command = ['ssh','-T','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ForwardAgent=no','-o','ClearAllForwardings=yes',
               '--','plgnasqret@helios.cyfronet.pl','/usr/bin/python3 -I -B -c ' + shlex.quote(code)]
    started = datetime.now(timezone.utc).isoformat()
    result = subprocess.run(command,input=raw,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30)
    assert len(result.stdout) <= 65536 and len(result.stderr) <= 65536
    record = {'schema':'peano-hydra-transfer-receiver-probe-transport-v1','started_at_utc':started,
        'finished_at_utc':datetime.now(timezone.utc).isoformat(),'returncode':result.returncode,
        'remote_program_sha256':hashlib.sha256(code.encode()).hexdigest(),'input_inventory_sha256':hashlib.sha256(raw).hexdigest(),
        'stdout':result.stdout.decode(),'stderr':result.stderr.decode(),'read_only':True,'automatic_retry':False}
    with output.open('xb') as stream:
        stream.write((json.dumps(record,sort_keys=True,indent=2)+'\n').encode())
    print(json.dumps(record,sort_keys=True),flush=True)


if __name__ == '__main__':
    main()
