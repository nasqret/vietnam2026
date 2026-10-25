"""Bounded observations of an existing proof graph, never proof validation.

The three main counts have the frozen engine's meanings: distinct ``Proof``
objects by identity, tree occurrences with sharing expanded, and root-at-one
proof depth. Embedded terms/formulas, history, context and Python allocation
overhead are excluded. These counts are not an RSS measurement.

Pass ``stage='partial'`` for the current uncompiled partial certificate and
``stage='final'`` only for the actual final certificate. Nothing here performs
substitution, local-cut compilation, normalization or kernel checking. In
particular, a partial count is not a prediction of the final certificate:
LocalHave/LocalSuffices are inlined by the frozen compiler, while Cut survives.
"""
from __future__ import annotations

from dataclasses import dataclass, fields

from peano_lab.kernel import proofs as p
from peano_lab.engine.proof_reduction import LocalHave, LocalSuffices
from peano_lab.engine.state import Hole


POLICY = "hydra-proof-cost-observation-v1"


@dataclass(frozen=True, slots=True)
class ProofCostLimits:
    max_objects: int = 100_000
    max_occurrences: int = 500_000
    max_depth: int = 256
    max_work: int = 500_000

    def __post_init__(self):
        for name, maximum in (("max_objects", 100_000), ("max_occurrences", 500_000),
                              ("max_depth", 256), ("max_work", 500_000)):
            value = getattr(self, name)
            if type(value) is not int or not 1 <= value <= maximum:
                raise ValueError(name + " must be a positive integer at most " + str(maximum))


DEFAULT_LIMITS = ProofCostLimits()
_CHILD_FIELDS = {
    p.Hyp: (), p.Axiom: (), p.DNE: (), p.EqRefl: (), Hole: (),
    p.ImpIntro: ("body",), p.ImpElim: ("f", "a"),
    p.Cut: ("lemma", "body"), p.AndIntro: ("left", "right"),
    p.AndElimL: ("pair",), p.AndElimR: ("pair",),
    p.OrIntroL: ("proof",), p.OrIntroR: ("proof",),
    p.OrElim: ("disjunction", "left_case", "right_case"),
    p.BotElim: ("absurdity",), p.ForallIntro: ("body",),
    p.ForallElim: ("p",), p.ExistsIntro: ("p",), p.ExistsElim: ("p", "body"),
    p.EqSym: ("proof",), p.EqTrans: ("first", "second"), p.CongS: ("proof",),
    p.CongAdd: ("left", "right"), p.CongMul: ("left", "right"),
    p.EqSubst: ("eq_proof", "body_proof"), p.Ind: ("base", "step"),
    LocalHave: ("proof", "body"), LocalSuffices: ("body", "proof"),
}
_FIELDS = {kind: tuple(field.name for field in fields(kind)) for kind in _CHILD_FIELDS}
_METRICS = ("distinct_objects", "structural_occurrences", "depth")


