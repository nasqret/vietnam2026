"""Heldout-clean, genuinely matched frozen-Alpha evaluation boundaries."""

from __future__ import annotations

from collections import defaultdict
import hashlib
import json
from pathlib import Path
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
from training.peano_hydra import evaluation  # noqa: E402
from training.peano_hydra.evaluation import (  # noqa: E402
    HydraEvaluationError,
    build_matched_evaluation_plan,
    execute_model_comparison,
    run_symbolic_controls,
)
from training.peano_policy.contract import (  # noqa: E402
    MODEL_V3_HELD_OUT_POLICY_GOALS,
    canonical_held_out_formulas,
    held_out_contract_sha256,
)
from training.peano_policy.prompt import PEANO_PROMPT_V3  # noqa: E402
from training.peano_policy.manifest import artifact_directory_hash  # noqa: E402
from training.peano_policy.objective import (  # noqa: E402
    TRAINER_RUNTIME_FORMAT,
    TRAINER_RUNTIME_VERSION,
    completion_objective_record,
)
from training.peano_policy.search import SearchLimits  # noqa: E402
from training.peano_policy.training_evidence import (  # noqa: E402
    FiniteGradientAudit,
    adapter_update_audit_record,
)


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _jsonl(rows: tuple[dict[str, object], ...]) -> bytes:
    return b"".join(_canonical(row) + b"\n" for row in rows)


def _rewrite_manifest(directory: Path, manifest: dict[str, object]) -> None:
    (directory / "manifest.json").write_bytes(_canonical(manifest) + b"\n")


def _replace_jsonl(
    directory: Path,
    manifest: dict[str, object],
    filename: str,
    rows: tuple[dict[str, object], ...],
) -> None:
    payload = _jsonl(rows)
    (directory / filename).write_bytes(payload)
    manifest["files"][filename] = {
        "bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "rows": len(rows),
    }
    _rewrite_manifest(directory, manifest)


@pytest.fixture(scope="module")
def prepared_data() -> tuple[object, object]:
    epoch, curriculum, _ = prepare_script.prepare(
        catalog_limit=1,
        catalog_theorems=("eq_symm",),
    )
    return epoch, curriculum


