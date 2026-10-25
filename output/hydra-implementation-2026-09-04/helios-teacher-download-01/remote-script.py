CONFIG = {'spec': {'config': {'architectures': ['LlamaForCausalLM'], 'attention_bias': False, 'attention_dropout': 0.0, 'bos_token_id': 100000, 'eos_token_id': 100001, 'head_dim': 128, 'hidden_act': 'silu', 'hidden_size': 4096, 'initializer_range': 0.02, 'intermediate_size': 11008, 'max_position_embeddings': 65536, 'mlp_bias': False, 'model_type': 'llama', 'num_attention_heads': 32, 'num_hidden_layers': 30, 'num_key_value_heads': 32, 'pretraining_tp': 1, 'rms_norm_eps': 1e-06, 'rope_scaling': {'beta_fast': 32, 'beta_slow': 1, 'factor': 16, 'mscale': True, 'original_max_position_embeddings': 4096, 'type': 'yarn'}, 'rope_theta': 10000, 'tie_word_embeddings': False, 'torch_dtype': 'bfloat16', 'transformers_version': '4.46.3', 'use_cache': True, 'vocab_size': 102400}, 'declared_parameter_count': 6910365696, 'dependencies': {'accelerate': '1.8.1', 'huggingface-hub': '0.33.4', 'peft': '0.16.0', 'safetensors': '0.5.3', 'tokenizers': '0.21.2', 'torch': '2.9.1+cu129', 'transformers': '4.53.3'}, 'inference_backend': {'attention': 'sdpa', 'device': 'cuda:0', 'dtype': 'bfloat16', 'framework': 'torch', 'local_mlx_supported': False, 'platform': 'linux-aarch64', 'quantization': 'none'}, 'metadata_files': {'LICENSE': {'bytes': 1064, 'sha256': '1c8f573e830ca9b3ebfeb7ace1823146e22b66f99ee223840e7637c9e745e1c7'}, 'README.md': {'bytes': 9957, 'sha256': '9b401b7ddeba804aa7595c4a4bc44ebc3b5865e8f76ac47b3938a30624ed1e21'}, 'config.json': {'bytes': 833, 'sha256': 'b65e97cd6b17aed8f52a8add5b06bc3802d6ae7fc070065974f4ad5247712e6e'}, 'model.safetensors.index.json': {'bytes': 22736, 'sha256': '5a49365b5047e42c403c1ea996a95d7225f923a6f49d639608e6bd685294f04d'}, 'tokenizer.json': {'bytes': 4610628, 'sha256': '091b9dadb9845f0e8386c38bdb87e98db8adc7b0aacf36cb9257c00d0a668714'}, 'tokenizer_config.json': {'bytes': 3883, 'sha256': '7f1394a1791473968ebf8ca25adc2c7f4678388a85c4aff1d4cffca881828734'}}, 'model_id': 'deepseek-ai/DeepSeek-Prover-V2-7B', 'model_key': 'deepseek-prover-v2-7b-teacher', 'planner_contract': 'hydra-greedy-json-plan-decoder-v1', 'revision': 'a8d9e14432b2e8dd9df2a4d4e70f1ba9bc8d9b7b', 'schema': 'hydra-experimental-teacher-registry-v1', 'teacher_adapters_allowed': False, 'teacher_prompt_contract': 'hydra-deepseek-native-json-teacher-input-v1', 'tokenizer_class': 'LlamaTokenizerFast', 'weight_files': {'model-00001-of-000002.safetensors': {'bytes': 8596557586, 'sha256': 'f7eebe5f578ccfa90eea70b00c164adff6df2bdec511b9939c101234c3e3ae65'}, 'model-00002-of-000002.safetensors': {'bytes': 5224205544, 'sha256': '7dd518c7ca44e82a7bda20f1959bd131b89f721c70fb3bc2e9ac0b53ad2c4ce9'}}, 'weights_downloaded_by_preparation': False}, 'directory': '/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904/base-models/deepseek-prover-v2-7b-teacher', 'registry_sha256': 'a56dad7ac6368964c039c9ddabab5ac6174939f9684ae23bf6872080cf38c105'}

import hashlib,json,os,re,shutil,signal,sys,time,urllib.request
from pathlib import Path
os.umask(0o077)
signal.alarm(1250)
started=time.monotonic()
spec=CONFIG['spec']
assert spec['model_id']=='deepseek-ai/DeepSeek-Prover-V2-7B'
assert spec['revision']=='a8d9e14432b2e8dd9df2a4d4e70f1ba9bc8d9b7b'
directory=Path(CONFIG['directory'])
expected=dict(spec['metadata_files']);expected.update(spec['weight_files'])
assert 1<=len(expected)<=16
total=sum(row['bytes'] for row in expected.values())
assert total<14*1024**3
project=Path('/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training')
assert shutil.disk_usage(str(project)).free>total+1024**3
directory.mkdir(parents=True,exist_ok=False)
record={'schema':'hydra-base-download-v1','status':'running','registry_sha256':CONFIG['registry_sha256'],
 'model_id':spec['model_id'],'revision':spec['revision'],'directory':str(directory),
 'expected_bytes':total,'max_wall_seconds':1200,'automatic_retry':False,'resumption':False,
 'gpu_allocations':0,'files':{}}
def save():
 (directory/'download-receipt.json').write_text(json.dumps(record,indent=2)+'\n')
def event(value):
 print(json.dumps(value),flush=True)
save()
try:
 for name,descriptor in sorted(expected.items()):
  assert re.fullmatch(r'[A-Za-z0-9_.-]+',name) and name not in ('.','..')
  assert 0<descriptor['bytes']<9*1024**3
  assert re.fullmatch(r'[0-9a-f]{64}',descriptor['sha256'])
  if time.monotonic()-started>=1200:raise TimeoutError('Download wall ceiling reached')
  url='https://huggingface.co/'+spec['model_id']+'/resolve/'+spec['revision']+'/'+name+'?download=true'
  partial=directory/(name+'.partial')
  digest=hashlib.sha256();observed=0;notice=256*1024**2
  event({'file':name,'status':'starting','expected_bytes':descriptor['bytes']})
  with urllib.request.urlopen(url,timeout=30) as response, partial.open('xb') as destination:
   assert response.status==200
   while True:
    if time.monotonic()-started>=1200:raise TimeoutError('Download wall ceiling reached')
    block=response.read(1024**2)
    if not block:break
    observed+=len(block)
    if observed>descriptor['bytes']:raise ValueError('Response exceeds exact pinned size')
    digest.update(block);destination.write(block)
    if observed>=notice:
     event({'file':name,'status':'downloading','bytes':observed})
     notice+=256*1024**2
   destination.flush();os.fsync(destination.fileno())
  actual={'bytes':observed,'sha256':digest.hexdigest()}
  assert actual==descriptor,'Base file hash/size mismatch: '+name
  partial.rename(directory/name)
  record['files'][name]=actual;save()
  event({'file':name,'status':'verified','bytes':observed})
 record['status']='complete'
except BaseException as error:
 record.update(status='failed',error=type(error).__name__+': '+str(error)[:500])
 raise
finally:
 record['elapsed_seconds']=time.monotonic()-started
 save();event(record)
