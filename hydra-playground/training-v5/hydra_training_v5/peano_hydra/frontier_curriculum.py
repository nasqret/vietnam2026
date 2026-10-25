"""Bounded, authored frontier teachers, not unseen data or autonomous rollouts.

Planning declares routes without QED or construction of an implicit epoch.
Single-route verification supports a caller-owned, bounded streaming/sharded
workflow. Only complete original-goal QED traces yield positive action rows.
An optional second replay actually rejects a declared wrong primitive, checks
transactional state preservation, and finishes the same proof. Its error is
separate recovery evidence, never a negative theorem or positive policy label.

Build/verify/publication callers must supply owned CPU/wall/RSS guards. This
module starts no processes, loads no models, and changes no historical source.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import re
import stat
import tempfile
from typing import TYPE_CHECKING, Iterator

if TYPE_CHECKING:
    from hydra_training_v5.peano_hydra.curriculum import VerifiedCurriculum
    from hydra_training_v5.peano_hydra.epoch import HydraEpoch
    from hydra_training_v5.peano_hydra.posttrain import VerifiedSource


ROOT = Path(__file__).resolve().parents[2]
FRONTIER_SOURCE_SCHEMA = "peano-hydra-native-frontier-curriculum-source-v1"
FRONTIER_PLAN_SCHEMA = "peano-hydra-native-frontier-curriculum-plan-v1"
FRONTIER_EVIDENCE_SCHEMA = "peano-hydra-native-frontier-curriculum-evidence-v1"
RECOVERY_SCHEMA = "peano-hydra-native-frontier-rejected-primitive-v1"
AUTHORITY_PROFILE = "peano-authority-primitive-v1"
SOURCE_FILENAMES = ("epoch.json", "sft.jsonl", "preferences.jsonl", "discovery.jsonl", "manifest.json")
PROFILES = ("smoke", "pilot")
MAX_ROUTES = 1152
MAX_ROUTE_DECISIONS = 24
MAX_TRANSITIONS = 16384
MAX_ROUTE_TRACE_BYTES = 256 * 1024
MAX_SOURCE_BYTES = 64 * 1024**2
MAX_NUMERAL = 6
_AUTHORSHIP = "explicit-native-frontier-teachers-after-public-paired-search-v2-results"
_VARIANTS = tuple((depth, shape, numeral, width) for depth in (1, 2, 3)
                  for shape in range(4) for numeral in (1, 2, 3, 4) for width in (2, 3, 4))
# These are declared authoring groups, NOT independent mathematical lineages.
# Parent references explain known correlation without reusing old source rows.
_FAMILIES = (
    ("frontier_conjunction_chain", "train", "multi_goal_conjunction", ("scale:equality_path", "scale:conjunction_associate")),
    ("frontier_conjunction_rebuild", "train", "multi_goal_conjunction", ("scale:conjunction_swap", "scale:conjunction_associate")),
    ("frontier_local_induction", "train", "available_local_induction", ("scale:inductive_add_mul_zero",)),
    ("frontier_inductive_witness", "train", "witness_and_remaining_conjunction", ("scale:inductive_nested_zero", "scale:nested_existentials")),
    ("frontier_witness_transport", "train", "witness_and_remaining_conjunction", ("scale:existential_transport", "scale:equality_path")),
    ("frontier_witness_recovery", "train", "rejected_primitive_recovery", ("witness:universal_explicit_witness", "scale:conjunction_swap")),
    ("frontier_disjunction_diagnostic", "dev", "exposed_disjunction_diagnostic", ("scale:disjunction_map",)),
    ("frontier_universal_diagnostic", "dev", "exposed_universal_diagnostic", ("scale:universal_specialization",)),
)


class HydraFrontierCurriculumError(ValueError):
    """A frontier candidate lost its declaration, proof or exposure boundary."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise HydraFrontierCurriculumError(message)


def _native():
    # Deliberately lazy: importing the plan API neither freezes a catalog nor
    # initializes Peano, tokenizers, model frameworks, or a proof session.
    from hydra_training_v5.peano_hydra import composition
    return composition


def _digest(value: object) -> str:
    return hashlib.sha256(_native()._canonical(value)).hexdigest()


def _variants(profile: str) -> tuple[tuple[int, int, int, int], ...]:
    _require(type(profile) is str and profile in PROFILES, "unknown frontier curriculum profile")
    return _VARIANTS[:1] if profile == "smoke" else _VARIANTS