@pytest.fixture
def preparation(
    tmp_path: Path,
    prepared_data: tuple[object, object],
) -> tuple[Path, dict[str, object], object]:
    epoch, curriculum = prepared_data
    directory = tmp_path / "hydra-posttrain"
    directory.mkdir()
    canonical_goals = canonical_held_out_formulas(PEANO_PROMPT_V3)
    heldout = frozenset(canonical_goals)
    quarantined = tuple(
        row for row in curriculum.transitions if row["theorem"] in heldout
    )
    assert quarantined
    quarantined_lineages = sorted({row["lineage_sha256"] for row in quarantined})
    allowed = tuple(
        row
        for row in curriculum.transitions
        if row["lineage_sha256"] not in quarantined_lineages
    )
    development_lineage = next(
        row["lineage_sha256"]
        for row in allowed
        if row["theorem_name"] == "eq_symm"
    )
    wrappers: dict[str, list[dict[str, object]]] = {"train": [], "dev": []}
    for transition in allowed:
        split = "dev" if transition["lineage_sha256"] == development_lineage else "train"
        theorem = transition["theorem"]
        wrappers[split].append(
            {
                "schema": evaluation.EXAMPLE_SCHEMA,
                "epoch_sha256": epoch.epoch_sha256,
                "edition_identity_sha256": epoch.edition_identity_sha256,
                "theorem_name": transition["theorem_name"],
                "theorem_statement_sha256": hashlib.sha256(
                    theorem.encode("utf-8")
                ).hexdigest(),
                "lineage_sha256": transition["lineage_sha256"],
                "split": split,
                "source_split": transition["split"],
                "source_transition_sha256": hashlib.sha256(
                    _canonical(transition)
                ).hexdigest(),
                "state_sha256": transition["state_sha256"],
                "action": transition["action"],
                "prompt": transition["prompt"],
                "completion": transition["completion"],
                "environment_sha256": transition["environment_sha256"],
                "kernel_checked": True,
                "transition": transition,
            }
        )
    quarantine: list[dict[str, object]] = []
    groups: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in quarantined:
        groups[(row["theorem_name"], row["lineage_sha256"])].append(row)
    for (name, lineage), rows in sorted(groups.items()):
        matches = [
            goal_name
            for (goal_name, _), formula in zip(
                MODEL_V3_HELD_OUT_POLICY_GOALS,
                canonical_goals,
                strict=True,
            )
            if formula == rows[0]["theorem"]
        ]
        quarantine.append(
            {
                "schema": evaluation.QUARANTINE_SCHEMA,
                "epoch_sha256": epoch.epoch_sha256,
                "theorem_name": name,
                "theorem_statement_sha256": hashlib.sha256(
                    rows[0]["theorem"].encode("utf-8")
                ).hexdigest(),
                "lineage_sha256": lineage,
                "rows": len(rows),
                "matched_goal_names": matches,
                "reasons": ["historical-heldout-canonical-statement"],
            }
        )
    preferences = tuple(
        row
        for row in curriculum.preferences
        if row["lineage_sha256"]
        in {item["lineage_sha256"] for item in wrappers["train"]}
    )
    discovery = tuple(
        {
            "schema": "peano-hydra-posttrain-discovery-summary-v1",
            "epoch_sha256": epoch.epoch_sha256,
            "theorem_name": row["theorem_name"],
            "rows": row["rows"],
        }
        for row in quarantine
    )
    payloads = {
        "train.jsonl": _jsonl(tuple(wrappers["train"])),
        "dev.jsonl": _jsonl(tuple(wrappers["dev"])),
        "preferences.jsonl": _jsonl(preferences),
        "discovery.jsonl": _jsonl(discovery),
        "quarantine.jsonl": _jsonl(tuple(quarantine)),
        "config.toml": evaluation.posttraining_config(epoch, output=directory)[0],
    }
    files: dict[str, dict[str, object]] = {}
    for name, payload in payloads.items():
        (directory / name).write_bytes(payload)
        descriptor: dict[str, object] = {
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
        }
        if name.endswith(".jsonl"):
            descriptor["rows"] = len(payload.splitlines())
        files[name] = descriptor
    splits = {
        split: {
            "rows": len(rows),
            "lineages": sorted({row["lineage_sha256"] for row in rows}),
            "theorems": sorted({row["theorem_name"] for row in rows}),
        }
        for split, rows in wrappers.items()
    }
    manifest = {
        "schema": evaluation.PREPARATION_SCHEMA,
        "epoch_sha256": epoch.epoch_sha256,
        "edition_identity_sha256": epoch.edition_identity_sha256,
        "theorem_dag_sha256": epoch.theorem_dag_sha256,
        "reviewed_definition_dag_sha256": epoch.reviewed_definition_dag_sha256,
        "surface_label": epoch.surface_label,
        "version": epoch.version,
        "model": {
            "model_id": evaluation.EXPECTED_BASE_MODEL_ID,
            "revision": evaluation.EXPECTED_BASE_MODEL_REVISION,
        },
        "files": files,
        "splits": splits,
        "held_out": {
            "historical_v3_contract_sha256": held_out_contract_sha256(PEANO_PROMPT_V3),
            "excluded_goal_names": [name for name, _ in MODEL_V3_HELD_OUT_POLICY_GOALS],
            "excluded_goal_statement_sha256s": [
                hashlib.sha256(formula.encode("utf-8")).hexdigest()
                for formula in canonical_goals
            ],
            "training_contamination_count": 0,
            "development_contamination_count": 0,
            "training_lineages": splits["train"]["lineages"],
            "development_lineages": splits["dev"]["lineages"],
            "matched_source_theorems": sorted({row["theorem_name"] for row in quarantine}),
            "quarantined_lineages": quarantined_lineages,
            "quarantine_rows": len(quarantined),
        },
        "research_claim_eligible": False,
        "model_trained": False,
        "alpha_admitted": False,
        "sealed_benchmark": False,
    }
    _rewrite_manifest(directory, manifest)
    return directory, manifest, epoch


