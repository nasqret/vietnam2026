import json,hashlib,signal,os,stat
from pathlib import Path
signal.alarm(15)
expected=json.loads('{"alpha_pattern": {}, "auto_mapping": null, "base_model_name_or_path": "Qwen/Qwen3-1.7B-Base", "bias": "none", "corda_config": null, "eva_config": null, "exclude_modules": null, "fan_in_fan_out": false, "inference_mode": true, "init_lora_weights": true, "layer_replication": null, "layers_pattern": null, "layers_to_transform": null, "loftq_config": {}, "lora_alpha": 32, "lora_bias": false, "lora_dropout": 0.05, "megatron_config": null, "megatron_core": "megatron.core", "modules_to_save": null, "peft_type": "LORA", "qalora_group_size": 16, "r": 16, "rank_pattern": {}, "revision": null, "task_type": "CAUSAL_LM", "trainable_token_indices": null, "use_dora": false, "use_qalora": false, "use_rslora": false}')
base=Path('/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904')
p=base/'bundles/source-data-07/source/output/hydra-implementation-2026-09-04/training-fresh-1.7b-v2-01/adapter/adapter_config.json'
assert os.getuid()==105923 and p.resolve(strict=True)==p
before=p.stat();assert stat.S_ISREG(before.st_mode) and before.st_size<=65536
raw=p.read_bytes();after=p.stat()
assert all(getattr(before,k)==getattr(after,k) for k in ['st_ino','st_dev','st_size','st_mtime_ns','st_ctime_ns'])
assert hashlib.sha256(raw).hexdigest()=='3c02ffee08fb2e7945a6666f3ed92e831c0ee6d6104ed5bb225159108f5eacc4'
config=json.loads(raw);assert set(config)==set(expected)|{'target_modules'}
modules=['q_proj','k_proj','v_proj','o_proj','gate_proj','up_proj','down_proj']
difference=sorted(k for k in expected if config[k]!=expected[k])
report={'schema':'hydra-redacted-config-comparison-v1','exact_saved_config_hash_matches':True,'different_setting_names':difference,'base_name_matches_public_model_id':config['base_model_name_or_path']==expected['base_model_name_or_path'],'base_name_matches_already_authenticated_base_directory':config['base_model_name_or_path']==str(base/'authenticated-bases-01/qwen3-1.7b-base'),'all_non_base_settings_match':all(config[k]==v for k,v in expected.items() if k!='base_model_name_or_path'),'target_modules_match':type(config['target_modules']) is list and len(config['target_modules'])==7 and set(config['target_modules'])==set(modules),'config_values_transferred':False,'config_file_transferred':False,'source_text_transferred':False,'model_calls':0,'gpu_allocations':0}
print(json.dumps(report))
