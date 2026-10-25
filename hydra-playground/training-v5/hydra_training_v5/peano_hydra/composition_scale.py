"""A separate, bounded structural native-teacher corpus, never an unseen test.

The inventory is authored before replay and uses no theorem imports, models,
solver calls, admission, or subprocesses.  The old 32-route pilot is unchanged.
All publication and verification regenerates every original-goal native QED;
the compact evidence stores trace hashes, while SFT retains complete states.
Run a complete stage inside the caller's explicitly bounded CPU worker.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import re
import tempfile
from typing import TYPE_CHECKING

from peano_lab.batch import run_proof
from hydra_training_v5.peano_hydra import composition as pilot
from hydra_training_v5.peano_hydra.curriculum import VerifiedCurriculum, encode_jsonl
from hydra_training_v5.peano_hydra.epoch import HydraEpoch, freeze_epoch
from hydra_training_v5.peano_hydra.protocol import validate_statement
from hydra_training_v5.peano_policy.contract import MODEL_V3_HELD_OUT_POLICY_GOALS

if TYPE_CHECKING:
    from hydra_training_v5.peano_hydra.posttrain import VerifiedSource


ROOT = Path(__file__).resolve().parents[2]
SCALED_COMPOSITION_SCHEMA = "peano-hydra-native-composition-scale-source-v1"
SCALED_COMPOSITION_PLAN_SCHEMA = "peano-hydra-native-composition-scale-plan-v1"
COMPOSITION_PROFILE = pilot.COMPOSITION_PROFILE
SOURCE_FILENAMES = pilot.SOURCE_FILENAMES
MAX_ROUTES = 1024
MAX_ROUTE_DECISIONS = 24
MAX_TOTAL_DECISIONS = 12_288
MAX_NUMERAL = 16
MAX_ROUTE_TRACE_BYTES = pilot.MAX_ROUTE_TRACE_BYTES
MAX_SOURCE_FILE_BYTES = pilot.MAX_SOURCE_FILE_BYTES
MAX_SOURCE_TOTAL_BYTES = pilot.MAX_SOURCE_TOTAL_BYTES
_AUTHORSHIP = "explicit-structural-teachers-authored-after-public-capacity-results"
_NUMBER = re.compile(r"(?<![A-Za-z_0-9'])[0-9]+")
_VARIANTS = tuple((depth, shape, numeral) for depth in (1, 2, 3)
                  for shape in range(4) for numeral in (1, 2, 3, 4))
_FAMILIES = (
    ("equality_path", "train", "Compose two to four assumed equalities inside a term tree."),
    ("equality_reverse_path", "train", "Reverse a contextual equality obtained from a finite path."),
    ("congruence_pair", "train", "Transport one equality through two different term trees."),
    ("conjunction_swap", "train", "Reorder and reverse two assumed equalities."),
    ("conjunction_associate", "train", "Destructure and reassociate three conjuncts."),
    ("closed_arithmetic_composition", "train", "Compute three small closed arithmetic claims in one conjunction."),
    ("implication_compose", "train", "Compose two nontrivial implication hypotheses."),
    ("implication_pair", "train", "Apply two implications to construct a conjunction."),
    ("numeric_witness_composition", "train", "Choose two small literal witnesses and check three arithmetic properties."),
    ("disjunction_swap", "train", "Eliminate a disjunction and reintroduce its reversed form."),
    ("disjunction_map", "train", "Eliminate both branches using independently supplied maps."),
    ("universal_specialization", "train", "Specialize one universal premise at two distinct variables."),
    ("universal_composition", "train", "Compose two universally quantified implications."),
    ("existential_transport", "train", "Construct a term witness and transport its second property."),
    ("existential_unpack", "train", "Eliminate an existential and rebuild a reordered witness package."),
    ("nested_existentials", "train", "Choose three dependent term witnesses and prove four properties."),
    ("inductive_nested_zero", "train", "Prove a local left-zero lemma by induction and reuse it twice."),
    ("inductive_add_mul_zero", "train", "Prove two local inductive lemmas and combine their consequences."),
    ("inductive_distribution", "train", "Prove successor addition by induction and transport distributivity."),
    ("contradiction_elimination", "dev", "Exposed whole-family diagnostic: eliminate an explicit contradiction."),
    ("guarded_projection", "dev", "Exposed whole-family diagnostic: project a guarded nested conjunction."),
)


class HydraScaledCompositionError(ValueError):
    """A scaled teacher source escaped its fixed proof or resource boundary."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise HydraScaledCompositionError(message)


