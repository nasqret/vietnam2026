"""Reproduce a small cut-normal certificate for consecutive-product parity.

This is a proof-size experiment, not a claimed lower bound.  Run from the
repository root with ``python3 scripts/minimize_parity_certificate.py``.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import fields
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON_ROOT = ROOT / "peano-lab" / "py"
sys.path.insert(0, str(PYTHON_ROOT))

from peano_lab.engine.proof_reduction import normalise_cuts
from peano_lab.engine.state import proof_size
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Eq, Exists, Forall, parse_formula
from peano_lab.kernel.proofs import (
    Axiom,
    CongAdd,
    EqRefl,
    EqSubst,
    EqSym,
    EqTrans,
    ExistsElim,
    ExistsIntro,
    ForallElim,
    ForallIntro,
    Hyp,
    ImpIntro,
    Ind,
    Proof,
)
from peano_lab.kernel.subst import shift_term
from peano_lab.kernel.terms import Add, Mul, Succ, Var, Zero
from peano_lab.ui.panels import render_certificate


ZERO = Zero()
ONE = Succ(ZERO)
TWO = Succ(ONE)


def pa3(a):
    return ForallElim(Axiom("PA3"), a)


def pa4(a, b):
    return ForallElim(ForallElim(Axiom("PA4"), a), b)


def pa5(a):
    return ForallElim(Axiom("PA5"), a)


def pa6(a, b):
    return ForallElim(ForallElim(Axiom("PA6"), a), b)


def chain(*proofs):
    result = proofs[0]
    for proof in proofs[1:]:
        result = EqTrans(result, proof)
    return result


def instantiate(proof, *terms):
    result = proof
    for term in terms:
        result = ForallElim(result, term)
    return normalise_cuts(result)


def qone(a):
    """A six-node proof of ``a + 1 = S a``."""

    motive = Eq(Add(shift_term(a, 1), ONE), Succ(Var(0)))
    return EqSubst(motive, pa3(a), pa4(a, ZERO))


def qtwo(a):
    """A ten-node proof of ``a + 2 = S (S a)``."""

    motive = Eq(Add(shift_term(a, 1), TWO), Succ(Var(0)))
    return EqSubst(motive, qone(a), pa4(a, ONE))


# A 20-node proof of forall a b. S a + b = S (a + b).
B = Var(0)
A = Var(1)
ADD_SUCC_MOTIVE = Eq(Add(Succ(A), B), Succ(Add(A, B)))
ADD_SUCC_GOAL = Forall(Forall(ADD_SUCC_MOTIVE))

a = Var(0)
add_succ_base = EqSubst(
    Eq(Add(Succ(shift_term(a, 1)), ZERO), Succ(Var(0))),
    EqSym(pa3(a)),
    pa3(Succ(a)),
)

b = Var(0)
a = Var(1)
left = Add(Succ(a), Succ(b))
left_motive = Eq(shift_term(left, 1), Succ(Var(0)))
left_to_normal = EqSubst(left_motive, Hyp(0), pa4(Succ(a), b))
add_succ_step = EqSubst(
    left_motive,
    EqSym(pa4(a, b)),
    left_to_normal,
)
ADD_SUCC = ForallIntro(
    Ind(
        ADD_SUCC_MOTIVE,
        add_succ_base,
        ForallIntro(ImpIntro(add_succ_step)),
    )
)
assert check((), ADD_SUCC, ADD_SUCC_GOAL)
assert proof_size(ADD_SUCC) == 20


def add_succ_at(a, b):
    return instantiate(ADD_SUCC, a, b)


def swap_special(A, a, n):
    """Prove ``(A+n)+S a = (A+a)+S n`` for these parameters (51 nodes).

    Folding the two outer PA4 transports into this induction is one node
    smaller than composing them with the unshifted swap theorem.
    """

    A_motive = shift_term(A, 1)
    a_motive = shift_term(a, 1)
    j = Var(0)
    motive = Eq(
        Add(Add(A_motive, j), Succ(a_motive)),
        Add(Add(A_motive, a_motive), Succ(j)),
    )
    base_core = chain(
        pa4(A, a),
        EqSym(qone(Add(A, a))),
    )
    base = EqSubst(
        Eq(
            Add(Var(0), shift_term(Succ(a), 1)),
            shift_term(Add(Add(A, a), ONE), 1),
        ),
        EqSym(pa3(A)),
        base_core,
    )

    A_step = shift_term(A, 1)
    a_step = shift_term(a, 1)
    successor_j = Succ(j)
    original_left = Add(Add(A_step, successor_j), Succ(a_step))
    successor_bridge = add_succ_at(Add(A_step, j), Succ(a_step))
    first_motive = Eq(
        Add(Var(0), shift_term(Succ(a_step), 1)),
        Succ(shift_term(Add(Add(A_step, j), Succ(a_step)), 1)),
    )
    first = EqSubst(
        first_motive,
        EqSym(pa4(A_step, j)),
        successor_bridge,
    )
    second = EqSubst(
        Eq(shift_term(original_left, 1), Succ(Var(0))),
        Hyp(0),
        first,
    )
    third = EqSubst(
        Eq(shift_term(original_left, 1), Var(0)),
        EqSym(pa4(Add(A_step, a_step), successor_j)),
        second,
    )
    result = ForallElim(
        Ind(motive, base, ForallIntro(ImpIntro(third))),
        n,
    )
    assert proof_size(result) == 51
    return result


def mul_succ_left_special(a, n):
    """Prove ``S a*n = a*n+n`` for these exact parameters (75 nodes)."""

    a_motive = shift_term(a, 1)
    j = Var(0)
    motive = Eq(
        Mul(Succ(a_motive), j),
        Add(Mul(a_motive, j), j),
    )
    base = chain(
        pa5(Succ(a)),
        EqSym(chain(pa3(Mul(a, ZERO)), pa5(a))),
    )

    a_step = shift_term(a, 1)
    product = Mul(a_step, j)
    successor_a = Succ(a_step)
    successor_j = Succ(j)
    original_left = Mul(successor_a, successor_j)
    first = EqSubst(
        Eq(
            shift_term(original_left, 1),
            Add(Var(0), shift_term(successor_a, 1)),
        ),
        Hyp(0),
        pa6(successor_a, j),
    )
    second = EqSubst(
        Eq(shift_term(original_left, 1), Var(0)),
        swap_special(product, a_step, j),
        first,
    )
    third = EqSubst(
        Eq(
            shift_term(original_left, 1),
            Add(Var(0), shift_term(successor_j, 1)),
        ),
        EqSym(pa6(a_step, j)),
        second,
    )
    result = ForallElim(
        Ind(motive, base, ForallIntro(ImpIntro(third))),
        n,
    )
    assert proof_size(result) == 75
    return result


def arithmetic_finish_special(w, n):
    """Prove ``(2*w+S n)+S n = 2*(w+S n)`` (65 nodes).

    The induction motive is the zero-offset identity
    ``(2*w+j)+j = 2*(w+j)``; the requested theorem is its ``j = S n``
    instance.  This makes the induction base just zero elimination.
    """

    w_motive = shift_term(w, 1)
    j = Var(0)
    twice_w = Mul(TWO, w_motive)
    motive = Eq(
        Add(Add(twice_w, j), j),
        Mul(TWO, Add(w_motive, j)),
    )

    twice_w_base = Mul(TWO, w)
    original_base_left = Add(Add(twice_w_base, ZERO), ZERO)
    left_to_twice_w = chain(
        pa3(Add(twice_w_base, ZERO)),
        pa3(twice_w_base),
    )
    base = EqSubst(
        Eq(shift_term(original_base_left, 1), Mul(TWO, Var(0))),
        EqSym(pa3(w)),
        left_to_twice_w,
    )

    w_step = shift_term(w, 1)
    twice_w = Mul(TWO, w_step)
    successor_j = Succ(j)
    old_left = Add(Add(twice_w, j), j)
    new_left = Add(Add(twice_w, successor_j), successor_j)
    old_witness = Add(w_step, j)
    successor_bridge = add_succ_at(
        Add(twice_w, j),
        successor_j,
    )
    first_motive = Eq(
        Add(Var(0), shift_term(successor_j, 1)),
        Succ(
            shift_term(
                Add(Add(twice_w, j), successor_j),
                1,
            )
        ),
    )
    first = EqSubst(
        first_motive,
        EqSym(pa4(twice_w, j)),
        successor_bridge,
    )
    second = EqSubst(
        Eq(shift_term(new_left, 1), Succ(Var(0))),
        pa4(Add(twice_w, j), j),
        first,
    )
    third = EqSubst(
        Eq(shift_term(new_left, 1), Succ(Succ(Var(0)))),
        Hyp(0),
        second,
    )
    right_normal = chain(
        pa6(TWO, old_witness),
        qtwo(Mul(TWO, old_witness)),
    )
    fourth = EqTrans(
        third,
        EqSym(right_normal),
    )
    fifth = EqSubst(
        Eq(shift_term(new_left, 1), Mul(TWO, Var(0))),
        EqSym(pa4(w_step, j)),
        fourth,
    )
    result = ForallElim(
        Ind(motive, base, ForallIntro(ImpIntro(fifth))),
        Succ(n),
    )
    assert proof_size(result) == 65
    return result


ORIGINAL_GOAL = parse_formula("forall n. exists x. n * (n + 1) = 2 * x")
STRONG_MOTIVE = Exists(
    Eq(
        Add(Mul(Var(1), Var(1)), Var(1)),
        Mul(TWO, Var(0)),
    )
)
STRONG_GOAL = Forall(STRONG_MOTIVE)

# Prove the recurrence-normal form ``n*n+n = 2*x`` by induction.  Choosing
# this stronger motive removes the repeated IH normalization from the step.
strong_base_equality = chain(
    pa3(Mul(ZERO, ZERO)),
    pa5(ZERO),
    EqSym(pa5(TWO)),
)
strong_base = ExistsIntro(ZERO, strong_base_equality)

# Strong step after eliminating the existential IH: x is #0 and n is #1.
x = Var(0)
n = Var(1)
successor_n = Succ(n)
right = Mul(TWO, Add(x, successor_n))

# Expand ``S n*S n`` using the successor-left lemma, then preserve equality
# while adding the final ``S n`` on both sides.
inner_expansion = EqSubst(
    Eq(
        Mul(shift_term(successor_n, 1), shift_term(successor_n, 1)),
        Add(Var(0), shift_term(successor_n, 1)),
    ),
    mul_succ_left_special(n, n),
    pa6(successor_n, n),
)
expansion = CongAdd(inner_expansion, EqRefl(successor_n))

# Transport the raw strong IH forward through both occurrences at once, then
# finish with the 65-node doubling identity.  This orientation avoids EqSym.
expanded_with_ih = EqSubst(
    Eq(
        shift_term(Add(Mul(successor_n, successor_n), successor_n), 1),
        Add(
            Add(Var(0), shift_term(successor_n, 1)),
            shift_term(successor_n, 1),
        ),
    ),
    Hyp(0),
    expansion,
)
strong_step_equality = EqTrans(
    expanded_with_ih,
    arithmetic_finish_special(x, n),
)

STRONG_CERTIFICATE = Ind(
    STRONG_MOTIVE,
    strong_base,
    ForallIntro(
        ImpIntro(
            ExistsElim(
                Hyp(0),
                ExistsIntro(Add(x, successor_n), strong_step_equality),
            )
        )
    ),
)
assert check((), STRONG_CERTIFICATE, STRONG_GOAL)
assert normalise_cuts(STRONG_CERTIFICATE) == STRONG_CERTIFICATE
assert proof_size(STRONG_CERTIFICATE) == 165

# Translate the recurrence-normal theorem to the user's stated expression
# once, outside the induction: n*(n+1) = n*n+n = 2*x.  Rewrite the whole
# existential proposition instead of opening and rebuilding its witness.
n = Var(0)
original_left = Mul(n, Add(n, ONE))
normal_left = Add(Mul(n, n), n)
original_to_normal = EqSubst(
    Eq(Mul(shift_term(n, 1), Var(0)), shift_term(normal_left, 1)),
    EqSym(qone(n)),
    pa6(n, n),
)
strong_instance = ForallElim(STRONG_CERTIFICATE, Var(0))
CERTIFICATE = ForallIntro(
    EqSubst(
        Exists(Eq(Var(1), Mul(TWO, Var(0)))),
        EqSym(original_to_normal),
        strong_instance,
    )
)

EXPECTED_NODES = 180


def metrics(proof):
    counts = Counter()
    maximum_depth = 0

    def visit(node, depth=1):
        nonlocal maximum_depth
        maximum_depth = max(maximum_depth, depth)
        counts[type(node).__name__] += 1
        for field in fields(node):
            child = getattr(node, field.name)
            if isinstance(child, Proof):
                visit(child, depth + 1)

    visit(proof)
    return maximum_depth, counts


def build_experiment():
    """Return the original target and its optimized certificate."""

    return ORIGINAL_GOAL, CERTIFICATE


def main():
    """Validate the experiment and print its reproducible size metrics."""

    target, certificate = build_experiment()
    normal = normalise_cuts(certificate)
    assert normal == certificate
    assert check((), certificate, target)
    assert check((), normal, target)
    assert proof_size(certificate) == EXPECTED_NODES

    depth, type_counts = metrics(certificate)
    rendered = render_certificate(certificate, ())
    print(f"proof_nodes={proof_size(certificate)}")
    print(f"proof_depth={depth}")
    print(f"rendered_characters={len(rendered)}")
    print("cut_normal=true")
    print("kernel_check=true")
    print("node_types=" + repr(dict(sorted(type_counts.items()))))


if __name__ == "__main__":
    main()
