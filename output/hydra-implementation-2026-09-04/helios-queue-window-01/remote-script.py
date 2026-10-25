
import json,subprocess,signal
signal.alarm(20)
command=['squeue','-h','-p','plgrid-gpu-gh200','-t','RUNNING','-o','%L|%D|%b']
r=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=15)
assert len(r.stdout.encode())+len(r.stderr.encode())<=32768
print(json.dumps({'read_only':True,'command':command,'actual_exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr}),flush=True)