def _context(variable: str, depth: int, shape: int, numeral: int) -> str:
    terms = (f"({variable} + {numeral})", f"({numeral} + {variable})",
             f"({variable} * {numeral + 1})", f"({variable} + ({variable} * {numeral + 1}))")
    term = terms[shape]
    for _ in range(depth):
        term = f"S ({term})"
    return term


def _arithmetic_context(variable: str, depth: int, shape: int, numeral: int) -> str:
    # Multiplication-rich outer contexts can make simplification certificates
    # disproportionately large. Inductive teachers use shallow additive trees;
    # logical teachers still exercise all four richer arithmetic contexts.
    terms = (f"(({variable}) + {numeral})", f"((({variable}) + 0) + {numeral})",
             f"((({variable}) + {numeral}) + 0)", f"((({variable}) + 0) + ({numeral} + 0))")
    term = terms[shape]
    for _ in range(depth):
        term = f"S ({term})"
    return term


def _small_sum(left: str, right: str, shape: int) -> str:
    return (f"(({left}) + ({right}))", f"((({left}) + 0) + ({right}))",
            f"(({left}) + (({right}) + 0))", f"((({left}) + 0) + (({right}) + 0))")[shape]


def _route(family: str, depth: int, shape: int, numeral: int) -> tuple[str, tuple[str, ...]]:
    context = _arithmetic_context if family.startswith("inductive_") else _context
    def c(variable: str) -> str:
        return context(variable, depth, shape, numeral)
    def d(variable: str) -> str:
        return context(variable, depth, (shape + 1) % 4, numeral)
    def rewrite(name: str, term_shape: int = shape) -> tuple[str, ...]:
        # Native rewrite changes one occurrence. The fourth rich context has
        # two occurrences, so both explicit primitive decisions are recorded.
        return (f"rewrite {name}",) * (2 if term_shape == 3 else 1)
    a, b, e = "n = m", f"{c('n')} = {c('m')}", f"{d('m')} = {d('p')}"
    intro2 = ("intro n", "intro m")
    intro3 = (*intro2, "intro p")
    if family in {"equality_path", "equality_reverse_path"}:
        variables = tuple(f"x{i}" for i in range(depth + 2))
        premises = tuple(f"{variables[i]} = {variables[i + 1]}" for i in range(depth + 1))
        target = f"{c(variables[0])} = {c(variables[-1])}"
        reverse = family == "equality_reverse_path"
        if reverse:
            target = f"{c(variables[-1])} = {c(variables[0])}"
        commands = (tuple(f"intro {name}" for name in variables)
                    + tuple(f"intro h{i}" for i in range(len(premises)))
                    + (("symm",) if reverse else ())
                    + tuple(command for i in range(len(premises)) for command in rewrite(f"h{i}")) + ("refl",))
        return f"forall {' '.join(variables)}. {' -> '.join((*premises, target))}", commands
    if family == "congruence_pair":
        return (f"forall n m. {a} -> ({b} /\\ {d('n')} = {d('m')})",
                (*intro2, "intro h", "split", *rewrite("h"), "refl", *rewrite("h", (shape + 1) % 4), "refl"))
    if family == "conjunction_swap":
        return (f"forall n m. ({a} /\\ {b}) -> ({c('m')} = {c('n')} /\\ m = n)",
                (*intro2, "intro h", "cases h", "split", "symm", "assumption", "symm", "assumption"))
    if family == "conjunction_associate":
        return (f"forall n m p. ({a} /\\ ({b} /\\ {e})) -> ({e} /\\ ({a} /\\ {b}))",
                (*intro3, "intro h", "cases h", "cases h_right", "split", "assumption",
                 "split", "assumption", "assumption"))
    if family == "closed_arithmetic_composition":
        first = _small_sum(str(numeral), str(depth), shape)
        second = _small_sum(f"{numeral} * 2", str(depth), shape)
        third = _small_sum(f"{numeral} * ({depth} + 1)", "0", shape)
        return (f"({first} = {numeral + depth} /\\ ({second} = {2 * numeral + depth} /\\ {third} = {numeral * (depth + 1)}))",
                ("split", "norm_num", "split", "norm_num", "norm_num"))
    if family == "implication_compose":
        return (f"forall n m p. ({a} -> {b}) -> ({b} -> {e}) -> {a} -> {e}",
                (*intro3, "intro f", "intro g", "intro h", "apply g", "apply f", "exact h"))
    if family == "implication_pair":
        return (f"forall n m p. ({a} -> {b}) -> ({a} -> {e}) -> {a} -> ({b} /\\ {e})",
                (*intro3, "intro f", "intro g", "intro h", "split", "apply f", "exact h", "apply g", "exact h"))
    if family == "numeric_witness_composition":
        first = _small_sum("x", str(numeral), shape)
        second = _small_sum("y", str(depth), shape)
        third = _small_sum("x * y", "0", shape)
        return (f"exists x y. ({first} = {2 * numeral} /\\ ({second} = {2 * depth} /\\ {third} = {numeral * depth}))",
                (f"exists {numeral}", f"exists {depth}", "split", "norm_num", "split", "norm_num", "norm_num"))
    if family == "disjunction_swap":
        return (f"forall n m. ({a} \\/ {b}) -> ({b} \\/ {a})",
                (*intro2, "intro h", "cases h", "right", "assumption", "left", "assumption"))
    if family == "disjunction_map":
        return (f"forall n m p. ({a} -> {e}) -> ({b} -> {e}) -> ({a} \\/ {b}) -> {e}",
                (*intro3, "intro f", "intro g", "intro h", "cases h", "apply f", "assumption", "apply g", "assumption"))
    if family == "universal_specialization":
        return (f"forall n m. (forall x. {c('x')} = {d('x')}) -> ({c('n')} = {d('n')} /\\ {c('m')} = {d('m')})",
                (*intro2, "intro h", "split", "specialize h n", "exact h", "specialize h m", "exact h"))
    if family == "universal_composition":
        return (f"forall m. (forall x. x = m -> {c('x')} = {c('m')}) -> "
                f"(forall x. {c('x')} = {c('m')} -> {d('x')} = {d('m')}) -> "
                f"forall n. n = m -> {d('n')} = {d('m')}",
                ("intro m", "intro f", "intro g", "intro n", "intro h", "specialize g n",
                 "apply g", "specialize f n", "apply f", "exact h"))
    if family == "existential_transport":
        return (f"forall n m. n = m -> exists x. (x = {c('n')} /\\ x = {c('m')})",
                (*intro2, "intro h", f"exists {c('n')}", "split", "refl", *rewrite("h"), "refl"))
    if family == "existential_unpack":
        return (f"forall n. (exists x. (x = n /\\ {c('x')} = {c('n')})) -> "
                f"exists y. ({c('y')} = {c('n')} /\\ y = n)",
                ("intro n", "intro h", "cases h", "cases h_witness", "exists x", "split", "assumption", "assumption"))
    if family == "nested_existentials":
        return (f"forall n m p. exists x y z. (x = {c('n')} /\\ (y = {c('m')} /\\ "
                f"(z = {c('p')} /\\ (x + y) + z = ({c('n')} + {c('m')}) + {c('p')})))",
                (*intro3, f"exists {c('n')}", f"exists {c('m')}", f"exists {c('p')}",
                 "split", "refl", "split", "refl", "split", "refl", "refl"))
    zero_add = ("have hz : forall a. 0 + a = a", "intro a", "induction a", "simp", "simp [IH]")
    zero_mul = ("have hm : forall a. 0 * a = 0", "intro a", "induction a", "simp", "simp [IH]")
    if family == "inductive_nested_zero":
        term = "n"
        for _ in range(depth + 1):
            term = f"0 + ({term})"
        return (f"forall n. ({c(term)} = {c('n')} /\\ {d(term)} = {d('n')})",
                (*zero_add, "intro n", "split", "simp [hz]", "simp [hz]"))
    if family == "inductive_add_mul_zero":
        return (f"forall n. ({c('0 + n')} = {c('n')} /\\ {d('0 * n')} = {d('0')})",
                (*zero_add, *zero_mul, "intro n", "split", "simp [hz]", "simp [hm]"))
    if family == "inductive_distribution":
        lhs, rhs = f"((n + {numeral}) * 2)", f"(n * 2 + {2 * numeral})"
        return (f"forall n. ({c(lhs)} = {c(rhs)} /\\ {d(rhs)} = {d(lhs)})",
                ("have hs : forall a b. S a + b = S (a + b)", "intro a", "intro b", "induction b",
                 "simp", "simp [IH]", "intro n", "split", "simp [hs]", "symm", "simp [hs]"))
    if family == "contradiction_elimination":
        return (f"forall n m. ({b} /\\ ({b} -> bot)) -> n = m",
                (*intro2, "intro h", "cases h", "exfalso", "apply h_right", "exact h_left"))
    if family == "guarded_projection":
        return (f"forall n m p. (({a} /\\ ({b} /\\ {e})) /\\ n + 1 = n + 1) -> {b}",
                (*intro3, "intro h", "cases h", "cases h_left", "cases h_left_right", "assumption"))
    raise HydraScaledCompositionError("undeclared scaled teacher family")


