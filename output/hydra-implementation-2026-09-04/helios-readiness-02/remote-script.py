import json,os,subprocess
p='/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904'
commands={'queue':['squeue','--array','-h','-u',str(os.getuid()),'-o','%i|%T|%j|%b'],'quota':['/usr/bin/lfs','quota','-q','-u',str(os.getuid()),p]}
result={}
for k,c in commands.items():
 r=subprocess.run(c,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=10)
 assert len(r.stdout)+len(r.stderr)<65536
 result[k]={'actual_exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
print(json.dumps(result))
