import json,os,shutil,signal,subprocess,time
signal.alarm(40)
exe=shutil.which('scontrol');assert exe
results=[]
for label,ld in [('inherited',os.environ.get('LD_LIBRARY_PATH')),('fixture_python_lib','/net/software/x86_64/el8/Python/3.11.5-GCCcore-13.2.0/lib')]:
 env=dict(os.environ)
 if ld is None:env.pop('LD_LIBRARY_PATH',None)
 else:env['LD_LIBRARY_PATH']=ld
 began=time.monotonic();r=subprocess.run([exe,'-o','show','partition','plgrid'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,timeout=15)
 assert len(r.stdout)+len(r.stderr)<=65536
 results.append({'label':label,'executable':exe,'ld_library_path':ld,'actual_exit_code':r.returncode,'elapsed_seconds':time.monotonic()-began,'stdout':r.stdout.decode(),'stderr':r.stderr.decode()})
print(json.dumps({'read_only':True,'queries':results}))