def _source_identity() -> dict[str, object]:
    files = dict(pilot._source_identity()["files"])
    for name in ("training/peano_hydra/composition_scale.py", "training/peano_hydra/comparison.py",
                 "training/peano_hydra/protocol.py", "training/peano_hydra/posttrain.py"):
        files[name] = hashlib.sha256(pilot._read(ROOT / name, maximum=2 * 1024**2)).hexdigest()
    files = dict(sorted(files.items()))
    return {"coverage": "scaled generator, exact public comparison inventory, grammar and bounded native replay source bytes; not whole-repository attestation",
            "files": files, "source_files_sha256": pilot._digest(files)}


def excluded_comparison_targets() -> tuple[dict[str, str], ...]:
    """Predeclared exact target exclusion, not semantic or lineage independence."""
    from hydra_training_v5.peano_hydra.comparison import comparison_goals
    rows = [{"name": row["name"], "statement": row["statement"], "cohort": row["cohort"]}
            for row in comparison_goals()]
    _require(len(rows) == 96, "public comparison must retain exactly 96 declared goals")
    rows.extend({"name": name, "statement": validate_statement(source), "cohort": "historical-four"}
                for name, source in MODEL_V3_HELD_OUT_POLICY_GOALS)
    _require(len(rows) == 100 and len({row["name"] for row in rows}) == 100,
             "public/historical exclusion inventory changed")
    return tuple(rows)


