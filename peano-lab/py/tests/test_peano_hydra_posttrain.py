"""Independent Alpha post-training admission and strict benchmark quarantine."""

from __future__ import annotations

from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "scripts"
for import_root in (ROOT, SCRIPTS):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

import prepare_peano_hydra as prepare_script  # noqa: E402
from training.peano_hydra import posttrain  # noqa: E402
from training.peano_hydra.epoch import freeze_epoch  # noqa: E402
from training.peano_policy.config import load_config  # noqa: E402
from training.peano_policy.contract import (  # noqa: E402
    MODEL_V3_HELD_OUT_POLICY_GOALS,
    held_out_contract_sha256,
)
from training.peano_policy.prompt import parse_prompt  # noqa: E402
from training.peano_policy import runtime as training_runtime  # noqa: E402


@pytest.fixture(scope="module")
def prepared_posttraining(tmp_path_factory: pytest.TempPathFactory):
    root = tmp_path_factory.mktemp("hydra-alpha-posttrain")
    source = root / "source"
    output = root / "posttrain"
    epoch, curriculum, manifest = prepare_script.prepare(
        catalog_theorems=("eq_symm", "eq_trans"),
    )
    prepare_script._publish(
        source,
        epoch=epoch,
        curriculum=curriculum,
        manifest=manifest,
        include_graphs=False,
    )
    prepared = posttrain.prepare_posttraining(source, output)
    posttrain.publish_preparation(prepared)
    return prepared


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_rows(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_template_pins_a_fresh_alpha_qwen_adapter_and_never_reuses_model_v3() -> None:
    config = load_config(posttrain.TEMPLATE_PATH)

    assert config.model.model_id == "Qwen/Qwen3-1.7B-Base"
    assert config.model.revision == "ea980cb0a6c2ae4b936e82123acc929f1cec04c1"
    assert config.model.dtype == "bfloat16"
    assert config.model.trust_remote_code is False
    assert config.curriculum is None
    assert config.run.resume == "never"
    assert config.data.max_length == 4096
    assert config.trainer.per_device_train_batch_size == 1
    assert config.trainer.gradient_checkpointing is True
    assert config.trainer.epochs == 1.0
    assert config.trainer.max_steps == -1
    assert config.run.output_dir.startswith("results/peano-hydra/")


def test_independent_handoff_separates_training_development_and_full_quarantine(
    prepared_posttraining,
) -> None:
    prepared = prepared_posttraining
    manifest = prepared.manifest

    assert len(prepared.source.curriculum.transitions) == 29
    assert len(prepared.train_rows) == 11
    assert len(prepared.development_rows) == 5
    assert manifest["held_out"]["quarantine_rows"] == 13
    assert manifest["held_out"]["matched_source_theorems"] == [
        "triangular_product_even_hydra_candidate"
    ]
    assert manifest["splits"]["dev"]["theorems"] == ["eq_symm"]
    assert set(manifest["splits"]["train"]["theorems"]) == {
        "eq_trans",
        "zero_add",
    }
    assert not set(manifest["held_out"]["training_lineages"]) & set(
        manifest["held_out"]["development_lineages"]
    )
    assert not set(manifest["held_out"]["quarantined_lineages"]) & (
        set(manifest["held_out"]["training_lineages"])
        | set(manifest["held_out"]["development_lineages"])
    )


def test_historical_heldout_alias_is_absent_from_both_exposed_splits(
    prepared_posttraining,
) -> None:
    prepared = prepared_posttraining
    held_out = prepared.manifest["held_out"]
    forbidden = set(held_out["excluded_goal_statement_sha256s"])

    assert held_out["historical_v3_contract_sha256"] == held_out_contract_sha256(3)
    assert held_out["excluded_goal_names"] == [
        name for name, _ in MODEL_V3_HELD_OUT_POLICY_GOALS
    ]
    assert held_out["training_contamination_count"] == 0
    assert held_out["development_contamination_count"] == 0
    for row in (*prepared.train_rows, *prepared.development_rows):
        assert row["theorem_statement_sha256"] not in forbidden
        assert row["theorem_name"] not in held_out["excluded_goal_names"]
        for goal in (*row["transition"]["goals_before"], *row["transition"]["goals_after"]):
            canonical = posttrain._goal_target(goal)
            if canonical is not None:
                assert hashlib.sha256(canonical.encode("utf-8")).hexdigest() not in forbidden


def test_intermediate_historical_goal_quarantines_the_complete_lineage(
    prepared_posttraining,
) -> None:
    clean = dict(prepared_posttraining.train_rows[0]["transition"])
    target = posttrain._held_out_targets()[-1][1]
    clean["goals_after"] = [f"⊢ {target}"]

    reasons, matches, _ = posttrain._contamination(
        prepared_posttraining.source.epoch,
        (clean,),
    )

    assert "historical-held-out-proof-goal" in reasons[clean["lineage_sha256"]]
    assert matches[clean["lineage_sha256"]] == {"consecutive_product_even"}


def test_quarantine_and_discovery_evidence_cannot_expose_proof_content(
    prepared_posttraining,
) -> None:
    prepared = prepared_posttraining
    forbidden = {
        "theorem",
        "prompt",
        "completion",
        "action",
        "actions",
        "commands",
        "goals_before",
        "goals_after",
        "transition",
        "trace",
    }

    for name in ("quarantine.jsonl", "discovery.jsonl"):
        for row in _read_rows(prepared.output_directory / name):
            assert not forbidden.intersection(row)
    quarantine = _read_rows(prepared.output_directory / "quarantine.jsonl")
    assert len(quarantine) == 1
    assert quarantine[0]["rows"] == 13
    assert quarantine[0]["matched_goal_names"] == ["consecutive_product_even"]
    discovery = _read_rows(prepared.output_directory / "discovery.jsonl")
    assert discovery[0]["quarantined"] is True
    assert discovery[0]["model_training_exposed"] is False


def test_every_published_file_and_prompt_remains_bound_to_exact_alpha_epoch(
    prepared_posttraining,
) -> None:
    prepared = prepared_posttraining

    assert set(prepared.manifest["files"]) == {
        "train.jsonl",
        "dev.jsonl",
        "preferences.jsonl",
        "discovery.jsonl",
        "quarantine.jsonl",
        "config.toml",
    }
    for name, identity in prepared.manifest["files"].items():
        payload = (prepared.output_directory / name).read_bytes()
        assert identity["sha256"] == hashlib.sha256(payload).hexdigest()
        assert identity["bytes"] == len(payload)
        if name.endswith(".jsonl"):
            assert identity["rows"] == len(payload.splitlines())
    for row in (*prepared.train_rows, *prepared.development_rows):
        parsed = parse_prompt(row["prompt"])
        assert parsed.surface == prepared.source.epoch.surface_label
        assert parsed.goals == tuple(row["transition"]["goals_before"])
        assert row["source_transition_sha256"] == hashlib.sha256(
            json.dumps(
                row["transition"],
                ensure_ascii=False,
                allow_nan=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()


def test_development_is_a_whole_reassigned_source_lineage_not_row_sampling(
    prepared_posttraining,
) -> None:
    development = prepared_posttraining.development_rows

    assert {row["split"] for row in development} == {"dev"}
    assert {row["source_split"] for row in development} == {"train"}
    assert {row["transition"]["split"] for row in development} == {"train"}
    assert len({row["lineage_sha256"] for row in development}) == 1


def test_preferences_are_safe_training_only_and_other_artifacts_are_never_consumed(
    prepared_posttraining,
) -> None:
    prepared = prepared_posttraining
    training = prepared.manifest["training"]
    preferences = _read_rows(prepared.output_directory / "preferences.jsonl")

    assert training["consumed_artifacts"] == ["train.jsonl", "dev.jsonl"]
    assert training["preferences_consumed"] is False
    assert training["discovery_consumed"] is False
    assert training["quarantine_consumed"] is False
    assert training["legacy_attestor_bypassed"] is False
    assert training["independent_alpha_attestation"] is True
    assert preferences[0]["lineage_sha256"] in prepared.manifest["splits"]["train"][
        "lineages"
    ]


def test_dynamic_training_output_is_fresh_and_complete_epoch_digest_is_bound(
    prepared_posttraining,
) -> None:
    prepared = prepared_posttraining
    suffix = f"{prepared.source.epoch.version}-{prepared.source.epoch.epoch_sha256[:12]}"

    assert prepared.config.run.output_dir == (
        f"results/peano-hydra/qwen3-1.7b-alpha-{suffix}"
    )
    assert prepared.manifest["training"]["adapter_output_dir"] == prepared.config.run.output_dir
    assert prepared.manifest["surface_label"] == (
        f"hydra-alpha-{prepared.source.epoch.version}-"
        f"{prepared.source.epoch.edition_identity_sha256}"
    )
    assert prepared.manifest["historical_model_authority"]["frozen_checked_theorem_count"] == 247
    assert prepared.manifest["model_trained"] is False
    assert prepared.manifest["research_claim_eligible"] is False
    assert prepared.manifest["sealed_benchmark"] is False


def test_posttraining_reload_and_preflight_need_no_gpu_or_model_weights(
    prepared_posttraining,
) -> None:
    prepared = prepared_posttraining
    reloaded = posttrain.load_preparation(prepared.output_directory)
    report = posttrain.preflight(prepared.output_directory)

    assert reloaded.manifest == prepared.manifest
    assert report["training_rows"] == 11
    assert report["development_rows"] == 5
    assert report["quarantined_rows"] == 13
    assert report["expected_optimizer_steps"] == 2
    assert report["required_pythonhashseed"] == "20260826"
    assert report["cuda_initialized"] is False
    assert report["model_trained"] is False


def test_python_module_preflight_bootstraps_peano_without_pythonpath(
    prepared_posttraining,
) -> None:
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "training.peano_hydra.posttrain",
            "--preflight",
            "--preparation-dir",
            str(prepared_posttraining.output_directory),
        ],
        cwd=ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["training_rows"] == 11
    assert report["cuda_initialized"] is False


def test_prepare_check_mode_replays_exact_source_without_writing(
    prepared_posttraining,
    tmp_path: Path,
) -> None:
    destination = tmp_path / "unpublished"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "prepare_peano_hydra_posttrain.py"),
            "--source-dir",
            str(prepared_posttraining.source.directory),
            "--output-dir",
            str(destination),
            "--check",
        ],
        cwd=ROOT,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["training_rows"] == 11
    assert not destination.exists()


