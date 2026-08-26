#!/bin/bash -l
#SBATCH --partition=gpu_csi
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --gpus=nvidia_a100:1
#SBATCH --constraint=vram80g
#SBATCH --time=00:05:00
#SBATCH --job-name=peano-wmi-probe
#SBATCH --output=logs/peano-wmi-probe-%j.out
#SBATCH --error=logs/peano-wmi-probe-%j.err

# Read-only WMI A100 capability probe.  This job deliberately installs nothing.
set -euo pipefail

cd "${SLURM_SUBMIT_DIR:?SLURM_SUBMIT_DIR is not defined}"
export PYTHONNOUSERSITE=1
unset PYTHONOPTIMIZE

printf '%s\n' '== scheduler =='
date -Is
hostname
uname -a
printf 'job_id=%s\n' "${SLURM_JOB_ID:-}"
printf 'partition=%s\n' "${SLURM_JOB_PARTITION:-}"
printf 'nodes=%s\n' "${SLURM_JOB_NODELIST:-}"
printf 'job_gpus=%s\n' "${SLURM_JOB_GPUS:-}"
printf 'cuda_visible_devices=%s\n' "${CUDA_VISIBLE_DEVICES:-}"

printf '%s\n' '== accelerator =='
if ! command -v nvidia-smi >/dev/null 2>&1; then
  printf '%s\n' 'nvidia-smi: missing' >&2
  exit 1
fi
nvidia-smi -L
nvidia-smi \
  --query-gpu=name,driver_version,memory.total,compute_cap \
  --format=csv,noheader
if ! nvidia-smi --query-gpu=name --format=csv,noheader | grep -F 'A100' >/dev/null; then
  printf '%s\n' 'assigned accelerator is not an NVIDIA A100' >&2
  exit 1
fi

printf '%s\n' '== base runtime =='
printf 'python3=%s\n' "$(command -v python3 || true)"
python3 --version || true
printf 'nvcc=%s\n' "$(command -v nvcc || true)"
nvcc --version || true

printf '%s\n' '== environment modules =='
if ! command -v module >/dev/null 2>&1; then
  printf '%s\n' 'module: missing'
  exit 1
fi
module purge
module -t spider anaconda 2>&1 || true
module -t spider miniconda 2>&1 || true
module -t spider cuda 2>&1 || true

printf '%s\n' '== documented PyTorch environment =='
module load anaconda/2025.12-1
module list 2>&1
printf 'conda=%s\n' "$(command -v conda)"
conda --version
# The central environment's MKL activation hook reads MKL_INTERFACE_LAYER
# without a default.  Keep our script strict, but do not impose nounset on the
# administrator-owned Conda activation hooks.
set +u
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate pytorch-gpu
set -u
conda env list
python --version
python - <<'PY'
import json
import math
import platform

import torch

assert platform.machine() == "x86_64", platform.machine()
assert torch.__version__ == "2.5.1", torch.__version__
assert torch.version.cuda == "12.4", torch.version.cuda
assert torch.cuda.is_available()
assert torch.cuda.device_count() == 1, torch.cuda.device_count()
properties = torch.cuda.get_device_properties(0)
assert "A100" in properties.name, properties.name
assert properties.total_memory >= 75 * 1024**3, properties.total_memory
assert torch.cuda.is_bf16_supported()

tensor = torch.randn(
    (2048, 2048),
    device="cuda",
    dtype=torch.bfloat16,
    requires_grad=True,
)
loss = (tensor @ tensor).float().square().mean()
loss.backward()
torch.cuda.synchronize()
assert tensor.grad is not None
assert bool(torch.isfinite(tensor.grad).all())
assert math.isfinite(loss.item())

report = {
    "bf16_supported": torch.cuda.is_bf16_supported(),
    "cuda_available": torch.cuda.is_available(),
    "device": properties.name,
    "device_count": torch.cuda.device_count(),
    "implementation": platform.python_implementation(),
    "loss": loss.item(),
    "machine": platform.machine(),
    "peak_bytes": torch.cuda.max_memory_allocated(),
    "python": platform.python_version(),
    "torch": torch.__version__,
    "torch_cuda": torch.version.cuda,
    "total_memory": properties.total_memory,
}
print(json.dumps(report, sort_keys=True))
PY

printf '%s\n' '== outbound access =='
for url in \
  https://pypi.org/simple/torch/ \
  https://huggingface.co/Qwen/Qwen3-1.7B-Base/resolve/ea980cb0a6c2ae4b936e82123acc929f1cec04c1/config.json
do
  if curl --fail --silent --show-error --location --head --max-time 20 "$url" >/dev/null; then
    printf 'reachable %s\n' "$url"
  else
    printf 'unreachable %s\n' "$url"
  fi
done

printf '%s\n' '== storage =='
df -h "$SLURM_SUBMIT_DIR" /work 2>&1 || true
printf '%s\n' 'Peano WMI A100 probe: OK'