def scaled_composition_plan(epoch: HydraEpoch, *, profile: str = COMPOSITION_PROFILE) -> dict[str, object]:
    _require(type(epoch) is HydraEpoch, "scaled composition requires an exact frozen HydraEpoch")
    _, environment, authority, prompt_contract, decoder_profile = pilot._authority(epoch, profile)
    from hydra_training_v5.peano_policy.authority import validate_authority_tactic
    excluded = excluded_comparison_targets()
    excluded_statements = {row["statement"] for row in excluded}
    catalog_names = {row.name for row in epoch.theorems}
    families, routes = [], []
    for family, split, description in _FAMILIES:
        declaration = {"id": family, "split": split, "description": description,
                       "variants": [list(row) for row in _VARIANTS], "variant_axes": ["structural_depth", "term_tree_shape", "small_numeral"],
                       "authorship": _AUTHORSHIP, "semantic_independence_claim": False}
        lineage = pilot._digest({"kind": "declared-structural-teacher-family-not-mathematical-component",
                                 "epoch_sha256": epoch.epoch_sha256, "declaration": declaration})
        declaration["lineage_sha256"] = lineage
        families.append(declaration)
        for seed, (depth, shape, numeral) in enumerate(_VARIANTS):
            source, commands = _route(family, depth, shape, numeral)
            _require(1 <= len(commands) <= MAX_ROUTE_DECISIONS, "scaled route exceeds its decision bound")
            _require(all(int(token) <= MAX_NUMERAL for token in _NUMBER.findall(source)), "scaled route numeral exceeds its bound")
            statement = validate_statement(source)
            _require(statement not in excluded_statements, "scaled teacher is an excluded exact public/historical target")
            name = f"hydra_teacher_scale_{family}_{seed:02d}"
            _require(name not in catalog_names, "scaled teacher impersonates an enrolled theorem")
            for command in commands:
                validate_authority_tactic(command, environment)
            routes.append({"name": name, "family": family, "generator_seed": seed,
                           "structural_depth": depth, "term_tree_shape": shape, "small_numeral": numeral,
                           "lineage_sha256": lineage, "split": split, "source": source, "statement": statement,
                           "statement_sha256": hashlib.sha256(statement.encode()).hexdigest(),
                           "commands": list(commands), "commands_sha256": pilot._digest(list(commands))})
    _require(len(routes) == len(_FAMILIES) * len(_VARIANTS) <= MAX_ROUTES, "scaled route inventory exceeds its bound")
    _require(len({row["name"] for row in routes}) == len(routes)
             and len({row["statement_sha256"] for row in routes}) == len(routes), "duplicate scaled route names or exact canonical statements")
    decisions = sum(len(row["commands"]) for row in routes)
    _require(decisions <= MAX_TOTAL_DECISIONS, "scaled source exceeds its total decision bound")
    common = pilot._digest({"kind": "one-common-exposed-structural-teacher-component",
                           "epoch_sha256": epoch.epoch_sha256, "authorship": _AUTHORSHIP,
                           "families": [row["id"] for row in families]})
    plan = {"schema": SCALED_COMPOSITION_PLAN_SCHEMA, "epoch_sha256": epoch.epoch_sha256,
            "authority_profile": profile, "authority": authority, "prompt_contract": prompt_contract,
            "decoder_profile": decoder_profile, "source_identity": _source_identity(),
            "families": families, "routes": routes, "route_count": len(routes), "tactic_decisions": decisions,
            "split_policy": pilot.COMPOSITION_SPLIT_POLICY,
            "excluded_targets": list(excluded), "excluded_targets_sha256": pilot._digest(excluded),
            "limits": {"max_routes": MAX_ROUTES, "max_route_decisions": MAX_ROUTE_DECISIONS,
                       "max_total_decisions": MAX_TOTAL_DECISIONS, "max_numeral": MAX_NUMERAL,
                       "max_route_trace_bytes": MAX_ROUTE_TRACE_BYTES,
                       "max_source_file_bytes": MAX_SOURCE_FILE_BYTES, "max_source_total_bytes": MAX_SOURCE_TOTAL_BYTES},
            "exposure": {"authorship": _AUTHORSHIP, "guided_teacher_proofs": True, "model_generated": False,
                         "public_and_correlated": True, "common_exposure_component_sha256": common,
                         "exact_public_comparison_target_exclusion": True, "exact_historical_target_exclusion": True,
                         "closed_intermediate_target_exclusion_required": True,
                         "declared_family_groups_are_mathematical_components": False,
                         "eligible_for_unseen_model_comparison": False, "semantic_equivalence_complete": False,
                         "independent_human_review": False, "sealed_benchmark": False,
                         "research_claim_eligible": False, "alpha_admitted": False, "dag_mutated": False}}
    plan["plan_sha256"] = pilot._digest(plan)
    return plan


