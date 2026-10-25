"""Local pipe checks only: no SSH, source repair, model, or scheduler process."""
from pathlib import Path
import hashlib
import json
import runpy
import sys

HERE = Path(__file__).resolve().parent
run = runpy.run_path(str(HERE / 'repair_source04.py'))['run_transport']
wire = b'synthetic-local-transport-data\n' * 20000
results = []

record, stdout, stderr = run([sys.executable, '-I', '-B', '-c',
    'import hashlib,sys; b=sys.stdin.buffer.read(); print(len(b),hashlib.sha256(b).hexdigest())'], wire)
assert record['actual_ssh_exit_code'] == 0 and record['capture_complete']
assert record['stdin_bytes_written'] == len(wire) and stderr == b''
assert stdout.decode().strip() == str(len(wire)) + ' ' + hashlib.sha256(wire).hexdigest()
results.append({'case': 'large_stdin_pumped_without_deadlock', 'passed': True})

record, stdout, stderr = run([sys.executable, '-I', '-B', '-c',
    'import sys; sys.stdout.buffer.write(b"x"*70000); sys.stdout.buffer.flush()'], wire)
assert record['output_limit_exceeded'] and not record['capture_complete']
assert len(stdout) == 65536 and len(stderr) <= 65536
results.append({'case': 'output_overflow_capped_during_capture', 'passed': True})

record, stdout, stderr = run([sys.executable, '-I', '-B', '-c',
    'import os; os._exit(255)'], wire)
assert record['actual_ssh_exit_code'] == 255 and record['capture_complete']
assert record['stdin_bytes_written'] < len(wire) and stdout == b'' and stderr == b''
results.append({'case': 'early_255_preserves_partial_stdin_and_actual_exit', 'passed': True})

report = {'schema': 'hydra-local-repair-transport-check-v1', 'passed': True,
          'local_child_processes': 3, 'ssh_calls': 0, 'remote_writes': 0,
          'cpu_allocations': 0, 'gpu_allocations': 0, 'model_calls': 0, 'native_runs': 0,
          'source_sha256': hashlib.sha256((HERE / 'repair_source04.py').read_bytes()).hexdigest(),
          'checks': results}
with (HERE / 'LOCAL_TRANSPORT_CHECK.json').open('x') as file:
    json.dump(report, file, indent=2)
    file.write('\n')
print(json.dumps(report), flush=True)
