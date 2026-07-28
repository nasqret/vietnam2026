"""One repository-owned environment and held-out boundary for policy M19."""

from __future__ import annotations

from functools import lru_cache
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
from peano_lab.library.theorems import THEOREMS  # noqa: E402

from .prompt import (
    PEANO_PROMPT_V1,
    PEANO_PROMPT_V2,
    CapabilityIdentity,
    LibraryRecord,
    PromptEnvironment,
    prompt_contract_sha256,
    prompt_manifest_record,
)
from .library_identity import (
    SEALED_LIBRARY_GOALS,
    SEALED_LIBRARY_NAMES,
    model_v2_library_identity,
    model_v2_library_identity_sha256,
    sealed_library_closure,
)


CONTRACT_VERSION = 1
HELD_OUT_POLICY_GOALS = SEALED_LIBRARY_GOALS
HELD_OUT_POLICY_NAMES = frozenset(name for name, _ in HELD_OUT_POLICY_GOALS)
EXCLUDED_POLICY_LIBRARY_NAMES = sealed_library_closure(THEOREMS)


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


@lru_cache(maxsize=1)
def model_v2_library() -> tuple[LibraryRecord, ...]:
    """Return the canonical public catalog visible to model-v2.

    The four benchmark targets and all of their dependency descendants are
    absent. Statements are parser/printer canonicalized so whitespace edits in
    source records do not silently create a new prompt library snapshot.
    """

    sealed_formulas: set[str] = set()
    for name, source in HELD_OUT_POLICY_GOALS:
        target, free_names = parse_formula_with_names(source)
        if free_names:
            raise RuntimeError(f"held-out policy goal {name!r} is not closed")
        sealed_formulas.add(pretty_formula(target, list(free_names)))
    allowed_names = frozenset(
        spec.name
        for spec in THEOREMS
        if spec.name not in EXCLUDED_POLICY_LIBRARY_NAMES
    )
    records: list[LibraryRecord] = []
    for spec in THEOREMS:
        if spec.name in EXCLUDED_POLICY_LIBRARY_NAMES:
            continue
        formula, free_names = parse_formula_with_names(spec.statement)
        if free_names:
            raise RuntimeError(f"public theorem {spec.name!r} is not closed")
        statement = pretty_formula(formula, list(free_names))
        if statement in sealed_formulas:
            raise RuntimeError(
                f"public theorem {spec.name!r} aliases a held-out target"
            )
        unavailable = set(spec.dependencies).difference(allowed_names)
        if unavailable:
            raise RuntimeError(
                f"public theorem {spec.name!r} depends outside model-v2: "
                + ", ".join(sorted(unavailable))
            )
        records.append(LibraryRecord(spec.name, statement))
    return tuple(sorted(records, key=lambda record: record.name))


MODEL_V2_THEOREMS: tuple[str, ...] = tuple(
    record.name for record in model_v2_library()
)


@lru_cache(maxsize=1)
def model_v2_environment() -> PromptEnvironment:
    """Return full public intuitionistic authority minus frozen targets."""

    if HELD_OUT_POLICY_NAMES != SEALED_LIBRARY_NAMES:
        raise RuntimeError("model-v2 identity and held-out contract disagree")
    if not HELD_OUT_POLICY_NAMES <= EXCLUDED_POLICY_LIBRARY_NAMES:
        raise RuntimeError("model-v2 import exclusion omits a held-out target")
    library = model_v2_library()
    identity = model_v2_library_identity()
    if tuple((item.name, item.statement) for item in identity) != tuple(
        (item.name, item.statement) for item in library
    ):
        raise RuntimeError(
            "model-v2 checked identity differs from its prompt projection"
        )
    return PromptEnvironment(
        False,
        CapabilityIdentity(
            label="model-v2",
            allowed_commands=tuple(sorted(MODEL_V1_COMMANDS)),
            allowed_theorems=MODEL_V2_THEOREMS,
        ),
        prompt_version=PEANO_PROMPT_V2,
        library=library,
        library_identity_sha256=model_v2_library_identity_sha256(),
    )


