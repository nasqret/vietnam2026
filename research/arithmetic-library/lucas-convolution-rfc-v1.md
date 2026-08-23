# Constructive Lucas prime-row convolution foundations

This isolated twelve-row tranche supplies dependency-curried, independently
kernel-checked first-order Heyting-arithmetic proof bodies for prime Pascal
rows and complete prime-block binomial coefficient congruences. No polynomial
primitive, classical axiom, Alpha enrollment, or Stable admission is introduced.

The first genuinely unbounded prime-block theorem is

```text
lucas_prime_shift_below_base:
  forall p a b C D.
    Prime(p) -> b < p ->
    Choose(p+a,b,C) -> Choose(a,b,D) ->
    ModEq(p,C,D).
```

Here `a` is completely unrestricted: the theorem covers every below-base
column in every pair of Pascal rows separated by a prime.  Its proof is an
ordinary constructive induction using exact relational Pascal recurrence,
the two row boundaries, and the divisibility of every interior coefficient
in the prime Pascal row. Its dependency-curried certificate has 224 proof
nodes, proof depth 44, and exact expanded-statement SHA-256
`4c888d1f6dd9974f52317bc48c2ab28f9ca5331c05fe362eab8b1403a6fbbcc7`.

The complementary unrestricted high-column theorem is

```text
lucas_prime_shift_high_column:
  forall p a j C A B.
    Prime(p) ->
    Choose(p+a,p+j,C) -> Choose(a,p+j,A) -> Choose(a,j,B) ->
    ModEq(p,C,A+B).
```

Neither `a` nor `j` is bounded. Together, the low-column and high-column
identities give the full constructive prime Pascal-row block shift: below
column `p` the old coefficient is unchanged; at column `p+j` the new
coefficient is congruent to the sum of the old coefficients in columns `p+j`
and `j`.

The high-column proof uses induction on `a`. The zeroth row follows from its
boundary and out-of-range cases. At successor rows, column `p` combines the
already-checked below-base shift at the predecessor of `p` with the old
column-`p` induction hypothesis. Higher columns combine the two adjacent
induction hypotheses through the exact Pascal recurrence and constructive
modular addition. Its dependency-curried certificate has 504 proof nodes,
proof depth 58, and exact expanded-statement SHA-256
`7b1c762ed80e5f588398b877dc372628b6f143bf9aae4bd289a0988bbb8f6ea0`.

Separate checked rungs prove lower-index equality transport, both zeroth-row
boundaries, explicit divisibility-to-congruence transport, bounded digit
complements, prime-row interior vanishing modulo the prime, positivity and
strict-order bridges, and the general modular Pascal-recurrence step. All
display predicates above expand exactly
to the original first-order language `{0,S,+,*,=}`.

This isolated factory itself does not claim the final one-step digit-product
congruence or the arbitrary-multidigit Lucas theorem. Those endpoints require
separate checked composition with coherent quotient/digit chains; independently
owned candidate factories may supply that additional evidence.

Focused verification:

```bash
cd peano-lab/py
python3 -m pytest -q --tb=line tests/test_lucas_convolution_candidate.py
```

These are isolated candidate bodies; empty-context closure, release admission,
and remote publication remain separate evidence gates.
