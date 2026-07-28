#!/usr/bin/env python3
"""Generate a scalable, proof-first Peano policy corpus.

This module is a data driver around :func:`peano_lab.batch.run_proof`, not a
second prover.  Each schema constructs a true statement together with an
ordinary public-surface tactic script.  The production headless runner then
parses the statement, executes the script under the fixed ``model-v2``
capability set, builds a certificate, and asks the independent kernel to check
QED against the original statement.  Model-v2 keeps the 25-command language
from model-v1, but binds the current public theorem catalog while removing the
four sealed evaluation targets and every theorem depending on one of them from
its import authority.

Generation is bounded by *successful tactic rows*.  A session is either
written completely (all transitions and its footer) or the unpublished staged
artifact set is discarded.  The resulting raw trace, metadata JSONL, and
manifest use the same three-artifact contract as the curated M19 pilot.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
import tempfile
import unicodedata
from collections import Counter
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = REPOSITORY_ROOT / "scripts"
PEANO_PYTHON = REPOSITORY_ROOT / "peano-lab" / "py"
for import_root in (REPOSITORY_ROOT, PEANO_PYTHON):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from peano_lab.batch import (  # noqa: E402
    MODEL_V1_COMMANDS,
    BatchResult,
    capability_sha256,
    run_proof,
)
from peano_lab.engine.trace import TRACE_VERSION  # noqa: E402
from peano_lab.kernel.formulas import (  # noqa: E402
    ParseError,
    parse_formula_with_names,
    pretty_formula,
)
from peano_lab.library.theorems import THEOREMS, TheoremSpec  # noqa: E402
from peano_lab.ui.prove import SurfaceCapabilities  # noqa: E402
from training.peano_policy.contract import (  # noqa: E402
    EXCLUDED_POLICY_LIBRARY_NAMES,
    HELD_OUT_POLICY_GOALS,
    HELD_OUT_POLICY_NAMES,
    MODEL_V2_THEOREMS as CONTRACT_MODEL_V2_THEOREMS,
    canonical_held_out_formulas,
    environment_record,
    held_out_contract_sha256,
    model_v2_environment,
)
from training.peano_policy.library_identity import (  # noqa: E402
    EXPECTED_MODEL_V2_LIBRARY_COUNT,
    EXPECTED_PUBLIC_LIBRARY_COUNT,
    MOD5_SOURCE_REPORT,
    PUBLIC_LIBRARY_CATALOG,
    model_v2_library_identity_record,
    model_v2_library_identity_sha256,
)


FORMAT = "peano-policy-corpus"
VERSION = 1
PROFILE = "model-v2"
CATALOG_VERSION = 4
GENERATOR = "proof-first-synthetic-v2"
DEFAULT_SEED = "peano-synthetic-v2"
DEFAULT_ROW_BUDGET = 1_000
MAX_ROW_BUDGET = 100_000
HELD_OUT_NAMES = HELD_OUT_POLICY_NAMES
EXCLUDED_LIBRARY_NAMES = EXCLUDED_POLICY_LIBRARY_NAMES
HELD_OUT_FORMULAS = frozenset(canonical_held_out_formulas())
MODEL_V2_THEOREMS = frozenset(CONTRACT_MODEL_V2_THEOREMS)
MODEL_V2_THEOREM_SPECS: tuple[TheoremSpec, ...] = tuple(
    spec for spec in THEOREMS if spec.name in MODEL_V2_THEOREMS
)
POLICY_CAPABILITIES = SurfaceCapabilities(
    label="model-v2",
    allowed_commands=MODEL_V1_COMMANDS,
    allowed_theorems=MODEL_V2_THEOREMS,
)
CAPABILITY_FIELDS = ("label", "allowed_commands", "allowed_theorems")
DOMAINS = ("logic", "equality", "recurrence", "witnesses", "arithmetic")
LANE_WEIGHTS: tuple[tuple[str, int], ...] = (
    ("foundation", 2),
    ("induction", 1),
    ("library", 1),
)
LANES = tuple(lane for lane, _ in LANE_WEIGHTS)
LANE_WEIGHT_BY_NAME = dict(LANE_WEIGHTS)
MIN_BALANCE_AUDIT_ROWS = 1_000


class GenerationError(RuntimeError):
    """The generator cannot publish a sound, reproducible corpus."""


@dataclass(frozen=True, slots=True)
class Candidate:
    """One proof-first concrete theorem before checked execution."""

    statement: str
    tactics: tuple[str, ...]
    parameters: dict[str, object]


@dataclass(frozen=True, slots=True)
class Schema:
    """A deterministic family of concrete statements and tactic proofs."""

    name: str
    domain: str
    tags: tuple[str, ...]
    build: Callable[[int], Candidate]
    lane: str = "foundation"
    weight: int = 1


@dataclass(frozen=True, slots=True)
class GenerationResult:
    """Published paths and exact manifest for one completed generation."""

    trace_path: Path
    metadata_path: Path
    manifest_path: Path
    manifest: dict[str, object]


class _DigestingWriter:
    """Write UTF-8 text while hashing the exact bytes accepted by the file."""

    __slots__ = ("stream", "digest", "bytes_written")

    def __init__(self, stream: TextIO) -> None:
        self.stream = stream
        self.digest = hashlib.sha256()
        self.bytes_written = 0

    def write(self, text: str) -> int:
        if type(text) is not str:
            raise TypeError("artifact writers accept text only")
        accepted = self.stream.write(text)
        if accepted != len(text):
            raise GenerationError(
                f"staged artifact short write: accepted {accepted!r} of "
                f"{len(text)} characters"
            )
        encoded = text.encode("utf-8")
        self.digest.update(encoded)
        self.bytes_written += len(encoded)
        return accepted

    @property
    def sha256(self) -> str:
        return self.digest.hexdigest()


def _safe_text(value: object, *, nonempty: bool = False) -> bool:
    if type(value) is not str or (nonempty and not value):
        return False
    return not any(
        unicodedata.category(char) in {"Cc", "Cf", "Cs", "Zl", "Zp"}
        for char in value
    )


def _line_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(128 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _capability_record() -> dict[str, object]:
    record = {
        "label": POLICY_CAPABILITIES.label,
        "allowed_commands": sorted(POLICY_CAPABILITIES.allowed_commands or ()),
        "allowed_theorems": sorted(POLICY_CAPABILITIES.allowed_theorems or ()),
    }
    if tuple(record) != CAPABILITY_FIELDS:
        raise RuntimeError("internal capability field order changed")
    return record


def _source_manifest() -> dict[str, dict[str, str]]:
    """Hash every local source that can affect generated proof meaning."""

    paths = (
        Path(__file__).resolve(),
        SCRIPTS_ROOT / "export_traces.py",
        REPOSITORY_ROOT / "training" / "peano_policy" / "contract.py",
        REPOSITORY_ROOT / "training" / "peano_policy" / "prompt.py",
        REPOSITORY_ROOT / "training" / "peano_policy" / "library_identity.py",
        MOD5_SOURCE_REPORT,
        PUBLIC_LIBRARY_CATALOG,
        *sorted((PEANO_PYTHON / "peano_lab").rglob("*.py")),
    )
    return {
        path.relative_to(REPOSITORY_ROOT).as_posix(): {
            "sha256": _sha256_file(path)
        }
        for path in paths
    }


def _runtime_record() -> dict[str, str]:
    return {
        "implementation": platform.python_implementation(),
        "python": platform.python_version(),
    }


def _library_snapshot() -> dict[str, object]:
    """Return the exact public catalog and sealed model-v2 import boundary."""

    entries = [
        {
            "name": spec.name,
            "statement": pretty_formula(
                parse_formula_with_names(spec.statement)[0], []
            ),
            "dependencies": list(spec.dependencies),
        }
        for spec in THEOREMS
    ]
    encoded = json.dumps(
        entries,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return {
        "catalog_entries": len(entries),
        "catalog_sha256": hashlib.sha256(encoded).hexdigest(),
        "entries": entries,
        "allowed_imports": sorted(MODEL_V2_THEOREMS),
        "allowed_import_count": len(MODEL_V2_THEOREMS),
        "excluded_imports": sorted(EXCLUDED_LIBRARY_NAMES),
        "excluded_import_count": len(EXCLUDED_LIBRARY_NAMES),
        "checked_authority": model_v2_library_identity_record(),
        "checked_authority_sha256": model_v2_library_identity_sha256(),
        "prompt_library_identity_sha256": model_v2_environment().library_sha256,
        "sealed_evaluation_targets": [
            {"name": name, "statement": statement}
            for (name, _), statement in zip(
                HELD_OUT_POLICY_GOALS,
                canonical_held_out_formulas(),
                strict=True,
            )
        ],
        "held_out_contract_sha256": held_out_contract_sha256(),
    }


def _digits(value: int, base: int, count: int) -> tuple[int, ...]:
    result: list[int] = []
    for _ in range(count):
        result.append(value % base)
        value //= base
    return tuple(result)


def _term(index: int, variable: str = "n") -> str:
    """Return one bounded open arithmetic term from a 40,000-shape grammar."""

    value = index % 40_000
    a, b, c, d = _digits(value % 10_000, 10, 4)
    shape = value // 10_000
    if shape == 0:
        return f"(({variable} + {a}) * {b + 1} + ({c} * {variable} + {d}))"
    if shape == 1:
        return f"(({a} * {variable} + {b}) + S ({variable} + {c}) + {d})"
    if shape == 2:
        return f"((S {variable} * {a + 1} + {b}) * {c + 1} + {d})"
    return f"(({variable} + {a}) * ({b} + {c + 1}) + S ({variable} + {d}))"


def _small_term(index: int, variable: str = "n") -> str:
    a, b, c, d = _digits(index % 4_096, 8, 4)
    return f"((({variable} + {a}) + {b}) + {c}) + {d}"


def _numeric_expression(index: int) -> tuple[str, int, tuple[int, ...]]:
    digits = _digits(index % 65_536, 4, 8)
    a, b, c, d, e, f, g, h = digits
    expression = f"(({a} * {b} + {c}) + ({d} * {e} + {f})) + ({g} + {h})"
    return expression, a * b + c + d * e + f + g + h, digits


def _terms(index: int) -> tuple[str, str, str, str]:
    return (
        _term(index * 5 + 1),
        _term(index * 5 + 2),
        _term(index * 5 + 3),
        _term(index * 5 + 4),
    )


def _candidate(
    statement: str,
    tactics: Sequence[str],
    **parameters: object,
) -> Candidate:
    return Candidate(statement, tuple(tactics), dict(parameters))


# Logic schemas use arithmetic formulas as atoms.  Truth does not come from
# trusting those atoms: each proof uses only the displayed hypotheses and
# ordinary logical constructors.
def _logic_identity(index: int) -> Candidate:
    term = _term(index)
    atom = f"{term} = {term}"
    return _candidate(
        f"forall n. ({atom}) -> ({atom})",
        ("intro n", "intro h", "exact h"),
        term=term,
    )


def _logic_and_swap(index: int) -> Candidate:
    left, right, _, _ = _terms(index)
    p, q = f"{left} = {left}", f"{right} = {right}"
    return _candidate(
        f"forall n. (({p}) /\\ ({q})) -> ({q}) /\\ ({p})",
        (
            "intro n",
            "intro h",
            "cases h",
            "split",
            "exact h_right",
            "exact h_left",
        ),
        left=left,
        right=right,
    )


def _logic_or_swap(index: int) -> Candidate:
    left, right, _, _ = _terms(index)
    p, q = f"{left} = {left}", f"{right} = {right}"
    return _candidate(
        f"forall n. (({p}) \\/ ({q})) -> ({q}) \\/ ({p})",
        (
            "intro n",
            "intro h",
            "cases h",
            "right",
            "exact h_left",
            "left",
            "exact h_right",
        ),
        left=left,
        right=right,
    )


def _logic_and_left(index: int) -> Candidate:
    left, right, _, _ = _terms(index)
    p, q = f"{left} = {left}", f"{right} = {right}"
    return _candidate(
        f"forall n. (({p}) /\\ ({q})) -> ({p})",
        ("intro n", "intro h", "cases h", "exact h_left"),
        left=left,
        right=right,
    )


def _logic_compose(index: int) -> Candidate:
    first, second, third, _ = _terms(index)
    p = f"{first} = {first}"
    q = f"{second} = {second}"
    r = f"{third} = {third}"
    return _candidate(
        f"forall n. (({p}) -> ({q})) -> (({q}) -> ({r})) -> ({p}) -> ({r})",
        (
            "intro n",
            "intro hpq",
            "intro hqr",
            "intro hp",
            "apply hqr",
            "apply hpq",
            "exact hp",
        ),
        first=first,
        second=second,
        third=third,
    )


def _equality_symmetry(index: int) -> Candidate:
    left, right, _, _ = _terms(index)
    return _candidate(
        f"forall n. {left} = {right} -> {right} = {left}",
        ("intro n", "intro h", "symm", "exact h"),
        left=left,
        right=right,
    )


def _equality_transitivity(index: int) -> Candidate:
    left, middle, right, _ = _terms(index)
    return _candidate(
        f"forall n. {left} = {middle} -> {middle} = {right} -> {left} = {right}",
        (
            "intro n",
            "intro h1",
            "intro h2",
            f"trans {middle}",
            "exact h1",
            "exact h2",
        ),
        left=left,
        middle=middle,
        right=right,
    )


def _equality_successor_congruence(index: int) -> Candidate:
    left, right, _, _ = _terms(index)
    return _candidate(
        f"forall n. {left} = {right} -> S ({left}) = S ({right})",
        ("intro n", "intro h", "congr", "exact h"),
        left=left,
        right=right,
    )


def _equality_add_congruence(index: int) -> Candidate:
    left, right, extra_left, extra_right = _terms(index)
    return _candidate(
        (
            f"forall n. {left} = {right} -> {extra_left} = {extra_right} -> "
            f"({left}) + ({extra_left}) = ({right}) + ({extra_right})"
        ),
        (
            "intro n",
            "intro h1",
            "intro h2",
            "congr",
            "exact h1",
            "exact h2",
        ),
        left=left,
        right=right,
        extra_left=extra_left,
        extra_right=extra_right,
    )


def _equality_rewrite_forward(index: int) -> Candidate:
    left, right, context, _ = _terms(index)
    return _candidate(
        f"forall n. {left} = {right} -> ({left}) + ({context}) = ({right}) + ({context})",
        ("intro n", "intro h", "rewrite h", "refl"),
        left=left,
        right=right,
        context=context,
    )


def _equality_rewrite_reverse(index: int) -> Candidate:
    left, right, context, _ = _terms(index)
    return _candidate(
        f"forall n. {left} = {right} -> ({right}) * ({context}) = ({left}) * ({context})",
        ("intro n", "intro h", "rewrite <- h", "refl"),
        left=left,
        right=right,
        context=context,
    )


def _recurrence_pa3(index: int) -> Candidate:
    term = _term(index)
    return _candidate(
        f"forall n. ({term}) + 0 = {term}",
        ("intro n", "rewrite PA3", "refl"),
        term=term,
        axiom="PA3",
    )


def _recurrence_pa4(index: int) -> Candidate:
    left, right, _, _ = _terms(index)
    return _candidate(
        f"forall n. ({left}) + S ({right}) = S (({left}) + ({right}))",
        ("intro n", "rewrite PA4", "refl"),
        left=left,
        right=right,
        axiom="PA4",
    )


def _recurrence_pa5(index: int) -> Candidate:
    term = _term(index)
    return _candidate(
        f"forall n. ({term}) * 0 = 0",
        ("intro n", "rewrite PA5", "refl"),
        term=term,
        axiom="PA5",
    )


def _recurrence_pa6(index: int) -> Candidate:
    left, right, _, _ = _terms(index)
    return _candidate(
        (
            f"forall n. ({left}) * S ({right}) = "
            f"({left}) * ({right}) + ({left})"
        ),
        ("intro n", "rewrite PA6", "refl"),
        left=left,
        right=right,
        axiom="PA6",
    )


def _recurrence_pa1(index: int) -> Candidate:
    term = _term(index)
    return _candidate(
        f"forall n. ~(S ({term}) = 0)",
        ("intro n", "intro h", "apply PA1", "exact h"),
        term=term,
        axiom="PA1",
    )


def _recurrence_pa2(index: int) -> Candidate:
    left, right, _, _ = _terms(index)
    return _candidate(
        f"forall n. S ({left}) = S ({right}) -> {left} = {right}",
        ("intro n", "intro h", "apply PA2", "exact h"),
        left=left,
        right=right,
        axiom="PA2",
    )


def _witness_right(index: int) -> Candidate:
    term = _term(index)
    return _candidate(
        f"forall n. exists x. {term} = x",
        ("intro n", f"exists {term}", "refl"),
        witness=term,
    )


def _witness_left(index: int) -> Candidate:
    term = _term(index)
    return _candidate(
        f"forall n. exists x. x = {term}",
        ("intro n", f"exists {term}", "refl"),
        witness=term,
    )


def _witness_pair(index: int) -> Candidate:
    term = _term(index)
    return _candidate(
        f"forall n. exists x. (x = {term}) /\\ ({term} = x)",
        ("intro n", f"exists {term}", "split", "refl", "refl"),
        witness=term,
    )


def _witness_add_zero(index: int) -> Candidate:
    term = _term(index)
    return _candidate(
        f"forall n. exists x. ({term}) + x = {term}",
        ("intro n", "exists 0", "rewrite PA3", "refl"),
        witness="0",
        term=term,
    )


def _witness_mul_zero(index: int) -> Candidate:
    term = _term(index)
    return _candidate(
        f"forall n. exists x. ({term}) * x = 0",
        ("intro n", "exists 0", "rewrite PA5", "refl"),
        witness="0",
        term=term,
    )


def _witness_repack(index: int) -> Candidate:
    term = _term(index)
    return _candidate(
        f"forall n. (exists x. x = {term}) -> exists y. y = {term}",
        ("intro n", "intro h", "cases h", "exists x", "exact h_witness"),
        term=term,
    )


def _witness_two(index: int) -> Candidate:
    left, right, _, _ = _terms(index)
    return _candidate(
        (
            f"forall n. (exists x. x = {left}) /\\ "
            f"(exists y. {right} = y)"
        ),
        (
            "intro n",
            "split",
            f"exists {left}",
            "refl",
            f"exists {right}",
            "refl",
        ),
        left=left,
        right=right,
    )


def _arithmetic_closed_norm(index: int) -> Candidate:
    expression, value, digits = _numeric_expression(index)
    return _candidate(
        f"{expression} = {value}",
        ("norm_num",),
        digits=list(digits),
        value=value,
    )


def _arithmetic_open_norm(index: int) -> Candidate:
    expression, value, digits = _numeric_expression(index)
    return _candidate(
        f"forall n. ({expression}) * n = {value} * n",
        ("intro n", "norm_num"),
        digits=list(digits),
        value=value,
    )


def _arithmetic_ring_square(index: int) -> Candidate:
    a, b, c, d = _digits(index % 4_096, 8, 4)
    return _candidate(
        (
            f"forall n. ((n + {a}) * (n + {b})) + {c} * n + {d} = "
            f"n * n + {a + b + c} * n + {a * b + d}"
        ),
        ("intro n", "ring"),
        coefficients=[a, b, c, d],
    )


def _arithmetic_ring_product(index: int) -> Candidate:
    a, b, c, d = _digits(index % 4_096, 8, 4)
    return _candidate(
        (
            f"forall n m. ((n + {a}) * (m + {b})) + {c} * n + {d} * m = "
            f"n * m + {b + c} * n + {a + d} * m + {a * b}"
        ),
        ("intro n", "intro m", "ring"),
        coefficients=[a, b, c, d],
    )


def _arithmetic_compact(index: int) -> Candidate:
    term = _small_term(index)
    return _candidate(
        f"forall n. ({term}) + 1 = S ({term})",
        ("intro n", "compact_arith"),
        term=term,
    )


# Model-v2 coverage schemas.  These are deliberately small public-surface
# programs: their purpose is to expose state shapes and tactic heads that the
# first synthetic catalog never emitted, not to add a second proof procedure.
def _logic_assumption(index: int) -> Candidate:
    term = _term(index)
    atom = f"({term}) = ({term})"
    return _candidate(
        f"forall n. ({atom}) -> ({atom})",
        ("intro n", "intro h", "assumption"),
        term=term,
    )


def _logic_exfalso(index: int) -> Candidate:
    term = _term(index)
    return _candidate(
        f"forall n. S ({term}) = 0 -> ({term}) = ({term})",
        ("intro n", "intro h", "exfalso", "apply PA1", "exact h"),
        term=term,
    )


def _logic_specialize(index: int) -> Candidate:
    term = _term(index)
    return _candidate(
        f"forall n. (forall x. x + 0 = x) -> ({term}) + 0 = ({term})",
        ("intro n", "intro h", f"specialize h {term}", "exact h"),
        term=term,
    )


def _logic_forall_elim(index: int) -> Candidate:
    term = _term(index)
    return _candidate(
        f"forall n. (forall x. x + 0 = x) -> ({term}) + 0 = ({term})",
        ("intro n", "intro h", f"forall_elim h {term}", "exact h"),
        term=term,
    )


def _logic_have(index: int) -> Candidate:
    term = _term(index)
    atom = f"({term}) = ({term})"
    return _candidate(
        f"forall n. {atom}",
        ("intro n", f"have h : {atom}", "refl", "exact h"),
        term=term,
    )


def _logic_suffices(index: int) -> Candidate:
    term = _term(index)
    atom = f"({term}) = ({term})"
    return _candidate(
        f"forall n. {atom}",
        ("intro n", f"suffices h : {atom}", "exact h", "refl"),
        term=term,
    )


def _induction_add_zero(index: int) -> Candidate:
    gate = f"forall a. ({_term(index, 'a')}) = ({_term(index, 'a')})"
    return _candidate(
        f"({gate}) -> forall n. 0 + n = n",
        ("intro gate", "induction n", "simp", "simp [IH]"),
        gate=gate,
        induction_variable="n",
    )


def _induction_mul_zero(index: int) -> Candidate:
    gate = f"forall a. ({_term(index, 'a')}) = ({_term(index, 'a')})"
    return _candidate(
        f"({gate}) -> forall n. 0 * n = 0",
        ("intro gate", "induction n", "simp", "simp [IH]"),
        gate=gate,
        induction_variable="n",
    )


def _induction_add_one(index: int) -> Candidate:
    gate = f"forall a. ({_term(index, 'a')}) = ({_term(index, 'a')})"
    return _candidate(
        f"({gate}) -> forall n. n + 0 = n",
        ("intro gate", "induction n", "simp", "simp [IH]"),
        gate=gate,
        induction_variable="n",
    )


def _induction_explicit_ih(index: int) -> Candidate:
    gate = f"forall a. ({_term(index, 'a')}) = ({_term(index, 'a')})"
    return _candidate(
        f"({gate}) -> forall n. 0 = 0",
        ("intro gate", "induction n", "refl", "exact IH"),
        gate=gate,
        induction_variable="n",
    )


def _library_gate(index: int, shape: str) -> str:
    term = _term(index, "z")
    if shape == "refl":
        return f"forall z. ({term}) = ({term})"
    if shape == "add-zero":
        return f"forall z. ({term}) + 0 = ({term})"
    if shape == "successor":
        return f"forall z. S ({term}) = S ({term})"
    if shape == "mul-zero":
        return f"forall z. ({term}) * 0 = ({term}) * 0"
    raise RuntimeError(f"unknown internal library gate shape {shape!r}")


def _library_selection(
    index: int,
    specs: Sequence[TheoremSpec] = MODEL_V2_THEOREM_SPECS,
) -> tuple[TheoremSpec, int]:
    if not specs:
        raise RuntimeError("model-v2 has no checked library theorems")
    return specs[index % len(specs)], index // len(specs)


def _library_import(index: int) -> Candidate:
    spec, variant = _library_selection(index)
    gate = _library_gate(variant, "refl")
    return _candidate(
        f"({gate}) -> ({spec.statement})",
        ("intro gate", f"use {spec.name}", f"exact {spec.name}"),
        gate=gate,
        retrieved_theorems=[spec.name],
        library_statement=spec.statement,
    )


def _library_conjunction(index: int) -> Candidate:
    spec, variant = _library_selection(index)
    gate = _library_gate(variant, "refl")
    return _candidate(
        f"({gate}) -> (({spec.statement}) /\\ ({gate}))",
        (
            "intro gate",
            "split",
            f"use {spec.name}",
            f"exact {spec.name}",
            "exact gate",
        ),
        gate=gate,
        retrieved_theorems=[spec.name],
        library_statement=spec.statement,
    )


def _library_have(index: int) -> Candidate:
    spec, variant = _library_selection(index)
    gate = _library_gate(variant, "add-zero")
    return _candidate(
        f"({gate}) -> ({spec.statement})",
        (
            "intro gate",
            f"have imported : {spec.statement}",
            f"use {spec.name}",
            f"exact {spec.name}",
            "exact imported",
        ),
        gate=gate,
        retrieved_theorems=[spec.name],
        library_statement=spec.statement,
    )


def _authored_specs(minimum: int, maximum: int) -> tuple[TheoremSpec, ...]:
    return tuple(
        spec
        for spec in MODEL_V2_THEOREM_SPECS
        if spec.dependencies
        and set(spec.dependencies) <= MODEL_V2_THEOREMS
        and minimum <= 1 + len(spec.dependencies) + len(spec.script) <= maximum
    )


MEDIUM_AUTHORED_SPECS = _authored_specs(8, 15)
LONG_AUTHORED_SPECS = _authored_specs(16, 32)


def _library_authored(index: int, specs: Sequence[TheoremSpec], shape: str) -> Candidate:
    spec, variant = _library_selection(index, specs)
    gate = _library_gate(variant, shape)
    imports = tuple(f"use {dependency}" for dependency in spec.dependencies)
    return _candidate(
        f"({gate}) -> ({spec.statement})",
        ("intro gate", *imports, *spec.script),
        gate=gate,
        retrieved_theorems=list(spec.dependencies),
        authored_theorem=spec.name,
        library_statement=spec.statement,
    )


def _library_authored_medium(index: int) -> Candidate:
    return _library_authored(index, MEDIUM_AUTHORED_SPECS, "successor")


def _library_authored_long(index: int) -> Candidate:
    return _library_authored(index, LONG_AUTHORED_SPECS, "mul-zero")


SCHEMAS: tuple[Schema, ...] = (
    Schema("logic-identity", "logic", ("logic", "intro", "exact"), _logic_identity),
    Schema("logic-and-swap", "logic", ("logic", "cases", "split"), _logic_and_swap),
    Schema("logic-or-swap", "logic", ("logic", "cases", "disjunction"), _logic_or_swap),
    Schema("logic-and-left", "logic", ("logic", "cases", "exact"), _logic_and_left),
    Schema("logic-compose", "logic", ("logic", "apply", "composition"), _logic_compose),
    Schema("equality-symmetry", "equality", ("equality", "symm"), _equality_symmetry),
    Schema("equality-transitivity", "equality", ("equality", "trans"), _equality_transitivity),
    Schema(
        "equality-successor-congruence",
        "equality",
        ("equality", "congr"),
        _equality_successor_congruence,
    ),
    Schema(
        "equality-add-congruence",
        "equality",
        ("equality", "congr", "addition"),
        _equality_add_congruence,
    ),
    Schema(
        "equality-rewrite-forward",
        "equality",
        ("equality", "rewrite"),
        _equality_rewrite_forward,
    ),
    Schema(
        "equality-rewrite-reverse",
        "equality",
        ("equality", "rewrite", "reverse"),
        _equality_rewrite_reverse,
    ),
    Schema("recurrence-pa3", "recurrence", ("recurrence", "rewrite", "PA3"), _recurrence_pa3),
    Schema("recurrence-pa4", "recurrence", ("recurrence", "rewrite", "PA4"), _recurrence_pa4),
    Schema("recurrence-pa5", "recurrence", ("recurrence", "rewrite", "PA5"), _recurrence_pa5),
    Schema("recurrence-pa6", "recurrence", ("recurrence", "rewrite", "PA6"), _recurrence_pa6),
    Schema("recurrence-pa1", "recurrence", ("recurrence", "apply", "PA1"), _recurrence_pa1),
    Schema("recurrence-pa2", "recurrence", ("recurrence", "apply", "PA2"), _recurrence_pa2),
    Schema("witness-right", "witnesses", ("existential", "witness"), _witness_right),
    Schema("witness-left", "witnesses", ("existential", "witness"), _witness_left),
    Schema("witness-pair", "witnesses", ("existential", "split"), _witness_pair),
    Schema("witness-add-zero", "witnesses", ("existential", "addition", "PA3"), _witness_add_zero),
    Schema(
        "witness-mul-zero",
        "witnesses",
        ("existential", "multiplication", "PA5"),
        _witness_mul_zero,
    ),
    Schema("witness-repack", "witnesses", ("existential", "cases"), _witness_repack),
    Schema("witness-two", "witnesses", ("existential", "split"), _witness_two),
    Schema(
        "arithmetic-closed-norm",
        "arithmetic",
        ("arithmetic", "norm_num", "closed"),
        _arithmetic_closed_norm,
    ),
    Schema(
        "arithmetic-open-norm",
        "arithmetic",
        ("arithmetic", "norm_num", "open"),
        _arithmetic_open_norm,
    ),
    Schema(
        "arithmetic-ring-square",
        "arithmetic",
        ("arithmetic", "ring", "polynomial"),
        _arithmetic_ring_square,
    ),
    Schema(
        "arithmetic-ring-product",
        "arithmetic",
        ("arithmetic", "ring", "polynomial"),
        _arithmetic_ring_product,
    ),
    Schema(
        "arithmetic-compact",
        "arithmetic",
        ("arithmetic", "compact_arith"),
        _arithmetic_compact,
    ),
    Schema(
        "logic-assumption",
        "logic",
        ("logic", "context", "assumption"),
        _logic_assumption,
        lane="foundation",
        weight=3,
    ),
    Schema(
        "logic-exfalso",
        "logic",
        ("logic", "false-elimination", "exfalso"),
        _logic_exfalso,
        lane="foundation",
        weight=3,
    ),
    Schema(
        "logic-specialize",
        "logic",
        ("logic", "universal", "specialize"),
        _logic_specialize,
        lane="foundation",
        weight=3,
    ),
    Schema(
        "logic-forall-elim",
        "logic",
        ("logic", "universal", "forall_elim"),
        _logic_forall_elim,
        lane="foundation",
        weight=3,
    ),
    Schema(
        "logic-have",
        "logic",
        ("logic", "local-cut", "have"),
        _logic_have,
        lane="foundation",
        weight=3,
    ),
    Schema(
        "logic-suffices",
        "logic",
        ("logic", "local-cut", "suffices"),
        _logic_suffices,
        lane="foundation",
        weight=3,
    ),
    Schema(
        "induction-add-zero",
        "arithmetic",
        ("arithmetic", "induction", "IH", "addition"),
        _induction_add_zero,
        lane="induction",
        weight=1,
    ),
    Schema(
        "induction-mul-zero",
        "arithmetic",
        ("arithmetic", "induction", "IH", "multiplication"),
        _induction_mul_zero,
        lane="induction",
        weight=1,
    ),
    Schema(
        "induction-add-one",
        "arithmetic",
        ("arithmetic", "induction", "IH", "successor"),
        _induction_add_one,
        lane="induction",
        weight=1,
    ),
    Schema(
        "induction-explicit-IH",
        "logic",
        ("logic", "induction", "IH", "exact"),
        _induction_explicit_ih,
        lane="induction",
        weight=1,
    ),
    Schema(
        "library-import",
        "logic",
        ("library", "retrieval", "use"),
        _library_import,
        lane="library",
        weight=5,
    ),
    Schema(
        "library-conjunction",
        "logic",
        ("library", "retrieval", "composition", "split"),
        _library_conjunction,
        lane="library",
        weight=1,
    ),
    Schema(
        "library-have",
        "logic",
        ("library", "retrieval", "composition", "have"),
        _library_have,
        lane="library",
        weight=1,
    ),
    Schema(
        "library-authored-medium",
        "arithmetic",
        ("library", "retrieval", "composition", "medium"),
        _library_authored_medium,
        lane="library",
        weight=1,
    ),
    Schema(
        "library-authored-long",
        "arithmetic",
        ("library", "retrieval", "composition", "long"),
        _library_authored_long,
        lane="library",
        weight=1,
    ),
)


def _validate_catalog() -> None:
    names: set[str] = set()
    if {schema.domain for schema in SCHEMAS} != set(DOMAINS):
        raise GenerationError("synthetic catalog does not cover every declared domain")
    if {schema.lane for schema in SCHEMAS} != set(LANES):
        raise GenerationError("synthetic catalog does not cover every curriculum lane")
    if (
        len(THEOREMS) != EXPECTED_PUBLIC_LIBRARY_COUNT
        or len(MODEL_V2_THEOREMS) != EXPECTED_MODEL_V2_LIBRARY_COUNT
    ):
        raise GenerationError(
            "model-v2 theorem counts differ from the pinned checked authority"
        )
    if MODEL_V2_THEOREMS & EXCLUDED_LIBRARY_NAMES:
        raise GenerationError("model-v2 import authority contains a sealed descendant")
    if capability_sha256(POLICY_CAPABILITIES) != model_v2_environment().sha256:
        raise GenerationError(
            "model-v2 runner authority differs from the prompt environment"
        )
    if not MEDIUM_AUTHORED_SPECS or not LONG_AUTHORED_SPECS:
        raise GenerationError("model-v2 needs both medium and long authored routes")
    for schema in SCHEMAS:
        if not _safe_text(schema.name, nonempty=True) or schema.name in names:
            raise GenerationError(f"duplicate or unsafe schema name {schema.name!r}")
        names.add(schema.name)
        if schema.domain not in DOMAINS:
            raise GenerationError(f"schema {schema.name!r} has an unknown domain")
        if schema.lane not in LANES:
            raise GenerationError(f"schema {schema.name!r} has an unknown lane")
        if type(schema.weight) is not int or schema.weight < 1:
            raise GenerationError(f"schema {schema.name!r} has an invalid weight")
        if not schema.tags or not all(_safe_text(tag, nonempty=True) for tag in schema.tags):
            raise GenerationError(f"schema {schema.name!r} has unsafe tags")


def _canonical_statement(candidate: Candidate, schema: Schema) -> str:
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
        raise GenerationError(
            f"schema {schema.name!r} emitted a sealed held-out target"
        )
    return canonical


def _rank(seed: str, epoch: int, label: str) -> str:
    material = json.dumps(
        [seed, CATALOG_VERSION, epoch, label],
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def _schema_offset(seed: str, schema: Schema) -> int:
    material = f"{seed}\0{CATALOG_VERSION}\0{schema.name}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(material).digest()[:4], "big") % 20_000


def _schema_schedule(seed: str, lane: str) -> Iterator[Schema]:
    """Yield an infinite deterministic weighted schedule inside one lane."""

    schemas = tuple(schema for schema in SCHEMAS if schema.lane == lane)
    if not schemas:
        raise GenerationError(f"curriculum lane {lane!r} has no schemas")
    epoch = 0
    while True:
        tickets = [
            (schema, ticket)
            for schema in schemas
            for ticket in range(schema.weight)
        ]
        tickets.sort(
            key=lambda item: (
                _rank(seed, epoch, f"{lane}:{item[0].name}:{item[1]}"),
                item[0].name,
                item[1],
            )
        )
        for schema, _ in tickets:
            yield schema
        epoch += 1


def _lane_order(
    seed: str,
    rows: int,
    lane_rows: Counter[str],
) -> tuple[str, ...]:
    """Put the most under-target row lane first, with a stable seeded tie."""

    total_weight = sum(LANE_WEIGHT_BY_NAME.values())
    return tuple(
        sorted(
            LANES,
            key=lambda lane: (
                -(
                    (rows + 1) * LANE_WEIGHT_BY_NAME[lane]
                    - lane_rows[lane] * total_weight
                ),
                _rank(seed, rows, f"lane:{lane}"),
                lane,
            ),
        )
    )


def _generation_fingerprint(
    *,
    seed: str,
    row_budget: int,
    sources: dict[str, dict[str, str]],
) -> str:
    payload = {
        "format": FORMAT,
        "version": VERSION,
        "profile": PROFILE,
        "catalog_version": CATALOG_VERSION,
        "generator": GENERATOR,
        "config": {"seed": seed, "row_budget": row_budget},
        "environment": environment_record(model_v2_environment()),
        "library_snapshot": _library_snapshot(),
        "curriculum": {
            "lane_row_weights": dict(LANE_WEIGHTS),
        },
        "runtime": _runtime_record(),
        "sources": sources,
        "schemas": [
            {
                "name": schema.name,
                "domain": schema.domain,
                "tags": list(schema.tags),
                "lane": schema.lane,
                "weight": schema.weight,
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
    digest = hashlib.sha256(encoded).hexdigest()[:20]
    return f"synthetic-v2/{schema.name}/{digest}"


def _checked_result(
    result: BatchResult,
    *,
    schema: Schema,
    candidate: Candidate,
    canonical_statement: str,
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
        result.surface != POLICY_CAPABILITIES.label
        or result.environment_sha256 != capability_sha256(POLICY_CAPABILITIES)
        or result.classical is not False
    ):
        raise GenerationError(f"schema {schema.name!r} escaped model-v2 authority")
    if result.trace is None or not result.trace:
        raise GenerationError(f"schema {schema.name!r} returned no binding trace")
    transitions = tuple(record for record in result.trace if "v" in record)
    if len(transitions) != len(candidate.tactics):
        raise GenerationError(
            f"schema {schema.name!r} emitted {len(transitions)} transitions for "
            f"{len(candidate.tactics)} authored tactic rows"
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
    root: str,
    seed: str,
    parameter_index: int,
    ordinal: int,
) -> dict[str, object]:
    theorem_id = f"synthetic.{schema.name}.{root.rsplit('/', 1)[-1]}"
    script_text = json.dumps(
        list(candidate.tactics),
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return {
        "session": result.session_id,
        "theorem": theorem_id,
        # The v1 builder joins either shared field into one split component.
        # Root-specific values preserve descendants without collapsing a broad
        # domain such as all arithmetic into one giant component.
        "family": root,
        "lineage": root,
        "classical": False,
        "surface": POLICY_CAPABILITIES.label,
        "environment_sha256": capability_sha256(POLICY_CAPABILITIES),
        "library_identity_sha256": model_v2_library_identity_sha256(),
        "capabilities": _capability_record(),
        "statement": canonical_statement,
        "statement_sha256": _sha256_text(canonical_statement),
        "script_sha256": _sha256_text(script_text),
        "template": schema.name,
        "domain": schema.domain,
        "tags": list(schema.tags),
        "lane": schema.lane,
        "schema_weight": schema.weight,
        "seed": seed,
        "ordinal": ordinal,
        "root": root,
        "variant": "authored-v2",
        "parents": [],
        "transformations": ["proof-first-schema-instantiation"],
        "parameter_index": parameter_index,
        "parameters": candidate.parameters,
        "tactics": list(candidate.tactics),
        "tactic_rows": len(candidate.tactics),
        "length_band": (
            "short"
            if len(candidate.tactics) <= 7
            else "medium"
            if len(candidate.tactics) <= 15
            else "long"
            if len(candidate.tactics) <= 32
            else "extended"
        ),
        "proof_nodes": result.proof_nodes,
    }


def _paths_alias(paths: Sequence[Path]) -> bool:
    for index, left in enumerate(paths):
        for right in paths[index + 1 :]:
            try:
                if left.resolve(strict=False) == right.resolve(strict=False):
                    return True
            except (OSError, RuntimeError):
                pass
            try:
                if os.path.samefile(left, right):
                    return True
            except OSError:
                pass
    return False


def _preflight_outputs(paths: Sequence[Path]) -> None:
    if _paths_alias(paths):
        raise GenerationError("trace, metadata, and manifest paths must be distinct")
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        if os.path.lexists(path) and not os.path.isfile(path):
            raise GenerationError(
                f"corpus artifact must be a regular file or absent: {path}"
            )


def _open_staged(destination: Path) -> tuple[TextIO, Path]:
    stream = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="\n",
        dir=destination.parent,
        prefix=f".{destination.name}.",
        suffix=".tmp",
        delete=False,
    )
    return stream, Path(stream.name)


def _finish_staged(stream: TextIO) -> None:
    stream.flush()
    os.fsync(stream.fileno())
    stream.close()


def _reserved_backup_path(path: Path) -> Path:
    descriptor, name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".bak", dir=path.parent
    )
    os.close(descriptor)
    backup = Path(name)
    backup.unlink()
    return backup


def _publish_staged(artifacts: Sequence[tuple[Path, Path]]) -> None:
    """Install a fully written artifact set, restoring old files on failure."""

    staged = {destination: temporary for destination, temporary in artifacts}
    backups: dict[Path, Path] = {}
    installed: list[Path] = []
    try:
        for destination, _ in artifacts:
            if os.path.lexists(destination):
                backup = _reserved_backup_path(destination)
                backups[destination] = backup
                os.replace(destination, backup)
        for destination, _ in artifacts:
            installed.append(destination)
            os.replace(staged[destination], destination)
            staged.pop(destination)
    except BaseException as original:
        rollback_errors: list[str] = []
        for destination in reversed(installed):
            try:
                destination.unlink(missing_ok=True)
            except BaseException as exc:
                rollback_errors.append(f"remove {destination}: {exc}")
        for destination, backup in reversed(tuple(backups.items())):
            if not os.path.lexists(backup):
                if not os.path.lexists(destination):
                    rollback_errors.append(
                        f"restore {destination}: destination and backup are missing"
                    )
                continue
            try:
                os.replace(backup, destination)
                backups.pop(destination)
            except BaseException as exc:
                rollback_errors.append(f"restore {destination}: {exc}")
        if rollback_errors:
            preserved = [
                str(path) for path in backups.values() if os.path.lexists(path)
            ]
            backups.clear()
            raise RuntimeError(
                "synthetic corpus publication failed and rollback was incomplete: "
                + "; ".join(rollback_errors)
                + ("; backups preserved at " + ", ".join(preserved) if preserved else "")
            ) from original
        raise
    finally:
        for temporary in (*staged.values(), *backups.values()):
            temporary.unlink(missing_ok=True)


def _validate_arguments(seed: object, row_budget: object) -> tuple[str, int]:
    if not _safe_text(seed, nonempty=True):
        raise ValueError("seed must be non-empty control-free text")
    if type(row_budget) is not int or isinstance(row_budget, bool):
        raise TypeError("row_budget must be an integer")
    if not 1 <= row_budget <= MAX_ROW_BUDGET:
        raise ValueError(f"row_budget must be between 1 and {MAX_ROW_BUDGET}")
    assert type(seed) is str
    return seed, row_budget


def generate_corpus(
    trace_output: str | os.PathLike[str],
    metadata_output: str | os.PathLike[str],
    manifest_output: str | os.PathLike[str],
    *,
    seed: str = DEFAULT_SEED,
    row_budget: int = DEFAULT_ROW_BUDGET,
) -> GenerationResult:
    """Stream exactly ``row_budget`` checked positive tactic rows and publish."""

    seed, row_budget = _validate_arguments(seed, row_budget)
    _validate_catalog()
    trace_path = Path(trace_output)
    metadata_path = Path(metadata_output)
    manifest_path = Path(manifest_output)
    destinations = (trace_path, metadata_path, manifest_path)
    _preflight_outputs(destinations)

    sources = _source_manifest()
    fingerprint = _generation_fingerprint(
        seed=seed,
        row_budget=row_budget,
        sources=sources,
    )
    trace_stream, trace_temporary = _open_staged(trace_path)
    metadata_stream, metadata_temporary = _open_staged(metadata_path)
    manifest_stream: TextIO | None = None
    manifest_temporary: Path | None = None
    trace_writer = _DigestingWriter(trace_stream)
    metadata_writer = _DigestingWriter(metadata_stream)

    sessions = 0
    rows = 0
    proof_nodes = 0
    domain_counts: Counter[str] = Counter()
    schema_counts: Counter[str] = Counter()
    schema_row_counts: Counter[str] = Counter()
    lane_counts: Counter[str] = Counter()
    lane_row_counts: Counter[str] = Counter()
    length_band_counts: Counter[str] = Counter()
    length_band_row_counts: Counter[str] = Counter()
    tactic_heads: Counter[str] = Counter()
    library_use_counts: Counter[str] = Counter()
    schema_attempts: Counter[str] = Counter()
    seen_statements: set[str] = set()
    seen_roots: set[str] = set()
    ih_observation_rows = 0
    lane_schedules = {
        lane: _schema_schedule(seed, lane)
        for lane in LANES
    }
    attempts_per_lane = {
        lane: 4 * sum(
            schema.weight for schema in SCHEMAS if schema.lane == lane
        )
        for lane in LANES
    }
    manifest: dict[str, object]

    try:
        while rows < row_budget:
            remaining = row_budget - rows
            made_progress = False
            for lane in _lane_order(seed, rows, lane_row_counts):
                for _ in range(attempts_per_lane[lane]):
                    schema = next(lane_schedules[lane])
                    occurrence = schema_attempts[schema.name]
                    schema_attempts[schema.name] += 1
                    parameter_index = _schema_offset(seed, schema) + occurrence
                    candidate = schema.build(parameter_index)
                    if len(candidate.tactics) > remaining:
                        continue
                    canonical = _canonical_statement(candidate, schema)
                    if canonical in seen_statements:
                        continue
                    root = _root_id(schema, canonical)
                    if root in seen_roots:
                        raise GenerationError(
                            f"schema {schema.name!r} generated duplicate root {root!r}"
                        )

                    ordinal = sessions + 1
                    session_id = f"peano-synth-{fingerprint[:20]}-{ordinal:07d}"
                    result = run_proof(
                        candidate.statement,
                        candidate.tactics,
                        request_id=f"synthetic-{schema.name}-{ordinal}",
                        classical=False,
                        capabilities=POLICY_CAPABILITIES,
                        trace_sink=trace_writer,
                        session_id=session_id,
                    )
                    transitions = _checked_result(
                        result,
                        schema=schema,
                        candidate=candidate,
                        canonical_statement=canonical,
                    )
                    metadata = _metadata_record(
                        schema=schema,
                        candidate=candidate,
                        result=result,
                        canonical_statement=canonical,
                        root=root,
                        seed=seed,
                        parameter_index=parameter_index,
                        ordinal=ordinal,
                    )
                    metadata_writer.write(_line_json(metadata))

                    transition_count = len(transitions)
                    band = (
                        "short"
                        if transition_count <= 7
                        else "medium"
                        if transition_count <= 15
                        else "long"
                        if transition_count <= 32
                        else "extended"
                    )
                    seen_statements.add(canonical)
                    seen_roots.add(root)
                    sessions += 1
                    rows += transition_count
                    proof_nodes += result.proof_nodes or 0
                    domain_counts[schema.domain] += 1
                    schema_counts[schema.name] += 1
                    schema_row_counts[schema.name] += transition_count
                    lane_counts[schema.lane] += 1
                    lane_row_counts[schema.lane] += transition_count
                    length_band_counts[band] += 1
                    length_band_row_counts[band] += transition_count
                    heads = tuple(
                        command.split(maxsplit=1)[0]
                        for command in candidate.tactics
                    )
                    tactic_heads.update(heads)
                    for command in candidate.tactics:
                        pieces = command.split(maxsplit=1)
                        if pieces[0] == "use" and len(pieces) == 2:
                            library_use_counts[pieces[1].split()[0]] += 1
                    ih_observation_rows += sum(
                        any(
                            type(goal) is str and "IH :" in goal
                            for goal in transition.get("goals_before", [])
                        )
                        for transition in transitions
                    )
                    made_progress = True
                    break
                if made_progress:
                    break
            if not made_progress:
                raise GenerationError(
                    f"no unique schema instance can fill the remaining {remaining} row(s)"
                )

        if row_budget >= MIN_BALANCE_AUDIT_ROWS:
            for lane in ("induction", "library"):
                lane_rows = lane_row_counts[lane]
                if 5 * lane_rows < rows or 10 * lane_rows > 3 * rows:
                    raise GenerationError(
                        f"{lane} lane emitted {lane_rows}/{rows} rows outside "
                        "the audited 20--30% curriculum band"
                    )
        if row_budget >= 10_000:
            missing_heads = set(MODEL_V1_COMMANDS) - set(tactic_heads)
            if missing_heads:
                raise GenerationError(
                    "10k curriculum omitted tactic head(s): "
                    + ", ".join(sorted(missing_heads))
                )
            missing_imports = MODEL_V2_THEOREMS - set(library_use_counts)
            if missing_imports:
                raise GenerationError(
                    "10k curriculum omitted allowed library import(s): "
                    + ", ".join(sorted(missing_imports))
                )

        _finish_staged(trace_stream)
        _finish_staged(metadata_stream)

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
                "selection": "deficit-balanced-weighted-lanes-v2",
                "stopping": "complete-sessions-exact-positive-row-budget-v2",
                "lane_row_weights": dict(LANE_WEIGHTS),
                "balance_audit_minimum_rows": MIN_BALANCE_AUDIT_ROWS,
            },
            "environment": environment_record(model_v2_environment()),
            "library_snapshot": _library_snapshot(),
            "evaluation_exclusion": {
                "rule": "exact canonical target and theorem-name exclusion",
                "held_out_contract_sha256": held_out_contract_sha256(),
                "names": sorted(HELD_OUT_NAMES),
                "formulas": sorted(HELD_OUT_FORMULAS),
            },
            "sources": sources,
            "schemas": [
                {
                    "name": schema.name,
                    "domain": schema.domain,
                    "tags": list(schema.tags),
                    "lane": schema.lane,
                    "weight": schema.weight,
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
                "rows_by_schema": dict(sorted(schema_row_counts.items())),
                "sessions_by_lane": {
                    lane: lane_counts[lane] for lane in LANES
                },
                "rows_by_lane": {
                    lane: lane_row_counts[lane] for lane in LANES
                },
                "sessions_by_length_band": dict(
                    sorted(length_band_counts.items())
                ),
                "rows_by_length_band": dict(
                    sorted(length_band_row_counts.items())
                ),
                "transitions_with_induction_hypothesis": ih_observation_rows,
                "library_use": dict(sorted(library_use_counts.items())),
                "distinct_library_imports": len(library_use_counts),
                "tactic_heads": dict(sorted(tactic_heads.items())),
            },
            "curriculum": {
                "target_row_weights": dict(LANE_WEIGHTS),
                "audited_row_bands": {
                    "induction": {"minimum_percent": 20, "maximum_percent": 30},
                    "library": {"minimum_percent": 20, "maximum_percent": 30},
                },
                "induction_or_ih_session_rows": lane_row_counts["induction"],
                "library_retrieval_or_composition_rows": lane_row_counts["library"],
                "all_command_heads_required_at_rows": 10_000,
                "all_allowed_imports_required_at_rows": 10_000,
            },
            "genealogy": {
                "root": "sha256(catalog_version, schema, canonical_statement)",
                "family": "root-specific; descendants share the exact root value",
                "lineage": "root-specific; descendants share the exact root value",
                "deduplication": "canonical statements are unique before execution",
                "broad_taxonomy_fields": ["domain", "template", "tags", "lane"],
                "parents": "empty for these independently sampled roots",
            },
            "limitations": [
                "synthetic proof-first schemas, not unrestricted Peano conjecture generation",
                (
                    "positive checked QED sessions only; failed actions belong in "
                    "a separate preference corpus"
                ),
                "no natural-language formalization pairs",
                "induction motives are proof-first schemas, not planner-generated invariants",
                (
                    "schema similarity remains across IID roots; family-OOD "
                    "evaluation must hold out whole templates"
                ),
                (
                    "lane balance is deterministic; individual tactic heads remain "
                    "naturally frequency-skewed inside checked proofs"
                ),
            ],
        }
        manifest_text = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
        manifest_stream, manifest_temporary = _open_staged(manifest_path)
        manifest_stream.write(manifest_text)
        _finish_staged(manifest_stream)
        manifest_stream = None

        _publish_staged(
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
    parser.add_argument(
        "--profile",
        choices=(PROFILE,),
        required=True,
        help=(
            "required safety acknowledgement; model-v2 artifacts must not "
            "overwrite the frozen model-v1 release"
        ),
    )
    parser.add_argument("--trace-output", required=True)
    parser.add_argument("--metadata-output", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--seed", default=DEFAULT_SEED)
    parser.add_argument(
        "--row-budget",
        type=int,
        default=DEFAULT_ROW_BUDGET,
        help=(
            "exact number of successful next-tactic rows; common staging values "
            "are 100, 1000, and 10000"
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        result = generate_corpus(
            args.trace_output,
            args.metadata_output,
            args.manifest,
            seed=args.seed,
            row_budget=args.row_budget,
        )
    except (GenerationError, OSError, TypeError, ValueError) as exc:
        print(f"synthetic corpus generation failed: {exc}", file=sys.stderr)
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
    "Candidate",
    "Schema",
    "GenerationError",
    "GenerationResult",
    "PROFILE",
    "POLICY_CAPABILITIES",
    "MODEL_V2_THEOREMS",
    "LANE_WEIGHTS",
    "SCHEMAS",
    "generate_corpus",
    "main",
]