def test_tampered_handoff_file_is_rejected_before_model_initialization(
    prepared_posttraining,
    tmp_path: Path,
) -> None:
    copied = tmp_path / "tampered"
    shutil.copytree(prepared_posttraining.output_directory, copied)
    with (copied / "train.jsonl").open("ab") as handle:
        handle.write(b"\n")

    with pytest.raises(posttrain.HydraPosttrainError, match="empty|identity|changed"):
        posttrain.load_preparation(copied)


def test_self_forged_source_manifest_cannot_authorize_fake_kernel_boolean(
    prepared_posttraining,
    tmp_path: Path,
) -> None:
    copied = tmp_path / "forged-source"
    shutil.copytree(prepared_posttraining.source.directory, copied)
    rows = _read_rows(copied / "sft.jsonl")
    rows[0]["action"] = "refl"
    rows[0]["completion"] = "refl</tactic>"
    rows[0]["kernel_checked"] = True
    payload = b"".join(
        json.dumps(
            row,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        + b"\n"
        for row in rows
    )
    (copied / "sft.jsonl").write_bytes(payload)
    manifest = _read_json(copied / "manifest.json")
    manifest["files"]["sft.jsonl"] = {
        "rows": len(rows),
        "bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }
    (copied / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(posttrain.HydraPosttrainError, match="independently replayed"):
        posttrain.verify_source(copied)


def test_tampered_epoch_is_not_allowed_to_retarget_an_alpha_adapter(
    prepared_posttraining,
    tmp_path: Path,
) -> None:
    copied = tmp_path / "mixed-release"
    shutil.copytree(prepared_posttraining.source.directory, copied)
    epoch = _read_json(copied / "epoch.json")
    epoch["edition_identity_sha256"] = "0" * 64
    (copied / "epoch.json").write_text(
        json.dumps(epoch, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(posttrain.HydraPosttrainError, match="frozen release"):
        posttrain.verify_source(copied)


def test_pilot_only_corpus_fails_closed_after_heldout_quarantine(
    tmp_path: Path,
) -> None:
    source = tmp_path / "pilot"
    epoch, curriculum, manifest = prepare_script.prepare()
    prepare_script._publish(
        source,
        epoch=epoch,
        curriculum=curriculum,
        manifest=manifest,
        include_graphs=False,
    )

    with pytest.raises(posttrain.HydraPosttrainError, match="two clean checked lineages"):
        posttrain.prepare_posttraining(source, tmp_path / "rejected")


@pytest.mark.parametrize(
    "change",
    [
        lambda config: replace(config, model=replace(config.model, trust_remote_code=True)),
        lambda config: replace(config, data=replace(config.data, max_length=16_384)),
        lambda config: replace(config, trainer=replace(config.trainer, epochs=2.0)),
        lambda config: replace(config, trainer=replace(config.trainer, max_steps=10)),
        lambda config: replace(config, run=replace(config.run, resume="auto")),
        lambda config: replace(
            config,
            run=replace(config.run, output_dir="results/peano-policy/old-adapter"),
        ),
    ],
)
def test_training_configuration_rejects_unbounded_or_historical_adapter_changes(
    prepared_posttraining,
    change,
) -> None:
    with pytest.raises(posttrain.HydraPosttrainError, match="bounded fresh-model"):
        posttrain._validate_model_config(change(prepared_posttraining.config))


def test_actual_execution_requires_explicit_mode_and_preexisting_hash_seed(
    prepared_posttraining,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        posttrain,
        "preflight",
        lambda directory: {"expected_optimizer_steps": 2},
    )
    monkeypatch.setattr(
        posttrain,
        "load_preparation",
        lambda directory: prepared_posttraining,
    )
    monkeypatch.delenv("PYTHONHASHSEED", raising=False)

    with pytest.raises(posttrain.HydraPosttrainError, match="PYTHONHASHSEED=20260826"):
        posttrain.execute(prepared_posttraining.output_directory)


@pytest.fixture
def scheduled_training_runtime(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    for name in (
        "PEANO_BASE_ENV", "PEANO_BASE_MANIFEST", "PEANO_CLUSTER_BACKEND",
        "PEANO_JOB_ENV_SCRIPT", "PEANO_JOB_ENV_SHA256", "PEANO_ML_MODULE",
        "PEANO_REQUIREMENTS_LOCK",
    ):
        monkeypatch.delenv(name, raising=False)
    training = tmp_path / "training" / "peano_policy"
    training.mkdir(parents=True)
    requirements = training / "requirements-helios.lock"
    requirements.write_text(
        "transformers==4.53.3\npackaging==25.0\n"
        'tomli==2.2.1; python_version < "0"\n',
        encoding="utf-8",
    )
    script = tmp_path / "slurm" / "peano_hydra_alpha_train.sbatch"
    script.parent.mkdir()
    script.write_text("#!/bin/bash\ntrue\n", encoding="utf-8")
    source = tmp_path / ".peano-source-provenance.tsv"
    commit = "a" * 40
    synced_at = "2026-08-26T10:11:12Z"
    source.write_text(f"{commit}\tfalse\t{synced_at}\n", encoding="utf-8")
    ledger = tmp_path / "logs" / "submissions.tsv"
    ledger.parent.mkdir()
    ledger.write_text(
        "\t".join(training_runtime.SUBMISSION_FIELDS) + "\n"
        + "\t".join((
            "2026-08-26T10:12:00+00:00", "424242",
            "slurm/peano_hydra_alpha_train.sbatch", "12345", str(tmp_path),
            commit, "false", synced_at,
            hashlib.sha256(script.read_bytes()).hexdigest(),
        )) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(training_runtime, "REPOSITORY_ROOT", tmp_path)
    monkeypatch.setattr(training_runtime, "SOURCE_PROVENANCE_PATH", source)
    monkeypatch.setattr(training_runtime, "SUBMISSION_LEDGER_PATH", ledger)
    monkeypatch.setattr(training_runtime, "REQUIREMENTS_PATH", requirements)
    monkeypatch.setattr(posttrain, "REPOSITORY_ROOT", tmp_path)
    monkeypatch.setenv("SLURM_JOB_ID", "424242")
    monkeypatch.setenv("SLURM_SUBMIT_DIR", str(tmp_path))
    monkeypatch.setenv("PEANO_JOB_SCRIPT", "slurm/peano_hydra_alpha_train.sbatch")
    monkeypatch.setenv("PEANO_HELIOS_ML_MODULE", "ML-bundle/25.10")
    monkeypatch.setenv("LOADEDMODULES", "gcc/13.2.0:ML-bundle/25.10")
    installed = {"transformers": "4.53.3", "packaging": "25.0", "torch": "2.9.1+cu129"}

    def version(name: str) -> str:
        if name not in installed:
            raise training_runtime.importlib.metadata.PackageNotFoundError(name)
        return installed[name]

    monkeypatch.setattr(training_runtime.importlib.metadata, "version", version)
    return SimpleNamespace(
        root=tmp_path, requirements=requirements, script=script,
        source=source, ledger=ledger, installed=installed,
    )


def test_execution_provenance_joins_clean_source_ledger_and_exact_package_pins(
    scheduled_training_runtime,
) -> None:
    provenance = posttrain._execution_provenance()

    assert provenance["job"]["job_id"] == "424242"
    assert provenance["job"]["deployment"] == provenance["deployment"]
    assert provenance["deployment"]["source_sync"]["git_dirty"] is False
    lock = provenance["requirements_verification"]
    assert lock["status"] == "verified"
    assert lock["requirements"] == provenance["runtime"]["requirements"]
    assert lock["packages"] == {"packaging": "25.0", "transformers": "4.53.3"}
    assert lock["packages_sha256"] == posttrain._sha256(posttrain._canonical(lock["packages"]))
    posttrain._require_execution_provenance_unchanged(provenance)


@pytest.mark.parametrize("installed", [None, "4.54.0"])
def test_execution_rejects_missing_or_changed_reviewed_package(
    scheduled_training_runtime,
    installed: str | None,
) -> None:
    packages = scheduled_training_runtime.installed
    if installed is None:
        packages.pop("transformers")
    else:
        packages["transformers"] = installed

    with pytest.raises(posttrain.HydraPosttrainError, match="transformers requires 4.53.3"):
        posttrain._execution_provenance()


def test_runtime_lock_honors_wmi_hashed_overlay_without_imposing_helios_torch(
    scheduled_training_runtime,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime = scheduled_training_runtime
    overlay = runtime.requirements.with_name("requirements-wmi-overlay.lock")
    overlay.write_text(
        "# WMI keeps its separately reviewed central Torch base.\n"
        "transformers==4.53.3 \\\n    --hash=sha256:" + "f" * 64 + "\n",
        encoding="utf-8",
    )
    runtime.installed["torch"] = "2.5.1"
    monkeypatch.delenv("PEANO_HELIOS_ML_MODULE")
    monkeypatch.setenv("PEANO_CLUSTER_BACKEND", "wmi")
    monkeypatch.setenv(
        "PEANO_REQUIREMENTS_LOCK", "training/peano_policy/requirements-wmi-overlay.lock"
    )

    record = posttrain._verify_runtime_lock(training_runtime.runtime_identity())

    assert record["status"] == "verified"
    assert record["requirements"]["path"].endswith("requirements-wmi-overlay.lock")
    assert record["packages"] == {"transformers": "4.53.3"}


@pytest.mark.parametrize("pin", ["transformers>=4.53.3", "transformers==4.53.*"])
def test_runtime_lock_rejects_nonexact_pins(scheduled_training_runtime, pin: str) -> None:
    scheduled_training_runtime.requirements.write_text(pin + "\n", encoding="utf-8")

    with pytest.raises(posttrain.HydraPosttrainError, match="exact package-version pins"):
        posttrain._execution_provenance()


@pytest.mark.parametrize("changed", ["source", "script", "ledger", "runtime", "lock"])
def test_training_publication_rejects_provenance_changes(
    scheduled_training_runtime,
    changed: str,
) -> None:
    fixture = scheduled_training_runtime
    provenance = posttrain._execution_provenance()
    if changed == "source":
        fixture.source.write_text("b" * 40 + "\tfalse\t2026-08-26T10:11:12Z\n", encoding="utf-8")
    elif changed == "script":
        fixture.script.write_text("#!/bin/bash\nfalse\n", encoding="utf-8")
    elif changed == "ledger":
        fixture.ledger.write_text(
            fixture.ledger.read_text(encoding="utf-8").replace("\t12345\t", "\t54321\t"),
            encoding="utf-8",
        )
    elif changed == "runtime":
        fixture.installed["torch"] = "2.9.2+cu129"
    else:
        fixture.requirements.write_text(
            fixture.requirements.read_text(encoding="utf-8") + "# altered lock\n",
            encoding="utf-8",
        )

    with pytest.raises(ValueError, match="does not match|changed during execution"):
        posttrain._require_execution_provenance_unchanged(provenance)


def test_scheduled_training_refuses_a_consistently_dirty_source_and_ledger(
    scheduled_training_runtime,
) -> None:
    for path in (scheduled_training_runtime.source, scheduled_training_runtime.ledger):
        path.write_text(path.read_text(encoding="utf-8").replace("\tfalse\t", "\ttrue\t"), encoding="utf-8")

    with pytest.raises(posttrain.HydraPosttrainError, match="clean committed source"):
        posttrain._execution_provenance()


def test_execution_validates_scheduler_before_importing_model_frameworks(
    scheduled_training_runtime,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PYTHONHASHSEED", "20260826")
    monkeypatch.setattr(posttrain, "preflight", lambda directory: {})
    monkeypatch.setattr(
        posttrain, "load_preparation",
        lambda directory: SimpleNamespace(config=SimpleNamespace(run=SimpleNamespace(seed=20260826))),
    )
    monkeypatch.setattr(
        posttrain, "_required_frameworks",
        lambda: pytest.fail("unrelated scheduler job reached model imports"),
    )
    monkeypatch.setenv("SLURM_JOB_ID", "999999")

    with pytest.raises(ValueError, match="exactly one row for job 999999"):
        posttrain.execute(scheduled_training_runtime.root)


def test_wmi_helper_refuses_to_start_work_without_an_existing_allocation() -> None:
    environment = dict(os.environ)
    environment.pop("SLURM_JOB_ID", None)
    result = subprocess.run(
        ["bash", str(ROOT / "scripts" / "run_wmi_hydra_posttrain.sh")],
        cwd=ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert "existing WMI Slurm allocation" in result.stderr


def test_bridge_never_mutates_the_two_mathematical_dags(prepared_posttraining) -> None:
    before = prepared_posttraining.source.epoch
    after = freeze_epoch(ROOT)

    assert before == after
    assert prepared_posttraining.manifest["theorem_dag_sha256"] == after.theorem_dag_sha256
    assert (
        prepared_posttraining.manifest["reviewed_definition_dag_sha256"]
        == after.reviewed_definition_dag_sha256
    )
