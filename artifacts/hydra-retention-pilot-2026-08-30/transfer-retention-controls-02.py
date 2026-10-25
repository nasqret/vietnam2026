#!/usr/bin/env python3
"""Prepare/send five retention controls after actual bootstrap and LOCAL CPU evidence.

Protocol02 preserves failed remote attempt01 and binds its separate successful
local CPU correction. No remote token execution or receipt is fabricated.

No request, approval, CPU result or timestamp is fabricated. Preparation is
local-only and requires an externally pinned completed local finalization.
Sending separately requires the prepared-plan raw SHA and consumes a one-use
marker. Earlier helpers, source, payloads and archives are never modified.
"""
import argparse
import gzip
import hashlib
import io
import os
from pathlib import Path
import resource
import shlex
import signal
import stat
import struct
import sys
import tarfile
import types

ARCHIVE = Path('/Users/bnaskrecki/codex/peano/artifacts/hydra-retention-pilot-2026-08-30')
BOOTSTRAP_SENDER = ARCHIVE / 'transfer-retention-bootstrap-01.py'
BOOTSTRAP_SENDER_SHA = '5c8513abd6e4f9f94321a6fa3a7f45290fee3fba442020e1975921aa5a3694a5'
BOOTSTRAP_RECEIVER_SHA = '40d8391d2d770e509470c81c7a5fe21f0e7ec3a80048e4b70fa9cb0059e6edc2'
RECEIVER = ARCHIVE / 'transfer-retention-controls-remote-02.py'
RECEIVER_SHA = '6485393b288f86af4ab44915968f8c2af5afdde4757e466119bb386cb75e8f96'
FINALIZATION = ARCHIVE / 'finalize-controls-02.json'
ATTEMPT = ARCHIVE / 'controls-transfer-02'
BUNDLE = ATTEMPT / 'controls-02.tar.gz'
OUTPUT_NAMES = frozenset({'prepare-started.json','prepared-plan.json','prepare-result.json',
                         'send-started.json','send-header.json','ssh-process.json','send-result.json'})


