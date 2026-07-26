"""Plain, deterministic teaching cards for the Peano Lab tactic language.

The encyclopedia documents only commands that the browser proof session can
actually execute.  It is intentionally data-first: the UI may choose its own
layout, while tests can replay every worked example against the real engine.

Each example starts a fresh proof, runs ``example_commands`` in order, and is
then ready for ``qed``.  That convention keeps documentation examples honest
without giving this untrusted content module any proof-checking authority.
"""

from __future__ import annotations

from dataclasses import dataclass


NL = "\r\n"


@dataclass(frozen=True, slots=True)
class TacticCard:
    """One executable encyclopedia entry.

    ``kind`` is one of ``primitive``, ``tactical``, or ``automation``.  The
    certificate description is kept separate from the goal description: this
    distinction is the central pedagogical point of a proof-term prover.
    """

    name: str
    kind: str
    syntax: str
    summary: str
    goal_effect: str
    certificate_effect: str
    example_theorem: str
    example_commands: tuple[str, ...]
    common_errors: tuple[str, ...]


TACTIC_CARDS = (
    TacticCard(
        "intro",
        "primitive",
        "intro [name]",
        "Introduce one implication premise or one universally quantified variable.",
        "For A -> B, adds the named A hypothesis and focuses B. For forall x. P, "
        "adds a fresh rigid variable and focuses P.",
        "Replaces the focused hole by ImpIntro(?) or ForallIntro(?).",
        "0 = 0 -> 0 = 0",
        ("intro h", "exact h"),
        (
            "The goal is neither an implication nor a universal quantifier.",
            "The supplied name is already in use or is not a legal surface name.",
        ),
    ),
    TacticCard(
        "specialize",
        "primitive",
        "specialize <hypothesis> <term>",
        "Add a concrete instance of a universally quantified hypothesis.",
        "Keeps the original universal hypothesis under a fresh internal name and "
        "adds its selected instance under the requested name.",
        "Builds ForallElim for the instance and a local implication cut around the "
        "existing certificate hole.",
        "(forall x. x = x) -> 0 = 0",
        ("intro h", "specialize h 0", "exact h"),
        (
            "The named hypothesis is missing or is not universally quantified.",
            "The term is missing, malformed, or contains an unresolved metavariable.",
        ),
    ),
    TacticCard(
        "forall_elim",
        "primitive",
        "forall_elim <hypothesis> <term>",
        "Spell the same universal-hypothesis elimination as specialize.",
        "Adds the concrete instance to the context while retaining the universal fact.",
        "Builds the same ForallElim-and-cut certificate as specialize; this is a "
        "pedagogical alias, not a new kernel rule.",
        "(forall x. x = x) -> 1 = 1",
        ("intro h", "forall_elim h 1", "exact h"),
        (
            "The command needs exactly a hypothesis name and a concrete term.",
            "The named hypothesis is not a forall formula.",
        ),
    ),
    TacticCard(
        "induction",
        "primitive",
        "induction <variable>",
        "Apply structural induction to a leading forall or a named rigid variable.",
        "Replaces one goal by the zero case and the successor case; the latter has "
        "the step variable and an IH hypothesis.",
        "Installs an Ind certificate with base and step holes. The step is wrapped "
        "by ForallIntro and ImpIntro; local-variable induction also uses ForallElim.",
        "forall n. 0 + n = n",
        ("induction n", "simp", "simp [IH]"),
        (
            "The name is not a leading forall binder or a variable in the goal.",
            "An unresolved term metavariable prevents construction of a fixed motive.",
        ),
    ),
    TacticCard(
        "apply",
        "primitive",
        "apply <hypothesis|PA1..PA6|DNE>",
        "Use a local theorem, a PA axiom, or explicitly authorized DNE backwards.",
        "Matches the source conclusion against the goal and creates one subgoal for "
        "each implication premise; leading forall variables are inferred as metas.",
        "Starts with Hyp, Axiom, or DNE, adds ForallElim nodes for inferred terms, "
        "then ImpElim nodes whose argument positions are new holes.",
        "forall n. S n = 0 -> false",
        ("intro n", "intro h", "apply PA1", "exact h"),
        (
            "The proof source is unknown or its conclusion does not match the goal.",
            "DNE is rejected unless the session owner has enabled classical mode.",
        ),
    ),
    TacticCard(
        "split",
        "primitive",
        "split",
        "Prove both halves of a conjunction.",
        "Replaces A /\\ B by two ordered goals, first A and then B.",
        "Replaces the hole by AndIntro(left-hole, right-hole).",
        "0 = 0 /\\ 1 = 1",
        ("split", "refl", "refl"),
        (
            "The focused goal is not a conjunction.",
            "Extra arguments are not accepted.",
        ),
    ),
    TacticCard(
        "left",
        "primitive",
        "left",
        "Choose the left constructor of a disjunction.",
        "Replaces A \\/ B by the single goal A.",
        "Replaces the hole by OrIntroL(?).",
        "0 = 0 \\/ 0 = 1",
        ("left", "refl"),
        (
            "The focused goal is not a disjunction.",
            "Choosing left does not prove the discarded right alternative.",
        ),
    ),
    TacticCard(
        "right",
        "primitive",
        "right",
        "Choose the right constructor of a disjunction.",
        "Replaces A \\/ B by the single goal B.",
        "Replaces the hole by OrIntroR(?).",
        "0 = 1 \\/ 0 = 0",
        ("right", "refl"),
        (
            "The focused goal is not a disjunction.",
            "Choosing right does not prove the discarded left alternative.",
        ),
    ),
    TacticCard(
        "cases",
        "primitive",
        "cases <hypothesis>",
        "Eliminate a conjunction, disjunction, existential, or bottom hypothesis.",
        "A conjunction exposes both fields; a disjunction makes two branches; an "
        "existential opens a fresh witness; bottom closes the goal.",
        "Builds the matching AndElim cut, OrElim, ExistsElim, or BotElim tree with "
        "holes exactly corresponding to the displayed branches.",
        "(0 = 0 /\\ 1 = 1) -> 0 = 0",
        ("intro h", "cases h", "exact h_left"),
        (
            "The hypothesis name is unknown.",
            "Atomic, implication, universal, and equality hypotheses cannot be cased.",
        ),
    ),
    TacticCard(
        "exfalso",
        "primitive",
        "exfalso",
        "Reduce an arbitrary target to bottom (false).",
        "Keeps the context and replaces the focused target by false.",
        "Wraps the new hole in BotElim, so a proof of bottom can inhabit the old target.",
        "false -> 0 = 1",
        ("intro h", "exfalso", "exact h"),
        (
            "The current goal is already bottom, so the command would make no progress.",
            "Exfalso does not manufacture a contradiction; the new false goal remains.",
        ),
    ),
    TacticCard(
        "exists",
        "primitive",
        "exists <term|?>",
        "Supply a witness for an existential goal.",
        "Replaces exists x. P(x) by P(witness). A bare ? creates a flexible, "
        "proof-wide term metavariable that later unification must resolve.",
        "Replaces the hole by ExistsIntro(witness, proof-hole).",
        "exists n. n = 0",
        ("exists 0", "refl"),
        (
            "The focused goal is not existential or the witness term is malformed.",
            "QED fails if a ? witness remains unresolved in the final certificate.",
        ),
    ),
    TacticCard(
        "refl",
        "primitive",
        "refl",
        "Close an equality whose two sides unify as the same term.",
        "Removes the focused equality goal and may solve shared term metavariables.",
        "Inserts EqRefl(term), then propagates any new metavariable substitution "
        "through every sibling goal and the whole partial certificate.",
        "0 = 0",
        ("refl",),
        (
            "The goal is not an equality.",
            "The two rigid terms differ and cannot be made identical by solving metas.",
        ),
    ),
    TacticCard(
        "symm",
        "primitive",
        "symm",
        "Reverse the direction of an equality goal.",
        "Changes the target from a = b to b = a.",
        "Replaces the focused hole by EqSym(new-hole).",
        "0 = 1 -> 1 = 0",
        ("intro h", "symm", "exact h"),
        (
            "The focused goal is not an equality.",
            "Repeated symmetry can cycle; repeat detects that cycle and stops.",
        ),
    ),
    TacticCard(
        "trans",
        "primitive",
        "trans <middle-term|?>",
        "Split an equality through a chosen middle term.",
        "Replaces a = c by the ordered goals a = b and b = c.",
        "Replaces the hole by EqTrans(left-hole, right-hole); a ? midpoint is one "
        "shared metavariable in both holes.",
        "0 = 1 -> 1 = 0 -> 0 = 0",
        ("intro h01", "intro h10", "trans 1", "exact h01", "exact h10"),
        (
            "The goal is not an equality or the middle term is missing/malformed.",
            "A metavariable midpoint must be consistently solved across both subgoals.",
        ),
    ),
    TacticCard(
        "congr",
        "primitive",
        "congr",
        "Reduce equality of matching arithmetic constructors to their arguments.",
        "S a = S b makes one goal a = b; a+b = c+d and a*b = c*d each make two.",
        "Inserts CongS, CongAdd, or CongMul with one hole per component equality.",
        "forall n m. n = m -> S n = S m",
        ("intro n", "intro m", "intro h", "congr", "exact h"),
        (
            "The focused target is not an equality.",
            "The two sides do not share the same outer constructor S, +, or *.",
        ),
    ),
    TacticCard(
        "exact",
        "primitive",
        "exact <hypothesis>",
        "Close the goal with one named context hypothesis.",
        "Removes the focused goal when the hypothesis formula unifies with it.",
        "Replaces the hole by Hyp(index) and propagates any shared-meta solution.",
        "0 = 0 -> 0 = 0",
        ("intro h", "exact h"),
        (
            "The command needs exactly one existing hypothesis name.",
            "The named hypothesis does not match the current goal.",
        ),
    ),
    TacticCard(
        "assumption",
        "primitive",
        "assumption",
        "Close with the first context hypothesis that matches the goal.",
        "Scans the context deterministically from newest to oldest and removes the goal.",
        "Inserts the matching Hyp(index), with proof-wide metavariable propagation.",
        "1 = 1 -> 1 = 1",
        ("intro h", "assumption"),
        (
            "No context hypothesis matches the current goal.",
            "The tactic accepts no hypothesis name; use exact h to choose explicitly.",
        ),
    ),
    TacticCard(
        "rewrite",
        "primitive",
        "rewrite [<-] <equation> [at <hypothesis>]",
        "Rewrite the first eligible occurrence using a context equation or PA axiom.",
        "Without at, changes the goal; with at h, adds a rewritten version of h to "
        "the context. The <- marker reverses the selected equation.",
        "Builds EqSubst with an explicit motive and equality proof. Rewriting a "
        "hypothesis additionally uses a local implication cut.",
        "forall n. n = 0 -> S n = S 0",
        ("intro n", "intro h", "rewrite h", "refl"),
        (
            "The equation is unknown, non-equational, or has no occurrence in that direction.",
            "Rewriting is refused when it would cross a quantifier unsafely or metas remain.",
        ),
    ),
    TacticCard(
        "simp",
        "primitive",
        "simp [<equation-hypothesis>, <- <equation-hypothesis>, ...]",
        "Normalize with ordered PA3-PA6 rewrites plus explicitly named equations.",
        "Simplifies the target deterministically. It closes a reflexive, exact, or "
        "structurally congruent equality normal form; otherwise one simplified goal remains.",
        "Records every rewrite as EqSubst, adds ForallIntro when simplifying under "
        "leading quantifiers, and ends in EqRefl, Hyp, CongS/CongAdd/CongMul, or a hole.",
        "forall n. n = 0 -> S n = S 0",
        ("intro n", "intro h", "simp [h]"),
        (
            "An explicit lemma is missing, duplicated, non-equational, or badly oriented.",
            "The command fails transactionally if no rewrite or closing step makes progress.",
        ),
    ),
    TacticCard(
        "undo",
        "primitive",
        "undo",
        "Restore the exact proof state before the latest successful command.",
        "Restores goals, substitutions, certificate holes, and earlier history exactly.",
        "Discards the most recent transaction's certificate changes; it creates no "
        "kernel proof node of its own.",
        "0 = 0",
        ("refl", "undo", "refl"),
        (
            "There is no successful history entry to restore.",
            "Undo is a complete-line session command and cannot be nested in a tactical.",
        ),
    ),
    TacticCard(
        ";",
        "tactical",
        "<tactic-1> ; <tactic-2>",
        "Run the right tactic on every goal created by the left tactic.",
        "The left tactic runs on the focus; each of its newly created goals then receives "
        "the right tactic, in order.",
        "Splices the child certificates into their exact holes and publishes the whole "
        "compound command as one undo transaction.",
        "0 = 0 /\\ 1 = 1",
        ("split; refl",),
        (
            "Either side is empty or grouping is unbalanced.",
            "If any child fails, the entire compound command leaves the state unchanged.",
        ),
    ),
    TacticCard(
        "<|>",
        "tactical",
        "<tactic-1> <|> <tactic-2>",
        "Try the left tactic, falling back on ordinary failure while malformed input aborts.",
        "Publishes the left result when it succeeds; otherwise runs the right tactic on "
        "the exact original snapshot.",
        "Keeps only the successful branch certificate and records one outer undo transaction.",
        "0 = 0",
        ("assumption <|> refl",),
        (
            "Either side is empty or grouping is unbalanced.",
            "If both branches fail, the complete alternative fails without state leakage.",
        ),
    ),
    TacticCard(
        "repeat",
        "tactical",
        "repeat <tactic>",
        "Run a tactic until ordinary failure, no logical progress, or a revisited state.",
        "Applies the child repeatedly to the focused evolving state; the expected final "
        "failure is the stopping condition, not a failure of repeat.",
        "Combines all successful child certificate edits into one transaction. A 256-step "
        "guard prevents runaway growth.",
        "0 = 0 -> 0 = 0",
        ("repeat intro", "assumption"),
        (
            "The child tactic is missing.",
            "Syntax and resource-limit errors propagate instead of pretending repeat succeeded.",
            "A child that evades cycle detection for 256 steps triggers the termination guard.",
        ),
    ),
    TacticCard(
        "first",
        "tactical",
        "first [<tactic> | <tactic> | ...]",
        "Run the first tactic in a left-to-right list that succeeds.",
        "Each failed choice sees the same original state; the first success becomes visible.",
        "Retains only the winning child certificate and collapses it to one undo transaction.",
        "0 = 0",
        ("first [assumption | refl]",),
        (
            "The brackets or choices are missing, empty, or unbalanced.",
            "If every choice fails, first reports the last error and restores the snapshot.",
        ),
    ),
    TacticCard(
        "all_goals",
        "tactical",
        "all_goals <tactic>",
        "Apply a tactic once to every goal that exists when the command begins.",
        "Visits entry goals in order. New subgoals made by the child are preserved but are "
        "not recursively revisited by this same all_goals command.",
        "Splices each child certificate at its original hole and publishes one transaction.",
        "0 = 0 /\\ 1 = 1",
        ("split", "all_goals refl"),
        (
            "The child tactic is missing.",
            "Failure on any visited goal rolls back successes on all earlier goals.",
        ),
    ),
    TacticCard(
        "focus",
        "tactical",
        "focus <positive-goal-number> <tactic>",
        "Run one tactic on one selected goal without reordering the goal list.",
        "Uses one-based numbering from the displayed panel and leaves every other goal "
        "at its original position.",
        "Runs the child against the selected certificate hole, then splices its result "
        "back into that exact position as one transaction.",
        "0 = 0 /\\ 1 = 1",
        ("split", "focus 2 refl", "refl"),
        (
            "The goal number is missing, zero, negative, or outside the current list.",
            "The selected child failure leaves every goal and hole unchanged.",
        ),
    ),
    TacticCard(
        "auto",
        "automation",
        "auto [positive-depth]",
        "Search a bounded deterministic tree and replay a certificate-valid primitive plan.",
        "On success, closes the goals found by the winning plan. Exhausting a depth or node "
        "bound is reported as a limit, never as an unprovability result.",
        "Speculative branches publish nothing. Only the winning ordinary primitive steps are "
        "replayed, and QED still invokes the independent kernel checker afterward.",
        "forall n. 0 + n = n",
        ("auto 5",),
        (
            "Depth must be a positive integer; the default is 5.",
            "No plan was found in the finite search or a depth/node bound was reached.",
        ),
    ),
    TacticCard(
        "hint",
        "automation",
        "hint",
        "Inspect the focused goal and suggest one supported immediate command.",
        "Does not change any goal. Its found, none, and limit statuses are deliberately "
        "advisory and never claim that a theorem is provable or unprovable.",
        "Creates no certificate node and does not append proof history.",
        "0 = 0",
        ("hint", "refl"),
        (
            "A limit status means inspection stopped; it is not a negative proof result.",
            "The suggestion is text only and must still be executed and kernel-checked.",
        ),
    ),
)