def scaled_composition_profile_record(epoch: HydraEpoch | None = None, *, profile: str = COMPOSITION_PROFILE) -> dict[str, object]:
    """Detached declaration only: no teacher execution or successful-proof claim."""
    return scaled_composition_plan(freeze_epoch(ROOT) if epoch is None else epoch, profile=profile)


def _check_split(rows: tuple[dict[str, object], ...]) -> None:
    declared = {family: split for family, split, _ in _FAMILIES}
    seen = {}
    for row in rows:
        _require(row["family"] in declared and row["split"] == declared[row["family"]], "scaled family was split or reassigned")
        key = (row["environment_sha256"], row["state_sha256"], row["focus"], row["action"])
        _require(key not in seen or seen[key] == row["split"], "exact scaled state/action leaked across diagnostic splits")
        seen[key] = row["split"]
    _require({row["split"] for row in rows} == {"train", "dev"}, "scaled source lost a declared split")


def _check_intermediates(rows: tuple[dict[str, object], ...], excluded: set[str]) -> None:
    from hydra_training_v5.peano_hydra.posttrain import _goal_target
    for row in rows:
        for goal in (*row["goals_before"], *row["goals_after"]):
            target = _goal_target(goal)
            _require(target not in excluded,
                     f"scaled route exposes an excluded closed intermediate goal: {row.get('theorem_name')} step {row.get('step')}: {target}")


