"""Predeclared, lineage-audited Hydra development goals, never a sealed test.

The generators below are authored after seeing the historical four-goal smoke
test.  Their numerical variants are deliberately kept in whole families, and
their declared catalog derivations join the complete undirected theorem-DAG
components.  A large contaminated component is reported, not cut into more
favorable apparent holdouts.  Canonical equality is only a bounded syntactic
alias check: this module does not decide semantic equivalence or novelty.

Construction reads no preparation rows and contains no proof scripts.  An
audit first reconstructs this complete manifest, then authenticates a bounded
preparation and inspects all of its exposed roots and closed goal targets.
Neither operation imports a model framework or replays the training corpus.
"""

from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from training.peano_hydra.curriculum import _lineage_index
from training.peano_hydra.epoch import HydraEpoch, freeze_epoch
from training.peano_hydra.protocol import development_profile, validate_statement
from training.peano_policy.contract import MODEL_V3_HELD_OUT_POLICY_GOALS
from training.peano_policy.prompt import PEANO_PROMPT_V1, ProofExample, parse_prompt
from training.peano_policy.search import state_sha256


BENCHMARK_SCHEMA = "peano-hydra-development-benchmark-v1"
AUDIT_SCHEMA = "peano-hydra-development-lineage-audit-v1"
BENCHMARK_VERSION = "bounded-public-dev-68-v1"
MAX_BENCHMARK_BYTES = 24 * 1_024 * 1_024
MAX_ROW_STATEMENT_BYTES = 4_096
MAX_RENDERED_GOAL_BYTES = 16_384
MAX_ROW_GOALS = 64
MAX_AUDIT_NUMERAL = 128
# Native lexing consumes a leading decimal run even before an invalid alphabetic
# suffix.  A trailing word boundary would dangerously miss ``999999bad``.
_NUMBER = re.compile(r"(?<![A-Za-z_0-9'])[0-9]+")
_AUTHORSHIP = "hydra-development-agent-after-historical-alpha-smoke"

# These are pre-outcome generator/derivation declarations, not classifications
# inferred from whichever rows a later preparation happens to contain.
_FAMILIES: tuple[dict[str, Any], ...] = (
    {
        "id": "closed_arithmetic",
        "stratum": "ground_arithmetic",
        "description": "Small closed addition/multiplication expressions.",
        "derivation_root": "arithmetic-normalization-dev-v1",
        "catalog_anchors": ("zero_add", "add_comm", "mul_zero_left"),
        "historical_names": ("closed_arithmetic_seven",),
        "template": "(a + b) * 2 + c = 2 * (a + b) + c; bounded decimal a,b,c",
    },
    {
        "id": "arithmetic_witnesses",
        "stratum": "closed_existential_witness",
        "description": "A small additive witness, not a supplied witness tactic.",
        "derivation_root": "additive-witness-dev-v1",
        "catalog_anchors": ("zero_add", "add_comm", "le_refl"),
        "historical_names": ("existential_subtraction_two",),
        "template": "exists x. x + offset = total; bounded offset,total",
    },
    {
        "id": "implication_transport",
        "stratum": "quantified_implication",
        "description": "Transport equality through addition under a hypothesis.",
        "derivation_root": "equality-context-logic-dev-v1",
        "catalog_anchors": ("eq_symm", "eq_trans", "add_congr"),
        "historical_names": (),
        "template": "forall n m. n = m -> offset + n = offset + m",
    },
    {
        "id": "conjunction_transport",
        "stratum": "quantified_conjunction",
        "description": "Reorder a conjunction and reverse an equality.",
        "derivation_root": "equality-context-logic-dev-v1",
        "catalog_anchors": ("eq_symm", "eq_trans"),
        "historical_names": (),
        "template": "forall n m. (n = m /\\ k = k) -> (k = k /\\ m = n)",
    },
    {
        "id": "disjunction_transport",
        "stratum": "quantified_disjunction",
        "description": "Introduce a disjunction from a supplied equality hypothesis.",
        "derivation_root": "equality-context-logic-dev-v1",
        "catalog_anchors": ("eq_symm", "eq_trans"),
        "historical_names": (),
        "template": "forall n. n = k -> (n = k \\/ n = k + 1)",
    },
    {
        "id": "universal_equalities",
        "stratum": "quantified_normalization",
        "description": "Normalize a right-zero context around an open sum.",
        "derivation_root": "right-zero-normalization-dev-v1",
        "catalog_anchors": ("zero_add", "add_assoc", "add_comm"),
        "historical_names": ("double_right_zero",),
        "template": "forall n. (n + k) + 0 = n + k",
    },
    {
        "id": "inductive_arithmetic",
        "stratum": "induction_or_algebra",
        "description": "Distributive arithmetic; induction is allowed, not prescribed.",
        "derivation_root": "inductive-polynomial-dev-v1",
        "catalog_anchors": ("mul_add", "mul_comm", "add_assoc"),
        "historical_names": ("consecutive_product_even",),
        "template": "forall n. (n + k) * 2 = n * 2 + 2*k",
    },
    {
        "id": "existential_composition",
        "stratum": "quantified_witness_composition",
        "description": "A variable-dependent witness with a conjunctive consequence.",
        "derivation_root": "composed-additive-witness-dev-v1",
        "catalog_anchors": ("add_comm", "add_assoc", "le_trans"),
        "historical_names": (),
        "template": "forall n. exists x. (x = n + k /\\ x + 1 = n + (k+1))",
    },
)


