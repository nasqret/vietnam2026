import os,json,subprocess,signal
from pathlib import Path
signal.alarm(25)
base=Path('/net/software/x86_64/el8')
items={}
for name in ['libffi','OpenSSL']:
 p=base/name
 matches=list(p.glob('*/lib*/libffi.so*')) if name=='libffi' else list(p.glob('*/lib*/libssl.so*'))
 assert len(matches)<=64
 items[name]=[str(x) for x in matches]
lib=str(base/'Python/3.11.5-GCCcore-13.2.0/lib')
ctypes=list((base/'Python/3.11.5-GCCcore-13.2.0/lib/python3.11/lib-dynload').glob('_ctypes*.so'))
assert len(ctypes)==1
env=dict(os.environ);env['LD_LIBRARY_PATH']=lib
r=subprocess.run(['/usr/bin/ldd',str(ctypes[0])],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10,env=env)
assert len(r.stdout)+len(r.stderr)<=65536
print(json.dumps({'libraries':items,'ctypes':str(ctypes[0]),'ldd_exit':r.returncode,'ldd':r.stdout.decode(),'stderr':r.stderr.decode(),'model_calls':0,'gpu_allocations':0}))