def _context(variable: str, depth: int, shape: int, numeral: int) -> str:
    # One variable occurrence per tree keeps one native rewrite one decision.
    term = (f"({variable} + {numeral})", f"({numeral} + {variable})",
            f"({variable} * {numeral + 1})", f"({numeral + 1} * {variable})")[shape]
    for _ in range(depth):
        term = f"S ({term})"
    return term


def _conjunction(parts: tuple[str, ...]) -> str:
    result = parts[-1]
    for part in reversed(parts[:-1]):
        result = f"({part} /\\ {result})"
    return result


def _conjunction_commands(proofs: tuple[tuple[str, ...], ...]) -> tuple[str, ...]:
    return tuple(command for index, proof in enumerate(proofs)
                 for command in (("split",) if index < len(proofs) - 1 else ()) + proof)


def _template(family: str, variant: tuple[int, int, int, int]):
    depth, shape, numeral, width = variant
    def term(variable: str) -> str:
        return _context(variable, depth, shape, numeral)
    a, c = term("a"), term("c")
    equality_parts = (f"{a} = {c}", f"{c} = {a}", f"({a}) + 0 = {c}", f"S ({a}) = S ({c})")[:width]
    zero_add = ("have hz : forall z. 0 + z = z", "intro z", "induction z", "simp", "simp [IH]")
    zero_mul = ("have hm : forall z. 0 * z = 0", "intro z", "induction z", "simp", "simp [IH]")
    if family in {"frontier_conjunction_chain", "frontier_conjunction_rebuild", "frontier_witness_transport"}:
        first, second = ("h_left", "h_right_left") if family == "frontier_conjunction_rebuild" else ("h0", "h1")
        forward = (f"rewrite {first}", f"rewrite {second}", "refl")
        proofs = (forward, ("symm", *forward), (*forward[:-1], "simp"), forward)[:width]
        if family == "frontier_conjunction_rebuild":
            source = f"forall a b c. (a = b /\\ (b = c /\\ {numeral} = {numeral})) -> {_conjunction(equality_parts)}"
            prefix = ("intro a", "intro b", "intro c", "intro h", "cases h", "cases h_right")
        else:
            prefix = ("intro a", "intro b", "intro c", "intro h0", "intro h1")
            target = _conjunction(equality_parts)
            if family == "frontier_witness_transport":
                parts = (f"x = {c}", f"{c} = x", f"x + 0 = {c}", f"S x = S ({c})")[:width]
                target = f"exists x. {_conjunction(parts)}"
                prefix += (f"exists {a}",)
            source = f"forall a b c. a = b -> b = c -> {target}"
        return source, (*prefix, *_conjunction_commands(proofs)), ()
    if family == "frontier_local_induction":
        n = term("n")
        parts = (f"0 + ({n}) = {n}", f"0 * ({n}) = 0",
                 f"0 + (0 * ({n})) = 0", f"0 * (0 + ({n})) = 0")[:width]
        proofs = (("simp [hz]",), ("simp [hm]",), ("simp [hm]",), ("simp [hm]",))[:width]
        return (f"forall n. {_conjunction(parts)}",
                (*zero_add, *zero_mul, "intro n", *_conjunction_commands(proofs)),
                ({"before_step": 3, "command": "rewrite IH", "failure_mode": "unavailable_induction_hypothesis"},))
    if family == "frontier_inductive_witness":
        n = term("n")
        parts = (f"x = {n}", f"0 + x = {n}", f"x + 0 = {n}", f"S x = S ({n})")[:width]
        proofs = (("refl",), ("simp [hz]",), ("simp",), ("refl",))[:width]
        return (f"forall n. exists x. {_conjunction(parts)}",
                (*zero_add, "intro n", f"exists {n}", *_conjunction_commands(proofs)),
                ({"before_step": 7, "command": "split", "failure_mode": "split_before_existential_witness"},))
    if family == "frontier_witness_recovery":
        # Stay off both diagonal values k and k+1: otherwise opposite context
        # shapes collapse to k+k or (k+1)*(k+1) in the closed target.
        assumed = numeral + 2
        closed = term(str(assumed))
        parts = (f"x = {closed}", f"n = {assumed}", f"x + 0 = {closed}", f"S x = S ({closed})")[:width]
        proofs = (("rewrite h", "refl"), ("exact h",), ("rewrite h", "simp"), ("rewrite h", "refl"))[:width]
        mistake = ({"before_step": 3, "command": "split", "failure_mode": "split_before_existential_witness"}
                   if width == 4 else {"before_step": 4, "command": "intro p" if width == 2 else "refl",
                                       "failure_mode": "wrong_primitive_on_remaining_conjunction"})
        return (f"forall n. n = {assumed} -> exists x. {_conjunction(parts)}",
                ("intro n", "intro h", f"exists {term('n')}", *_conjunction_commands(proofs)), (mistake,))
    if family == "frontier_disjunction_diagnostic":
        a, b = term("a"), term("b")
        left = (f"{a} = {b}", f"S ({a}) = S ({b})", f"({a}) + 0 = {b}")[width - 2]
        return (f"forall a b. a = b -> ({left} \\/ {b} = {a})",
                ("intro a", "intro b", "intro h", "left", "rewrite h", "simp" if width == 4 else "refl"), ())
    if family == "frontier_universal_diagnostic":
        def wrapped(variable: str) -> str:
            t = term(variable)
            return (f"({t}) + 0", f"({t}) + (0 + 0)", f"(({t}) + 0) + 0")[width - 2]
        a, b, z = wrapped("a"), wrapped("b"), wrapped("z")
        return (f"forall a b. (forall z. 0 + ({z}) = {z}) -> (0 + ({a}) = {a} /\\ {b} = 0 + ({b}))",
                ("intro a", "intro b", "intro h", "split", "specialize h a", "exact h",
                 "specialize h b", "symm", "exact h"), ())
    raise HydraFrontierCurriculumError("undeclared frontier template")


