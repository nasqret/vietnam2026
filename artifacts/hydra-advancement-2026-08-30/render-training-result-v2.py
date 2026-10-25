"""Render only the recovered, independently pinned completed training evidence.

No model weights, training, native proof replay, remote calls, or installations.
Outputs use exclusive creation; a partial output directory is never recycled.
"""
from __future__ import annotations

import ast
import hashlib
import io
import json
import math
import os
from pathlib import Path
import resource
import signal
import sys


ROOT = Path('/Users/bnaskrecki/codex/peano')
ARCHIVE = ROOT / 'artifacts/hydra-advancement-2026-08-30'
TRAINING = ROOT / 'artifacts/frontier-training-2026-08-30'
OUTPUT = ARCHIVE / 'training-result-02'
INPUTS = {
    'completed-manifest-01.json': '5795d5a3d70f781f56f81e83c2295c887d0949795924f4208f45d26a3ef89b68',
    'completed-training-verification-01.json': '67226503019dfee7bd549baa1e3f69b1d3ca6da8fa3e9e2ef5a66d18d330841d',
    'completed-artifacts-01/receipt.json': '6af7c587bf87b956ad31addaa45617cb6e0fa8db3f74c462b2b80619b3b59ffc',
}


def require(value, message):
    if not value:
        raise ValueError(message)


def timed_out(signum, frame):
    raise TimeoutError('training diagnostic render exceeded 30 seconds')


