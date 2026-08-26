"""One-step, directed and capture-safe rewriting.

The kernel's :class:`~peano_lab.kernel.proofs.EqSubst` rule does not store an
occurrence path.  Instead it stores a *motive*: a formula with a distinguished
free variable at de Bruijn index zero.  Replacing that variable by the left and
right sides of the equation must recover the formula before and after the
rewrite, respectively.

``rewrite_first`` constructs exactly that pair.  Occurrences are considered in
formula left-to-right order and term pre-order (a whole term before its
children), so the result is deterministic.  The extra motive variable is made
room for by shifting every other free variable; ``shift_formula`` performs this
capture-safely through any untouched quantifiers.

Below ``d`` quantifiers an outer source is represented by ``shift(source, d)``.
The replacement is lifted by the same amount, the motive placeholder becomes
``Var(d)``, and untouched free variables shift at cutoff ``d``.  Bound indices
below that cutoff never move.  This is the entire alpha-safety argument, and
``rewrite_first`` checks both substitution identities before returning.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..kernel.checker import axiom_formula
from ..kernel.formulas import And, Bot, Eq, Exists, Forall, Formula, Imp, Or
from ..kernel.proofs import Axiom, EqSubst, EqSym, ForallElim, Proof
from ..kernel.subst import shift_formula, shift_term, subst_formula
from ..kernel.terms import Add, Mul, Succ, Term, Var, Zero


class RewriteError(ValueError):
    """Base class for an expected directed-rewrite failure."""


class NoRewriteOccurrence(RewriteError):
    """The source term does not occur in the formula."""


class RewriteUnderBinder(RewriteError):
    """Compatibility name retained from M1; M3 enters binders safely."""


class SimpError(RewriteError):
    """An explicit simplification set or run is invalid."""


class InvalidSimpRule(SimpError):
    """A proposed simp lemma is not an oriented, decreasing equation."""


class SimpLimitExceeded(SimpError):
    """The optional resource guard stopped an otherwise terminating run."""


@dataclass(frozen=True, slots=True)
class SimpRule:
    """A named theorem offered to the untrusted simplifier.

    ``theorem`` may have leading universal quantifiers, but its body must be an
    equation.  ``proof`` proves that exact theorem in the context where the
    rule will be used.  Reversing a rule is explicit; either orientation must
    still pass the termination order before simplification begins.
    """

    name: str
    theorem: Formula
    proof: Proof
    reverse: bool = False

    def __post_init__(self) -> None:
        if type(self.name) is not str or not self.name:
            raise InvalidSimpRule("a simp rule needs a non-empty name")
        if not _is_formula(self.theorem):
            raise InvalidSimpRule(f"simp rule {self.name!r} is not a rigid PA formula")
        if not isinstance(self.proof, Proof):
            raise InvalidSimpRule(f"simp rule {self.name!r} needs a proof certificate")
        if type(self.reverse) is not bool:
            raise InvalidSimpRule(f"simp rule {self.name!r} has a non-Boolean direction")


@dataclass(frozen=True, slots=True)
class SimpSet:
    """An immutable, ordered simp set.

    Rule order is semantic: at each step the first rule having a match wins,
    then that rule rewrites the first formula/term occurrence in canonical
    left-to-right pre-order.  Duplicate names are rejected so trace output can
    always identify the rule unambiguously.
    """

    rules: tuple[SimpRule, ...] = ()

    def __post_init__(self) -> None:
        rules = tuple(self.rules)
        if not all(type(rule) is SimpRule for rule in rules):
            raise InvalidSimpRule("a simp set may contain only SimpRule values")
        names = [rule.name for rule in rules]
        if len(names) != len(set(names)):
            raise InvalidSimpRule("simp rule names must be unique within a simp set")
        object.__setattr__(self, "rules", rules)

    def extend(self, *rules: SimpRule) -> "SimpSet":
        return SimpSet(self.rules + tuple(rules))


@dataclass(frozen=True, slots=True)
class SimpStep:
    """One certified, left-to-right rewrite chosen by ``simplify_formula``."""

    rule: str
    before: Formula
    after: Formula
    motive: Formula
    equation: Eq
    equation_proof: Proof


@dataclass(frozen=True, slots=True)
class SimpResult:
    """A normal form together with every equality transport needed to reach it."""

    formula: Formula
    steps: tuple[SimpStep, ...]

    def transport_back(self, normal_proof: Proof) -> Proof:
        """Turn a proof of the normal form into a proof of the input formula."""

        proof = normal_proof
        for step in reversed(self.steps):
            # The visible step uses s=t from old to new.  A goal proof travels
            # in the opposite direction, exactly as the primitive rewrite
            # tactic does: motive[t] -> motive[s].
            proof = EqSubst(step.motive, EqSym(step.equation_proof), proof)
        return proof


def _is_rigid_term(term: object) -> bool:
    """Return whether ``term`` is an exact, metavariable-free kernel term."""

    if type(term) is Var:
        return type(term.index) is int and term.index >= 0
    if type(term) is Zero:
        return True
    if type(term) is Succ:
        return _is_rigid_term(term.term)
    if type(term) in (Add, Mul):
        return _is_rigid_term(term.left) and _is_rigid_term(term.right)
    return False


def _is_formula(formula: object) -> bool:
    if type(formula) is Eq:
        return _is_rigid_term(formula.left) and _is_rigid_term(formula.right)
    if type(formula) is Bot:
        return True
    if type(formula) in (Imp, And, Or):
        return _is_formula(formula.left) and _is_formula(formula.right)
    if type(formula) in (Forall, Exists):
        return _is_formula(formula.body)
    return False


def _rewrite_term(
    term: Term, source: Term, replacement: Term, depth: int
) -> tuple[Term, Term, bool]:
    """Return ``(new_term, motive_term, found)`` for one pre-order step."""

    if term == shift_term(source, depth):
        return shift_term(replacement, depth), Var(depth), True

    if type(term) is Succ:
        new_child, motive_child, found = _rewrite_term(
            term.term, source, replacement, depth
        )
        if found:
            return Succ(new_child), Succ(motive_child), True
    elif type(term) in (Add, Mul):
        constructor = type(term)
        new_left, motive_left, found = _rewrite_term(
            term.left, source, replacement, depth
        )
        if found:
            return (
                constructor(new_left, term.right),
                constructor(motive_left, shift_term(term.right, 1, cutoff=depth)),
                True,
            )
        new_right, motive_right, found = _rewrite_term(
            term.right, source, replacement, depth
        )
        if found:
            return (
                constructor(term.left, new_right),
                constructor(shift_term(term.left, 1, cutoff=depth), motive_right),
                True,
            )

    # This entire subtree is untouched.  Its free variables still need to move
    # past the motive's fresh index zero.
    return term, shift_term(term, 1, cutoff=depth), False


def _rewrite_in_formula(
    formula: Formula, source: Term, replacement: Term, depth: int
) -> tuple[Formula, Formula, bool]:
    """Return ``(new, motive, found)`` at the current binder depth."""

    if type(formula) is Eq:
        new_left, motive_left, found = _rewrite_term(
            formula.left, source, replacement, depth
        )
        if found:
            return (
                Eq(new_left, formula.right),
                Eq(motive_left, shift_term(formula.right, 1, cutoff=depth)),
                True,
            )
        new_right, motive_right, found = _rewrite_term(
            formula.right, source, replacement, depth
        )
        if found:
            return (
                Eq(formula.left, new_right),
                Eq(shift_term(formula.left, 1, cutoff=depth), motive_right),
                True,
            )
        return formula, shift_formula(formula, 1, cutoff=depth), False

    if type(formula) is Bot:
        return formula, formula, False

    if type(formula) in (Imp, And, Or):
        constructor = type(formula)
        new_left, motive_left, found = _rewrite_in_formula(
            formula.left, source, replacement, depth
        )
        if found:
            return (
                constructor(new_left, formula.right),
                constructor(
                    motive_left,
                    shift_formula(formula.right, 1, cutoff=depth),
                ),
                True,
            )
        new_right, motive_right, found = _rewrite_in_formula(
            formula.right, source, replacement, depth
        )
        if found:
            return (
                constructor(formula.left, new_right),
                constructor(
                    shift_formula(formula.left, 1, cutoff=depth),
                    motive_right,
                ),
                True,
            )
        return formula, shift_formula(formula, 1, cutoff=depth), False

    if type(formula) in (Forall, Exists):
        new_body, motive_body, found = _rewrite_in_formula(
            formula.body, source, replacement, depth + 1
        )
        if found:
            return type(formula)(new_body), type(formula)(motive_body), True
        return formula, shift_formula(formula, 1, cutoff=depth), False

    raise TypeError("expected a rigid PA formula")


def rewrite_first(
    formula: Formula, source: Term, replacement: Term
) -> tuple[Formula, Formula]:
    """Rewrite the first eligible ``source`` to ``replacement``.

    The returned pair is ``(new_formula, motive)`` and obeys::

        subst_formula(motive, 0, source) == formula
        subst_formula(motive, 0, replacement) == new_formula

    Both terms must be rigid kernel terms.  Quantifier bodies are traversed,
    but a bound variable is never mistaken for an outer variable of the same
    numerical index.
    """

    if not _is_formula(formula):
        raise TypeError("rewrite target must be a rigid PA formula")
    if not _is_rigid_term(source):
        raise TypeError("rewrite source must be a rigid PA term")
    if not _is_rigid_term(replacement):
        raise TypeError("rewrite replacement must be a rigid PA term")

    rewritten, motive, found = _rewrite_in_formula(
        formula, source, replacement, 0
    )
    if found:
        if subst_formula(motive, 0, source) != formula:
            raise RewriteError("internal error: rewrite motive does not recover the source.")
        if subst_formula(motive, 0, replacement) != rewritten:
            raise RewriteError("internal error: rewrite motive does not recover the result.")
        return rewritten, motive
    raise NoRewriteOccurrence("rewrite source does not occur in the target formula")


def rewrite_formula(
    formula: Formula, equation: Eq, *, reverse: bool = False
) -> tuple[Formula, Formula]:
    """Rewrite with an exact kernel equation, optionally right-to-left.

    ``reverse=False`` chooses ``equation.left`` as the source; ``True`` chooses
    ``equation.right``.  A tactic using the reverse direction must correspondingly
    pass ``EqSym(equation_proof)`` to the kernel's ``EqSubst`` constructor.
    """

    if type(equation) is not Eq or not _is_formula(equation):
        raise TypeError("rewrite theorem must be an exact kernel equation")
    if type(reverse) is not bool:
        raise TypeError("rewrite direction flag must be a boolean")
    source, replacement = (
        (equation.right, equation.left) if reverse else (equation.left, equation.right)
    )
    return rewrite_first(formula, source, replacement)


# ``simp`` termination -----------------------------------------------------
#
# Node count is not a termination measure for PA6: ``x * S y`` rewrites to
# the larger tree ``x * y + x``.  We instead use lexicographic path ordering
# (LPO), a standard simplification order, with precedence
#
#     multiplication > addition > successor > zero.
#
# Variables compare only through the subterm clause.  Thus all four recursive
# equations decrease: PA3/PA5 to a subterm, PA4 because ``+ > S`` after its
# recursive argument shrinks, and PA6 because ``* > +`` while ``x*y`` is
# smaller than ``x*S y``.  LPO is well-founded and closed under term contexts.
# A formula step changes one term component to an LPO-smaller component, so
# the finite product extension over formula positions is well-founded too.
# User rules must pass the same check.  A concrete context equation may also
# decrease the total extension where free de Bruijn variables are rigid
# constants.  A purely permutative schema (the same symbols and variables
# rearranged, such as a local commutativity IH) is the standard other case: it
# fires only when that total extension decreases.  This is the familiar
# "ordered rewriting" treatment of commutative lemmas.
# A step limit is only an optional browser resource guard, never the argument
# for logical termination.


def _term_children(term: Term) -> tuple[Term, ...]:
    if type(term) is Succ:
        return (term.term,)
    if type(term) in (Add, Mul):
        return (term.left, term.right)
    return ()


_LPO_PRECEDENCE = {Zero: 0, Succ: 1, Add: 2, Mul: 3}


def _lpo_greater(left: Term, right: Term) -> bool:
    """Strict lexicographic path ordering used by the simp rule gate."""

    if left == right:
        return False

    left_children = _term_children(left)
    if any(child == right or _lpo_greater(child, right) for child in left_children):
        return True

    # Variables are atoms in the ordering.  In particular a constant is not
    # greater than an unrelated rule variable; this preserves substitution.
    if type(left) is Var or type(right) is Var:
        return False

    right_children = _term_children(right)
    if not all(_lpo_greater(left, child) for child in right_children):
        return False

    left_precedence = _LPO_PRECEDENCE[type(left)]
    right_precedence = _LPO_PRECEDENCE[type(right)]
    if left_precedence > right_precedence:
        return True
    if type(left) is not type(right):
        return False

    # Same head symbol: lexicographic status.  Equal arguments form a common
    # prefix; the first different left argument must itself be greater.
    for left_child, right_child in zip(left_children, right_children):
        if left_child != right_child:
            return _lpo_greater(left_child, right_child)
    return False


def _ordered_lpo_greater(left: Term, right: Term) -> bool:
    """A total-on-variables LPO extension for rigid and permutative rules.

    Kernel variables are rigid symbols during one simplification run, so their
    de Bruijn indices provide a deterministic atom order.  For quantified
    schemas we use this only after proving that a rule merely permutes an
    identical multiset of symbols; concrete context equations have no flexible
    pattern variables and can use it directly.
    """

    if left == right:
        return False
    left_children = _term_children(left)
    if any(
        child == right or _ordered_lpo_greater(child, right)
        for child in left_children
    ):
        return True
    right_children = _term_children(right)
    if not all(_ordered_lpo_greater(left, child) for child in right_children):
        return False
    # In an instantiated goal, de Bruijn variables are rigid constants.  Give
    # them a deterministic precedence above the function symbols.  The
    # recursive "greater than every RHS child" guard still rejects x -> S x.
    left_precedence = (
        (1, left.index) if type(left) is Var else (0, _LPO_PRECEDENCE[type(left)])
    )
    right_precedence = (
        (1, right.index)
        if type(right) is Var
        else (0, _LPO_PRECEDENCE[type(right)])
    )
    if left_precedence > right_precedence:
        return True
    if type(left) is not type(right):
        return False
    for left_child, right_child in zip(left_children, right_children):
        if left_child != right_child:
            return _ordered_lpo_greater(left_child, right_child)
    return False


def simp_decreases(source: Term, replacement: Term) -> bool:
    """Return whether an orientation uniformly decreases under substitution."""

    if not _is_rigid_term(source) or not _is_rigid_term(replacement):
        raise TypeError("simp ordering needs two rigid PA terms")
    return _lpo_greater(source, replacement)


@dataclass(frozen=True, slots=True)
class _PreparedRule:
    rule: SimpRule
    binder_count: int
    source_pattern: Term
    replacement_pattern: Term
    ordered: bool


def _rule_body(rule: SimpRule) -> tuple[int, Eq]:
    binder_count = 0
    body = rule.theorem
    while type(body) is Forall:
        binder_count += 1
        body = body.body
    if type(body) is not Eq:
        raise InvalidSimpRule(
            f"simp rule {rule.name!r} must be an equation after leading foralls"
        )
    return binder_count, body


def _pattern_variables(term: Term, binder_count: int) -> set[int]:
    if type(term) is Var:
        return {term.index} if term.index < binder_count else set()
    result: set[int] = set()
    for child in _term_children(term):
        result.update(_pattern_variables(child, binder_count))
    return result


def _symbol_multiset(term: Term) -> dict[tuple[str, int | None], int]:
    """Count exact symbols; equality means two terms differ only by permutation."""

    if type(term) is Var:
        key = ("Var", term.index)
    else:
        key = (type(term).__name__, None)
    result = {key: 1}
    for child in _term_children(term):
        for symbol, count in _symbol_multiset(child).items():
            result[symbol] = result.get(symbol, 0) + count
    return result


def _prepare_rule(rule: SimpRule) -> _PreparedRule:
    binder_count, equation = _rule_body(rule)
    source, replacement = (
        (equation.right, equation.left)
        if rule.reverse
        else (equation.left, equation.right)
    )
    source_variables = _pattern_variables(source, binder_count)
    replacement_variables = _pattern_variables(replacement, binder_count)
    if not replacement_variables <= source_variables:
        raise InvalidSimpRule(
            f"simp rule {rule.name!r} introduces a variable on its right-hand side"
        )
    strictly_decreasing = _lpo_greater(source, replacement)
    permutative = _symbol_multiset(source) == _symbol_multiset(replacement)
    concrete_decrease = binder_count == 0 and _ordered_lpo_greater(
        source, replacement
    )
    if not strictly_decreasing and not (permutative or concrete_decrease):
        arrow = "right-to-left" if rule.reverse else "left-to-right"
        raise InvalidSimpRule(
            f"simp rule {rule.name!r} is not decreasing {arrow}"
        )
    return _PreparedRule(
        rule,
        binder_count,
        source,
        replacement,
        not strictly_decreasing,
    )


def _match_pattern(
    pattern: Term,
    candidate: Term,
    binder_count: int,
    assignments: dict[int, Term],
) -> bool:
    if type(pattern) is Var:
        if pattern.index < binder_count:
            previous = assignments.get(pattern.index)
            if previous is None:
                assignments[pattern.index] = candidate
                return True
            return previous == candidate
        # A free parameter below the theorem's binders remains rigid after
        # those binder slots are removed.
        return candidate == Var(pattern.index - binder_count)
    if type(pattern) is not type(candidate):
        return False
    if type(pattern) is Zero:
        return True
    if type(pattern) is Succ:
        return _match_pattern(
            pattern.term, candidate.term, binder_count, assignments
        )
    if type(pattern) in (Add, Mul):
        return _match_pattern(
            pattern.left, candidate.left, binder_count, assignments
        ) and _match_pattern(
            pattern.right, candidate.right, binder_count, assignments
        )
    return False


def _instantiate_rule(
    prepared: _PreparedRule, candidate: Term
) -> tuple[Eq, Proof] | None:
    assignments: dict[int, Term] = {}
    if not _match_pattern(
        prepared.source_pattern,
        candidate,
        prepared.binder_count,
        assignments,
    ):
        return None
    if len(assignments) != prepared.binder_count:
        # Every quantified variable must be inferable from the oriented LHS.
        # This makes instantiation deterministic and mirrors primitive rewrite.
        return None

    formula = prepared.rule.theorem
    proof = prepared.rule.proof
    for index in reversed(range(prepared.binder_count)):
        term = assignments[index]
        assert type(formula) is Forall
        formula = subst_formula(formula.body, 0, term)
        proof = ForallElim(proof, term)
    assert type(formula) is Eq
    if prepared.rule.reverse:
        formula = Eq(formula.right, formula.left)
        proof = EqSym(proof)
    if formula.left != candidate:
        raise SimpError("internal error: instantiated simp source changed")
    decreases = (
        _ordered_lpo_greater(formula.left, formula.right)
        if prepared.ordered
        else _lpo_greater(formula.left, formula.right)
    )
    if not decreases:
        # Ordered permutative rules simply do not fire in the increasing
        # direction.  This is not an error and does not consume a step.
        return None
    return formula, proof


def _simp_term(
    term: Term, prepared: _PreparedRule
) -> tuple[Term, Term, Eq | None, Proof | None]:
    instantiated = _instantiate_rule(prepared, term)
    if instantiated is not None:
        equation, proof = instantiated
        return equation.right, Var(0), equation, proof

    if type(term) is Succ:
        new_child, motive_child, equation, proof = _simp_term(term.term, prepared)
        if equation is not None:
            return Succ(new_child), Succ(motive_child), equation, proof
    elif type(term) in (Add, Mul):
        constructor = type(term)
        new_left, motive_left, equation, proof = _simp_term(term.left, prepared)
        if equation is not None:
            return (
                constructor(new_left, term.right),
                constructor(motive_left, shift_term(term.right, 1)),
                equation,
                proof,
            )
        new_right, motive_right, equation, proof = _simp_term(term.right, prepared)
        if equation is not None:
            return (
                constructor(term.left, new_right),
                constructor(shift_term(term.left, 1), motive_right),
                equation,
                proof,
            )
    return term, shift_term(term, 1), None, None


def _simp_formula_once(
    formula: Formula, prepared: _PreparedRule
) -> tuple[Formula, Formula, Eq | None, Proof | None]:
    """Use one prepared rule at its first proof-context-safe occurrence.

    Quantifier bodies are not entered here because a rule instantiated with a
    locally bound variable cannot be proved in the surrounding kernel context.
    The tactic layer opens leading quantifiers with ``ForallIntro`` first and
    shifts rules/context capture-safely; this keeps every equation proof honest.
    """

    if type(formula) is Eq:
        new_left, motive_left, equation, proof = _simp_term(
            formula.left, prepared
        )
        if equation is not None:
            return (
                Eq(new_left, formula.right),
                Eq(motive_left, shift_term(formula.right, 1)),
                equation,
                proof,
            )
        new_right, motive_right, equation, proof = _simp_term(
            formula.right, prepared
        )
        if equation is not None:
            return (
                Eq(formula.left, new_right),
                Eq(shift_term(formula.left, 1), motive_right),
                equation,
                proof,
            )
        return formula, shift_formula(formula, 1), None, None

    if type(formula) is Bot:
        return formula, formula, None, None
    if type(formula) in (Imp, And, Or):
        constructor = type(formula)
        new_left, motive_left, equation, proof = _simp_formula_once(
            formula.left, prepared
        )
        if equation is not None:
            return (
                constructor(new_left, formula.right),
                constructor(motive_left, shift_formula(formula.right, 1)),
                equation,
                proof,
            )
        new_right, motive_right, equation, proof = _simp_formula_once(
            formula.right, prepared
        )
        if equation is not None:
            return (
                constructor(formula.left, new_right),
                constructor(shift_formula(formula.left, 1), motive_right),
                equation,
                proof,
            )
        return formula, shift_formula(formula, 1), None, None
    if type(formula) in (Forall, Exists):
        return formula, shift_formula(formula, 1), None, None
    raise TypeError("expected a rigid PA formula")


def simplify_formula(
    formula: Formula,
    simp_set: SimpSet,
    *,
    max_steps: int | None = 4096,
) -> SimpResult:
    """Normalize term occurrences with an explicit, ordered simp set.

    Every returned step contains the instantiated equation proof and its
    ``EqSubst`` motive.  This function never evaluates arithmetic and never
    claims a proposition true; callers must prove the returned normal form and
    use :meth:`SimpResult.transport_back` to build the certificate.
    """

    if not _is_formula(formula):
        raise TypeError("simp target must be a rigid PA formula")
    if type(simp_set) is not SimpSet:
        raise TypeError("simp needs an explicit SimpSet")
    if max_steps is not None and (type(max_steps) is not int or max_steps < 1):
        raise ValueError("simp max_steps must be a positive integer or None")

    # Validate the entire set before changing anything.  A bad late rule must
    # not be silently hidden by an earlier rule that happens to normalize.
    prepared_rules = tuple(_prepare_rule(rule) for rule in simp_set.rules)
    current = formula
    steps: list[SimpStep] = []
    while True:
        for prepared in prepared_rules:
            after, motive, equation, proof = _simp_formula_once(current, prepared)
            if equation is None:
                continue
            if max_steps is not None and len(steps) >= max_steps:
                raise SimpLimitExceeded(
                    f"simp exceeded its explicit {max_steps}-step resource limit"
                )
            assert proof is not None
            if subst_formula(motive, 0, equation.left) != current:
                raise SimpError("internal error: simp motive lost the source formula")
            if subst_formula(motive, 0, equation.right) != after:
                raise SimpError("internal error: simp motive lost the result formula")
            steps.append(
                SimpStep(
                    prepared.rule.name,
                    current,
                    after,
                    motive,
                    equation,
                    proof,
                )
            )
            current = after
            break
        else:
            return SimpResult(current, tuple(steps))


def _pa_simp_set() -> SimpSet:
    rules: list[SimpRule] = []
    for name in ("PA3", "PA4", "PA5", "PA6"):
        theorem = axiom_formula(name)
        assert theorem is not None
        rules.append(SimpRule(name, theorem, Axiom(name)))
    result = SimpSet(tuple(rules))
    # Keep an executable assertion beside the mathematical termination note.
    for rule in result.rules:
        _prepare_rule(rule)
    return result


PA_SIMP_SET = _pa_simp_set()


__all__ = [
    "RewriteError",
    "NoRewriteOccurrence",
    "RewriteUnderBinder",
    "SimpError",
    "InvalidSimpRule",
    "SimpLimitExceeded",
    "SimpRule",
    "SimpSet",
    "SimpStep",
    "SimpResult",
    "PA_SIMP_SET",
    "simp_decreases",
    "simplify_formula",
    "rewrite_first",
    "rewrite_formula",
]
