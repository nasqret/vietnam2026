#!/usr/bin/env python3
"""Publish the four completely checked, definition-aware Alpha-v20 campaigns.

This is an evidence-reading documentation generator, never a proof provider.
Its only admission authority is the already sealed Alpha-v20 catalog and its
actual unchanged-kernel proof-bundle receipt. The generator does not decode,
replay, or construct a proof bundle. New display definitions are parsed into
the unchanged first-order syntax, expanded hygienically, and accepted only
when their compacted theorem statements re-expand to the identical native AST.
"""

from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
import html
import json
from pathlib import Path
import re
import sys
from typing import Any


REPO = Path(__file__).resolve().parents[1]
PY_ROOT = REPO / "peano-lab" / "py"
if str(PY_ROOT) not in sys.path:
    sys.path.insert(0, str(PY_ROOT))

from constructive_frontier_exact_explorer import (  # noqa: E402
    render_exact_index,
    render_exact_theorem,
)
from constructive_next_layer_definitions import (  # noqa: E402
    NEXT_LAYER_DEFINITIONS,
    NEXT_LAYER_DEFINITIONS_BY_NAME,
    NEXT_LAYER_REGISTRIES,
)
from constructive_proof_explorer_template import (  # noqa: E402
    render_canonical_family_landing,
)
from peano_lab.kernel.formulas import (  # noqa: E402
    And,
    Bot,
    Eq,
    Exists,
    Forall,
    Formula,
    Imp,
    Or,
    _as_le,
    _fresh_binder,
    parse_formula_in_context,
    parse_formula_with_names,
)
from peano_lab.kernel.terms import (  # noqa: E402
    ParseError,
    Term,
    _is_identifier,
    _parse_term_from,
    _pretty_term,
)
from peano_lab.library import editions_v20 as v20  # noqa: E402
from peano_lab.library import editions_v24 as v24  # noqa: E402
from peano_lab.library.alpha_enrollment_v20 import (  # noqa: E402
    EXPECTED_CAMPAIGN_COUNTS,
    FRONTIER_V20_EXPECTED_COUNT,
    FrontierV20Campaign,
    alpha_v20_enrollment,
)
from peano_lab.library.bertrand_defined_edition import (  # noqa: E402
    ALL_BERTRAND_DEFINITIONS,
    _formula_shape,
)
from peano_lab.library.defined_edition import (  # noqa: E402
    _formula_nodes,
    _leading_source_binders,
    _match_formula,
)
from peano_lab.library.defined_syntax import (  # noqa: E402
    DefinitionSpec,
    _DefinedFormulaParser,
    _instantiate_formula,
)


OUTPUT = REPO / "book" / "_static" / "constructive-next-layer-explorer"
CATALOG = REPO / "artifacts" / "peano-library" / "alpha" / "catalog-v20.json"
CURRENT_CATALOG = REPO / "artifacts" / "peano-library" / "alpha" / "catalog-v24.json"
CURRENT_CHANNELS = REPO / "artifacts" / "peano-library" / "channels-v24.json"
CAMPAIGN = REPO / "book" / "_static" / "constructive-grand-campaign" / "campaign.json"
GLOBAL_DEFINITIONS = CAMPAIGN.with_name("definitions.json")
EXPECTED_ALPHA_COUNT = 1_776
EXPECTED_STABLE_COUNT = 432
EXPECTED_BUNDLE_NODE_COUNT = 590
MAX_DEFINED_EXPANSION_NODES = 1_000_000
SCHEMA = "peano-lab-constructive-next-layer-explorer-v1"
STATUS = (
    "Alpha v24 checked-use · first admitted v20 · independently kernel and Lean verified; not Stable"
)
ASSET_SOURCES = {
    "defined-explorer.css": REPO / "book" / "_static" / "pa-proof-explorer" / "defined" / "assets" / "explorer.css",
    "defined-explorer.js": REPO / "book" / "_static" / "pa-proof-explorer" / "defined" / "assets" / "explorer.js",
    "exact-explorer.css": REPO / "book" / "_static" / "pa-proof-explorer" / "assets" / "explorer.css",
    "exact-explorer.js": REPO / "book" / "_static" / "pa-proof-explorer" / "assets" / "explorer.js",
    "proofs.css": REPO / "deploy" / "proofs" / "proofs.css",
}
PINNED_ASSETS = {
    "defined-explorer.css": "eb26033797a96d83d62b36d9562ffa37afe7443e2a54bd1d693fc9d5da5ad220",
    "defined-explorer.js": "1b95ce2289502ba87f76708096aa76c07961be733d37dd56f64711b04621d982",
    "exact-explorer.css": "6dd0cf105c498dec70fe6a7fac04dcda397b40f947de677b36fc9c01962d84bc",
    "exact-explorer.js": "98f11fff5d34b5fa481c1dd6a6b39eef58fed28d00bb7d1f4ac7d1226b4d6606",
}


class NextLayerExplorerError(ValueError):
    """A sealed proof receipt, exact definition, or displayed DAG is invalid."""


@dataclass(frozen=True, slots=True)
class Family:
    slug: str
    campaign: FrontierV20Campaign
    prefix: str
    title: str
    kicker: str
    description: str
    formula: str
    domain: str
    family_id: str
    milestones: tuple[str, ...]
    roots: tuple[str, ...]
    definitions: tuple[str, ...]

    @property
    def caveat(self) -> str:
        """Preserve the original, evidence-honest first-admission boundary."""

        if self.domain == "D05":
            return (
                "The broader T13 milestone remains OPEN: these ten historical verified "
                "matrix and dot-product components are now supplemented by complete "
                "arbitrary signed matrix multiplication and exact signed minors in Alpha v24; arbitrary-dimensional "
                "determinants, rank, and lattices remain open."
            )
        return (
            "Every displayed theorem was first admitted in Alpha v20, remains "
            "independently kernel- and Lean-verified for current Alpha v24 checked "
            "use, and has not been promoted to Stable."
        )


FAMILIES = (
    Family(
        slug="polynomial-horner",
        campaign=FrontierV20Campaign.POLYNOMIAL_HORNER,
        prefix="PH",
        title="Constructive polynomial evaluation",
        kicker="Horner traces · totality · uniqueness",
        description="Seven independently checked first-order proofs construct, characterize, and uniquely evaluate every finite beta-coded natural polynomial.",
        formula="Horner(b,c,x,ℓ,z) · zᵢ₊₁ = zᵢx + aᵢ",
        domain="D04",
        family_id="F10",
        milestones=("T12",),
        roots=(
            "beta_horner_eval_exists_unique",
            "beta_horner_eval_successor_decompose",
            "beta_horner_eval_exists",
        ),
        definitions=("Beta", "Lt", "Horner"),
    ),
    Family(
        slug="matrix-dot-product",
        campaign=FrontierV20Campaign.MATRIX_DOT_PRODUCT,
        prefix="MD",
        title="Finite matrices and dot products",
        kicker="Matrix cells · dot products · signed 2×2 determinants",
        description="Ten independently checked constructive results establish total finite matrix entries, unique natural dot products, commutativity, and exact signed two-by-two determinant components.",
        formula="DotProduct(b,c,d,e,ℓ,z) · det₂ = ad − bc",
        domain="D05",
        family_id="F12",
        milestones=("T13",),
        roots=(
            "beta_matrix_cell_exists_unique",
            "signed_matrix_two_determinant_functional",
            "beta_dot_product_exists_unique",
        ),
        definitions=("Beta", "Lt", "Sum", "MatrixAt", "DotProduct", "SignedDet2"),
    ),
    Family(
        slug="bertrand-prime-chains",
        campaign=FrontierV20Campaign.BERTRAND_PRIME,
        prefix="BP",
        title="Bertrand prime windows and iterated chains",
        kicker="Exact binomial valuation · arbitrarily long prime chains",
        description="Thirteen complete proofs establish a prime of multiplicity exactly one in the central binomial coefficient and construct beta-coded strict Bertrand chains of arbitrary finite length.",
        formula="n < p < 2n · vₚ(C(2n,n)) = 1 · pᵢ < pᵢ₊₁ < 2pᵢ",
        domain="D02",
        family_id="F03",
        milestones=("G023", "G024"),
        roots=(
            "central_binom_prime_divisor_multiplicity_one_exists",
            "iterated_bertrand_prime_chain_exists",
        ),
        definitions=("Beta", "Lt", "Prime", "PowerValuation", "BertrandWindow", "PowerValuationOne", "BertrandChain"),
    ),
    Family(
        slug="continued-fractions",
        campaign=FrontierV20Campaign.CONTINUED_FRACTION,
        prefix="CF",
        title="Finite simple continued fractions",
        kicker="Reverse Euclidean history · forward quotient list",
        description="Nine independently checked Heyting-arithmetic proofs build a complete beta-coded Euclidean history and prove existence of a nonempty simple continued fraction for every pair of positive naturals.",
        formula="a,b > 0 → ∃s. ContinuedFraction(a,b,s)",
        domain="D03",
        family_id="F08",
        milestones=("G071",),
        roots=("continued_fraction_positive_nonempty_exists", "continued_fraction_positive_exists"),
        definitions=("Beta", "Lt", "ListCell", "ContinuedFractionTrace", "ContinuedFraction"),
    ),
)


