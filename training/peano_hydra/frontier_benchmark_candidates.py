"""Authored constructive evaluation candidates, never training or a sealed test.

The inventory is fixed before native replay. All eight variants of a template
are reserved from training; four form a proposed PRIMARY32 and four remain
unscored reservations, not a second independent test. There is no theorem
import, classical principle, model call, training row, admission, or ownership
attestation here. A caller must put native work inside ``run_bounded``.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from training.peano_hydra.epoch import HydraEpoch


ROOT = Path(__file__).resolve().parents[2]
PLAN_SCHEMA = "peano-hydra-frontier-benchmark-candidate-plan-v1"
PROOF_SCHEMA = "peano-hydra-frontier-benchmark-candidate-native-proof-v1"
BUNDLE_SCHEMA = "peano-hydra-frontier-benchmark-candidate-bundle-v1"
MANIFEST_SCHEMA = "peano-hydra-frontier-benchmark-candidate-manifest-v1"
PRIMARY_COHORT = "heldout-candidate-primary32"
RESERVED_COHORT = "heldout-candidate-reserved32"
AUTHORITY_PROFILE = "peano-authority-primitive-v1"
MAX_ROUTES = 64
MAX_ROUTE_DECISIONS = 16
MAX_ROUTE_TRACE_BYTES = 256 * 1024
MAX_BUNDLE_BYTES = 8 * 1024**2
MAX_NUMERAL = 5
_AUTHORSHIP = "agent-authored-after-exposed-primary32-results-2026-08-30"
_VARIANTS = tuple((numeral, shape) for numeral in (1, 2, 3, 4) for shape in (0, 1))
# These are new authored whole templates, not independent mathematical DAG
# components. Correlated primitive motifs are explicitly retained below.
_FAMILIES = (
    ("and_distributes_over_or", "A /\\ (B \\/ C) -> (A /\\ B) \\/ (A /\\ C)",
     "Distribute a retained conjunct through both cases of a disjunction.",
     ("scale:conjunction_associate", "scale:disjunction_map")),
    ("disjunctive_implication_split", "((A \\/ B) -> C) -> ((A -> C) /\\ (B -> C))",
     "Turn one map out of a disjunction into two separately introduced maps.",
     ("scale:implication_pair", "scale:disjunction_map")),
    ("de_morgan_disjunction", "((A -> bot) /\\ (B -> bot)) -> ((A \\/ B) -> bot)",
     "Eliminate a disjunction against its separately supplied negations.",
     ("scale:contradiction_elimination", "scale:disjunction_map")),
    ("double_negated_excluded_middle", "((A \\/ (A -> bot)) -> bot) -> bot",
     "Prove only double-negated excluded middle by constructive continuations.",
     ("scale:contradiction_elimination", "composition:disjunction_injection")),
    ("exists_disjunction_distribution", "(exists x. A(x) \\/ B(x)) -> (exists x. A(x)) \\/ (exists x. B(x))",
     "Unpack an unknown witness before choosing its justified disjunct.",
     ("scale:existential_unpack", "scale:disjunction_swap")),
    ("exists_constant_conjunction", "(exists x. A(x) /\\ B) -> (exists x. A(x)) /\\ B",
     "Extract a constant conjunct while retaining an unknown existential witness.",
     ("scale:existential_unpack", "scale:conjunction_swap")),
    ("witness_universal_exchange", "(exists x. forall y. R(x,y)) -> forall y. exists x. R(x,y)",
     "Retain one unknown witness while specializing its universal property.",
     ("scale:existential_unpack", "scale:universal_specialization")),
    ("peirce_double_negated_conclusion", "((A -> B) -> A) -> ((A -> bot) -> bot)",
     "Derive a double-negated conclusion from a higher-order premise, constructively.",
     ("scale:implication_compose", "scale:contradiction_elimination")),
)


class CandidateError(ValueError):
    """Candidate evidence escaped its declared source, proof, or claim bounds."""


class CandidateNativeFailure(CandidateError):
    """A native failure whose complete bounded observation must be preserved."""

    def __init__(self, message: str, evidence: dict[str, object]):
        super().__init__(message)
        self.evidence = evidence


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CandidateError(message)


def _native():
    from training.peano_hydra import composition
    return composition


def _canonical(value: object) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False,
                          separators=(",", ":")).encode("utf-8")
    except (TypeError, ValueError, RecursionError) as error:
        raise CandidateError("candidate metadata is not bounded strict JSON") from error


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _text_digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _context_term(variable: str, numeral: int, shape: int) -> str:
    return f"({variable} + {numeral})" if shape == 0 else f"({variable} * {numeral + 1})"


def _template(family: str, variant: tuple[int, int]) -> tuple[str, tuple[str, ...]]:
    k, shape = variant
    def term(variable: str) -> str:
        return _context_term(variable, k, shape)
    a, b, c = f"{term('n')} = {term('m')}", f"n = {k}", f"m = {k + 1}"
    prefix = ("intro n", "intro m")
    if family == "and_distributes_over_or":
        return (f"forall n m. ({a} /\\ ({b} \\/ {c})) -> (({a} /\\ {b}) \\/ ({a} /\\ {c}))",
                (*prefix, "intro h", "cases h", "cases h_right", "left", "split",
                 "exact h_left", "exact h_right_left", "right", "split", "exact h_left", "exact h_right_right"))
    if family == "disjunctive_implication_split":
        return (f"forall n m. (({a} \\/ {b}) -> {c}) -> (({a} -> {c}) /\\ ({b} -> {c}))",
                (*prefix, "intro h", "split", "intro ha", "apply h", "left", "exact ha",
                 "intro hb", "apply h", "right", "exact hb"))
    if family == "de_morgan_disjunction":
        return (f"forall n m. (({a} -> bot) /\\ ({b} -> bot)) -> (({a} \\/ {b}) -> bot)",
                (*prefix, "intro h", "cases h", "intro q", "cases q", "apply h_left",
                 "exact q_left", "apply h_right", "exact q_right"))
    if family == "double_negated_excluded_middle":
        return (f"forall n m. (({a} \\/ ({a} -> bot)) -> bot) -> bot",
                (*prefix, "intro h", "apply h", "right", "intro ha", "apply h", "left", "exact ha"))
    if family == "exists_disjunction_distribution":
        ax, bx = f"{term('x')} = n", f"S ({term('x')}) = n"
        return (f"forall n. (exists x. ({ax} \\/ {bx})) -> ((exists x. {ax}) \\/ (exists x. {bx}))",
                ("intro n", "intro h", "cases h", "cases h_witness", "left", "exists x",
                 "exact h_witness_left", "right", "exists x", "exact h_witness_right"))
    if family == "exists_constant_conjunction":
        ax = f"{term('x')} = n"
        return (f"forall n m. (exists x. ({ax} /\\ m = n)) -> ((exists x. {ax}) /\\ m = n)",
                (*prefix, "intro h", "cases h", "cases h_witness", "split", "exists x",
                 "exact h_witness_left", "exact h_witness_right"))
    if family == "witness_universal_exchange":
        relation = f"{term('x')} * y = n * y"
        return (f"forall n. (exists x. forall y. {relation}) -> forall y. exists x. {relation}",
                ("intro n", "intro h", "cases h", "intro y", "specialize h_witness y", "exists x", "exact h_witness"))
    if family == "peirce_double_negated_conclusion":
        return (f"forall n m. (({a} -> {b}) -> {a}) -> (({a} -> bot) -> bot)",
                (*prefix, "intro f", "intro h", "apply h", "apply f", "intro ha", "exfalso", "apply h", "exact ha"))
    raise CandidateError("undeclared benchmark candidate template")


def _source_identity() -> dict[str, object]:
    native = _native()
    files = dict(native._source_identity()["files"])
    for name in ("training/peano_hydra/frontier_benchmark_candidates.py",
                 "scripts/build_peano_hydra_benchmark_candidates.py",
                 "training/peano_hydra/composition_scale.py", "training/peano_hydra/frontier_curriculum.py",
                 "training/peano_hydra/witness_repair.py", "training/peano_hydra/protocol.py",
                 "training/peano_hydra/review_runtime.py", "scripts/hydra_bounded_exec.py"):
        files[name] = hashlib.sha256(native._read(ROOT / name, maximum=2 * 1024**2)).hexdigest()
    files = dict(sorted(files.items()))
    return {"files": files, "source_files_sha256": _digest(files),
            "coverage": "candidate generator/driver, declared related generators, native kernel/engine and primitive authority; not whole-repository or transitive-import attestation"}


def _claims() -> dict[str, object]:
    return {"status": "candidate_pending_external_review", "authorship": _AUTHORSHIP,
            "external_owner_attested": False, "independent_human_review": False,
            "sealed_benchmark": False, "eligible_for_unseen_model_comparison": False,
            "semantic_equivalence_complete": False, "mathematical_lineages_independent": False,
            "primitive_proof_motifs_correlated_with_training": True,
            "excluded_from_training_by_design": True, "historical_training_exclusion_audit_complete": False,
            "training_rows_created": 0, "model_calls": 0, "gpu_jobs": 0,
            "classical": False, "theorem_imports": [], "theorem_admission": False,
            "reserved_variants_are_independent_test": False, "research_claim_eligible": False}


@dataclass(frozen=True, slots=True)
class _Context:
    epoch: HydraEpoch
    capabilities: object
    environment: object
    authority: dict
    prompt_contract: dict
    decoder_profile: dict
    source_identity: dict


def _context(epoch: HydraEpoch) -> _Context:
    from training.peano_hydra.epoch import HydraEpoch as Epoch
    _require(type(epoch) is Epoch, "candidate construction requires an explicit frozen HydraEpoch")
    caps, environment, authority, prompt, decoder = _native()._authority(epoch, AUTHORITY_PROFILE)
    return _Context(epoch, caps, environment, authority, prompt, decoder, _source_identity())


def _families(context: _Context) -> list[dict[str, object]]:
    records = []
    for name, logical_template, description, motifs in _FAMILIES:
        body = {"id": name, "logical_template": logical_template, "description": description,
                "template_version": 1, "variant_axes": ["small_numeral", "arithmetic_atom_context"],
                "variants": [list(row) for row in _VARIANTS], "primary_seeds": [0, 1, 2, 3],
                "reserved_seeds": [4, 5, 6, 7], "all_variants_excluded_from_training": True,
                "known_correlated_primitive_motifs": list(motifs),
                "whole_template_distinctness_pending_external_audit": True,
                "semantic_independence_claim": False, "authorship": _AUTHORSHIP}
        template_sha = _digest(body)
        records.append({**body, "logical_template_sha256": _text_digest(logical_template),
                        "template_sha256": template_sha,
                        "lineage_sha256": _digest({"kind": "authored-candidate-template-not-independent-mathematical-component",
                            "epoch_sha256": context.epoch.epoch_sha256, "template_sha256": template_sha})})
    return records


def _route(context: _Context, families: list[dict], ordinal: int) -> dict[str, object]:
    from training.peano_hydra.protocol import validate_statement
    from training.peano_policy.authority import validate_authority_tactic
    _require(type(ordinal) is int and 0 <= ordinal < MAX_ROUTES, "invalid candidate route ordinal")
    family_index, seed = divmod(ordinal, len(_VARIANTS))
    family = families[family_index]
    source, commands = _template(family["id"], _VARIANTS[seed])
    _require(1 <= len(commands) <= MAX_ROUTE_DECISIONS and len(source.encode()) <= 4096,
             "candidate statement or teacher exceeds its bound")
    statement = validate_statement(source)
    for command in commands:
        _require(validate_authority_tactic(command, context.environment) == command,
                 "candidate command changed primitive authority")
    body = {"ordinal": ordinal, "name": f"hydra_candidate_{family['id']}_{seed:02d}",
            "family": family["id"], "generator_seed": seed, "variant": list(_VARIANTS[seed]),
            "cohort": PRIMARY_COHORT if seed < 4 else RESERVED_COHORT,
            "use": "evaluation_candidate_only", "source": source, "source_sha256": _text_digest(source),
            "statement": statement, "statement_sha256": _text_digest(statement),
            "commands": list(commands), "commands_sha256": _digest(commands),
            "teacher_decisions": len(commands), "template_sha256": family["template_sha256"],
            "logical_template_sha256": family["logical_template_sha256"],
            "lineage_sha256": family["lineage_sha256"], "epoch_sha256": context.epoch.epoch_sha256,
            "source_identity_sha256": context.source_identity["source_files_sha256"]}
    return {**body, "route_sha256": _digest(body)}


def _plan(context: _Context) -> dict[str, object]:
    from training.peano_hydra.composition_scale import excluded_comparison_targets
    families = _families(context)
    routes = [_route(context, families, ordinal) for ordinal in range(MAX_ROUTES)]
    excluded = {row["statement"] for row in excluded_comparison_targets()}
    _require(len({row["statement"] for row in routes}) == MAX_ROUTES, "candidate exact targets repeat")
    _require(not excluded & {row["statement"] for row in routes}, "candidate duplicates a public comparison target")
    body = {"schema": PLAN_SCHEMA, "route_count": MAX_ROUTES, "family_count": len(families),
            "epoch": context.epoch.to_dict(include_graphs=False), "source_identity": context.source_identity,
            "authority": context.authority, "prompt_contract": context.prompt_contract,
            "decoder_profile": context.decoder_profile, "families": families, "routes": routes,
            "primary_count": 32, "reserved_count": 32,
            "cohort_policy": "all eight variants reserved from training; fixed seeds0-3 scored only after review; seeds4-7 not scored in pilot",
            "common_exposure_component_sha256": _digest({"authorship": _AUTHORSHIP,
                "epoch_sha256": context.epoch.epoch_sha256, "families": families}),
            "limits": {"max_routes": MAX_ROUTES, "max_route_decisions": MAX_ROUTE_DECISIONS,
                       "max_route_trace_bytes": MAX_ROUTE_TRACE_BYTES, "max_bundle_bytes": MAX_BUNDLE_BYTES,
                       "max_numeral": MAX_NUMERAL},
            "pre_model_acceptance": {"all_native_teachers_required": True,
                "all_roots_and_intermediate_states_retained": True,
                "external_whole_template_exposure_audit_required": True,
                "human_owned_benchmark_review_required": True,
                "budgets_to_compare_separately": [8, 16],
                "model_improvement_threshold": "separate parent-owned frozen experiment protocol; not set from candidate outcomes"},
            "rejected_designs": [{"family": "not_exists_to_forall_not",
                "reason": "same logical template as historical not-divisibility duality in library/theorems.py; never an evaluation candidate"},
                {"family": "relational_witness_composition",
                 "reason": "simple arithmetic totality instances gave redundant explicit witnesses or impossible premises; not authored"}],
            "claims": _claims()}
    return {**body, "plan_sha256": _digest(body)}


def candidate_plan(epoch: HydraEpoch) -> dict[str, object]:
    """Declare all64 routes without native replay, implicit epoch, or models."""
    context = _context(epoch)
    result = _plan(context)
    _require(_source_identity() == context.source_identity, "candidate source changed during declaration")
    return result


def evaluation_goals(plan: dict[str, object], *, cohort: str = PRIMARY_COHORT) -> tuple[dict[str, object], ...]:
    """Detach goal-only input; this is not a seal or evaluator authorization."""
    _require(cohort in (PRIMARY_COHORT, RESERVED_COHORT), "unknown candidate cohort")
    _require(type(plan) is dict and plan.get("schema") == PLAN_SCHEMA
             and plan.get("claims") == _claims()
             and plan.get("plan_sha256") == _digest({k: v for k, v in plan.items() if k != "plan_sha256"}),
             "candidate plan changed its identity or claims")
    fields = ("name", "family", "generator_seed", "cohort", "statement", "statement_sha256",
              "template_sha256", "lineage_sha256", "route_sha256")
    rows = tuple({key: route[key] for key in fields} for route in plan["routes"] if route["cohort"] == cohort)
    _require(len(rows) == 32 and Counter(row["family"] for row in rows) == Counter({row[0]: 4 for row in _FAMILIES}),
             "candidate cohort changed whole-template allocation")
    return rows


def _goal_record(display: str) -> dict[str, object]:
    from peano_lab.kernel.formulas import parse_formula_with_names, pretty_formula
    from training.peano_hydra.witness_repair import _target
    _require(type(display) is str and len(display.encode()) <= 16384, "candidate goal display exceeds its bound")
    target = _target(display)
    formula, names = parse_formula_with_names(target)
    canonical = pretty_formula(formula, list(names))
    return {"display": display, "display_sha256": _text_digest(display), "target_source": target,
            "target_source_sha256": _text_digest(target), "target_canonical": canonical,
            "target_canonical_sha256": _text_digest(canonical), "free_names": list(names),
            "closed_target_sha256": None if names else _text_digest(canonical)}


def _replay(context: _Context, route: dict[str, object], expected: dict[str, object]) -> dict[str, object]:
    native = _native()
    _require(type(route) is dict and native._canonical(route) == native._canonical(expected),
             "candidate route changed its exact declaration")
    result = native.run_proof(route["source"], tuple(route["commands"]), request_id=route["name"],
        session_id=route["name"], classical=False, on_error="stop", capabilities=context.capabilities,
        trace_byte_limit=MAX_ROUTE_TRACE_BYTES)
    try:
        native._checked_result(result, route, caps=context.capabilities, environment_sha256=context.environment.sha256)
    except ValueError as error:
        raise CandidateNativeFailure(str(error), {"route": route, "native_result": result.to_dict(),
            "status": "native_proof_failed", "claims": _claims()}) from error
    states = []
    from training.peano_policy.search import state_sha256
    for index, entry in enumerate(result.trace[:-1]):
        _require(entry.get("tactic") == route["commands"][index]
                 and entry.get("status") == "ok" and entry.get("step") == index + 1,
                 "candidate transition differs from declared command")
        before, after = entry["goals_before"], entry["goals_after"]
        _require(index == 0 or before == result.trace[index - 1]["goals_after"], "candidate trace disconnected")
        body = {"step": index + 1, "action": entry["tactic"], "focus": entry["focus"],
                "environment_sha256": context.environment.sha256,
                "before_state_sha256": state_sha256(tuple(before)), "after_state_sha256": state_sha256(tuple(after)),
                "before": [_goal_record(goal) for goal in before], "after": [_goal_record(goal) for goal in after]}
        states.append({**body, "intermediate_sha256": _digest(body)})
    body = {"schema": PROOF_SCHEMA, "name": route["name"], "route_sha256": route["route_sha256"],
            "family": route["family"], "lineage_sha256": route["lineage_sha256"],
            "template_sha256": route["template_sha256"], "source_sha256": route["source_sha256"],
            "statement_sha256": route["statement_sha256"], "commands_sha256": route["commands_sha256"],
            "source_identity_sha256": route["source_identity_sha256"], "epoch_sha256": route["epoch_sha256"],
            "kernel_checked": True, "proof_nodes": result.proof_nodes, "engine_steps": result.engine_steps,
            "native_result": result.to_dict(), "trace_sha256": _digest(result.trace),
            "intermediates": states, "intermediates_sha256": _digest(states),
            "use": "evaluation_candidate_evidence_only", "training_row": False}
    return {**body, "proof_sha256": _digest(body)}


def verify_candidate_route(epoch: HydraEpoch, route: dict[str, object]) -> dict[str, object]:
    """One complete native QED with full bounded trace, never an SFT example."""
    context = _context(epoch)
    _require(type(route) is dict, "candidate route must be an exact dictionary")
    expected = _route(context, _families(context), route.get("ordinal"))
    result = _replay(context, route, expected)
    _require(_source_identity() == context.source_identity, "candidate source changed during replay")
    return result


def build_candidate_bundle(epoch: HydraEpoch, *,
                           observe: Callable[[str, dict[str, object]], None] | None = None) -> dict[str, object]:
    """Verify all64; optional observer retains declarations and partial evidence.

    The observer is called before proofs with ``plan``, then after each checked
    route with ``proof``. A failed native route is observed as ``failure`` before
    propagating its exception. The caller preserves every such attempt.
    """
    context = _context(epoch)
    plan = _plan(context)
    if observe is not None:
        observe("plan", plan)
    proofs = []
    for route in plan["routes"]:
        try:
            proof = _replay(context, route, route)
        except CandidateNativeFailure as error:
            if observe is not None:
                observe("failure", error.evidence)
            raise
        proofs.append(proof)
        if observe is not None:
            observe("proof", proof)
    body = {"schema": BUNDLE_SCHEMA, "plan": plan, "proofs": proofs,
            "primary_goals": list(evaluation_goals(plan)),
            "reserved_goals": list(evaluation_goals(plan, cohort=RESERVED_COHORT)),
            "verified_route_count": len(proofs), "verified_decisions": sum(len(row["commands"]) for row in plan["routes"]),
            "proofs_sha256": _digest(proofs), "claims": _claims()}
    result = {**body, "bundle_sha256": _digest(body)}
    _require(len(_native()._canonical(result)) <= MAX_BUNDLE_BYTES, "candidate bundle exceeds its byte bound")
    _require(_source_identity() == context.source_identity, "candidate source changed during complete replay")
    return result


def build_candidate_manifest(bundle: dict[str, object], *,
                             artifacts: dict[str, dict[str, object]]) -> dict[str, object]:
    """Bind already-observed complete evidence; no replay or ownership claim.

    The native worker constructs this only after ``build_candidate_bundle``.
    A consuming protocol must separately pin these exact manifest bytes and
    the bounded process receipt; hashes alone never authenticate a proof.
    """
    _require(type(bundle) is dict and bundle.get("schema") == BUNDLE_SCHEMA
             and bundle.get("claims") == _claims()
             and bundle.get("bundle_sha256") == _digest({k: v for k, v in bundle.items() if k != "bundle_sha256"})
             and len(_canonical(bundle)) <= MAX_BUNDLE_BYTES,
             "candidate bundle changed before manifest construction")
    plan = bundle["plan"]
    primary = evaluation_goals(plan)
    reserved = evaluation_goals(plan, cohort=RESERVED_COHORT)
    _require(bundle["primary_goals"] == list(primary) and bundle["reserved_goals"] == list(reserved)
             and bundle["proofs_sha256"] == _digest(bundle["proofs"])
             and len(bundle["proofs"]) == MAX_ROUTES == bundle["verified_route_count"],
             "candidate bundle lost a planned native proof or goal")
    references = []
    for route, proof in zip(plan["routes"], bundle["proofs"]):
        result = proof["native_result"]
        _require(proof["proof_sha256"] == _digest({k: v for k, v in proof.items() if k != "proof_sha256"})
                 and proof["route_sha256"] == route["route_sha256"] and proof["name"] == route["name"]
                 and proof["kernel_checked"] is True and result["kernel_checked"] is True
                 and result["status"] == "proved" and result["theorem"] == route["statement"]
                 and result["goals"] == [] and result["classical"] is False
                 and result["failed_tactics"] == 0 and result["tactics_applied"] == len(route["commands"])
                 and proof["trace_sha256"] == _digest(result["trace"])
                 and proof["intermediates_sha256"] == _digest(proof["intermediates"]),
                 "candidate proof metadata changed before manifest construction")
        references.append({key: proof[key] for key in ("name", "route_sha256", "trace_sha256", "proof_sha256",
                                                       "intermediates_sha256", "proof_nodes")})
        references[-1]["teacher_decisions"] = len(route["commands"])
    body = {"schema": MANIFEST_SCHEMA, "claims": _claims(), "primary_goals": list(primary),
            "reserved_goals": list(reserved), "source_identity": plan["source_identity"], "epoch": plan["epoch"],
            "families": plan["families"], "common_exposure_component_sha256": plan["common_exposure_component_sha256"],
            "plan_sha256": plan["plan_sha256"], "bundle_sha256": bundle["bundle_sha256"],
            "proofs_sha256": bundle["proofs_sha256"], "proof_references": references,
            "verified_route_count": MAX_ROUTES, "verified_decisions": bundle["verified_decisions"],
            "artifacts": artifacts, "native_scope": "complete original-goal native constructive QEDs; fresh process replay separately receipted",
            "validation_scope": "bounded metadata/hash consistency; not a native recheck, historical exposure audit, external owner or final-test seal"}
    result = {**body, "manifest_sha256": _digest(body)}
    validate_manifest(result)
    return result


def validate_manifest(record: dict[str, object]) -> None:
    """Pure bounded metadata validation; importing this module loads no engine."""
    required = {"schema", "claims", "primary_goals", "reserved_goals", "source_identity", "epoch", "families",
                "common_exposure_component_sha256", "plan_sha256", "bundle_sha256", "proofs_sha256",
                "proof_references", "verified_route_count", "verified_decisions", "artifacts", "native_scope",
                "validation_scope", "manifest_sha256"}
    _require(type(record) is dict and set(record) == required and len(_canonical(record)) <= 512 * 1024,
             "candidate manifest fields or byte bound changed")
    _require(record["schema"] == MANIFEST_SCHEMA and record["claims"] == _claims()
             and record["manifest_sha256"] == _digest({k: v for k, v in record.items() if k != "manifest_sha256"}),
             "candidate manifest identity or candidate-only claims changed")
    def sha(value: object) -> bool:
        return type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value) is not None
    for field in ("common_exposure_component_sha256", "plan_sha256", "bundle_sha256", "proofs_sha256"):
        _require(sha(record[field]), "candidate manifest lost a required evidence digest")
    source = record["source_identity"]
    _require(type(source) is dict and set(source) == {"files", "source_files_sha256", "coverage"}
             and type(source["files"]) is dict and 1 <= len(source["files"]) <= 128
             and source["source_files_sha256"] == _digest(source["files"]), "candidate source identity changed")
    _require(all(type(name) is str and name and not Path(name).is_absolute() and ".." not in Path(name).parts
                 and sha(value) for name, value in source["files"].items()), "candidate source file inventory is unsafe")
    families = record["families"]
    _require(type(families) is list and len(families) == len(_FAMILIES)
             and [item["id"] for item in families] == [row[0] for row in _FAMILIES], "candidate template inventory changed")
    for family in families:
        _require(family["template_sha256"] == _digest({k: v for k, v in family.items()
                     if k not in {"template_sha256", "logical_template_sha256", "lineage_sha256"}})
                 and family["logical_template_sha256"] == _text_digest(family["logical_template"])
                 and family["semantic_independence_claim"] is False
                 and family["all_variants_excluded_from_training"] is True,
                 "candidate whole-template evidence changed")
    by_family = {row["id"]: row for row in families}
    seen = {}
    fields = {"name", "family", "generator_seed", "cohort", "statement", "statement_sha256",
              "template_sha256", "lineage_sha256", "route_sha256"}
    for cohort, field, seeds in ((PRIMARY_COHORT, "primary_goals", set(range(4))),
                                 (RESERVED_COHORT, "reserved_goals", set(range(4, 8)))):
        rows = record[field]
        _require(type(rows) is list and len(rows) == 32, "candidate cohort size changed")
        assignments = set()
        for row in rows:
            _require(type(row) is dict and set(row) == fields and row["family"] in by_family
                     and type(row["generator_seed"]) is int and row["generator_seed"] in seeds
                     and row["cohort"] == cohort and type(row["statement"]) is str
                     and 1 <= len(row["statement"].encode()) <= 4096
                     and row["statement_sha256"] == _text_digest(row["statement"])
                     and row["template_sha256"] == by_family[row["family"]]["template_sha256"]
                     and row["lineage_sha256"] == by_family[row["family"]]["lineage_sha256"]
                     and sha(row["route_sha256"]), "candidate goal differs from its source/template/cohort")
            _require(row["name"] == f"hydra_candidate_{row['family']}_{row['generator_seed']:02d}"
                     and row["name"] not in seen, "candidate goal name repeats or lost its declared origin")
            seen[row["name"]] = row
            assignments.add((row["family"], row["generator_seed"]))
        _require(assignments == {(family, seed) for family in by_family for seed in seeds},
                 "candidate cohort no longer includes four fixed variants of every template")
    _require(len({row["statement_sha256"] for row in seen.values()}) == MAX_ROUTES, "candidate targets repeat")
    references = record["proof_references"]
    _require(type(references) is list and len(references) == MAX_ROUTES
             and {row["name"] for row in references} == set(seen), "candidate proof reference inventory incomplete")
    for reference in references:
        _require(set(reference) == {"name", "route_sha256", "trace_sha256", "proof_sha256",
                                    "intermediates_sha256", "proof_nodes", "teacher_decisions"}
                 and reference["route_sha256"] == seen[reference["name"]]["route_sha256"]
                 and all(sha(reference[field]) for field in ("trace_sha256", "proof_sha256", "intermediates_sha256"))
                 and type(reference["teacher_decisions"]) is int and 1 <= reference["teacher_decisions"] <= MAX_ROUTE_DECISIONS
                 and type(reference["proof_nodes"]) is int and 1 <= reference["proof_nodes"] <= 100000,
                 "candidate proof reference lost its complete bounded teacher identity")
    _require(type(record["verified_route_count"]) is int and record["verified_route_count"] == MAX_ROUTES
             and type(record["verified_decisions"]) is int
             and record["verified_decisions"] == sum(row["teacher_decisions"] for row in references),
             "candidate proof counts changed")
    artifacts = record["artifacts"]
    _require(type(artifacts) is dict and 2 <= len(artifacts) <= 128
             and {"bundle.json", "plan.json"} <= set(artifacts), "candidate artifact inventory incomplete")
    for name, entry in artifacts.items():
        _require(type(name) is str and name and not Path(name).is_absolute() and ".." not in Path(name).parts
                 and type(entry) is dict and set(entry) == {"bytes", "sha256"}
                 and type(entry["bytes"]) is int and 0 < entry["bytes"] <= MAX_BUNDLE_BYTES
                 and sha(entry["sha256"]), "candidate artifact reference is unsafe or unbounded")