def _adapter(
    tmp_path: Path,
    plan: object,
    *,
    mutate: dict[str, object] | None = None,
) -> Path:
    root = tmp_path / "trained-alpha-adapter"
    root.mkdir()
    adapter_directory = root / "adapter"
    tokenizer_directory = root / "tokenizer"
    adapter_directory.mkdir()
    tokenizer_directory.mkdir()
    payloads = {
        "adapter_config.json": b'{"peft_type":"LORA"}\n',
        "adapter_model.safetensors": b"bounded-fake-safetensors-for-mocked-runtime",
    }
    for name, payload in payloads.items():
        (adapter_directory / name).write_bytes(payload)
    (tokenizer_directory / "tokenizer.json").write_bytes(b"{}\n")
    preparation = json.loads(
        (plan.preparation_directory / "manifest.json").read_text(encoding="utf-8")
    )
    # CPU-only fixtures exercise the actual trainer record format without
    # pretending that these deliberately fake weights came from model work.
    _, config = evaluation.posttraining_config(plan.epoch, output=plan.preparation_directory)
    train_rows = preparation["splits"]["train"]["rows"]
    dev_rows = preparation["splits"]["dev"]["rows"]
    accumulation = config.trainer.gradient_accumulation_steps
    steps = (train_rows + accumulation - 1) // accumulation
    names = ("test.lora_A.default.weight", "test.lora_B.default.weight")
    gradients = FiniteGradientAudit(
        expected_optimizer_steps=steps,
        trainable_parameter_names=names,
    )
    for step in range(steps):
        gradients.observe_pre_optimizer_step(
            trainer_state_global_step=step,
            raw_finite_gradient_parameter_names=names,
            pre_clip_global_norm=0.1,
            post_clip_finite_gradient_parameter_names=names,
        )
    from packaging.requirements import Requirement
    from packaging.utils import canonicalize_name

    requirements_path = Path("training/peano_policy/requirements-helios.lock")
    requirements_raw = (ROOT / requirements_path).read_bytes()
    packages = {}
    for line in requirements_raw.decode("utf-8").splitlines():
        line = line.partition("#")[0].strip()
        if not line:
            continue
        requirement = Requirement(line)
        if requirement.marker is None or requirement.marker.evaluate({"python_version": "3.11"}):
            packages[canonicalize_name(requirement.name)] = tuple(requirement.specifier)[0].version
    requirements = {
        "path": requirements_path.as_posix(),
        "sha256": hashlib.sha256(requirements_raw).hexdigest(),
    }
    deployment = {
        "mode": "local",
        "source_sync": {"status": "not-synced"},
        "job_script": {"status": "not-declared"},
        "modules": {"status": "not-loaded"},
    }
    record = {
        "schema": evaluation.ADAPTER_SCHEMA,
        "version": plan.epoch.version,
        "epoch_sha256": plan.epoch.epoch_sha256,
        "edition_identity_sha256": plan.epoch.edition_identity_sha256,
        "theorem_dag_sha256": plan.epoch.theorem_dag_sha256,
        "reviewed_definition_dag_sha256": plan.epoch.reviewed_definition_dag_sha256,
        "surface_label": plan.epoch.surface_label,
        "preparation_manifest_sha256": plan.preparation_manifest_sha256,
        "preparation": {
            "manifest_sha256": plan.preparation_manifest_sha256,
            "files": preparation["files"],
        },
        "held_out": preparation["held_out"],
        "model_trained": True,
        "model": dict(plan.model),
        "adapter": artifact_directory_hash(root, "adapter"),
        "tokenizer": artifact_directory_hash(root, "tokenizer"),
        "objective": completion_objective_record(),
        "finite_gradient_audit": gradients.record(),
        "adapter_update": adapter_update_audit_record(
            trainable_parameter_names=names,
            initial_tensor_population_sha256="1" * 64,
            final_tensor_population_sha256="2" * 64,
            changed_parameter_names=names,
            final_finite_parameter_names=names,
        ),
        "trainer_runtime": {
            "format": TRAINER_RUNTIME_FORMAT,
            "v": TRAINER_RUNTIME_VERSION,
            "num_processes": 1,
            "visible_gpus": 1,
            "device": {"type": "cuda", "index": 0},
            "mixed_precision": "bf16",
            "distributed_type": {"name": "NO", "value": "NO"},
            "dynamo_backend": {"name": "NO", "value": "NO"},
            "plugins": {"deepspeed": False, "fsdp": False, "tensor_parallel": False},
            "manual_trainer_accumulation": True,
            "configured_trainer_gradient_accumulation_steps": accumulation,
            "accelerator_backward_divisor": 1,
        },
        "runtime": {
            "implementation": "CPython",
            "python": "3.11.5",
            "machine": "aarch64",
            "platform": "Linux-test-fixture",
            "hostname": "test-only-no-model-loaded",
            "packages": packages,
            "packages_sha256": hashlib.sha256(_canonical(packages)).hexdigest(),
            "requirements": requirements,
            "accelerator": {
                "torch": packages["torch"],
                "cuda_available": True,
                "bf16_supported": True,
            },
        },
        "deployment": deployment,
        "job": {"scheduler": "none", "deployment": deployment},
        "requirements_verification": {
            "schema": evaluation.RUNTIME_LOCK_SCHEMA,
            "status": "not-required-local",
            "requirements": requirements,
        },
        "metrics": {
            "expected_optimizer_steps": steps,
            "actual_optimizer_steps": steps,
            "training_rows": train_rows,
            "development_rows": dev_rows,
            "train": {"train_loss": 0.5},
            "dev": {"eval_loss": 0.6},
        },
        "research_claim_eligible": False,
        "alpha_admitted": False,
        "sealed_benchmark": False,
    }
    if mutate:
        record.update(mutate)
    (root / "manifest.json").write_bytes(_canonical(record) + b"\n")
    return root


