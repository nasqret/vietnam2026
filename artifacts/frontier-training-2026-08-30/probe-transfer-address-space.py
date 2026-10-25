"""Read-only check of a measured address-space correction, not a transfer."""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import shlex
import subprocess

ARCHIVE = Path(__file__).absolute().parent


def main():
    output = ARCHIVE / 'transfer-receiver-memory-probe-01.json'
    assert not output.exists()
    spec = importlib.util.spec_from_file_location('original_receiver_probe', ARCHIVE / 'probe-transfer-receiver.py')
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)
    source = (ARCHIVE / 'transfer-frontier-training-remote.py').read_bytes()
    assert hashlib.sha256(source).hexdigest() == '175b1580fed0156c343224c88fe8376e780e357cbaea1ad224cb3adaaa7d772c'
    original = b'(256 * 1024**2, 256 * 1024**2)'
    corrected = b'(320 * 1024**2, 320 * 1024**2)'
    assert source.count(original) == 1 and probe.PROBE.count(original.decode()) == 1
    candidate = source.replace(original, corrected, 1)
    code = candidate.decode() + probe.PROBE.replace(original.decode(), corrected.decode(), 1)
    raw = (ARCHIVE / 'transfer-01/inventory.json').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == 'e25aeab7944c65c98d4c476db2208070bce6a7e8f29069092874eab9c1eee061'
    command = ['ssh','-T','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ForwardAgent=no','-o','ClearAllForwardings=yes',
        '--','plgnasqret@helios.cyfronet.pl','/usr/bin/python3 -I -B -c ' + shlex.quote(code)]
    started = datetime.now(timezone.utc).isoformat()
    result = subprocess.run(command,input=raw,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30)
    assert len(result.stdout) <= 65536 and len(result.stderr) <= 65536
    record = {'schema':'peano-hydra-transfer-address-space-read-only-probe-v1','started_at_utc':started,
        'finished_at_utc':datetime.now(timezone.utc).isoformat(),'returncode':result.returncode,
        'original_receiver_sha256':hashlib.sha256(source).hexdigest(),
        'candidate_receiver_sha256':hashlib.sha256(candidate).hexdigest(),
        'remote_program_sha256':hashlib.sha256(code.encode()).hexdigest(),
        'address_space_cap_before_bytes':256*1024**2,'address_space_cap_probe_bytes':320*1024**2,
        'reason':'Measured interpreter VmSize 265900 KiB already exceeds 256 MiB before any payload allocation; RSS was only 13284 KiB. This tests finite headroom for mapped libraries plus bounded metadata.',
        'gpu_or_native_worker_limits_changed':False,'remote_writes_performed':False,
        'stdout':result.stdout.decode(),'stderr':result.stderr.decode(),'read_only':True,'automatic_retry':False}
    with output.open('xb') as stream:
        stream.write((json.dumps(record,sort_keys=True,indent=2)+'\n').encode())
    print(json.dumps(record,sort_keys=True),flush=True)


if __name__ == '__main__':
    main()