def _source_identity() -> dict[str, object]:
    native = _native()
    files = dict(native._source_identity()["files"])
    for name in ("training/peano_hydra/frontier_curriculum.py", "training/peano_hydra/composition_scale.py",
                 "training/peano_hydra/comparison.py", "training/peano_hydra/protocol.py",
                 "training/peano_hydra/witness_repair.py"):
        files[name] = hashlib.sha256(native._read(ROOT / name, maximum=2 * 1024**2)).hexdigest()
    files = dict(sorted(files.items()))
    return {"files": files, "source_files_sha256": _digest(files),
            "coverage": "declared generators, exclusion parsers, V4 prompts and native replay sources; not transitive-import or whole-repository attestation"}


@dataclass(frozen=True, slots=True)
class _Context:
    epoch: HydraEpoch
    profile: str
    capabilities: object
    environment: object
    authority: dict
    prompt_contract: dict
    decoder_profile: dict
    source_identity: dict
    excluded: tuple[dict, ...]


def _context_record(epoch: HydraEpoch, profile: str) -> _Context:
    from hydra_training_v5.peano_hydra.epoch import HydraEpoch as Epoch
    from hydra_training_v5.peano_hydra.composition_scale import excluded_comparison_targets
    _variants(profile)
    _require(type(epoch) is Epoch, "frontier requires an explicit frozen HydraEpoch")
    caps, environment, authority, prompt, decoder = _native()._authority(epoch, AUTHORITY_PROFILE)
    return _Context(epoch, profile, caps, environment, authority, prompt, decoder,
                    _source_identity(), excluded_comparison_targets())


def _family_record(context: _Context, index: int) -> dict[str, object]:
    name, split, role, parents = _FAMILIES[index]
    declaration = {"id": name, "split": split, "proof_role": role, "parent_families": list(parents),
                   "authorship": _AUTHORSHIP, "template_version": 1, "semantic_independence_claim": False}
    # Family identity does not change between smoke and pilot: expanding rows
    # must not invent additional independent lineages.
    declaration["lineage_sha256"] = _digest({"epoch_sha256": context.epoch.epoch_sha256,
        "kind": "correlated-authored-frontier-family", "declaration": declaration})
    return declaration


