"""Evict only the reviewed old, regenerable pip HTTP download-cache entries.

No installed environment, project model/checkpoint, source or evidence is
selected. The exact plan was inspected before this cache-only operation.
"""
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import stat

ARCHIVE = Path('/Users/bnaskrecki/codex/peano/artifacts/hydra-retention-pilot-2026-08-30')
CACHE = Path('/Users/bnaskrecki/Library/Caches/pip/http')
PLAN = ARCHIVE / 'pip-cache-eviction-plan-01.json'
PIN = '968a761e338555778e1140534a6ee2277ccda411993ee06ea0af054d8b380fd1'
RECEIPT = ARCHIVE / 'pip-cache-eviction-01.jsonl'


def identity(info):
    return {'device': info.st_dev, 'inode': info.st_ino, 'bytes': info.st_size,
            'mtime_ns': info.st_mtime_ns, 'ctime_ns': info.st_ctime_ns}


def checked(item):
    path = Path(item['path'])
    relative = path.relative_to(CACHE).as_posix()
    assert re.fullmatch(r'(?:[0-9a-f]/){5}[0-9a-f]{56}', relative)
    for parent in (path.parent, *path.parent.parents):
        assert stat.S_ISDIR(parent.lstat().st_mode)
    parent = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
    try:
        info = os.fstat(fd)
        assert stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_uid == os.getuid()
        assert info.st_mtime < 1759276800 and identity(info) == {k: item[k] for k in identity(info)}
        h = hashlib.sha256()
        with os.fdopen(fd, 'rb', closefd=False) as stream:
            for block in iter(lambda: stream.read(4 * 1024**2), b''): h.update(block)
        assert h.hexdigest() == item['sha256'] and identity(os.fstat(fd)) == identity(info)
    except BaseException:
        os.close(parent)
        raise
    finally: os.close(fd)
    return path, parent, info


def main():
    raw = PLAN.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == PIN
    plan = json.loads(raw)
    assert plan['cache_root'] == str(CACHE) and plan['removal_performed'] is False
    items = plan['selected']
    assert len(items) == 23 and sum(i['bytes'] for i in items) == plan['total_bytes'] == 815348969
    assert plan['total_bytes'] <= plan['maximum_bytes'] == 1024**3
    assert len({i['path'] for i in items}) == len(items)
    assert not os.path.lexists(RECEIPT)
    # Verify the complete exact list before the first eviction.
    for item in items:
        _, parent, _ = checked(item); os.close(parent)
    before = os.statvfs(ARCHIVE)
    with RECEIPT.open('xb') as stream:
        def emit(record):
            stream.write((json.dumps(record, sort_keys=True) + '\n').encode()); stream.flush(); os.fsync(stream.fileno())
        emit({'kind': 'start', 'schema': 'peano-hydra-pip-download-cache-eviction-v1', 'plan_sha256': PIN,
              'available_bytes_before': before.f_bavail * before.f_frsize,
              'utc': datetime.datetime.now(datetime.timezone.utc).isoformat()})
        for item in items:
            path, parent, info = checked(item)
            try:
                assert identity(os.stat(path.name, dir_fd=parent, follow_symlinks=False)) == identity(info)
                os.unlink(path.name, dir_fd=parent); os.fsync(parent)
            finally: os.close(parent)
            emit({'kind': 'evicted-regenerable-download', 'path': str(path), 'bytes': item['bytes'],
                  'sha256': item['sha256'], 'package': item['package']})
        after = os.statvfs(ARCHIVE)
        result = {'kind': 'complete', 'files': len(items), 'logical_bytes_evicted': plan['total_bytes'],
                  'available_bytes_after': after.f_bavail * after.f_frsize,
                  'installed_packages_or_project_artifacts_modified': False}
        emit(result)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__': main()
