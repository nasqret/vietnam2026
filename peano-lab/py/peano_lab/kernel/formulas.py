"""PA formulas: t = t | ⊥ | φ→φ | φ∧φ | φ∨φ | ∀x.φ | ∃x.φ ; ¬φ := φ→⊥.

    class Formula: ...                  # Eq, Bot, Imp, And, Or, Forall, Exists
    def parse_formula(src: str) -> Formula
    def pretty_formula(f: Formula, names: list[str]) -> str   # canonical, deterministic
"""

raise NotImplementedError("M0")
