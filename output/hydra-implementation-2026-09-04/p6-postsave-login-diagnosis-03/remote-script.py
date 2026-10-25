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
assert len(ctypes)<=8
selected=[p for p in ctypes if p.name.startswith('_ctypes.')]
env=dict(os.environ);env['LD_LIBRARY_PATH']=lib
checks=[]
for p in selected:
 r=subprocess.run(['/usr/bin/ldd',str(p)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10,env=env)
 assert len(r.stdout)+len(r.stderr)<=65536
 checks.append({'path':str(p),'exit':r.returncode,'stdout':r.stdout.decode(),'stderr':r.stderr.decode()})
print(json.dumps({'libraries':items,'ctypes_candidates':[str(p) for p in ctypes],'checks':checks,'model_calls':0,'gpu_allocations':0}))
