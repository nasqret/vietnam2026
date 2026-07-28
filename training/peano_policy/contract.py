"""One repository-owned environment and held-out boundary for policy M19."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PEANO_PYTHON = REPOSITORY_ROOT / "peano-lab" / "py"
if str(PEANO_PYTHON) not in sys.path:
    sys.path.insert(0, str(PEANO_PYTHON))

from peano_lab.batch import MODEL_V1_COMMANDS, MODEL_V1_THEOREMS  # noqa: E402
from peano_lab.kernel.formulas import (  # noqa: E402
    parse_formula_with_names,
    pretty_formula,
)

from .prompt import CapabilityIdentity, PromptEnvironment


CONTRACT_VERSION = 1
HELD_OUT_POLICY_GOALS: tuple[tuple[str, str], ...] = (
    ("le_trans", "forall n m k. n <= m -> m <= k -> n <= k"),
    ("le_antisymm", "forall n m. n <= m -> m <= n -> n = m"),
    ("le_total", "forall n m. n <= m \\/ m <= n"),
    ("mul_eq_zero", "forall n m. n * m = 0 -> n = 0 \\/ m = 0"),
)


def model_v1_environment() -> PromptEnvironment:
    """Return the exact fixed intuitionistic policy authority."""

    return PromptEnvironment(
        False,
        CapabilityIdentity(
            label="model-v1",
            allowed_commands=tuple(sorted(MODEL_V1_COMMANDS)),
            allowed_theorems=tuple(sorted(MODEL_V1_THEOREMS)),
        ),
    )


def environment_record(environment: PromptEnvironment) -> dict[str, object]:
    """Canonical manifest/report form of a policy environment."""

    if type(environment) is not PromptEnvironment:
        raise TypeError("environment must be a PromptEnvironment")
    return {
        "classical": environment.classical,
        "surface": environment.capabilities.label,
        "environment_sha256": environment.sha256,
        "capabilities": environment.capabilities.to_record(),
    }


def canonical_held_out_formulas() -> tuple[str, ...]:
    result: list[str] = []
    for name, statement in HELD_OUT_POLICY_GOALS:
        target, free_names = parse_formula_with_names(statement)
        if free_names:
            raise RuntimeError(f"held-out policy goal {name!r} is not closed")
        result.append(pretty_formula(target, list(free_names)))
    return tuple(result)


def held_out_contract_record() -> dict[str, object]:
    formulas = canonical_held_out_formulas()
    return {
        "v": CONTRACT_VERSION,
        "goals": [
            {"name": name, "statement": formula}
            for (name, _), formula in zip(
                HELD_OUT_POLICY_GOALS, formulas, strict=True
            )
        ],
    }


def held_out_contract_sha256() -> str:
    payload = json.dumps(
        held_out_contract_record(),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def attested_training_environment(
    training_manifest: object,
) -> PromptEnvironment:
    """Validate the replay/holdout gate embedded in a trained adapter."""

    if type(training_manifest) is not dict:
        raise ValueError("training manifest must be an object")
    inputs = training_manifest.get("inputs")
    attestation = inputs.get("dataset_attestation") if type(inputs) is dict else None
    if type(attestation) is not dict:
        raise ValueError("training manifest has no dataset attestation")
    if (
        attestation.get("format") != "peano-policy-dataset-attestation"
        or attestation.get("v") != 1
        or attestation.get("independent_replay") is not True
        or attestation.get("held_out_contamination") != 0
        or attestation.get("held_out_contract") != held_out_contract_record()
        or attestation.get("held_out_contract_sha256")
        != held_out_contract_sha256()
    ):
        raise ValueError("training dataset attestation is invalid or contaminated")
    splits = attestation.get("splits")
    train_data = inputs.get("train_data")
    eval_data = inputs.get("eval_data")
    train_manifest = inputs.get("train_dataset_manifest")
    eval_manifest = inputs.get("eval_dataset_manifest")
    if (
        type(splits) is not dict
        or type(splits.get("train")) is not dict
        or type(splits.get("val")) is not dict
        or type(train_data) is not dict
        or type(eval_data) is not dict
        or type(train_manifest) is not dict
        or type(eval_manifest) is not dict
        or train_data.get("sha256") != splits["train"].get("sha256")
        or eval_data.get("sha256") != splits["val"].get("sha256")
        or train_manifest.get("sha256") != attestation.get("manifest_sha256")
        or eval_manifest.get("sha256") != attestation.get("manifest_sha256")
    ):
        raise ValueError(
            "training input hashes are not bound to the dataset attestation"
        )
    record = attestation.get("environment")
    if type(record) is not dict or set(record) != {
        "classical",
        "surface",
        "environment_sha256",
        "capabilities",
    }:
        raise ValueError("training dataset environment attestation is malformed")
    classical = record.get("classical")
    if type(classical) is not bool:
        raise ValueError("attested policy logic mode must be Boolean")
    capability_record = record.get("capabilities")
    if type(capability_record) is not dict or set(capability_record) != {
        "label",
        "allowed_commands",
        "allowed_theorems",
    }:
        raise ValueError("attested policy capabilities are malformed")
    # Dataset rows have a deliberately fixed construction order, which
    # CapabilityIdentity.from_record checks.  Training manifests are canonical
    # JSON written with sort_keys=True, so their nested mapping is necessarily
    # read back in lexical key order.  Reconstruct the semantic record here;
    # exact fields and the environment preimage/hash comparison below remain
    # mandatory.
    canonical_capabilities = {
        "label": capability_record["label"],
        "allowed_commands": capability_record["allowed_commands"],
        "allowed_theorems": capability_record["allowed_theorems"],
    }
    environment = PromptEnvironment(
        classical,
        CapabilityIdentity.from_record(canonical_capabilities),
    )
    if environment_record(environment) != record:
        raise ValueError("attested policy environment hash/preimage mismatch")
    if environment != model_v1_environment():
        raise ValueError("adapter was not trained under the fixed model-v1 authority")
    return environment


__all__ = [
    "CONTRACT_VERSION",
    "HELD_OUT_POLICY_GOALS",
    "canonical_held_out_formulas",
    "attested_training_environment",
    "environment_record",
    "held_out_contract_record",
    "held_out_contract_sha256",
    "model_v1_environment",
]
