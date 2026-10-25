import resource,signal
resource.setrlimit(resource.RLIMIT_CPU,(15,15));resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));signal.alarm(20)
import ctypes,_ctypes,json,os,sys,hashlib
from pathlib import Path
ffi=Path('/net/software/x86_64/el8/libffi/3.4.4-GCCcore-13.2.0/lib64/libffi.so.8').resolve(strict=True)
ctypes.CDLL(str(ffi))
assert 'torch' not in sys.modules and sys.version_info[:2]==(3,11)
print(json.dumps({'passed':True,'python':sys.executable,'version':sys.version,'ctypes_module':_ctypes.__file__,'libffi':str(ffi),'libffi_sha256':hashlib.sha256(ffi.read_bytes()).hexdigest(),'ld_library_path':os.environ['LD_LIBRARY_PATH'],'model_imports':False,'gpu_allocations':0}))