class HydraBenchmarkError(ValueError):
    """A development benchmark or an exposed preparation lost its boundaries."""


def _canonical(value: object) -> bytes:
    try:
        return json.dumps(
            value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    except (TypeError, ValueError, RecursionError) as error:
        raise HydraBenchmarkError(f"development evidence is not strict JSON: {error}") from None


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _sources(family: str) -> tuple[str, ...]:
    result: list[str] = []
    for seed in range(8):
        k = seed + 1
        if family == "closed_arithmetic":
            a, b, c = seed % 4 + 1, (seed // 2) % 3 + 1, seed % 3
            result.append(f"({a} + {b}) * 2 + {c} = {2 * (a + b) + c}")
        elif family == "arithmetic_witnesses":
            offset, total = seed % 3 + 1, k + seed % 3 + 1
            result.append(f"exists x. x + {offset} = {total}")
        elif family == "implication_transport":
            result.append(f"forall n m. n = m -> {k} + n = {k} + m")
        elif family == "conjunction_transport":
            result.append(f"forall n m. (n = m /\\ {k} = {k}) -> ({k} = {k} /\\ m = n)")
        elif family == "disjunction_transport":
            result.append(f"forall n. n = {k} -> (n = {k} \\/ n = {k + 1})")
        elif family == "universal_equalities":
            result.append(f"forall n. (n + {k}) + 0 = n + {k}")
        elif family == "inductive_arithmetic":
            result.append(f"forall n. (n + {k}) * 2 = n * 2 + {2 * k}")
        elif family == "existential_composition":
            result.append(f"forall n. exists x. (x = n + {k} /\\ x + 1 = n + {k + 1})")
        else:
            raise HydraBenchmarkError("undeclared development generator")
    return tuple(result)


class _Components:
    def __init__(self) -> None:
        self.parent: dict[str, str] = {}
        self.edges: set[tuple[str, str, str]] = set()

    def find(self, name: str) -> str:
        self.parent.setdefault(name, name)
        current = name
        while self.parent[current] != current:
            current = self.parent[current]
        while self.parent[name] != name:
            following = self.parent[name]
            self.parent[name] = current
            name = following
        return current

    def join(self, left: str, right: str, relation: str) -> None:
        self.edges.add((left, right, relation))
        a, b = self.find(left), self.find(right)
        if a != b:
            self.parent[max(a, b)] = min(a, b)

    def groups(self) -> dict[str, list[str]]:
        result: dict[str, list[str]] = defaultdict(list)
        for name in sorted(self.parent):
            result[self.find(name)].append(name)
        return dict(result)


def _descendants(epoch: HydraEpoch, roots: set[str]) -> set[str]:
    reverse: dict[str, set[str]] = {item.name: set() for item in epoch.theorems}
    for item in epoch.theorems:
        for dependency in item.dependencies:
            reverse[dependency].add(item.name)
    result = set(roots)
    pending = list(roots)
    while pending:
        current = pending.pop()
        for child in reverse[current] - result:
            result.add(child)
            pending.append(child)
    return result


def build_development_benchmark(epoch: HydraEpoch) -> dict[str, object]:
    """Build all 68 goals and every declared relation before observing rows.

    Eight families each contain eight correlated seeds.  Four previously
    reported diagnostics are separate records and join their declared family;
    none is relabeled as a new independent benchmark observation.
    """

    if type(epoch) is not HydraEpoch:
        raise TypeError("development benchmarks require one exact HydraEpoch")
    names = {item.name for item in epoch.theorems}
    if len(names) != len(epoch.theorems) or any(
        set(item.dependencies) - names for item in epoch.theorems
    ):
        raise HydraBenchmarkError("frozen theorem DAG has duplicate or dangling members")
    profile = development_profile()
    graph = _Components()
    for item in epoch.theorems:
        graph.find(f"catalog:{item.name}")
        for dependency in item.dependencies:
            graph.join(f"catalog:{item.name}", f"catalog:{dependency}", "checked_dependency")

    family_records: list[dict[str, object]] = []
    goals: list[dict[str, object]] = []
    historical_family: dict[str, dict[str, object]] = {}
    for declared in _FAMILIES:
        family = declared["id"]
        sources = _sources(family)
        generator = f"{BENCHMARK_VERSION}:{family}"
        declaration: dict[str, object] = {
            **declared,
            "catalog_anchors": list(declared["catalog_anchors"]),
            "historical_names": list(declared["historical_names"]),
            "generator_id": generator,
            "generator_seeds": list(range(8)),
            "authorship": _AUTHORSHIP,
            "expanded_goal_count": len(sources),
            "anchor_policy": "exact declared catalog names and their whole dependency components",
            "missing_catalog_anchors": sorted(set(declared["catalog_anchors"]) - names),
        }
        declaration["generator_sha256"] = _digest({"declaration": declaration, "sources": sources})
        family_records.append(declaration)
        graph.join(f"family:{family}", f"generator:{generator}", "shared_generator")
        graph.join(f"family:{family}", f"derivation:{declared['derivation_root']}", "authored_derivation")
        for anchor in declared["catalog_anchors"]:
            if anchor in names:
                graph.join(f"family:{family}", f"catalog:{anchor}", "declared_catalog_derivation")
        for seed, source in enumerate(sources):
            goal_id = f"dev_{family}_{seed:02d}"
            canonical = validate_statement(source)
            statement_sha256 = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
            goals.append(
                {
                    "id": goal_id,
                    "name": goal_id,
                    "source": source,
                    "canonical": canonical,
                    "statement": canonical,
                    "statement_sha256": statement_sha256,
                    "kind": "expanded_development",
                    "cohort": "expanded",
                    "family": family,
                    "stratum": declared["stratum"],
                    "generator_id": generator,
                    "generator_seed": seed,
                    "authorship": _AUTHORSHIP,
                    "derivation_root": declared["derivation_root"],
                    "profile_sha256": profile["profile_sha256"],
                    "historical_derivation_names": list(declared["historical_names"]),
                    "independent_of_other_family_seeds": False,
                }
            )
            graph.join(f"goal:{goal_id}", f"family:{family}", "family_member")
            graph.join(f"goal:{goal_id}", f"seed:{generator}:{seed}", "generator_seed")
            graph.join(f"goal:{goal_id}", f"canonical:{statement_sha256}", "canonical_alias")
        for name in declared["historical_names"]:
            historical_family[name] = declared

    for name, source in MODEL_V3_HELD_OUT_POLICY_GOALS:
        declared = historical_family[name]
        canonical = validate_statement(source)
        statement_sha256 = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        goals.append(
            {
                "id": name,
                "name": name,
                "source": source,
                "canonical": canonical,
                "statement": canonical,
                "statement_sha256": statement_sha256,
                "kind": "historical_diagnostic",
                "cohort": "historical",
                "family": declared["id"],
                "stratum": "historical_four_goal_smoke",
                "generator_id": "historical-model-v3-four-goal-contract",
                "generator_seed": None,
                "authorship": "historical-public-policy-diagnostic",
                "derivation_root": declared["derivation_root"],
                "profile_sha256": profile["profile_sha256"],
                "historical_derivation_names": [name],
                "independent_of_other_family_seeds": False,
            }
        )
        graph.join(f"goal:{name}", f"family:{declared['id']}", "historical_family_derivation")
        graph.join(
            f"goal:{name}",
            "generator:historical-model-v3-four-goal-contract",
            "shared_historical_contract",
        )
        graph.join(f"goal:{name}", f"canonical:{statement_sha256}", "canonical_alias")

    canonical_aliases: dict[str, list[str]] = defaultdict(list)
    uncertain: list[str] = []
    catalog_canonical: dict[str, str] = {}
    for item in epoch.theorems:
        try:
            # The profile performs lexical/resource rejection before parsing.
            canonical = validate_statement(item.statement)
        except (ValueError, TypeError, RecursionError):
            uncertain.append(item.name)
            continue
        catalog_canonical[item.name] = canonical
        statement_sha256 = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        canonical_aliases[statement_sha256].append(item.name)
        graph.join(f"catalog:{item.name}", f"canonical:{statement_sha256}", "canonical_alias")

    groups = graph.groups()
    node_component: dict[str, str] = {}
    component_records: list[dict[str, object]] = []
    theorem_lineages = _lineage_index(epoch)
    for members in sorted(groups.values()):
        component_id = _digest({"kind": "declared-development-lineage", "members": members})
        node_component.update((member, component_id) for member in members)
        goal_ids = [member.removeprefix("goal:") for member in members if member.startswith("goal:")]
        if not goal_ids:
            continue
        catalog_members = [member.removeprefix("catalog:") for member in members if member.startswith("catalog:")]
        component_records.append(
            {
                "id": component_id,
                "goal_ids": goal_ids,
                "families": [member.removeprefix("family:") for member in members if member.startswith("family:")],
                "catalog_members": catalog_members,
                "catalog_lineage_sha256s": sorted({theorem_lineages[name] for name in catalog_members}),
                "member_count": len(members),
                "members_sha256": _digest(members),
            }
        )
    by_component = {record["id"]: record for record in component_records}
    uncertain_mask = _descendants(epoch, set(uncertain))
    for goal in goals:
        component_id = node_component[f"goal:{goal['id']}"]
        aliases = sorted(canonical_aliases[goal["statement_sha256"]])
        descendants = _descendants(epoch, set(aliases))
        members = set(by_component[component_id]["catalog_members"])
        masked = sorted(members | descendants | uncertain_mask)
        goal.update(
            {
                "component_id": component_id,
                "frozen_catalog_aliases": aliases,
                "target_alias_descendants": sorted(descendants),
                "masked_theorems": masked,
                "mask_sha256": _digest(masked),
                "allowed_theorems": [],
                "retrieval_allowed_theorems": [],
                "theorem_authority": "no-imports-no-retrieval",
            }
        )
    for family in family_records:
        family["component_id"] = node_component[f"family:{family['id']}"]

    result: dict[str, object] = {
        "schema": BENCHMARK_SCHEMA,
        "version": BENCHMARK_VERSION,
        "epoch_sha256": epoch.epoch_sha256,
        "edition_identity_sha256": epoch.edition_identity_sha256,
        "theorem_dag_sha256": epoch.theorem_dag_sha256,
        "reviewed_definition_dag_sha256": epoch.reviewed_definition_dag_sha256,
        "profile": profile,
        "profile_sha256": profile["profile_sha256"],
        "goal_count": len(goals),
        "expanded_goal_count": 64,
        "historical_goal_count": 4,
        "declared_family_count": len(family_records),
        "declared_connected_component_count": len(component_records),
        "families": family_records,
        "goals": goals,
        "components": component_records,
        "lineage_relations": sorted({edge[2] for edge in graph.edges}),
        "lineage_graph_sha256": _digest(sorted(graph.edges)),
        "lineage_graph_edge_count": len(graph.edges),
        "catalog_alias_audit": {
            "checked_theorems": len(catalog_canonical),
            "unresolved_theorems": sorted(uncertain),
            "unresolved_theorem_count": len(uncertain),
            "all_catalog_canonical_aliases_checked": not uncertain,
            "unresolved_theorems_and_descendants_masked": True,
            "canonicalization_profile_sha256": profile["profile_sha256"],
        },
        "construction": {
            "preparation_rows_read": 0,
            "outcomes_read": 0,
            "proof_scripts_supplied": False,
            "authors_knew_historical_smoke_outcomes": True,
            "authors_knew_catalog_families": True,
            "historical_variants_are_independent": False,
            "declared_relations_frozen_before_row_exposure": True,
        },
        "development_only": True,
        "sealed_benchmark": False,
        "research_claim_eligible": False,
        "semantic_equivalence_complete": False,
        "eligible_for_unseen_model_comparison": False,
        "claim_boundary": (
            "Public, post-historical-outcome DEV diagnostics. Numerical seeds are correlated; "
            "declared lineage components, not goals, are the isolation units. Canonical aliases "
            "and declared derivations do not establish semantic novelty, complete semantic "
            "separation, theoremhood, non-theoremhood, a sealed H1 benchmark, or model advantage."
        ),
    }
    result["manifest_sha256"] = _digest(result)
    if len(_canonical(result)) > MAX_BENCHMARK_BYTES:
        raise HydraBenchmarkError("development benchmark exceeds its complete evidence byte bound")
    return result


def validate_benchmark(benchmark: object, epoch: HydraEpoch) -> dict[str, object]:
    """Authenticate generators, profile, complete graph and masks, not just a hash."""

    if type(benchmark) is not dict:
        raise HydraBenchmarkError("development benchmark must be one manifest object")
    raw = _canonical(benchmark)
    if len(raw) > MAX_BENCHMARK_BYTES:
        raise HydraBenchmarkError("development benchmark exceeds its complete evidence byte bound")
    expected = build_development_benchmark(epoch)
    if raw != _canonical(expected):
        raise HydraBenchmarkError("development benchmark differs from its complete predeclared epoch manifest")
    return expected


def _guard_parser_input(source: object, *, maximum: int, field: str) -> str:
    if type(source) is not str or not source or len(source.encode("utf-8")) > maximum:
        raise HydraBenchmarkError(f"{field} exceeds its bounded text authority")
    if any(character.isdigit() and not character.isascii() for character in source):
        raise HydraBenchmarkError(f"{field} contains a resource-dangerous non-ASCII numeral")
    numerals = _NUMBER.findall(source)
    if any(len(item) > 3 or int(item) > MAX_AUDIT_NUMERAL for item in numerals):
        raise HydraBenchmarkError(f"{field} contains a resource-dangerous numeral")
    if source.count("(") > 256 or len(source.split()) > 2_048:
        raise HydraBenchmarkError(f"{field} exceeds its bounded parser work")
    return source


def audit_preparation(
    benchmark: dict[str, object],
    preparation_dir: Path,
    *,
    epoch: HydraEpoch | None = None,
) -> dict[str, object]:
    """Authenticate one preparation and conservatively audit every DEV component.

    A ``safe_under_declared_relations`` component has no detected exposure under
    the declared graph.  It still is not certified semantically unseen. Unknown
    non-catalog roots without authenticated derivation preimages block all
    components instead of being guessed independent.
    """

    frozen = freeze_epoch() if epoch is None else epoch
    trusted = validate_benchmark(benchmark, frozen)  # Must precede any row exposure.
    from training.peano_hydra import evaluation

    try:
        directory, manifest, manifest_sha256, rows = evaluation._load_preparation(preparation_dir)
        for field, expected in (
            ("epoch_sha256", frozen.epoch_sha256),
            ("edition_identity_sha256", frozen.edition_identity_sha256),
            ("theorem_dag_sha256", frozen.theorem_dag_sha256),
            ("reviewed_definition_dag_sha256", frozen.reviewed_definition_dag_sha256),
            ("surface_label", frozen.surface_label),
            ("version", frozen.version),
            ("research_claim_eligible", False),
            ("sealed_benchmark", False),
            ("alpha_admitted", False),
            ("model_trained", False),
        ):
            if manifest.get(field) != expected or type(manifest.get(field)) is not type(expected):
                raise HydraBenchmarkError(f"preparation changed its frozen {field}")
        evaluation._model_record(manifest.get("model"))
        evaluation._validated_preparation_config(frozen, directory, manifest)
        catalog = {item.name: item for item in frozen.theorems}
        for split in ("train", "dev"):
            for row in rows[f"{split}.jsonl"]:
                transition = row.get("transition")
                if type(transition) is not dict:
                    raise HydraBenchmarkError("exposed row has no checked transition identity")
                _guard_parser_input(transition.get("theorem"), maximum=MAX_ROW_STATEMENT_BYTES, field="training theorem")
                enrolled = catalog.get(row.get("theorem_name"))
                if enrolled is not None:
                    _guard_parser_input(enrolled.statement, maximum=MAX_ROW_STATEMENT_BYTES, field="enrolled training theorem")
                parsed = parse_prompt(row.get("prompt"))
                if parsed.classical is not False or parsed.prompt_version != PEANO_PROMPT_V1:
                    raise HydraBenchmarkError("exposed prompt escaped its intuitionistic Alpha protocol")
                if (
                    row.get("state_sha256") != state_sha256(parsed.goals)
                    or transition.get("focus") != parsed.focus
                ):
                    raise HydraBenchmarkError("exposed prompt changed its exact state/focus identity")
                for field in ("goals_before", "goals_after"):
                    goals = transition.get(field)
                    if type(goals) is not list or len(goals) > MAX_ROW_GOALS:
                        raise HydraBenchmarkError("exposed row exceeds its complete goal inventory bound")
                    for goal in goals:
                        text = _guard_parser_input(goal, maximum=MAX_RENDERED_GOAL_BYTES, field="exposed goal")
                        _, marker, target = text.rpartition("⊢")
                        if not marker:
                            raise HydraBenchmarkError("exposed goal lost its target turnstile")
                        _guard_parser_input(target.strip(), maximum=MAX_ROW_STATEMENT_BYTES, field="exposed goal target")
        preference_exposure: list[dict[str, object]] = []
        catalog_lineages = _lineage_index(frozen)
        for row in rows["preferences.jsonl"]:
            name = row.get("theorem_name")
            source = _guard_parser_input(row.get("theorem"), maximum=MAX_ROW_STATEMENT_BYTES, field="preference theorem")
            canonical = evaluation._canonical_formula(source)
            if type(name) is not str or not name:
                raise HydraBenchmarkError("preference has no exact theorem root")
            enrolled = catalog.get(name)
            if enrolled is not None:
                source = _guard_parser_input(enrolled.statement, maximum=MAX_ROW_STATEMENT_BYTES, field="enrolled preference theorem")
                if (
                    canonical != evaluation._canonical_formula(source)
                    or row.get("lineage_sha256") != catalog_lineages[name]
                ):
                    raise HydraBenchmarkError("preference changed its exact catalog root or lineage")
            parsed = parse_prompt(row.get("prompt"))
            if (
                row.get("schema") != "peano-hydra-verified-preference-v1"
                or parsed.classical is not False
                or parsed.surface != frozen.surface_label
                or parsed.prompt_version != PEANO_PROMPT_V1
                or state_sha256(parsed.goals) != row.get("state_sha256")
            ):
                raise HydraBenchmarkError("preference changed its declared Alpha prompt authority")
            for completion in ("chosen", "rejected"):
                ProofExample(
                    example_id=f"hydra-dev-audit:{name}:{completion}",
                    prompt=row["prompt"],
                    completion=row.get(completion),
                    environment_sha256=parsed.environment_sha256,
                )
            closed_targets: list[str] = []
            if len(parsed.goals) > MAX_ROW_GOALS:
                raise HydraBenchmarkError("preference exceeds its complete goal inventory bound")
            for rendered in parsed.goals:
                text = _guard_parser_input(rendered, maximum=MAX_RENDERED_GOAL_BYTES, field="preference goal")
                _, marker, target = text.rpartition("⊢")
                if not marker:
                    raise HydraBenchmarkError("preference goal lost its target turnstile")
                _guard_parser_input(target.strip(), maximum=MAX_ROW_STATEMENT_BYTES, field="preference goal target")
                canonical_target = evaluation._canonical_goal_target(text)
                if canonical_target is not None:
                    closed_targets.append(canonical_target)
            preference_exposure.append(
                {"name": name, "canonical": canonical, "lineage": row["lineage_sha256"], "closed_targets": closed_targets}
            )
        historical = tuple(goal for goal in trusted["goals"] if goal["cohort"] == "historical")
        historical_audit = evaluation._verify_holdout(manifest, rows, epoch=frozen, goals=historical)
    except HydraBenchmarkError:
        raise
    except (ValueError, TypeError, KeyError) as error:
        raise HydraBenchmarkError(f"preparation authentication failed: {error}") from error

    exposure: dict[str, dict[str, set[str]]] = {
        split: {"roots": set(), "lineages": set(), "formulas": set(), "goal_formulas": set()}
        for split in ("train", "dev")
    }
    unresolved_roots: set[str] = set()
    for split in ("train", "dev"):
        for row in rows[f"{split}.jsonl"]:
            transition = row["transition"]
            name = row["theorem_name"]
            canonical = evaluation._canonical_formula(transition["theorem"])
            exposure[split]["roots"].add(name)
            exposure[split]["lineages"].add(row["lineage_sha256"])
            exposure[split]["formulas"].add(canonical)
            if name not in catalog:
                # Existing v1 prompts bind an environment digest but do not
                # expose the dependency preimage needed for broader derivation
                # authentication.  Never turn its hash into an unseen claim.
                unresolved_roots.add(name)
            for field in ("goals_before", "goals_after"):
                for rendered in transition[field]:
                    target = evaluation._canonical_goal_target(rendered)
                    if target is not None:
                        exposure[split]["goal_formulas"].add(target)
    for row in preference_exposure:
        exposure["train"]["roots"].add(row["name"])
        exposure["train"]["lineages"].add(row["lineage"])
        exposure["train"]["formulas"].add(row["canonical"])
        exposure["train"]["goal_formulas"].update(row["closed_targets"])
        if row["name"] not in catalog:
            unresolved_roots.add(row["name"])

    component_results: list[dict[str, object]] = []
    goal_by_id = {goal["id"]: goal for goal in trusted["goals"]}
    for component in trusted["components"]:
        members = set(component["catalog_members"])
        lineages = set(component["catalog_lineage_sha256s"])
        formulas = {goal_by_id[name]["canonical"] for name in component["goal_ids"]}
        split_overlap: dict[str, object] = {}
        reasons: list[str] = []
        for split in ("train", "dev"):
            declared_roots = sorted(members & exposure[split]["roots"])
            component_overlap = sorted(lineages & exposure[split]["lineages"])
            theorem_aliases = sorted(formulas & exposure[split]["formulas"])
            goal_aliases = sorted(formulas & exposure[split]["goal_formulas"])
            split_overlap[split] = {
                "catalog_roots": declared_roots,
                "catalog_lineages": component_overlap,
                "canonical_theorem_aliases": theorem_aliases,
                "canonical_closed_goal_aliases": goal_aliases,
            }
            if declared_roots or component_overlap or theorem_aliases or goal_aliases:
                reasons.append(f"{split}_exposes_declared_component")
        if unresolved_roots:
            reasons.append("uncataloged_exposure_derivation_preimages_unavailable")
        component_results.append(
            {
                "component_id": component["id"],
                "families": component["families"],
                "goal_ids": component["goal_ids"],
                "catalog_member_count": len(members),
                "status": "blocked" if reasons else "safe_under_declared_relations",
                "reasons": reasons,
                "exposure": split_overlap,
                "eligible_for_unseen_model_comparison": False,
            }
        )
    by_id = {record["component_id"]: record for record in component_results}
    families = [
        {
            "family": family["id"],
            "component_id": family["component_id"],
            "status": by_id[family["component_id"]]["status"],
            "reasons": by_id[family["component_id"]]["reasons"],
            "eligible_for_unseen_model_comparison": False,
        }
        for family in trusted["families"]
    ]
    counts = Counter(row["status"] for row in families)
    result: dict[str, object] = {
        "schema": AUDIT_SCHEMA,
        "benchmark_manifest_sha256": trusted["manifest_sha256"],
        "epoch_sha256": frozen.epoch_sha256,
        "profile_sha256": trusted["profile_sha256"],
        "preparation_manifest_sha256": manifest_sha256,
        "preparation_run_id": manifest.get("run_id"),
        "authenticated_files": manifest["files"],
        "exposed_rows": {split: len(rows[f"{split}.jsonl"]) for split in ("train", "dev")},
        "exposed_theorem_roots": {split: sorted(exposure[split]["roots"]) for split in ("train", "dev")},
        "preferences_authenticated_under_training_lineages": len(rows["preferences.jsonl"]),
        "historical_contract_audit": historical_audit,
        "components": component_results,
        "families": families,
        "blocked_family_count": counts["blocked"],
        "safe_under_declared_relations_family_count": counts["safe_under_declared_relations"],
        "unresolved_uncataloged_exposure_roots": sorted(unresolved_roots),
        "declared_relations_frozen_before_row_exposure": True,
        "declared_file_hashes_authenticated": True,
        "declared_catalog_row_lineages_authenticated": True,
        "training_corpus_independently_replayed_in_this_audit": False,
        "open_goal_semantic_closures_checked": False,
        "semantic_equivalence_complete": False,
        "eligible_for_unseen_model_comparison": False,
        "sealed_benchmark": False,
        "research_claim_eligible": False,
        "status": "blocked" if counts["blocked"] else "safe_under_declared_relations_only",
        "claim_boundary": (
            "Authenticated preparation bytes and declared whole-component exposure only; "
            "not a new proof replay, complete semantic-equivalence audit, unseen-model "
            "benchmark, sealed H1 test, or permission to train on these DEV goals."
        ),
    }
    result["audit_sha256"] = _digest(result)
    return result
