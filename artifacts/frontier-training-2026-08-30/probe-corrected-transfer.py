"""Verify the corrected receiver against exact control frames without writing."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import struct

ARCHIVE = Path(__file__).absolute().parent
PROBE = r'''
import traceback
def memory():
    with open('/proc/self/status') as stream:
        values = dict(line.strip().split(':',1) for line in stream if ':' in line)
    return {key:values.get(key,'').strip() for key in ('VmSize','VmRSS','VmData','VmPeak','Threads')}
result = {'schema':'peano-hydra-corrected-transfer-read-only-probe-v1',
          'memory_before_limit':memory(), 'python':sys.version.split()[0],
          'destination_exists':os.path.lexists(REMOTE_ROOT), 'writes_performed':False,
          'job_submission_performed':False, 'address_space_cap_bytes':320*1024**2}
resource.setrlimit(resource.RLIMIT_CPU,(20,20))
resource.setrlimit(resource.RLIMIT_AS,(320*1024**2,320*1024**2))
resource.setrlimit(resource.RLIMIT_FSIZE,(0,0))
phase = 'read-control-frames'
try:
    stream = sys.stdin.buffer
    require(exact(stream,len(MAGIC)) == MAGIC,'probe stream magic')
    length = struct.unpack('>Q',exact(stream,8))[0]
    require(0 < length <= MAX_JSON,'probe inventory bound')
    raw = exact(stream,length)
    require(sha(raw) == 'e25aeab7944c65c98d4c476db2208070bce6a7e8f29069092874eab9c1eee061','probe inventory pin')
    phase = 'validate-inventory'
    record = validate_inventory(decode(raw))
    result['inventory_sha256'] = sha(raw)
    result['inventory_validated'] = True
    phase = 'validate-request-and-approval'
    controls = {name:exact(stream,record['files'][name]['bytes']) for name in (REQUEST,APPROVAL)}
    validate_control(record,controls[REQUEST],controls[APPROVAL])
    require(stream.read(1) == b'','unexpected probe bytes')
    result['request_and_approval_validated'] = True
    phase = 'open-parent-directory-read-only'
    parent = directory(REMOTE_ROOT.rsplit('/',1)[0])
    os.close(parent)
    result['parent_directory_opened'] = True
    result['memory_after_validation'] = memory()
    result['status'] = 'read-only-control-check-passed'
except BaseException as error:
    result['status'] = 'read-only-check-failed'
    result['error'] = type(error).__name__ + ': ' + str(error)
    result['traceback'] = traceback.format_exc(limit=8)
    result['memory_at_failure'] = memory()
result['last_phase'] = phase
result['destination_exists_after'] = os.path.lexists(REMOTE_ROOT)
print(json.dumps(result,sort_keys=True),flush=True)
'''


def main():
    output = ARCHIVE / 'transfer-receiver-corrected-probe-01.json'
    assert not output.exists()
    helper = ARCHIVE / 'transfer-frontier-training-remote-v2.py'
    source = helper.read_bytes()
    assert len(source) <= 65536
    inventory_raw = (ARCHIVE / 'transfer-01/inventory.json').read_bytes()
    assert hashlib.sha256(inventory_raw).hexdigest() == 'e25aeab7944c65c98d4c476db2208070bce6a7e8f29069092874eab9c1eee061'
    inventory = json.loads(inventory_raw)
    magic = b'HYDRA-FRONTIER-TRAINING-TRANSFER-V1\n'
    size = len(magic) + 8 + len(inventory_raw)
    size += sum(inventory['files'][name]['bytes'] for name in ('_deploy/hydra-frontier-training-v1/resource-request.json', '_deploy/hydra-frontier-training-v1/approval.json'))
    assert size <= 1024**2
    with (ARCHIVE / 'transfer-01/bundle.bin').open('rb') as stream:
        raw = stream.read(size)
    assert len(raw) == size and raw[:len(magic)] == magic
    assert raw[len(magic)+8:len(magic)+8+len(inventory_raw)] == inventory_raw
    code = source.decode() + PROBE
    command = ['ssh','-T','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ForwardAgent=no','-o','ClearAllForwardings=yes',
        '--','plgnasqret@helios.cyfronet.pl','/usr/bin/python3 -I -B -c ' + shlex.quote(code)]
    started = datetime.now(timezone.utc).isoformat()
    result = subprocess.run(command,input=raw,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30)
    assert len(result.stdout) <= 65536 and len(result.stderr) <= 65536
    record = {'schema':'peano-hydra-corrected-transfer-probe-transport-v1','started_at_utc':started,
        'finished_at_utc':datetime.now(timezone.utc).isoformat(),'returncode':result.returncode,
        'candidate_receiver_sha256':hashlib.sha256(source).hexdigest(),
        'remote_program_sha256':hashlib.sha256(code.encode()).hexdigest(),
        'control_frame_bytes':len(raw),'control_frame_sha256':hashlib.sha256(raw).hexdigest(),
        'stdout':result.stdout.decode(),'stderr':result.stderr.decode(),'read_only':True,'automatic_retry':False}
    with output.open('xb') as stream:
        stream.write((json.dumps(record,sort_keys=True,indent=2)+'\n').encode())
    print(json.dumps(record,sort_keys=True),flush=True)


if __name__ == '__main__':
    main()
