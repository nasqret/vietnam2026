#!/usr/bin/env python3
"""One bounded read-only observation of an explicitly identified retention job.

No scheduler mutation, retry, source edit, upload, model/native import or proof
verification. Each invocation keeps a fresh local start marker and observation.
Log/HEAD progress is operational evidence, never an independently verified score.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import selectors
import shlex
import signal
import stat
import subprocess
import sys
import time

ARCHIVE = Path('/Users/bnaskrecki/codex/peano/artifacts/hydra-retention-pilot-2026-08-30')
SOURCE_COMMIT = '4aeae795c8cb5bfc622c9943359b5b38446089b9'
HOST = 'plgnasqret@helios.cyfronet.pl'
LIMITS = {'remote_cpu_seconds':20, 'remote_wall_seconds':30, 'remote_address_space_bytes':320 * 1024**2,
          'remote_file_write_bytes':0, 'scheduler_command_wall_seconds':8, 'scheduler_stream_bytes':65536,
          'log_tail_bytes_each':65536, 'small_metadata_bytes':65536, 'manifest_bytes':4 * 1024**2,
          'evaluation_report_hash_bytes':48 * 1024**2, 'ssh_wall_seconds':50, 'local_wall_seconds':60,
          'local_cpu_seconds':20, 'local_checked_rss_bytes':320 * 1024**2,
          'stdout_bytes':2 * 1024**2, 'stderr_bytes':65536, 'local_receipt_bytes':4 * 1024**2}

PROGRAM = r'''
import base64,datetime,hashlib,json,os,re,resource,selectors,signal,stat,subprocess,sys,time
from pathlib import Path
ROOT='/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/retention-pilot-v1'
PROFILE='peano-hydra-retention-pilot-v1'
PACKAGE='_deploy/hydra-retention-pilot-v1'
COMMIT='4aeae795c8cb5bfc622c9943359b5b38446089b9'
TRAIN_PLAN='da26332740d587bdd946b12999fd37de73817115ed3da8983edf5004bd02abf0'
AUTHORITY='04ac3b5997b4f2a78c4ce41642b9e596d63abf1c82ec2441ab240b0f78fd5778'
MODEL='results/peano-hydra/qwen3-1.7b-authority-primitive-retention-pilot-v1'
EVALUATION='results/peano-hydra/evaluations/retention-pilot-v1'
SOURCE_PINS={
 'training/peano_hydra/__init__.py':{'bytes':1325,'sha256':'b1decc860e0951b02bd1f175078a1a0ff0e3b59b41aa9ce6d6de8cc65473f298'},
 'training/peano_hydra/retention_launch.py':{'bytes':28602,'sha256':'bed869bec7d2d873885fd90c97e90c1910948ab39a492caa829299f7f599c9c0'},
 'training/peano_hydra/search_launch.py':{'bytes':49182,'sha256':'3d393ceb547c5199297748af647c7c6c51c67bf176011dcd68b257dc6d3f97ca'},
}
CAP=65536
RESERVATIONS={'train':{'seconds':7200,'gpus':1,'cpus':8,'memory_gib':64},
              'evaluate':{'seconds':3600,'gpus':1,'cpus':8,'memory_gib':64}}
WALL={'train':'02:00:00','evaluate':'01:00:00'}
def require(value,message):
    if not value:raise ValueError(message)
def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def sha(raw):return hashlib.sha256(raw).hexdigest()
def pin(raw):return {'bytes':len(raw),'sha256':sha(raw)}
def decode(raw):
    def pairs(items):
        result={}
        for key,value in items:
            require(key not in result,'duplicate metadata key');result[key]=value
        return result
    def invalid(_):raise ValueError('nonfinite metadata value')
    result=json.loads(raw,object_pairs_hook=pairs,parse_constant=invalid)
    require(type(result) is dict,'metadata object required')
    return result
def directory(path):
    require(path.startswith('/') and all(part not in ('','..','.') for part in path.split('/')[1:]),'fixed absolute directory required')
    parts=path.split('/')[1:];access=getattr(os,'O_PATH',os.O_RDONLY)
    fd=os.open('/',access|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:
        for i,part in enumerate(parts,1):
            nxt=os.open(part,(os.O_RDONLY if i==len(parts) else access)|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd)
            os.close(fd);fd=nxt
        result,fd=fd,-1;return result
    finally:
        if fd>=0:os.close(fd)
def signature(info):
    return (info.st_dev,info.st_ino,info.st_mode,info.st_nlink,info.st_size,info.st_mtime_ns,info.st_ctime_ns)
def read_file(name,maximum,retain=True):
    require(name and not name.startswith('/') and all(p not in ('','.','..') for p in name.split('/')),'fixed root-relative file required')
    parent_path,leaf=(ROOT+'/'+name).rsplit('/',1);parent=directory(parent_path);fd=-1
    try:
        fd=os.open(leaf,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=parent);before=os.fstat(fd)
        require(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and 0<=before.st_size<=maximum,'unsafe or oversized metadata file')
        chunks=[];count=0;hasher=hashlib.sha256()
        while True:
            block=os.read(fd,min(CAP,maximum-count+1))
            if not block:break
            count+=len(block);require(count<=maximum,'file grew past read cap');hasher.update(block)
            if retain:chunks.append(block)
        after=os.fstat(fd);named=os.stat(leaf,dir_fd=parent,follow_symlinks=False)
        require(signature(before)==signature(after)==signature(named) and count==before.st_size,'metadata changed during observation')
        again=directory(parent_path)
        try:require((os.fstat(again).st_dev,os.fstat(again).st_ino)==(os.fstat(parent).st_dev,os.fstat(parent).st_ino),'input parent replaced')
        finally:os.close(again)
        return {'bytes':count,'sha256':hasher.hexdigest()},b''.join(chunks) if retain else None
    finally:
        if fd>=0:os.close(fd)
        os.close(parent)
def bound_job(job,stage,approval_sha,header_sha):
    for name,expected in SOURCE_PINS.items():require(read_file(name,CAP)[0]==expected,'pinned read-only launcher source changed')
    require(not os.path.lexists(ROOT+'/.git'),'observer requires actual transferred source provenance')
    if ROOT not in sys.path:sys.path.insert(0,ROOT)
    from training.peano_hydra import retention_launch as gate
    require(str(gate.ROOT)==str(gate.safe.ROOT)==ROOT,'read-only gate imported another source root')
    approval_raw=read_file(PACKAGE+'/approval.json',CAP)[1]
    request_raw=read_file(PACKAGE+'/resource-request.json',4*1024**2)[1]
    approval,request=decode(approval_raw),decode(request_raw)
    require(sha(approval_raw)==approval_sha and approval.get('schema')==gate.APPROVAL_SCHEMA
        and approval.get('profile')==PROFILE and approval.get('run_id')=='retention-pilot-v1'
        and approval.get('approved') is True and approval.get('standing_authority_sha256')==AUTHORITY
        and approval.get('request_file_sha256')==sha(request_raw),'external approval/request binding differs')
    require(request.get('schema')==gate.REQUEST_SCHEMA and request.get('status')=='ready'
        and request.get('profile')==PROFILE and request.get('run_id')=='retention-pilot-v1'
        and request.get('source_commit')==COMMIT and request.get('reservations')==RESERVATIONS
        and request.get('maximum_aggregate_gpu_seconds')==10800 and request.get('maximum_concurrent_gpus')==1
        and all(request.get(k) is False for k in ('automatic_retry','resume','refunds'))
        and request.get('payloads_sha256')==gate.digest(request['payloads']),'fixed pilot resource header differs')
    identity=gate.identity(approval,request,approval_sha)
    require(gate.digest(identity)==header_sha,'external immutable source header changed')
    ledger=gate.load_ledger(stage,identity)
    require(ledger['job_id']==job and ledger['phase'] in ('accepted','held-validated','release-authorized','released')
        and ledger['gpu_seconds']==RESERVATIONS[stage]['seconds'],'actual job is not the recorded one-use stage reservation')
    item=request['scientific_inputs'][stage]
    require(item['path']==PACKAGE+'/'+stage+'-request.json','scientific stage path changed')
    stage_pin,stage_raw=read_file(item['path'],CAP)
    require(stage_pin=={k:item[k] for k in ('bytes','sha256')},'scientific stage raw pin changed')
    scientific=decode(stage_raw)
    require(scientific.get('schema')=='peano-hydra-retention-pilot-stage-request-v1'
        and scientific.get('profile')==PROFILE and scientific.get('run_id')=='retention-pilot-v1'
        and scientific.get('stage')==stage and scientific.get('training_plan_sha256')==TRAIN_PLAN
        and scientific.get('output')==(MODEL if stage=='train' else EVALUATION),'scientific stage/output changed')
    require(not any(name in sys.modules for name in ('torch','transformers','peft','peano_lite','accelerate')),'observer imported a model/native framework')
    return {'job_id':job,'stage':stage,**identity,'source_header_sha256':header_sha,
        'scientific_input':item,'training_plan_sha256':TRAIN_PLAN,'ledger_phase':ledger['phase'],
        'ledger_events':len(ledger['events']),'ledger_path':gate.LEDGERS[stage],
        'ledger':pin(ledger['raw']),'ledger_base64':base64.b64encode(ledger['raw']).decode(),
        'reservation':RESERVATIONS[stage],'reserved_model_manifest':ledger['model_manifest'],
        'full_execution_source_and_payloads_rehashed':False,'scientific_inputs_reauthenticated':False}
def command(args):
    child=None;selector=None;values={'stdout':bytearray(),'stderr':bytearray()};started=time.monotonic()
    try:
        child=subprocess.Popen(args,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
        selector=selectors.DefaultSelector()
        for name in values:
            stream=getattr(child,name);os.set_blocking(stream.fileno(),False);selector.register(stream,selectors.EVENT_READ,name)
        while selector.get_map():
            require(time.monotonic()-started<8,'scheduler read deadline')
            for key,_ in selector.select(.1):
                raw=os.read(key.fileobj.fileno(),8192)
                if not raw:selector.unregister(key.fileobj);continue
                room=CAP-len(values[key.data]);values[key.data].extend(raw[:room])
                require(len(raw)<=room,'scheduler read output bound')
        child.wait(timeout=max(.01,8-(time.monotonic()-started)))
        return {'argv':args,'returncode':child.returncode,'wall_seconds':time.monotonic()-started,
                **{key:bytes(value).decode('utf-8','replace') for key,value in values.items()}}
    finally:
        if child is not None:
            if child.poll() is None:
                try:os.killpg(child.pid,signal.SIGKILL)
                except ProcessLookupError:pass
                child.wait(timeout=2)
            child.stdout.close();child.stderr.close()
        if selector is not None:selector.close()
def scheduler(job,stage):
    current=command(['scontrol','-o','show','job',job]);accounting=command(['sacct','-n','-P','-X','-j',job,
        '--format=JobIDRaw,JobName%80,State%32,ExitCode,ElapsedRaw,TimelimitRaw,AllocCPUS,ReqMem,AllocTRES%256,WorkDir%4096,Account,Partition,User'])
    live_state=account_state=None
    if current['returncode']==0:
        lines=current['stdout'].strip().splitlines();require(len(lines)==1,'one exact scheduler job required')
        fields={}
        for match in re.finditer(r'(?:^|\s)([A-Za-z][A-Za-z0-9]*)=(\S*)',lines[0]):
            key,value=match.groups();require(key not in fields,'duplicate scheduler field');fields[key]=value
        require(fields.get('JobId')==job and fields.get('JobName')==PROFILE+'-'+stage
            and fields.get('WorkDir')==ROOT and fields.get('Account')=='plgccaiautore2026-gpu-gh200'
            and fields.get('Partition')=='plgrid-gpu-gh200' and fields.get('TimeLimit')==WALL[stage]
            and fields.get('NumCPUs')=='8' and fields.get('NumNodes') in ('1','1-1') and fields.get('Requeue')=='0'
            and re.fullmatch(r'plgnasqret\([0-9]+\)',fields.get('UserId',''))
            and fields.get('StdOut')==ROOT+'/logs/'+PROFILE+'-'+stage+'-'+job+'.out'
            and fields.get('StdErr')==ROOT+'/logs/'+PROFILE+'-'+stage+'-'+job+'.err','scontrol identity/resources/log paths changed')
        tres={}
        for item in fields.get('ReqTRES','').split(','):
            key,separator,value=item.partition('=');require(separator and key not in tres,'ambiguous requested resources');tres[key]=value
        require(tres.get('cpu')=='8' and tres.get('node')=='1' and tres.get('gres/gpu')=='1'
            and tres.get('mem') in ('64G','65536M','67108864K')
            and all(v=='1' for k,v in tres.items() if k.startswith('gres/gpu:')),'scontrol one-GPU/64GiB request changed')
        live_state=fields.get('JobState');current['bound_fields']=fields
    if accounting['returncode']==0:
        rows=[]
        for line in accounting['stdout'].splitlines():
            if not line.strip():continue
            row=[part.strip() for part in line.split('|')]
            if len(row)==14 and row[-1]=='':row.pop()
            require(len(row)==13 and row[0]==job,'accounting returned another job');rows.append(row)
        require(len(rows)<=1,'duplicate top-level accounting job')
        if rows:
            row=rows[0]
            require(row[1]==PROFILE+'-'+stage and row[5]==str(RESERVATIONS[stage]['seconds']//60)
                and row[7] in ('64G','65536M','67108864K') and row[9]==ROOT
                and row[10:]==['plgccaiautore2026-gpu-gh200','plgrid-gpu-gh200','plgnasqret'],
                'sacct identity/resources changed')
            account_state=row[2];accounting['bound_row']=row
    require(live_state or account_state,'actual job is absent from both bounded scheduler reads')
    return {'scontrol':current,'sacct':accounting,'observed_state':live_state or account_state,
            'snapshots_may_differ':True,'terminal_state_required':False}
def tail(name):
    parent=fd=None
    try:
        parent_path,leaf=(ROOT+'/'+name).rsplit('/',1);parent=directory(parent_path)
        fd=os.open(leaf,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=parent);before=os.fstat(fd)
        require(stat.S_ISREG(before.st_mode) and before.st_nlink==1,'unsafe job log')
        offset=max(0,before.st_size-CAP);wanted=before.st_size-offset;os.lseek(fd,offset,os.SEEK_SET);raw=bytearray()
        while len(raw)<wanted:
            block=os.read(fd,wanted-len(raw));require(bool(block),'job log shrank while reading');raw.extend(block)
        after=os.fstat(fd);named=os.stat(leaf,dir_fd=parent,follow_symlinks=False)
        require(all(stat.S_ISREG(v.st_mode) and v.st_nlink==1 and (v.st_dev,v.st_ino)==(before.st_dev,before.st_ino)
            and v.st_size>=before.st_size for v in (after,named)),'job log replaced or shrank')
        again=directory(parent_path)
        try:require((os.fstat(again).st_dev,os.fstat(again).st_ino)==(os.fstat(parent).st_dev,os.fstat(parent).st_ino),'job log parent replaced')
        finally:os.close(again)
        return {'path':name,'exists':True,**pin(raw),'base64':base64.b64encode(raw).decode(),
            'offset':offset,'file_bytes_at_open':before.st_size,'file_bytes_after_read':after.st_size,
            'grew_during_read':after.st_size>before.st_size,'whole_file_captured':offset==0 and after.st_size==before.st_size}
    except FileNotFoundError:return {'path':name,'exists':False}
    finally:
        if fd is not None:os.close(fd)
        if parent is not None:os.close(parent)
def metadata(name,maximum=CAP,retain=True):
    try:
        item,raw=read_file(name,maximum,retain)
        return {'path':name,'exists':True,**item,'value':decode(raw) if retain else None,'independently_verified':False}
    except FileNotFoundError:return {'path':name,'exists':False}
    except (OSError,ValueError) as error:
        return {'path':name,'exists':None,'status':'unavailable-or-changed','error':str(error)[:512]}
def progress(logs,stage):
    latest=optimizer=None
    log=logs['out']
    if log.get('exists'):
        raw=base64.b64decode(log['base64']);lines=raw.splitlines(keepends=True)
        if log['offset'] and lines:lines=lines[1:]
        for line in lines:
            if not line.endswith(b'\n') or len(line)>16384:continue
            try:value=decode(line)
            except (ValueError,UnicodeError):continue
            schema=value.get('schema');phase=value.get('phase')
            if schema=='peano-hydra-retention-training-progress-v1' and stage=='train':
                latest=value
                if phase=='optimizer-log' and type(value.get('step')) is int and 0<=value['step']<=1469:optimizer=value
            elif schema=='peano-hydra-comparison-progress-v1' and stage=='evaluate':latest=value
    return {'latest_event_in_tail':latest,'latest_optimizer_event_in_tail':optimizer,
        'latest_optimizer_step_in_tail':None if optimizer is None else optimizer['step'],
        'expected_optimizer_steps':1469 if stage=='train' else None,
        'tail_only':True,'absence_does_not_mean_no_progress':True,'quality_claim':None}
def observe(job,stage,approval_sha,header_sha):
    binding=bound_job(job,stage,approval_sha,header_sha)
    status=scheduler(job,stage)
    logs={suffix:tail('logs/'+PROFILE+'-'+stage+'-'+job+'.'+suffix) for suffix in ('out','err')}
    values={'execution_status':metadata((MODEL if stage=='train' else EVALUATION)+'/execution-status.json')}
    measured=progress(logs,stage)
    if stage=='train':
        values['terminal_manifest']=metadata(MODEL+'/manifest.json',4*1024**2,False)
    else:
        values['checkpoint_head']=metadata(EVALUATION+'/checkpoint/HEAD.json')
        values['terminal_report']=metadata(EVALUATION+'/evaluation.json',48*1024**2,False)
        head=values['checkpoint_head'].get('value')
        measured['checkpoint_completed_records']=None
        measured['expected_checkpoint_records']=256
        if type(head) is dict and head.get('schema')=='peano-hydra-retention-evaluation-checkpoint-head-v1':
            count=head.get('completed')
            if type(count) is int and 0<=count<=256 and head.get('head_sha256')==sha(canonical({k:v for k,v in head.items() if k!='head_sha256'})):
                measured['checkpoint_completed_records']=count
                measured['checkpoint_head_self_digest_matches']=True
        measured['checkpoint_rows_or_proofs_verified']=False
    require(bound_job(job,stage,approval_sha,header_sha)==binding,'immutable source/approval/ledger changed during observation')
    return {'schema':'peano-hydra-retention-job-observation-v1','binding':binding,'scheduler':status,'logs':logs,
        'metadata':values,'progress':measured,'observed_at_utc':datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
        'read_only':True,'model_loaded':False,'model_weights_read_or_downloaded':False,
        'native_proofs_executed':False,'proofs_independently_verified':False,'quality_claim':None,
        'checkpoint_goal_records_collected':False,'scheduler_mutation_performed':False,'remote_file_writes':False,
        'automatic_retry':False}
def main():
    require(sys.flags.isolated and sys.dont_write_bytecode and sys.platform=='linux' and len(sys.argv)==5,'isolated exact-job observer required')
    job,stage,approval_sha,header_sha=sys.argv[1:]
    require(re.fullmatch(r'[1-9][0-9]{0,19}',job) and stage in RESERVATIONS
        and all(re.fullmatch(r'[0-9a-f]{64}',value) for value in (approval_sha,header_sha)),'external actual job/stage/header pins required')
    resource.setrlimit(resource.RLIMIT_CPU,(20,20));resource.setrlimit(resource.RLIMIT_AS,(320*1024**2,320*1024**2))
    resource.setrlimit(resource.RLIMIT_FSIZE,(0,0));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    def expired(*_):raise TimeoutError('remote observation30-second wall deadline')
    signal.signal(signal.SIGALRM,expired);signal.alarm(30);started=time.monotonic()
    result=observe(job,stage,approval_sha,header_sha)
    own,children=resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)
    result['resources']={'wall_seconds':time.monotonic()-started,'own_cpu_seconds':own.ru_utime+own.ru_stime,
        'waited_children_cpu_seconds':children.ru_utime+children.ru_stime,'peak_rss_bytes':int(own.ru_maxrss)*1024,
        'log_bytes_each_cap':CAP}
    require(result['resources']['wall_seconds']<30 and own.ru_utime+own.ru_stime+children.ru_utime+children.ru_stime<20
        and int(own.ru_maxrss)*1024<=320*1024**2,'remote observation final resource bound')
    raw=canonical(result)+b'\n';require(len(raw)<=2*1024**2,'remote observation output cap')
    sys.stdout.buffer.write(raw);sys.stdout.buffer.flush();signal.alarm(0)
if __name__=='__main__':main()
'''


def require(value, message):
    if not value:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()


def pin(raw):
    return {'bytes':len(raw), 'sha256':hashlib.sha256(raw).hexdigest()}


def write_new(path, value):
    require(path.parent == ARCHIVE, 'observation must be a direct archive child')
    raw = canonical(value) + b'\n'
    require(len(raw) <= LIMITS['local_receipt_bytes'], 'local observation byte cap')
    for parent in (path.parent, *path.parent.parents):
        require(stat.S_ISDIR(parent.lstat().st_mode), 'symlink or non-directory output ancestor')
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    return pin(raw)


def exchange(command, deadline):
    child = selector = None
    values, error, code = {'stdout':bytearray(), 'stderr':bytearray()}, None, None
    try:
        child = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, start_new_session=True)
        selector = selectors.DefaultSelector()
        for name in values:
            stream = getattr(child, name)
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_READ, name)
        while selector.get_map():
            require(time.monotonic() < deadline, 'SSH observation deadline')
            require(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss <= LIMITS['local_checked_rss_bytes'], 'local observation RSS bound')
            for key, _ in selector.select(.1):
                block = os.read(key.fileobj.fileno(), 65536)
                if not block:
                    selector.unregister(key.fileobj)
                    continue
                room = LIMITS[key.data + '_bytes'] - len(values[key.data])
                values[key.data].extend(block[:room])
                require(len(block) <= room, 'SSH observation output cap')
        code = child.wait(timeout=max(.01, deadline-time.monotonic()))
    except BaseException as failure:
        error = type(failure).__name__ + ': ' + str(failure)[:1024]
    finally:
        if child is not None:
            if child.poll() is None:
                try:
                    os.killpg(child.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                child.wait(timeout=3)
            code = child.returncode
            child.stdout.close()
            child.stderr.close()
        if selector is not None:
            selector.close()
    return code, bytes(values['stdout']), bytes(values['stderr']), error


def main():
    started = time.monotonic()
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('--job-id', required=True)
    parser.add_argument('--stage', required=True, choices=('train', 'evaluate'))
    parser.add_argument('--approval-sha256', required=True)
    parser.add_argument('--source-header-sha256', required=True)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    require(sys.flags.isolated and sys.dont_write_bytecode and sys.platform == 'darwin', 'use isolated uncached Mac Python')
    require(Path(__file__).absolute() == ARCHIVE / 'observe-retention-job-01.py', 'fixed observer source path required')
    require(re.fullmatch(r'[1-9][0-9]{0,19}', args.job_id)
            and all(re.fullmatch(r'[0-9a-f]{64}', value) for value in (args.approval_sha256, args.source_header_sha256)),
            'actual external job ID and immutable approval/source pins required')
    output = args.output
    mark = output.with_name(output.stem + '.started.json')
    require(output.is_absolute() and output == output.resolve(strict=False) and output.parent == ARCHIVE
            and re.fullmatch('retention-' + args.stage + r'-observation-[0-9]{2,3}\.json', output.name)
            and not os.path.lexists(output) and not os.path.lexists(mark), 'fresh stage-specific archive observation required')
    resource.setrlimit(resource.RLIMIT_CPU, (20, 20))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_FSIZE, (LIMITS['local_receipt_bytes'], LIMITS['local_receipt_bytes']))
    def expired(*_):
        raise TimeoutError('local observation60-second wall deadline')
    signal.signal(signal.SIGALRM, expired)
    signal.alarm(60)
    helper = Path(__file__).read_bytes()
    identifiers = {'job_id':args.job_id, 'stage':args.stage, 'approval_sha256':args.approval_sha256,
                   'source_header_sha256':args.source_header_sha256, 'source_commit':SOURCE_COMMIT}
    write_new(mark, {'schema':'peano-hydra-retention-job-observation-start-v1', **identifiers,
        'helper':pin(helper), 'remote_program':pin(PROGRAM.encode()), 'limits':LIMITS, 'read_only':True,
        'automatic_retry':False, 'started_at_utc':datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')})
    remote = shlex.join(['/usr/bin/python3.9', '-I', '-B', '-c', PROGRAM, args.job_id, args.stage,
                         args.approval_sha256, args.source_header_sha256])
    command = ['/usr/bin/ssh', '-T', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15',
        '-o', 'ServerAliveInterval=10', '-o', 'ServerAliveCountMax=2', '-o', 'ForwardAgent=no',
        '-o', 'ClearAllForwardings=yes', '-o', 'StrictHostKeyChecking=yes', '-o', 'UpdateHostKeys=no',
        '-o', 'ControlMaster=no', '-o', 'ControlPath=none', '--', HOST, remote]
    code, stdout, stderr, error = exchange(command, started + LIMITS['ssh_wall_seconds'])
    observation = None
    try:
        require(code == 0 and error is None, 'bounded remote observation did not complete')
        observation = json.loads(stdout)
        require(observation.get('schema') == 'peano-hydra-retention-job-observation-v1'
                and all(observation['binding'].get(key) == value for key, value in identifiers.items())
                and observation.get('read_only') is True and observation.get('quality_claim') is None
                and observation.get('proofs_independently_verified') is False
                and observation.get('scheduler_mutation_performed') is False
                and observation.get('remote_file_writes') is False, 'observation identity/scope differs')
    except (ValueError, KeyError, TypeError) as failure:
        error = error or type(failure).__name__ + ': ' + str(failure)[:1024]
        observation = None
    own, children = resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)
    if own.ru_maxrss > LIMITS['local_checked_rss_bytes'] or time.monotonic()-started >= 60:
        error = error or 'local observation resource envelope reached'
    record = {'schema':'peano-hydra-retention-job-observation-receipt-v1', **identifiers,
        'status':'observed-not-proof-verified' if error is None else 'failed-observation-preserved',
        'helper':pin(helper), 'remote_program':pin(PROGRAM.encode()), 'returncode':code, 'error':error,
        'stdout':pin(stdout), 'stderr':stderr.decode('utf-8', 'replace'),
        'failed_stdout_prefix':stdout[:65536].decode('utf-8', 'replace') if observation is None else None,
        'observation':observation, 'limits':LIMITS, 'read_only':True, 'automatic_retry':False,
        'proofs_independently_verified':False, 'quality_claim':None,
        'resources':{'wall_seconds':time.monotonic()-started, 'own_cpu_seconds':own.ru_utime+own.ru_stime,
                     'waited_child_cpu_seconds':children.ru_utime+children.ru_stime, 'peak_rss_bytes':int(own.ru_maxrss)}}
    receipt = write_new(output, record)
    print(json.dumps({'status':record['status'], 'output':str(output), 'receipt':receipt,
        'job_id':args.job_id, 'stage':args.stage,
        'scheduler_state':None if observation is None else observation['scheduler']['observed_state'],
        'progress':None if observation is None else observation['progress'], 'error':error}, sort_keys=True), flush=True)
    signal.alarm(0)
    return 0 if error is None else 2


if __name__ == '__main__':
    raise SystemExit(main())