def test_matched_plan_binds_one_alpha_epoch_and_identical_base_and_budget(
    preparation: tuple[Path, dict[str, object], object],
) -> None:
    directory, _, epoch = preparation
    plan = build_matched_evaluation_plan(directory)
    report = plan.to_dict()
    pretrained = report["lanes"]["pretrained"]
    trained = report["lanes"]["trained"]

    assert report["schema"] == evaluation.EVALUATION_SCHEMA
    assert report["epoch_sha256"] == epoch.epoch_sha256
    assert report["edition_identity_sha256"] == epoch.edition_identity_sha256
    assert report["theorem_dag_sha256"] == epoch.theorem_dag_sha256
    assert report["reviewed_definition_dag_sha256"] == epoch.reviewed_definition_dag_sha256
    for field in (
        "epoch_sha256",
        "surface_label",
        "environment_sha256",
        "goal_set_sha256",
        "model",
        "matched_budget",
        "theorem_authority",
    ):
        assert pretrained[field] == trained[field]
    assert report["theorem_authority"]["allowed_theorems"] == []
    assert report["theorem_authority"]["allowed_theorem_count"] == 0
    assert report["comparison"]["status"] == "unmeasured"
    assert report["comparison"]["model_metrics"] is None
    assert trained["status"] == "unavailable"
    assert report["research_claim_eligible"] is False


def test_historical_alias_and_entire_teacher_lineage_are_quarantined(
    preparation: tuple[Path, dict[str, object], object],
) -> None:
    directory, _, _ = preparation
    report = build_matched_evaluation_plan(directory).to_dict()

    assert len(report["goals"]) == 4
    assert report["held_out"]["matched_source_theorems"] == [
        "triangular_product_even_hydra_candidate"
    ]
    assert report["held_out"]["quarantine_rows"] == 13
    assert report["held_out"]["training_contamination_count"] == 0
    assert report["held_out"]["development_contamination_count"] == 0
    assert not set(report["held_out"]["quarantined_lineages"]) & set(
        report["held_out"]["split_lineages"]["train"]
    )
    assert not set(report["held_out"]["quarantined_lineages"]) & set(
        report["held_out"]["split_lineages"]["dev"]
    )


def test_model_free_planning_never_enters_the_cuda_loader(
    preparation: tuple[Path, dict[str, object], object],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    directory, _, _ = preparation

    def forbidden() -> None:
        raise AssertionError("model-free planning must never inspect/load a GPU runtime")

    monkeypatch.setattr(evaluation, "_model_runtime", forbidden)
    assert build_matched_evaluation_plan(directory).to_dict()["comparison"]["status"] == (
        "unmeasured"
    )


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("epoch_sha256", "0" * 64),
        ("edition_identity_sha256", "1" * 64),
        ("theorem_dag_sha256", "2" * 64),
        ("reviewed_definition_dag_sha256", "3" * 64),
        ("surface_label", "ordinary-stable-only"),
    ),
)
def test_evaluation_rejects_every_mismatched_frozen_epoch_identity(
    preparation: tuple[Path, dict[str, object], object],
    field: str,
    value: str,
) -> None:
    directory, manifest, _ = preparation
    manifest[field] = value
    _rewrite_manifest(directory, manifest)

    with pytest.raises(HydraEvaluationError, match="exact frozen Alpha epoch"):
        build_matched_evaluation_plan(directory)


def test_evaluation_rejects_changed_prepared_file_bytes(
    preparation: tuple[Path, dict[str, object], object],
) -> None:
    directory, _, _ = preparation
    path = directory / "train.jsonl"
    path.write_bytes(path.read_bytes() + b" ")

    with pytest.raises(HydraEvaluationError, match="changed from its exact prepared bytes"):
        build_matched_evaluation_plan(directory)