def _digest(value: str | bytes) -> str:
    return sha256(value.encode("utf-8") if isinstance(value, str) else value).hexdigest()


def _json(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2, sort_keys=True)
        + "\n"
    ).encode("utf-8")


def _e(value: object) -> str:
    return html.escape(str(value), quote=True)


def _versioned(path: str, revision: str) -> str:
    if path.startswith("#"):
        return _e(path)
    destination, marker, fragment = path.partition("#")
    separator = "&" if "?" in destination else "?"
    result = f"{destination}{separator}v={revision}"
    return _e(result + (f"#{fragment}" if marker else ""))


def _file_digest(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as source:
        while chunk := source.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()


@lru_cache(maxsize=1)
def _definition_specs() -> dict[str, DefinitionSpec]:
    reviewed = {definition.name: definition for definition in ALL_BERTRAND_DEFINITIONS}
    if len(reviewed) != len(ALL_BERTRAND_DEFINITIONS):
        raise NextLayerExplorerError("reviewed definition registry repeats an identity")
    definitions = dict(reviewed)
    known_ids = {definition.stable_id for definition in reviewed.values()}
    for definition in NEXT_LAYER_DEFINITIONS:
        if definition.name in definitions or definition.stable_id in known_ids:
            raise NextLayerExplorerError(
                f"new constructive definition shadows {definition.name!r}"
            )
        definitions[definition.name] = definition
        known_ids.add(definition.stable_id)
    for definition in definitions.values():
        if len(set(definition.conceptual_dependencies)) != len(definition.conceptual_dependencies):
            raise NextLayerExplorerError(
                f"constructive definition {definition.name!r} repeats a dependency"
            )
        for dependency in definition.conceptual_dependencies:
            if dependency not in definitions or dependency == definition.name:
                raise NextLayerExplorerError(
                    f"constructive definition {definition.name!r} has an invalid dependency"
                )
    return definitions


def _definition_closure(names: Sequence[str]) -> tuple[DefinitionSpec, ...]:
    available = _definition_specs()
    ordered: list[DefinitionSpec] = []
    active: set[str] = set()
    complete: set[str] = set()

    def visit(name: str) -> None:
        if name in complete:
            return
        if name in active:
            raise NextLayerExplorerError(f"circular constructive definition {name!r}")
        definition = available.get(name)
        if definition is None:
            raise NextLayerExplorerError(f"unknown constructive definition {name!r}")
        active.add(name)
        for dependency in definition.conceptual_dependencies:
            visit(dependency)
        active.remove(name)
        complete.add(name)
        ordered.append(definition)

    for name in names:
        visit(name)
    return tuple(ordered)


class _LocalDefinedParser(_DefinedFormulaParser):
    """Opt-in, isolated parser for only one family's conservative aliases."""

    def __init__(self, source: str, definitions: Mapping[str, DefinitionSpec]):
        super().__init__(source, MAX_DEFINED_EXPANSION_NODES)
        self._definitions = definitions

    def _atom(self) -> Formula:
        token = self.stream.peek()
        position = self.stream.position
        opened = (
            position + 1 < len(self.stream.tokens)
            and self.stream.tokens[position + 1].text == "("
        )
        if _is_identifier(token) and token != "S" and opened:
            column = self.stream.column()
            name = self.stream.take()
            definition = self._definitions.get(name)
            if definition is None:
                raise ParseError(f"unknown next-layer definition {name!r} at column {column}")
            self.stream.expect("(")
            arguments: list[Term] = []
            if self.stream.accept(")") is None:
                while True:
                    arguments.append(_parse_term_from(self.stream, self.bound, self.free))
                    if self.stream.accept(")") is not None:
                        break
                    self.stream.expect(",")
            if len(arguments) != definition.arity:
                raise ParseError(
                    f"definition {name!r} expects {definition.arity} arguments, "
                    f"got {len(arguments)} at column {column}"
                )
            return _instantiate_formula(
                definition.template_formula,
                tuple(arguments),
                0,
                self.expansion_counter,
                definition,
                column,
            )
        return super()._atom()


def _parts_append(
    parts: list[dict[str, str]],
    text: str,
    *,
    definition: str | None = None,
) -> None:
    if not text:
        return
    if definition is None and parts and parts[-1]["kind"] == "text":
        parts[-1]["text"] += text
    elif definition is None:
        parts.append({"kind": "text", "text": text})
    else:
        parts.append({"kind": "definition", "text": text, "definition": definition})


class _FormulaCompactor:
    """Render reviewed/new notation and require exact binder-safe AST equality."""

    def __init__(self, definitions: Sequence[DefinitionSpec]) -> None:
        self.by_name = {definition.name: definition for definition in definitions}
        if len(self.by_name) != len(definitions):
            raise NextLayerExplorerError("local definitions repeat a surface name")
        sorted_definitions = sorted(
            enumerate(definitions),
            key=lambda item: (-_formula_nodes(item[1].template_formula), item[0]),
        )
        self.by_shape: dict[tuple[object, ...], list[DefinitionSpec]] = {}
        for _position, definition in sorted_definitions:
            self.by_shape.setdefault(_formula_shape(definition.template_formula), []).append(
                definition
            )

    def _match(self, formula: Formula) -> tuple[DefinitionSpec, tuple[Term, ...]] | None:
        for definition in self.by_shape.get(_formula_shape(formula), ()):
            bindings: list[Term | None] = [None] * definition.arity
            if _match_formula(
                definition.template_formula,
                formula,
                depth=0,
                arity=definition.arity,
                bindings=bindings,
            ) and all(binding is not None for binding in bindings):
                return definition, tuple(value for value in bindings if value is not None)
        return None

    def _render(
        self,
        formula: Formula,
        names: list[str],
        parent_precedence: int,
        uses: Counter[str],
        binders: list[tuple[type[Formula], str]] | None = None,
    ) -> list[dict[str, str]]:
        found = self._match(formula)
        if found is not None:
            definition, arguments = found
            text = (
                definition.name
                + "("
                + ",".join(_pretty_term(argument, names, 0) for argument in arguments)
                + ")"
            )
            uses[definition.stable_id] += 1
            parts = [{"kind": "definition", "definition": definition.stable_id, "text": text}]
            precedence = 5
        else:
            weak_order = _as_le(formula)
            if weak_order is not None:
                lower, upper = weak_order
                parts = [{"kind": "text", "text": (
                    f"{_pretty_term(lower, names, 0)} ≤ {_pretty_term(upper, names, 0)}"
                )}]
                precedence = 5
            elif isinstance(formula, Eq):
                parts = [{"kind": "text", "text": (
                    f"{_pretty_term(formula.left, names, 0)} = "
                    f"{_pretty_term(formula.right, names, 0)}"
                )}]
                precedence = 5
            elif isinstance(formula, Bot):
                parts, precedence = [{"kind": "text", "text": "⊥"}], 5
            elif isinstance(formula, Imp) and isinstance(formula.right, Bot):
                parts = [{"kind": "text", "text": "¬"}]
                for item in self._render(formula.left, names, 4, uses):
                    _parts_append(parts, item["text"], definition=item.get("definition"))
                precedence = 4
            elif isinstance(formula, (And, Or, Imp)):
                if isinstance(formula, And):
                    precedence, symbol = 3, "∧"
                elif isinstance(formula, Or):
                    precedence, symbol = 2, "∨"
                else:
                    precedence, symbol = 1, "→"
                parts = self._render(
                    formula.left,
                    names,
                    precedence + (1 if isinstance(formula, Imp) else 0),
                    uses,
                )
                _parts_append(parts, f" {symbol} ")
                right_precedence = precedence if isinstance(formula, Imp) else precedence + 1
                if isinstance(formula, Imp) and isinstance(formula.right, (Forall, Exists)):
                    right_precedence = 0
                for item in self._render(formula.right, names, right_precedence, uses):
                    _parts_append(parts, item["text"], definition=item.get("definition"))
            elif isinstance(formula, (Forall, Exists)):
                binder = _fresh_binder(names)
                if binders and binders[0][0] is type(formula):
                    _quantifier, preferred = binders.pop(0)
                    if preferred not in names:
                        binder = preferred
                symbol = "∀" if isinstance(formula, Forall) else "∃"
                parts = [{"kind": "text", "text": f"{symbol} {binder}. "}]
                for item in self._render(formula.body, [binder] + names, 0, uses, binders):
                    _parts_append(parts, item["text"], definition=item.get("definition"))
                precedence = 0
            else:
                raise TypeError("expected an ordinary first-order Heyting-arithmetic formula")
        if precedence < parent_precedence:
            wrapped = [{"kind": "text", "text": "("}]
            for item in parts:
                _parts_append(wrapped, item["text"], definition=item.get("definition"))
            _parts_append(wrapped, ")")
            return wrapped
        return parts

    def compact(self, source: str) -> dict[str, Any]:
        exact, free_names = parse_formula_with_names(source)
        uses: Counter[str] = Counter()
        parts = self._render(
            exact,
            list(free_names),
            0,
            uses,
            _leading_source_binders(source),
        )
        surface = "".join(part["text"] for part in parts)
        parser = _LocalDefinedParser(surface, self.by_name)
        parser.free = list(free_names)
        expanded = parser.parse()
        if tuple(parser.free) != free_names or expanded != exact:
            raise NextLayerExplorerError(
                "next-layer defined notation does not expand to the exact native formula"
            )
        if Counter(
            part["definition"] for part in parts if part["kind"] == "definition"
        ) != uses:
            raise NextLayerExplorerError("defined theorem tokens do not match their use receipt")
        return {
            "defined_statement": surface,
            "expanded_statement_sha256": _digest(source),
            "defined_statement_sha256": _digest(surface),
            "statement_parts": parts,
            "statement_definition_uses": dict(sorted(uses.items())),
            "script_definition_uses": {},
            "definition_uses": dict(sorted(uses.items())),
            "exact_ast_equivalence": True,
            "free_names": list(free_names),
        }


def _load_inputs() -> dict[str, Any]:
    """Validate sealed release receipts without decoding any proof artifact."""

    raw_catalog = CATALOG.read_bytes()
    catalog = json.loads(raw_catalog)
    expected_counts = {
        campaign.value: count for campaign, count in EXPECTED_CAMPAIGN_COUNTS.items()
    }
    if (
        catalog.get("schema") != "peano-library-alpha-snapshot-v20"
        or catalog.get("theorem_count") != EXPECTED_ALPHA_COUNT
        or catalog.get("checked_use_count") != EXPECTED_ALPHA_COUNT
        or catalog.get("stable_count") != EXPECTED_STABLE_COUNT
        or catalog.get("edition_identity_sha256") != v20.ALPHA_V20_IDENTITY_SHA256
        or catalog.get("frontier_v20_campaign_counts") != expected_counts
    ):
        raise NextLayerExplorerError("the sealed, fully checked Alpha-v20 catalog changed")
    promotion = catalog.get("alpha_v20_next_layer_promotion")
    if (
        not isinstance(promotion, dict)
        or promotion.get("status")
        != "kernel_checked_complete_dependency_closed_additive_edition"
        or promotion.get("frontier_new_count") != FRONTIER_V20_EXPECTED_COUNT
        or promotion.get("campaign_counts") != expected_counts
        or promotion.get("remaining_body_checked_count") != 0
    ):
        raise NextLayerExplorerError("Alpha-v20 lacks complete constructive admission evidence")
    bundle = promotion.get("proof_bundle")
    expected_path = (
        "research/arithmetic-library/artifacts/alpha-v20-next-layer-proof-bundle-v1.json"
    )
    if (
        not isinstance(bundle, dict)
        or bundle.get("artifact_path") != expected_path
        or bundle.get("node_count") != EXPECTED_BUNDLE_NODE_COUNT
        or bundle.get("kernel_calls") != EXPECTED_BUNDLE_NODE_COUNT
        or bundle.get("frontier_count") != FRONTIER_V20_EXPECTED_COUNT
        or bundle.get("inherited_dependency_count")
        != EXPECTED_BUNDLE_NODE_COUNT - FRONTIER_V20_EXPECTED_COUNT - 1
    ):
        raise NextLayerExplorerError("Alpha-v20 lacks the exact original-kernel bundle receipt")
    artifact = (REPO / expected_path).resolve()
    if (
        artifact.parent != (REPO / "research" / "arithmetic-library" / "artifacts").resolve()
        or not artifact.is_file()
        or artifact.stat().st_size != bundle.get("artifact_bytes")
        or _file_digest(artifact) != bundle.get("artifact_sha256")
    ):
        raise NextLayerExplorerError("the sealed constructive proof-bundle bytes changed")

    channels = json.loads(CURRENT_CHANNELS.read_text(encoding="utf-8"))
    current = channels.get("channels", {}).get("alpha", {})
    current_digest = _file_digest(CURRENT_CATALOG)
    if (
        channels.get("schema") != "peano-library-channels-v24"
        or channels.get("default_channel") != "stable"
        or channels.get("parent_channels_v23", {}).get("path")
        != "artifacts/peano-library/channels-v23.json"
        or current.get("artifact_path") != "artifacts/peano-library/alpha/catalog-v24.json"
        or current.get("artifact_sha256") != current_digest
        or current.get("theorem_count") != v24.EXPECTED_ALPHA_V24_COUNT
        or current.get("checked_use_count") != v24.EXPECTED_ALPHA_V24_CHECKED_USE_COUNT
        or current.get("edition_identity_sha256") != v24.ALPHA_V24_IDENTITY_SHA256
        or current.get("parent_alpha_v20_sha256") != _digest(raw_catalog)
    ):
        raise NextLayerExplorerError("the current immutable Alpha-v24 child release changed")

    entries = catalog.get("theorems")
    if not isinstance(entries, list) or len(entries) != EXPECTED_ALPHA_COUNT:
        raise NextLayerExplorerError("Alpha-v20 does not contain its complete theorem catalog")
    by_name: dict[str, dict[str, Any]] = {}
    for row in entries:
        if not isinstance(row, dict) or not isinstance(row.get("name"), str):
            raise NextLayerExplorerError("malformed theorem row in Alpha-v20")
        if row["name"] in by_name:
            raise NextLayerExplorerError(f"duplicate Alpha-v20 theorem {row['name']!r}")
        by_name[row["name"]] = row

    campaign = json.loads(CAMPAIGN.read_text(encoding="utf-8"))
    global_graph = json.loads(GLOBAL_DEFINITIONS.read_text(encoding="utf-8"))
    canonical_campaign = json.dumps(
        campaign, ensure_ascii=False, allow_nan=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    if (
        global_graph.get("definition_count") != len(campaign.get("definitions", ()))
        or global_graph.get("campaign_snapshot_sha256") != _digest(canonical_campaign)
    ):
        raise NextLayerExplorerError("global atlas definition artifact is stale")
    if not isinstance(campaign["definitions"], dict):
        raise NextLayerExplorerError("global atlas does not contain named definitions")
    blueprint = dict(campaign["definitions"])
    milestones = {row["id"]: row for row in campaign.get("nodes", ())}
    linked_roots = {
        "T12": "beta_horner_eval_exists",
        "T13": "beta_dot_product_exists_unique",
        "G023": "central_binom_prime_divisor_multiplicity_one_exists",
        "G024": "iterated_bertrand_prime_chain_exists",
        "G071": "continued_fraction_positive_exists",
    }
    for goal, root in linked_roots.items():
        milestone = milestones.get(goal)
        theorem = by_name.get(root)
        evidence = milestone.get("evidence") if isinstance(milestone, dict) else None
        partial = goal == "T13"
        if partial:
            from peano_lab.library.campaign_research_layer_closure import (
                EXPECTED_RESEARCH_LAYER_BUNDLE_NODE_COUNT,
                EXPECTED_RESEARCH_LAYER_BUNDLE_SHA256,
                research_layer_plan,
            )

            current_root = v24.entry("beta_signed_matrix_minor_exists", edition="alpha")
            positions = {
                row.name: row.node_id for row in research_layer_plan().rows
            }
            if (
                theorem is None
                or current_root is None
                or not isinstance(evidence, dict)
                or evidence.get("alpha_version") != "v24"
                or evidence.get("independent_lean_bundle_verified") is not True
                or evidence.get("partial_theorem_name") != current_root.spec.name
                or evidence.get("partial_theorem_statement_sha256")
                != _digest(current_root.spec.statement)
                or evidence.get("bundle_sha256") != EXPECTED_RESEARCH_LAYER_BUNDLE_SHA256
                or evidence.get("bundle_nodes") != EXPECTED_RESEARCH_LAYER_BUNDLE_NODE_COUNT
                or evidence.get("bundle_node_id") != positions[current_root.spec.name]
                or milestone.get("status") != "open"
                or evidence.get("checked_use") is not False
                or evidence.get("partial_component_checked_use") is not True
                or evidence.get("full_arbitrary_signed_matrix_product_proved") is not True
                or evidence.get("full_arbitrary_signed_minor_proved") is not True
                or evidence.get("signed_four_by_four_determinant_proved") is not True
                or evidence.get("full_arbitrary_determinant_proved") is not False
                or evidence.get("full_rank_substrate_proved") is not False
                or evidence.get("full_lattice_substrate_proved") is not False
            ):
                raise NextLayerExplorerError(
                    "T13 lost its independently verified Alpha-v24 signed-minor "
                    "progress or falsely claimed full closure"
                )
            continue
        name_key = "partial_theorem_name" if partial else "theorem_name"
        digest_key = "partial_theorem_statement_sha256" if partial else "theorem_statement_sha256"
        if (
            theorem is None
            or not isinstance(evidence, dict)
            or evidence.get("independent_lean_bundle_verified") is not True
            or evidence.get("bundle_sha256") != bundle["artifact_sha256"]
            or evidence.get(name_key) != root
            or evidence.get(digest_key) != theorem.get("statement_sha256")
            or evidence.get("bundle_node_id")
            != theorem.get("empty_context_closure", {}).get("bundle_node_id")
            or evidence.get("alpha_version") != "v20"
            or milestone.get("status") != ("open" if partial else "alpha_closed")
            or evidence.get("checked_use") is not (False if partial else True)
            or (partial and evidence.get("partial_component_checked_use") is not True)
        ):
            raise NextLayerExplorerError(
                f"milestone lacks its exact independently Lean-verified bundle evidence: {goal}"
            )
    enrollment = alpha_v20_enrollment()
    if len(enrollment.frontier_specs) != FRONTIER_V20_EXPECTED_COUNT:
        raise NextLayerExplorerError("Alpha-v20 enrollment does not contain exactly 39 proofs")
    for spec in enrollment.frontier_specs:
        row = by_name.get(spec.name)
        if row is None:
            raise NextLayerExplorerError(f"sealed catalog omits checked theorem {spec.name!r}")
        _validate_theorem(
            row,
            spec=spec,
            campaign=enrollment.campaign_by_name[spec.name],
            source=enrollment.source_by_name[spec.name],
            bundle=bundle,
        )
    return {
        "catalog": catalog,
        "catalog_sha256": current_digest,
        "historical_catalog_sha256": _digest(raw_catalog),
        "current_edition_identity_sha256": v24.ALPHA_V24_IDENTITY_SHA256,
        "revision": current_digest[:12],
        "bundle": bundle,
        "by_name": by_name,
        "campaign": campaign,
        "blueprint": blueprint,
        "milestones": milestones,
        "global_graph": global_graph,
        "enrollment": enrollment,
    }


def _validate_theorem(
    row: Mapping[str, Any],
    *,
    spec: Any,
    campaign: FrontierV20Campaign,
    source: str,
    bundle: Mapping[str, Any],
) -> None:
    """Reject any release row whose exact logic, provenance, or closure changed."""

    if (
        row.get("name") != spec.name
        or row.get("statement") != spec.statement
        or row.get("dependencies") != list(spec.dependencies)
        or row.get("script") != list(spec.script)
        or row.get("summary") != spec.summary
        or row.get("frontier_campaign") != campaign.value
        or row.get("statement_sha256") != _digest(spec.statement)
        or row.get("script_sha256") != _digest("\n".join(spec.script) + "\n")
        or row.get("checked_use") is not True
        or row.get("evidence_status") != "alpha_closed"
        or row.get("membership") != "alpha_only"
        or not isinstance(row.get("source"), dict)
        or row["source"].get("path") != source
    ):
        raise NextLayerExplorerError(f"exact checked Alpha-v20 theorem changed: {spec.name}")
    closure = row.get("empty_context_closure")
    receipt = row.get("alpha_v20_frontier_enrollment")
    if (
        not isinstance(closure, dict)
        or closure.get("status") != "checked"
        or closure.get("kernel_mode") != "intuitionistic"
        or closure.get("closure_kind") != "dependency_closed_bundle_node"
        or closure.get("bundle_campaign") != "next_layer"
        or closure.get("bundle_node_count") != bundle["node_count"]
        or closure.get("bundle_path") != bundle["artifact_path"]
        or closure.get("certificate_sha256") != bundle["artifact_sha256"]
        or closure.get("node_statement_sha256") != row["statement_sha256"]
        or type(closure.get("bundle_node_id")) is not int
        or not 0 <= closure["bundle_node_id"] < bundle["node_count"]
        or not isinstance(receipt, dict)
        or receipt.get("campaign") != campaign.value
        or receipt.get("bundle_campaign") != "next_layer"
        or receipt.get("bundle_node_id") != closure["bundle_node_id"]
        or receipt.get("bundle_sha256") != bundle["artifact_sha256"]
    ):
        raise NextLayerExplorerError(
            f"theorem lacks its original-kernel dependency-closed proof: {spec.name}"
        )


def _definition_records(
    family: Family, inputs: Mapping[str, Any]
) -> tuple[tuple[DefinitionSpec, ...], list[dict[str, Any]]]:
    specs = _definition_closure(family.definitions)
    by_name = {item.name: item for item in specs}
    reviewed_links = {
        row["reviewed_name"]: row
        for row in inputs["global_graph"]["compatible_reviewed_matches"]
    }
    global_reviewed = {
        row["name"]: row for row in inputs["global_graph"]["reviewed_definitions"]
    }
    canonical_routes = {
        definition.name: route
        for route, definitions in NEXT_LAYER_REGISTRIES
        for definition in definitions
    }
    by_id: dict[str, dict[str, Any]] = {}
    rows: list[dict[str, Any]] = []
    for definition in specs:
        direct = [by_name[name].stable_id for name in definition.conceptual_dependencies]
        if any(identifier not in by_id for identifier in direct):
            raise NextLayerExplorerError("definition DAG is not in dependency-first order")
        ancestors: set[str] = set(direct)
        for identifier in direct:
            ancestors.update(by_id[identifier]["transitive_dependencies"])
        layer = max((by_id[identifier]["topological_layer"] + 1 for identifier in direct), default=0)
        custom = definition.stable_id.startswith("ND")
        blueprint = inputs["blueprint"].get(definition.name)
        global_name: str | None = None
        positions: list[int] | None = None
        reviewed_id: str | None = None
        reviewed_route: str | None = None
        if custom:
            shared = NEXT_LAYER_DEFINITIONS_BY_NAME.get(definition.name)
            global_record = global_reviewed.get(definition.name)
            if (
                shared is not definition
                or global_record is None
                or global_record.get("id") != definition.stable_id
                or tuple(global_record.get("parameters", ())) != definition.parameters
                or global_record.get("expansion_sha256") != _digest(definition.template_source)
                or global_record.get("dependencies") != list(definition.conceptual_dependencies)
                or global_record.get("route") != canonical_routes.get(definition.name)
            ):
                raise NextLayerExplorerError(
                    f"definition {definition.name!r} is not the canonical shared reviewed object"
                )
            reviewed_id = definition.stable_id
            reviewed_route = global_record["route"]
        if custom and blueprint is not None:
            if tuple(blueprint["parameters"]) != definition.parameters:
                raise NextLayerExplorerError(
                    f"new definition {definition.name!r} disagrees with global blueprint arity"
                )
            global_name, positions = definition.name, list(range(definition.arity))
            if definition.name == "Beta":
                reviewed = _definition_specs()["BetaAt"]
                if (
                    reviewed.parameters != definition.parameters
                    or reviewed.template_formula != definition.template_formula
                ):
                    raise NextLayerExplorerError("Beta is no longer the exact reviewed BetaAt alias")
                reviewed_id = reviewed.stable_id
                reviewed_route = reviewed_links["BetaAt"]["route"]
            else:
                reviewed = reviewed_links.get(definition.name)
                if (
                    reviewed is None
                    or reviewed.get("reviewed_id") != definition.stable_id
                    or reviewed.get("blueprint_name") != definition.name
                    or reviewed.get("route") != canonical_routes[definition.name]
                    or reviewed.get("reviewed_expansion_sha256")
                    != _digest(definition.template_source)
                ):
                    raise NextLayerExplorerError(
                        f"global atlas does not share canonical reviewed definition {definition.name!r}"
                    )
        elif not custom and definition.name in reviewed_links:
            reviewed = reviewed_links[definition.name]
            if (
                reviewed["reviewed_id"] != definition.stable_id
                or tuple(reviewed["reviewed_parameters"]) != definition.parameters
            ):
                raise NextLayerExplorerError(
                    f"reviewed definition {definition.name!r} changed its atlas signature"
                )
            global_name = reviewed["blueprint_name"]
            positions = list(reviewed["reviewed_argument_blueprint_positions"])
            reviewed_id = definition.stable_id
            reviewed_route = reviewed["route"]
        if global_name is not None:
            if len(positions or ()) != definition.arity or sorted(positions or ()) != list(
                range(definition.arity)
            ):
                raise NextLayerExplorerError("global definition argument permutation is invalid")
            if global_name not in inputs["blueprint"]:
                raise NextLayerExplorerError("local definition links to an unknown atlas node")
        row = {
            "id": definition.stable_id,
            "name": definition.name,
            "parameters": list(definition.parameters),
            "arity": definition.arity,
            "signature": f"{definition.name}({','.join(definition.parameters)})",
            "summary": definition.summary,
            "expanded_template": definition.template_source,
            "expansion_sha256": _digest(definition.template_source),
            "dependencies": direct,
            "dependency_names": list(definition.conceptual_dependencies),
            "topological_layer": layer,
            "transitive_dependencies": sorted(ancestors),
            "origin": (
                "shared-reviewed-hygienic-conservative-definition"
                if custom
                else "reviewed-conservative-definition"
            ),
            "reviewed_definition_id": reviewed_id,
            "reviewed_definition_route": reviewed_route,
            "shared_definition_identity": definition.stable_id if custom else None,
            "global_definition": global_name,
            "global_argument_positions": positions,
            "exact_ast_verified": True,
            "kernel_signature_unchanged": True,
        }
        by_id[definition.stable_id] = row
        rows.append(row)
    return specs, rows


def _factory_name(campaign: FrontierV20Campaign) -> str:
    return {
        FrontierV20Campaign.POLYNOMIAL_HORNER: "make_polynomial_horner_candidate_theorems",
        FrontierV20Campaign.MATRIX_DOT_PRODUCT: "make_matrix_dot_product_candidate_theorems",
        FrontierV20Campaign.BERTRAND_PRIME: "make_bertrand_prime_campaign_candidate_theorems",
        FrontierV20Campaign.CONTINUED_FRACTION: "make_continued_fraction_candidate_theorems",
    }[campaign]


def _goal(family: Family, theorem: str) -> str:
    if family.campaign is FrontierV20Campaign.BERTRAND_PRIME:
        return "G024" if "chain" in theorem else "G023"
    return family.milestones[-1]


def _family_corpus(family: Family, inputs: Mapping[str, Any]) -> dict[str, Any]:
    enrollment = inputs["enrollment"]
    specs = tuple(
        spec
        for spec in enrollment.frontier_specs
        if enrollment.campaign_by_name[spec.name] is family.campaign
    )
    if len(specs) != EXPECTED_CAMPAIGN_COUNTS[family.campaign]:
        raise NextLayerExplorerError(f"checked family cardinality changed: {family.slug}")
    definition_specs, definitions = _definition_records(family, inputs)
    compactor = _FormulaCompactor(definition_specs)
    tags = {spec.name: f"{family.prefix}{index:04X}" for index, spec in enumerate(specs, 1)}
    nodes: list[dict[str, Any]] = []
    for spec in specs:
        row = inputs["by_name"][spec.name]
        closure = row["empty_context_closure"]
        source = enrollment.source_by_name[spec.name]
        nodes.append({
            "id": tags[spec.name],
            "name": spec.name,
            "summary": spec.summary,
            "statement": spec.statement,
            "statement_sha256": row["statement_sha256"],
            "script": list(spec.script),
            "dependencies": list(spec.dependencies),
            "source_module": source,
            "factory": _factory_name(family.campaign),
            "sources": [{
                "source_module": source,
                "factory": _factory_name(family.campaign),
                "selected": True,
                "statement_sha256": row["statement_sha256"],
                "script_sha256": row["script_sha256"],
            }],
            "status": STATUS,
            "enrolled_in_alpha": True,
            "alpha_evidence": "alpha_closed",
            "alpha_checked_use": True,
            "alpha_edition_version": "v24",
            "alpha_first_enrolled_version": "v20",
            "stable_member": False,
            "admitted_to_alpha": True,
            "admitted_to_stable": False,
            "checked_use": True,
            "independent_lean_bundle_verified": True,
            "proof_bundle_node_id": closure["bundle_node_id"],
            "proof_bundle_sha256": closure["certificate_sha256"],
            "body_proof_nodes": closure["body_proof_nodes"],
            "body_proof_depth": closure["body_proof_depth"],
            "campaign_milestone": _goal(family, spec.name),
            "defined": compactor.compact(spec.statement),
        })
    for name in family.roots:
        if name not in tags:
            raise NextLayerExplorerError(f"published root is absent from checked family: {name}")

    external_names = sorted({
        dependency for node in nodes for dependency in node["dependencies"] if dependency not in tags
    })
    external: list[dict[str, Any]] = []
    for name in external_names:
        row = inputs["by_name"].get(name)
        if row is None or row.get("checked_use") is not True:
            raise NextLayerExplorerError(f"unchecked or unknown theorem prerequisite: {name}")
        stable = row.get("membership") == "stable"
        external.append({
            "name": name,
            "evidence": row["evidence_status"],
            "alpha_evidence": row["evidence_status"],
            "alpha_checked_use": True,
            "enrolled_in_alpha": True,
            "admitted_to_alpha": True,
            "admitted_to_stable": stable,
            "kind": "stable-admitted-theorem" if stable else "alpha-admitted-theorem",
            "statement_sha256": row["statement_sha256"],
        })

    layers: dict[str, int] = {}
    critical_paths: dict[str, list[str]] = {}
    adjacency: dict[str, dict[str, list[str]]] = {}
    by_name = {node["name"]: node for node in nodes}
    for node in nodes:
        internal = [name for name in node["dependencies"] if name in tags]
        if any(name not in layers for name in internal):
            raise NextLayerExplorerError("theorem DAG has a forward or circular dependency")
        layers[node["name"]] = max((layers[name] + 1 for name in internal), default=0)
        previous = max(internal, key=lambda name: len(critical_paths[name]), default=None)
        critical_paths[node["name"]] = (
            ([] if previous is None else critical_paths[previous]) + [tags[node["name"]]]
        )
    for node in nodes:
        name = node["name"]
        adjacency[name] = {
            "dependencies": [dep for dep in node["dependencies"] if dep in tags],
            "dependents": [item["name"] for item in nodes if name in item["dependencies"]],
            "critical_root_path": critical_paths[name],
        }

    proof_edges = [
        {"kind": "proof_dependency", "source": tags[name], "target": tags[node["name"]]}
        for node in nodes for name in node["dependencies"] if name in tags
    ]
    usage_edges = [
        {
            "kind": "uses_definition",
            "source": tags[node["name"]],
            "target": identifier,
            "occurrence_count": count,
            "statement_occurrences": count,
            "local_proposition_occurrences": 0,
        }
        for node in nodes
        for identifier, count in node["defined"]["statement_definition_uses"].items()
    ]
    notation_edges = [
        {"kind": "definition_uses_definition", "source": item["id"], "target": dependency}
        for item in definitions for dependency in item["dependencies"]
    ]
    return {
        "schema": SCHEMA,
        "family_slug": family.slug,
        "family_title": family.title,
        "campaign_domain_id": family.domain,
        "campaign_family_id": family.family_id,
        "campaign_goal_id": family.milestones[-1],
        "campaign_milestone_ids": list(family.milestones),
        "root_names": list(family.roots),
        "nodes": nodes,
        "definitions": definitions,
        "external_dependencies": external,
        "edges": proof_edges + usage_edges + notation_edges,
        "node_count": len(nodes),
        "edge_count": sum(len(node["dependencies"]) for node in nodes),
        "internal_edge_count": len(proof_edges),
        "external_dependency_count": len(external),
        "definition_count": len(definitions),
        "definition_dependency_count": len(notation_edges),
        "definition_layer_count": max((item["topological_layer"] + 1 for item in definitions), default=0),
        "definition_topological_order": [item["id"] for item in definitions],
        "statement_definition_use_count": len(usage_edges),
        "formal_line_count": sum(len(node["script"]) for node in nodes),
        "candidate_status": STATUS,
        "alpha_edition_version": "v24",
        "alpha_first_enrolled_version": "v20",
        "alpha_edition_identity_sha256": inputs["current_edition_identity_sha256"],
        "alpha_catalog_sha256": inputs["catalog_sha256"],
        "alpha_first_enrollment_catalog_sha256": inputs["historical_catalog_sha256"],
        "alpha_proof_bundle_sha256": inputs["bundle"]["artifact_sha256"],
        "independent_lean_bundle_verified": True,
        "alpha_enrolled_node_count": len(nodes),
        "alpha_checked_use_node_count": len(nodes),
        "stable_admitted_node_count": 0,
        "tags": tags,
        "layers": layers,
        "proof_adjacency": adjacency,
        "proof_paths": {tags[name]: path for name, path in critical_paths.items()},
        "path_policy": "proof_dependency_edges_only",
    }


def _asset(name: str, prefix: str) -> str:
    digest = PINNED_ASSETS.get(name)
    if digest is None:
        digest = _file_digest(ASSET_SOURCES[name])
    return _versioned(f"{prefix}assets/{name}", digest[:12])


def _atlas_navigation(
    family: Family, *, prefix: str, revision: str, goal: str | None = None
) -> str:
    labels = (
        ("global", "Full campaign map", ""),
        ("domain", "Campaign domain", f"?view=domain&focus={family.domain}"),
        ("family", "Campaign family", f"?view=family&focus={family.family_id}"),
    )
    parts = [
        f'<a data-campaign-link="{kind}" '
        f'href="{_versioned(f"{prefix}grand-campaign/{suffix}", revision)}">'
        f"{_e(label)}</a>"
        for kind, label, suffix in labels
    ]
    for milestone in ((goal,) if goal is not None else family.milestones):
        parts.append(
            f'<a data-campaign-link="goal" data-campaign-goal="{_e(milestone)}" '
            f'href="{_versioned(f"{prefix}grand-campaign/?view=goal&focus={milestone}", revision)}">'
            f"{_e(milestone)} milestone</a>"
        )
    return "".join(parts)


def _inject_atlas_navigation(
    document: bytes, family: Family, *, prefix: str, revision: str, goal: str | None = None
) -> bytes:
    extras = []
    extras.append(
        f'<a data-campaign-link="domain" '
        f'href="{_versioned(f"{prefix}grand-campaign/?view=domain&focus={family.domain}", revision)}">'
        "Campaign domain</a>"
    )
    for milestone in ((goal,) if goal is not None else family.milestones):
        extras.append(
            f'<a data-campaign-link="goal" data-campaign-goal="{_e(milestone)}" '
            f'href="{_versioned(f"{prefix}grand-campaign/?view=goal&focus={milestone}", revision)}">'
            f"{_e(milestone)} milestone</a>"
        )
    if document.count(b"</nav>") != 1:
        raise NextLayerExplorerError("shared exact renderer changed its navigation contract")
    return document.replace(b"</nav>", "".join(extras).encode("utf-8") + b"</nav>", 1)


def _document(
    family: Family,
    *,
    title: str,
    body: str,
    prefix: str,
    defined: bool = True,
    extra_script: str = "",
) -> bytes:
    style = "defined-explorer.css" if defined else "proofs.css"
    script = (
        f'<script defer src="{_asset("defined-explorer.js", prefix)}"></script>'
        if defined else ""
    )
    classes = "pa-defined-proof-site" if defined else "proof-library-site"
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{_e(title)}</title>
  <link rel="stylesheet" href="{_asset(style, prefix)}">
  {script}{extra_script}
</head>
<body class="{classes}" data-family="{_e(family.slug)}">{body}</body>
</html>
""".encode("utf-8")


def _family_landing(
    family: Family, corpus: Mapping[str, Any], *, revision: str
) -> bytes:
    return render_canonical_family_landing(
        family,
        corpus,
        revision=revision,
        current_alpha_version="v24",
        first_admitted_version="v20",
        bundle_node_count=EXPECTED_BUNDLE_NODE_COUNT,
    )


def _defined_statement(node: Mapping[str, Any], *, revision: str) -> str:
    rendered: list[str] = []
    for part in node["defined"]["statement_parts"]:
        text = _e(part["text"])
        if part["kind"] == "definition":
            text = (
                f'<a class="pd-definition-ref" data-definition="{_e(part["definition"])}" '
                f'href="{_versioned("../definition/" + part["definition"] + ".html", revision)}">'
                f"{text}</a>"
            )
        rendered.append(text)
    return "".join(rendered)


def _defined_index(
    family: Family, corpus: Mapping[str, Any], *, revision: str
) -> bytes:
    cards: list[str] = []
    for node in corpus["nodes"]:
        tag = corpus["tags"][node["name"]]
        cards.append(
            '<article class="pd-result pd-result-theorem" '
            f'data-entry data-kind="theorem" data-status="alpha_closed" '
            f'data-layer="{corpus["layers"][node["name"]]}" '
            f'data-search="{_e((tag + " " + node["name"] + " " + node["summary"]).lower())}">'
            f'<a href="{_versioned(f"tag/{tag}.html", revision)}">'
            f'<code>{_e(tag)}</code> <strong>{_e(node["name"])}</strong></a>'
            f'<p>{_e(node["summary"])}</p><small>{_e(STATUS)}</small></article>'
        )
    for definition in corpus["definitions"]:
        cards.append(
            '<article class="pd-result pd-result-definition" '
            f'data-entry data-kind="definition" data-status="definition" '
            f'data-layer="{definition["topological_layer"]}" '
            f'data-search="{_e((definition["id"] + " " + definition["signature"] + " " + definition["summary"]).lower())}">'
            f'<a href="{_versioned("definition/" + definition["id"] + ".html", revision)}">'
            f'<code>{_e(definition["id"])}</code> <strong>{_e(definition["signature"])}</strong></a>'
            f'<p>{_e(definition["summary"])}</p><small>Conservative definition · '
            f'notation layer {definition["topological_layer"]}</small></article>'
        )
    root = corpus["tags"][family.roots[-1]]
    body = f"""<header class="pd-header pd-hero">
  <nav><a href="{_versioned('../../', revision)}">{_e(family.title)}</a>
       <a href="{_versioned('../', revision)}">Exact proof explorer</a>
       <a href="{_versioned(f'graph.html?target={root}', revision)}">Interactive dependency graph</a>
       {_atlas_navigation(family, prefix='../../../', revision=revision)}</nav>
  <p class="pd-kicker">{_e(family.kicker)}</p><h1>{_e(family.title)}</h1>
  <p>{_e(family.description)}</p>
  <div class="pd-stats"><b>{corpus['node_count']}</b> kernel- and Lean-verified Alpha-closed theorems ·
    <b>{corpus['definition_count']}</b> conservative definitions ·
    <b>{corpus['definition_dependency_count']}</b> notation dependencies</div>
  <p class="pd-status">{_e(STATUS)}</p>
</header>
<main data-defined-dashboard><section class="pd-controls">
  <label>Search <input data-search type="search"></label>
  <label>Kind <select data-kind><option value="all">All</option><option value="theorem">Checked theorems</option><option value="definition">Definitions</option></select></label>
  <label>Layer <select data-layer><option value="all">All layers</option>{''.join(f'<option value="{layer}">{layer}</option>' for layer in sorted(set(corpus['layers'].values())))}</select></label>
  <button data-clear type="button">Clear</button><output data-count>{len(cards)} items</output>
</section><section class="pd-results">{''.join(cards)}</section>
<p class="pd-callout">Only proof arrows are theorem dependencies. Definition arrows are hygienic abbreviations of exact first-order formulas and introduce no axiom or kernel symbol.</p>
</main>"""
    return _document(
        family, title=f"{family.title} — Defined Proof Explorer", body=body, prefix="../../../"
    )


_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_']*")


def _formal_command(
    line: str,
    *,
    tags: Mapping[str, str],
    dependencies: set[str],
    revision: str,
) -> str:
    parts: list[str] = []
    end = 0
    for match in _IDENTIFIER.finditer(line):
        parts.append(_e(line[end:match.start()]))
        token = match.group()
        if token in dependencies and token in tags:
            parts.append(
                f'<a class="pd-theorem-ref" '
                f'href="{_versioned(f"{tags[token]}.html", revision)}">{_e(token)}</a>'
            )
        else:
            parts.append(_e(token))
        end = match.end()
    parts.append(_e(line[end:]))
    return "".join(parts)


def _defined_theorem(
    family: Family, corpus: Mapping[str, Any], node: Mapping[str, Any], *, revision: str
) -> bytes:
    name = node["name"]
    tag = corpus["tags"][name]
    definitions = {item["id"]: item for item in corpus["definitions"]}
    uses = node["defined"]["definition_uses"]
    chips = "".join(
        f'<a class="pd-chip" href="{_versioned(f"../definition/{identifier}.html", revision)}">'
        f"{_e(definitions[identifier]['signature'])} · {count}</a>"
        for identifier, count in uses.items()
    ) or '<span class="pd-empty">none</span>'
    dependencies = "".join(
        (
            f'<a class="pd-chip" href="{_versioned(corpus["tags"][dependency] + ".html", revision)}">'
            f"{_e(dependency)}</a>"
            if dependency in corpus["tags"] else
            f'<span class="pd-chip pd-external">{_e(dependency)} · checked external prerequisite</span>'
        )
        for dependency in node["dependencies"]
    ) or '<span class="pd-empty">none</span>'
    proof_lines = "".join(
        f'<li class="pd-proof-line" id="L{index}" data-line="{index}">'
        f'<a class="pd-line-number" href="#L{index}">{index:04d}</a>'
        f'<code>{_formal_command(line, tags=corpus["tags"], dependencies=set(node["dependencies"]), revision=revision)}</code></li>'
        for index, line in enumerate(node["script"], 1)
    )
    milestone_note = (
        '<p class="pd-callout">T13 remains open: this proof is an independently checked '
        'finite matrix/dot-product component, not a proof of the full matrix-ring or '
        'Cayley–Hamilton milestone.</p>'
        if family.domain == "D05" else ""
    )
    body = f"""<header class="pd-header pd-theorem-heading">
  <nav><a href="{_versioned('../', revision)}">Definitions and proofs</a>
       <a href="{_versioned(f'../../tag/{tag}.html', revision)}">Exact original proof</a>
       <a href="{_versioned(f'../graph.html?target={tag}', revision)}">Interactive proof graph</a>
       {_atlas_navigation(family, prefix='../../../../', revision=revision, goal=node['campaign_milestone'])}</nav>
  <p class="pd-tag">{_e(tag)}</p><h1>{_e(name)}</h1>
  <p>{_e(node['summary'])}</p><p class="pd-status">{_e(STATUS)}</p>
</header>
<main class="pd-theorem-layout"><div class="pd-proof-panel">
  {milestone_note}
  <section class="pd-statement"><h2>Exact theorem in conservative defined notation</h2>
    <pre><code>{_defined_statement(node, revision=revision)}</code></pre>
    <p>Every linked abbreviation expands hygienically to the identical original native formula.</p></section>
  <section><h2>Definition DAG</h2><div class="pd-chip-row">{chips}</div></section>
  <section><h2>Actual proof prerequisites</h2><div class="pd-chip-row">{dependencies}</div></section>
  <details class="pd-expanded"><summary>Original expanded first-order statement</summary>
    <pre><code>{_e(node['statement'])}</code></pre></details>
  <section><h2>Complete unchanged native tactic proof</h2>
    <p>All {len(node['script'])} lines are the exact independently kernel-checked original script.</p>
    <ol class="pd-formal-proof">{proof_lines}</ol></section>
</div><aside class="pd-proof-sidebar pd-trust-panel"><h2>Independent closure receipt</h2>
  <dl><dt>Authority</dt><dd>Alpha v24 checked use</dd><dt>First admission</dt><dd>Alpha v20</dd><dt>Stable membership</dt><dd>none</dd>
      <dt>Proof-bundle node</dt><dd>{node['proof_bundle_node_id']} / {EXPECTED_BUNDLE_NODE_COUNT}</dd>
      <dt>Kernel mode</dt><dd>unchanged intuitionistic Heyting arithmetic</dd>
      <dt>Independent Lean verifier</dt><dd>compiled verifier accepted all 590 exact bundle nodes</dd>
      <dt>Body proof nodes / depth</dt><dd>{node['body_proof_nodes']} / {node['body_proof_depth']}</dd>
      <dt>Statement SHA-256</dt><dd><code>{_e(node['statement_sha256'])}</code></dd>
      <dt>Script SHA-256</dt><dd><code>{_e(node['sources'][0]['script_sha256'])}</code></dd>
      <dt>Proof bundle SHA-256</dt><dd><code>{_e(node['proof_bundle_sha256'])}</code></dd>
      <dt>Exact source module</dt><dd><code>{_e(node['source_module'])}</code></dd></dl>
</aside></main>"""
    return _document(family, title=f"{tag} — {name} — Defined Proof", body=body, prefix="../../../../")


def _defined_definition(
    family: Family,
    corpus: Mapping[str, Any],
    definition: Mapping[str, Any],
    *,
    revision: str,
) -> bytes:
    identifier = definition["id"]
    definitions = {item["id"]: item for item in corpus["definitions"]}
    dependencies = "".join(
        f'<a class="pd-chip" href="{_versioned(dependency + ".html", revision)}">'
        f"{_e(definitions[dependency]['signature'])}</a>"
        for dependency in definition["dependencies"]
    ) or '<span class="pd-empty">none — first-order arithmetic only</span>'
    consumers = [
        node for node in corpus["nodes"] if identifier in node["defined"]["definition_uses"]
    ]
    users = "".join(
        f'<a class="pd-chip" '
        f'href="{_versioned("../tag/" + corpus["tags"][node["name"]] + ".html", revision)}">'
        f"{_e(corpus['tags'][node['name']])} · {_e(node['name'])}</a>"
        for node in consumers
    ) or '<span class="pd-empty">none directly; see definition consumers</span>'
    notation_users = "".join(
        f'<a class="pd-chip" href="{_versioned(item["id"] + ".html", revision)}">'
        f"{_e(item['signature'])}</a>"
        for item in corpus["definitions"] if identifier in item["dependencies"]
    ) or '<span class="pd-empty">none</span>'
    global_link = (
        f'<a data-campaign-link="definition" '
        f'href="{_versioned("../../../../grand-campaign/?view=definition&focus=" + definition["global_definition"], revision)}">'
        f"Global definition: {_e(definition['global_definition'])}</a>"
        if definition["global_definition"] is not None else
        "<span>No signature-compatible global blueprint alias is asserted.</span>"
    )
    reviewed = (
        f"Exact reviewed registry identity {_e(definition['reviewed_definition_id'])}."
        if definition["reviewed_definition_id"] is not None else
        "Family-local hygienic display abbreviation."
    )
    body = f"""<header class="pd-header pd-definition-heading">
  <nav><a href="{_versioned('../', revision)}">Definitions and proofs</a>
       <a href="{_versioned('../graph.html', revision)}">Interactive dependency graph</a>
       {global_link}{_atlas_navigation(family, prefix='../../../../', revision=revision)}</nav>
  <p class="pd-tag">{_e(identifier)}</p><h1>{_e(definition['signature'])}</h1>
  <p>{_e(definition['summary'])}</p><p class="pd-status">Conservative notation; not a theorem, primitive, or axiom.</p>
</header><main class="pd-theorem-layout"><div class="pd-proof-panel">
  <section><h2>Hygienic expanded first-order definition</h2>
    <pre><code>{_e(definition['expanded_template'])}</code></pre>
    <p>The unchanged native kernel never receives this surface symbol. Binder-safe expansion produces only its existing first-order syntax.</p></section>
  <section><h2>Direct definition dependencies</h2><div class="pd-chip-row">{dependencies}</div></section>
  <section><h2>Definitions depending on this notation</h2><div class="pd-chip-row">{notation_users}</div></section>
  <section><h2>Checked theorems using this definition</h2><div class="pd-chip-row">{users}</div></section>
</div><aside class="pd-proof-sidebar"><h2>Definition identity</h2><dl>
  <dt>Arity</dt><dd>{definition['arity']}</dd>
  <dt>Topological notation layer</dt><dd>{definition['topological_layer']}</dd>
  <dt>Transitive prerequisites</dt><dd>{len(definition['transitive_dependencies'])}</dd>
  <dt>Origin</dt><dd>{_e(definition['origin'])}</dd>
  <dt>Reviewed identity</dt><dd>{reviewed}</dd>
  <dt>Expanded formula SHA-256</dt><dd><code>{_e(definition['expansion_sha256'])}</code></dd>
</dl></aside></main>"""
    return _document(
        family, title=f"{identifier} — {definition['signature']} — Definition", body=body,
        prefix="../../../../",
    )


def _graph_payload(
    family: Family, corpus: Mapping[str, Any], *, revision: str
) -> dict[str, Any]:
    theorem_nodes = [
        {
            "id": corpus["tags"][node["name"]],
            "name": node["name"],
            "kind": "theorem",
            "scope": "candidate",
            "summary": node["summary"],
            "layer": corpus["layers"][node["name"]],
            "href": _versioned(f"tag/{corpus['tags'][node['name']]}.html", revision),
            "alpha_checked_use": True,
            "alpha_edition_version": "v24",
            "alpha_first_enrolled_version": "v20",
            "independent_lean_bundle_verified": True,
            "stable_member": False,
            "proof_bundle_node_id": node["proof_bundle_node_id"],
        }
        for node in corpus["nodes"]
    ]
    definition_nodes = [
        {
            "id": item["id"],
            "name": item["name"],
            "kind": "definition",
            "signature": item["signature"],
            "summary": item["summary"],
            "layer": item["topological_layer"],
            "href": _versioned(f"definition/{item['id']}.html", revision),
            "global_definition": item["global_definition"],
        }
        for item in corpus["definitions"]
    ]
    adjacency = {
        corpus["tags"][name]: {
            "dependencies": [corpus["tags"][value] for value in row["dependencies"]],
            "dependents": [corpus["tags"][value] for value in row["dependents"]],
            "critical_root_path": row["critical_root_path"],
        }
        for name, row in corpus["proof_adjacency"].items()
    }
    return {
        "schema": f"{SCHEMA}-graph",
        "family_slug": family.slug,
        "nodes": theorem_nodes + definition_nodes,
        "edges": corpus["edges"],
        "proof_adjacency": adjacency,
        "root_ids": [corpus["tags"][name] for name in family.roots],
        "path_policy": "proof_dependency_edges_only",
        "alpha_edition_version": "v24",
        "alpha_first_enrolled_version": "v20",
        "independent_lean_bundle_verified": True,
        "alpha_checked_use_node_count": corpus["node_count"],
        "stable_admitted_node_count": 0,
        "definition_topological_order": corpus["definition_topological_order"],
    }


def _defined_graph(
    family: Family,
    corpus: Mapping[str, Any],
    graph: Mapping[str, Any],
    *,
    revision: str,
) -> bytes:
    serialized = json.dumps(graph, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
    if "</script" in serialized.lower():
        raise NextLayerExplorerError("graph payload contains an unsafe script boundary")
    overlay = """<script>
document.addEventListener("DOMContentLoaded", function () {
  var title = document.querySelector("[data-graph-title]");
  var kind = document.querySelector("[data-graph-kind]");
  if (!title || !kind || typeof MutationObserver === "undefined") return;
  function label() {
    var id = String(title.textContent || "").split(" · ")[0];
    var row = (window.PA_DEFINED_GRAPH.nodes || []).find(function (node) { return node.id === id; });
    if (row && row.kind === "theorem" && row.alpha_checked_use) {
      kind.textContent = "Alpha v24 checked-use theorem — first admitted v20; independently kernel and Lean verified; not Stable";
    }
  }
  new MutationObserver(label).observe(title, { childList: true, characterData: true, subtree: true });
  label();
});
</script>"""
    body = f"""<header class="pd-header pd-graph-heading">
 <nav><a href="{_versioned('./', revision)}">Definitions and proofs</a>
      <a href="{_versioned('../', revision)}">Exact original proof explorer</a>
      {_atlas_navigation(family, prefix='../../../', revision=revision)}</nav>
 <h1>{_e(family.title)} — interactive proof and definition DAG</h1>
 <p>Solid arrows are independently checked theorem prerequisites. Dashed arrows are conservative notation dependencies, never proof steps.</p>
</header>
<main class="pd-graph-page" data-defined-graph>
 <form class="pd-graph-controls" data-graph-form>
   <label>Target theorem <input list="pd-graph-theorems" data-graph-target><datalist id="pd-graph-theorems"></datalist></label>
   <label>Proof view <select data-graph-view><option value="critical">Critical proof path</option><option value="prerequisites">All proof prerequisites</option><option value="neighborhood">Immediate neighborhood</option><option value="corpus">Complete family</option></select></label>
   <label>Definitions <select data-graph-definitions><option value="selected">Selected theorem</option><option value="visible">All displayed theorems</option><option value="off">Hide notation</option></select></label>
   <label>Arrows <select data-graph-edges><option value="focus">Focused arrows</option><option value="all">All arrows</option><option value="none">Hide arrows</option></select></label>
   <button type="submit">Show proof</button>
 </form>
 <div class="pd-graph-workspace"><section class="pd-graph-canvas">
   <div class="pd-graph-toolbar"><button type="button" data-graph-zoom="in">+</button>
     <button type="button" data-graph-zoom="out">−</button>
     <button type="button" data-graph-fit>Fit proof</button>
     <output data-graph-summary>Loading checked constructive graph…</output></div>
   <div class="pd-graph-svg-wrap"><svg data-graph-svg tabindex="0" role="img" aria-label="Interactive checked theorem and conservative definition dependency graph"></svg></div>
 </section><aside class="pd-graph-details"><h2 data-graph-title tabindex="-1">Selected node</h2>
   <p data-graph-kind></p><p data-graph-description></p><dl data-graph-metadata></dl>
   <a data-graph-open href="#">Open node →</a><h3>Outgoing relations</h3>
   <ul data-graph-outgoing></ul><h3>Incoming relations</h3><ul data-graph-incoming></ul>
 </aside></div>
</main><script id="pa-defined-graph-data">window.PA_DEFINED_GRAPH={serialized};</script>{overlay}"""
    return _document(
        family, title=f"{family.title} — Interactive Checked Proof Graph", body=body,
        prefix="../../../",
    )


def _top_index(corpora: Sequence[tuple[Family, Mapping[str, Any]]], *, revision: str) -> bytes:
    entries = "".join(
        f'<article class="proof-card"><h2><a href="{_versioned(family.slug + "/", revision)}">'
        f"{_e(family.title)}</a></h2><p>{_e(family.description)}</p>"
        f"<p>{corpus['node_count']} independently checked theorems · "
        f"{corpus['definition_count']} conservative definitions</p></article>"
        for family, corpus in corpora
    )
    body = f"""<main class="proof-home proof-library-home"><header class="proof-hero">
 <p class="eyebrow">ALPHA v24 · CHECKED-USE · HISTORICAL v20 FIRST ADMISSION</p>
 <h1>Four independently checked number-theory campaigns</h1>
 <p>Thirty-nine completed intuitionistic Heyting-arithmetic proofs independently accepted by both the original kernel and the compiled Lean verifier, exposed with their exact original scripts, genuine proof DAGs, and hygienic conservative definition hierarchies.</p>
 <nav><a href="{_versioned('../', revision)}">Proof library</a>
 <a href="{_versioned('../grand-campaign/', revision)}">Full number-theory campaign atlas</a></nav>
 </header><section class="proof-grid">{entries}</section>
 <p>All displayed theorems were first independently admitted in Alpha v20 and retain checked-use authority in the current Alpha v24 release; Stable remains a separate immutable release.</p></main>"""
    return _document(FAMILIES[0], title="Constructive Next-Layer Proof Library", body=body,
                     prefix="", defined=False)


def build_files() -> dict[str, bytes]:
    """Return reproducible evidence-backed files without replaying a theorem."""

    inputs = _load_inputs()
    revision = inputs["revision"]
    files: dict[str, bytes] = {}
    for name, source in ASSET_SOURCES.items():
        payload = source.read_bytes()
        if name in PINNED_ASSETS and _digest(payload) != PINNED_ASSETS[name]:
            raise NextLayerExplorerError(f"reviewed shared explorer asset changed: {name}")
        files[f"assets/{name}"] = payload

    built: list[tuple[Family, Mapping[str, Any]]] = []
    for family in FAMILIES:
        corpus = _family_corpus(family, inputs)
        graph = _graph_payload(family, corpus, revision=revision)
        prefix = family.slug
        files[f"{prefix}/index.html"] = _family_landing(family, corpus, revision=revision)
        files[f"{prefix}/api/corpus.json"] = _json(corpus)
        files[f"{prefix}/explorer/index.html"] = _inject_atlas_navigation(
            render_exact_index(
                family,
                corpus,
                corpus["tags"],
                corpus["layers"],
                stylesheet_href=_asset("exact-explorer.css", "../../"),
                script_href=_asset("exact-explorer.js", "../../"),
                html_revision=revision,
            ),
            family,
            prefix="../../",
            revision=revision,
        )
        files[f"{prefix}/explorer/defined/index.html"] = _defined_index(
            family, corpus, revision=revision
        )
        files[f"{prefix}/explorer/defined/graph.html"] = _defined_graph(
            family, corpus, graph, revision=revision
        )
        files[f"{prefix}/explorer/defined/api/graph.json"] = _json(graph)
        for node in corpus["nodes"]:
            tag = corpus["tags"][node["name"]]
            files[f"{prefix}/explorer/tag/{tag}.html"] = _inject_atlas_navigation(
                render_exact_theorem(
                    family,
                    corpus,
                    node,
                    corpus["tags"],
                    corpus["layers"],
                    stylesheet_href=_asset("exact-explorer.css", "../../../"),
                    script_href=_asset("exact-explorer.js", "../../../"),
                    html_revision=revision,
                ),
                family,
                prefix="../../../",
                revision=revision,
                goal=node["campaign_milestone"],
            )
            files[f"{prefix}/explorer/defined/tag/{tag}.html"] = _defined_theorem(
                family, corpus, node, revision=revision
            )
        for definition in corpus["definitions"]:
            files[f"{prefix}/explorer/defined/definition/{definition['id']}.html"] = (
                _defined_definition(family, corpus, definition, revision=revision)
            )
        built.append((family, corpus))
    files["index.html"] = _top_index(built, revision=revision)
    inventory = [
        {"path": name, "bytes": len(payload), "sha256": _digest(payload)}
        for name, payload in sorted(files.items())
    ]
    manifest = {
        "schema": f"{SCHEMA}-manifest",
        "catalog_sha256": inputs["catalog_sha256"],
        "first_enrollment_catalog_sha256": inputs["historical_catalog_sha256"],
        "html_revision": revision,
        "edition_identity_sha256": inputs["current_edition_identity_sha256"],
        "alpha_edition_version": "v24",
        "alpha_first_enrolled_version": "v20",
        "proof_bundle_sha256": inputs["bundle"]["artifact_sha256"],
        "independent_lean_bundle_verified": True,
        "theorem_count": sum(corpus["node_count"] for _, corpus in built),
        "checked_use_count": sum(corpus["alpha_checked_use_node_count"] for _, corpus in built),
        "stable_count": 0,
        "families": [
            {
                "slug": family.slug,
                "campaign": family.campaign.value,
                "domain": family.domain,
                "family": family.family_id,
                "milestones": list(family.milestones),
                "theorem_count": corpus["node_count"],
                "definition_count": corpus["definition_count"],
                "root_tags": {name: corpus["tags"][name] for name in family.roots},
            }
            for family, corpus in built
        ],
        "file_count": len(inventory),
        "inventory_sha256": _digest(_json(inventory)),
        "files": inventory,
    }
    files["manifest.json"] = _json(manifest)
    return files


def _write(root: Path, files: Mapping[str, bytes]) -> None:
    root.mkdir(parents=True, exist_ok=True)
    for name, payload in sorted(files.items()):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists() or path.read_bytes() != payload:
            path.write_bytes(payload)


def _check(root: Path, files: Mapping[str, bytes]) -> bool:
    if not root.is_dir():
        return False
    actual = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*") if path.is_file()
    }
    return actual == set(files) and all((root / name).read_bytes() == data for name, data in files.items())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--check", action="store_true")
    options = parser.parse_args()
    try:
        files = build_files()
    except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError) as error:
        print(f"constructive next-layer explorer: {error}", file=sys.stderr)
        return 1
    if options.check:
        if not _check(options.output, files):
            print("constructive next-layer explorer is stale", file=sys.stderr)
            return 1
        print(f"constructive next-layer explorer: {len(files)} files, 39 checked theorems")
        return 0
    _write(options.output, files)
    print(f"constructive next-layer explorer: wrote {len(files)} files, 39 checked theorems")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