def _route_record(context: _Context, ordinal: int) -> dict[str, object]:
    from hydra_training_v5.peano_hydra.protocol import validate_statement
    from hydra_training_v5.peano_policy.authority import validate_authority_tactic
    variants = _variants(context.profile)
    _require(type(ordinal) is int and 0 <= ordinal < len(_FAMILIES) * len(variants), "invalid frontier route ordinal")
    family_index, seed = divmod(ordinal, len(variants))
    declaration = _family_record(context, family_index)
    variant = variants[seed]
    source, commands, recovery = _template(str(declaration["id"]), variant)
    _require(type(source) is str and len(source.encode()) <= 4096
             and type(commands) is tuple and 1 <= len(commands) <= MAX_ROUTE_DECISIONS,
             "frontier route exceeds its statement/decision bound")
    _require(all(len(token) <= 1 and int(token) <= MAX_NUMERAL
                 for token in re.findall(r"(?<![A-Za-z_0-9'])[0-9]+", source)),
             "frontier route exceeds its small-numeral bound")
    statement = validate_statement(source)
    _require(statement not in {item["statement"] for item in context.excluded}, "frontier target is an excluded comparison goal")
    name = f"hydra_teacher_frontier_{declaration['id'][9:]}_{seed:03d}"
    _require(name not in {item.name for item in context.epoch.theorems}, "frontier route impersonates an enrolled theorem")
    for command in commands:
        _require(type(command) is str and validate_authority_tactic(command, context.environment) == command,
                 "frontier command changed its primitive authority")
    _require(type(recovery) is tuple and len(recovery) <= 1, "too many declared recovery attempts")
    for attempt in recovery:
        _require(type(attempt) is dict and set(attempt) == {"before_step", "command", "failure_mode"}
                 and type(attempt["before_step"]) is int and 1 <= attempt["before_step"] <= len(commands)
                 and type(attempt["failure_mode"]) is str and 0 < len(attempt["failure_mode"]) <= 128,
                 "invalid declared recovery attempt")
        validate_authority_tactic(attempt["command"], context.environment)
    record = {"ordinal": ordinal, "name": name, "family": declaration["id"], "split": declaration["split"],
              "proof_role": declaration["proof_role"], "parent_families": declaration["parent_families"],
              "generator_seed": seed, "variant": list(variant), "curriculum_profile": context.profile,
              "lineage_sha256": declaration["lineage_sha256"], "epoch_sha256": context.epoch.epoch_sha256,
              "source_identity_sha256": context.source_identity["source_files_sha256"],
              "authorship": _AUTHORSHIP, "source": source, "statement": statement,
              "statement_sha256": hashlib.sha256(statement.encode()).hexdigest(),
              "commands": list(commands), "commands_sha256": _digest(list(commands)),
              "recovery_attempts": list(recovery)}
    return {**record, "route_sha256": _digest(record)}


def iter_frontier_routes(epoch: HydraEpoch, *, profile: str = "smoke") -> Iterator[dict[str, object]]:
    """Yield detached, strictly bounded declarations; no native proof execution."""
    context = _context_record(epoch, profile)
    for ordinal in range(len(_FAMILIES) * len(_variants(profile))):
        yield _route_record(context, ordinal)
    _require(_source_identity() == context.source_identity, "frontier source changed during generation")


def iter_frontier_chunks(epoch: HydraEpoch, *, profile: str = "smoke", chunk_size: int = 16):
    _require(type(chunk_size) is int and 1 <= chunk_size <= 64, "frontier chunk size must be 1..64")
    chunk = []
    for route in iter_frontier_routes(epoch, profile=profile):
        chunk.append(route)
        if len(chunk) == chunk_size:
            yield tuple(chunk)
            chunk = []
    if chunk:
        yield tuple(chunk)


