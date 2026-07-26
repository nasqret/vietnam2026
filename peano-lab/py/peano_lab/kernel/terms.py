"""PA terms: x | 0 | S t | t + t | t * t.

Kernel representation uses de Bruijn indices; the surface syntax is named.
Must provide (signatures are binding, implementations are M0 work):

    class Term: ...                     # frozen dataclasses: Var(int), Zero, Succ, Add, Mul
    def parse_term(src: str) -> Term    # numerals are sugar: "3" -> S(S(S(0)))
    def pretty_term(t: Term, names: list[str]) -> str   # CANONICAL: one output per term
"""

raise NotImplementedError("M0")
