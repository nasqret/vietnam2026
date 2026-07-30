from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import sys

import pytest

from training.peano_policy.manifest import (
    artifact_directory_hash,
    sha256_file,
    sha256_json,
    write_manifest,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
VERIFIER_PATH = REPOSITORY_ROOT / "scripts" / "verify_peano_morning_adapter.py"
SYNC_PATH = REPOSITORY_ROOT / "scripts" / "sync_peano_morning_adapter.sh"
BOOTSTRAP_PATH = REPOSITORY_ROOT / "scripts" / "bootstrap_peano_model_lab_macos.sh"
PREFETCH_PATH = REPOSITORY_ROOT / "scripts" / "prefetch_peano_base_model.py"

spec = importlib.util.spec_from_file_location("morning_adapter_verifier", VERIFIER_PATH)
assert spec is not None and spec.loader is not None
verifier = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = verifier
spec.loader.exec_module(verifier)


def _fixture_adapter(root: Path) -> verifier.AdapterSeal:
    files = {
        "adapter/README.md": b"adapter\n",
        "adapter/adapter_config.json": b"{}\n",
        "adapter/adapter_model.safetensors": b"safe-test-weights\n",
        "run-identity.json": b'{"test":true}\n',
        "tokenizer/added_tokens.json": b"{}\n",
        "tokenizer/chat_template.jinja": b"template\n",
        "tokenizer/merges.txt": b"merge\n",
        "tokenizer/special_tokens_map.json": b"{}\n",
        "tokenizer/tokenizer.json": b"{}\n",
        "tokenizer/tokenizer_config.json": b"{}\n",
        "tokenizer/vocab.json": b"{}\n",
    }
    for name, payload in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)

    probe = root / "morning-reload-probe.json"
    write_manifest(
        probe,
        {
            "exact_match": True,
            "expected_tactic": "exact h",
            "format": "peano-policy-v3-morning-reload-probe",
            "parsed_tactic": "exact h",
            "status": "probe-completed",
            "v": 1,
            "valid_single_tactic": True,
        },
    )
    adapter_hash = sha256_file(root / "adapter" / "adapter_model.safetensors")
    tensor_names_hash = "7" * 64
    diagnostic_core = {
        "adapter_tensor_audit": {
            "dtypes": {"torch.float32": 392},
            "sha256": adapter_hash,
            "tensor_names_sha256": tensor_names_hash,
            "tensors": 392,
        },
        "format": "peano-policy-v3-morning-diagnostic",
        "reload_probe": {
            "path": probe.name,
            "sha256": sha256_file(probe),
        },
        "status": "completed-diagnostic-not-production",
        "v": 1,
    }
    diagnostic = {
        **diagnostic_core,
        "diagnostic_sha256": sha256_json(diagnostic_core),
    }
    base_config_hash = "8" * 64
    manifest = root / "training-manifest.json"
    write_manifest(
        manifest,
        {
            "adapter": artifact_directory_hash(root, "adapter"),
            "base_model": {
                "config_sha256": base_config_hash,
                "id": "unit/base",
                "requested_revision": "a" * 40,
                "resolved_snapshot_hash": "a" * 40,
            },
            "diagnostic": diagnostic,
            "tokenizer": {
                "artifacts": artifact_directory_hash(root, "tokenizer")
            },
            "v": 1,
        },
    )
    sidecar = root / "morning-diagnostic.json"
    write_manifest(
        sidecar,
        {
            "diagnostic_sha256": diagnostic["diagnostic_sha256"],
            "format": diagnostic["format"],
            "status": diagnostic["status"],
            "training_manifest": {"sha256": sha256_file(manifest)},
            "v": 1,
        },
    )
    sizes = {
        path.relative_to(root).as_posix(): path.stat().st_size
        for path in root.rglob("*")
        if path.is_file()
    }
    top_hashes = {
        name: sha256_file(root / name)
        for name in (
            "morning-diagnostic.json",
            "morning-reload-probe.json",
            "run-identity.json",
            "training-manifest.json",
        )
    }
    adapter_record = artifact_directory_hash(root, "adapter")
    tokenizer_record = artifact_directory_hash(root, "tokenizer")
    return verifier.AdapterSeal(
        file_sizes=sizes,
        top_level_hashes=top_hashes,
        total_bytes=sum(sizes.values()),
        manifest_sha256=sha256_file(manifest),
        adapter_model_sha256=adapter_hash,
        adapter_aggregate_sha256=adapter_record["sha256"],
        tokenizer_aggregate_sha256=tokenizer_record["sha256"],
        base_model_id="unit/base",
        base_model_revision="a" * 40,
        base_config_sha256=base_config_hash,
        adapter_tensors=392,
        adapter_tensor_names_sha256=tensor_names_hash,
    )