def _plan(context: _Context) -> dict[str, object]:
    routes = [_route_record(context, ordinal)
              for ordinal in range(len(_FAMILIES) * len(_variants(context.profile)))]
    _require(len(routes) <= MAX_ROUTES and len({row["statement"] for row in routes}) == len(routes)
             and len({row["name"] for row in routes}) == len(routes), "duplicate or excessive frontier routes")
    decisions = sum(len(row["commands"]) for row in routes)
    _require(decisions <= MAX_TRANSITIONS, "frontier plan exceeds the complete source-row bound")
    families = [_family_record(context, index) for index in range(len(_FAMILIES))]
    parent_sets = {split: {parent for family in families if family["split"] == split
                          for parent in family["parent_families"]} for split in ("train", "dev")}
    _require(not parent_sets["train"] & parent_sets["dev"], "known frontier parent family crosses the diagnostic split")
    body = {"schema": FRONTIER_PLAN_SCHEMA, "curriculum_profile": context.profile,
            "epoch_sha256": context.epoch.epoch_sha256, "authority_profile": AUTHORITY_PROFILE,
            "authority": context.authority, "prompt_contract": context.prompt_contract,
            "decoder_profile": context.decoder_profile, "source_identity": context.source_identity,
            "families": families, "routes": routes, "route_count": len(routes),
            "tactic_decisions": decisions, "transition_count": decisions,
            "split_route_counts": {split: sum(row["split"] == split for row in routes) for split in ("train", "dev")},
            "split_transition_counts": {split: sum(len(row["commands"]) for row in routes if row["split"] == split)
                                         for split in ("train", "dev")},
            "declared_recovery_attempts": sum(len(row["recovery_attempts"]) for row in routes),
            "variant_axes": ["successor_depth", "single_occurrence_term_shape", "small_numeral", "conjunction_width_or_diagnostic_shape"],
            "split_policy": _native().COMPOSITION_SPLIT_POLICY,
            "excluded_targets": list(context.excluded), "excluded_targets_sha256": _digest(context.excluded),
            "limits": {"max_routes": MAX_ROUTES, "max_route_decisions": MAX_ROUTE_DECISIONS,
                       "max_source_rows": MAX_TRANSITIONS, "max_numeral": MAX_NUMERAL,
                       "max_route_trace_bytes": MAX_ROUTE_TRACE_BYTES, "max_source_bytes": MAX_SOURCE_BYTES,
                       "max_wrong_attempts_per_route": 1, "max_recovery_replay_decisions": MAX_ROUTE_DECISIONS + 1},
            "exposure": {"authorship": _AUTHORSHIP, "guided_teacher_proofs": True, "model_generated": False,
                         "public_and_correlated": True, "declared_family_groups_are_mathematical_components": False,
                         "common_exposure_component_sha256": _digest({"epoch_sha256": context.epoch.epoch_sha256,
                             "authorship": _AUTHORSHIP, "families": families}),
                         "parent_references_are_new_native_templates_not_old_data_imports": True,
                         "exact_public_comparison_target_exclusion": True, "exact_historical_target_exclusion": True,
                         "closed_intermediate_target_exclusion_required": True,
                         "semantic_equivalence_complete": False, "independent_human_review": False,
                         "eligible_for_unseen_model_comparison": False, "sealed_benchmark": False,
                         "research_claim_eligible": False, "alpha_admitted": False, "dag_mutated": False,
                         "model_facing_split_review_pending": True},
            "recovery_policy": {"failed_actions_are_positive_labels": False, "negative_theorem_claim": False,
                                "student_generated": False, "state_preservation_required": True,
                                "same_original_goal_complete_qed_required": True}}
    return {**body, "plan_sha256": _digest(body)}


def frontier_plan(epoch: HydraEpoch, *, profile: str = "smoke") -> dict[str, object]:
    """Plan only; the caller supplies the epoch and no theorem is replayed."""
    context = _context_record(epoch, profile)
    plan = _plan(context)
    _require(_source_identity() == context.source_identity, "frontier source changed during planning")
    return plan


@dataclass(frozen=True, slots=True)
class VerifiedFrontierRoute:
    route: dict[str, object]
    transitions: tuple[dict[str, object], ...]
    evidence: dict[str, object]
    recovery_attempts: tuple[dict[str, object], ...]


def _recovery(context: _Context, route: dict, clean, attempt: dict) -> dict[str, object]:
    native = _native()
    index = attempt["before_step"] - 1
    commands = tuple(route["commands"])
    attempted = (*commands[:index], attempt["command"], *commands[index:])
    result = native.run_proof(route["source"], attempted, request_id=route["name"] + "-recovery",
        session_id=route["name"] + "-recovery", classical=False, on_error="continue",
        capabilities=context.capabilities, trace_byte_limit=MAX_ROUTE_TRACE_BYTES)
    _require(type(result) is native.BatchResult and result.status == "proved" and result.kernel_checked is True
             and result.theorem == route["statement"] and result.goals == () and result.failed_tactics == 1
             and result.tactics_applied == len(commands) and result.tactics_requested == len(attempted)
             and result.engine_steps == clean.engine_steps and result.proof_nodes == clean.proof_nodes
             and result.surface == context.capabilities.label and result.environment_sha256 == context.environment.sha256
             and result.classical is False and result.on_error == "continue"
             and result.error is None and result.error_type is None and result.failed_step is None,
             "recovery must contain exactly one real rejection and the unchanged complete original-goal QED")
    _require(type(result.trace) is tuple and len(result.trace) == len(commands) + 2,
             "recovery trace has an incomplete inventory")
    failed = result.trace[index]
    _require(type(failed) is dict and failed.get("status") == "error"
             and failed.get("tactic") == attempt["command"] and failed.get("step") == index + 1
             and failed.get("session") == result.session_id
             and type(failed.get("error")) is str and 0 < len(failed["error"].encode()) <= 4096
             and failed.get("goals_before") == failed.get("goals_after") == clean.trace[index]["goals_before"]
             and failed.get("focus") == clean.trace[index]["focus"],
             "rejected primitive did not preserve its exact complete proof state")
    successful = (*result.trace[:index], *result.trace[index + 1:-1])
    for step, (actual, expected) in enumerate(zip(successful, clean.trace[:-1]), 1):
        _require(type(actual) is dict and actual.get("step") == step + (step > index)
                 and actual.get("session") == result.session_id
                 and {k: v for k, v in actual.items() if k not in {"session", "step"}}
                 == {k: v for k, v in expected.items() if k not in {"session", "step"}},
                 "recovery changed the clean successful continuation")
    footer = result.trace[-1]
    _require(type(footer) is dict and footer.get("qed") is True and footer.get("theorem") == route["statement"]
             and footer.get("proof_size") == clean.proof_nodes and footer.get("tactic_count") == len(attempted),
             "recovery lost its original-goal checked footer")
    body = {"schema": RECOVERY_SCHEMA, "route_sha256": route["route_sha256"], "attempt": dict(attempt),
            "failed_trace": failed, "trace_sha256": _digest(result.trace),
            "clean_trace_sha256": _digest(clean.trace), "successful_commands_sha256": route["commands_sha256"],
            "commands_with_rejection_sha256": _digest(attempted), "kernel_checked_after_recovery": True,
            "proof_nodes": result.proof_nodes, "state_and_history_transaction_checked_by_batch": True,
            "positive_policy_label": False, "negative_theorem_claim": False, "student_generated": False,
            "authorship": "declared wrong primitive actually executed in a separate native proof session"}
    return {**body, "recovery_sha256": _digest(body)}


