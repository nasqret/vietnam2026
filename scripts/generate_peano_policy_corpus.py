#!/usr/bin/env python3
"""Generate a small, deterministic, kernel-checked Peano policy corpus.

This is deliberately a corpus *driver*, not another theorem prover.  Every
authored tactic line goes through :func:`peano_lab.batch.run_proof`, which uses
the browser surface grammar and submits each closed certificate to the
independent Peano Lab kernel.  The three published artifacts are:

* one contiguous, unmodified version-1 trace stream;
* one strict metadata JSONL record per trace session; and
* one manifest binding the configuration, sources, and artifact digests.

The embedded pilot catalog favors readable proofs and tactic diversity over
volume.  Larger self-play generators can use the same artifact contract after
the small catalog has exercised the end-to-end training pipeline.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import sys
import unicodedata
from collections import Counter
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = REPOSITORY_ROOT / "scripts"
PEANO_PYTHON = REPOSITORY_ROOT / "peano-lab" / "py"
if str(PEANO_PYTHON) not in sys.path:
    sys.path.insert(0, str(PEANO_PYTHON))

from peano_lab.batch import (  # noqa: E402
    MODEL_V1_COMMANDS,
    MODEL_V1_THEOREMS,
    BatchResult,
    capability_sha256,
    run_proof,
)
from peano_lab.engine.trace import TRACE_VERSION  # noqa: E402
from peano_lab.kernel.formulas import (  # noqa: E402
    Formula,
    ParseError,
    parse_formula_with_names,
)
from peano_lab.ui.prove import SurfaceCapabilities  # noqa: E402
from export_traces import publish_text_artifact_set  # noqa: E402


FORMAT = "peano-policy-corpus"
VERSION = 1
CATALOG_VERSION = 1
DEFAULT_SEED = "peano-policy-pilot-v1"
POLICY_THEOREMS = frozenset(MODEL_V1_THEOREMS)
POLICY_CAPABILITIES = SurfaceCapabilities(
    label="model-v1",
    allowed_commands=MODEL_V1_COMMANDS,
    allowed_theorems=POLICY_THEOREMS,
)
CAPABILITY_FIELDS = ("label", "allowed_commands", "allowed_theorems")
METADATA_FIELDS = (
    "session",
    "theorem",
    "family",
    "lineage",
    "classical",
    "surface",
    "environment_sha256",
    "capabilities",
    "statement",
    "template",
    "tags",
    "seed",
    "ordinal",
    "tactics",
    "proof_nodes",
)
SMOKE_THEOREMS = (
    "logic_and_swap",
    "existential_witness",
    "closed_norm_num",
    "compact_add_succ",
)


class GenerationError(RuntimeError):
    """A corpus cannot be generated without violating its checked contract."""


@dataclass(frozen=True, slots=True)
class ProofTemplate:
    """One authored pilot theorem and its public-surface tactic proof."""

    theorem: str
    statement: str
    tactics: tuple[str, ...]
    family: str
    lineage: str
    tags: tuple[str, ...]
    classical: bool = False


@dataclass(frozen=True, slots=True)
class GenerationResult:
    """Published paths and the exact manifest written to disk."""

    trace_path: Path
    metadata_path: Path
    manifest_path: Path
    manifest: dict[str, object]


# These proofs are intentionally ordinary Peano Lab programs.  In particular,
# automation emits normal kernel certificates; no template carries trusted
# proof objects or reaches into engine internals.
PILOT_TEMPLATES: tuple[ProofTemplate, ...] = (
    ProofTemplate(
        "logic_and_swap",
        "(0 = 0 /\\ 1 = 1) -> 1 = 1 /\\ 0 = 0",
        ("intro h", "cases h", "split", "exact h_right", "exact h_left"),
        "logic-connectives",
        "pilot-v1/logic/and-swap",
        ("logic", "cases", "split"),
    ),
    ProofTemplate(
        "logic_or_swap",
        "(0 = 0 \\/ 1 = 1) -> 1 = 1 \\/ 0 = 0",
        (
            "intro h",
            "cases h",
            "right",
            "exact h_left",
            "left",
            "exact h_right",
        ),
        "logic-connectives",
        "pilot-v1/logic/or-swap",
        ("logic", "cases", "left", "right"),
    ),
    ProofTemplate(
        "equality_congruence",
        "forall n m. n = m -> S n = S m",
        ("intro n", "intro m", "intro h", "congr", "exact h"),
        "equality-reasoning",
        "pilot-v1/equality/congruence-successor",
        ("equality", "congr"),
    ),
    ProofTemplate(
        "equality_symmetry",
        "forall n m. n = m -> m = n",
        ("intro n", "intro m", "intro h", "symm", "exact h"),
        "equality-reasoning",
        "pilot-v1/equality/symmetry",
        ("equality", "symm"),
    ),
    ProofTemplate(
        "equality_transitivity_refl",
        "forall n. n = n",
        ("intro n", "trans n", "refl", "refl"),
        "equality-reasoning",
        "pilot-v1/equality/transitivity-reflexive",
        ("equality", "trans", "refl"),
    ),
    ProofTemplate(
        "context_assumption",
        "0 = 0 -> 0 = 0",
        ("intro h", "assumption"),
        "context-reasoning",
        "pilot-v1/context/assumption",
        ("logic", "assumption"),
    ),
    ProofTemplate(
        "theorem_use_add_assoc",
        "forall n m k. (n + m) + k = n + (m + k)",
        ("use add_assoc", "exact add_assoc"),
        "checked-library-use",
        "pilot-v1/library/add-assoc",
        ("theorem-use", "addition", "use"),
    ),
    ProofTemplate(
        "induction_zero_add",
        "forall n. 0 + n = n",
        ("induction n", "simp", "simp [IH]"),
        "addition-induction",
        "pilot-v1/addition/zero-add-induction",
        ("addition", "induction", "simp"),
    ),
    ProofTemplate(
        "addition_builtin_rewrite",
        "forall n. n + 0 = n",
        ("intro n", "rewrite PA3", "refl"),
        "addition-axioms",
        "pilot-v1/addition/right-zero-rewrite",
        ("addition", "rewrite", "PA3"),
    ),
    ProofTemplate(
        "induction_zero_mul",
        "forall n. 0 * n = 0",
        ("induction n", "simp", "simp [IH]"),
        "multiplication-induction",
        "pilot-v1/multiplication/zero-mul-induction",
        ("multiplication", "induction", "simp"),
    ),
    ProofTemplate(
        "existential_witness",
        "forall n. exists x. n = x",
        ("intro n", "exists n", "refl"),
        "existential-reasoning",
        "pilot-v1/existential/direct-witness",
        ("existential", "exists"),
    ),
    ProofTemplate(
        "existential_elimination",
        "(exists x. x = 0) -> exists y. y = 0",
        ("intro h", "cases h", "exists x", "exact h_witness"),
        "existential-reasoning",
        "pilot-v1/existential/eliminate-and-repack",
        ("existential", "cases", "exists"),
    ),
    ProofTemplate(
        "local_have",
        "0 = 0",
        ("have h : 0 = 0", "refl", "exact h"),
        "local-reasoning",
        "pilot-v1/local/have-reflexive",
        ("have", "local-cut"),
    ),
    ProofTemplate(
        "local_suffices",
        "1 = 1",
        ("suffices h : 1 = 1", "exact h", "refl"),
        "local-reasoning",
        "pilot-v1/local/suffices-reflexive",
        ("suffices", "local-cut"),
    ),
    ProofTemplate(
        "closed_norm_num",
        "2 * 3 + 1 = 7",
        ("norm_num",),
        "arithmetic-normalization",
        "pilot-v1/arithmetic/norm-num-2x3-plus-1",
        ("arithmetic", "norm_num"),
    ),
    ProofTemplate(
        "ring_add_comm_one",
        "forall n. n + 1 = 1 + n",
        ("intro n", "ring"),
        "arithmetic-normalization",
        "pilot-v1/arithmetic/ring-add-comm-one",
        ("arithmetic", "addition", "ring"),
    ),
    ProofTemplate(
        "compact_add_succ",
        "forall a b. S a + b = S (a + b)",
        ("intro a", "intro b", "compact_arith"),
        "arithmetic-normalization",
        "pilot-v1/arithmetic/compact-successor-addition",
        ("arithmetic", "addition", "compact_arith"),
    ),
    ProofTemplate(
        "apply_successor_nonzero",
        "forall n. ~(S n = 0)",
        ("apply PA1",),
        "pa-axiom-application",
        "pilot-v1/pa/apply-successor-nonzero",
        ("logic", "apply", "PA1"),
    ),
)


def _safe_text(value: object, *, nonempty: bool = False) -> bool:
    if type(value) is not str or (nonempty and not value):
        return False
    return not any(
        unicodedata.category(char) in {"Cc", "Cf", "Cs", "Zl", "Zp"}
        for char in value
    )


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(128 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _line_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n"


def _capability_record(capabilities: SurfaceCapabilities) -> dict[str, object]:
    result = {
        "label": capabilities.label,
        "allowed_commands": (
            None
            if capabilities.allowed_commands is None
            else sorted(capabilities.allowed_commands)
        ),
        "allowed_theorems": (
            None
            if capabilities.allowed_theorems is None
            else sorted(capabilities.allowed_theorems)
        ),
    }
    if tuple(result) != CAPABILITY_FIELDS:
        raise RuntimeError("internal capability field order changed")
    return result


def _source_manifest() -> dict[str, dict[str, str]]:
    # Session identities must change whenever any proof-producing package code
    # changes, not only when the thin adapter changes.  Hash the complete
    # Peano Lab Python package; this deliberately favors an auditable broad
    # dependency boundary over a fragile hand-maintained import list.
    paths = (
        Path(__file__).resolve(),
        SCRIPTS_ROOT / "export_traces.py",
        *sorted((PEANO_PYTHON / "peano_lab").rglob("*.py")),
    )
    result: dict[str, dict[str, str]] = {}
    for path in paths:
        relative = path.relative_to(REPOSITORY_ROOT).as_posix()
        result[relative] = {"sha256": _sha256_file(path)}
    return result


def _runtime_record() -> dict[str, str]:
    return {
        "implementation": sys.implementation.name,
        "python": ".".join(str(part) for part in sys.version_info[:3]),
    }


def _parsed_statement(template: ProofTemplate) -> Formula:
    try:
        formula, free_names = parse_formula_with_names(template.statement)
    except (ParseError, ValueError) as exc:
        raise GenerationError(
            f"template {template.theorem!r} has an invalid statement: {exc}"
        ) from exc
    if free_names:
        raise GenerationError(
            f"template {template.theorem!r} is not closed: "
            + ", ".join(free_names)
        )
    return formula


def _validate_templates(templates: Sequence[ProofTemplate]) -> None:
    if not templates:
        raise GenerationError("the pilot catalog is empty")
    theorem_names: set[str] = set()
    lineages: set[str] = set()
    statements: dict[Formula, str] = {}
    for template in templates:
        if type(template.classical) is not bool:
            raise GenerationError(
                f"template {template.theorem!r} has a non-Boolean logic mode"
            )
        if template.classical:
            raise GenerationError(
                "policy corpus v1 has one fixed intuitionistic environment; "
                f"template {template.theorem!r} requested classical logic"
            )
        for field in ("theorem", "family", "lineage"):
            if not _safe_text(getattr(template, field), nonempty=True):
                raise GenerationError(
                    f"template {template.theorem!r} has unsafe {field} metadata"
                )
        if template.theorem in theorem_names:
            raise GenerationError(f"duplicate theorem id {template.theorem!r}")
        theorem_names.add(template.theorem)
        if template.lineage in lineages:
            raise GenerationError(f"duplicate lineage {template.lineage!r}")
        lineages.add(template.lineage)
        if not template.tactics:
            raise GenerationError(f"template {template.theorem!r} has no tactics")
        if not all(_safe_text(item, nonempty=True) for item in template.tactics):
            raise GenerationError(
                f"template {template.theorem!r} has unsafe tactic text"
            )
        if not all(_safe_text(tag, nonempty=True) for tag in template.tags):
            raise GenerationError(f"template {template.theorem!r} has unsafe tags")
        formula = _parsed_statement(template)
        previous = statements.get(formula)
        if previous is not None:
            raise GenerationError(
                f"duplicate statement in templates {previous!r} and "
                f"{template.theorem!r}"
            )
        statements[formula] = template.theorem


def _rank(seed: str, template: ProofTemplate) -> str:
    material = json.dumps(
        [seed, CATALOG_VERSION, template.lineage],
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def select_templates(
    templates: Sequence[ProofTemplate] = PILOT_TEMPLATES,
    *,
    seed: str = DEFAULT_SEED,
    count: int | None = None,
    smoke: bool = False,
) -> tuple[ProofTemplate, ...]:
    """Validate and deterministically select a bounded pilot subset."""

    _validate_templates(templates)
    if not _safe_text(seed, nonempty=True):
        raise ValueError("seed must be non-empty control-free text")
    if smoke and count is not None:
        raise ValueError("--smoke and --count are mutually exclusive")
    by_name = {template.theorem: template for template in templates}
    if smoke:
        missing = set(SMOKE_THEOREMS) - set(by_name)
        if missing:
            raise GenerationError(
                "smoke catalog is missing theorem(s): " + ", ".join(sorted(missing))
            )
        return tuple(by_name[name] for name in SMOKE_THEOREMS)
    if count is None:
        count = len(templates)
    if type(count) is not int or isinstance(count, bool) or not 1 <= count <= len(
        templates
    ):
        raise ValueError(f"count must be between 1 and {len(templates)}")
    ordered = sorted(templates, key=lambda item: (_rank(seed, item), item.lineage))
    return tuple(ordered[:count])


def _generation_fingerprint(
    selected: Sequence[ProofTemplate],
    *,
    seed: str,
    smoke: bool,
    sources: dict[str, dict[str, str]],
) -> str:
    payload = {
        "format": FORMAT,
        "version": VERSION,
        "catalog_version": CATALOG_VERSION,
        "seed": seed,
        "smoke": smoke,
        "capabilities": _capability_record(POLICY_CAPABILITIES),
        "runtime": _runtime_record(),
        "sources": sources,
        "templates": [asdict(template) for template in selected],
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _checked_result(result: BatchResult, template: ProofTemplate) -> None:
    if result.status != "proved" or result.kernel_checked is not True:
        detail = result.error or result.status
        raise GenerationError(
            f"template {template.theorem!r} did not reach checked QED: {detail}"
        )
    if result.trace is None or not result.trace:
        raise GenerationError(f"template {template.theorem!r} returned no trace")
    footer = result.trace[-1]
    if footer.get("qed") is not True:
        raise GenerationError(
            f"template {template.theorem!r} lacks a checked qed:true footer"
        )
    if (
        result.surface != POLICY_CAPABILITIES.label
        or result.environment_sha256 != capability_sha256(POLICY_CAPABILITIES)
        or result.classical is not template.classical
    ):
        raise GenerationError(
            f"template {template.theorem!r} escaped its declared environment"
        )


def _metadata_record(
    template: ProofTemplate,
    result: BatchResult,
    *,
    seed: str,
    ordinal: int,
) -> dict[str, object]:
    record = {
        "session": result.session_id,
        "theorem": template.theorem,
        "family": template.family,
        "lineage": template.lineage,
        "classical": template.classical,
        "surface": POLICY_CAPABILITIES.label,
        "environment_sha256": capability_sha256(POLICY_CAPABILITIES),
        "capabilities": _capability_record(POLICY_CAPABILITIES),
        "statement": result.theorem,
        "template": template.theorem,
        "tags": list(template.tags),
        "seed": seed,
        "ordinal": ordinal,
        "tactics": list(template.tactics),
        "proof_nodes": result.proof_nodes,
    }
    if tuple(record) != METADATA_FIELDS:
        raise RuntimeError("internal metadata field order changed")
    return record


def _paths_alias(paths: Sequence[Path]) -> bool:
    resolved: set[Path] = set()
    for path in paths:
        try:
            canonical = path.resolve(strict=False)
        except (OSError, RuntimeError):
            canonical = path.absolute()
        if canonical in resolved:
            return True
        resolved.add(canonical)
    return False


def _publish(artifacts: Sequence[tuple[Path, str]]) -> None:
    """Publish one coherent artifact set with ordinary-failure rollback."""

    destinations = [path for path, _ in artifacts]
    if _paths_alias(destinations):
        raise GenerationError("trace, metadata, and manifest paths must be distinct")
    try:
        publish_text_artifact_set(artifacts)
    except ValueError as exc:
        raise GenerationError(str(exc).replace("export artifact", "corpus artifact")) from exc


def generate_corpus(
    trace_output: str | os.PathLike[str],
    metadata_output: str | os.PathLike[str],
    manifest_output: str | os.PathLike[str],
    *,
    seed: str = DEFAULT_SEED,
    count: int | None = None,
    smoke: bool = False,
    templates: Sequence[ProofTemplate] = PILOT_TEMPLATES,
) -> GenerationResult:
    """Generate, kernel-check, and atomically publish one pilot corpus."""

    selected = select_templates(templates, seed=seed, count=count, smoke=smoke)
    sources = _source_manifest()
    fingerprint = _generation_fingerprint(
        selected,
        seed=seed,
        smoke=smoke,
        sources=sources,
    )
    trace_stream = io.StringIO()
    metadata: list[dict[str, object]] = []
    tactic_heads: Counter[str] = Counter()
    tag_counts: Counter[str] = Counter()
    family_counts: Counter[str] = Counter()
    proof_nodes = 0
    transition_records = 0

    for ordinal, template in enumerate(selected, 1):
        session_id = f"peano-policy-{fingerprint[:20]}-{ordinal:04d}"
        result = run_proof(
            template.statement,
            template.tactics,
            request_id=template.theorem,
            classical=template.classical,
            capabilities=POLICY_CAPABILITIES,
            trace_sink=trace_stream,
            session_id=session_id,
        )
        _checked_result(result, template)
        metadata.append(
            _metadata_record(template, result, seed=seed, ordinal=ordinal)
        )
        transitions = tuple(record for record in result.trace or () if "v" in record)
        transition_records += len(transitions)
        proof_nodes += result.proof_nodes or 0
        family_counts[template.family] += 1
        tactic_heads.update(command.split(maxsplit=1)[0] for command in template.tactics)
        tag_counts.update(template.tags)

    trace_text = trace_stream.getvalue()
    metadata_text = "".join(_line_json(record) for record in metadata)
    if not trace_text or not trace_text.endswith("\n"):
        raise GenerationError("the headless runner returned an incomplete trace stream")
    if not metadata_text.endswith("\n"):
        raise GenerationError("the metadata sidecar is incomplete")

    trace_path = Path(trace_output)
    metadata_path = Path(metadata_output)
    manifest_path = Path(manifest_output)
    manifest: dict[str, object] = {
        "format": FORMAT,
        "version": VERSION,
        "trace_version": TRACE_VERSION,
        "catalog_version": CATALOG_VERSION,
        "run_fingerprint": fingerprint,
        "runtime": _runtime_record(),
        "config": {
            "seed": seed,
            "count": len(selected),
            "smoke": smoke,
            "selection": (
                "fixed-smoke-v1" if smoke else "sha256-ranked-lineage-v1"
            ),
        },
        "environment": {
            "surface": POLICY_CAPABILITIES.label,
            "classical": False,
            "environment_sha256": capability_sha256(POLICY_CAPABILITIES),
            "capabilities": _capability_record(POLICY_CAPABILITIES),
        },
        "sources": sources,
        "artifacts": {
            "trace": {
                "path": trace_path.name,
                "bytes": len(trace_text.encode("utf-8")),
                "sha256": _sha256_bytes(trace_text.encode("utf-8")),
            },
            "metadata": {
                "path": metadata_path.name,
                "bytes": len(metadata_text.encode("utf-8")),
                "sha256": _sha256_bytes(metadata_text.encode("utf-8")),
            },
        },
        "counts": {
            "sessions": len(selected),
            "kernel_checked_qed": len(selected),
            "transition_records": transition_records,
            "footer_records": len(selected),
            "proof_nodes": proof_nodes,
            "sessions_by_family": dict(sorted(family_counts.items())),
            "tactic_heads": dict(sorted(tactic_heads.items())),
            "tags": dict(sorted(tag_counts.items())),
        },
        "sessions": [
            {
                "session": record["session"],
                "theorem": record["theorem"],
                "family": record["family"],
                "lineage": record["lineage"],
                "proof_nodes": record["proof_nodes"],
            }
            for record in metadata
        ],
        "limitations": [
            "curated pilot catalog, not large-scale self-play",
            "positive checked QED sessions only; no preference-negative records",
            "closed PA statements only; no natural-language formalization pairs",
            "--count subsets do not guarantee full tactic-family coverage",
        ],
    }
    manifest_text = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    _publish(
        (
            (trace_path, trace_text),
            (metadata_path, metadata_text),
            (manifest_path, manifest_text),
        )
    )
    return GenerationResult(trace_path, metadata_path, manifest_path, manifest)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trace-output", required=True)
    parser.add_argument("--metadata-output", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--seed", default=DEFAULT_SEED)
    parser.add_argument(
        "--count",
        type=int,
        help=f"seeded pilot subset size (1..{len(PILOT_TEMPLATES)})",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help=f"generate the fixed {len(SMOKE_THEOREMS)}-session smoke corpus",
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
            count=args.count,
            smoke=args.smoke,
        )
    except (GenerationError, OSError, ValueError) as exc:
        parser.exit(2, f"generation failed: {exc}\n")
    print(
        f"generated {result.manifest['counts']['sessions']} checked sessions; "
        f"manifest: {result.manifest_path}"
    )
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised through subprocess
    raise SystemExit(main())
