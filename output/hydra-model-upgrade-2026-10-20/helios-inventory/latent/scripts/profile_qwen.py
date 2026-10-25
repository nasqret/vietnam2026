"""Actual 1.7B correctness/memory/timing gate. SLURM only."""
import argparse, gc, json, os, time
from pathlib import Path
import torch
from latentproof.qwen_train import make_model, model_inventory, atomic_json

p=argparse.ArgumentParser(); p.add_argument('--model',required=True); p.add_argument('--out',required=True); a=p.parse_args()
assert os.environ.get('SLURM_JOB_ID') and torch.cuda.is_available()
torch.set_num_threads(4)
cfg=json.loads(Path('configs/campaign3.json').read_text())
out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
receipts=[]
for arm in cfg['arms']:
 torch.manual_seed(11);torch.cuda.manual_seed_all(11)
 model=make_model(cfg,a.model,arm);model.eval()
 ids=torch.arange(64,device='cuda').unsqueeze(0)+100
 if arm=='qwen_vanilla':
  with torch.inference_mode(),torch.autocast('cuda',dtype=torch.bfloat16):
   upstream=model.base_model(input_ids=ids,use_cache=False,logits_to_keep=4).logits
   actual=model.fixed_forward(input_ids=ids,recurrence=1,logits_to_keep=4)['logits']
  maximum=float((upstream.float()-actual.float()).abs().max())
  torch.testing.assert_close(actual,upstream,rtol=0,atol=0)
 else: maximum=None
 del ids
 model.train();torch.cuda.reset_peak_memory_stats()
 ids=(torch.arange(1024,device='cuda').unsqueeze(0)%1000)+100
 labels=ids.clone();labels[:,:-16]=-100
 mask=torch.ones_like(ids)
 trainable=[v for v in model.parameters() if v.requires_grad]
 optimizer=torch.optim.AdamW(trainable,lr=1e-5)
 times=[];losses=[]
 for repeat in range(2):
  optimizer.zero_grad(set_to_none=True);torch.cuda.synchronize();start=time.monotonic()
  with torch.autocast('cuda',dtype=torch.bfloat16):
   result=model.supervised_loss(ids,labels,attention_mask=mask,mode='adaptive' if arm=='qwen_adaptive' else 'fixed',recurrence=1 if arm=='qwen_vanilla' else 4)
  assert bool(torch.isfinite(result['loss']))
  result['loss'].backward()
  norm=torch.nn.utils.clip_grad_norm_(trainable,1.,error_if_nonfinite=True)
  assert float(norm)>0
  optimizer.step();torch.cuda.synchronize();times.append(time.monotonic()-start);losses.append(float(result['loss']))
 receipt={'arm':arm,'job_id':os.environ['SLURM_JOB_ID'],'device':torch.cuda.get_device_name(0),'sequence_length':1024,'micro_batch':1,'supervised_tokens':16,'optimizer_step_seconds':times,'losses':losses,'upstream_r1_max_abs_difference':maximum,'trainable_parameters':sum(v.numel() for v in trainable),'peak_allocated_bytes':torch.cuda.max_memory_allocated(),'peak_reserved_bytes':torch.cuda.max_memory_reserved(),'block_calls':result['block_calls']}
 receipts.append(receipt);atomic_json(out/'profile.json',receipts);print(json.dumps(receipt),flush=True)
 del result,model,optimizer,trainable,ids,labels,mask;gc.collect();torch.cuda.empty_cache()
atomic_json(out/'model-inventory.json',model_inventory(a.model))
