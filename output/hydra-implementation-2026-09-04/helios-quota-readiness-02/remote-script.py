
import json,os,subprocess,signal
signal.alarm(50)
commands=[['/usr/bin/lfs','quota','-h','-u',str(os.getuid()),'/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training'],['squeue','--start','-h','-j','21911815','-o','%i|%T|%S|%R']]
rows=[]
for command in commands:
 r=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=20)
 assert len(r.stdout.encode())+len(r.stderr.encode())<=16384
 rows.append({'command':command,'actual_exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
print(json.dumps({'read_only':True,'observations':rows}),flush=True)
