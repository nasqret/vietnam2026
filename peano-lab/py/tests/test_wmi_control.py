"""Static, no-network checks for the WMI A100 capability probe."""

from __future__ import annotations

from pathlib import Path
import subprocess


REPO_ROOT = Path(__file__).resolve().parents[3]
PROBE = REPO_ROOT / "slurm" / "peano_wmi_a100_probe.sbatch"


def _source() -> str:
    return PROBE.read_text(encoding="utf-8")


def test_wmi_probe_parses_as_bash() -> None:
    subprocess.run(["bash", "-n", str(PROBE)], check=True)


def test_wmi_probe_requests_one_nonpreemptible_a100_briefly() -> None:
    source = _source()
    assert "#SBATCH --partition=gpu_csi" in source
    assert "#SBATCH --gpus=nvidia_a100:1" in source
    assert "#SBATCH --constraint=vram80g" in source
    assert "#SBATCH --time=00:05:00" in source
    assert "#SBATCH --mem=8G" in source
    assert "gpu_spot" not in source


def test_wmi_probe_is_read_only_and_records_decisive_runtime_facts() -> None:
    source = _source()
    assert "installs nothing" in source
    assert "pip install" not in source
    assert "conda create" not in source
    assert "nvidia-smi" in source
    assert "driver_version" in source
    assert "compute_cap" in source
    assert "torch.cuda.is_bf16_supported()" in source
    assert 'torch.__version__ == "2.5.1"' in source
    assert 'torch.version.cuda == "12.4"' in source
    assert "torch.cuda.device_count() == 1" in source
    assert "loss.backward()" in source
    assert "anaconda/2025.12-1" in source
    assert "conda activate pytorch-gpu" in source
    assert "module -t spider anaconda" in source
    assert "pypi.org/simple/torch/" in source
    assert "Qwen/Qwen3-1.7B-Base" in source
    assert "Peano WMI A100 probe: OK" in source
