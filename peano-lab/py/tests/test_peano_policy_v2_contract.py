"""The overnight policy prompt is versioned, retrieved, and fail-closed."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import random
import sys

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from peano_lab.batch import capability_sha256, run_proof
from peano_lab.library.theorems import THEOREMS
from peano_lab.ui.prove import SurfaceCapabilities
from training.peano_policy.contract import (
    EXCLUDED_POLICY_LIBRARY_NAMES,
    HELD_OUT_POLICY_NAMES,
    attested_training_environment,
    environment_record,
    held_out_contract_record,
    held_out_contract_sha256,
    model_v2_environment,
)
import training.peano_policy.generate as generation
from training.peano_policy.attest import attest_dataset
from training.peano_policy.data import example_from_record
from training.peano_policy.prompt import (
    PEANO_PROMPT_V1,
    PEANO_PROMPT_V2,
    V2_RETRIEVAL_K,
    V2_TACTIC_GRAMMAR,
    CapabilityIdentity,
    PromptEnvironment,
    PromptError,
    library_snapshot_sha256,
    parse_prompt,
    prompt_contract_sha256,
    prompt_manifest_record,
    render_prompt,
    retrieve_theorems,
)
from training.peano_policy.library_identity import (
    LIBRARY_IDENTITY_FORMAT,
    LIBRARY_IDENTITY_VERSION,
    model_v2_library_identity_sha256,
)


def _load_builder() -> object:
    path = REPOSITORY_ROOT / "scripts" / "build_peano_policy_dataset.py"
    spec = importlib.util.spec_from_file_location("_test_v2_dataset_builder", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _v2_training_manifest() -> dict[str, object]:
    environment = model_v2_environment()
    train_hash = "1" * 64
    val_hash = "2" * 64
    manifest_hash = "3" * 64
    attestation = {
        "format": "peano-policy-dataset-attestation",
        "v": 1,
        "independent_replay": True,
        "held_out_contamination": 0,
        "held_out_contract": held_out_contract_record(),
        "held_out_contract_sha256": held_out_contract_sha256(),
        "environment": environment_record(environment),
        "prompt_version": PEANO_PROMPT_V2,
        "prompt_contract": prompt_manifest_record(PEANO_PROMPT_V2),
        "prompt_contract_sha256": prompt_contract_sha256(PEANO_PROMPT_V2),
        "library_snapshot_sha256": environment.library_sha256,
        "manifest_sha256": manifest_hash,
        "splits": {
            "train": {"rows": 1, "sha256": train_hash},
            "val": {"rows": 1, "sha256": val_hash},
            "test": {"rows": 0, "sha256": "4" * 64},
        },
    }
    return {
        "prompt_version": PEANO_PROMPT_V2,
        "prompt_contract_sha256": prompt_contract_sha256(PEANO_PROMPT_V2),
        "inputs": {
            "dataset_attestation": attestation,
            "train_data": {"sha256": train_hash},
            "eval_data": {"sha256": val_hash},
            "train_dataset_manifest": {"sha256": manifest_hash},
            "eval_dataset_manifest": {"sha256": manifest_hash},
        },
    }


def test_model_v2_remains_the_exact_published_56_theorem_authority() -> None:
    environment = model_v2_environment()
    public_names = {spec.name for spec in THEOREMS}
    allowed = set(environment.capabilities.allowed_theorems or ())

    assert environment.prompt_version == PEANO_PROMPT_V2
    assert allowed == public_names - EXCLUDED_POLICY_LIBRARY_NAMES
    assert allowed.isdisjoint(EXCLUDED_POLICY_LIBRARY_NAMES)
    assert HELD_OUT_POLICY_NAMES < EXCLUDED_POLICY_LIBRARY_NAMES
    assert len(EXCLUDED_POLICY_LIBRARY_NAMES) == len(THEOREMS) - 56
    assert len(allowed) == 56
    assert tuple(record.name for record in environment.library) == tuple(
        sorted(allowed)
    )
    assert environment.library_sha256 == model_v2_library_identity_sha256()
    assert environment.library_statement_sha256 == library_snapshot_sha256(
        environment.library
    )
    assert environment.library_sha256 != environment.library_statement_sha256
    assert environment_record(environment)["library_identity_sha256"] == (
        environment.library_sha256
    )


def test_v2_retrieval_is_bounded_deterministic_relevant_and_permitted() -> None:
    environment = model_v2_environment()
    goals = ("⊢ ∀ n. 0 + n = n",)

    first = retrieve_theorems(goals=goals, focus=0, environment=environment)
    second = retrieve_theorems(goals=goals, focus=0, environment=environment)

    assert first == second
    assert len(first) == V2_RETRIEVAL_K
    assert first[0].name == "zero_add"
    assert {record.name for record in first}.isdisjoint(
        EXCLUDED_POLICY_LIBRARY_NAMES
    )
    assert all(
        record.name in (environment.capabilities.allowed_theorems or ())
        for record in first
    )


def test_v2_prompt_round_trips_with_exact_grammar_and_snapshot_provenance() -> None:
    environment = model_v2_environment()
    goals = (
        "Variables\n  n : ℕ\nContext\n  h : 0 + n = n\nTarget\n  n = n",
        "⊢ 0 = 0",
    )
    prompt = render_prompt(goals=goals, focus=0, environment=environment)
    parsed = parse_prompt(prompt)

    assert parsed.prompt_version == PEANO_PROMPT_V2
    assert parsed.goals == goals
    assert parsed.focus == 0
    assert parsed.environment == environment.text
    assert parsed.prompt_contract_sha256 == prompt_contract_sha256(PEANO_PROMPT_V2)
    assert parsed.library_sha256 == environment.library_sha256
    assert f"<grammar>{V2_TACTIC_GRAMMAR}</grammar>" in prompt
    assert render_prompt(goals=parsed.goals, focus=parsed.focus, environment=environment) == prompt


def test_builder_and_inference_render_the_identical_v2_prompt(monkeypatch: pytest.MonkeyPatch) -> None:
    builder = _load_builder()
    environment = model_v2_environment()
    capabilities = SurfaceCapabilities(
        label="model-v2",
        allowed_commands=frozenset(environment.capabilities.allowed_commands or ()),
        allowed_theorems=frozenset(environment.capabilities.allowed_theorems or ()),
    )
    goals = ("⊢ ∀ n. 0 + n = n",)
    env_text, builder_prompt = builder._prompt(
        goals,
        0,
        classical=False,
        capabilities=capabilities,
        environment_sha256=environment.sha256,
        library_identity_sha256=environment.library_sha256,
    )
    captured: dict[str, object] = {}

    def fake_generate_one_tactic(**kwargs: object) -> str:
        captured.update(kwargs)
        return "refl"

    monkeypatch.setattr(generation, "generate_one_tactic", fake_generate_one_tactic)
    policy = generation.PeanoPolicyAdapter(None, None, environment)
    assert policy.propose(goals, sample=0, step=0, rng=random.Random(1)) == "refl"
    assert env_text == environment.text
    assert captured["prompt"] == builder_prompt


def test_builder_emits_loadable_v2_rows_from_checked_replay(tmp_path: Path) -> None:
    builder = _load_builder()
    environment = model_v2_environment()
    capabilities = SurfaceCapabilities(
        label="model-v2",
        allowed_commands=frozenset(environment.capabilities.allowed_commands or ()),
        allowed_theorems=frozenset(environment.capabilities.allowed_theorems or ()),
    )
    proof = run_proof(
        "0 = 0",
        ("refl",),
        request_id="v2-builder",
        session_id="v2-builder",
        capabilities=capabilities,
    )
    assert proof.status == "proved" and proof.trace is not None
    raw = tmp_path / "raw.jsonl"
    raw.write_text(
        "".join(
            json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"
            for record in proof.trace
        ),
        encoding="utf-8",
    )
    metadata = tmp_path / "metadata.jsonl"
    metadata.write_text(
        json.dumps(
            {
                "session": "v2-builder",
                "theorem": "zero_reflexive",
                "family": "v2-contract",
                "lineage": "v2-contract/zero",
                "classical": False,
                "surface": "model-v2",
                    "environment_sha256": capability_sha256(capabilities),
                    "library_identity_sha256": environment.library_sha256,
                    "capabilities": environment.capabilities.to_record(),
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )
    built = builder.build_dataset((raw,), metadata, tmp_path / "dataset")
    row = json.loads(built.train_path.read_text(encoding="utf-8"))

    assert built.manifest["prompt"] == prompt_manifest_record(PEANO_PROMPT_V2)
    compiler_sources = built.manifest["source"]["compiler"]["sources"]
    assert {
        "training/peano_policy/prompt.py",
        "training/peano_policy/library_identity.py",
        "artifacts/peano-library/mod5-source-validation-report.json",
    } <= set(compiler_sources)
    assert row["prompt"] == render_prompt(
        goals=tuple(row["state"]), focus=row["focus"], environment=environment
    )
    assert row["metadata"]["library_identity_sha256"] == (
        environment.library_sha256
    )
    assert example_from_record(row, 1).tactic == "refl"
    for claimed in (None, "0" * 64):
        forged = json.loads(json.dumps(row))
        if claimed is None:
            forged["metadata"].pop("library_identity_sha256")
        else:
            forged["metadata"]["library_identity_sha256"] = claimed
        with pytest.raises(PromptError, match="checked-library identity mismatch"):
            example_from_record(forged, 1)
    attestation = attest_dataset(built.train_path, built.val_path)
    assert attestation["prompt_version"] == PEANO_PROMPT_V2
    assert attestation["prompt_contract_sha256"] == prompt_contract_sha256(
        PEANO_PROMPT_V2
    )
    assert attestation["library_snapshot_sha256"] == environment.library_sha256


@pytest.mark.parametrize("claimed", [None, "0" * 64])
def test_builder_rejects_missing_or_mismatched_v2_library_identity(
    tmp_path: Path,
    claimed: str | None,
) -> None:
    builder = _load_builder()
    environment = model_v2_environment()
    capabilities = SurfaceCapabilities(
        label="model-v2",
        allowed_commands=frozenset(environment.capabilities.allowed_commands or ()),
        allowed_theorems=frozenset(environment.capabilities.allowed_theorems or ()),
    )
    proof = run_proof(
        "0 = 0",
        ("refl",),
        request_id="v2-identity-negative",
        session_id="v2-identity-negative",
        capabilities=capabilities,
    )
    assert proof.trace is not None
    raw = tmp_path / "raw.jsonl"
    raw.write_text(
        "".join(
            json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"
            for record in proof.trace
        ),
        encoding="utf-8",
    )
    metadata_record = {
        "session": "v2-identity-negative",
        "theorem": "zero_reflexive",
        "family": "v2-identity-negative",
        "lineage": "v2-identity-negative",
        "classical": False,
        "surface": "model-v2",
        "environment_sha256": capability_sha256(capabilities),
        "capabilities": environment.capabilities.to_record(),
    }
    if claimed is not None:
        metadata_record["library_identity_sha256"] = claimed
    metadata = tmp_path / "metadata.jsonl"
    metadata.write_text(
        json.dumps(metadata_record, ensure_ascii=False, separators=(",", ":"))
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        builder.DatasetBuildError,
        match="library_identity_sha256.*does not match",
    ):
        builder.build_dataset((raw,), metadata, tmp_path / "dataset")
    assert not (tmp_path / "dataset").exists()


def test_v2_attestation_binds_version_contract_and_library_snapshot() -> None:
    manifest = _v2_training_manifest()
    assert attested_training_environment(manifest) == model_v2_environment()

    manifest["inputs"]["dataset_attestation"]["library_snapshot_sha256"] = "0" * 64  # type: ignore[index]
    with pytest.raises(ValueError, match="prompt attestation"):
        attested_training_environment(manifest)


def test_v1_prompt_bytes_and_legacy_attestation_shape_remain_accepted() -> None:
    capabilities = CapabilityIdentity(
        "model-v1",
        ("assumption", "refl"),
        ("zero_add",),
    )
    environment = PromptEnvironment(False, capabilities)
    prompt = render_prompt(goals=("⊢ 0 = 0",), focus=0, environment=environment)

    assert PEANO_PROMPT_V1 == 1
    assert prompt == (
        "<task>next_tactic</task>\n"
        f"<env>{environment.text}</env>\n"
        '<state>{"focus":0,"goals":["⊢ 0 = 0"]}</state>\n'
        "<tactic>"
    )
    assert parse_prompt(prompt).prompt_version == PEANO_PROMPT_V1
    assert prompt_manifest_record() == prompt_manifest_record(PEANO_PROMPT_V1)


def test_v2_prompt_manifest_uses_the_checked_identity_schema_constants() -> None:
    identity = prompt_manifest_record(PEANO_PROMPT_V2)["library_identity"]
    assert identity["format"] == LIBRARY_IDENTITY_FORMAT
    assert identity["version"] == LIBRARY_IDENTITY_VERSION


def test_v2_environment_requires_enough_theorems_for_fixed_retrieval() -> None:
    library = model_v2_environment().library[: V2_RETRIEVAL_K - 1]
    capabilities = CapabilityIdentity(
        "small-v2",
        ("refl",),
        tuple(record.name for record in library),
    )
    with pytest.raises(PromptError, match="at least 8"):
        PromptEnvironment(
            False,
            capabilities,
            prompt_version=PEANO_PROMPT_V2,
            library=library,
            library_identity_sha256="0" * 64,
        )


def test_model_v2_label_cannot_hide_a_partial_or_heldout_catalog() -> None:
    environment = model_v2_environment()
    contaminated = tuple(sorted((*environment.capabilities.allowed_theorems, "le_total")))  # type: ignore[arg-type]
    capabilities = CapabilityIdentity(
        "model-v2",
        environment.capabilities.allowed_commands,
        contaminated,
    )
    with pytest.raises(ValueError, match="exact fixed intuitionistic authority"):
        from training.peano_policy.contract import prompt_environment

        prompt_environment(False, capabilities)

    prompt = render_prompt(
        goals=("⊢ 0 = 0",), focus=0, environment=environment
    )
    with pytest.raises(PromptError):
        parse_prompt(prompt.replace(environment.library_sha256 or "", "0" * 64, 1))
