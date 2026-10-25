"""Prepare the fixed inference-only comparison; no remote actions."""
from pathlib import Path
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parent
WORK = ROOT.parent
REPO = WORK.parent.parent
REMOTE_PROJECT = '/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training'
REMOTE = REMOTE_PROJECT + '/experiments/hydra-model-upgrade-20261020/comparison-01'

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def write(path, value):
    with path.open('x') as f:
        json.dump(value, f, indent=2, ensure_ascii=False, sort_keys=True, allow_nan=False)
        f.write('\n')

assert not (ROOT / 'study.json').exists(), 'Preparation is one-use'
shutil.copytree(WORK / 'helios-inventory/c5-frozen-source', ROOT / 'latent-source')
shutil.copy2(WORK / 'helios-inventory/c5-training/helios-c5-main-qwen_vanilla-s29/receipt.json', ROOT / 'helios-receipt.json')
shutil.copy2(WORK / 'helios-inventory/c5-training/helios-c5-main-qwen_vanilla-s29/selection.json', ROOT / 'helios-selection.json')
shutil.copy2(WORK / 'local-discovery/COMPARISON_INPUTS_32.json', ROOT / 'inputs.json')
shutil.copy2(WORK / 'runtime-assessment/proposed-provider/hydra_torch_candidate.py', ROOT / 'hydra_torch_candidate.py')
c5 = json.loads((ROOT / 'helios-receipt.json').read_text())
c6 = json.loads((ROOT / 'wmi-selected/receipt.json').read_text())
assert c5['identity']['sources_sha256'] == c6['identity']['sources_sha256']
assert c5['identity']['base'] == c6['identity']['base']
for name, pin in c5['identity']['sources_sha256'].items():
    assert digest(ROOT / 'latent-source' / name) == pin
selection = json.loads((ROOT / 'wmi-selected/selection.json').read_text())
assert selection['state'] == 'locked' and selection['checkpoint_step'] == 8192
assert digest(ROOT / 'wmi-selected/best.pt') == selection['checkpoint_sha256']
source_manifest = json.loads((REPO / 'output/hydra-implementation-2026-09-04/combined-source-bundle-07/manifest.json').read_text())
source_pins = {name: entry['sha256'] for name, entry in source_manifest['files'].items()
               if name.startswith('_deploy/hydra-retention-evaluation-recovery-execution-20260831/')
               or name.startswith('hydra-playground/')}
