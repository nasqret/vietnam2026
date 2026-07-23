"""Frozen combinator catalogue for the browser ``ch lib`` command.

Generated from the desktop ``lambda_lab/lab/curry_howard/library.py`` with
the i18n description keys resolved to their English strings (the browser
build has no i18n). ``type_str`` is ``None`` for combinators that are not
typeable in STLC (Y, O). Do not edit by hand; regenerate from the desktop.
"""

# (name, aliases, lambda_src, type_str, lean_src, description)
COMBINATORS = [
    ("id", ["I", "identity"], r"\x. x", "α → α",
     "fun x => x",
     "Identity - returns its argument unchanged; logically: `P -> P`."),
    ("K", ["const", "konst"], r"\x y. x", "α → β → α",
     "fun x _ => x",
     "Constant - takes two arguments, returns the first; logically: `P -> Q -> P`."),
    ("S", [], r"\x y z. x z (y z)", "(α → β → γ) → (α → β) → α → γ",
     "fun x y z => x z (y z)",
     "Substitutor - distributes the argument to f and g; logically Hilbert's S."),
    ("B", ["compose", "comp"], r"\f g x. f (g x)", "(β → γ) → (α → β) → α → γ",
     "fun f g x => f (g x)",
     "Composition - the classic f . g; logically transitivity of implication."),
    ("C", ["flip"], r"\f x y. f y x", "(α → β → γ) → β → α → γ",
     "fun f x y => f y x",
     "Flip - swaps the order of two arguments."),
    ("Y", ["fix", "fixpoint"], r"\f. (\x. f (x x)) (\x. f (x x))", None,
     "-- Y combinator is not typeable in STLC / Lean's type theory",
     "Fixed point - recursion in unhypothesised lambda; untypeable in STLC."),
    ("fst", ["first", "proj1"], r"\x y. x", "α → β → α",
     "fun x _ => x",
     "First projection - alias of K (for a curried pair)."),
    ("snd", ["second", "proj2"], r"\x y. y", "α → β → β",
     "fun _ y => y",
     "Second projection - K I; takes two, returns the second."),
    ("app", ["apply"], r"\f x. f x", "(α → β) → α → β",
     "fun f x => f x",
     "Application - explicitly `\\f x. f x`; eta-expansion of identity."),
    ("const", ["constant"], r"\x y. x", "α → β → α",
     "fun x _ => x",
     "Synonym for K."),
    ("W", ["dup"], r"\f x. f x x", "(α → α → β) → α → β",
     "fun f x => f x x",
     "Duplicator - `\\f x. f x x`; feeds `x` to `f` twice."),
    ("O", ["owl"], r"\f g. g (f g)", None,
     "-- 'owl' does not typecheck in STLC without polymorphism",
     "Owl - `\\f g. g (f g)`; not typeable in STLC without polymorphism."),
]


def _make_lib():
    out = {}
    for name, aliases, lam, ty, lean, desc in COMBINATORS:
        entry = {
            "name": name,
            "aliases": aliases,
            "lambda_src": lam,
            "type_str": ty,
            "lean_src": lean,
            "description": desc,
        }
        out[name] = entry
        for a in aliases:
            out[a] = entry
    return out


LIBRARY = _make_lib()


def canonical_names():
    """Canonical names (without aliases), in insertion order."""
    return [name for name, *_ in COMBINATORS]


def lookup(name):
    return LIBRARY.get(name)
