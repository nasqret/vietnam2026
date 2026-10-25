CONFIG = {'spec': {'config': {'architectures': ['Qwen3ForCausalLM'], 'attention_bias': False, 'attention_dropout': 0.0, 'bos_token_id': 151643, 'eos_token_id': 151643, 'head_dim': 128, 'hidden_act': 'silu', 'hidden_size': 4096, 'initializer_range': 0.02, 'intermediate_size': 12288, 'max_position_embeddings': 32768, 'max_window_layers': 36, 'model_type': 'qwen3', 'num_attention_heads': 32, 'num_hidden_layers': 36, 'num_key_value_heads': 8, 'rms_norm_eps': 1e-06, 'rope_scaling': None, 'rope_theta': 1000000, 'sliding_window': None, 'tie_word_embeddings': False, 'torch_dtype': 'bfloat16', 'transformers_version': '4.51.0', 'use_cache': True, 'use_sliding_window': False, 'vocab_size': 151936}, 'metadata_files': {'config.json': {'bytes': 729, 'sha256': '3bd01d7ad7a2e203ecbbe84e24087a51c6d2a108ee4bcc42d0016bf49564983a'}, 'generation_config.json': {'bytes': 138, 'sha256': '8c970692323e3ea0e9b8b0a4dca79388d31226e41f83c9fd6014804280ebf6e8'}, 'merges.txt': {'bytes': 1671853, 'sha256': '8831e4f1a044471340f7c0a83d7bd71306a5b867e95fd870f74d0c5308a904d5'}, 'model.safetensors.index.json': {'bytes': 32878, 'sha256': 'cd39d5e44c5aadfd1954b598883aea1c4a98822a2f7723d214ef2278b7fec2e4'}, 'tokenizer.json': {'bytes': 7031645, 'sha256': 'c0382117ea329cdf097041132f6d735924b697924d6f6fc3945713e96ce87539'}, 'tokenizer_config.json': {'bytes': 9678, 'sha256': '3c04ed3ca964ea2f6b2b5faf0dc4d31aec1cb1e8b4bcf63f402d295046b422b5'}, 'vocab.json': {'bytes': 2776833, 'sha256': 'ca10d7e9fb3ed18575dd1e277a2579c16d108e32f27439684afa0e10b1440910'}}, 'metadata_sha256': '2c9dfc3572d3cc66802172833ce87bbc34897b4112847616640e51aa93f60f98', 'metadata_url': 'https://huggingface.co/api/models/Qwen/Qwen3-8B-Base/revision/49e3418fbbbca6ecbdf9608b4d22e5a407081db4?blobs=true', 'model_id': 'Qwen/Qwen3-8B-Base', 'revision': '49e3418fbbbca6ecbdf9608b4d22e5a407081db4', 'weight_files': {'model-00001-of-00005.safetensors': {'bytes': 3996250744, 'sha256': '9983f1b9ef2f60e7c3730d9bc11ada914e6ec630639b5b020a89bd158cd0446b'}, 'model-00002-of-00005.safetensors': {'bytes': 3993160032, 'sha256': '9aa12339835bf7a093d3d0b0a0d2d77f8538301cfc7f8e7ec7a585858ebf7a1f'}, 'model-00003-of-00005.safetensors': {'bytes': 3959604768, 'sha256': 'c7dd5a191c8da555def0714550375b3c0117751add408fcdda0c2a79ac0186bc'}, 'model-00004-of-00005.safetensors': {'bytes': 3187841392, 'sha256': 'ad8b708792105133e03fe19e2d56c89c709f677f01285f8b3ede8947d59fd9fe'}, 'model-00005-of-00005.safetensors': {'bytes': 1244659840, 'sha256': 'fbf24915d47ea030bb68ab0b9488f4515a907185baa6dc26837c9c3f2326a550'}}}, 'directory': '/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904/base-models/qwen3-8b-base', 'registry_sha256': '3303c4727052557a04bc2e33ea624ff7093703c68ae8fa95b12fb05adbc781c1'}

import hashlib,json,os,re,shutil,signal,sys,time,urllib.request
from pathlib import Path
os.umask(0o077)
signal.alarm(1250)
started=time.monotonic()
spec=CONFIG['spec']
assert spec['model_id']=='Qwen/Qwen3-8B-Base'
assert spec['revision']=='49e3418fbbbca6ecbdf9608b4d22e5a407081db4'
directory=Path(CONFIG['directory'])
expected=dict(spec['metadata_files']);expected.update(spec['weight_files'])
assert 1<=len(expected)<=16
total=sum(row['bytes'] for row in expected.values())
assert total<17*1024**3
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