source_inventory_sha = hashlib.sha256(json.dumps(source_pins, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
payload_files = {p.relative_to(ROOT).as_posix(): digest(p) for p in ROOT.rglob('*')
                 if p.is_file() and p.name != 'prepare_study.py'}
study = {
    'schema': 'hydra-model-upgrade-comparison-v1',
    'authority': 'HYDRA_EXPERIMENT_AUTHORITY.md; current user request compare and replace with the better model',
    'scope': 'Exposed development integration screen, not an unseen benchmark. Restricted-authority transfer to current Hydra. Same raw base and Torch BF16; not the deployed Mac MLX beam4 runtime.',
    'selection': 'WMI vanilla seed47 selected before panel output by its complete50/64 dev receipt; Helios vanilla29 historical complete16/64; previous deployed retention adapter as control.',
    'promotion_gate': 'Complete comparisons, zero proved controls, more independently replayed positive proofs without losing baseline proofs, then actual Mac-runtime verification. No automatic promotion from training/development receipts.',
    'allocation': {'gpus': 1, 'gpu_type': 'GH200', 'cpus': 8, 'memory_gib': 64,
                   'wall_seconds': 3600, 'training': False, 'automatic_retry': False,
                   'account': 'plgccaiautore2026-gpu-gh200', 'partition': 'plgrid-gpu-gh200',
                   'accounting': 'New October inference comparison; does not modify the closed September6h campaign'},
    'hydra_source': REMOTE_PROJECT + '/experiments/hydra-practical-v1-20260904/bundles/combined-source-07/source',
    'hydra_source_files': source_pins, 'source_inventory_sha256': source_inventory_sha,
    'base': '/net/scratch/hscra/plgrid/plgnasqret/latent/models/qwen3-1.7b-base',
    'base_files': c5['identity']['base'],
    'baseline': REMOTE_PROJECT + '/experiments/retention-pilot-v1/results/peano-hydra/qwen3-1.7b-authority-primitive-retention-pilot-v1',
    'baseline_manifest_sha256': 'cdacbda7777568120029b671374aaf16e994f2da2a54b867a00c81ece086d6ca',
    'dependencies': {key: c5['identity'][key] for key in ['torch', 'transformers', 'peft']},
    'payload_files': payload_files,
    'search_limits': {'max_depth': 96, 'max_states': 2048, 'max_tactic_attempts': 6000,
                      'max_expansions': 384, 'max_frontier': 128, 'candidates_per_state': 48,
                      'max_macro_steps': 8, 'closure_steps': 16, 'heuristic_burst': 8,
                      'max_model_calls': 16, 'max_vampire_calls': 0, 'wall_seconds': 30},
    'provider_limits': {'max_calls': 16, 'max_new_tokens': 128, 'max_total_decision_tokens': 4096,
                        'max_context_tokens': 6144, 'provider_seconds': 30},
    'hard_case_seconds': 35,
    'decoding': 'Common greedy width1,6144 total context,128 max decisions,no truncation; baseline retains primitive-v4 authority token mask and saved tokenizer; latent retains compact-v3 full247 conditioning but cannot import any theorem. Literal proposals all pass identical noimports postflight/native search/replay.',
    'arms': {
        'historical_retention': {'kind': 'historical_primitive_v4', 'latent_source': 'latent-source', 'receipt': 'helios-receipt.json'},
        'wmi_c6_vanilla47': {'kind': 'latent_compact_v3', 'latent_source': 'latent-source', 'receipt': 'wmi-selected/receipt.json',
                             'checkpoint': 'wmi-selected/best.pt', 'checkpoint_sha256': selection['checkpoint_sha256'], 'selected_step': 8192},
        'helios_c5_vanilla29': {'kind': 'latent_compact_v3', 'latent_source': 'latent-source', 'receipt': 'helios-receipt.json',
                               'checkpoint': '/net/scratch/hscra/plgrid/plgnasqret/latent/artifacts/campaign5/runs/helios-c5-main-qwen_vanilla-s29/best.pt',
                               'checkpoint_sha256': 'ce98db794ee6f87565f0012cadce3e0d1b5854ee3bcb513405e85c7f8921467f', 'selected_step': 2048}},
}
write(ROOT / 'study.json', study)
pin = digest(ROOT / 'study.json')
job = f'''#!/bin/bash -l
#SBATCH --job-name=hydra-upgrade-20261020
#SBATCH --account=plgccaiautore2026-gpu-gh200
#SBATCH --partition=plgrid-gpu-gh200
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --gres=gpu:1
#SBATCH --mem=64G
#SBATCH --time=01:00:00
#SBATCH --no-requeue
#SBATCH --output={REMOTE}/job-%j.out
#SBATCH --error={REMOTE}/job-%j.err
set -euo pipefail
umask 077
module purge
module load ML-bundle/25.10
unset PYTHONPATH PYTHONHOME
export PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 PYTHONHASHSEED=0
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS=8 CUBLAS_WORKSPACE_CONFIG=:4096:8
cd {REMOTE}
mkdir results
for arm in historical_retention wmi_c6_vanilla47 helios_c5_vanilla29; do
  {REMOTE_PROJECT}/.venv-helios/bin/python -B -s {REMOTE}/run_arm.py --study {REMOTE}/study.json --study-sha256 {pin} --arm "$arm" --output {REMOTE}/results/"$arm"
done
'''
(ROOT / 'job.sbatch').write_text(job)
write(ROOT / 'ACTION.json', {'purpose': study['scope'], 'remote_directory': REMOTE, 'authority': study['authority'],
    'allocation': study['allocation'], 'study_sha256': pin, 'job_sha256': digest(ROOT / 'job.sbatch'),
    'payload_bytes': sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file()), 'payload_files': len(payload_files),
    'launches': 1, 'retraining': False, 'automatic_retry': False,
    'one_use_remote_marker': REMOTE + '/launch-reserved', 'state': 'prepared'})
print(json.dumps({'study_sha256': pin, 'payload_files': len(payload_files), 'native_source_files': len(source_pins),
                  'payload_bytes': sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file()), 'allocation': study['allocation']}, indent=2))
