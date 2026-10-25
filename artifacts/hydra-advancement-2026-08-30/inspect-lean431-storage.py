"""Read only the official ZIP directory to assess storage, without installation."""
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import urllib.request
import zipfile

ROOT = Path('/Users/bnaskrecki/codex/peano')
ARCHIVE = Path(__file__).absolute().parent
URL = 'https://github.com/leanprover/lean4/releases/download/v4.31.0/lean-4.31.0-darwin_aarch64.zip'
PUBLISHED_SHA = 'e8cd241b8d2b81c70415920f0900c9ec5b156e98e6b62163cb14b8288c6e0656'
MAX_NETWORK = 8*1024**2


class MetadataReader(io.RawIOBase):
    def __init__(self):
        self.position = 0
        self.network_bytes = 0
        self.requests = []
        self.total_size = None
        self._range(0,1)

    def readable(self): return True
    def seekable(self): return True
    def tell(self): return self.position

    def seek(self, offset, whence=0):
        value = offset if whence==0 else self.position+offset if whence==1 else self.total_size+offset
        if not 0 <= value <= self.total_size: raise ValueError('ZIP metadata seek bound')
        self.position=value
        return value

    def _range(self, start, size):
        if not 0<size<=MAX_NETWORK-self.network_bytes: raise ValueError('metadata download limit')
        request=urllib.request.Request(URL,headers={'Range':f'bytes={start}-{start+size-1}',
            'Accept-Encoding':'identity','User-Agent':'Hydra-toolchain-metadata-inspection/1'})
        with urllib.request.urlopen(request,timeout=15) as response:
            if response.status!=206: raise ValueError('server did not honor bounded Range; full download refused')
            match=re.fullmatch(r'bytes (\d+)-(\d+)/(\d+)',response.headers.get('Content-Range',''))
            if match is None: raise ValueError('missing exact Content-Range')
            begin,end,total=map(int,match.groups())
            if begin!=start or end!=start+size-1: raise ValueError('wrong returned Range')
            if self.total_size is not None and total!=self.total_size: raise ValueError('archive length changed')
            self.total_size=total
            raw=response.read(size+1)
            if len(raw)!=size: raise ValueError('wrong metadata byte length')
            self.network_bytes+=len(raw)
            self.requests.append({'start':start,'bytes':size,'sha256':hashlib.sha256(raw).hexdigest()})
            return raw

    def read(self, size=-1):
        if size<0: size=self.total_size-self.position
        size=min(size,self.total_size-self.position)
        if not size:return b''
        raw=self._range(self.position,size)
        self.position+=size
        return raw


def main():
    output=ARCHIVE/'lean431-storage-inspection-01.json'
    assert not output.exists()
    result={'schema':'peano-hydra-toolchain-storage-inspection-v1',
        'started_at_utc':datetime.now(timezone.utc).isoformat(),'source_url':URL,
        'published_archive_sha256':PUBLISHED_SHA,'full_archive_hash_verified':False,
        'installation_performed':False,'payload_members_downloaded':False,'automatic_retry':False}
    reader=None
    try:
        reader=MetadataReader()
        with zipfile.ZipFile(reader) as archive:
            entries=archive.infolist()
            assert len(entries)<=100000
            files=[item for item in entries if not item.is_dir()]
            groups=defaultdict(int)
            for item in files:
                parts=item.filename.split('/')
                assert parts[0]=='lean-4.31.0-darwin_aarch64' and '..' not in parts and not item.filename.startswith('/')
                groups[parts[1] if len(parts)>1 else '(root)']+=item.file_size
            unpacked=sum(item.file_size for item in files)
            free=shutil.disk_usage(ROOT).free
            result.update(status='metadata-inspected',zip_bytes=reader.total_size,files=len(files),
                full_uncompressed_bytes=unpacked,uncompressed_bytes_by_top_directory=dict(groups),
                current_free_bytes=free,minimum_free_reserve_bytes=1024**3,
                full_install_peak_bytes_with_reserve=reader.total_size+unpacked+1024**3,
                full_install_fits=free>=reader.total_size+unpacked+1024**3,
                largest_files=[{'path':item.filename,'bytes':item.file_size} for item in sorted(files,key=lambda x:x.file_size,reverse=True)[:12]])
    except Exception as error:
        result.update(status='metadata-unavailable-no-download',error=type(error).__name__+': '+str(error))
    if reader is not None:
        result.update(metadata_bytes_downloaded=reader.network_bytes,range_requests=reader.requests)
    result['finished_at_utc']=datetime.now(timezone.utc).isoformat()
    raw=(json.dumps(result,sort_keys=True,indent=2)+'\n').encode()
    with output.open('xb') as stream: stream.write(raw)
    print(json.dumps(result,sort_keys=True),flush=True)


if __name__=='__main__':main()
