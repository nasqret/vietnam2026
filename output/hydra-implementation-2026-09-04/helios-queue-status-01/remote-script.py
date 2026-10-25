
import json,os,subprocess,signal
signal.alarm(45)
commands=[['sinfo','-h','-p','plgrid-gpu-gh200','-o','%P|%a|%D|%t|%G'],['squeue','--start','-h','-j','21911815','-o','%i|%T|%S|%R']]
rows=[]
for command in commands:
 r=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=15)
 assert len(r.stdout.encode())+len(r.stderr.encode())<=16384
 rows.append({'command':command,'actual_exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
print(json.dumps({'read_only':True,'observations':rows}),flush=True)