@dataclass(frozen=True, slots=True)
class ScaledCompositionSource:
    epoch: HydraEpoch
    curriculum: VerifiedCurriculum
    manifest: dict[str, object]
    payloads: dict[str, bytes]


def build_scaled_composition_source(epoch: HydraEpoch | None = None, *, profile: str = COMPOSITION_PROFILE) -> ScaledCompositionSource:
    if epoch is None:
        epoch = freeze_epoch(ROOT)
    plan = scaled_composition_plan(epoch, profile=profile)
    caps, environment, authority, prompt_contract, decoder_profile = pilot._authority(epoch, profile)
    rows, evidence = [], []
    for route in plan["routes"]:
        result = run_proof(route["source"], tuple(route["commands"]), request_id=route["name"], session_id=route["name"],
                           classical=False, on_error="stop", capabilities=caps, trace_byte_limit=MAX_ROUTE_TRACE_BYTES)
        try:
            pilot._checked_result(result, route, caps=caps, environment_sha256=environment.sha256)
        except ValueError as error:
            raise HydraScaledCompositionError(f"{route['name']}: {error}; {result.error}") from error
        rows.extend(pilot._rows(epoch, route, result, environment))
        evidence.append({"name": route["name"], "statement_sha256": route["statement_sha256"],
                         "commands_sha256": route["commands_sha256"], "kernel_checked": True,
                         "proof_nodes": result.proof_nodes, "trace_sha256": pilot._digest(result.trace),
                         "trace_bytes": len(pilot._canonical(result.trace)), "trace_encoding": "sha256-of-exact-canonical-full-native-trace"})
    transitions = tuple(rows)
    _require(len(transitions) == plan["tactic_decisions"], "scaled row inventory differs from declared decisions")
    _check_split(transitions)
    _check_intermediates(transitions, {row["statement"] for row in plan["excluded_targets"]})
    curriculum = VerifiedCurriculum(epoch.epoch_sha256, transitions, (), ())
    manifest = curriculum.manifest()
    manifest.update({"schema": SCALED_COMPOSITION_SCHEMA, "version": epoch.version,
                     "edition_identity_sha256": epoch.edition_identity_sha256,
                     "theorem_dag_sha256": epoch.theorem_dag_sha256,
                     "reviewed_definition_dag_sha256": epoch.reviewed_definition_dag_sha256,
                     "authority_profile": profile, "authority": authority, "prompt_contract": prompt_contract,
                     "decoder_profile": decoder_profile, "split_policy": pilot.COMPOSITION_SPLIT_POLICY,
                     "exposure": plan["exposure"],
                     "composition": {"plan": plan, "teacher_routes": evidence,
                                     "verified_route_count": len(evidence), "verified_tactic_decisions": len(transitions),
                                     "family_route_counts": dict(sorted(Counter(row["family"] for row in plan["routes"]).items())),
                                     "exact_cross_split_state_action_overlaps": 0,
                                     "excluded_closed_intermediate_hits": 0,
                                     "trace_evidence": "complete SFT states plus exact full-trace hashes; no duplicated embedded traces",
                                     "independent_verification": "regenerate every fixed scaled teacher against its original goal"},
                     "proof_optimization_claim": "none; explicit guided teacher routes, not minimum proofs",
                     "discovery_claim": "none; not autonomous theorem discovery or unseen model evidence",
                     "open_research_gates": ["H0 full reference/conformance scope", "H1 independently reviewed sealed benchmark", "H5 unseen model advantage"]})
    payloads = {"epoch.json": pilot._pretty(epoch.to_dict(include_graphs=True)),
                "sft.jsonl": encode_jsonl(transitions), "preferences.jsonl": b"", "discovery.jsonl": b"",
                "manifest.json": pilot._pretty(manifest)}
    _require(all(len(raw) <= MAX_SOURCE_FILE_BYTES for raw in payloads.values())
             and sum(map(len, payloads.values())) <= MAX_SOURCE_TOTAL_BYTES, "scaled source exceeds file or aggregate byte bounds")
    _require(scaled_composition_plan(epoch, profile=profile) == plan, "scaled source identity changed during native replay")
    return ScaledCompositionSource(epoch, curriculum, manifest, payloads)