def _verify_route(context: _Context, route: dict[str, object]) -> VerifiedFrontierRoute:
    native = _native()
    _require(type(route) is dict, "frontier route must be an exact declaration")
    expected = _route_record(context, route.get("ordinal"))
    _require(native._canonical(route) == native._canonical(expected), "frontier route has altered or stale declaration/provenance")
    result = native.run_proof(route["source"], tuple(route["commands"]), request_id=route["name"],
        session_id=route["name"], classical=False, on_error="stop", capabilities=context.capabilities,
        trace_byte_limit=MAX_ROUTE_TRACE_BYTES)
    native._checked_result(result, route, caps=context.capabilities, environment_sha256=context.environment.sha256)
    rows = native._rows(context.epoch, route, result, context.environment)
    from hydra_training_v5.peano_hydra.witness_repair import _check_intermediates
    _check_intermediates(rows, {row["statement"] for row in context.excluded})
    recovery = tuple(_recovery(context, route, result, attempt) for attempt in route["recovery_attempts"])
    evidence = {"name": route["name"], "route_sha256": route["route_sha256"], "statement": route["statement"],
                "commands_sha256": route["commands_sha256"], "family": route["family"],
                "lineage_sha256": route["lineage_sha256"], "proof_role": route["proof_role"],
                "parent_families": route["parent_families"], "kernel_checked": True, "proof_nodes": result.proof_nodes,
                "trace_sha256": _digest(result.trace), "transitions_sha256": _digest(rows),
                "recovery_attempts": list(recovery)}
    return VerifiedFrontierRoute(expected, rows, evidence, recovery)


def verify_frontier_route(epoch: HydraEpoch, route: dict[str, object], *, profile: str = "smoke") -> VerifiedFrontierRoute:
    """Recheck one declared route; suitable for an externally bounded shard worker."""
    context = _context_record(epoch, profile)
    result = _verify_route(context, route)
    _require(_source_identity() == context.source_identity, "frontier source changed during single-route verification")
    return result


def _check_splits(rows: tuple[dict, ...], plan: dict) -> None:
    declared = {item["id"]: (item["split"], item["lineage_sha256"]) for item in plan["families"]}
    seen = {}
    for row in rows:
        _require((row["split"], row["lineage_sha256"]) == declared.get(row["family"]), "frontier family split/lineage changed")
        key = (row["environment_sha256"], row["state_sha256"], row["focus"], row["action"])
        _require(key not in seen or seen[key] == row["split"], "frontier exact state/action crosses the diagnostic split")
        seen[key] = row["split"]
    _require(dict(Counter(row["split"] for row in rows)) == plan["split_transition_counts"], "frontier split row counts changed")


@dataclass(frozen=True, slots=True)
class FrontierSource:
    epoch: HydraEpoch
    curriculum: VerifiedCurriculum
    manifest: dict[str, object]
    payloads: dict[str, bytes]


