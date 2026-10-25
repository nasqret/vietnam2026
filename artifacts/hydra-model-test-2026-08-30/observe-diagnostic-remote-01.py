"""One read-only observation; COLLECTOR is the exact pinned collector namespace."""
import base64
import datetime
import os
import resource
import selectors
import signal
import stat
import subprocess
import sys
import time

require = COLLECTOR['require']
canonical = COLLECTOR['canonical']
decode = COLLECTOR['decode']
sha = COLLECTOR['sha']
ROOT = COLLECTOR['ROOT']
PROFILE = COLLECTOR['PROFILE']
RESULT = COLLECTOR['RESULT']
JOB = '21453693'
APPROVAL = '10873068c69239375587420c47194efd09895006a3b6ef719c513860eacdc66e'
CAP = 65536


def command(args):
    child = subprocess.Popen(args, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, start_new_session=True)
    values, selector = {'stdout': bytearray(), 'stderr': bytearray()}, selectors.DefaultSelector()
    started = time.monotonic()
    try:
        for label in values:
            stream = getattr(child, label)
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_READ, label)
        while selector.get_map():
            require(time.monotonic() - started < 8, 'scheduler read deadline')
            for key, _ in selector.select(0.1):
                block = os.read(key.fileobj.fileno(), 8192)
                if not block:
                    selector.unregister(key.fileobj)
                else:
                    room = CAP - len(values[key.data])
                    values[key.data].extend(block[:room])
                    require(len(block) <= room, 'scheduler read byte cap')
        child.wait(timeout=max(0.01, 8 - (time.monotonic() - started)))
    finally:
        if child.poll() is None:
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            child.wait(timeout=2)
        selector.close()
        child.stdout.close()
        child.stderr.close()
    return dict(command=args, returncode=child.returncode,
                stdout=values['stdout'].decode('utf-8', 'replace'),
                stderr=values['stderr'].decode('utf-8', 'replace'))


def scheduler():
    queue = command(['squeue', '-h', '-j', JOB, '-o', '%i|%j|%T|%M|%l|%C|%m|%R|%a|%P|%u'])
    rows = [line.split('|') for line in queue['stdout'].splitlines() if line.strip()]
    queue['bound_state'] = None
    if queue['returncode'] == 0:
        require(len(rows) <= 1, 'unexpected queue rows')
        if rows:
            row = [part.strip() for part in rows[0]]
            require(len(row) == 11 and row[:2] == [JOB, PROFILE + '-evaluate']
                    and row[8:] == ['plgccaiautore2026-gpu-gh200', 'plgrid-gpu-gh200', 'plgnasqret'],
                    'queue identity changed')
            queue['bound_state'], queue['row'] = row[2], row
    accounting = command(['sacct', '-n', '-P', '-j', JOB,
        '--format=JobIDRaw,JobName%80,State%32,ExitCode,ElapsedRaw,TimelimitRaw,AllocCPUS,ReqMem,AllocTRES%256,WorkDir%4096,Account,Partition,User'])
    accounting['bound_state'] = None
    if accounting['returncode'] == 0:
        rows = [line.split('|') for line in accounting['stdout'].splitlines() if line.strip()]
        require(len(rows) <= 8 and all(len(row) == 13 and row[0] in
            (JOB, JOB + '.batch', JOB + '.extern') for row in rows), 'unexpected accounting rows')
        top = [row for row in rows if row[0] == JOB]
        require(len(top) <= 1, 'duplicate accounting top job')
        if top:
            row = top[0]
            require(row[1] == PROFILE + '-evaluate' and row[5] == '15' and row[7] == '64G'
                and row[9] == ROOT and row[10:] ==
                ['plgccaiautore2026-gpu-gh200', 'plgrid-gpu-gh200', 'plgnasqret'],
                'accounting identity/resources changed')
            accounting['bound_state'], accounting['top_row'] = row[2], row
    return {'squeue': queue, 'sacct': accounting,
            'observed_state': queue['bound_state'] or accounting['bound_state'] or 'unknown',
            'terminal_state_required': False, 'snapshots_may_differ': True}


