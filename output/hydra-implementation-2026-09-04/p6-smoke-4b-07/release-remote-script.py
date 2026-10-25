
import hashlib,json,os,re,subprocess,sys
from pathlib import Path
request=json.loads(sys.stdin.read(128*1024))
record=request['reservation'];job=record['job_id'];directory=Path(request['directory'])
raw=request['raw'].encode();assert hashlib.sha256(raw).hexdigest()==request['sha256']
assert json.loads(raw)==record and record['uid']==os.getuid()
assert directory.is_dir() and directory.name=='p6-smoke-4b-07'
query=subprocess.run(['scontrol','-o','show','job',job],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=5)
assert query.returncode==0 and len(query.stdout.encode())<=65536
fields=dict(re.findall(r'(?:^|\s)([A-Za-z][A-Za-z0-9]*)=([^\s]+)',query.stdout))
assert fields.get('JobId')==job and fields.get('JobName')==record['job_name']
assert fields.get('Comment')=='hydra-p6:'+record['nonce'] and fields.get('JobState')=='PENDING'
assert fields.get('Reason')=='JobHeldUser' and fields.get('Requeue')=='0' and fields.get('Restarts')=='0'
assert fields.get('Account')==record['account'] and fields.get('Partition')==record['partition']
assert fields.get('TimeLimit')=='00:10:00' and fields.get('NumCPUs')=='8'
assert re.fullmatch(r'[^()]+\('+str(os.getuid())+r'\)',fields.get('UserId',''))
tres=dict(item.split('=',1) for item in fields['ReqTRES'].split(','))
assert tres.get('cpu')=='8' and tres.get('mem')=='64G' and tres.get('node')=='1' and tres.get('gres/gpu')=='1'
queue=subprocess.run(['squeue','-h','-u',str(os.getuid()),'-o','%i|%b'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=5)
assert queue.returncode==0 and len(queue.stdout.encode())<=16384
for line in queue.stdout.splitlines():
 identifier,gres=line.split('|',1)
 assert identifier==job or gres in ('N/A','(null)',''),'Another owned GPU job appeared; do not release'
with (directory/'reservation.json').open('xb') as stream:stream.write(raw)
with (directory/'reservation.sha256').open('x') as stream:stream.write(request['sha256']+'\n')
with (directory/'release-request.json').open('x') as stream:json.dump({'job_id':job,'reservation_sha256':request['sha256'],'before':fields,'automatic_retry':False},stream)
result=subprocess.run(['scontrol','release',job],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=5)
receipt={'actual_release_exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr,
 'job_id':job,'reservation_sha256':request['sha256'],'released':result.returncode==0,'allocated_seconds_ceiling':600,'automatic_retry':False}
with (directory/'release-completion.json').open('x') as stream:json.dump(receipt,stream,indent=2)
print(json.dumps(receipt),flush=True)
sys.exit(result.returncode)