def prompt_environment(
    classical: bool,
    capabilities: CapabilityIdentity,
) -> PromptEnvironment:
    """Resolve capabilities to the unique repository-owned prompt contract.

    Existing/custom surfaces remain version 1.  The label ``model-v2`` is
    reserved: it is accepted only with the exact current command/theorem
    preimage, preventing a partial or contaminated catalog from masquerading
    under the v2 prompt contract.
    """

    if type(classical) is not bool:
        raise TypeError("classical must be a Boolean")
    if type(capabilities) is not CapabilityIdentity:
        raise TypeError("capabilities must be a CapabilityIdentity")
    if capabilities.label != "model-v2":
        return PromptEnvironment(classical, capabilities)
    expected = model_v2_environment()
    if classical or capabilities != expected.capabilities:
        raise ValueError(
            "model-v2 requires its exact fixed intuitionistic authority"
        )
    return expected


def environment_record(environment: PromptEnvironment) -> dict[str, object]:
    """Canonical manifest/report form of a policy environment."""

    if type(environment) is not PromptEnvironment:
        raise TypeError("environment must be a PromptEnvironment")
    record: dict[str, object] = {
        "classical": environment.classical,
        "surface": environment.capabilities.label,
        "environment_sha256": environment.sha256,
        "capabilities": environment.capabilities.to_record(),
    }
    if environment.prompt_version == PEANO_PROMPT_V2:
        record["library_identity_sha256"] = environment.library_sha256
    return record


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
    if type(record) is not dict:
        raise ValueError("training dataset environment attestation is malformed")
    expected_environment_fields = {
        "classical",
        "surface",
        "environment_sha256",
        "capabilities",
    }
    if record.get("surface") == "model-v2":
        expected_environment_fields.add("library_identity_sha256")
    if set(record) != expected_environment_fields:
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
    capabilities = CapabilityIdentity.from_record(canonical_capabilities)
    try:
        environment = prompt_environment(classical, capabilities)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"attested policy environment is unsupported: {exc}") from None
    if environment_record(environment) != record:
        raise ValueError("attested policy environment hash/preimage mismatch")
    if (
        environment.prompt_version == PEANO_PROMPT_V1
        and environment != model_v1_environment()
    ):
        raise ValueError("adapter was not trained under the fixed model-v1 authority")

    expected_version = environment.prompt_version
    expected_contract = prompt_manifest_record(expected_version)
    expected_contract_sha256 = prompt_contract_sha256(expected_version)
    attested_version = attestation.get("prompt_version")
    attested_contract = attestation.get("prompt_contract")
    attested_contract_sha256 = attestation.get("prompt_contract_sha256")
    attested_library_sha256 = attestation.get("library_snapshot_sha256")
    if expected_version == PEANO_PROMPT_V1 and all(
        value is None
        for value in (
            attested_version,
            attested_contract,
            attested_contract_sha256,
            attested_library_sha256,
        )
    ):
        # Compatibility for already published v1 adapter manifests.
        pass
    elif (
        attested_version != expected_version
        or attested_contract != expected_contract
        or attested_contract_sha256 != expected_contract_sha256
        or attested_library_sha256 != environment.library_sha256
    ):
        raise ValueError("training dataset prompt attestation is invalid")

    manifest_version = training_manifest.get("prompt_version")
    manifest_contract_sha256 = training_manifest.get("prompt_contract_sha256")
    if manifest_version is None and manifest_contract_sha256 is None:
        if expected_version != PEANO_PROMPT_V1:
            raise ValueError("model-v2 adapter lacks a bound prompt contract")
    elif (
        manifest_version != expected_version
        or manifest_contract_sha256 != expected_contract_sha256
    ):
        raise ValueError("adapter prompt identity differs from its dataset")
    return environment


__all__ = [
    "CONTRACT_VERSION",
    "EXCLUDED_POLICY_LIBRARY_NAMES",
    "HELD_OUT_POLICY_GOALS",
    "HELD_OUT_POLICY_NAMES",
    "MODEL_V2_THEOREMS",
    "canonical_held_out_formulas",
    "attested_training_environment",
    "environment_record",
    "held_out_contract_record",
    "held_out_contract_sha256",
    "model_v1_environment",
    "model_v2_environment",
    "model_v2_library",
    "prompt_environment",
]