def publish_scaled_composition_source(source: ScaledCompositionSource, directory: Path) -> Path:
    from hydra_training_v5.peano_policy.manifest import publish_staged_directory_noreplace
    _require(type(source) is ScaledCompositionSource, "publication requires an exact scaled source")
    directory = Path(directory).absolute()
    _require(not directory.exists() and not directory.is_symlink(), "scaled composition destination already exists")
    _require(not any(parent.is_symlink() for parent in directory.parents), "scaled output ancestors must not be symlinks")
    fresh = build_scaled_composition_source(source.epoch, profile=source.manifest.get("authority_profile"))
    _require(source.payloads == fresh.payloads and source.manifest == fresh.manifest and source.curriculum == fresh.curriculum,
             "refusing altered or unverified scaled teacher data")
    directory.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{directory.name}.partial-", dir=directory.parent))
    for name in SOURCE_FILENAMES:
        with (staging / name).open("xb") as stream:
            stream.write(fresh.payloads[name])
            stream.flush()
            os.fsync(stream.fileno())
    publish_staged_directory_noreplace(staging, directory)
    return directory


def verify_scaled_composition_source(directory: Path) -> VerifiedSource:
    from hydra_training_v5.peano_hydra.posttrain import VerifiedSource
    directory = Path(directory).absolute()
    payloads = pilot._read_source(directory)
    manifest = pilot._decode(payloads["manifest.json"])
    _require(manifest.get("schema") == SCALED_COMPOSITION_SCHEMA and manifest.get("authority_profile") == COMPOSITION_PROFILE,
             "scaled source requires its distinct schema and explicit authority profile")
    epoch = freeze_epoch(ROOT)
    _require(pilot._decode(payloads["epoch.json"]) == epoch.to_dict(include_graphs=True),
             "scaled source differs from current frozen epoch and both DAGs")
    _require(type(manifest.get("composition")) is dict
             and manifest["composition"].get("plan") == scaled_composition_plan(epoch),
             "scaled source changed its fixed generator, exclusions, families, or authority")
    fresh = build_scaled_composition_source(epoch)
    _require(payloads == fresh.payloads, "scaled bytes differ from independently regenerated native QED evidence")
    _require(pilot._read_source(directory) == payloads, "scaled source changed during replay")
    return VerifiedSource(directory, epoch, fresh.curriculum, fresh.manifest, payloads)


__all__ = ["SCALED_COMPOSITION_SCHEMA", "SCALED_COMPOSITION_PLAN_SCHEMA", "COMPOSITION_PROFILE",
           "ScaledCompositionSource", "HydraScaledCompositionError", "scaled_composition_plan",
           "scaled_composition_profile_record", "build_scaled_composition_source",
           "publish_scaled_composition_source", "verify_scaled_composition_source", "excluded_comparison_targets"]