def load_bootstrap():
    if BOOTSTRAP_SENDER.parent.resolve() != ARCHIVE or BOOTSTRAP_SENDER.is_symlink():
        raise ValueError('fixed bootstrap helper path required')
    fd = os.open(BOOTSTRAP_SENDER,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    try:
        info = os.fstat(fd)
        if not (stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and 0 < info.st_size <= 65536):
            raise ValueError('bounded single-link inherited helper required')
        raw = os.read(fd,65537)
        if len(raw) != info.st_size or hashlib.sha256(raw).hexdigest() != BOOTSTRAP_SENDER_SHA:
            raise ValueError('reviewed bootstrap sender changed')
        after = os.fstat(fd)
        if (after.st_mtime_ns,after.st_ctime_ns) != (info.st_mtime_ns,info.st_ctime_ns):
            raise ValueError('inherited sender changed during read')
    finally:
        os.close(fd)
    module = types.ModuleType('pinned_retention_bootstrap_sender')
    module.__file__ = str(BOOTSTRAP_SENDER)
    exec(compile(raw,str(BOOTSTRAP_SENDER),'exec'),module.__dict__)
    return module,raw


b, BOOTSTRAP_SENDER_RAW = load_bootstrap()
r = b.r
r.require(r.sha(b.RECEIVER_RAW) == BOOTSTRAP_RECEIVER_SHA,'pinned bootstrap receiver changed')
r._pinned_raw_sha256 = BOOTSTRAP_RECEIVER_SHA
RECEIVER_RAW = b.read_file(RECEIVER,65536)
r.require(r.sha(RECEIVER_RAW) == RECEIVER_SHA,'reviewed controls receiver changed')
c = types.ModuleType('pinned_retention_controls_receiver')
c.__file__, c.r = str(RECEIVER),r
exec(compile(RECEIVER_RAW,str(RECEIVER),'exec'),c.__dict__)
LOCAL_ROOT = Path(r.LOCAL_ROOT)


def new_json(name,record):
    r.require(name in OUTPUT_NAMES,'unapproved local controls receipt path')
    raw = r.canonical(record)+b'\n'
    r.require(len(raw) <= (c.C_MAX_PLAN if name == 'prepared-plan.json' else c.C_MAX_FILE),'local controls receipt byte bound')
    tree = r.Tree(str(ATTEMPT))
    try:
        r.write_stream_file(tree,name,c.c_pin(raw),0o600,io.BytesIO(raw))
        os.fsync(tree.fd)
    finally:
        tree.close()
    return {'path':str(ATTEMPT/name),**c.c_pin(raw)}


def check_helpers():
    r.require(b.read_file(BOOTSTRAP_SENDER,65536) == BOOTSTRAP_SENDER_RAW
              and b.read_file(b.RECEIVER,65536) == b.RECEIVER_RAW
              and b.read_file(RECEIVER,65536) == RECEIVER_RAW,'inherited/current transport source changed')
    return {'sender':c.c_pin(b.read_file(Path(__file__).absolute(),65536)),
            'receiver':c.c_pin(RECEIVER_RAW), 'bootstrap_sender':c.c_pin(BOOTSTRAP_SENDER_RAW),
            'bootstrap_receiver':c.c_pin(b.RECEIVER_RAW)}


def bootstrap_context(final):
    send_raw = b.read_file(b.ATTEMPT/'send-result.json',r.MAX_JSON)
    r.require(final['bootstrap_send_result'] == {'path':str(b.ATTEMPT/'send-result.json'),**c.c_pin(send_raw)},
              'actual successful bootstrap observation changed since finalization')
    sent = r.decode(send_raw)
    r.require(sent.get('status') == 'transferred-and-rehashed' and sent.get('network_contacted') is True
              and sent.get('local_inputs_rechecked') is True and sent.get('job_submitted') is False
              and sent.get('ssh_process',{}).get('reason') == 'exited'
              and sent.get('ssh_process',{}).get('returncode') == 0,
              'actual successful bootstrap transfer is required; no substitute or blocked attempt')
    observed = sent['remote']
    r.require(observed.get('status') == 'transferred-and-rehashed'
              and observed.get('remote_root') == r.REMOTE_ROOT and observed.get('source_commit') == c.C_SOURCE_COMMIT
              and observed.get('remote_receipt') == final['bootstrap_receipt'], 'bootstrap finalization pin differs')
    header_raw = b.read_file(b.ATTEMPT/'send-header.json',r.MAX_HEADER)
    r.require(sent['send_header'] == {'path':str(b.ATTEMPT/'send-header.json'),**c.c_pin(header_raw)},
              'bootstrap actual send header changed')
    header = r.decode(header_raw)
    plan,plan_raw,_,_ = b.context(header['plan_sha256'])
    r.validate_header(header,plan)
    header_sha = r.sha(r.canonical(header))
    r.require(header_sha == sent['send_header_wire_sha256'] == observed['header_sha256'],
              'bootstrap wire header identity differs')
    provenance = observed['source_provenance'].encode('ascii')
    r.require(provenance == (c.C_SOURCE_COMMIT+'\tfalse\t'+observed['transfer_started_at_utc']+'\n').encode()
              and r.sha(provenance) == observed['source_provenance_sha256'],'actual bootstrap provenance differs')
    receipt = r.receipt_record(plan,header,header_sha,observed['transfer_started_at_utc'],provenance,observed['bundle'])
    expected_raw = r.canonical(receipt)+b'\n'
    r.require({'path':r.REMOTE_RECEIPT,**c.c_pin(expected_raw)} == final['bootstrap_receipt'],
              'exact durable bootstrap receipt cannot be reconstructed from actual successful transfer')
    return plan,receipt


def local_context(expected_finalization_sha):
    r.require(type(expected_finalization_sha) is str and r.HEX.fullmatch(expected_finalization_sha),
              'externally pinned actual finalization receipt required')
    final_raw = b.read_file(FINALIZATION,c.C_MAX_FILE)
    r.require(r.sha(final_raw) == expected_finalization_sha,'actual finalization raw receipt changed')
    final = r.decode(final_raw,c.C_MAX_FILE)
    r.require(final.get('schema') == 'peano-hydra-retention-controls-finalization-v2'
              and final.get('status') == 'controls-ready-local-only'
              and final.get('source_commit') == c.C_SOURCE_COMMIT and final.get('frozen_root') == r.LOCAL_ROOT
              and final.get('local_gate',{}).get('returncode') == 0,
              'completed genuine local finalization with the frozen metadata gate required')
    for key in ('source_files_unchanged','bootstrap_files_unchanged','all_input_pins_unchanged',
                'exactly_five_package_files_created','archived_binding_and_local_token_plan_equal'):
        r.require(final.get(key) is True,'local finalization prerequisite missing: '+key)
    for key in ('model_or_tokenizer_loaded','native_proofs_replayed','network_contacted','scheduler_called',
                'gpu_job_submitted','automatic_retry','resume'):
        r.require(final.get(key) is False,'local finalization scope changed: '+key)
    c.c_descriptor(final['bootstrap_receipt'],r.REMOTE_RECEIPT,r.MAX_JSON)
    r.require(final.get('preflight_execution_location') == 'local', 'truthful local tokenizer provenance required')
    c.c_descriptor(final['remote_failed_cpu_process'],c.C_CPU_PROCESS)
    c.c_descriptor(final['remote_failed_cpu_start'],c.C_CPU_START)
    for key,path in (('local_cpu_process',ARCHIVE/'cpu-preflight-local-02/process.json'),
                     ('local_cpu_output',ARCHIVE/'cpu-preflight-local-02/token-preflight.json'),
                     ('runtime_manifest',ARCHIVE/'tokenizer-runtime-02.json')):
        c.c_descriptor(final[key],str(path))
        r.require(final[key] == {'path':str(path),**c.c_pin(b.read_file(path,c.C_MAX_FILE))},
                  'actual local tokenizer evidence changed: '+key)
    local_process = r.decode(b.read_file(ARCHIVE/'cpu-preflight-local-02/process.json',c.C_MAX_FILE))
    r.require(local_process.get('schema') == 'peano-hydra-retention-local-tokenizer-preflight-process-v2'
              and local_process.get('status') == 'passed' and local_process.get('returncode') == 0
              and local_process.get('error') is None, 'genuine successful local CPU process required')
    bootstrap_plan,bootstrap = bootstrap_context(final)
    files = final.get('control_files')
    r.require(type(files) is dict and set(files) == set(c.C_FILES),'local finalization must declare exactly five controls')
    controls,payloads = {},{}
    tree = r.Tree(r.LOCAL_ROOT)
    try:
        for name in c.C_FILES:
            r.descriptor(files[name],mode=False,maximum=c.C_MAX_FILE)
            raw = b.read_file(LOCAL_ROOT/name,c.C_MAX_FILE)
            r.decode(raw,c.C_MAX_FILE)
            actual,_,info = tree.fingerprint(name)
            r.require(actual == files[name] == c.c_pin(raw) and stat.S_IMODE(info[2]) == 0o600,
                      'actual control file byte/mode pin changed: '+name)
            controls[name],payloads[name] = {**actual,'mode':'0600'},raw
        r.require(sum(len(value) for value in payloads.values()) <= c.C_MAX_TOTAL,'five controls exceed total byte bound')
    finally:
        tree.close()
    request = r.decode(payloads[c.C_REQUEST],c.C_MAX_FILE)
    bound = {'approval_sha256':files[c.C_APPROVAL]['sha256'], 'resource_request_sha256':files[c.C_REQUEST]['sha256'],
        'source_commit':c.C_SOURCE_COMMIT,'source_files_sha256':final['source_files_sha256'],
        'payloads_sha256':final['payloads_sha256'],'synced_at':bootstrap['transfer_started_at_utc'],
        'job_script_sha256':{stage:request['source_files']['slurm/peano_hydra_retention_'+stage+'.sbatch']['sha256']
                            for stage in ('train','evaluate')}}
    r.require(final['resource_request_sha256'] == bound['resource_request_sha256']
              and final['approval_sha256'] == bound['approval_sha256'],'finalized approval/request raw pins changed')
    context = {'final':final,'final_raw':final_raw,'bootstrap_plan':bootstrap_plan,'bootstrap':bootstrap,
               'controls':controls,'payloads':payloads,'execution_identity':bound,'helpers':check_helpers()}
    c.c_check_incoming({'control_files':controls,'execution_identity':bound},bootstrap,payloads)
    r.require(c.c_pin(payloads[c.C_TOKEN]) == {k:final['local_cpu_output'][k] for k in ('bytes','sha256')},
              'local token preflight is not the pinned actual local CPU output')
    check_local_inputs(context)
    return context


def check_local_inputs(context):
    state = b.git_state(c.C_SOURCE_COMMIT)
    selected = {**context['bootstrap_plan']['selected_files'],**context['controls']}
    tree = r.Tree(r.LOCAL_ROOT)
    try:
        total = 0
        for name,item in selected.items():
            actual,_,info = tree.fingerprint(name)
            total += actual['bytes']
            r.require(total <= r.MAX_TOTAL and actual == {k:item[k] for k in ('bytes','sha256')}
                      and stat.S_IMODE(info[2]) == int(item['mode'],8),'local source/bootstrap/control changed: '+name)
        package = r.Tree(str(LOCAL_ROOT/r.PACKAGE))
        try:
            r.require({r.PACKAGE+'/'+name for name in package.files()}
                      == set(context['bootstrap_plan']['bootstrap_files']) | set(c.C_FILES),'local finalized package is not closed')
        finally:
            package.close()
        tree.anchored()
    finally:
        tree.close()
    r.require(b.git_state(c.C_SOURCE_COMMIT) == state,'actual frozen Git identity changed through control checks')
    check_helpers()
    return state


def plan_record(context,bundle):
    final = context['final']
    return {'schema':'peano-hydra-retention-controls-transfer-plan-v2','status':'prepared-local-only',
        'source_root':r.LOCAL_ROOT,'source_commit':c.C_SOURCE_COMMIT,'destination_host':r.HOST,'destination_directory':r.REMOTE_ROOT,
        'bootstrap_receipt':final['bootstrap_receipt'],
        'remote_failed_cpu_process':final['remote_failed_cpu_process'],'remote_failed_cpu_start':final['remote_failed_cpu_start'],
        'local_cpu_process':final['local_cpu_process'],'local_cpu_output':final['local_cpu_output'],
        'runtime_manifest':final['runtime_manifest'],'control_files':context['controls'],
        'control_files_sha256':r.sha(r.canonical(context['controls'])),
        'control_bytes':sum(item['bytes'] for item in context['controls'].values()),
        'bundle':{'path':str(BUNDLE),**bundle},'execution_identity':context['execution_identity'],
        'source_header_sha256':r.sha(r.canonical(context['execution_identity'])),
        'finalization_receipt':{'path':str(FINALIZATION),**c.c_pin(context['final_raw'])},
        'helpers':context['helpers'],'limits':c.C_LIMITS,'job_submission_performed':False,
        'model_loaded':False,'native_work_performed':False,'automatic_retry':False,'resume':False}


def construct_bundle(context):
    tree = r.Tree(str(ATTEMPT))
    try:
        fd = os.open(BUNDLE.name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=tree.fd)
        with os.fdopen(fd,'wb') as stream:
            with gzip.GzipFile(filename='',fileobj=stream,mode='wb',compresslevel=6,mtime=0) as compressed:
                with tarfile.open(fileobj=compressed,mode='w|',format=tarfile.USTAR_FORMAT) as tar:
                    for name in c.C_FILES:
                        raw = context['payloads'][name]
                        info = tarfile.TarInfo(name)
                        info.size,info.mode = len(raw),0o600
                        info.uid = info.gid = info.mtime = 0
                        info.uname = info.gname = ''
                        tar.addfile(info,io.BytesIO(raw))
                        r.require(stream.tell() <= c.C_MAX_BUNDLE,'compressed controls exceed cap')
            stream.flush();os.fsync(stream.fileno())
            r.require(0 < stream.tell() <= c.C_MAX_BUNDLE,'compressed controls final byte cap')
        bundle,_,_ = tree.fingerprint(BUNDLE.name)
        tree.anchored();os.fsync(tree.fd)
        return bundle
    finally:
        tree.close()


def open_bundle(bundle):
    tree = r.Tree(str(ATTEMPT))
    stream = None
    try:
        fd,before = tree.open_file(BUNDLE.name)
        r.require(0 < before[4] == bundle['bytes'] <= c.C_MAX_BUNDLE,'prepared controls tar size changed')
        stream = os.fdopen(fd,'rb')
        hasher = hashlib.sha256()
        while True:
            block = stream.read(65536)
            if not block:break
            hasher.update(block)
        r.require(hasher.hexdigest() == bundle['sha256'] and r.identity(os.fstat(stream.fileno())) == before,
                  'prepared controls tar raw bytes changed')
        check,after = tree.open_file(BUNDLE.name);os.close(check)
        r.require(after == before,'controls tar path changed')
        tree.anchored();stream.seek(0)
        result,stream = stream,None
        return result,before
    finally:
        if stream is not None:stream.close()
        tree.close()


def prepare(expected_finalization_sha):
    parent = r.directory(str(ARCHIVE))
    try:
        os.mkdir(ATTEMPT.name,0o700,dir_fd=parent);os.fsync(parent)
    finally:
        os.close(parent)
    new_json('prepare-started.json',{'started_at_utc':r.utc(),'finalization_receipt_sha256':expected_finalization_sha,
                                   'network_contacted':False,'automatic_retry':False})
    result = {'schema':'peano-hydra-retention-controls-transfer-prepare-result-v2','network_contacted':False,
              'job_submitted':False,'automatic_retry':False,'partial_outputs_preserved':True}
    try:
        context = local_context(expected_finalization_sha)
        bundle = construct_bundle(context)
        plan = plan_record(context,bundle)
        raw = r.canonical(plan)+b'\n'
        c.c_validate_plan(raw,r.sha(raw))
        stream,before = open_bundle(bundle)
        try:
            def consume(name,item,expanded):
                r.require(r.exact(expanded,item['bytes']) == context['payloads'][name],'prepared control tar payload differs')
            tar_result = r.consume_tar(stream,plan['control_files'],consume,bundle)
            r.require(stream.read(1) == b'' and r.identity(os.fstat(stream.fileno())) == before,'prepared tar framing/identity changed')
        finally:
            stream.close()
        final_context = local_context(expected_finalization_sha)
        r.require(plan_record(final_context,bundle) == plan,'source/control/finalization/helper changed during preparation')
        result.update(status='prepared-local-only',prepared_plan=new_json('prepared-plan.json',plan),tar_validation=tar_result)
    except BaseException as error:
        result.update(status='failed-local-only',error=type(error).__name__+': '+str(error)[:2048])
    receipt = new_json('prepare-result.json',result)
    print(r.canonical({'status':result['status'],'receipt':receipt,'prepared_plan':result.get('prepared_plan'),
                       'error':result.get('error')}).decode(),flush=True)
    return 0 if result['status'] == 'prepared-local-only' else 2


def remote_program():
    # Both source strings are raw-pinned before compilation. No received file
    # is imported or written; the original receiver main is never invoked.
    return ('import types\n'
            'r = types.ModuleType("pinned_bootstrap_primitives")\n'
            'exec(compile('+repr(b.RECEIVER_RAW)+', "<raw-pinned-bootstrap-receiver>", "exec"), r.__dict__)\n'
            'r._pinned_raw_sha256 = '+repr(BOOTSTRAP_RECEIVER_SHA)+'\n'
            + RECEIVER_RAW.decode('utf-8') + '\ncontrols_main()\n')


def send(expected_plan_sha):
    r.require(type(expected_plan_sha) is str and r.HEX.fullmatch(expected_plan_sha),'external prepared controls-plan raw SHA required')
    new_json('send-started.json',{'started_at_utc':r.utc(),'prepared_plan_sha256':expected_plan_sha,
                                'network_contacted':False,'automatic_retry':False})
    result = {'schema':'peano-hydra-retention-controls-transfer-send-result-v2','network_contacted':False,
              'job_submitted':False,'automatic_retry':False,'partial_outputs_preserved':True}
    try:
        plan_raw = b.read_file(ATTEMPT/'prepared-plan.json',c.C_MAX_PLAN)
        plan = c.c_validate_plan(plan_raw,expected_plan_sha)
        ready = r.decode(b.read_file(ATTEMPT/'prepare-result.json',r.MAX_JSON))
        r.require(ready.get('status') == 'prepared-local-only'
                  and ready.get('prepared_plan') == {'path':str(ATTEMPT/'prepared-plan.json'),**c.c_pin(plan_raw)},
                  'successful exact controls preparation missing')
        context = local_context(plan['finalization_receipt']['sha256'])
        bundle = {k:plan['bundle'][k] for k in ('bytes','sha256')}
        r.require(plan_record(context,bundle) == plan,'prepared controls/helper/source binding changed')
        stream,before = open_bundle(bundle)
        try:
            header = {'schema':'peano-hydra-retention-controls-transfer-header-v2','plan_bytes':len(plan_raw),
                'plan_sha256':expected_plan_sha,'source_header_sha256':plan['source_header_sha256'],
                'source_commit':c.C_SOURCE_COMMIT,'sender_sha256':plan['helpers']['sender']['sha256'],
                'receiver_sha256':RECEIVER_SHA,'bootstrap_receiver_sha256':BOOTSTRAP_RECEIVER_SHA,
                'started_at_utc':r.utc(),'limits':c.C_LIMITS}
            c.c_validate_header(header,plan)
            header_raw = r.canonical(header)
            r.require(len(header_raw) <= r.MAX_HEADER,'controls header byte cap')
            header_artifact = new_json('send-header.json',header)
            header_sha = r.sha(header_raw)
            prefix = c.C_MAGIC+struct.pack('>Q',len(header_raw))+header_raw+plan_raw
            program = remote_program()
            remote = shlex.join(['/usr/bin/env','-i','PATH=/usr/bin:/bin','/usr/bin/python3.9','-I','-B','-c',program,header_sha])
            r.require(len(remote.encode()) <= 120000,'bounded remote program command size')
            command = ['/usr/bin/ssh','-T','-o','BatchMode=yes','-o','ConnectTimeout=15',
                       '-o','ServerAliveInterval=10','-o','ServerAliveCountMax=2','-o','ForwardAgent=no',
                       '-o','ClearAllForwardings=yes','-o','StrictHostKeyChecking=yes','-o','UpdateHostKeys=no',
                       '-o','ControlMaster=no','-o','ControlPath=none','--',r.HOST,remote]
            result.update(network_contacted=True,send_header=header_artifact,send_header_wire_sha256=header_sha,
                          receiver_program_sha256=r.sha(program.encode()))
            process = b.bounded(command,c.C_LIMITS['ssh_wall_seconds'],prefix=prefix,bundle_stream=stream,bundle=bundle)
            new_json('ssh-process.json',process);result['ssh_process']=process
            r.require(r.identity(os.fstat(stream.fileno())) == before,'control tar changed during transfer')
        finally:
            stream.close()
        current = local_context(plan['finalization_receipt']['sha256'])
        r.require(plan_record(current,bundle) == plan,'local source/controls changed through transfer')
        stream,_ = open_bundle(bundle);stream.close()
        result['local_inputs_rechecked']=True
        r.require(process['reason'] == 'exited' and process['returncode'] == 0,'control transfer did not complete; no retry')
        observed = r.decode(process['stdout'].encode())
        r.require(observed.get('schema') == 'peano-hydra-retention-controls-transfer-remote-result-v2'
                  and observed.get('status') == 'installed-and-validated'
                  and observed.get('remote_root') == r.REMOTE_ROOT and observed.get('source_commit') == c.C_SOURCE_COMMIT
                  and observed.get('plan_sha256') == expected_plan_sha and observed.get('header_sha256') == header_sha
                  and observed.get('source_header_sha256') == plan['source_header_sha256']
                  and observed.get('execution_identity') == plan['execution_identity']
                  and observed.get('bootstrap_receipt') == plan['bootstrap_receipt']
                  and observed.get('remote_failed_cpu_process') == plan['remote_failed_cpu_process']
                  and observed.get('remote_failed_cpu_start') == plan['remote_failed_cpu_start']
                  and observed.get('local_cpu_process') == plan['local_cpu_process']
                  and observed.get('local_cpu_output') == plan['local_cpu_output']
                  and observed.get('runtime_manifest') == plan['runtime_manifest']
                  and observed.get('control_files_sha256') == plan['control_files_sha256']
                  and observed.get('control_bytes') == plan['control_bytes'] and observed.get('control_files_written') == 5
                  and observed.get('bundle') == ready['tar_validation'],'remote controls receipt binding differs')
        for key in ('all_retained_and_new_bytes_rechecked','genuine_frozen_metadata_and_identity_validated',
                    'exact_inventory_checked','token_preflight_matches_pinned_local_output','failed_remote_cpu_attempt_preserved'):
            r.require(observed.get(key) is True,'remote metadata gate incomplete: '+key)
        for key in ('job_submission_performed','scheduler_called','model_loaded','native_work_performed','automatic_retry','local_tokenizer_executed_remotely'):
            r.require(observed.get(key) is False,'unexpected remote work: '+key)
        durable = observed['receipt_record']
        durable_raw = r.canonical(durable)+b'\n'
        r.require(len(durable_raw) <= c.C_MAX_FILE
                  and observed['remote_receipt'] == {'path':c.C_RECEIPT,**c.c_pin(durable_raw)}
                  and durable.get('schema') == 'peano-hydra-retention-controls-transfer-receipt-v2'
                  and durable.get('status') == 'installed-and-validated'
                  and durable.get('execution_identity') == plan['execution_identity']
                  and durable.get('control_files') == plan['control_files']
                  and durable.get('plan_sha256') == expected_plan_sha
                  and durable.get('header_sha256') == header_sha
                  and durable.get('limits') == c.C_LIMITS
                  and 0 <= observed['cpu_seconds'] < 45 and 0 <= observed['wall_seconds'] < 55
                  and 0 < observed['peak_rss_bytes'] <= 320 * 1024**2,
                  'durable controls receipt or resource bounds changed')
        result.update(status='installed-and-validated',remote=observed)
    except BaseException as error:
        result.update(status='failed-no-automatic-retry',error=type(error).__name__+': '+str(error)[:2048])
    result['finished_at_utc']=r.utc()
    receipt=new_json('send-result.json',result)
    print(r.canonical({'status':result['status'],'receipt':receipt,'network_contacted':result['network_contacted'],
                       'error':result.get('error')}).decode(),flush=True)
    return 0 if result['status'] == 'installed-and-validated' else 2


def main():
    parser=argparse.ArgumentParser(description=__doc__,allow_abbrev=False)
    modes=parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--prepare',action='store_true');modes.add_argument('--send',action='store_true')
    parser.add_argument('--expected-finalization-receipt-sha256');parser.add_argument('--expected-plan-sha256')
    args=parser.parse_args()
    r.require(sys.flags.isolated and sys.dont_write_bytecode,'invoke with -I -B')
    r.require(Path(__file__).absolute() == ARCHIVE/'transfer-retention-controls-02.py','fixed controls sender archive path required')
    r.require((args.prepare and args.expected_finalization_receipt_sha256 is not None and args.expected_plan_sha256 is None)
              or (args.send and args.expected_plan_sha256 is not None and args.expected_finalization_receipt_sha256 is None),
              'preparation and send require only their actual external raw pin')
    os.umask(0o077)
    resource.setrlimit(resource.RLIMIT_CPU,(60,60));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    bound=c.C_MAX_BUNDLE if args.prepare else c.C_MAX_FILE
    resource.setrlimit(resource.RLIMIT_FSIZE,(bound,bound))
    def expired(_signum,_frame):raise TimeoutError('local five-control transfer90-second wall deadline')
    signal.signal(signal.SIGALRM,expired);signal.alarm(90)
    try:
        return prepare(args.expected_finalization_receipt_sha256) if args.prepare else send(args.expected_plan_sha256)
    finally:
        signal.alarm(0)


if __name__ == '__main__':
    raise SystemExit(main())
