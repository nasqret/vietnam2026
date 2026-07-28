# Fundamental theorem of arithmetic — Lean companion

This independently checked companion states the conventional theorem for
natural numbers using a finite list of primes:

\[
\forall n \ne 0,\; \exists F,\;
  \operatorname{prod}(F)=n \land
  \operatorname{AllPrime}(F) \land
  \forall G,\;
    (\operatorname{prod}(G)=n \land \operatorname{AllPrime}(G))
    \to G \sim F.
\]

Here `G ∼ F` is list permutation, so uniqueness is exactly up to factor order
and multiplicity. The empty list is the unique factorization of `1`.

The implementation in [`FTA.lean`](FTA.lean) separates the theorem into:

1. `prime_factorization_exists`;
2. `prime_factorization_unique`;
3. `fundamental_theorem_of_arithmetic`.

## Reproduce

```bash
cd artifacts/lean-fta
lake update
lake exe cache get
lake build
printf 'import FTA\n#print axioms ArithmeticFTA.fundamental_theorem_of_arithmetic\n' \
  > /tmp/fta-axioms.lean
lake env lean /tmp/fta-axioms.lean
```

The dependency is pinned to Mathlib commit
`37df177aaa770670452312393d4e84aaad56e7b6` (tag `v4.23.0`). The axiom audit
must report exactly Lean's standard `propext`, `Classical.choice`, and
`Quot.sound`; CI rejects `sorryAx`. These dependencies are explicit—not hidden
admissions.

## Trust boundary

This is a checked companion, not a new Peano Lab axiom. Peano Lab's unchanged
kernel still accepts only PA1–PA6, equality/logic rules, and induction. The
companion fixes the intended existence-and-uniqueness statement while the
Peano implementation develops a conservative natural-number encoding of
finite sequences and prefix products.