def build_frontier_source(epoch: HydraEpoch, *, profile: str = "smoke") -> FrontierSource:
    """Full bounded candidate build; no implicit split review or model admission."""
    from hydra_training_v5.peano_hydra.curriculum import VerifiedCurriculum, encode_jsonl
    context = _context_record(epoch, profile)
    plan = _plan(context)
    rows, evidence, retained_bytes = [], [], 0
    for route in plan["routes"]:
        verified = _verify_route(context, route)
        retained_bytes += len(encode_jsonl(verified.transitions)) + len(_native()._canonical(verified.evidence)) + 1
        _require(retained_bytes <= MAX_SOURCE_BYTES, "frontier retained rows/evidence exceed the byte bound")
        rows.extend(verified.transitions)
        evidence.append(verified.evidence)
    transitions = tuple(rows)
    _require(len(transitions) == plan["tactic_decisions"] <= MAX_TRANSITIONS, "frontier lost a declared positive transition")
    _check_splits(transitions, plan)
    curriculum = VerifiedCurriculum(epoch.epoch_sha256, transitions, (), ())
    manifest = curriculum.manifest()
    manifest.update({"schema": FRONTIER_SOURCE_SCHEMA, "curriculum_profile": profile,
        "epoch_graph_storage": "exact-rehashed-source-catalogs; digest-and-count-reference-only",
        "version": epoch.version, "edition_identity_sha256": epoch.edition_identity_sha256,
        "theorem_dag_sha256": epoch.theorem_dag_sha256, "reviewed_definition_dag_sha256": epoch.reviewed_definition_dag_sha256,
        "authority_profile": AUTHORITY_PROFILE, "authority": plan["authority"], "prompt_contract": plan["prompt_contract"],
        "decoder_profile": plan["decoder_profile"], "split_policy": plan["split_policy"], "exposure": plan["exposure"],
        "composition": {"schema": FRONTIER_EVIDENCE_SCHEMA, "plan": plan, "teacher_routes": evidence,
            "verified_route_count": len(evidence), "verified_tactic_decisions": len(transitions), "transition_count": len(transitions),
            "verified_recovery_attempts": sum(len(item["recovery_attempts"]) for item in evidence),
            "family_route_counts": dict(sorted(Counter(row["family"] for row in plan["routes"]).items())),
            "exact_cross_split_state_action_overlaps": 0, "excluded_closed_intermediate_hits": 0,
            "exact_original_target_overlaps": 0, "repeated_routes_added": 0,
            "independent_verification": "regenerate all declared original-goal QEDs and transactional recovery attempts",
            "publication_verification_scope": "same caller process, fresh native sessions; not independent-process attestation"},
        "proof_optimization_claim": "none; authored frontier teachers, not autonomous or minimum-length proofs",
        "discovery_claim": "none; no theorem admission or unseen-model improvement",
        "open_research_gates": ["H0 full reference/conformance scope", "H1 independently reviewed sealed benchmark", "H5 unseen model advantage"]})
    native = _native()
    # Compact metadata preserves every native proof/recovery field while
    # avoiding megabytes of indentation at pilot scale. Human inspection can
    # pretty-print individual routes; legacy source encodings are untouched.
    # The primitive teacher authority imports no catalog theorem. Bind the
    # canonical source DAGs by their exact hashes/counts instead of duplicating
    # every catalog statement into this dataset. Verification below still
    # freezes and authenticates those complete source catalogs afresh.
    payloads = {"epoch.json": native._canonical(epoch.to_dict(include_graphs=False)) + b"\n",
                "sft.jsonl": encode_jsonl(transitions), "preferences.jsonl": b"", "discovery.jsonl": b"",
                "manifest.json": native._canonical(manifest) + b"\n"}
    sizes = {name: len(raw) for name, raw in payloads.items()}
    _require(sum(sizes.values()) <= MAX_SOURCE_BYTES,
             "frontier complete source exceeds 64 MiB: " + str(sizes))
    _require(_source_identity() == context.source_identity, "frontier source changed during full verification")
    return FrontierSource(epoch, curriculum, manifest, payloads)


def _directory(path: Path, *, fresh: bool = False) -> Path:
    _require(isinstance(path, Path), "frontier directory must be an explicit Path")
    path = path.absolute()
    _require(".." not in path.parts and not path.is_symlink() and not any(p.is_symlink() for p in path.parents),
             "frontier directory has traversal or symlink components")
    _require(not path.exists() if fresh else path.is_dir(), "frontier destination exists" if fresh else "frontier directory is missing")
    return path