def test_verifier_accepts_one_complete_sealed_tree(tmp_path: Path) -> None:
    seal = _fixture_adapter(tmp_path)

    record = verifier.verify_adapter(tmp_path, seal=seal)

    assert record["status"] == "verified"
    assert record["files"] == 14
    assert record["bytes"] == seal.total_bytes


def test_verifier_rejects_mutation_and_extra_file(tmp_path: Path) -> None:
    seal = _fixture_adapter(tmp_path)
    (tmp_path / "adapter" / "README.md").write_bytes(b"changed\n")
    with pytest.raises(ValueError, match="size mismatch|hash mismatch"):
        verifier.verify_adapter(tmp_path, seal=seal)

    (tmp_path / "adapter" / "README.md").write_bytes(b"adapter\n")
    (tmp_path / "unexpected").write_text("x", encoding="utf-8")
    with pytest.raises(ValueError, match="file tree mismatch"):
        verifier.verify_adapter(tmp_path, seal=seal)


def test_verifier_rejects_symlink_even_when_name_is_expected(tmp_path: Path) -> None:
    seal = _fixture_adapter(tmp_path)
    target = tmp_path / "run-identity-target.json"
    target.write_text('{"test":true}\n', encoding="utf-8")
    (tmp_path / "run-identity.json").unlink()
    (tmp_path / "run-identity.json").symlink_to(target)

    with pytest.raises(ValueError, match="unsafe file"):
        verifier.verify_adapter(tmp_path, seal=seal)


@pytest.mark.parametrize("script", [SYNC_PATH, BOOTSTRAP_PATH])
def test_macos_shell_scripts_parse(script: Path) -> None:
    completed = subprocess.run(
        ["bash", "-n", str(script)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr


def test_sync_is_staged_verified_and_no_clobber() -> None:
    source = SYNC_PATH.read_text(encoding="utf-8")
    assert ".incoming.XXXXXX" in source
    assert source.count("verify_peano_morning_adapter.py") == 2
    assert 'mv -n "$staging" "$destination"' in source
    assert "--delete" not in source
    assert "--protect-args" not in source
    assert "if [ -e \"$destination\" ]" in source
    assert "158302721" not in source  # identity remains centralized in verifier


def test_bootstrap_is_hash_locked_and_pins_the_base_snapshot() -> None:
    source = BOOTSTRAP_PATH.read_text(encoding="utf-8")
    assert "--require-hashes" in source
    assert "--only-binary=:all:" in source
    assert "prefetch_peano_base_model.py" in source
    assert "--verify-only" in source
    assert "HF_XET_HIGH_PERFORMANCE=1" in source
    assert "trust_remote_code=True" not in source


def test_base_prefetch_has_exact_online_and_offline_seals() -> None:
    source = PREFETCH_PATH.read_text(encoding="utf-8")
    assert "ea980cb0a6c2ae4b936e82123acc929f1cec04c1" in source
    assert "6df85b39330e5a425ee36253d0f894e4387e4f0a15b9c53cb467d668e6b3a841" in source
    assert "1bb33a92c3548fbc68b889b490e810440435253598835bd71dff0396060c12db" in source
    assert "8c970692323e3ea0e9b8b0a4dca79388d31226e41f83c9fd6014804280ebf6e8" in source
    assert "generation_config.json" in source
    assert 'if verify_only:' in source
    assert "snapshot_download" in source
