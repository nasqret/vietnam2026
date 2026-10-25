"""Inference-only paired screen. Run once per arm in the owned Slurm job."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import signal
import sys
import time
import traceback


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def checked(path, expected):
    path = Path(path)
    require(path.is_file() and not path.is_symlink(), f'Missing/linked input: {path}')
    require(digest(path) == expected, f'Input hash mismatch: {path}')
    return path


def save(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--study', required=True)
    parser.add_argument('--study-sha256', required=True)
    parser.add_argument('--arm', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    study_path = checked(args.study, args.study_sha256)
    study = json.loads(study_path.read_text())
    root = study_path.parent
    arm = study['arms'][args.arm]
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    receipt = {'schema': 'hydra-upgrade-arm-v1', 'arm': args.arm,
               'started_utc': datetime.now(timezone.utc).isoformat(),
               'study_sha256': args.study_sha256, 'job_id': os.environ.get('SLURM_JOB_ID'),
               'training': False, 'automatic_retry': False, 'status': 'starting', 'cases': []}
    try:
        require(sys.platform == 'linux' and os.environ.get('SLURM_JOB_ID'), 'Owned Slurm job required')
        require(os.environ.get('HF_HUB_OFFLINE') == '1' and os.environ.get('TRANSFORMERS_OFFLINE') == '1', 'Offline mode required')
        require(int(os.environ.get('SLURM_CPUS_PER_TASK', '0')) == 8, 'Expected eight allocated CPUs')
        for name, pin in study['payload_files'].items():
            checked(root / name, pin)
        source = Path(study['hydra_source'])
        for name, pin in study['hydra_source_files'].items():
            checked(source / name, pin)
        for name, pin in study['base_files'].items():
            checked(Path(study['base']) / name, pin)
        baseline_path = Path(study['baseline'])
        manifest = json.loads(checked(baseline_path / 'manifest.json', study['baseline_manifest_sha256']).read_text())
        for group in ('adapter', 'tokenizer'):
            for name, pin in manifest[group]['files'].items():
                checked(baseline_path / name, pin)
        actual_versions = {name: importlib.metadata.version(name) for name in study['dependencies']}
        require(actual_versions == study['dependencies'], f'Dependency mismatch: {actual_versions}')
        receipt['dependencies'] = actual_versions
        sys.path[:0] = [str(root), str(source / 'hydra-playground')]
        import worker
        worker.load_kernel()
        from training.peano_policy.prompt import CapabilityIdentity, render_prompt
        from training.peano_policy.contract import authority_prompt_environment
        from training.peano_policy.authority import AuthorityTokenConstraint, validate_authority_tactic, authority_profile_record
        from peano_lab.ui.prove import SurfaceCapabilities
        from hybrid_search import search, HybridLimits
        from hydra_torch_candidate import CandidatePolicy, TorchGreedyBackend, Limits
        cap_record = manifest['common_contract']['authority']['capabilities']
        environment = authority_prompt_environment(False, CapabilityIdentity.from_record({
            'label': cap_record['label'], 'allowed_commands': cap_record['allowed_commands'],
            'allowed_theorems': cap_record['allowed_theorems']}))
        require(authority_profile_record(environment) == manifest['common_contract']['decoder_profile'], 'Execution authority differs')
        capabilities = SurfaceCapabilities(label=cap_record['label'], allowed_commands=frozenset(cap_record['allowed_commands']), allowed_theorems=frozenset())
        latent_source = root / arm['latent_source']
        training_receipt = json.loads((root / arm['receipt']).read_text())
        identity = training_receipt['identity']
        config_hash = hashlib.sha256(json.dumps(training_receipt['config'], sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
        require(config_hash == identity['config_sha256'], 'Training config identity differs')
        modules = list((latent_source / 'src/latentproof').glob('*.py'))
        expected_modules = {name for name in identity['sources_sha256'] if name.startswith('src/latentproof/') and name.endswith('.py')}
        require(len(expected_modules) == 20 and {module.relative_to(latent_source).as_posix() for module in modules} == expected_modules,
                'Frozen latent Python module inventory differs')
        for module in modules:
            relative = module.relative_to(latent_source).as_posix()
            checked(module, identity['sources_sha256'][relative])
        sys.path.insert(0, str(latent_source / 'src'))
        from latentproof.qwen_data import compact_prompt
        from latentproof.qwen_eval import strict_generation, check_prompt_binding
        require(all(Path(sys.modules[name].__file__).resolve().is_relative_to(latent_source.resolve())
                    for name in ('latentproof', 'latentproof.qwen_data', 'latentproof.qwen_eval')),
                'Imported latent source came from another package')
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from peft import PeftModel
        require(torch.cuda.is_available() and torch.cuda.device_count() == 1, 'Exactly one CUDA device required')
        device = torch.cuda.get_device_properties(0)
        require('GH200' in device.name and device.major == 9, 'Expected allocated GH200')
        torch.set_num_threads(8)
        torch.manual_seed(0)
        torch.cuda.manual_seed_all(0)
        torch.use_deterministic_algorithms(True)
        receipt['device'] = device.name
        load_started = time.monotonic()
        if arm['kind'] == 'historical_primitive_v4':
            tokenizer = AutoTokenizer.from_pretrained(str(baseline_path / 'tokenizer'), local_files_only=True, trust_remote_code=False)
            base = AutoModelForCausalLM.from_pretrained(study['base'], torch_dtype=torch.bfloat16, attn_implementation='sdpa', local_files_only=True, trust_remote_code=False, use_safetensors=True)
            model = PeftModel.from_pretrained(base, str(baseline_path / 'adapter'), is_trainable=False, local_files_only=True, use_safetensors=True).to('cuda')
            model.config.use_cache = False
            named = {name: p for name, p in model.named_parameters() if '.lora_' in name}
            require(len(named) == 392 and all(16 in p.shape for p in named.values()), 'Historical adapter population differs')
            checkpoint_sha = manifest['adapter']['files']['adapter/adapter_model.safetensors']
            tokenizer_sha = manifest['tokenizer']['sha256']
        else:
            from latentproof.qwen_train import make_model, restore_trainable
            require(identity['arm'] == 'qwen_vanilla' and identity['base'] == study['base_files'], 'Candidate training identity/base differs')
            checkpoint = Path(arm['checkpoint'])
            if not checkpoint.is_absolute():
                checkpoint = root / checkpoint
            checked(checkpoint, arm['checkpoint_sha256'])
            saved = torch.load(checkpoint, map_location='cpu', weights_only=True)
            require(saved['identity'] == identity and saved['step'] == arm['selected_step'], 'Selected checkpoint identity/step differs')
            require(saved['policy'] == {'kind': 'fixed', 'depth': 1}, 'Only selected vanilla depth one supported')
            weights = saved['trainable']
            require(len(weights) == 392 and all('.lora_' in name and 32 in tensor.shape and bool(torch.isfinite(tensor).all()) for name, tensor in weights.items()), 'Vanilla rank32 population differs')
            tokenizer = AutoTokenizer.from_pretrained(study['base'], local_files_only=True, trust_remote_code=False)
            model = make_model(training_receipt['config'], study['base'], 'qwen_vanilla')
            targets = dict(model.named_parameters())
            require(all(targets[name].dtype == tensor.dtype for name, tensor in weights.items()), 'Candidate adapter dtype differs')
            restore_trainable(model, weights)
            restored = dict(model.named_parameters())
            require(all(torch.equal(restored[name].detach().cpu(), tensor) for name, tensor in weights.items()), 'Candidate reload differs')
            from safetensors.torch import save_file
            save_file({name: tensor.contiguous() for name, tensor in weights.items()}, str(out / 'selected-lora.safetensors'))
            receipt['exported_lora_sha256'] = digest(out / 'selected-lora.safetensors')
            checkpoint_sha = arm['checkpoint_sha256']
            tokenizer_sha = study['base_files']['tokenizer.json']
            del weights, saved
        model.eval()
        model.requires_grad_(False)
        tokenizer.pad_token = tokenizer.eos_token
        backend = TorchGreedyBackend(model, kind=arm['kind'])
        receipt['model_load_seconds'] = time.monotonic() - load_started
        receipt['checkpoint_sha256'] = checkpoint_sha
        provenance = {'checkpoint_sha256': checkpoint_sha, 'tokenizer_identity_sha256': tokenizer_sha,
                      'source_inventory_sha256': study['source_inventory_sha256'], 'run_id': args.arm,
                      'policy': {'kind': 'fixed', 'depth': 1}, 'model_vocab_size': backend.model_vocab_size}
        inputs = json.loads((root / 'inputs.json').read_text())['cases']
        require(len(inputs) == 32 and len({case['id'] for case in inputs}) == 32, 'Expected frozen 32 cases')
        def alarm(_signum, _frame):
            raise TimeoutError('Hard per-case wall limit')
        signal.signal(signal.SIGALRM, alarm)
        for case in inputs:
            case_started = time.monotonic()
            deadline = case_started + study['search_limits']['wall_seconds']
            policy = CandidatePolicy(backend=backend, tokenizer=tokenizer, kind=arm['kind'], environment=environment,
                provenance=provenance, render_prompt=render_prompt if arm['kind'] == 'historical_primitive_v4' else compact_prompt,
                strict_generation=strict_generation, check_prompt_binding=check_prompt_binding,
                validate_tactic=validate_authority_tactic,
                constraint_factory=AuthorityTokenConstraint if arm['kind'] == 'historical_primitive_v4' else None,
                limits=Limits(**study['provider_limits']), deadline_monotonic=deadline)
            record = {'case_id': case['id'], 'theorem': case['theorem'], 'status': 'started', 'proved': False}
            signal.setitimer(signal.ITIMER_REAL, study['hard_case_seconds'])
            try:
                result = search(case['theorem'], capabilities=capabilities, model_policy=policy,
                                limits=HybridLimits(**study['search_limits']))
                record['search'] = result
                record['status'] = result['status']
                failures = [attempt for attempt in policy.report()['attempts']
                            if attempt['status'] == 'failed' and attempt.get('error_type') != 'TimeoutError']
                require(not failures and not any(row.get('kind') == 'model_error' for row in result.get('diagnostics', [])),
                        'Provider infrastructure/receipt failure; not a model-quality result')
                if result['status'] == 'proof':
                    replay = worker.replay({'theorem': case['theorem'], 'tactics': result['commands']})
                    record['independent_replay'] = replay
                    require(result['kernel_checked'] is True and replay['status'] == 'proved' and replay['kernel_checked'] is True and not replay['goals'], 'Independent native replay failed')
                    require(replay['theorem'] == replay['original_theorem'] == case['theorem']
                            and replay['commands'] == result['commands'] and replay['classical'] is False
                            and 'experimental' not in replay and replay['kernel_source_commit'] == worker.SOURCE_COMMIT,
                            'Replay target/authority/source differs')
                    steps = [row for row in replay['trace'] if 'v' in row]
                    require(replay['trace'][-1].get('qed') is True
                            and replay['trace'][-1].get('theorem') == case['theorem']
                            and replay['tactics_applied'] == replay['tactics_requested'] == len(result['commands']) == len(steps)
                            and replay['failed_tactics'] == 0 and replay['failed_step'] is None and replay['error'] is None
                            and all(step.get('status') == 'ok' and step.get('error') is None for step in steps),
                            'Replay did not close with complete successful tactic accounting')
                    record['proved'] = True
            except TimeoutError as error:
                record.update(status='timeout', error=str(error))
            except BaseException as error:
                record.update(status='infrastructure_error', error_type=type(error).__name__, error=str(error))
                raise
            finally:
                signal.setitimer(signal.ITIMER_REAL, 0)
                record['wall_seconds'] = time.monotonic() - case_started
                record['provider'] = policy.report()
                save(out / (case['id'] + '.json'), record)
                receipt['cases'].append({key: record[key] for key in ('case_id', 'status', 'proved', 'wall_seconds')})
                print(json.dumps({'arm': args.arm, **receipt['cases'][-1]}, ensure_ascii=False), flush=True)
        receipt.update(status='completed', cases_completed=len(receipt['cases']),
                       peak_gpu_allocated_bytes=torch.cuda.max_memory_allocated())
    except BaseException as error:
        receipt.update(status='failed', error_type=type(error).__name__, error=str(error), traceback=traceback.format_exc())
        raise
    finally:
        receipt['wall_seconds'] = time.monotonic() - started
        receipt['finished_utc'] = datetime.now(timezone.utc).isoformat()
        save(out / 'receipt.json', receipt)


if __name__ == '__main__':
    main()
