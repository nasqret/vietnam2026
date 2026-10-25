import hashlib,json,subprocess,time
out={}
for name,argv in (('failed_job',['scontrol','-o','show','job','21911045']),('message_timeout',['scontrol','show','config'])):
 begin=time.monotonic()
 try:
  r=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=15)
  assert len(r.stdout)+len(r.stderr)<=256*1024
  text=r.stdout.decode('utf-8','replace')
  selected=text if name=='failed_job'else '\n'.join(line for line in text.splitlines() if line.strip().startswith('MessageTimeout'))
  out[name]={'actual_exit_code':r.returncode,'elapsed_seconds':time.monotonic()-begin,'stdout_bytes':len(r.stdout),'stdout_sha256':hashlib.sha256(r.stdout).hexdigest(),'selected_stdout':selected,'stderr':r.stderr.decode('utf-8','replace')}
 except subprocess.TimeoutExpired as e:
  out[name]={'timed_out':True,'elapsed_seconds':time.monotonic()-begin,'observed_stdout_bytes':len(e.stdout or b''),'observed_stderr_bytes':len(e.stderr or b'')}
print(json.dumps(out))
