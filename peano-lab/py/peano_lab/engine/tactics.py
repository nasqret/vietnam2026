"""Primitive tactics. Contract: Tactic = (ProofState, args: str) -> ProofState;
raise TacticError(final English) with state guaranteed unchanged on failure.
M1: refl symm trans congr exact assumption rewrite. M2: induction intro(∀)
specialize. M3: intro apply split left right cases exfalso exists classical.
"""

raise NotImplementedError("M1")
