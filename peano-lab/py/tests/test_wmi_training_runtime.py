"""Pure tests for site-neutral training provenance and smoke contracts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from training.peano_policy import runtime
from training.peano_policy.smoke import (
    DEFAULT_PLATFORM_CONTRACT,
    SmokePlatformContract,
    _parse_cuda_capability,
    _platform_contract_record,
    _verify_accelerator,
    _verify_machine,
)


_CLUSTER_ENVIRONMENT = (
    "LOADEDMODULES",
    "PEANO_BASE_ENV",
    "PEANO_BASE_MANIFEST",
    "PEANO_CLUSTER_BACKEND",
    "PEANO_HELIOS_ML_MODULE",
    "PEANO_JOB_ENV_SCRIPT",
    "PEANO_JOB_ENV_SHA256",
    "PEANO_JOB_SCRIPT",
    "PEANO_ML_MODULE",
    "PEANO_REQUIREMENTS_LOCK",
    "SLURM_JOB_ID",
    "SLURM_SUBMIT_DIR",
)


@pytest.fixture(autouse=True)
def _clear_cluster_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep local, Helios, and WMI declarations from leaking between tests."""

    for name in _CLUSTER_ENVIRONMENT:
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def requirements_tree(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[Path, Path]:
    training = tmp_path / "training" / "peano_policy"
    training.mkdir(parents=True, exist_ok=True)
    default = training / "requirements-helios.lock"
    override = training / "requirements-wmi-overlay.lock"
    default.write_text("transformers==4.53.2\n", encoding="utf-8")
    override.write_text("transformers==4.53.3\n", encoding="utf-8")
    monkeypatch.setattr(runtime, "REPOSITORY_ROOT", tmp_path)
    monkeypatch.setattr(runtime, "REQUIREMENTS_PATH", default)
    return default, override


@pytest.fixture
def base_manifest_tree(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Path:
    """Install one canonical reviewed-base fixture under the permitted path."""

    training = tmp_path / "training" / "peano_policy"
    training.mkdir(parents=True, exist_ok=True)
    path = training / "wmi-base-v1.json"
    manifest = {
        "base_environment": "pytorch-gpu",
        "central_prefix": "/projects/wmi_conda/pytorch-gpu",
        "ensurepip": "25.0.1",
        "machine": "x86_64",
        "module": "anaconda/2025.12-1",
        "packages": {"numpy": "2.3.5", "torch": "2.5.1"},
        "python": "3.12.12",
        "torch_cuda": "12.4",
        "v": 1,
    }
    path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(runtime, "REPOSITORY_ROOT", tmp_path)
    return path


@pytest.fixture
def wmi_job_tree(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[Path, Path]:
    """Declare one WMI job and its exact pre-source environment helper."""

    slurm = tmp_path / "slurm"
    scripts = tmp_path / "scripts"
    slurm.mkdir()
    scripts.mkdir()
    job = slurm / "peano_wmi_test.sbatch"
    helper = scripts / "wmi_job_environment.sh"
    job.write_text("#!/bin/bash\necho job\n", encoding="utf-8")
    helper.write_text("#!/bin/bash\necho helper-v1\n", encoding="utf-8")
    monkeypatch.setattr(runtime, "REPOSITORY_ROOT", tmp_path)
    monkeypatch.setenv("PEANO_CLUSTER_BACKEND", "wmi")
    monkeypatch.setenv("PEANO_JOB_SCRIPT", "slurm/peano_wmi_test.sbatch")
    monkeypatch.setenv("PEANO_JOB_ENV_SCRIPT", "scripts/wmi_job_environment.sh")
    return job, helper


def test_legacy_helios_and_generic_wmi_module_records_share_shape(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PEANO_HELIOS_ML_MODULE", "ML-bundle/25.10")
    monkeypatch.setenv("LOADEDMODULES", "gcc:ML-bundle/25.10")
    legacy = runtime.module_identity(required=True)
    assert legacy == {
        "status": "loaded",
        "requested": "ML-bundle/25.10",
        "loaded_modules": ["gcc", "ML-bundle/25.10"],
    }

    monkeypatch.delenv("PEANO_HELIOS_ML_MODULE")
    monkeypatch.setenv("PEANO_ML_MODULE", "anaconda/2025.12-1")
    monkeypatch.setenv("LOADEDMODULES", "anaconda/2025.12-1")
    assert runtime.module_identity(required=True) == {
        "status": "loaded",
        "requested": "anaconda/2025.12-1",
        "loaded_modules": ["anaconda/2025.12-1"],
    }


def test_conflicting_module_declarations_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PEANO_ML_MODULE", "anaconda/2025.12-1")
    monkeypatch.setenv("PEANO_HELIOS_ML_MODULE", "ML-bundle/25.10")
    monkeypatch.setenv("LOADEDMODULES", "anaconda/2025.12-1")
    with pytest.raises(ValueError, match="disagree"):
        runtime.module_identity(required=True)


def test_same_generic_and_legacy_module_declarations_are_accepted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PEANO_ML_MODULE", "ML-bundle/25.10")
    monkeypatch.setenv("PEANO_HELIOS_ML_MODULE", "ML-bundle/25.10")
    monkeypatch.setenv("LOADEDMODULES", "gcc:ML-bundle/25.10")
    assert runtime.module_identity(required=True) == {
        "status": "loaded",
        "requested": "ML-bundle/25.10",
        "loaded_modules": ["gcc", "ML-bundle/25.10"],
    }


@pytest.mark.parametrize(
    ("requested", "loaded"),
    (
        ("anaconda/2025.12-1", None),
        (None, "anaconda/2025.12-1"),
    ),
)
def test_required_module_declaration_rejects_incomplete_environment(
    requested: str | None,
    loaded: str | None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if requested is not None:
        monkeypatch.setenv("PEANO_ML_MODULE", requested)
    if loaded is not None:
        monkeypatch.setenv("LOADEDMODULES", loaded)
    with pytest.raises(ValueError, match="complete module stack"):
        runtime.module_identity(required=True)


@pytest.mark.parametrize(
    ("name", "value"),
    (
        ("PEANO_ML_MODULE", "anaconda/2025.12-1\nforged"),
        ("LOADEDMODULES", "anaconda/2025.12-1\tforged"),
    ),
)
def test_module_declaration_rejects_control_characters(
    name: str,
    value: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PEANO_ML_MODULE", "anaconda/2025.12-1")
    monkeypatch.setenv("LOADEDMODULES", "anaconda/2025.12-1")
    monkeypatch.setenv(name, value)
    with pytest.raises(ValueError, match="safe text"):
        runtime.module_identity(required=True)


def test_requirements_override_is_hashed_and_bound_to_deployment(
    requirements_tree: tuple[Path, Path],
    base_manifest_tree: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    default, override = requirements_tree

    default_identity = runtime.requirements_identity()
    assert default_identity == {
        "path": "training/peano_policy/requirements-helios.lock",
        "sha256": runtime.sha256_file(default),
    }

    override_name = "training/peano_policy/requirements-wmi-overlay.lock"
    monkeypatch.setenv("PEANO_REQUIREMENTS_LOCK", override_name)
    monkeypatch.setenv("PEANO_CLUSTER_BACKEND", "wmi")
    monkeypatch.setenv("PEANO_BASE_ENV", "pytorch-gpu")
    monkeypatch.setenv(
        "PEANO_BASE_MANIFEST",
        "training/peano_policy/wmi-base-v1.json",
    )

    identity = runtime.requirements_identity()
    assert identity == {
        "path": override_name,
        "sha256": runtime.sha256_file(override),
    }
    assert identity != default_identity
    deployment = runtime.deployment_identity()
    assert deployment["runtime_declaration"] == {
        "backend": "wmi",
        "base_environment": "pytorch-gpu",
        "base_manifest": {
            "path": "training/peano_policy/wmi-base-v1.json",
            "sha256": runtime.sha256_file(base_manifest_tree),
        },
        "requirements": identity,
    }


def test_base_manifest_safe_path_is_hashed_and_bound_to_deployment(
    requirements_tree: tuple[Path, Path],
    base_manifest_tree: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del requirements_tree
    name = "training/peano_policy/wmi-base-v1.json"
    monkeypatch.setenv("PEANO_BASE_MANIFEST", name)
    identity = runtime.base_manifest_identity()
    assert identity == {
        "path": name,
        "sha256": runtime.sha256_file(base_manifest_tree),
    }

    monkeypatch.setenv("PEANO_CLUSTER_BACKEND", "wmi")
    monkeypatch.setenv("PEANO_BASE_ENV", "pytorch-gpu")
    monkeypatch.setenv(
        "PEANO_REQUIREMENTS_LOCK",
        "training/peano_policy/requirements-wmi-overlay.lock",
    )
    declaration = runtime._runtime_declaration()
    assert declaration is not None
    assert declaration["base_manifest"] == identity


@pytest.mark.parametrize(
    "value",
    (
        "/tmp/wmi-base-v1.json",
        "../wmi-base-v1.json",
        "training/../../wmi-base-v1.json",
        "training/peano_policy/wmi base-v1.json",
        "training/peano_policy/wmi-base-v1000.json",
        "training/peano_policy/other-base-v1.json",
    ),
)
def test_base_manifest_rejects_unsafe_paths(
    value: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(runtime, "REPOSITORY_ROOT", tmp_path)
    monkeypatch.setenv("PEANO_BASE_MANIFEST", value)
    with pytest.raises(ValueError, match="base manifest"):
        runtime.base_manifest_identity()


def test_base_manifest_rejects_missing_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(runtime, "REPOSITORY_ROOT", tmp_path)
    monkeypatch.setenv(
        "PEANO_BASE_MANIFEST",
        "training/peano_policy/wmi-base-v2.json",
    )
    with pytest.raises(ValueError, match="regular file"):
        runtime.base_manifest_identity()


def test_base_manifest_rejects_final_symlink(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    training = tmp_path / "training" / "peano_policy"
    training.mkdir(parents=True)
    target = training / "reviewed.json"
    target.write_text("{}\n", encoding="utf-8")
    (training / "wmi-base-v2.json").symlink_to(target)
    monkeypatch.setattr(runtime, "REPOSITORY_ROOT", tmp_path)
    monkeypatch.setenv(
        "PEANO_BASE_MANIFEST",
        "training/peano_policy/wmi-base-v2.json",
    )
    with pytest.raises(ValueError, match="regular file"):
        runtime.base_manifest_identity()


def test_base_manifest_rejects_parent_symlink_escape(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    outside_training = tmp_path / "outside" / "training"
    (outside_training / "peano_policy").mkdir(parents=True)
    (outside_training / "peano_policy" / "wmi-base-v2.json").write_text(
        "{}\n",
        encoding="utf-8",
    )
    (repository / "training").symlink_to(
        outside_training,
        target_is_directory=True,
    )
    monkeypatch.setattr(runtime, "REPOSITORY_ROOT", repository)
    monkeypatch.setenv(
        "PEANO_BASE_MANIFEST",
        "training/peano_policy/wmi-base-v2.json",
    )
    with pytest.raises(ValueError, match="outside the repository"):
        runtime.base_manifest_identity()


def test_wmi_job_script_identity_composes_exact_support_helper(
    wmi_job_tree: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    job, helper = wmi_job_tree
    job_sha256 = runtime.sha256_file(job)
    helper_sha256 = runtime.sha256_file(helper)
    monkeypatch.setenv("PEANO_JOB_ENV_SHA256", helper_sha256)
    composite = hashlib.sha256(
        f"{job_sha256}\n{helper_sha256}\n".encode("ascii")
    ).hexdigest()
    identity = runtime.job_script_identity(required=True)
    assert identity == {
        "status": "declared",
        "path": "slurm/peano_wmi_test.sbatch",
        "file_sha256": job_sha256,
        "support_script": {
            "status": "declared",
            "path": "scripts/wmi_job_environment.sh",
            "sha256": helper_sha256,
            "sourced_sha256": helper_sha256,
        },
        "sha256": composite,
    }

    helper.write_text("#!/bin/bash\necho helper-v2\n", encoding="utf-8")
    monkeypatch.setenv("PEANO_JOB_ENV_SHA256", runtime.sha256_file(helper))
    changed = runtime.job_script_identity(required=True)
    assert changed["file_sha256"] == job_sha256
    assert changed["support_script"]["sha256"] != helper_sha256
    assert changed["sha256"] != composite


def test_wmi_job_script_identity_requires_pre_source_helper_hash(
    wmi_job_tree: tuple[Path, Path],
) -> None:
    del wmi_job_tree
    with pytest.raises(ValueError, match="PEANO_JOB_ENV_SHA256 is required"):
        runtime.job_script_identity(required=True)


@pytest.mark.parametrize(
    "declared",
    (
        "not-a-sha256",
        "0" * 64,
        "A" * 64,
        "f" * 63,
    ),
)
def test_wmi_job_script_identity_rejects_bad_pre_source_helper_hash(
    declared: str,
    wmi_job_tree: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del wmi_job_tree
    monkeypatch.setenv("PEANO_JOB_ENV_SHA256", declared)
    with pytest.raises(ValueError, match="helper hash does not match"):
        runtime.job_script_identity(required=True)


def test_wmi_job_script_identity_rejects_final_symlink(
    wmi_job_tree: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    job, helper = wmi_job_tree
    target = job.with_name("real.sbatch")
    target.write_text("#!/bin/bash\ntrue\n", encoding="utf-8")
    job.unlink()
    job.symlink_to(target)
    monkeypatch.setenv("PEANO_JOB_ENV_SHA256", runtime.sha256_file(helper))
    with pytest.raises(ValueError, match="regular repository job"):
        runtime.job_script_identity(required=True)


def test_wmi_nvidia_driver_version_is_unique_and_canonical(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Completed:
        stdout = "610.43.02\n610.43.02\n610.43.02\n610.43.02\n"

    monkeypatch.setattr(runtime.subprocess, "run", lambda *args, **kwargs: Completed())
    assert runtime._nvidia_driver_version() == "610.43.02"

    Completed.stdout = "610.43.02\nother\n"
    with pytest.raises(RuntimeError, match="canonical NVIDIA driver"):
        runtime._nvidia_driver_version()


@pytest.mark.parametrize(
    "value",
    ("/tmp/lock", "../lock", "training/../../lock", "bad lock"),
)
def test_requirements_override_rejects_unsafe_paths(
    value: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(runtime, "REPOSITORY_ROOT", tmp_path)
    monkeypatch.setenv("PEANO_REQUIREMENTS_LOCK", value)
    with pytest.raises(ValueError, match="requirements"):
        runtime.requirements_identity()


def test_requirements_override_rejects_missing_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(runtime, "REPOSITORY_ROOT", tmp_path)
    monkeypatch.setenv(
        "PEANO_REQUIREMENTS_LOCK",
        "training/peano_policy/requirements-missing.lock",
    )
    with pytest.raises(ValueError, match="regular file"):
        runtime.requirements_identity()


def test_requirements_override_rejects_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    directory = (
        tmp_path / "training" / "peano_policy" / "requirements-directory.lock"
    )
    directory.mkdir(parents=True)
    monkeypatch.setattr(runtime, "REPOSITORY_ROOT", tmp_path)
    monkeypatch.setenv(
        "PEANO_REQUIREMENTS_LOCK",
        "training/peano_policy/requirements-directory.lock",
    )
    with pytest.raises(ValueError, match="regular file"):
        runtime.requirements_identity()


def test_requirements_override_rejects_final_symlink(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    training = tmp_path / "training" / "peano_policy"
    training.mkdir(parents=True)
    target = training / "real.lock"
    target.write_text("transformers==4.53.3\n", encoding="utf-8")
    link = training / "requirements-link.lock"
    link.symlink_to(target)
    monkeypatch.setattr(runtime, "REPOSITORY_ROOT", tmp_path)
    monkeypatch.setenv(
        "PEANO_REQUIREMENTS_LOCK",
        "training/peano_policy/requirements-link.lock",
    )
    with pytest.raises(ValueError, match="regular file"):
        runtime.requirements_identity()


def test_requirements_override_rejects_parent_symlink_escape(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    outside = tmp_path / "outside" / "peano_policy"
    outside.mkdir(parents=True)
    (outside / "requirements-escaped.lock").write_text(
        "transformers==4.53.3\n",
        encoding="utf-8",
    )
    (repository / "training").symlink_to(outside.parent, target_is_directory=True)
    monkeypatch.setattr(runtime, "REPOSITORY_ROOT", repository)
    monkeypatch.setenv(
        "PEANO_REQUIREMENTS_LOCK",
        "training/peano_policy/requirements-escaped.lock",
    )
    with pytest.raises(ValueError, match="outside the repository"):
        runtime.requirements_identity()


@pytest.mark.parametrize(
    "present",
    tuple(
        tuple(
            name
            for index, name in enumerate(
                (
                    "PEANO_CLUSTER_BACKEND",
                    "PEANO_BASE_ENV",
                    "PEANO_REQUIREMENTS_LOCK",
                    "PEANO_BASE_MANIFEST",
                )
            )
            if mask & (1 << index)
        )
        for mask in range(1, (1 << 4) - 1)
    ),
)
def test_runtime_declaration_rejects_incomplete_environment(
    present: tuple[str, ...],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    values = {
        "PEANO_CLUSTER_BACKEND": "wmi",
        "PEANO_BASE_ENV": "pytorch-gpu",
        "PEANO_REQUIREMENTS_LOCK": (
            "training/peano_policy/requirements-wmi-overlay.lock"
        ),
        "PEANO_BASE_MANIFEST": "training/peano_policy/wmi-base-v1.json",
    }
    for name in present:
        monkeypatch.setenv(name, values[name])
    with pytest.raises(ValueError, match="declaration is incomplete"):
        runtime._runtime_declaration()


@pytest.mark.parametrize(
    ("name", "value"),
    (
        ("PEANO_CLUSTER_BACKEND", "bad backend"),
        ("PEANO_CLUSTER_BACKEND", "wmi\nforged"),
        ("PEANO_BASE_ENV", "bad base"),
        ("PEANO_BASE_ENV", "pytorch-gpu\tforged"),
    ),
)
def test_runtime_declaration_rejects_malformed_values(
    name: str,
    value: str,
    requirements_tree: tuple[Path, Path],
    base_manifest_tree: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del requirements_tree, base_manifest_tree
    monkeypatch.setenv("PEANO_CLUSTER_BACKEND", "wmi")
    monkeypatch.setenv("PEANO_BASE_ENV", "pytorch-gpu")
    monkeypatch.setenv(
        "PEANO_REQUIREMENTS_LOCK",
        "training/peano_policy/requirements-wmi-overlay.lock",
    )
    monkeypatch.setenv(
        "PEANO_BASE_MANIFEST",
        "training/peano_policy/wmi-base-v1.json",
    )
    monkeypatch.setenv(name, value)
    with pytest.raises(ValueError, match=f"{name} is malformed"):
        runtime._runtime_declaration()


def test_default_smoke_contract_preserves_helios_behavior() -> None:
    assert DEFAULT_PLATFORM_CONTRACT == SmokePlatformContract()
    assert DEFAULT_PLATFORM_CONTRACT.expected_machine == "aarch64"
    assert DEFAULT_PLATFORM_CONTRACT.minimum_cuda_capability is None
    assert DEFAULT_PLATFORM_CONTRACT.report_format == "peano-policy-gh200-smoke"
    assert _parse_cuda_capability("8.0") == (8, 0)
    assert _platform_contract_record(DEFAULT_PLATFORM_CONTRACT) is None


def test_wmi_contract_checks_machine_and_minimum_cuda(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    contract = SmokePlatformContract(
        expected_machine="x86_64",
        minimum_cuda_capability=(8, 0),
        report_format="peano-policy-wmi-a100-smoke",
    )
    assert _platform_contract_record(contract) == {
        "expected_machine": "x86_64",
        "minimum_cuda_capability": [8, 0],
        "report_format": "peano-policy-wmi-a100-smoke",
    }
    monkeypatch.setattr("training.peano_policy.smoke.platform.machine", lambda: "x86_64")
    _verify_machine(contract)

    class Cuda:
        @staticmethod
        def is_available() -> bool:
            return True

        @staticmethod
        def is_bf16_supported() -> bool:
            return True

        @staticmethod
        def get_device_capability(index: int) -> tuple[int, int]:
            assert index == 0
            return (8, 0)

    class Torch:
        cuda = Cuda()

    _verify_accelerator(Torch(), contract)
    with pytest.raises(RuntimeError, match="requires CUDA capability"):
        _verify_accelerator(
            Torch(),
            SmokePlatformContract(
                expected_machine="x86_64",
                minimum_cuda_capability=(8, 6),
                report_format="peano-policy-wmi-a100-smoke",
            ),
        )
