"""Interactive Curry-Howard proof builder — browser port.

Since the 2026-07-24 audit this module is a thin facade: ``ch build`` and
``prove`` share ONE sound engine, :mod:`lambda_lab.lab.webport.proof_builder`
(P0.1 checked finalization, P0.2 rigid atoms vs. metavariables, P0.3
proof-wide substitution, P0.4 free-variable rejection). Everything here is a
re-export so existing imports keep working.
"""

from __future__ import annotations

from .proof_builder import (  # noqa: F401
    Goal,
    InvalidProof,
    PartialTerm,
    ProofState,
    Step,
    TACTIC_NAMES,
    TacticError,
    apply_,
    apply_tactic,
    assumption,
    checked_final,
    exact,
    hint,
    holes_in,
    intro,
    intros,
    invariants_ok,
    is_valid_binder,
    refine,
    start,
    undo,
)
