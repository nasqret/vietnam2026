CONFIG = {'spec': {'config': {'architectures': ['Qwen3ForCausalLM'], 'attention_bias': False, 'attention_dropout': 0.0, 'bos_token_id': 151643, 'eos_token_id': 151643, 'head_dim': 128, 'hidden_act': 'silu', 'hidden_size': 2560, 'initializer_range': 0.02, 'intermediate_size': 9728, 'max_position_embeddings': 32768, 'max_window_layers': 36, 'model_type': 'qwen3', 'num_attention_heads': 32, 'num_hidden_layers': 36, 'num_key_value_heads': 8, 'rms_norm_eps': 1e-06, 'rope_scaling': None, 'rope_theta': 1000000, 'sliding_window': None, 'tie_word_embeddings': True, 'torch_dtype': 'bfloat16', 'transformers_version': '4.51.0', 'use_cache': True, 'use_sliding_window': False, 'vocab_size': 151936}, 'metadata_files': {'config.json': {'bytes': 727, 'sha256': '304b2545a258d35620f1d4bf46940c0471d9baa00715ff8e77f84c2fca5057c1'}, 'generation_config.json': {'bytes': 138, 'sha256': '8c970692323e3ea0e9b8b0a4dca79388d31226e41f83c9fd6014804280ebf6e8'}, 'merges.txt': {'bytes': 1671853, 'sha256': '8831e4f1a044471340f7c0a83d7bd71306a5b867e95fd870f74d0c5308a904d5'}, 'model.safetensors.index.json': {'bytes': 32819, 'sha256': 'd6c42883a895dfef5b0080ed2116a1bcd764f558406b98923d675978a1abf29c'}, 'tokenizer.json': {'bytes': 7031645, 'sha256': 'c0382117ea329cdf097041132f6d735924b697924d6f6fc3945713e96ce87539'}, 'tokenizer_config.json': {'bytes': 9678, 'sha256': '3c04ed3ca964ea2f6b2b5faf0dc4d31aec1cb1e8b4bcf63f402d295046b422b5'}, 'vocab.json': {'bytes': 2776833, 'sha256': 'ca10d7e9fb3ed18575dd1e277a2579c16d108e32f27439684afa0e10b1440910'}}, 'metadata_sha256': 'f6b7758c8181458bfb22984630ce507df826a2a5dc24826141d5436aa72acc85', 'metadata_url': 'https://huggingface.co/api/models/Qwen/Qwen3-4B-Base/revision/906bfd4b4dc7f14ee4320094d8b41684abff8539?blobs=true', 'model_id': 'Qwen/Qwen3-4B-Base', 'revision': '906bfd4b4dc7f14ee4320094d8b41684abff8539', 'weight_files': {'model-00001-of-00003.safetensors': {'bytes': 3957900840, 'sha256': '4c807e2503d68ae373d508689d00a41f4b33f33c2536da97ab81a20caddc1241'}, 'model-00002-of-00003.safetensors': {'bytes': 3987450520, 'sha256': 'f4707585548b2fc75a6b1d732e8465c62040a8699903c32850781beeb9b27826'}, 'model-00003-of-00003.safetensors': {'bytes': 99630640, 'sha256': 'c7b1aa8fb672de2e00423c99876926022e50b18d4f0d140670788510a27f9965'}}}, 'directory': '/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904/base-models/qwen3-4b-base', 'registry_sha256': '3303c4727052557a04bc2e33ea624ff7093703c68ae8fa95b12fb05adbc781c1'}

import hashlib,json,os,re,shutil,signal,sys,time,urllib.request
from pathlib import Path
os.umask(0o077)
signal.alarm(1250)
started=time.monotonic()
spec=CONFIG['spec']
assert spec['model_id']=='Qwen/Qwen3-4B-Base'
assert spec['revision']=='906bfd4b4dc7f14ee4320094d8b41684abff8539'
directory=Path(CONFIG['directory'])
expected=dict(spec['metadata_files']);expected.update(spec['weight_files'])
assert 1<=len(expected)<=16
total=sum(row['bytes'] for row in expected.values())
assert total<9*1024**3
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
  assert 0<descriptor['bytes']<5*1024**3
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
