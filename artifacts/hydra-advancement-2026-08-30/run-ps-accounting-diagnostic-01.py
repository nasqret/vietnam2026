"""One read-only SSH timing probe; retain no remote process rows or arguments."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import selectors
import shlex
import signal
import subprocess
import time


ARCHIVE = Path(__file__).resolve().parent
PYTHON = "/net/software/x86_64/el8/Python/3.11.5-GCCcore-13.2.0/bin/python3"
LIBRARIES = (
    "/net/software/x86_64/el8/Python/3.11.5-GCCcore-13.2.0/lib",
    "/net/software/x86_64/el8/libffi/3.4.4-GCCcore-13.2.0/lib64",
)
PROBE_SHA = "089288eb9d8d84c5bd440d7a724be988a193ebde00e9cb7f8abee9845da8a92a"
REMOTE_PROGRAM = r'''
import json, os, resource, signal, subprocess, sys, time

started = time.monotonic()
resource.setrlimit(resource.RLIMIT_CPU, (10, 10))
resource.setrlimit(resource.RLIMIT_AS, (512 * 1024**2, 512 * 1024**2))
resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
class DiagnosticDeadline(BaseException): pass
def deadline(_signum, _frame): raise DiagnosticDeadline()
signal.signal(signal.SIGALRM, deadline)
signal.alarm(12)
expected_python = '/net/software/x86_64/el8/Python/3.11.5-GCCcore-13.2.0/bin/python3'
expected_libraries = '/net/software/x86_64/el8/Python/3.11.5-GCCcore-13.2.0/lib:/net/software/x86_64/el8/libffi/3.4.4-GCCcore-13.2.0/lib64'
if sys.executable != expected_python or sys.version_info[:3] != (3, 11, 5):
    raise RuntimeError('diagnostic requires the previously tested exact EL8 interpreter')
if os.environ.get('LD_LIBRARY_PATH') != expected_libraries:
    raise RuntimeError('diagnostic runtime library pair differs')
if set(os.environ) - {'PATH', 'LC_ALL', 'LD_LIBRARY_PATH', 'LC_CTYPE'}:
    raise RuntimeError('diagnostic environment is not the explicit clean environment')
if not os.path.isfile('/bin/ps'):
    raise RuntimeError('the exact /bin/ps command is unavailable; no fallback')

def own_cpu():
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return usage.ru_utime + usage.ru_stime
def child_cpu():
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    return usage.ru_utime + usage.ru_stime
def output_size(value):
    return len(value.encode('utf-8')) if isinstance(value, str) else len(value or b'')

rows, stop = [], 'ten-probes-completed'
try:
    for index in range(10):
        # Reserve at least a full original one-second ps timeout plus cleanup.
        if time.monotonic() - started >= 10.5 or own_cpu() + child_cpu() >= 8:
            stop = 'diagnostic-reservation-exhausted'
            break
        before, before_self, before_children = time.monotonic(), own_cpu(), child_cpu()
        row = {'index': index + 1, 'command': ['/bin/ps', '-axo', 'pid=,pgid=,rss='],
               'timeout_seconds': 1, 'returncode': None, 'error_type': None,
               'error_errno': None, 'stdout_bytes': 0, 'stderr_bytes': 0,
               'original_guard_would_reject_this_call': False}
        try:
            result = subprocess.run(['/bin/ps', '-axo', 'pid=,pgid=,rss='],
                                    capture_output=True, text=True, timeout=1, check=False)
            row.update(returncode=result.returncode,
                       stdout_bytes=output_size(result.stdout), stderr_bytes=output_size(result.stderr),
                       original_guard_would_reject_this_call=(result.returncode != 0 or len(result.stdout) > 4 * 1024**2))
            # Deliberately retain neither numeric process rows nor stderr text.
            del result
        except subprocess.TimeoutExpired as error:
            row.update(error_type=type(error).__name__, stdout_bytes=output_size(error.stdout),
                       stderr_bytes=output_size(error.stderr), original_guard_would_reject_this_call=True)
        except OSError as error:
            row.update(error_type=type(error).__name__, error_errno=error.errno,
                       original_guard_would_reject_this_call=True)
        finally:
            row.update(wall_seconds=time.monotonic() - before,
                       own_cpu_seconds=own_cpu() - before_self,
                       reaped_ps_cpu_seconds=child_cpu() - before_children)
            rows.append(row)
        if index < 9:
            time.sleep(0.05)
except DiagnosticDeadline:
    stop = 'remote-diagnostic-wall-limit'
finally:
    signal.alarm(0)

usage = resource.getrusage(resource.RUSAGE_SELF)
print(json.dumps({
    'schema': 'peano-hydra-ps-accounting-read-only-diagnostic-v1',
    'status': stop, 'read_only': True, 'python': sys.version, 'executable': sys.executable,
    'runtime_library_paths': expected_libraries.split(':'),
    'limits': {'max_ps_calls': 10, 'ps_timeout_seconds': 1,
               'root_cpu_seconds': 10, 'stop_before_next_call_at_own_plus_reaped_child_cpu_seconds': 8,
               'remote_alarm_wall_seconds': 12, 'address_space_bytes': 512 * 1024**2},
    'calls': rows, 'wall_seconds': time.monotonic() - started,
    'own_cpu_seconds': own_cpu(), 'reaped_ps_cpu_seconds': child_cpu(),
    'own_peak_rss_bytes': usage.ru_maxrss * 1024,
    'original_guard_rejection_observed': any(row['original_guard_would_reject_this_call'] for row in rows),
    'remote_process_rows_retained': False, 'remote_process_arguments_or_environments_read': False,
    'project_source_imported': False, 'native_validation_performed': False,
    'proof_or_model_data_read': False, 'job_activity_performed': False,
    'installation_performed': False, 'remote_file_writes': False, 'automatic_retry': False,
}, sort_keys=True), flush=True)
'''


def write_once(name, raw):
    assert "/" not in name and len(raw) <= 256 * 1024
    with (ARCHIVE / name).open("xb") as stream:
        stream.write(raw)
    return {"path": name, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def main():
    probe = (ARCHIVE / "login-origin-import-probe-01.json").read_bytes()
    if hashlib.sha256(probe).hexdigest() != PROBE_SHA:
        raise ValueError("previous runtime probe differs from its exact raw pin")
    names = {key: "ps-accounting-diagnostic-01." + suffix for key, suffix in (
        ("start", "started.json"), ("stdout", "stdout.json"),
        ("stderr", "stderr.log"), ("receipt", "process.json"),
    )}
    if any(os.path.lexists(ARCHIVE / name) for name in names.values()):
        raise ValueError("the single diagnostic attempt has already been claimed; no retry")
    remote = shlex.join(["/usr/bin/env", "-i", "PATH=/usr/bin:/bin", "LC_ALL=C",
                         "LD_LIBRARY_PATH=" + ":".join(LIBRARIES),
                         PYTHON, "-I", "-B", "-X", "pycache_prefix=/dev/null", "-"])
    command = ["/usr/bin/ssh", "-T", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5",
               "-o", "ConnectionAttempts=1", "-o", "ServerAliveInterval=5", "-o", "ServerAliveCountMax=1",
               "-o", "ForwardAgent=no", "-o", "ClearAllForwardings=yes",
               "-o", "StrictHostKeyChecking=yes", "-o", "UpdateHostKeys=no",
               "-o", "ControlMaster=no", "-o", "ControlPath=none", "--",
               "plgnasqret@helios.cyfronet.pl", remote]
    program = REMOTE_PROGRAM.encode("utf-8")
    started = time.monotonic()
    initial = {
        "schema": "peano-hydra-ps-accounting-diagnostic-local-start-v1",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "helper_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "runtime_probe_raw_sha256": PROBE_SHA,
        "remote_program_bytes": len(program), "remote_program_sha256": hashlib.sha256(program).hexdigest(),
        "command": command, "transport_wall_limit_seconds": 15, "automatic_retry": False,
        "remote_file_writes_requested": False, "private_payload_sent": False,
    }
    write_once(names["start"], (json.dumps(initial, indent=2, sort_keys=True) + "\n").encode())
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, start_new_session=True)
    buffers = {"stdout": bytearray(), "stderr": bytearray()}
    caps = {"stdout": 64 * 1024, "stderr": 16 * 1024}
    selector = selectors.DefaultSelector()
    reason, error = "exited", None
    try:
        process.stdin.write(program)
        process.stdin.close()
        for label, stream in (("stdout", process.stdout), ("stderr", process.stderr)):
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_READ, label)
        while selector.get_map() or process.poll() is None:
            if time.monotonic() - started >= 15:
                raise TimeoutError("single read-only SSH diagnostic transport limit")
            for key, _ in selector.select(0.05):
                chunk = os.read(key.fileobj.fileno(), 16384)
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                remaining = caps[key.data] - len(buffers[key.data])
                buffers[key.data].extend(chunk[:remaining])
                if len(chunk) > remaining:
                    raise ValueError("diagnostic transport output limit")
        process.wait(timeout=0.5)
    except BaseException as failure:
        reason, error = "stopped", type(failure).__name__ + ": " + str(failure)
    finally:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=1)
        selector.close()
        process.stdout.close()
        process.stderr.close()
    streams = {name: write_once(names[name], bytes(raw)) for name, raw in buffers.items()}
    record = {**initial, "schema": "peano-hydra-ps-accounting-diagnostic-local-result-v1",
              "finished_at": datetime.now(timezone.utc).isoformat(),
              "returncode": process.returncode, "reason": reason, "error": error,
              "transport_wall_seconds": time.monotonic() - started, "streams": streams}
    if reason == "exited" and process.returncode == 0:
        record["diagnostic"] = json.loads(buffers["stdout"])
    receipt = write_once(names["receipt"], (json.dumps(record, indent=2, sort_keys=True) + "\n").encode())
    print(json.dumps({"receipt": receipt, "returncode": process.returncode, "reason": reason,
                      "diagnostic": record.get("diagnostic")}, sort_keys=True), flush=True)
    return 0 if reason == "exited" and process.returncode == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
