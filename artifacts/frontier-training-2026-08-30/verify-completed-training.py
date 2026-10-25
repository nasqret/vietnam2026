"""Qualify the completed pilot from exact saved evidence; no model execution."""
import ast
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import statistics
import sys

ARCHIVE = Path(__file__).absolute().parent
SOURCE = ARCHIVE.parents[1] / '_deploy/hydra-frontier-training-execution-20260830'
MANIFEST_SHA = '5795d5a3d70f781f56f81e83c2295c887d0949795924f4208f45d26a3ef89b68'
OBSERVATION_SHA = '3b85a4ceb82e3bc816b795efbe296cd31d114363cd11299cb31d73c3c0828cae'
ARTIFACT_RECEIPT_SHA = '6af7c587bf87b956ad31addaa45617cb6e0fa8db3f74c462b2b80619b3b59ffc'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read_json(path, expected=None):
    raw = path.read_bytes()
    assert len(raw) <= 4*1024**2
    if expected is not None:
        assert sha(raw) == expected, str(path)
    return json.loads(raw)


def main():
    assert sys.flags.isolated and sys.dont_write_bytecode
    output = ARCHIVE / 'completed-training-verification-01.json'
    assert not output.exists()
    request = read_json(SOURCE/'_deploy/hydra-frontier-training-v1/resource-request.json',
        '02e8c485eaee56523b82ce015c0e7478dde19622528c813f9cdf4079eb141feb')
    for name in ('training/peano_policy/training_evidence.py','training/peano_policy/objective.py',
                 'training/peano_policy/manifest.py'):
        assert sha((SOURCE/name).read_bytes()) == request['source_files'][name]['sha256']
    sys.path.insert(0,str(SOURCE))
    from training.peano_policy.training_evidence import (
        read_strict_training_manifest, _validate_gradients, _validate_adapter_update, _validate_runtime,
    )
    raw = (ARCHIVE/'completed-manifest-01.json').read_bytes()
    assert sha(raw) == MANIFEST_SHA
    manifest = read_strict_training_manifest(ARCHIVE/'completed-manifest-01.json')
    observation = read_json(ARCHIVE/'observation-v2-05.json',OBSERVATION_SHA)['observation']
    artifacts = read_json(ARCHIVE/'completed-artifacts-01/receipt.json',ARTIFACT_RECEIPT_SHA)
    account = [row for row in observation['scheduler_identity']['accounting_rows'] if row[0]=='21438102']
    assert len(account)==1 and account[0][2:4]==['COMPLETED','0:0'] and account[0][4]=='01:33:47'
    assert not observation['scheduler_identity']['integrity_issues']
    assert manifest['schema']=='peano-hydra-posttrain-adapter-v2' and manifest['run_id']=='frontier-training-v1'
    assert manifest['job']['job_id']=='21438102' and manifest['model_trained'] is True
    assert manifest['job']['submission']['git_commit']==request['source_commit']=='b08a6b1303d73217f6cc23800ae15e50b17db792'
    assert manifest['deployment']['source_sync']['git_dirty'] is False
    assert manifest['epoch_sha256']=='f64b5f100c9c9bc77049ea627f13e641be83ac72aaa474216682076679a468ad'
    assert manifest['preparation_manifest_sha256']=='729b97bf8418cb227d0ef1b1ba350fde5da537e46da4ad55774d8b4ca73517d3'
    assert manifest['model']==request['model']
    assert manifest['authority']['classical'] is False and manifest['authority']['capabilities']['allowed_theorems']==[]
    metrics = manifest['metrics']
    assert metrics['actual_optimizer_steps']==metrics['expected_optimizer_steps']==1597
    assert metrics['training_rows']==12772 and metrics['development_rows']==2096
    for values in (metrics['train'],metrics['dev']):
        assert all(type(x) in (int,float) and math.isfinite(x) for x in values.values())
        assert values['epoch']==1.0
    runtime = _validate_runtime(manifest['trainer_runtime'])
    gradients = _validate_gradients(manifest['finite_gradient_audit'],1597)
    update = _validate_adapter_update(manifest['adapter_update'],gradients=gradients)
    assert artifacts['status']=='verified-and-logs-retrieved' and len(artifacts['artifact_files'])==10
    assert {name:record['sha256'] for name,record in artifacts['artifact_files'].items()} == {
        **manifest['adapter']['files'],**manifest['tokenizer']['files']}
    log_path=ARCHIVE/'completed-artifacts-01/training.out.log'
    log_raw=log_path.read_bytes()
    assert sha(log_raw)==artifacts['logs']['out']['sha256']
    history=[]
    for line in log_raw.decode().splitlines():
        if line.startswith("{'loss':"):
            row=ast.literal_eval(line)
            assert set(row)=={'loss','learning_rate','epoch'}
            assert all(type(x) in (int,float) and math.isfinite(x) for x in row.values())
            history.append(row)
    assert len(history)==1597
    assert all(x['loss']>=0 and 0<=x['learning_rate']<=0.0001 for x in history)
    assert [x['epoch'] for x in history]==sorted(x['epoch'] for x in history)
    logged_mean=statistics.mean(x['loss'] for x in history)
    assert abs(logged_mean-metrics['train']['train_loss'])<=0.00005
    windows=[]
    for start,end in ((1,25),(26,50),(51,100),(101,200),(201,400),(401,800),(801,1200),(1201,1597)):
        values=[x['loss'] for x in history[start-1:end]]
        windows.append({'first_step':start,'last_step':end,'mean_rounded_logged_loss':statistics.mean(values)})
    result={'schema':'peano-hydra-completed-pilot-verification-v1','status':'completed-training-evidence-verified',
        'verified_at_utc':datetime.now(timezone.utc).isoformat(),'job_id':'21438102','scheduler_state':'COMPLETED',
        'exit_code':'0:0','elapsed_seconds':5627,'reserved_gpu_seconds':7200,'refunds':False,
        'run_id':manifest['run_id'],'source_commit':request['source_commit'],'epoch_sha256':manifest['epoch_sha256'],
        'manifest_sha256':MANIFEST_SHA,'terminal_observation_sha256':OBSERVATION_SHA,
        'artifact_verification_receipt_sha256':ARTIFACT_RECEIPT_SHA,'metrics':metrics,
        'training_log_records':len(history),'mean_rounded_logged_loss':logged_mean,'loss_windows':windows,
        'rounded_zero_loss_records':sum(row['loss']==0 for row in history),
        'finite_gradient_boundaries':gradients['observed_optimizer_boundaries'],
        'changed_parameter_tensors':update['changed_parameter_tensors'],
        'final_finite_parameter_tensors':update['final_finite_parameter_tensors'],
        'adapter_root_sha256':manifest['adapter']['sha256'],'tokenizer_root_sha256':manifest['tokenizer']['sha256'],
        'artifact_files_rehashed':10,'artifact_bytes_rehashed':artifacts['artifact_bytes_hashed'],
        'model_weights_downloaded':False,'model_frameworks_imported':sorted(name for name in ('torch','transformers','peft') if name in sys.modules),
        'native_proofs_replayed_by_this_check':False,'new_training_started':False,'benchmark_evaluation_performed':False,
        'research_claim_eligible':False,'pilot_comparison_accepted':False,
        'interpretation':['Training completed within its reservation and its saved runtime audits are internally valid.',
          'All adapter/tokenizer files were independently rehashed on Helios; this check did not independently reconstruct training or inspect tensor values.',
          'Loss logs are rounded; printed0.0 is not a claim of exact zero loss.',
          'TRAIN and diagnostic DEV losses have different aggregation and exposure; neither establishes proof-search gains or an unseen-test result.',
          'Matched old/new proof-search evaluation and its acceptance criteria remain pending.']}
    assert result['model_frameworks_imported']==[]
    encoded=(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
    with output.open('xb') as stream:
        stream.write(encoded);stream.flush();os.fsync(stream.fileno())
    print(json.dumps({'status':result['status'],'receipt':str(output),'receipt_sha256':sha(encoded),
        'optimizer_steps':1597,'finite_gradient_boundaries':result['finite_gradient_boundaries'],
        'changed_parameter_tensors':result['changed_parameter_tensors'],'loss_windows':windows},sort_keys=True),flush=True)


if __name__=='__main__':
    main()
