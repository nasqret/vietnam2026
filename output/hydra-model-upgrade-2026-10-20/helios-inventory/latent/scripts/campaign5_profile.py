"""Finite actual-Qwen batch/length profile; execute only inside a GPU SLURM job."""
import argparse
import gc
import hashlib
import json
import os
from pathlib import Path
import time

import torch
from latentproof.qwen_train import make_model, atomic_json
from latentproof import qwen_train


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', required=True)
    parser.add_argument('--config', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--lengths', type=int, nargs='+', default=[1024, 4096])
    parser.add_argument('--micro-batches', type=int, nargs='+', default=[1, 2, 4])
    args = parser.parse_args()
    if not os.environ.get('SLURM_JOB_ID') or not torch.cuda.is_available():
        raise SystemExit('GPU SLURM allocation required')
    if not set(args.lengths) <= {1024, 4096, 6144} or not set(args.micro_batches) <= {1, 2, 4}:
        raise SystemExit('Profile shape is outside the finite registered capacity grid')
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=False)
    cfg = json.loads(Path(args.config).read_text())
    torch.set_num_threads(int(os.environ.get('SLURM_CPUS_PER_TASK', '4')))
    records = []
    started = time.monotonic()
    package = Path(qwen_train.__file__).resolve().parent
    package_pins = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in package.glob('*.py')}
    pins = {str(path.resolve()): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in [Path(__file__), Path(args.config), *package.glob('*.py')]}
    # Synthetic inputs measure capacity; no model-quality conclusions follow.
    for arm, mode in (('qwen_vanilla', 'fixed'), ('qwen_fixed', 'fixed'),
                      ('qwen_adaptive', 'all_depth'), ('qwen_adaptive', 'adaptive')):
        for length, batch in ((length, batch) for length in args.lengths for batch in args.micro_batches):
            if time.monotonic() - started > 2700:
                records.append({'arm': arm, 'sequence_length': length, 'micro_batch': batch,
                                'state': 'not_started_profile_budget'})
                continue
            torch.manual_seed(11)
            torch.cuda.manual_seed_all(11)
            model = optimizer = result = ids = labels = mask = trainable = None
            record = {'arm': arm, 'sequence_length': length, 'micro_batch': batch,
                      'recurrence': 1 if arm == 'qwen_vanilla' else 2 if arm == 'qwen_fixed' else 4,
                      'mode': mode}
            try:
                model = make_model(cfg, args.model, arm)
                model.train()
                ids = ((torch.arange(length, device='cuda').unsqueeze(0) % 1000) + 100).repeat(batch, 1)
                labels = ids.clone()
                labels[:, :-16] = -100
                mask = torch.ones_like(ids)
                trainable = [v for v in model.parameters() if v.requires_grad]
                optimizer = torch.optim.AdamW(trainable, lr=1e-5)
                torch.cuda.reset_peak_memory_stats()
                times, losses, norms = [], [], []
                for repeat in range(3):
                    optimizer.zero_grad(set_to_none=True)
                    torch.cuda.synchronize()
                    tick = time.monotonic()
                    with torch.autocast('cuda', dtype=torch.bfloat16):
                        result = model.supervised_loss(ids, labels, attention_mask=mask,
                            mode=record['mode'], recurrence=record['recurrence'])
                    if not bool(torch.isfinite(result['loss'])):
                        raise RuntimeError('nonfinite profile loss')
                    result['loss'].backward()
                    norm = torch.nn.utils.clip_grad_norm_(trainable, 1., error_if_nonfinite=True)
                    if float(norm) <= 0:
                        raise RuntimeError('zero training gradient')
                    optimizer.step()
                    torch.cuda.synchronize()
                    times.append(time.monotonic() - tick)
                    losses.append(float(result['loss'].detach()))
                    norms.append(float(norm))
                record.update(state='completed', step_seconds=times, warmup_repeats=1,
                    losses=losses, grad_norms=norms, supervised_tokens=16*batch,
                    peak_allocated_bytes=torch.cuda.max_memory_allocated(),
                    peak_reserved_bytes=torch.cuda.max_memory_reserved(),
                    block_calls=result['block_calls'])
            except torch.cuda.OutOfMemoryError:
                record.update(state='out_of_memory')
            finally:
                model = optimizer = result = ids = labels = mask = trainable = None
                gc.collect()
                torch.cuda.empty_cache()
            records.append(record)
            receipt = {'format': 'latent-campaign5-profile-v1', 'job_id': os.environ['SLURM_JOB_ID'],
                'device': torch.cuda.get_device_name(0), 'source_sha256': pins,
                'source_package_sha256': package_pins,
                'synthetic_capacity_only': True, 'elapsed_seconds': time.monotonic()-started,
                'profiles': records}
            atomic_json(out/'profile.json', receipt)
            print(json.dumps(record), flush=True)
    if any(hashlib.sha256(Path(path).read_bytes()).hexdigest() != checksum for path, checksum in pins.items()):
        raise RuntimeError('Source changed during profile')


if __name__ == '__main__':
    main()