def _read_source(directory: Path) -> dict[str, bytes]:
    directory = _directory(directory)
    before = directory.stat()
    seen = set()
    with os.scandir(directory) as entries:
        for entry in entries:
            _require(entry.name in SOURCE_FILENAMES and entry.is_file(follow_symlinks=False)
                     and not entry.is_symlink(), "frontier source has an unexpected/unsafe inventory entry")
            seen.add(entry.name)
    _require(seen == set(SOURCE_FILENAMES), "frontier source inventory is incomplete")
    result, total = {}, 0
    for name in SOURCE_FILENAMES:
        target = directory / name
        _require(target.stat(follow_symlinks=False).st_nlink == 1, "frontier source must not contain hard links")
        raw = _native()._read(target, maximum=MAX_SOURCE_BYTES - total)
        total += len(raw)
        result[name] = raw
    after = directory.stat()
    _require((before.st_dev, before.st_ino, before.st_mtime_ns, before.st_ctime_ns)
             == (after.st_dev, after.st_ino, after.st_mtime_ns, after.st_ctime_ns), "frontier source directory changed while reading")
    return result


def publish_frontier_source(source: FrontierSource, directory: Path) -> Path:
    """Atomically publish fresh only after exact full native regeneration."""
    from hydra_training_v5.peano_policy.manifest import publish_staged_directory_noreplace
    _require(type(source) is FrontierSource, "frontier publication requires a complete FrontierSource")
    directory = _directory(directory, fresh=True)
    fresh = build_frontier_source(source.epoch, profile=source.manifest.get("curriculum_profile"))
    _require(source == fresh, "frontier publication refuses altered or stale source evidence")
    _directory(directory, fresh=True)
    directory.parent.mkdir(parents=True, exist_ok=True)
    _directory(directory.parent)
    staging = Path(tempfile.mkdtemp(prefix=f".{directory.name}.partial-", dir=directory.parent))
    for name in SOURCE_FILENAMES:
        with (staging / name).open("xb") as stream:
            stream.write(fresh.payloads[name])
            stream.flush()
            os.fsync(stream.fileno())
    _directory(directory, fresh=True)
    # Failed staging is retained, never cleaned by deleting existing user data.
    publish_staged_directory_noreplace(staging, directory)
    return directory


def verify_frontier_source(directory: Path) -> VerifiedSource:
    """Exact current epoch, source/provenance bytes and full fresh native QEDs."""
    from hydra_training_v5.peano_hydra.epoch import freeze_epoch
    from hydra_training_v5.peano_hydra.posttrain import VerifiedSource
    directory = _directory(directory)
    saved = _read_source(directory)
    manifest = _native()._decode(saved["manifest.json"])
    _require(manifest.get("schema") == FRONTIER_SOURCE_SCHEMA and manifest.get("authority_profile") == AUTHORITY_PROFILE,
             "frontier source requires its distinct schema and primitive authority")
    profile = manifest.get("curriculum_profile")
    _variants(profile)
    epoch = freeze_epoch(ROOT)
    _require(_native()._canonical(_native()._decode(saved["epoch.json"]))
             == _native()._canonical(epoch.to_dict(include_graphs=False)), "frontier source epoch changed")
    composition = manifest.get("composition")
    _require(type(composition) is dict, "frontier source has no exact composition evidence")
    _require(_native()._canonical(composition.get("plan"))
             == _native()._canonical(frontier_plan(epoch, profile=profile)),
             "frontier saved declaration/provenance is stale or altered")
    fresh = build_frontier_source(epoch, profile=profile)
    _require(saved == fresh.payloads, "frontier source bytes differ from complete native regeneration")
    _require(_read_source(directory) == saved, "frontier source changed during verification")
    return VerifiedSource(directory, epoch, fresh.curriculum, fresh.manifest, saved)


__all__ = ["FRONTIER_SOURCE_SCHEMA", "FRONTIER_PLAN_SCHEMA", "FRONTIER_EVIDENCE_SCHEMA", "RECOVERY_SCHEMA",
           "AUTHORITY_PROFILE", "PROFILES", "SOURCE_FILENAMES", "HydraFrontierCurriculumError", "FrontierSource",
           "VerifiedFrontierRoute", "frontier_plan", "iter_frontier_routes", "iter_frontier_chunks",
           "verify_frontier_route", "build_frontier_source", "publish_frontier_source", "verify_frontier_source"]
