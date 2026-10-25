"""Observe real SLURM batch USR1 delivery through the weekend Apptainer exec path."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

if not os.environ.get('SLURM_JOB_ID'):
    raise SystemExit('SLURM required')
out = Path('/net/scratch/hscra/plgrid/plgnasqret/latent/artifacts/campaign6/validation')/os.environ['SLURM_JOB_ID']
out.mkdir(parents=True,exist_ok=False)
start = time.monotonic()
received = []
signal.signal(signal.SIGUSR1,lambda number,frame:received.append(number))
child_code = '''import json,os,signal,sys,time
from pathlib import Path
root=Path(sys.argv[1]); received=[]
signal.signal(signal.SIGUSR1,lambda number,frame:received.append(number))
(root/'child-started.json').write_text(json.dumps({'pid':os.getpid()}))
while not received: time.sleep(.1)
tmp=root/'child-stop.tmp'; tmp.write_text(json.dumps({'signals':received,'checkpoint_saved':True}))
tmp.replace(root/'child-stop.json')
'''
child = subprocess.Popen([sys.executable,'-c',child_code,str(out)],start_new_session=True)
(out/'started.json').write_text(json.dumps({'pid':os.getpid(),'job_id':os.environ['SLURM_JOB_ID']}))
while not received and time.monotonic()-start < 100:
    time.sleep(.2)
if received:
    os.killpg(child.pid,signal.SIGUSR1)
    child.wait(timeout=10)
else:
    os.killpg(child.pid,signal.SIGTERM)
    child.wait(timeout=10)
child_record = json.loads((out/'child-stop.json').read_text()) if (out/'child-stop.json').exists() else {}
value = {'state':'passed' if received == [signal.SIGUSR1] and child_record.get('checkpoint_saved') else 'failed',
    'job_id':os.environ['SLURM_JOB_ID'],'signals':received,'elapsed_seconds':time.monotonic()-start,
    'child_receipt':child_record,
    'scope':'Observed batch USR1 via exec Apptainer to Python and owned child stop receipt; no model execution'}
(out/'validation.json').write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps(value),flush=True)
raise SystemExit(0 if value['state'] == 'passed' else 1)
