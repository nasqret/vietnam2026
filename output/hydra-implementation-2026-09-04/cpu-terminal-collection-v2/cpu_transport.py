"""Explicit one-shot CPU package upload, held submission, release, collection.

No action occurs at import. Every operation needs a fresh local receipt path;
remote claims survive failures. Submission remains held until a separate release.
The embedded login helper uses only Python 3.6-compatible standard-library code.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shlex
import subprocess
import time

CAMPAIGN = "/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904"
REMOTE_BUNDLE = CAMPAIGN + "/bundles/combined-source-01"
REMOTE_JOB = CAMPAIGN + "/cpu-fixture-01"
SSH = ["/usr/bin/ssh", "-T", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15",
       "-o", "ServerAliveInterval=10", "-o", "ServerAliveCountMax=2", "-o", "ForwardAgent=no",
       "-o", "ClearAllForwardings=yes", "-o", "StrictHostKeyChecking=yes", "-o", "UpdateHostKeys=no",
       "-o", "ControlMaster=no", "-o", "ControlPath=none", "--", "plgnasqret@helios.cyfronet.pl"]

REMOTE = r'''
import hashlib,io,json,os,re,shlex,signal,stat,subprocess,sys,tarfile,time
from pathlib import Path
os.umask(0o077)
signal.alarm(180)
started=time.monotonic()
CAMPAIGN='/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904'
BUNDLE=Path(CAMPAIGN+'/bundles/combined-source-01')
JOB=Path(CAMPAIGN+'/cpu-fixture-01')
CONTROL='output/hydra-implementation-2026-09-04/cpu-fixture-control-v1'
def need(value,message):
 if not value: raise ValueError(message)
def canonical(value):
 return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def save(path,value):
 raw=canonical(value)+b'\n';need(len(raw)<=1024*1024,'Oversized receipt')
 with path.open('xb') as out:out.write(raw)
def read(path,limit):
 info=path.lstat();need(stat.S_ISREG(info.st_mode) and info.st_nlink==1 and info.st_size<=limit,'Unsafe input')
 with path.open('rb') as stream:raw=stream.read(limit+1)
 need(len(raw)==info.st_size,'Input changed');return raw
def run(argv,label,seconds=20):
 output,error=JOB/(label+'.stdout.txt'),JOB/(label+'.stderr.txt')
 process=None;stop=None;began=time.monotonic()
 try:
  with output.open('xb') as out,error.open('xb') as err:
   process=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=out,stderr=err)
   while process.poll() is None:
    if time.monotonic()-began>seconds:stop='wall'
    elif output.stat().st_size+error.stat().st_size>65536:stop='output'
    if stop:process.kill();break
    time.sleep(.05)
   code=process.wait(timeout=3)
 finally:
  if process is not None and process.poll() is None:process.kill();process.wait(timeout=3)
 record={'argv':argv,'actual_exit_code':code,'stop_reason':stop,'elapsed_seconds':time.monotonic()-began,'child_reaped':True,'automatic_retry':False}
 save(JOB/(label+'.execution.json'),record)
 need(stop is None and code==0,'Command failed: '+label)
 return read(output,65536).decode()
def fields(raw):
 result={}
 for key,value in re.findall(r'(?:^|\s)([A-Za-z][A-Za-z0-9]*)=([^\s]+)',raw):
  need(key not in result,'Duplicate Slurm field');result[key]=value
 return result
def exact_held(raw,reservation):
 values=fields(raw)
 for key,value in {'JobId':reservation['job_id'],'JobName':reservation['job_name'],
 'Comment':'hydra-cpu-fixture:'+reservation['nonce'],'Account':'plgccaiautore2026-cpu',
 'Partition':'plgrid','JobState':'PENDING','Reason':'JobHeldUser','Requeue':'0','Restarts':'0',
 'NumNodes':'1','NumCPUs':'2','NumTasks':'1','TimeLimit':'00:02:00'}.items():
  need(values.get(key)==value,'Held CPU identity differs: '+key)
 owner=re.fullmatch(r'[^()\s]+\((\d+)\)',values.get('UserId',''))
 need(owner is not None and int(owner.group(1))==105923,'Wrong CPU job owner')
 need('gres' not in values.get('ReqTRES',''),'Held CPU request contains GRES')
 return values
def reservation_input(request):
 raw=read(JOB/'reservation.json',65536)
 need(hashlib.sha256(raw).hexdigest()==request['reservation_sha256'],'Changed reservation')
 reservation=json.loads(raw)
 need(reservation['job_id']==request['job_id'] and reservation['source']==str(BUNDLE/'source') and reservation['job_directory']==str(JOB),'Wrong owned CPU job')
 return reservation
need(os.getuid()==105923,'Wrong remote uid')
header=sys.stdin.buffer.readline(1024*1024+1)
need(header.endswith(b'\n') and len(header)<=1024*1024,'Invalid bounded request')
request=json.loads(header);operation=request['operation']
need(operation in {'upload','submit-held','release','collect'},'Unsupported operation')
if operation=='upload':
 manifest=request['manifest'];archive_bytes=manifest['archive_bytes']
 need(0<archive_bytes<16*1024*1024 and 0<manifest['expanded_bytes']<160*1024*1024 and 1200<manifest['file_count']<1400,'Package bounds differ')
 need(hashlib.sha256(canonical(manifest)+b'\n').hexdigest()==request['manifest_sha256'],'Exact canonical manifest required')
 BUNDLE.mkdir(parents=True,exist_ok=False)
 remaining=archive_bytes;digest=hashlib.sha256()
 with (BUNDLE/'source-data.tar.gz').open('xb') as out:
  while remaining:
   block=sys.stdin.buffer.read(min(1024*1024,remaining));need(block,'Premature upload EOF')
   out.write(block);digest.update(block);remaining-=len(block)
  need(not sys.stdin.buffer.read(1),'Trailing upload bytes')
 need(digest.hexdigest()==manifest['archive_sha256'],'Archive SHA differs')
 source=BUNDLE/'source';source.mkdir();seen=set();total=0
 with tarfile.open(str(BUNDLE/'source-data.tar.gz'),'r:gz') as archive:
  for item in archive:
   relative=Path(item.name);need(item.isfile() and not relative.is_absolute() and '..' not in relative.parts and str(relative)==item.name,'Unsafe archive member')
   need(item.name not in seen and item.name in manifest['files'],'Unexpected archive member');seen.add(item.name)
   pin=manifest['files'][item.name];need(item.size==pin['bytes'],'Archive size differs')
   total+=item.size;need(total<=manifest['expanded_bytes'],'Expansion bound exceeded')
   raw=archive.extractfile(item).read(item.size+1)
   need(len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256'],'Archive member changed')
   target=source/relative;target.parent.mkdir(parents=True,exist_ok=True)
   with target.open('xb') as out:out.write(raw)
 need(seen==set(manifest['files']) and len(seen)==manifest['file_count'] and total==manifest['expanded_bytes'],'Incomplete package')
 save(BUNDLE/'manifest.json',manifest)
 result={'schema':'hydra-combined-source-upload-v1','source':str(source),'archive_sha256':digest.hexdigest(),'manifest_sha256':request['manifest_sha256'],'verified_files':len(seen),'verified_bytes':total,'gpu_allocations':0,'automatic_retry':False}
 save(BUNDLE/'upload-completion.json',result);print(canonical(result).decode(),flush=True)
elif operation=='submit-held':
 need(not sys.stdin.buffer.read(1),'Trailing request')
 manifest_raw=read(BUNDLE/'manifest.json',1024*1024);manifest=json.loads(manifest_raw)
 need(hashlib.sha256(manifest_raw).hexdigest()==request['manifest_sha256'] and manifest['archive_sha256']==request['archive_sha256'],'Wrong remote package')
 source=BUNDLE/'source'
 for name in ('remote_cpu_job.sh','remote_cpu_fixture.py'):
  relative=CONTROL+'/'+name;raw=read(source/relative,1024*1024)
  need(manifest['files'][relative]=={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()},'Changed CPU wrapper')
 need(re.fullmatch(r'[0-9a-f]{32}',request['nonce']) is not None,'Invalid nonce')
 JOB.mkdir(exist_ok=False)
 save(JOB/'submission-intent.json',request)
 job_name='hydra-cpu-fixture-'+request['nonce'][:12]
 script='#!/bin/bash\nset -eu\numask 077\nexec /bin/bash '+shlex.quote(str(source/CONTROL/'remote_cpu_job.sh'))+' '+shlex.quote(str(source))+' '+shlex.quote(str(JOB))+'\n'
 with (JOB/'job.sh').open('xb') as out:out.write(script.encode())
 response=run(['sbatch','--parsable','--hold','--no-requeue','--account=plgccaiautore2026-cpu','--partition=plgrid','--nodes=1','--ntasks=1','--cpus-per-task=2','--mem=4096M','--time=00:02:00','--job-name='+job_name,'--comment=hydra-cpu-fixture:'+request['nonce'],'--output='+str(JOB/'slurm-%j.out'),'--error='+str(JOB/'slurm-%j.err'),str(JOB/'job.sh')],'sbatch',30).strip()
 match=re.fullmatch(r'([0-9]{1,20})(?:;[A-Za-z0-9_.-]+)?',response);need(match is not None,'Malformed actual sbatch job ID')
 job_id=match.group(1)
 reservation={'schema':'hydra-cpu-fixture-reservation-v1','job_id':job_id,'job_name':job_name,'nonce':request['nonce'],'uid':os.getuid(),'source':str(source),'job_directory':str(JOB),'archive_sha256':request['archive_sha256'],'manifest_sha256':request['manifest_sha256'],'account':'plgccaiautore2026-cpu','partition':'plgrid','cpus':2,'memory_gib':4,'seconds':120,'gpus':0,'automatic_retry':False,'resume':False}
 save(JOB/'reservation.json',reservation);reservation_sha=hashlib.sha256(read(JOB/'reservation.json',65536)).hexdigest()
 with (JOB/'reservation.sha256').open('xb') as out:out.write((reservation_sha+'\n').encode())
 held=exact_held(run(['scontrol','-o','show','job',job_id],'held-inspect',15),reservation)
 result={'schema':'hydra-cpu-held-submission-v1','job_id':job_id,'reservation_sha256':reservation_sha,'job_directory':str(JOB),'held':True,'observed':held,'gpu_allocations':0,'automatic_retry':False}
 save(JOB/'held-completion.json',result);print(canonical(result).decode(),flush=True)
elif operation=='release':
 need(not sys.stdin.buffer.read(1),'Trailing request')
 reservation=reservation_input(request)
 save(JOB/'release.claimed.json',{'job_id':reservation['job_id'],'reservation_sha256':request['reservation_sha256'],'automatic_retry':False})
 observed=exact_held(run(['scontrol','-o','show','job',reservation['job_id']],'release-inspect',15),reservation)
 run(['scontrol','release',reservation['job_id']],'release',20)
 result={'schema':'hydra-cpu-release-v1','job_id':reservation['job_id'],'released':True,'gpu_allocations':0,'automatic_retry':False}
 save(JOB/'release-completion.json',result);print(canonical(result).decode(),flush=True)
else:
 need(not sys.stdin.buffer.read(1),'Trailing request')
 reservation=reservation_input(request)
 # Read only, once per collection. The local destination must be fresh.
 suffix=request['collection_nonce'];need(re.fullmatch(r'[0-9a-f]{12}',suffix) is not None,'Invalid collection nonce')
 accounting=run(['sacct','--parsable2','--noheader','--jobs='+reservation['job_id'],'--format=JobIDRaw,JobName,State,ExitCode,ElapsedRaw,AllocCPUS,ReqMem,AllocTRES,NodeList'],'sacct-'+suffix,20)
 queue_all=run(['squeue','--array','--noheader','--user=105923','--format=%i|%j|%T|%M|%C|%m|%b'],'squeue-'+suffix,15)
 queue='\n'.join(row for row in queue_all.splitlines() if row.split('|',1)[0]==reservation['job_id'])
 result={'schema':'hydra-cpu-fixture-terminal-collection-v1','job_id':reservation['job_id'],'reservation_sha256':request['reservation_sha256'],'sacct':accounting,'squeue':queue,'queue_empty':not bool(queue.strip()),'actual_process_exit':None,'job_completion':None,'gpu_allocations':0,'automatic_retry':False}
 if (JOB/'actual-process-exit.txt').exists():result['actual_process_exit']=read(JOB/'actual-process-exit.txt',32).decode().strip()
 if (JOB/'job-completion.json').exists():result['job_completion']=json.loads(read(JOB/'job-completion.json',1024*1024))
 save(JOB/('collection-'+suffix+'.json'),result)
 members=[];total=0
 for path in sorted(JOB.rglob('*')):
  if path.is_dir():continue
  info=path.lstat();need(stat.S_ISREG(info.st_mode) and info.st_nlink==1 and info.st_size<=8*1024*1024,'Unsafe/oversized job artifact')
  total+=info.st_size;need(total<=32*1024*1024 and len(members)<160,'Job artifact bound exceeded')
  members.append(path)
 buffer=io.BytesIO()
 with tarfile.open(fileobj=buffer,mode='w:gz') as archive:
  for path in members:archive.add(str(path),arcname=str(path.relative_to(JOB)),recursive=False)
 raw=buffer.getvalue();need(len(raw)<=16*1024*1024,'Collected archive too large')
 header={'result':result,'archive_sha256':hashlib.sha256(raw).hexdigest(),'archive_bytes':len(raw),'files':len(members),'expanded_bytes':total}
 sys.stdout.buffer.write(canonical(header)+b'\n'+raw);sys.stdout.buffer.flush()
'''


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("collect",))
    parser.add_argument("--bundle", type=Path)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--job-id")
    parser.add_argument("--reservation-sha256")
    args = parser.parse_args()
    import secrets
    request = {"operation": args.operation}
    tail = b""
    if args.operation in {"upload", "submit-held"}:
        if args.bundle is None:
            parser.error("--bundle is required")
        raw = (args.bundle / "manifest.json").read_bytes()
        manifest = json.loads(raw)
        if raw != canonical(manifest) + b"\n":
            raise ValueError("Use the new combined package's exact canonical manifest.")
        request.update(manifest_sha256=hashlib.sha256(raw).hexdigest(), archive_sha256=manifest["archive_sha256"])
        if args.operation == "upload":
            tail = (args.bundle / "source-data.tar.gz").read_bytes()
            if len(tail) != manifest["archive_bytes"] or hashlib.sha256(tail).hexdigest() != manifest["archive_sha256"]:
                raise ValueError("Local sealed archive differs.")
            request["manifest"] = manifest
        else:
            request["nonce"] = secrets.token_hex(16)
    else:
        import re
        if not re.fullmatch(r"[0-9]{1,20}", args.job_id or "") or not re.fullmatch(r"[0-9a-f]{64}", args.reservation_sha256 or ""):
            parser.error("exact --job-id and --reservation-sha256 are required")
        request.update(job_id=args.job_id, reservation_sha256=args.reservation_sha256)
        if args.operation == "collect":
            request["collection_nonce"] = secrets.token_hex(6)
    args.receipt.mkdir(parents=True, exist_ok=False)
    (args.receipt / "request.json").write_bytes(canonical(request) + b"\n")
    (args.receipt / "remote-script.py").write_text(REMOTE)
    started, timed_out = time.monotonic(), False
    try:
        completed = subprocess.run(SSH + ["python3 -c " + shlex.quote(REMOTE)],
            input=canonical(request) + b"\n" + tail, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=200)
        output, error, code = completed.stdout, completed.stderr, completed.returncode
    except subprocess.TimeoutExpired as failure:
        timed_out = True
        output, error, code = failure.stdout or b"", failure.stderr or b"", None
    (args.receipt / "stdout.bin").write_bytes(output)
    (args.receipt / "stderr.txt").write_bytes(error)
    record = {"schema": "hydra-cpu-transport-execution-v1", "operation": args.operation,
              "actual_ssh_exit_code": code, "transport_timeout": timed_out,
              "elapsed_seconds": time.monotonic() - started, "stdout_bytes": len(output),
              "stderr_bytes": len(error), "remote_bundle": REMOTE_BUNDLE, "remote_job": REMOTE_JOB,
              "gpu_allocations": 0, "automatic_retry": False}
    (args.receipt / "actual-completion.json").write_bytes(canonical(record) + b"\n")
    if args.operation == "collect" and code == 0:
        header, archive = output.split(b"\n", 1)
        collection = json.loads(header)
        if len(archive) != collection["archive_bytes"] or hashlib.sha256(archive).hexdigest() != collection["archive_sha256"]:
            raise ValueError("Collected artifact archive differs.")
        (args.receipt / "job-artifacts.tar.gz").write_bytes(archive)
        (args.receipt / "collection.json").write_bytes(canonical(collection) + b"\n")
        print(json.dumps(collection, sort_keys=True))
    else:
        print(output.decode("utf-8", errors="replace")[:65536], end="")
    print(error.decode("utf-8", errors="replace")[:65536], end="")
    print(json.dumps(record, sort_keys=True), flush=True)
    return code if code is not None else 124


if __name__ == "__main__":
    raise SystemExit(main())
