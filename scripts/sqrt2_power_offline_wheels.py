"""Stage only the five pinned pure-Python test wheels, without pip or children.

This is job-local dependency preparation, never proof authority. Authenticate
all archives and validate every member before creating a fresh destination.
No installation hooks, entry-point wrappers, network access or global writes.
"""
import argparse
from hashlib import sha256
import io
import json
from pathlib import Path,PurePosixPath
import stat
import zipfile

from verify_sqrt2_power_wmi_regressions import WHEELS

MAX_MEMBER=1024**2
MAX_TOTAL=16*1024**2
MAX_FILES=1000


def member_name(info):
    name=info.filename;path=PurePosixPath(name)
    mode=info.external_attr>>16
    if (not name or path.is_absolute() or '..' in path.parts or str(path)!=name
            or '\\' in name or info.is_dir() or stat.S_ISLNK(mode)
            or stat.S_IFMT(mode) not in (0,stat.S_IFREG)
            or name.endswith('.pth') or any(part.endswith('.data') for part in path.parts)
            or not 0<=info.file_size<=MAX_MEMBER):
        raise ValueError('unsupported or unsafe pure-wheel member')
    return name


def collect(wheel_directory,expected):
    payloads={};total=0
    for name,digest in expected.items():
        path=wheel_directory/name
        if path.is_symlink() or not path.is_file() or path.stat().st_size>8*1024**2:
            raise ValueError('wheel must be a bounded regular file')
        raw=path.read_bytes()
        if sha256(raw).hexdigest()!=digest:raise ValueError('pinned wheel changed')
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            for info in archive.infolist():
                name=member_name(info)
                if name in payloads:raise ValueError('duplicate wheel destination')
                total+=info.file_size
                if total>MAX_TOTAL or len(payloads)>=MAX_FILES:raise ValueError('wheel extraction budget exceeded')
                data=archive.read(info)
                if len(data)!=info.file_size:raise ValueError('wheel member size changed')
                payloads[name]=data
    if any(str(parent) in payloads for name in payloads for parent in PurePosixPath(name).parents):
        raise ValueError('file and directory destinations collide')
    return payloads


def stage(wheel_directory,destination):
    if destination.exists() or destination.is_symlink():raise ValueError('fresh job-local dependency destination required')
    files=collect(wheel_directory,WHEELS)
    destination.mkdir(mode=0o700)
    manifest={}
    for name,data in sorted(files.items()):
        path=destination/name;path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('xb') as stream:stream.write(data)
        manifest[name]=dict(bytes=len(data),sha256=sha256(data).hexdigest())
    for name,pin in manifest.items():
        raw=(destination/name).read_bytes()
        if len(raw)!=pin['bytes'] or sha256(raw).hexdigest()!=pin['sha256']:
            raise ValueError('staged wheel member differs')
    encoded=json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()
    return dict(status='staged',wheels=WHEELS,files=len(files),bytes=sum(map(len,files.values())),
        manifest_sha256=sha256(encoded).hexdigest(),network_calls=0,child_processes=0,
        installation_hooks_executed=0,authority='dependency_staging_not_proof')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wheels',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();print(json.dumps(stage(args.wheels.resolve(),args.output),sort_keys=True))