PRIMITIVE_NAMES = tuple(
    card.name for card in TACTIC_CARDS if card.kind == "primitive"
)
TACTICAL_NAMES = tuple(
    card.name for card in TACTIC_CARDS if card.kind == "tactical"
)
AUTOMATION_NAMES = tuple(
    card.name for card in TACTIC_CARDS if card.kind == "automation"
)
TACTIC_MAP = {card.name: card for card in TACTIC_CARDS}

_ALIASES = {
    "then": ";",
    "orelse": "<|>",
}


def names() -> tuple[str, ...]:
    """Return canonical card names in stable display order."""

    return tuple(card.name for card in TACTIC_CARDS)


def lookup(name: str) -> TacticCard | None:
    """Look up one exact surface name, accepting two pedagogical aliases."""

    if type(name) is not str:
        return None
    canonical = _ALIASES.get(name.strip(), name.strip())
    return TACTIC_MAP.get(canonical)


def render_index() -> str:
    """Render a plain-text index without ANSI or terminal control sequences."""

    rows = ["Peano Lab tactic encyclopedia"]
    for kind, title in (
        ("primitive", "Primitive tactics"),
        ("tactical", "Tacticals"),
        ("automation", "Automation and advice"),
    ):
        rows.extend(("", title))
        for card in TACTIC_CARDS:
            if card.kind == kind:
                rows.append(f"  {card.name:<12} {card.summary}")
    rows.extend(("", "Type `pa tactic <name>` for a complete executable card."))
    return NL.join(rows)