def test_evaluation_rejects_nonmatching_qwen_base_revision(
    preparation: tuple[Path, dict[str, object], object],
) -> None:
    directory, manifest, _ = preparation
    manifest["model"]["revision"] = "a" * 40
    _rewrite_manifest(directory, manifest)

    with pytest.raises(HydraEvaluationError, match="identical pinned Qwen base revision"):
        build_matched_evaluation_plan(directory)


def test_evaluation_rejects_hidden_heldout_contract_changes(
    preparation: tuple[Path, dict[str, object], object],
) -> None:
    directory, manifest, _ = preparation
    manifest["held_out"]["excluded_goal_names"] = manifest["held_out"][
        "excluded_goal_names"
    ][:-1]
    _rewrite_manifest(directory, manifest)

    with pytest.raises(HydraEvaluationError, match="historical held-out contract"):
        build_matched_evaluation_plan(directory)


def test_quarantine_artifacts_can_never_leak_a_historical_proof(
    preparation: tuple[Path, dict[str, object], object],
) -> None:
    directory, manifest, _ = preparation
    rows = tuple(
        json.loads(line)
        for line in (directory / "quarantine.jsonl").read_text().splitlines()
    )
    rows[0]["commands"] = ["induction n", "simp"]
    _replace_jsonl(directory, manifest, "quarantine.jsonl", rows)

    with pytest.raises(HydraEvaluationError, match="exposed held-out proof"):
        build_matched_evaluation_plan(directory)


def test_wrapped_transitions_cannot_change_their_checked_source_authority(
    preparation: tuple[Path, dict[str, object], object],
) -> None:
    directory, manifest, _ = preparation
    rows = tuple(
        json.loads(line)
        for line in (directory / "train.jsonl").read_text().splitlines()
    )
    rows[0]["action"] = "norm_num"
    _replace_jsonl(directory, manifest, "train.jsonl", rows)

    with pytest.raises(HydraEvaluationError, match="exact checked transition fields"):
        build_matched_evaluation_plan(directory)


def test_matched_search_reservations_are_bounded_before_model_loading(
    preparation: tuple[Path, dict[str, object], object],
) -> None:
    directory, _, _ = preparation
    with pytest.raises(HydraEvaluationError, match="candidates_per_state"):
        build_matched_evaluation_plan(
            directory,
            limits=SearchLimits(candidates_per_state=9),
        )
    with pytest.raises(HydraEvaluationError, match="max_new_tokens"):
        build_matched_evaluation_plan(directory, max_new_tokens=129)


def test_symbolic_controls_are_independently_checked_and_never_model_metrics(
    preparation: tuple[Path, dict[str, object], object],
) -> None:
    directory, _, _ = preparation
    plan = build_matched_evaluation_plan(
        directory,
        limits=SearchLimits(
            max_depth=4,
            beam_width=2,
            candidates_per_state=4,
            max_model_calls=8,
            max_states=16,
        ),
    )
    controls = run_symbolic_controls(plan)

    assert controls["status"] == "executed"
    assert controls["model_generated"] is False
    assert controls["research_claim_eligible"] is False
    assert len(controls["goals"]) == 4
    assert controls["kernel_checked_proofs"] >= 1
    assert all(item["model_calls"] == 0 for item in controls["goals"])
    assert plan.to_dict()["comparison"]["model_metrics"] is None


def test_actual_model_execution_requires_an_exact_completed_alpha_adapter(
    preparation: tuple[Path, dict[str, object], object],
    tmp_path: Path,
) -> None:
    directory, _, _ = preparation
    plan = build_matched_evaluation_plan(directory)
    with pytest.raises(HydraEvaluationError, match="completed trained Alpha adapter"):
        execute_model_comparison(plan)

    incompatible = _adapter(tmp_path, plan, mutate={"epoch_sha256": "0" * 64})
    with pytest.raises(HydraEvaluationError, match="exact frozen epoch"):
        build_matched_evaluation_plan(directory, trained_adapter=incompatible)


@pytest.mark.parametrize(
    "field",
    (
        "objective", "finite_gradient_audit", "adapter_update", "trainer_runtime",
        "runtime", "deployment", "job", "requirements_verification",
    ),
)
def test_adapter_requires_actual_complete_training_evidence(
    preparation: tuple[Path, dict[str, object], object],
    tmp_path: Path,
    field: str,
) -> None:
    directory, _, _ = preparation
    plan = build_matched_evaluation_plan(directory)
    adapter = _adapter(tmp_path, plan, mutate={field: None})

    with pytest.raises(HydraEvaluationError, match="evidence|provenance|runtime"):
        build_matched_evaluation_plan(directory, trained_adapter=adapter)


