#!/usr/bin/env python3
"""Generate root-balanced, proof-first synthetic data for model-v3.

The model-v2 synthetic corpus accidentally taught an almost universal first
move: many otherwise useful schemas were hidden behind an artificial
``gate -> ...`` proposition, so their root transition was ``intro gate``.
This generator keeps the useful proof-first schema builders, drops every old
``library-*`` schema (library trajectories are generated separately), and
removes the induction gates as one validated immutable transformation.  The
gate-free induction bodies retain bounded closed tags so that they remain
distinct theorem roots instead of collapsing to four repeated statements.
The generator also adds genuinely closed equality, existential, conjunction,
and disjunction roots.

Sessions are scheduled by a deficit over their *first tactic head*.  Thus a
large family of introduction-based schemas cannot dominate root states, and
``intro`` is additionally capped at twenty percent of emitted sessions.  Each
accepted session is executed by :func:`peano_lab.batch.run_proof` under the
full model-v3 theorem prefix and reaches an independently kernel-checked QED.

Two stopping rules are available. ``exact`` emits exactly the requested
number of positive transition rows, selecting only a complete session that
fits the remaining budget. ``complete-session`` treats the budget as a lower
bound and may exceed it by one final, indivisible session.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
from collections import Counter
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import TextIO


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = REPOSITORY_ROOT / "scripts"
PEANO_PYTHON = REPOSITORY_ROOT / "peano-lab" / "py"
for import_root in (REPOSITORY_ROOT, SCRIPTS_ROOT, PEANO_PYTHON):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

import generate_peano_synthetic_corpus as source  # noqa: E402
from peano_lab.batch import (  # noqa: E402
    MODEL_V1_COMMANDS,
    BatchResult,
    capability_sha256,
    run_proof,
)
from peano_lab.engine.trace import TRACE_VERSION  # noqa: E402
from peano_lab.kernel.formulas import (  # noqa: E402
    And,
    Eq,
    Exists,
    Formula,
    Imp,
    Or,
    ParseError,
    parse_formula_with_names,
    pretty_formula,
)
from peano_lab.library.theorems import THEOREMS  # noqa: E402
from peano_lab.ui.prove import SurfaceCapabilities  # noqa: E402
from training.peano_policy.contract import (  # noqa: E402
    MODEL_V3_HELD_OUT_POLICY_GOALS,
    MODEL_V3_LIBRARY_SIZE,
    canonical_held_out_formulas,
    environment_record,
    held_out_contract_sha256,
    model_v3_environment,
)
from training.peano_policy.library_identity_v3 import (  # noqa: E402
    PUBLIC_LIBRARY_CATALOG,
    PUBLIC_LIBRARY_SOURCE,
)
from training.peano_policy.prompt import PEANO_PROMPT_V3, PromptEnvironment  # noqa: E402


Candidate = source.Candidate
Schema = source.Schema
GenerationError = source.GenerationError
GenerationResult = source.GenerationResult
_DigestingWriter = source._DigestingWriter


class _HeldOutTargetError(GenerationError):
    """A valid schema candidate is reserved exclusively for evaluation."""


FORMAT = "peano-policy-corpus"
VERSION = 1
PROFILE = "model-v3"
CATALOG_VERSION = 2
GENERATOR = "proof-first-root-balanced-v3"
DEFAULT_SEED = "peano-synthetic-v3-balanced"
DEFAULT_ROW_BUDGET = 1_000
MAX_ROW_BUDGET = 100_000
BUDGET_MODES = ("exact", "complete-session")
INTRO_ROOT_PERCENT = 20
SCHEDULE_SELECTION = "first-tactic-head-deficit-long-session-tiebreak-v2"
SCHEMA_OFFSET_MODULUS = 20_000
CLOSED_TERM_PERIOD = 10_000
INDUCTION_ZERO_TAG_BASE = 4
INDUCTION_ZERO_TAG_DIGITS = 6
INDUCTION_ZERO_TAG_PERIOD = INDUCTION_ZERO_TAG_BASE**INDUCTION_ZERO_TAG_DIGITS
HELD_OUT_NAMES = frozenset(
    name for name, _ in MODEL_V3_HELD_OUT_POLICY_GOALS
)
HELD_OUT_FORMULAS = frozenset(
    canonical_held_out_formulas(PEANO_PROMPT_V3)
)
REQUIRED_ROOT_KINDS = frozenset(
    {"equality", "existential", "conjunction", "disjunction", "induction"}
)


def _candidate(
    statement: str,
    tactics: Sequence[str],
    **parameters: object,
) -> Candidate:
    return Candidate(statement, tuple(tactics), dict(parameters))


def _digits(value: int, base: int, count: int) -> tuple[int, ...]:
    result: list[int] = []
    for _ in range(count):
        result.append(value % base)
        value //= base
    return tuple(result)


def _closed_term(index: int, *, salt: int = 0) -> str:
    a, b, c, d = _digits(
        (index * 17 + salt * 101) % CLOSED_TERM_PERIOD,
        10,
        4,
    )
    return f"(({a} + {b}) * ({c} + 1) + {d})"


def _closed_equality(index: int) -> Candidate:
    term = _closed_term(index, salt=1)
    return _candidate(
        f"{term} = {term}",
        ("refl",),
        root_kind="equality",
        term=term,
    )


def _closed_norm(index: int) -> Candidate:
    candidate = source._arithmetic_closed_norm(index)
    return Candidate(
        candidate.statement,
        candidate.tactics,
        {**candidate.parameters, "root_kind": "equality"},
    )


RING_DIGIT_BASE = 7
RING_ZERO_TAG_BASE = 4
RING_ZERO_TAG_DIGITS = 2
RING_ZERO_TAG_COUNT = RING_ZERO_TAG_BASE**RING_ZERO_TAG_DIGITS
RING_SAFE_COEFFICIENTS: tuple[tuple[int, int, int, int], ...] = tuple(
    (a, b, c, d)
    for d in range(RING_DIGIT_BASE)
    for c in range(RING_DIGIT_BASE)
    for b in range(RING_DIGIT_BASE)
    for a in range(RING_DIGIT_BASE)
    if (a + b) * (c + d) <= 128
)
RING_CANDIDATE_PERIOD = len(RING_SAFE_COEFFICIENTS) * RING_ZERO_TAG_COUNT


def _closed_ring(index: int) -> Candidate:
    cycle, coefficient_index = divmod(
        index % RING_CANDIDATE_PERIOD,
        len(RING_SAFE_COEFFICIENTS),
    )
    a, b, c, d = RING_SAFE_COEFFICIENTS[coefficient_index]
    tag_left, tag_right = _digits(
        cycle,
        RING_ZERO_TAG_BASE,
        RING_ZERO_TAG_DIGITS,
    )
    # The compact syntactic tag is always polynomially zero.  It gives the
    # one ring-root schema enough distinct closed statements for the largest
    # supported row budget without raising any normalized coefficient.
    zero_tag = f"({tag_left} * 0 + {tag_right} * 0)"
    return _candidate(
        (
            f"({a} + {b}) * ({c} + {d}) + {zero_tag} = "
            f"{a} * {c} + {a} * {d} + {b} * {c} + {b} * {d} + {zero_tag}"
        ),
        ("ring",),
        root_kind="equality",
        coefficients=[a, b, c, d],
        normalized_coefficient=(a + b) * (c + d),
        zero_tag_digits=[tag_left, tag_right],
    )


def _closed_rewrite(index: int) -> Candidate:
    term = _closed_term(index, salt=2)
    return _candidate(
        f"({term}) + 0 = {term}",
        ("rewrite PA3", "refl"),
        root_kind="equality",
        term=term,
    )


def _closed_trans(index: int) -> Candidate:
    term = _closed_term(index, salt=3)
    middle = f"({term}) + 0"
    return _candidate(
        f"{middle} = {middle}",
        (f"trans {middle}", "refl", "refl"),
        root_kind="equality",
        term=term,
    )


def _closed_symm(index: int) -> Candidate:
    term = _closed_term(index, salt=4)
    return _candidate(
        f"S ({term}) = S ({term})",
        ("symm", "refl"),
        root_kind="equality",
        term=term,
    )


def _closed_congr(index: int) -> Candidate:
    term = _closed_term(index, salt=5)
    return _candidate(
        f"S (S ({term})) = S (S ({term}))",
        ("congr", "refl"),
        root_kind="equality",
        term=term,
    )


def _closed_compact(index: int) -> Candidate:
    term = _closed_term(index, salt=6)
    return _candidate(
        f"({term}) + 1 = S ({term})",
        ("compact_arith",),
        root_kind="equality",
        term=term,
    )


def _closed_exists(index: int) -> Candidate:
    term = _closed_term(index, salt=7)
    return _candidate(
        f"exists x. x = {term}",
        (f"exists {term}", "refl"),
        root_kind="existential",
        witness=term,
    )


def _closed_conjunction(index: int) -> Candidate:
    left = _closed_term(index, salt=8)
    right = _closed_term(index, salt=9)
    return _candidate(
        f"({left} = {left}) /\\ ({right} = {right})",
        ("split", "refl", "refl"),
        root_kind="conjunction",
        left=left,
        right=right,
    )


def _closed_disjunction_left(index: int) -> Candidate:
    left = _closed_term(index, salt=10)
    right = _closed_term(index, salt=11)
    return _candidate(
        f"({left} = {left}) \\/ (S ({right}) = 0)",
        ("left", "refl"),
        root_kind="disjunction",
        branch="left",
    )


def _closed_disjunction_right(index: int) -> Candidate:
    left = _closed_term(index, salt=12)
    right = _closed_term(index, salt=13)
    return _candidate(
        f"(S ({left}) = 0) \\/ ({right} = {right})",
        ("right", "refl"),
        root_kind="disjunction",
        branch="right",
    )


ROOT_SCHEMAS: tuple[Schema, ...] = (
    Schema("root-equality-refl", "equality", ("closed", "equality", "refl"), _closed_equality),
    Schema("root-equality-norm", "arithmetic", ("closed", "equality", "norm_num"), _closed_norm),
    Schema("root-equality-ring", "arithmetic", ("closed", "equality", "ring"), _closed_ring),
    Schema(
        "root-equality-rewrite",
        "recurrence",
        ("closed", "equality", "rewrite"),
        _closed_rewrite,
    ),
    Schema("root-equality-trans", "equality", ("closed", "equality", "trans"), _closed_trans),
    Schema("root-equality-symm", "equality", ("closed", "equality", "symm"), _closed_symm),
    Schema("root-equality-congr", "equality", ("closed", "equality", "congr"), _closed_congr),
    Schema(
        "root-equality-compact",
        "arithmetic",
        ("closed", "equality", "compact_arith"),
        _closed_compact,
    ),
    Schema("root-existential", "witnesses", ("closed", "existential", "witness"), _closed_exists),
    Schema("root-conjunction", "logic", ("closed", "conjunction", "split"), _closed_conjunction),
    Schema(
        "root-disjunction-left",
        "logic",
        ("closed", "disjunction", "left"),
        _closed_disjunction_left,
    ),
    Schema(
        "root-disjunction-right",
        "logic",
        ("closed", "disjunction", "right"),
        _closed_disjunction_right,
    ),
)


def _ungate_candidate(candidate: Candidate) -> Candidate:
    """Remove one exact synthetic gate without mutating a partial candidate."""

    gate = candidate.parameters.get("gate")
    prefix = f"({gate}) -> " if type(gate) is str else ""
    if (
        not prefix
        or not candidate.statement.startswith(prefix)
        or not candidate.tactics
        or candidate.tactics[0] != "intro gate"
    ):
        raise GenerationError("induction schema has no exact removable gate")
    statement = candidate.statement[len(prefix) :]
    tactics = candidate.tactics[1:]
    if not statement or not tactics or tactics[0].split(maxsplit=1)[0] != "induction":
        raise GenerationError("induction gate removal did not expose induction")
    parameters = dict(candidate.parameters)
    parameters.pop("gate")
    parameters.update(
        {
            "artificial_gate_removed": True,
            "root_kind": "induction",
        }
    )
    return Candidate(statement, tactics, parameters)


_UNGATED_INDUCTION_BODIES = {
    "induction-add-zero": "forall n. 0 + n = n",
    "induction-mul-zero": "forall n. 0 * n = 0",
    "induction-add-one": "forall n. n + 0 = n",
    "induction-explicit-IH": "forall n. 0 = 0",
}
_UNGATED_INDUCTION_SALTS = {
    "induction-add-zero": 20,
    "induction-mul-zero": 21,
    "induction-add-one": 22,
    "induction-explicit-IH": 23,
}


def _closed_zero_tag(index: int, *, salt: int) -> str:
    digits = _digits(
        (index * 17 + salt * 101) % INDUCTION_ZERO_TAG_PERIOD,
        INDUCTION_ZERO_TAG_BASE,
        INDUCTION_ZERO_TAG_DIGITS,
    )
    return "(" + " + ".join(f"{digit} * 0" for digit in digits) + ")"


def _vary_ungated_induction(
    candidate: Candidate,
    *,
    schema_name: str,
    index: int,
) -> Candidate:
    expected = _UNGATED_INDUCTION_BODIES.get(schema_name)
    if expected is None or candidate.statement != expected:
        raise GenerationError("induction schema changed its reviewed gate-free body")
    tag = _closed_zero_tag(index, salt=_UNGATED_INDUCTION_SALTS[schema_name])
    if schema_name == "induction-add-zero":
        statement = f"forall n. ({tag}) + n = n"
        tactics = (
            "induction n",
            "simp",
            "rewrite PA4",
            "rewrite IH",
            "refl",
        )
    elif schema_name == "induction-mul-zero":
        statement = f"forall n. ({tag}) * n = 0"
        tactics = (
            "induction n",
            "simp",
            "rewrite PA6",
            "rewrite IH",
            "simp",
        )
    elif schema_name == "induction-add-one":
        statement = f"forall n. n + ({tag}) = n"
        tactics = candidate.tactics
    else:
        statement = f"forall n. ({tag}) = ({tag})"
        tactics = candidate.tactics
    return Candidate(
        statement,
        tactics,
        {
            **candidate.parameters,
            "closed_root_zero_tag": tag,
            "closed_root_zero_tag_method": "bounded-syntactic-zero-v1",
        },
    )


def _ungated_builder(
    build: Callable[[int], Candidate],
    schema_name: str,
) -> Callable[[int], Candidate]:
    def transformed(index: int) -> Candidate:
        candidate = _ungate_candidate(build(index))
        return _vary_ungated_induction(
            candidate,
            schema_name=schema_name,
            index=index,
        )

    return transformed


def _reused_schemas() -> tuple[Schema, ...]:
    result: list[Schema] = []
    for schema in source.SCHEMAS:
        if schema.lane == "library" or schema.name.startswith("library-"):
            continue
        build = schema.build
        tags = schema.tags + ("reused-v2-proof-first",)
        if schema.name.startswith("induction-"):
            build = _ungated_builder(build, schema.name)
            tags += ("gate-removed", "closed-root-tag",)
        result.append(
            Schema(
                f"reused-{schema.name}",
                schema.domain,
                tags,
                build,
                lane="synthetic",
                weight=schema.weight,
            )
        )
    return tuple(result)


REUSED_SCHEMAS = _reused_schemas()
SCHEMAS: tuple[Schema, ...] = ROOT_SCHEMAS + REUSED_SCHEMAS
DOMAINS = tuple(sorted({schema.domain for schema in SCHEMAS}))


def _safe_text(value: object, *, nonempty: bool = False) -> bool:
    return source._safe_text(value, nonempty=nonempty)


def _sha256_file(path: Path) -> str:
    return source._sha256_file(path)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _line_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n"


@lru_cache(maxsize=1)
def _policy_environment() -> PromptEnvironment:
    environment = model_v3_environment()
    if (
        environment.prompt_version != PEANO_PROMPT_V3
        or environment.library_prefix_length != MODEL_V3_LIBRARY_SIZE
        or environment.library_full_length != MODEL_V3_LIBRARY_SIZE
    ):
        raise GenerationError("model-v3 full-prefix environment is malformed")
    return environment


@lru_cache(maxsize=1)
def _policy_capabilities() -> SurfaceCapabilities:
    environment = _policy_environment()
    capabilities = SurfaceCapabilities(
        label=environment.capabilities.label,
        allowed_commands=frozenset(environment.capabilities.allowed_commands or ()),
        allowed_theorems=frozenset(environment.capabilities.allowed_theorems or ()),
    )
    if capability_sha256(capabilities) != environment.sha256:
        raise GenerationError("runner and model-v3 prompt authorities disagree")
    return capabilities


def _capability_record(environment: PromptEnvironment) -> dict[str, object]:
    return environment.capabilities.to_record()


def _source_manifest() -> dict[str, dict[str, str]]:
    paths = (
        Path(__file__).resolve(),
        SCRIPTS_ROOT / "generate_peano_synthetic_corpus.py",
        SCRIPTS_ROOT / "export_traces.py",
        REPOSITORY_ROOT / "training" / "peano_policy" / "contract.py",
        REPOSITORY_ROOT / "training" / "peano_policy" / "prompt.py",
        REPOSITORY_ROOT / "training" / "peano_policy" / "library_identity_v3.py",
        PUBLIC_LIBRARY_CATALOG,
        PUBLIC_LIBRARY_SOURCE,
        *sorted((PEANO_PYTHON / "peano_lab").rglob("*.py")),
    )
    return {
        path.relative_to(REPOSITORY_ROOT).as_posix(): {"sha256": _sha256_file(path)}
        for path in paths
    }


def _runtime_record() -> dict[str, str]:
    return {
        "implementation": platform.python_implementation(),
        "python": platform.python_version(),
    }


def _canonical_statement(candidate: Candidate, schema: Schema) -> tuple[str, Formula]:
    if not candidate.tactics:
        raise GenerationError(f"schema {schema.name!r} emitted no tactics")
    if not _safe_text(candidate.statement, nonempty=True):
        raise GenerationError(f"schema {schema.name!r} emitted unsafe statement text")
    for tactic in candidate.tactics:
        if not _safe_text(tactic, nonempty=True) or tactic != tactic.strip():
            raise GenerationError(f"schema {schema.name!r} emitted unsafe tactic text")
        head = tactic.split(maxsplit=1)[0]
        if head not in MODEL_V1_COMMANDS:
            raise GenerationError(
                f"schema {schema.name!r} emitted unavailable command {head!r}"
            )
    try:
        formula, free_names = parse_formula_with_names(candidate.statement)
    except (ParseError, TypeError, ValueError, RecursionError) as exc:
        raise GenerationError(
            f"schema {schema.name!r} emitted an invalid statement: {exc}"
        ) from exc
    if free_names:
        raise GenerationError(
            f"schema {schema.name!r} emitted a non-closed statement: "
            + ", ".join(free_names)
        )
    canonical = pretty_formula(formula, [])
    if canonical in HELD_OUT_FORMULAS:
        raise _HeldOutTargetError(
            f"schema {schema.name!r} emitted a model-v3 held-out target"
        )
    return canonical, formula


def _root_kind(formula: Formula, first_head: str, candidate: Candidate) -> str:
    explicit = candidate.parameters.get("root_kind")
    if type(explicit) is str:
        return explicit
    if first_head == "induction":
        return "induction"
    if isinstance(formula, Eq):
        return "equality"
    if isinstance(formula, Exists):
        return "existential"
    if isinstance(formula, And):
        return "conjunction"
    if isinstance(formula, Or):
        return "disjunction"
    if isinstance(formula, Imp):
        return "implication"
    return type(formula).__name__.lower()


def _rank(seed: str, epoch: int, label: str) -> str:
    payload = json.dumps(
        [seed, CATALOG_VERSION, epoch, label],
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _schema_offset(seed: str, schema: Schema) -> int:
    material = f"{seed}\0{CATALOG_VERSION}\0{schema.name}".encode("utf-8")
    return (
        int.from_bytes(hashlib.sha256(material).digest()[:4], "big")
        % SCHEMA_OFFSET_MODULUS
    )


def _first_head(schema: Schema) -> str:
    candidate = schema.build(0)
    return candidate.tactics[0].split(maxsplit=1)[0]


def _schemas_by_head() -> dict[str, tuple[Schema, ...]]:
    grouped: dict[str, list[Schema]] = {}
    for schema in SCHEMAS:
        grouped.setdefault(_first_head(schema), []).append(schema)
    return {
        head: tuple(sorted(schemas, key=lambda item: item.name))
        for head, schemas in sorted(grouped.items())
    }


SCHEMAS_BY_HEAD = _schemas_by_head()
ROOT_HEADS = tuple(SCHEMAS_BY_HEAD)
MIN_TACTIC_ROWS_BY_HEAD = {
    head: min(len(schema.build(0).tactics) for schema in schemas)
    for head, schemas in SCHEMAS_BY_HEAD.items()
}


def _validate_catalog() -> None:
    if len(THEOREMS) < MODEL_V3_LIBRARY_SIZE:
        raise GenerationError("frozen model-v3 prefix is absent from the source catalog")
    names = [schema.name for schema in SCHEMAS]
    if len(set(names)) != len(names):
        raise GenerationError("model-v3 synthetic schema names are not unique")
    if any(name.startswith("library-") or "reused-library-" in name for name in names):
        raise GenerationError("model-v3 synthetic catalog contains a library schema")
    if "intro" not in ROOT_HEADS or "induction" not in ROOT_HEADS:
        raise GenerationError("root curriculum lacks intro or induction")
    maximum_balanced_ring_attempts = (
        SCHEMA_OFFSET_MODULUS
        + (MAX_ROW_BUDGET + len(ROOT_HEADS) - 1) // len(ROOT_HEADS)
    )
    if (
        len(RING_SAFE_COEFFICIENTS) != 2_396
        or any((a + b) * (c + d) > 128 for a, b, c, d in RING_SAFE_COEFFICIENTS)
        or RING_CANDIDATE_PERIOD <= maximum_balanced_ring_attempts
    ):
        raise GenerationError("root ring schema exceeds its reviewed coefficient domain")
    induction_schemas = SCHEMAS_BY_HEAD["induction"]
    maximum_balanced_induction_attempts = (
        (MAX_ROW_BUDGET + len(ROOT_HEADS) - 1) // len(ROOT_HEADS)
        + len(induction_schemas)
        - 1
    ) // len(induction_schemas)
    if (
        len(induction_schemas) != 4
        or INDUCTION_ZERO_TAG_PERIOD <= maximum_balanced_induction_attempts
    ):
        raise GenerationError("induction root tags cannot cover the reviewed row budget")
    for schema in SCHEMAS:
        if not _safe_text(schema.name, nonempty=True):
            raise GenerationError("model-v3 synthetic catalog has an unsafe name")
        candidate = schema.build(0)
        canonical, formula = _canonical_statement(candidate, schema)
        del canonical, formula
        if schema.name.startswith("reused-induction-"):
            if candidate.tactics[0].split(maxsplit=1)[0] != "induction":
                raise GenerationError("induction gate removal was not root-visible")
            if "artificial_gate_removed" not in candidate.parameters:
                raise GenerationError("induction gate removal was not recorded")


def _generation_fingerprint(
    *,
    seed: str,
    row_budget: int,
    budget_mode: str,
    sources: dict[str, dict[str, str]],
    environment: PromptEnvironment,
) -> str:
    payload = {
        "format": FORMAT,
        "version": VERSION,
        "profile": PROFILE,
        "catalog_version": CATALOG_VERSION,
        "generator": GENERATOR,
        "config": {
            "seed": seed,
            "row_budget": row_budget,
            "budget_mode": budget_mode,
        },
        "environment": environment_record(environment),
        "held_out_contract_sha256": held_out_contract_sha256(PEANO_PROMPT_V3),
        "sources": sources,
        "schemas": [
            {
                "name": schema.name,
                "domain": schema.domain,
                "tags": list(schema.tags),
                "first_head": _first_head(schema),
            }
            for schema in SCHEMAS
        ],
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _root_id(schema: Schema, canonical_statement: str) -> str:
    encoded = json.dumps(
        [CATALOG_VERSION, schema.name, canonical_statement],
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"synthetic-v3/{schema.name}/{hashlib.sha256(encoded).hexdigest()[:20]}"


def _checked_result(
    result: BatchResult,
    *,
    schema: Schema,
    candidate: Candidate,
    canonical_statement: str,
    environment: PromptEnvironment,
) -> tuple[dict[str, object], ...]:
    if result.status != "proved" or result.kernel_checked is not True:
        detail = result.error or result.status
        raise GenerationError(
            f"schema {schema.name!r} failed checked QED for "
            f"{candidate.statement!r}: {detail}"
        )
    if result.theorem != canonical_statement:
        raise GenerationError(f"schema {schema.name!r} changed its original theorem")
    if (
        result.surface != environment.capabilities.label
        or result.environment_sha256 != environment.sha256
        or result.classical is not False
    ):
        raise GenerationError(f"schema {schema.name!r} escaped model-v3 authority")
    if result.trace is None or not result.trace:
        raise GenerationError(f"schema {schema.name!r} returned no binding trace")
    transitions = tuple(record for record in result.trace if "v" in record)
    if len(transitions) != len(candidate.tactics):
        raise GenerationError(
            f"schema {schema.name!r} returned an incomplete transition trace"
        )
    if any(record.get("status") != "ok" for record in transitions):
        raise GenerationError(f"schema {schema.name!r} retained a failed transition")
    footer = result.trace[-1]
    if (
        footer.get("qed") is not True
        or footer.get("tactic_count") != len(transitions)
        or footer.get("proof_size") != result.proof_nodes
    ):
        raise GenerationError(f"schema {schema.name!r} returned a malformed QED footer")
    return transitions


def _metadata_record(
    *,
    schema: Schema,
    candidate: Candidate,
    result: BatchResult,
    canonical_statement: str,
    root_formula: Formula,
    root: str,
    first_head: str,
    seed: str,
    parameter_index: int,
    ordinal: int,
    environment: PromptEnvironment,
) -> dict[str, object]:
    script_text = json.dumps(
        list(candidate.tactics), ensure_ascii=False, separators=(",", ":")
    )
    return {
        "session": result.session_id,
        "theorem": f"synthetic.{schema.name}.{root.rsplit('/', 1)[-1]}",
        "family": root,
        "lineage": root,
        "classical": False,
        "surface": environment.capabilities.label,
        "environment_sha256": environment.sha256,
        "library_identity_sha256": environment.library_sha256,
        "library_full_identity_sha256": environment.library_full_identity_sha256,
        "library_prefix_length": environment.library_prefix_length,
        "library_size": environment.library_full_length,
        "capabilities": _capability_record(environment),
        "statement": canonical_statement,
        "statement_sha256": _sha256_text(canonical_statement),
        "script_sha256": _sha256_text(script_text),
        "template": schema.name,
        "domain": schema.domain,
        "tags": list(schema.tags),
        "lane": "synthetic-root-balanced",
        "seed": seed,
        "ordinal": ordinal,
        "root": root,
        "root_first_tactic_head": first_head,
        "root_kind": _root_kind(root_formula, first_head, candidate),
        "variant": "authored-v3-root-balanced",
        "parents": [],
        "transformations": [
            "proof-first-schema-instantiation",
            *(
                ["remove-artificial-induction-gate"]
                if candidate.parameters.get("artificial_gate_removed") is True
                else []
            ),
            *(
                ["add-bounded-closed-induction-zero-tag"]
                if candidate.parameters.get("closed_root_zero_tag_method")
                == "bounded-syntactic-zero-v1"
                else []
            ),
        ],
        "parameter_index": parameter_index,
        "parameters": candidate.parameters,
        "tactics": list(candidate.tactics),
        "tactic_rows": len(candidate.tactics),
        "proof_nodes": result.proof_nodes,
    }


@dataclass(slots=True)
class _Schedule:
    seed: str
    attempts: Counter[str]
    head_counts: Counter[str]
    schema_cursors: Counter[str]
    duplicate_skips: int = 0
    held_out_skips: int = 0
    overlong_skips: int = 0

    def ordered_heads(self, sessions: int) -> tuple[str, ...]:
        heads = list(ROOT_HEADS)
        if 5 * (self.head_counts["intro"] + 1) > sessions + 1:
            heads.remove("intro")
        return tuple(
            sorted(
                heads,
                key=lambda head: (
                    self.head_counts[head],
                    -MIN_TACTIC_ROWS_BY_HEAD[head],
                    _rank(self.seed, sessions, f"root-head:{head}"),
                    head,
                ),
            )
        )

    def next_candidate(self, head: str) -> tuple[Schema, int, Candidate]:
        schemas = SCHEMAS_BY_HEAD[head]
        cursor = self.schema_cursors[head]
        self.schema_cursors[head] += 1
        epoch, position = divmod(cursor, len(schemas))
        ordered = sorted(
            schemas,
            key=lambda schema: (
                _rank(self.seed, epoch, f"schema:{head}:{schema.name}"),
                schema.name,
            ),
        )
        schema = ordered[position]
        occurrence = self.attempts[schema.name]
        self.attempts[schema.name] += 1
        parameter_index = _schema_offset(self.seed, schema) + occurrence
        candidate = schema.build(parameter_index)
        actual_head = candidate.tactics[0].split(maxsplit=1)[0]
        if actual_head != head:
            raise GenerationError(
                f"schema {schema.name!r} changed first head from {head!r} "
                f"to {actual_head!r}"
            )
        return schema, parameter_index, candidate


ScheduledCandidate = tuple[Schema, int, Candidate, str, Formula, str]


def _select_candidate(
    schedule: _Schedule,
    *,
    sessions: int,
    remaining: int,
    budget_mode: str,
    seen_statements: set[str],
    seen_roots: set[str],
) -> ScheduledCandidate:
    chosen: ScheduledCandidate | None = None
    # A full pass is enough to find a one-row root in exact mode; the
    # multiplier also lets duplicate or held-out candidates advance safely.
    max_attempts = max(16, 4 * len(SCHEMAS))
    for head in schedule.ordered_heads(sessions):
        for _ in range(max_attempts):
            schema, parameter_index, candidate = schedule.next_candidate(head)
            if budget_mode == "exact" and len(candidate.tactics) > remaining:
                schedule.overlong_skips += 1
                continue
            try:
                canonical, formula = _canonical_statement(candidate, schema)
            except _HeldOutTargetError:
                schedule.held_out_skips += 1
                continue
            if canonical in seen_statements:
                schedule.duplicate_skips += 1
                continue
            root = _root_id(schema, canonical)
            if root in seen_roots:
                raise GenerationError(
                    f"schema {schema.name!r} generated duplicate root {root!r}"
                )
            chosen = (
                schema,
                parameter_index,
                candidate,
                canonical,
                formula,
                root,
            )
            break
        if chosen is not None:
            break
    if chosen is None:
        raise GenerationError(
            f"no unique checked schema can fill the remaining {remaining} row(s)"
        )
    return chosen


def _schedule_digest_record(
    *,
    schema: Schema,
    parameter_index: int,
    candidate: Candidate,
    canonical: str,
    root: str,
) -> bytes:
    return (
        json.dumps(
            [schema.name, parameter_index, canonical, list(candidate.tactics), root],
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        + b"\n"
    )


def _validate_arguments(
    seed: object,
    row_budget: object,
    budget_mode: object,
) -> tuple[str, int, str]:
    if not _safe_text(seed, nonempty=True):
        raise ValueError("seed must be non-empty control-free text")
    if type(row_budget) is not int or isinstance(row_budget, bool):
        raise TypeError("row_budget must be an integer")
    if not 1 <= row_budget <= MAX_ROW_BUDGET:
        raise ValueError(f"row_budget must be between 1 and {MAX_ROW_BUDGET}")
    if budget_mode not in BUDGET_MODES:
        raise ValueError("budget_mode must be 'exact' or 'complete-session'")
    assert type(seed) is str and type(budget_mode) is str
    return seed, row_budget, budget_mode


def _plan_schedule(
    *,
    seed: str,
    row_budget: int,
    budget_mode: str,
) -> dict[str, object]:
    """Plan every root without executing tactics or emitting partial data."""

    seed, row_budget, budget_mode = _validate_arguments(
        seed,
        row_budget,
        budget_mode,
    )
    schedule = _Schedule(seed, Counter(), Counter(), Counter())
    sessions = 0
    rows = 0
    schema_counts: Counter[str] = Counter()
    seen_statements: set[str] = set()
    seen_roots: set[str] = set()
    digest = hashlib.sha256()
    while rows < row_budget:
        chosen = _select_candidate(
            schedule,
            sessions=sessions,
            remaining=row_budget - rows,
            budget_mode=budget_mode,
            seen_statements=seen_statements,
            seen_roots=seen_roots,
        )
        schema, parameter_index, candidate, canonical, _, root = chosen
        first_head = candidate.tactics[0].split(maxsplit=1)[0]
        digest.update(
            _schedule_digest_record(
                schema=schema,
                parameter_index=parameter_index,
                candidate=candidate,
                canonical=canonical,
                root=root,
            )
        )
        sessions += 1
        rows += len(candidate.tactics)
        schedule.head_counts[first_head] += 1
        schema_counts[schema.name] += 1
        seen_statements.add(canonical)
        seen_roots.add(root)

    head_values = tuple(schedule.head_counts[head] for head in ROOT_HEADS)
    if 5 * schedule.head_counts["intro"] > sessions:
        raise GenerationError("planned intro roots exceed the twenty-percent cap")
    if max(head_values) - min(head_values) > 1:
        raise GenerationError("planned root tactic heads are not session-balanced")
    return {
        "sessions": sessions,
        "positive_tactic_rows": rows,
        "independent_roots": len(seen_roots),
        "unique_canonical_statements": len(seen_statements),
        "root_sessions_by_first_tactic_head": {
            head: schedule.head_counts[head] for head in ROOT_HEADS
        },
        "sessions_by_schema": dict(sorted(schema_counts.items())),
        "candidate_skips": {
            "duplicate_statement": schedule.duplicate_skips,
            "held_out_target": schedule.held_out_skips,
            "overlong_exact_fill": schedule.overlong_skips,
        },
        "sequence_sha256": digest.hexdigest(),
    }


def generate_corpus(
    trace_output: str | os.PathLike[str],
    metadata_output: str | os.PathLike[str],
    manifest_output: str | os.PathLike[str],
    *,
    seed: str = DEFAULT_SEED,
    row_budget: int = DEFAULT_ROW_BUDGET,
    budget_mode: str = "exact",
) -> GenerationResult:
    """Generate complete checked sessions under the full model-v3 prefix."""

    seed, row_budget, budget_mode = _validate_arguments(
        seed, row_budget, budget_mode
    )
    _validate_catalog()
    schedule_plan = _plan_schedule(
        seed=seed,
        row_budget=row_budget,
        budget_mode=budget_mode,
    )
    environment = _policy_environment()
    capabilities = _policy_capabilities()
    trace_path = Path(trace_output)
    metadata_path = Path(metadata_output)
    manifest_path = Path(manifest_output)
    destinations = (trace_path, metadata_path, manifest_path)
    source._preflight_outputs(destinations)

    sources = _source_manifest()
    fingerprint = _generation_fingerprint(
        seed=seed,
        row_budget=row_budget,
        budget_mode=budget_mode,
        sources=sources,
        environment=environment,
    )
    trace_stream, trace_temporary = source._open_staged(trace_path)
    metadata_stream, metadata_temporary = source._open_staged(metadata_path)
    manifest_stream: TextIO | None = None
    manifest_temporary: Path | None = None
    trace_writer = _DigestingWriter(trace_stream)
    metadata_writer = _DigestingWriter(metadata_stream)

    schedule = _Schedule(seed, Counter(), Counter(), Counter())
    sessions = 0
    rows = 0
    proof_nodes = 0
    schema_counts: Counter[str] = Counter()
    domain_counts: Counter[str] = Counter()
    root_kind_counts: Counter[str] = Counter()
    tactic_heads: Counter[str] = Counter()
    seen_statements: set[str] = set()
    seen_roots: set[str] = set()
    schedule_digest = hashlib.sha256()
    manifest: dict[str, object]

    try:
        while rows < row_budget:
            remaining = row_budget - rows
            chosen = _select_candidate(
                schedule,
                sessions=sessions,
                remaining=remaining,
                budget_mode=budget_mode,
                seen_statements=seen_statements,
                seen_roots=seen_roots,
            )
            schema, parameter_index, candidate, canonical, formula, root = chosen
            first_head = candidate.tactics[0].split(maxsplit=1)[0]
            schedule_digest.update(
                _schedule_digest_record(
                    schema=schema,
                    parameter_index=parameter_index,
                    candidate=candidate,
                    canonical=canonical,
                    root=root,
                )
            )
            ordinal = sessions + 1
            session_id = f"peano-synth-v3-{fingerprint[:20]}-{ordinal:07d}"
            result = run_proof(
                candidate.statement,
                candidate.tactics,
                request_id=f"synthetic-v3-{schema.name}-{ordinal}",
                classical=False,
                capabilities=capabilities,
                trace_sink=trace_writer,
                session_id=session_id,
            )
            transitions = _checked_result(
                result,
                schema=schema,
                candidate=candidate,
                canonical_statement=canonical,
                environment=environment,
            )
            metadata = _metadata_record(
                schema=schema,
                candidate=candidate,
                result=result,
                canonical_statement=canonical,
                root_formula=formula,
                root=root,
                first_head=first_head,
                seed=seed,
                parameter_index=parameter_index,
                ordinal=ordinal,
                environment=environment,
            )
            metadata_writer.write(_line_json(metadata))

            transition_count = len(transitions)
            sessions += 1
            rows += transition_count
            proof_nodes += result.proof_nodes or 0
            schedule.head_counts[first_head] += 1
            schema_counts[schema.name] += 1
            domain_counts[schema.domain] += 1
            root_kind_counts[metadata["root_kind"]] += 1  # type: ignore[index]
            tactic_heads.update(
                command.split(maxsplit=1)[0] for command in candidate.tactics
            )
            seen_statements.add(canonical)
            seen_roots.add(root)

        if 5 * schedule.head_counts["intro"] > sessions:
            raise GenerationError("intro roots exceeded the twenty-percent cap")

        source._finish_staged(trace_stream)
        source._finish_staged(metadata_stream)

        head_values = tuple(schedule.head_counts[head] for head in ROOT_HEADS)
        if max(head_values) - min(head_values) > 1:
            raise GenerationError("root tactic heads are not session-balanced")
        observed_plan = {
            "sessions": sessions,
            "positive_tactic_rows": rows,
            "independent_roots": len(seen_roots),
            "unique_canonical_statements": len(seen_statements),
            "root_sessions_by_first_tactic_head": {
                head: schedule.head_counts[head] for head in ROOT_HEADS
            },
            "sessions_by_schema": dict(sorted(schema_counts.items())),
            "candidate_skips": {
                "duplicate_statement": schedule.duplicate_skips,
                "held_out_target": schedule.held_out_skips,
                "overlong_exact_fill": schedule.overlong_skips,
            },
            "sequence_sha256": schedule_digest.hexdigest(),
        }
        if observed_plan != schedule_plan:
            raise GenerationError(
                "executed corpus differs from its fail-fast schedule plan"
            )
        missing_root_kinds = REQUIRED_ROOT_KINDS.difference(root_kind_counts)
        manifest = {
            "format": FORMAT,
            "version": VERSION,
            "profile": PROFILE,
            "trace_version": TRACE_VERSION,
            "catalog_version": CATALOG_VERSION,
            "generator": GENERATOR,
            "run_fingerprint": fingerprint,
            "runtime": _runtime_record(),
            "config": {
                "seed": seed,
                "row_budget": row_budget,
                "budget_mode": budget_mode,
                "selection": SCHEDULE_SELECTION,
                "stopping": (
                    "complete-sessions-exact-positive-row-budget-v1"
                    if budget_mode == "exact"
                    else "complete-sessions-at-least-positive-row-budget-v1"
                ),
                "intro_root_maximum_percent": INTRO_ROOT_PERCENT,
            },
            "environment": environment_record(environment),
            "authority_schedule": {
                "method": "full-synthetic-v1",
                "library_prefix_length": environment.library_prefix_length,
                "library_size": environment.library_full_length,
                "library_full_identity_sha256": environment.library_full_identity_sha256,
            },
            "evaluation_exclusion": {
                "rule": "exact canonical model-v3 target exclusion",
                "held_out_contract_sha256": held_out_contract_sha256(
                    PEANO_PROMPT_V3
                ),
                "names": sorted(HELD_OUT_NAMES),
                "formulas": sorted(HELD_OUT_FORMULAS),
            },
            "sources": sources,
            "schemas": [
                {
                    "name": schema.name,
                    "domain": schema.domain,
                    "tags": list(schema.tags),
                    "first_head": _first_head(schema),
                }
                for schema in SCHEMAS
            ],
            "artifacts": {
                "trace": {
                    "path": trace_path.name,
                    "bytes": trace_writer.bytes_written,
                    "sha256": trace_writer.sha256,
                },
                "metadata": {
                    "path": metadata_path.name,
                    "bytes": metadata_writer.bytes_written,
                    "sha256": metadata_writer.sha256,
                },
            },
            "counts": {
                "sessions": sessions,
                "kernel_checked_qed": sessions,
                "transition_records": rows,
                "positive_tactic_rows": rows,
                "footer_records": sessions,
                "proof_nodes": proof_nodes,
                "independent_roots": len(seen_roots),
                "unique_canonical_statements": len(seen_statements),
                "sessions_by_domain": dict(sorted(domain_counts.items())),
                "sessions_by_schema": dict(sorted(schema_counts.items())),
                "sessions_by_root_kind": dict(sorted(root_kind_counts.items())),
                "root_sessions_by_first_tactic_head": {
                    head: schedule.head_counts[head] for head in ROOT_HEADS
                },
                "root_head_session_imbalance": max(head_values) - min(head_values),
                "intro_root_sessions": schedule.head_counts["intro"],
                "intro_root_percent": (
                    100 * schedule.head_counts["intro"] / sessions
                ),
                "tactic_heads": dict(sorted(tactic_heads.items())),
            },
            "curriculum": {
                "unit": "complete kernel-checked proof session",
                "stratum": "first successful tactic head at the original root",
                "root_heads": list(ROOT_HEADS),
                "required_root_kinds": sorted(REQUIRED_ROOT_KINDS),
                "missing_root_kinds": sorted(missing_root_kinds),
                "intro_root_maximum_percent": INTRO_ROOT_PERCENT,
                "artificial_induction_gates": 0,
                "schedule_plan": schedule_plan,
                "library_schemas": 0,
            },
            "limitations": [
                "synthetic proof-first roots, not unrestricted conjecture generation",
                "positive checked QED sessions only",
                "library trajectories and retrieval supervision are generated separately",
                "very small row budgets cannot contain every root constructor stratum",
            ],
        }
        manifest_text = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
        manifest_stream, manifest_temporary = source._open_staged(manifest_path)
        manifest_stream.write(manifest_text)
        source._finish_staged(manifest_stream)
        manifest_stream = None

        source._publish_staged(
            (
                (trace_path, trace_temporary),
                (metadata_path, metadata_temporary),
                (manifest_path, manifest_temporary),
            )
        )
        trace_temporary = metadata_temporary = manifest_temporary = Path()
    finally:
        for stream in (trace_stream, metadata_stream, manifest_stream):
            if stream is not None and not stream.closed:
                stream.close()
        for temporary in (trace_temporary, metadata_temporary, manifest_temporary):
            if temporary is not None and temporary != Path():
                temporary.unlink(missing_ok=True)

    return GenerationResult(trace_path, metadata_path, manifest_path, manifest)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=(PROFILE,), required=True)
    parser.add_argument("--trace-output", required=True)
    parser.add_argument("--metadata-output", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--seed", default=DEFAULT_SEED)
    parser.add_argument("--row-budget", type=int, default=DEFAULT_ROW_BUDGET)
    parser.add_argument("--budget-mode", choices=BUDGET_MODES, default="exact")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        result = generate_corpus(
            args.trace_output,
            args.metadata_output,
            args.manifest,
            seed=args.seed,
            row_budget=args.row_budget,
            budget_mode=args.budget_mode,
        )
    except (GenerationError, OSError, TypeError, ValueError) as exc:
        print(f"model-v3 synthetic generation failed: {exc}", file=sys.stderr)
        return 2
    counts = result.manifest["counts"]
    print(
        f"generated {counts['sessions']} kernel-checked sessions / "
        f"{counts['positive_tactic_rows']} positive rows; "
        f"manifest: {result.manifest_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "BUDGET_MODES",
    "Candidate",
    "GenerationError",
    "GenerationResult",
    "HELD_OUT_FORMULAS",
    "PROFILE",
    "REQUIRED_ROOT_KINDS",
    "ROOT_HEADS",
    "ROOT_SCHEMAS",
    "REUSED_SCHEMAS",
    "SCHEMAS",
    "generate_corpus",
    "main",
]