def render_card(card_or_name: TacticCard | str) -> str:
    """Render one complete teaching card, or a stable unknown-name message."""

    if type(card_or_name) is TacticCard:
        card = card_or_name
    elif type(card_or_name) is str:
        card = lookup(card_or_name)
    else:
        card = None
    if card is None:
        shown = card_or_name if type(card_or_name) is str else str(card_or_name)
        return f"No tactic named {shown!r}. Type `pa tactic`."

    rows = [
        f"Tactic: {card.name}",
        f"Kind: {card.kind}",
        f"Syntax: {card.syntax}",
        "",
        card.summary,
        "",
        f"Goal effect: {card.goal_effect}",
        f"Certificate effect: {card.certificate_effect}",
        "",
        "Worked executable example:",
        f"  pa prove {card.example_theorem}",
    ]
    rows.extend(f"  {command}" for command in card.example_commands)
    rows.append("  qed")
    rows.extend(("", "Common errors:"))
    rows.extend(f"  - {error}" for error in card.common_errors)
    return NL.join(rows)


__all__ = [
    "TacticCard",
    "TACTIC_CARDS",
    "TACTIC_MAP",
    "PRIMITIVE_NAMES",
    "TACTICAL_NAMES",
    "AUTOMATION_NAMES",
    "names",
    "lookup",
    "render_index",
    "render_card",
]