@pytest.mark.parametrize(
    "mutation",
    (
        "matching-but-wrong-steps",
        "boolean-step",
        "float-step",
        "wrong-training-rows",
        "wrong-development-rows",
        "missing-training-loss",
        "missing-development-loss",
        "nonfinite-development-loss",
        "incomplete-gradient-boundaries",
        "changed-gradient-record",
        "unchanged-adapter",
        "wrong-accumulation",
    ),
)
def test_adapter_rejects_inconsistent_steps_metrics_and_optimizer_evidence(
    preparation: tuple[Path, dict[str, object], object],
    tmp_path: Path,
    mutation: str,
) -> None:
    directory, _, _ = preparation
    plan = build_matched_evaluation_plan(directory)
    adapter = _adapter(tmp_path, plan)
    manifest_path = adapter / "manifest.json"
    record = json.loads(manifest_path.read_text(encoding="utf-8"))
    metrics = record["metrics"]
    if mutation == "matching-but-wrong-steps":
        metrics["expected_optimizer_steps"] += 1
        metrics["actual_optimizer_steps"] = metrics["expected_optimizer_steps"]
    elif mutation == "boolean-step":
        metrics["actual_optimizer_steps"] = True
    elif mutation == "float-step":
        metrics["actual_optimizer_steps"] = float(metrics["expected_optimizer_steps"])
    elif mutation == "wrong-training-rows":
        metrics["training_rows"] = 1
    elif mutation == "wrong-development-rows":
        metrics["development_rows"] += 1
    elif mutation == "missing-training-loss":
        metrics["train"] = {}
    elif mutation == "missing-development-loss":
        metrics["dev"] = {}
    elif mutation == "nonfinite-development-loss":
        metrics["dev"]["eval_loss"] = "NaN"
    elif mutation == "incomplete-gradient-boundaries":
        record["finite_gradient_audit"]["observed_optimizer_boundaries"] -= 1
    elif mutation == "changed-gradient-record":
        record["finite_gradient_audit"]["records"][0]["pre_clip_global_norm"] = 9.0
    elif mutation == "unchanged-adapter":
        update = record["adapter_update"]
        update["final_tensor_population_sha256"] = update["initial_tensor_population_sha256"]
    elif mutation == "wrong-accumulation":
        record["trainer_runtime"]["configured_trainer_gradient_accumulation_steps"] += 1
    _rewrite_manifest(adapter, record)

    with pytest.raises(HydraEvaluationError):
        build_matched_evaluation_plan(directory, trained_adapter=adapter)


@pytest.mark.parametrize(
    "mutation",
    ("none", "unverified-lock", "incomplete-lock", "dirty-source", "wrong-job", "stale-ledger", "package-drift"),
)
def test_saved_scheduled_runtime_is_validated_without_local_gpu_or_scheduler(
    preparation: tuple[Path, dict[str, object], object],
    tmp_path: Path,
    mutation: str,
) -> None:
    directory, _, _ = preparation
    plan = build_matched_evaluation_plan(directory)
    adapter = _adapter(tmp_path, plan)
    record = json.loads((adapter / "manifest.json").read_text(encoding="utf-8"))
    deployment = {
        "mode": "slurm",
        "source_sync": {
            "status": "synced",
            "path": ".peano-source-provenance.tsv",
            "sha256": "1" * 64,
            "git_commit": "a" * 40,
            "git_dirty": False,
            "synced_at": "2026-08-26T12:00:00Z",
        },
        "job_script": {
            "status": "declared",
            "path": "slurm/peano_hydra_alpha_train.sbatch",
            "sha256": "2" * 64,
        },
    }
    submission = {
        "job_id": "12345",
        "git_commit": deployment["source_sync"]["git_commit"],
        "git_dirty": "false",
        "sync_timestamp": deployment["source_sync"]["synced_at"],
        "script": deployment["job_script"]["path"],
        "script_sha256": deployment["job_script"]["sha256"],
    }
    record["deployment"] = deployment
    record["job"] = {
        "scheduler": "slurm",
        "job_id": "12345",
        "deployment": deployment,
        "submission": submission,
        "ledger": {
            "path": "logs/submissions.tsv",
            "row_sha256": hashlib.sha256(_canonical(submission)).hexdigest(),
        },
    }
    lock = record["requirements_verification"]
    lock["status"] = "verified"
    lock["packages"] = dict(record["runtime"]["packages"])
    lock["packages_sha256"] = hashlib.sha256(_canonical(lock["packages"])).hexdigest()
    if mutation == "unverified-lock":
        lock["status"] = "not-required-local"
    elif mutation == "incomplete-lock":
        lock["packages"].pop("transformers")
        lock["packages_sha256"] = hashlib.sha256(_canonical(lock["packages"])).hexdigest()
    elif mutation == "dirty-source":
        deployment["source_sync"]["git_dirty"] = True
    elif mutation == "wrong-job":
        record["job"]["job_id"] = "54321"
    elif mutation == "stale-ledger":
        record["job"]["ledger"]["row_sha256"] = "0" * 64
    elif mutation == "package-drift":
        record["runtime"]["packages"]["transformers"] = "99.0.0"
        record["runtime"]["packages_sha256"] = hashlib.sha256(_canonical(record["runtime"]["packages"])).hexdigest()
    _rewrite_manifest(adapter, record)

    if mutation == "none":
        assert build_matched_evaluation_plan(directory, trained_adapter=adapter).trained_adapter
    else:
        with pytest.raises(HydraEvaluationError):
            build_matched_evaluation_plan(directory, trained_adapter=adapter)