def tail(relative):
    parent = fd = None
    try:
        parent_path, leaf = (ROOT + '/' + relative).rsplit('/', 1)
        parent = COLLECTOR['directory'](parent_path)
        fd = os.open(leaf, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        before = os.fstat(fd)
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_size >= 0,
                'log is not a single-link regular file')
        offset = max(0, before.st_size - CAP)
        wanted = before.st_size - offset
        os.lseek(fd, offset, os.SEEK_SET)
        raw = bytearray()
        while len(raw) < wanted:
            block = os.read(fd, wanted - len(raw))
            require(bool(block), 'log shrank during tail read')
            raw.extend(block)
        after, named = os.fstat(fd), os.stat(leaf, dir_fd=parent, follow_symlinks=False)
        require(all(stat.S_ISREG(info.st_mode) and info.st_nlink == 1
            and (info.st_dev, info.st_ino) == (before.st_dev, before.st_ino)
            and info.st_size >= before.st_size for info in (after, named)), 'log replaced or shrank')
        return {'path': relative, 'exists': True, 'bytes': len(raw), 'sha256': sha(raw),
            'base64': base64.b64encode(raw).decode('ascii'), 'offset': offset,
            'file_bytes_at_open': before.st_size, 'file_bytes_after_read': after.st_size,
            'grew_during_read': after.st_size > before.st_size,
            'whole_file_captured': offset == 0 and after.st_size == before.st_size,
            'snapshot_is_not_a_proof_score': True}
    except FileNotFoundError:
        return {'path': relative, 'exists': False}
    finally:
        if fd is not None:
            os.close(fd)
        if parent is not None:
            os.close(parent)


def metadata(relative):
    try:
        descriptor, raw, _ = COLLECTOR['read_file'](relative, CAP, True)
        return dict(descriptor, path=relative, exists=True, value=decode(raw),
                    independently_verified=False)
    except FileNotFoundError:
        return {'path': relative, 'exists': False}
    except (OSError, ValueError) as error:
        # HEAD can be atomically replaced between the two stable-reader checks.
        # Never infer progress or score from a failed metadata snapshot.
        return {'path': relative, 'exists': None, 'status': 'unavailable-or-changed',
                'error': type(error).__name__ + ': ' + str(error)[:512]}


def main():
    require(sys.flags.isolated and sys.dont_write_bytecode and len(sys.argv) == 1,
            'isolated fixed-job observer required')
    resource.setrlimit(resource.RLIMIT_CPU, (20, 20))
    resource.setrlimit(resource.RLIMIT_AS, (320 * 1024**2, 320 * 1024**2))
    resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('observation wall cap')))
    signal.alarm(30)
    started = time.monotonic()
    binding = COLLECTOR['bound_job'](JOB, APPROVAL)
    result = {'schema': 'peano-hydra-diagnostic-live-observation-v1', 'binding': binding,
        'observed_at_utc': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
        'scheduler': scheduler(),
        'logs': {suffix: tail('logs/' + PROFILE + '-evaluate-' + JOB + '.' + suffix)
                 for suffix in ('out', 'err')},
        'metadata': {name: metadata(RESULT + '/' + name)
                     for name in ('execution-status.json', 'checkpoint/HEAD.json')},
        'read_only': True, 'model_loaded': False, 'model_weights_read_or_downloaded': False,
        'proofs_independently_verified': False, 'quality_claim': None,
        'checkpoint_goal_records_collected': False, 'automatic_retry': False,
        'scheduler_mutation_performed': False, 'remote_file_writes': False}
    require(COLLECTOR['bound_job'](JOB, APPROVAL) == binding, 'approval/ledger changed during observation')
    usage = resource.getrusage(resource.RUSAGE_SELF)
    result['resources'] = {'wall_seconds': time.monotonic() - started,
        'cpu_seconds': usage.ru_utime + usage.ru_stime,
        'maxrss_bytes': usage.ru_maxrss * 1024, 'log_bytes_per_file_cap': CAP}
    raw = canonical(result) + b'\n'
    require(len(raw) <= 2 * 1024**2, 'observation output cap')
    sys.stdout.buffer.write(raw)
    sys.stdout.buffer.flush()
    signal.alarm(0)


if __name__ == '__main__':
    main()