def write_new(name, raw):
    require(len(raw) <= 8 * 1024**2, 'rendered artifact exceeds 8 MiB')
    with (OUTPUT / name).open('xb') as stream:
        stream.write(raw)
    return {'path': name, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def main():
    resource.setrlimit(resource.RLIMIT_CPU, (20, 21))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    signal.signal(signal.SIGALRM, timed_out)
    signal.alarm(30)
    require(ARCHIVE.resolve() == ARCHIVE and TRAINING.resolve() == TRAINING,
            'archive paths must be canonical')
    inputs, records = {}, {}
    for name, expected in INPUTS.items():
        path = TRAINING / name
        require(path.is_file() and not path.is_symlink() and path.stat().st_size <= 4 * 1024**2,
                'unsafe or oversized input')
        raw = path.read_bytes()
        require(hashlib.sha256(raw).hexdigest() == expected, 'input pin changed: ' + name)
        records[name] = json.loads(raw)
        inputs[name] = {'bytes': len(raw), 'sha256': expected}
    manifest = records['completed-manifest-01.json']
    check = records['completed-training-verification-01.json']
    require(check['status'] == 'completed-training-evidence-verified'
            and check['job_id'] == '21438102' and check['finite_gradient_boundaries'] == 1597
            and check['new_training_started'] is False, 'wrong completed evidence')
    log_path = TRAINING / 'completed-artifacts-01/training.out.log'
    require(log_path.stat().st_size <= 1024**2 and not log_path.is_symlink(), 'unsafe log')
    log_raw = log_path.read_bytes()
    artifact_receipt = records['completed-artifacts-01/receipt.json']
    # The exact collector record is pinned above. Locate its saved stdout hash
    # without depending on the collector's diagnostic field layout.
    log_sha = hashlib.sha256(log_raw).hexdigest()
    require(log_sha in json.dumps(artifact_receipt), 'stdout hash is absent from collector receipt')
    losses, learning_rates = [], []
    for line in log_raw.decode('utf-8').splitlines():
        if not line.startswith("{'loss':"):
            continue
        row = ast.literal_eval(line)
        require(type(row) is dict and type(row['loss']) in (int, float)
                and math.isfinite(row['loss']) and row['loss'] >= 0, 'invalid loss row')
        losses.append(float(row['loss']))
        learning_rates.append(float(row['learning_rate']))
    gradients = manifest['finite_gradient_audit']['records']
    require(len(losses) == len(gradients) == 1597, 'incomplete diagnostic rows')
    require([r['step'] for r in gradients] == list(range(1, 1598)), 'gradient sequence changed')
    norms = [float(r['pre_clip_global_norm']) for r in gradients]
    require(all(math.isfinite(n) and n >= 0 for n in norms), 'nonfinite gradient norm')
    require(abs(sum(losses) / len(losses) - check['mean_rounded_logged_loss']) < 1e-12,
            'loss aggregation changed')
    inputs['completed-artifacts-01/training.out.log'] = {'bytes': len(log_raw), 'sha256': log_sha}

    OUTPUT.mkdir(mode=0o700)
    os.environ['MPLCONFIGDIR'] = str(OUTPUT / '.matplotlib-cache')
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib import pyplot as plt

    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
                         'axes.spines.top': False, 'axes.spines.right': False,
                         'svg.hashsalt': 'hydra-completed-training-21438102'})
    fig, axes = plt.subplots(2, 1, figsize=(10.8, 7.0), constrained_layout=True)
    steps = list(range(1, 1598))
    axes[0].plot(steps, losses, color='#155f88', linewidth=1.1)
    axes[0].set_yscale('symlog', linthresh=0.0001)
    axes[0].set_ylabel('Rounded logged TRAIN loss')
    axes[0].set_title('Completed Hydra pilot: 1,597 optimizer updates', loc='left', weight='bold')
    axes[0].text(0.98, 0.94, 'Job 21438102  |  1 epoch  |  12,772 TRAIN rows\n'
                 'Rounded zeros are not exact zero loss', ha='right', va='top',
                 transform=axes[0].transAxes, fontsize=9,
                 bbox={'facecolor': 'white', 'edgecolor': 'none', 'alpha': 0.88})
    axes[1].plot(steps, norms, color='#9b4c20', linewidth=1.0)
    axes[1].axhline(1.0, color='#575757', linestyle='--', linewidth=0.8, label='Clip maximum: 1.0')
    axes[1].set_yscale('symlog', linthresh=0.0001)
    axes[1].set_ylabel('Pre-clip global gradient norm')
    axes[1].set_xlabel('Optimizer update')
    axes[1].legend(loc='upper right', frameon=False)
    for axis in axes:
        axis.set_xlim(1, 1597)
        axis.set_ylim(bottom=0)
        axis.grid(True, color='#dddddd', linewidth=0.6, alpha=0.75)
    fig.supxlabel('Training diagnostics only. Matched proof-search evaluation is still pending.', fontsize=9)
    outputs = []
    for extension in ('png', 'svg'):
        buffer = io.BytesIO()
        fig.savefig(buffer, format=extension, dpi=150,
                    metadata={'Software': 'Matplotlib'} if extension == 'png' else {'Date': None})
        outputs.append(write_new('training-diagnostics.' + extension, buffer.getvalue()))
    plt.close(fig)

    metrics = check['metrics']
    window_rows = '\n'.join(
        f"| {r['first_step']}–{r['last_step']} | {r['mean_rounded_logged_loss']:.8g} |"
        for r in check['loss_windows'])
    text = f'''# Completed Hydra training pilot

Helios job **21438102** completed with exit **0:0** in **1h 33m 47s**.
The one authorized fresh Qwen3-1.7B-Base LoRA epoch produced a saved adapter
after **1,597 optimizer updates** on **12,772 TRAIN rows**. Its final diagnostic
DEV-loss pass used **2,096 rows**. No additional training job was started.

| Recorded measurement | Value |
| --- | ---: |
| Final TRAIN loss | {metrics['train']['train_loss']:.8f} |
| Diagnostic DEV loss | {metrics['dev']['eval_loss']:.8f} |
| Finite pre/post-clip gradient boundaries | 1,597 / 1,597 |
| Changed trainable parameter tensors | 392 / 392 |
| Saved adapter/tokenizer files independently rehashed | 10 |
| Bytes independently rehashed on Helios | 85,670,667 |
| New proof-search benchmark outcomes | 0 |

![Recorded training loss and gradient norms](training-diagnostics.png)

The curve uses all 1,597 rounded log records and the full saved gradient audit.
The original framework-free validators accepted the audit. Independent remote
file hashing checked the saved artifacts without downloading model weights.
This is integrity and runtime evidence; it does not reconstruct training or
independently inspect saved tensor values.

| Optimizer updates | Mean rounded logged TRAIN loss |
| --- | ---: |
{window_rows}

Loss reaches the logging precision early. A printed `0.0` is rounded, and
TRAIN and DEV losses have different aggregation and exposure. These values do
not establish unseen-test quality or theorem-proving improvement. The next
useful model experiment is the preregistered old/new proof-search comparison
at 8 and 16 calls, with its acceptance and regression criteria preserved.

The full **7,200 GPU-second reservation remains charged**. There is no refund,
automatic retry, resume, benchmark acceptance, reference readiness or renewed
GPU authorization in this report.

The exact final manifest SHA256 is
`{INPUTS['completed-manifest-01.json']}`. The evidence-check SHA256 is
`{INPUTS['completed-training-verification-01.json']}`.
Full input and rendered-file hashes are in [receipt.json](receipt.json).
'''
    outputs.append(write_new('REPORT.md', text.encode()))
    require(not {'torch', 'transformers', 'peft', 'tokenizers'} & set(sys.modules),
            'render unexpectedly loaded a model framework')
    receipt = {'schema': 'peano-hydra-completed-training-diagnostic-render-v1',
               'status': 'rendered', 'job_id': '21438102', 'inputs': inputs,
               'outputs': outputs, 'loss_rows': len(losses), 'gradient_rows': len(norms),
               'matplotlib_version': matplotlib.__version__, 'python_version': sys.version,
               'helper_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               'new_model_or_native_execution': False, 'network_or_scheduler_calls': False,
               'benchmark_or_research_acceptance': False,
               'supersedes_render': 'training-result-01',
               'render_correction': 'Both nonnegative diagnostics now have a zero lower axis bound; data unchanged.'}
    output_pin = write_new('receipt.json', (json.dumps(receipt, indent=2, sort_keys=True) + '\n').encode())
    print(json.dumps({'output_directory': str(OUTPUT), 'receipt': output_pin}, sort_keys=True))
    signal.alarm(0)


if __name__ == '__main__':
    main()
