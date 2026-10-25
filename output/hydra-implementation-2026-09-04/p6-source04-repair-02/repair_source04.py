"""Prepare or perform one explicitly selected source04 repair; never retry a phase."""
from pathlib import Path
import argparse
import ast
import base64
import hashlib
import json
import os
import re
import selectors
import shlex
import stat
import subprocess
import time

HERE = Path(__file__).resolve().parent
CAMPAIGN = HERE.parent
REPO = CAMPAIGN.parent.parent
BUNDLE = CAMPAIGN / 'combined-source-bundle-04'
ATTEMPT = HERE / 'attempt-01'
SSH = ['/usr/bin/ssh', '-T', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15',
       '-o', 'ServerAliveInterval=10', '-o', 'ServerAliveCountMax=2',
       '-o', 'ForwardAgent=no', '-o', 'ClearAllForwardings=yes',
       '-o', 'StrictHostKeyChecking=yes', '-o', 'UpdateHostKeys=no',
       '-o', 'ControlMaster=no', '-o', 'ControlPath=none',
       '--', 'plgnasqret@helios.cyfronet.pl']


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path, maximum):
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode) or path.is_symlink() or before.st_size > maximum:
        raise ValueError('Unexpected local file type or size: ' + str(path))
    raw = path.read_bytes()
    after = path.lstat()
    if len(raw) != before.st_size or (before.st_ino, before.st_mtime_ns) != (after.st_ino, after.st_mtime_ns):
        raise ValueError('Local file changed while reading: ' + str(path))
    return raw


def pinned(descriptor, maximum):
    relative = Path(descriptor['path'])
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('Evidence path must stay in the repository')
    raw = read(REPO / relative, maximum)
    if len(raw) != descriptor['bytes'] or digest(raw) != descriptor['sha256']:
        raise ValueError('Pinned local file changed: ' + str(relative))
    return raw


def prepare(review_sha256):
    if re.fullmatch('[0-9a-f]{64}', review_sha256) is None:
        raise ValueError('An exact review SHA256 is required')
    review_raw = read(HERE / 'REPAIR_REVIEW.json', 65536)
    if digest(review_raw) != review_sha256:
        raise ValueError('Repair review changed')
    review = json.loads(review_raw)
    if review['schema'] != 'hydra-source04-partial-copy-repair-review-v2':
        raise ValueError('Wrong repair review schema')
    if review['automatic_retry'] is not False or review['allocations'] != 0:
        raise ValueError('Repair must not retry or allocate jobs')
    if review['bounds'] != {'remote_wall_seconds': 120, 'remote_cpu_soft_seconds': 60,
                            'remote_cpu_hard_seconds': 75, 'remote_address_space_bytes': 536870912,
                            'ssh_wall_seconds': 150, 'maximum_input_bytes': 2097152,
                            'maximum_stdout_bytes': 65536, 'maximum_stderr_bytes': 65536}:
        raise ValueError('Unexpected repair bounds')
    code = pinned(review['remote_code'], 65536)
    ast.parse(code, feature_version=(3, 6))
    payloads = {}
    for target, descriptor in review['payloads'].items():
        payloads[target] = pinned(descriptor, 1024 * 1024)
    controller = 'source/output/hydra-implementation-2026-09-04/paired-evaluation-v2/paired_controller.py'
    if set(payloads) != {'manifest.json', 'paired-source-pins.json', controller}:
        raise ValueError('Only the original three source04 payloads are allowed')
    if sum(map(len, payloads.values())) != 423394:
        raise ValueError('Source04 payload byte count changed')
    failed = json.loads(pinned(review['failed_stage_actual'], 65536))
    if failed['actual_ssh_exit_code'] != 255:
        raise ValueError('Original stage255 must remain a failed attempt')
    failed_tool = json.loads(pinned(review['failed_stage_tool_actual'], 65536))
    if failed_tool['actual_process_exit_code'] != 255 or failed_tool['completion_chunk'] != 'add706':
        raise ValueError('Original failed tool completion changed')
    inventory = json.loads(pinned(review['partial_inventory'], 1024 * 1024))
    if inventory['file_count'] != 821 or inventory['total_bytes'] != 79300068:
        raise ValueError('Unexpected partial-copy evidence')
    inventory_tool = json.loads(pinned(review['partial_inventory_tool_actual'], 65536))
    if inventory_tool['actual_ssh_exit_code'] != 0 or inventory_tool['completion_chunk'] != '42a78c':
        raise ValueError('Partial inventory lacks its real successful observation')
    previous = json.loads(pinned(review['previous_repair_transport'], 65536))
    if previous['actual_ssh_exit_code'] != 1 or previous['capture_complete'] is not True or previous['stdout']['bytes'] != 0:
        raise ValueError('Prior repair must remain an observed failed preflight')
    previous_tool = json.loads(pinned(review['previous_repair_tool_failure'], 65536))
    if previous_tool['actual_process_exit_code'] != 1 or previous_tool['completion_chunk'] != '908edc' or previous_tool['source_mutation_phase_reached'] is not False:
        raise ValueError('Prior repair failure evidence differs')
    traversal = json.loads(pinned(review['traversal_check'], 65536))
    if traversal['passed'] is not True or traversal['uid'] != 105923 or traversal['source04_root_entries'] != ['source']:
        raise ValueError('The actual read-only traversal prerequisite failed')
    traversal_tool = json.loads(pinned(review['traversal_check_actual'], 65536))
    if traversal_tool['actual_ssh_exit_code'] != 0 or traversal_tool['completion_chunk'] != 'f92faf':
        raise ValueError('Actual traversal completion is required')
    request = {'schema': 'hydra-source04-partial-copy-repair-request-v2',
               'authority': 'HYDRA_EXPERIMENT_AUTHORITY.md',
               'automatic_retry': False, 'review_sha256': review_sha256,
               'payloads': {name: base64.b64encode(raw).decode('ascii') for name, raw in payloads.items()}}
    wire = json.dumps(request, sort_keys=True, separators=(',', ':')).encode()
    if len(wire) > 2097152:
        raise ValueError('Repair input exceeds its bound')
    return review, code, wire