def measure_proof(proof, *, stage, limits=DEFAULT_LIMITS, should_stop=None):
    """Return JSON-safe observations; an unavailable count is None, never zero.

    ``stage`` is an explicit caller label, not a proof-authority claim. A final
    snapshot containing a Hole or local scheduler is rejected. Otherwise this
    helper does not establish that the object is a final or valid certificate.

    A memoized iterative traversal costs O(distinct objects + proof edges), not
    the potentially exponential number of structural occurrences. Saturating
    arithmetic avoids constructing huge integers. On a bound or cancellation,
    exact unavailable counts remain None and observed lower bounds are marked
    separately. Limits only bound this diagnostic; they do not change the
    engine's proof limits or decide admission.
    """
    if type(stage) is not str or stage not in ("partial", "final"):
        raise ValueError("proof stage must be explicitly partial or final")
    if type(limits) is not ProofCostLimits:
        raise TypeError("limits must be ProofCostLimits")
    if not isinstance(proof, p.Proof):
        raise TypeError("measure_proof expects a native proof object")
    if should_stop is not None and not callable(should_stop):
        raise TypeError("should_stop must be callable")

    # Retain original objects strongly: no equality, recursive hashing, or id
    # reuse participates in object accounting.
    nodes, summaries, active = {}, {}, set()
    pending = [(proof, False, 1)]
    work = edges = visits = object_lower = depth_lower = occurrence_lower = 0
    has_holes = has_local = False

    def report(status, reason=None, *, graph_complete=False):
        root = summaries.get(id(proof)) if graph_complete else None
        values = {
            "distinct_objects": len(nodes) if graph_complete else None,
            "structural_occurrences": root[0] if root and root[0] <= limits.max_occurrences else None,
            "depth": root[1] if root and root[1] <= limits.max_depth else None,
        }
        lower = {"distinct_objects": len(nodes) if graph_complete else object_lower,
                 "structural_occurrences": root[0] if root else occurrence_lower,
                 "depth": root[1] if root else depth_lower}
        return {
            "policy": POLICY, "kind": "observed_proof_structure", "stage": stage,
            "status": status, "reason": reason,
            **values, "exact": {key: values[key] is not None for key in _METRICS},
            "lower_bounds": lower,
            "proof_edges": edges if graph_complete else None,
            "reused_references": max(0, edges - len(nodes) + 1) if graph_complete else None,
            "contains_holes": True if has_holes else (False if graph_complete else None),
            "contains_local_schedulers": True if has_local else (False if graph_complete else None),
            "work_units": work,
            "limits": {field.name: getattr(limits, field.name) for field in fields(limits)},
            "counts_scope": "Proof objects only; excludes term/formula payloads, context and history",
            "normalization_performed": False, "proof_check_performed": False,
        }

    while pending:
        if should_stop is not None and work % 64 == 0 and should_stop():
            return report("cancelled", "caller_stop")
        if work >= limits.max_work:
            return report("limited", "work")
        node, leaving, depth = pending.pop()
        work += 1
        identity = id(node)
        if leaving:
            children = nodes[identity][1]
            size = min(limits.max_occurrences + 1,
                       1 + sum(summaries[id(child)][0] for child in children))
            height = 1 + max((summaries[id(child)][1] for child in children), default=0)
            summaries[identity] = (size, height)
            occurrence_lower = max(occurrence_lower, size)
            active.remove(identity)
            continue

        visits += 1
        occurrence_lower = max(occurrence_lower, visits)
        depth_lower = max(depth_lower, depth)
        if identity in active:
            return report("invalid", "cycle")
        if identity in summaries:
            continue
        object_lower = max(object_lower, len(nodes) + 1)
        if depth > limits.max_depth:
            return report("limited", "depth")
        if len(nodes) >= limits.max_objects:
            return report("limited", "objects")
        kind = type(node)
        if kind not in _CHILD_FIELDS:
            return report("unsupported", "proof_constructor")
        if kind is Hole:
            has_holes = True
        if kind in (LocalHave, LocalSuffices):
            has_local = True
        if stage == "final" and (has_holes or has_local):
            raise ValueError("a final snapshot cannot contain holes or local proof schedulers")
        try:
            children = tuple(getattr(node, name) for name in _CHILD_FIELDS[kind])
            # Match the native walker exactly for supported, well-shaped
            # constructors; do not silently miss a Proof in a payload slot.
            actual = tuple(name for name in _FIELDS[kind] if isinstance(getattr(node, name), p.Proof))
        except AttributeError:
            return report("invalid", "missing_proof_field")
        if actual != _CHILD_FIELDS[kind]:
            return report("invalid", "proof_field_shape")
        nodes[identity] = (node, children)
        active.add(identity)
        edges += len(children)
        pending.append((node, True, depth))
        pending.extend((child, False, depth + 1) for child in reversed(children))

    size, depth = summaries[id(proof)]
    limited = [name for name, value, maximum in
               (("occurrences", size, limits.max_occurrences), ("depth", depth, limits.max_depth))
               if value > maximum]
    return report("limited" if limited else "complete", ",".join(limited) or None,
                  graph_complete=True)


__all__ = ["POLICY", "ProofCostLimits", "DEFAULT_LIMITS", "measure_proof"]
