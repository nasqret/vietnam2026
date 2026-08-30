"""Small, deterministic teaching cards for the Peano Lab knowledge base.

The knowledge base is deliberately plain data.  It imports no prover code,
performs no I/O, and makes no mathematical claim depend on the tactic layer.
That keeps the browser renderer replaceable and the prose straightforward to
test.  Card order is part of the public presentation: axioms first, then the
architectural and metamathematical ideas needed to understand the lab.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


_SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")


@dataclass(frozen=True, slots=True)
class KBCard:
    """One immutable, terminal-friendly knowledge-base entry."""

    slug: str
    title: str
    summary: str
    body: str
    related_commands: tuple[str, ...]
    keywords: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if type(self.slug) is not str or _SLUG.fullmatch(self.slug) is None:
            raise ValueError("a KB slug must be lowercase ASCII words joined by hyphens")
        for label, value in (
            ("title", self.title),
            ("summary", self.summary),
            ("body", self.body),
        ):
            if type(value) is not str or not value.strip():
                raise ValueError(f"a KB card needs non-empty {label} text")
        if (
            type(self.related_commands) is not tuple
            or not self.related_commands
            or not all(
                type(command) is str and command.strip()
                for command in self.related_commands
            )
        ):
            raise ValueError("related commands must be a tuple of non-empty strings")
        if type(self.keywords) is not tuple or not all(
            type(keyword) is str and keyword.strip() for keyword in self.keywords
        ):
            raise ValueError("keywords must be a tuple of non-empty strings")


CARDS: tuple[KBCard, ...] = (
    KBCard(
        slug="pa1",
        title="PA1 — zero is not a successor",
        summary="No successor is equal to zero.",
        body=(
            "Formal rule constant: ∀x. ¬(S x = 0), where ¬A abbreviates "
            "A → ⊥. PA1 separates zero from every number visibly built with S. "
            "It does not by itself prove that every nonzero number is a successor; "
            "that is a different statement requiring a derivation."
        ),
        related_commands=("pa axioms", "pa prove forall x. ~(S x = 0)"),
        keywords=("axiom", "successor", "zero", "nonzero"),
    ),
    KBCard(
        slug="pa2",
        title="PA2 — successor is injective",
        summary="Equal successors have equal predecessors.",
        body=(
            "Formal rule constant: ∀x y. S x = S y → x = y. This is injectivity, "
            "not a cancellation heuristic: a proof uses the PA2 certificate and "
            "ordinary implication and universal-elimination rules. The converse "
            "x = y → S x = S y is supplied by equality congruence, not by PA2."
        ),
        related_commands=("pa axioms", "pa tactic apply", "pa tactic congr"),
        keywords=("axiom", "successor", "injective", "equality"),
    ),
    KBCard(
        slug="pa3",
        title="PA3 — addition at zero",
        summary="Adding zero on the right leaves a number unchanged.",
        body=(
            "Formal rule constant: ∀x. x + 0 = x. Together with PA4, this defines "
            "addition by recursion on its second argument. The direction matters "
            "pedagogically: x + 0 = x is immediate from PA3, whereas 0 + x = x "
            "is proved by induction on x."
        ),
        related_commands=("pa axioms", "pa tactic rewrite", "pa tactic simp"),
        keywords=("axiom", "addition", "zero", "recursive equation"),
    ),
    KBCard(
        slug="pa4",
        title="PA4 — addition at a successor",
        summary="Addition recurses through a successor in its right argument.",
        body=(
            "Formal rule constant: ∀x y. x + S y = S (x + y). PA4 exposes one "
            "recursive step of addition. Peano Lab orients it from left to right "
            "in the built-in simplifier, and every use still contributes an "
            "instantiated PA4 proof to the final certificate."
        ),
        related_commands=("pa axioms", "pa tactic rewrite", "pa tactic simp"),
        keywords=("axiom", "addition", "successor", "recursive equation"),
    ),
    KBCard(
        slug="pa5",
        title="PA5 — multiplication at zero",
        summary="Multiplying by zero on the right gives zero.",
        body=(
            "Formal rule constant: ∀x. x · 0 = 0. Together with PA6, this defines "
            "multiplication by recursion on its second argument. Thus x · 0 = 0 "
            "is an axiom instance, while 0 · x = 0 is a theorem normally obtained "
            "by induction."
        ),
        related_commands=("pa axioms", "pa tactic rewrite", "pa tactic simp"),
        keywords=("axiom", "multiplication", "zero", "recursive equation"),
    ),
    KBCard(
        slug="pa6",
        title="PA6 — multiplication at a successor",
        summary="Multiplication recurses by one addition in its right argument.",
        body=(
            "Formal rule constant: ∀x y. x · S y = x · y + x. Notice the exact "
            "operand order: the recursive product comes first. The built-in simp "
            "orientation can make the syntax tree larger, so termination cannot "
            "be justified by node count alone."
        ),
        related_commands=("pa axioms", "pa tactic rewrite", "pa tactic simp"),
        keywords=("axiom", "multiplication", "successor", "recursive equation"),
    ),
    KBCard(
        slug="induction-schema",
        title="Induction is a schema",
        summary="Each arithmetic formula supplies a distinct induction instance.",
        body=(
            "For every formula φ(n, ā), possibly with additional parameters ā, "
            "induction takes proofs of φ(0, ā) and ∀n. φ(n, ā) → φ(S n, ā), "
            "and concludes ∀n. φ(n, ā). The first-order object language cannot "
            "quantify over formulas φ, so this is an infinite, effective schema, "
            "not one ordinary first-order sentence. In the kernel, an Ind proof "
            "stores the particular motive formula; the checker reconstructs and "
            "checks its zero, successor, and universally quantified instances."
        ),
        related_commands=(
            "pa tactic induction",
            "pa prove forall n. 0 + n = n",
        ),
        keywords=("ind", "motive", "structural induction", "schema", "parameters"),
    ),
    KBCard(
        slug="de-bruijn-indices",
        title="De Bruijn indices and capture",
        summary=(
            "Bound variables are binder distances; capture avoidance becomes explicit shifting."
        ),
        body=(
            "The named formula ∀x. ∃y. x + y = y + x has y at index 0 and x at "
            "index 1 inside the equality: 0 means the nearest term binder. Names "
            "are restored only for surface printing. When substitution descends "
            "under a binder, it increments the sought slot and shifts the free "
            "indices of the replacement. For example, a free index 0 inserted "
            "beneath ∀y must become index 1; leaving it at 0 would silently capture "
            "it as y. Shifting and opening are therefore part of soundness, not "
            "pretty-printer bookkeeping."
        ),
        related_commands=("pa prove forall x. exists y. x = y",),
        keywords=(
            "binder",
            "capture avoiding substitution",
            "alpha equivalence",
            "shift",
            "nameless",
        ),
    ),
    KBCard(
        slug="lcf-vs-proof-terms",
        title="LCF theorem values versus proof terms",
        summary="Both architectures isolate trust, but they place the certificate differently.",
        body=(
            "In an LCF-style prover, clients can obtain values of an abstract "
            "Theorem type only through trusted primitive inference functions; tactics "
            "compose those functions. In a proof-term prover, tactics instead build "
            "explicit certificate syntax and a small independent checker validates "
            "that syntax. Peano Lab chooses proof terms so students can inspect the "
            "growing certificate and QED can recheck it against the original goal. "
            "Neither architecture makes a buggy kernel, an inconsistent axiom set, "
            "or a compromised runtime harmless—the trust boundary must still be "
            "small, explicit, and audited."
        ),
        related_commands=("pa prove forall x. x = x", "pa tactic exact"),
        keywords=("lcf", "abstract theorem", "certificate", "kernel", "proof object"),
    ),
    KBCard(
        slug="de-bruijn-criterion",
        title="The De Bruijn criterion",
        summary="A small checker, independent of proof search, decides certificate validity.",
        body=(
            "The De Bruijn criterion asks that a formal proof be checkable by a "
            "small, independently inspectable program. It is distinct from, though "
            "named after the same mathematician as, de Bruijn indices. Peano Lab's "
            "kernel checker imports nothing from the tactic engine or UI, and every "
            "QED sends it the completed proof term and the original stated formula. "
            "A tactic may crash, loop, or construct nonsense without licensing a "
            "theorem. The criterion reduces the trusted computing base; it does not "
            "prove that the checker has no bugs or that the chosen axioms are "
            "consistent."
        ),
        related_commands=("pa prove forall x. x = x", "qed"),
        keywords=("soundness", "trusted computing base", "independent checker", "qed"),
    ),
    KBCard(
        slug="simp-termination",
        title="Why simp terminates",
        summary="Every fired rewrite decreases a well-founded deterministic order.",
        body=(
            "Unrestricted equality rewriting can loop: commutativity alone can swap "
            "the same two terms forever. PA3–PA6 decrease a substitution-stable "
            "lexicographic path ordering with precedence · > + > S > 0; this handles "
            "PA6 even though x · S y becomes the larger tree x · y + x. A concrete "
            "context equation has no flexible pattern variables and may instead use "
            "the deterministic total extension that orders rigid de Bruijn variables "
            "as atoms. Purely permutative schemas may enter the rule set, but an "
            "instantiated step fires only in its decreasing total-order direction. "
            "Those well-founded orders—not the browser step cap—are the termination "
            "argument. Each selected rewrite also carries equality-transport evidence, "
            "and QED checks the assembled certificate; termination alone would not "
            "establish soundness."
        ),
        related_commands=("pa tactic simp", "pa simp 2 * S 3"),
        keywords=("simplifier", "rewrite", "lpo", "well founded", "loop"),
    ),
    KBCard(
        slug="godel-limits",
        title="Gödel incompleteness and the limits",
        summary="Sound proof checking is not a decision procedure for arithmetic truth.",
        body=(
            "By the Gödel–Rosser theorem, any consistent, effectively axiomatized "
            "theory strong enough for ordinary arithmetic, including PA and HA, is "
            "incomplete: some "
            "arithmetic sentence is neither provable nor refutable in that theory. "
            "Under the usual arithmetization and derivability conditions, such a "
            "theory also cannot prove its own consistency if it is consistent. "
            "Therefore no sound effective extension of this lab can enumerate proofs "
            "of every truth about the standard natural numbers. Separately, `auto` "
            "is only bounded proof search, so its failure says even less: it is not a "
            "counterexample and not an unprovability result. The kernel establishes "
            "derivability from encoded rules, not truth in the intended model or the "
            "consistency of those rules."
        ),
        related_commands=("pa tactic auto", "pa prove forall x. x = x"),
        keywords=("godel", "incompleteness", "consistency", "undecidable", "limits"),
    ),
    KBCard(
        slug="heyting-vs-classical-pa",
        title="Heyting arithmetic versus classical PA",
        summary="The default logic is constructive; classical reasoning is an explicit extension.",
        body=(
            "Heyting arithmetic (HA) uses the arithmetic axioms and induction schema "
            "with intuitionistic first-order logic. Conventional Peano arithmetic "
            "uses classical logic. Peano Lab starts in the HA-style core and labels "
            "the extension: `classical on` authorizes proof nodes for double-negation "
            "elimination, ¬¬φ → φ, from which excluded middle is derivable. It changes "
            "the logical checker mode, not the meanings of 0, S, +, or ·. Every "
            "constructive proof remains valid classically, but not conversely. For a "
            "closed Π₁ sentence whose matrix HA proves decidable, negative translation "
            "gives the precise direction PA ⊢ A implies HA ⊢ A; that metatheorem is "
            "context, not code inside this prover."
        ),
        related_commands=("pa prove forall x. x = x", "classical on", "apply DNE"),
        keywords=(
            "ha",
            "intuitionistic",
            "constructive",
            "classical",
            "double negation elimination",
            "excluded middle",
        ),
    ),
)


_BY_SLUG = {card.slug: card for card in CARDS}
if len(_BY_SLUG) != len(CARDS):  # fail loudly during development, never ambiguously at runtime
    raise RuntimeError("duplicate Peano Lab knowledge-base slug")


def list_cards() -> tuple[KBCard, ...]:
    """Return all cards in their stable pedagogical order."""

    return CARDS


def _slug_key(slug: str) -> str:
    if type(slug) is not str:
        raise TypeError("a KB slug must be text")
    return slug.strip().casefold().replace("_", "-")


def get_card(slug: str) -> KBCard | None:
    """Look up a card by slug, accepting surrounding space and underscores."""

    return _BY_SLUG.get(_slug_key(slug))


def _search_text(text: str) -> str:
    """Case- and accent-fold prose without locale- or platform-dependent rules."""

    decomposed = unicodedata.normalize("NFKD", text).casefold()
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def search_cards(query: str) -> tuple[KBCard, ...]:
    """Return cards containing every whitespace-separated query term.

    Results retain :data:`CARDS` order, never relevance-score order, which
    makes identical queries deterministic across Python and Pyodide.
    """

    if type(query) is not str:
        raise TypeError("a KB search query must be text")
    terms = tuple(_search_text(term) for term in query.split() if term)
    if not terms:
        return CARDS
    matches: list[KBCard] = []
    for card in CARDS:
        document = _search_text(
            " ".join(
                (
                    card.slug,
                    card.title,
                    card.summary,
                    card.body,
                    *card.related_commands,
                    *card.keywords,
                )
            )
        )
        if all(term in document for term in terms):
            matches.append(card)
    return tuple(matches)


def render_card(card: KBCard | str) -> str:
    """Render one card as deterministic plain text suitable for the terminal."""

    if type(card) is str:
        slug = card
        found = get_card(slug)
        if found is None:
            raise KeyError(slug)
        card = found
    if type(card) is not KBCard:
        raise TypeError("render_card expects a KBCard or slug")
    commands = "\n".join(f"  {command}" for command in card.related_commands)
    return (
        f"{card.title}\n"
        f"{card.summary}\n\n"
        f"{card.body}\n\n"
        f"Related commands:\n{commands}"
    )


def render_index(cards: tuple[KBCard, ...] | None = None) -> str:
    """Render a compact index for all cards or a search-result tuple."""

    selected = CARDS if cards is None else cards
    if type(selected) is not tuple or not all(type(card) is KBCard for card in selected):
        raise TypeError("render_index expects a tuple of KBCard values")
    rows = ["Peano Lab knowledge base"]
    rows.extend(f"  {card.slug:<24} {card.title}" for card in selected)
    if len(rows) == 1:
        rows.append("  No cards matched.")
    return "\n".join(rows)


__all__ = [
    "KBCard",
    "CARDS",
    "list_cards",
    "get_card",
    "search_cards",
    "render_card",
    "render_index",
]