def run_transport(argv, wire):
    """Bound capture while pumping stdin; abort only this owned SSH process."""
    process = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    poller = selectors.DefaultSelector()
    buffers = {'stdout': bytearray(), 'stderr': bytearray()}
    written = 0
    deadline = time.monotonic() + 150
    timed_out = False
    exceeded = False
    io_error = None
    for name, stream, event in [('stdin', process.stdin, selectors.EVENT_WRITE),
                                ('stdout', process.stdout, selectors.EVENT_READ),
                                ('stderr', process.stderr, selectors.EVENT_READ)]:
        os.set_blocking(stream.fileno(), False)
        poller.register(stream, event, name)
    try:
        while poller.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                timed_out = True
                break
            for key, _ in poller.select(min(remaining, 0.25)):
                name, stream = key.data, key.fileobj
                if name == 'stdin':
                    try:
                        written += os.write(stream.fileno(), wire[written:written + 65536])
                    except BlockingIOError:
                        continue
                    except BrokenPipeError:
                        poller.unregister(stream)
                        stream.close()
                        continue
                    if written == len(wire):
                        poller.unregister(stream)
                        stream.close()
                else:
                    try:
                        chunk = os.read(stream.fileno(), 65536)
                    except BlockingIOError:
                        continue
                    if not chunk:
                        poller.unregister(stream)
                        stream.close()
                        continue
                    available = 65536 - len(buffers[name])
                    buffers[name].extend(chunk[:available])
                    if len(chunk) > available:
                        exceeded = True
                        break
            if exceeded:
                break
    except OSError as error:
        io_error = type(error).__name__
    finally:
        if timed_out or exceeded or io_error:
            if process.poll() is None:
                process.kill()
        for key in list(poller.get_map().values()):
            poller.unregister(key.fileobj)
            key.fileobj.close()
        poller.close()
    try:
        exit_code = process.wait(timeout=max(0.01, deadline - time.monotonic()))
    except subprocess.TimeoutExpired:
        timed_out = True
        process.kill()
        exit_code = process.wait(timeout=5)
    return {'actual_ssh_exit_code': exit_code, 'outer_timeout': timed_out,
            'output_limit_exceeded': exceeded, 'io_error': io_error,
            'capture_complete': not (timed_out or exceeded or io_error),
            'stdin_bytes_written': written, 'stdin_bytes_expected': len(wire)}, bytes(buffers['stdout']), bytes(buffers['stderr'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--check', action='store_true', help='Read-only local pin and syntax check')
    action.add_argument('--execute', action='store_true', help='One explicitly selected remote repair; not yet authorized by packet05')
    parser.add_argument('--review-sha256', required=True)
    args = parser.parse_args()
    review, code, wire = prepare(args.review_sha256)
    summary = {'review_sha256': args.review_sha256, 'remote_code_sha256': digest(code),
               'wire_payload_bytes': len(wire), 'wire_payload_sha256': digest(wire),
               'raw_payload_bytes': 423394, 'allocations': 0, 'automatic_retry': False}
    if args.check:
        print(json.dumps(dict(summary, local_check=True, ssh_calls=0)), flush=True)
        return 0
    # This directory is intentionally never removed or recycled, including after SSH failure.
    ATTEMPT.mkdir(exist_ok=False)
    (ATTEMPT / 'intent.json').write_text(json.dumps(dict(summary, phase='repair'), indent=2) + '\n')
    (ATTEMPT / 'remote-script.py').write_bytes(code)
    (ATTEMPT / 'request-metadata.json').write_text(json.dumps(summary, indent=2) + '\n')
    began = time.monotonic()
    transport, stdout, stderr = run_transport(
        SSH + ['/usr/bin/python3 -I -B -c ' + shlex.quote(code.decode('utf-8'))], wire)
    elapsed = time.monotonic() - began
    (ATTEMPT / 'stdout.json').write_bytes(stdout)
    (ATTEMPT / 'stderr.txt').write_bytes(stderr)
    record = dict(summary, schema='hydra-source04-partial-copy-repair-actual-completion-v2',
                  **transport, elapsed_seconds=elapsed,
                  stdout={'bytes': len(stdout), 'sha256': digest(stdout)},
                  stderr={'bytes': len(stderr), 'sha256': digest(stderr)},
                  original_stage_exit_code=255, original_stage_completion_chunk='add706',
                  original_stage_preserved=True, remote_copy_outcome='unadmitted_until_receipt_validation',
                  automatic_retry_performed=False)
    (ATTEMPT / 'actual-completion.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps(record), flush=True)
    if not transport['capture_complete']:
        return 1
    if stdout:
        print(stdout.decode('utf-8', 'replace'), end='', flush=True)
    if stderr:
        print(stderr.decode('utf-8', 'replace'), end='', flush=True)
    return transport['actual_ssh_exit_code']


if __name__ == '__main__':
    raise SystemExit(main())