@pytest.mark.parametrize("lane", ("pretrained", "trained"))
def test_model_lane_retains_bounded_independently_replayable_proposal_receipts(
    preparation: tuple[Path, dict[str, object], object],
    monkeypatch: pytest.MonkeyPatch,
    lane: str,
) -> None:
    from peano_lab.batch import run_proof
    from training.peano_policy import generate

    directory, _, _ = preparation
    plan = build_matched_evaluation_plan(
        directory,
        limits=SearchLimits(
            max_depth=4,
            beam_width=2,
            candidates_per_state=4,
            max_model_calls=8,
            max_states=16,
        ),
    )
    monkeypatch.setattr(
        generate,
        "generate_tactic_candidates",
        lambda **kwargs: ("norm_num", "simp", "intro n", "exists 5"),
    )
    result = evaluation._run_model_lane(
        plan,
        model=object(),
        tokenizer=object(),
        lane=lane,
        provider={"kind": "explicitly-mocked-test-generator", "research_claim_eligible": False},
    )
    assert result["kernel_checked_proofs"] == 3
    total_bytes = 0
    for goal, row in zip(plan.goals, result["goals"], strict=True):
        evidence = row["evidence"]
        encoded = _canonical(evidence)
        total_bytes += len(encoded)
        assert row["evidence_sha256"] == hashlib.sha256(encoded).hexdigest()
        assert len(encoded) <= evaluation.MAX_GOAL_EVIDENCE_BYTES
        assert len(evidence["proposal_records"]) == row["model_generate_calls"]
        commands = evidence["search"]["commands"]
        if row["kernel_checked"]:
            replay = run_proof(goal["source"], commands, capabilities=plan.capabilities)
            assert replay.kernel_checked
            assert replay.theorem == goal["statement"]
            assert replay.proof_nodes == row["proof_nodes"]
            assert row["commands_sha256"] == hashlib.sha256(_canonical(commands)).hexdigest()
            assert evidence["replay"] is not None
        else:
            assert commands == []
            assert evidence["replay"] is None
    assert total_bytes == result["retained_evidence_bytes"]
    assert total_bytes <= evaluation.MAX_LANE_EVIDENCE_BYTES

    monkeypatch.setattr(evaluation, "MAX_GOAL_EVIDENCE_BYTES", 1)
    with pytest.raises(HydraEvaluationError, match="retained-byte bound"):
        evaluation._run_model_lane(
            plan,
            model=object(),
            tokenizer=object(),
            lane=lane,
            provider={"kind": "explicitly-mocked-test-generator"},
        )


def test_real_execution_loads_pretrained_and_lora_sequentially_with_one_gpu(
    preparation: tuple[Path, dict[str, object], object],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    directory, _, _ = preparation
    initial = build_matched_evaluation_plan(directory)
    adapter = _adapter(tmp_path, initial)
    plan = build_matched_evaluation_plan(directory, trained_adapter=adapter)
    assert type(plan.trained_adapter["training_evidence"]["actual_optimizer_steps"]) is int
    assert plan.trained_adapter["training_evidence"]["actual_optimizer_steps"] >= 1
    events: list[str] = []

    class FakeModel:
        def __init__(self) -> None:
            self.config = SimpleNamespace(_commit_hash=plan.model["revision"])

        def to(self, device: str) -> None:
            assert device == "cuda:0"
            events.append("model-to-gpu")

        def eval(self) -> None:
            events.append("model-eval")

    class FakeCUDA:
        def manual_seed_all(self, seed: int) -> None:
            del seed

        def empty_cache(self) -> None:
            events.append("gpu-release")

        def synchronize(self) -> None:
            events.append("gpu-synchronize")

        def get_device_name(self, index: int) -> str:
            assert index == 0
            return "fake-one-cuda-gpu"

    tokenizer = SimpleNamespace(pad_token_id=0, eos_token_id=1)
    torch = SimpleNamespace(
        __version__="fake-torch",
        bfloat16="bf16",
        cuda=FakeCUDA(),
        manual_seed=lambda seed: None,
    )
    transformers = SimpleNamespace(
        __version__="fake-transformers",
        set_seed=lambda seed: None,
        AutoTokenizer=SimpleNamespace(
            from_pretrained=lambda *args, **kwargs: tokenizer
        ),
    )
    peft = SimpleNamespace(
        __version__="fake-peft",
        PeftModel=SimpleNamespace(
            from_pretrained=lambda model, path, **kwargs: (
                events.append("attach-lora") or model
            )
        ),
    )
    monkeypatch.setattr(evaluation, "_model_runtime", lambda: (torch, transformers, peft))
    monkeypatch.setattr(
        evaluation,
        "_load_base_model",
        lambda *args: events.append("load-base") or FakeModel(),
    )

    def run_lane(
        current: object,
        *,
        model: object,
        tokenizer: object,
        lane: str,
        provider: dict[str, object],
    ) -> dict[str, object]:
        del model, tokenizer, provider
        assert current is plan
        events.append(f"run-{lane}")
        solved = 1 if lane == "pretrained" else 2
        return {
            "status": "executed",
            "lane": lane,
            "model": dict(plan.model),
            "epoch_sha256": plan.epoch.epoch_sha256,
            "environment_sha256": plan.environment["environment_sha256"],
            "goal_set_sha256": plan.goal_set_sha256,
            "matched_budget": plan.matched_budget,
            "kernel_checked_proofs": solved,
            "model_generate_calls": 4,
        }

    monkeypatch.setattr(evaluation, "_run_model_lane", run_lane)
    report = execute_model_comparison(plan)

    assert events.count("load-base") == 2
    assert events.count("attach-lora") == 1
    assert events.index("run-pretrained") < events.index("gpu-release")
    assert events.index("gpu-release") < events.index("attach-lora")
    assert events.index("attach-lora") < events.index("run-trained")
    assert report["model_metrics"]["pretrained_kernel_checked_proofs"] == 1
    assert report["model_metrics"]["trained_kernel_checked_proofs"] == 2
    assert report["model_metrics"]["kernel_checked_proof_delta"] == 1
    assert report["research_claim_eligible"] is False


def test_execution_rejects_mutated_safetensors_before_gpu_loading(
    preparation: tuple[Path, dict[str, object], object],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    directory, _, _ = preparation
    initial = build_matched_evaluation_plan(directory)
    adapter = _adapter(tmp_path, initial)
    plan = build_matched_evaluation_plan(directory, trained_adapter=adapter)
    (adapter / "adapter" / "adapter_model.safetensors").write_bytes(
        b"replaced-after-planning"
    )
    monkeypatch.setattr(
        evaluation,
        "_model_runtime",
        lambda: (_ for _ in ()).throw(AssertionError("GPU must not load")),
    )

    with pytest.raises(HydraEvaluationError, match="exact saved bytes"):
        execute_model_comparison(plan)


def test_cli_check_is_deterministic_and_never_writes_or_executes_models(
    preparation: tuple[Path, dict[str, object], object],
) -> None:
    directory, _, _ = preparation
    command = [
        sys.executable,
        str(ROOT / "scripts" / "eval_peano_hydra_posttrain.py"),
        "--preparation-dir",
        str(directory),
        "--check",
    ]
    first = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=True)
    second = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=True)

    assert first.stdout == second.stdout
    assert json.loads(first.stdout)["comparison"]["status"] == "unmeasured"
    assert len(tuple(directory.iterdir())) == 7


def test_cli_requires_explicit_adapter_for_real_gpu_execution(
    preparation: tuple[Path, dict[str, object], object],
) -> None:
    directory, _, _ = preparation
    command = [
        sys.executable,
        str(ROOT / "scripts" / "eval_peano_hydra_posttrain.py"),
        "--preparation-dir",
        str(directory),
        "--execute-models",
    ]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)

    assert result.returncode == 2
    assert "requires explicit --trained-adapter PATH" in result.stderr
