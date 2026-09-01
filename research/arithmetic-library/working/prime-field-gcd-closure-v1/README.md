# Recursive prime-field polynomial gcd and Bézout

This working checkpoint joins the unchanged [95-row Euclidean
checkpoint](../prime-field-euclidean-closure-v1/README.md) with 24 new rows:
four Bézout laws, nine recursive-existence rows, and eleven uniqueness rows.
All 24 new theorems now have dependency-complete verification. The final
bundle passed the original HA kernel and the independent compiled Lean
checker on identical authenticated bytes. All 14 principal results also
passed ordinary, empty-context HA reconstruction and checking. This is a
verified local working checkpoint, not an Alpha or Stable admission.

## Mathematical contract

For every prime `p` and canonical coefficient representations `A,B`, the
existence endpoint constructs actual beta-coded representations `G,U,V` with

```text
NormalizedGcd(p,G,A,B) and BezoutRepresentation(p,A,B,G,U,V).
```

Each polynomial denotes a beta-code/scale/length triple. Coefficients in its
represented, highest-degree-first prefix are natural residues less than `p`.
Formal equivalence compares coefficients at every natural power, taking
coefficients outside the represented support to be zero; it does not constrain
unrelated beta entries or merely compare evaluations on the finite field.

The [conservative definition registry](../prime-field-gcd-notation-v1/working_gcd_notation.py)
uses these exact grouped graphs:

- **ND0348 — FpPolynomialZeroOrMonic:** `Glen=0` or canonical monic `G`.
- **ND0349 — FpPolynomialRightGcd:** `G` is a common right divisor of `A,B`,
  and every common right divisor `D` right-divides `G`.
- **ND0350 — FpPolynomialNormalizedGcd:** ND0348 and ND0349 together.

The existing right-divisibility orientation is `D |r A` when a genuine
product `Q*D` is formally equivalent to canonical `A`. Greatestness is this
universal divisibility property, not a numerical maximum. Bézout contains
actual products `U*A`, `V*B` and an aligned sum formally equivalent to `G`.
Any two normalized gcds of the same inputs are formally coefficientwise
equivalent. Neither their raw beta codes nor their Bézout coefficients `U,V`
are asserted unique.

## Constructive recursion and source families

The [existence source](../prime-field-gcd-existence-v1/prime_field_polynomial_gcd_existence_candidate.py)
inducts on a bound for the second input's length, universally quantifying both
inputs. It first trims the second input: a nonempty all-zero prefix is not a
nonzero polynomial. For a retained divisor `T` of represented degree `d`,
actual division gives `A ≃ Q*T+R` and `Rlen ≤ d < Tlen`. The recursive
witnesses for `(T,R)` update by
`(G,U,V) → (G,V,U−V*Q)`, using actual products, aligned subtraction and
formal-equivalence transport back to the original second input.

The empty-second branch constructs a zero-or-monic associate of the first
input. Thus zero inputs and leading-zero encodings are included; `(0,0)` has
empty normalized gcd, not one. No degree is assigned to zero. Characteristic
two is included in the prime hypothesis.

The [Bézout laws](../prime-field-gcd-bezout-laws-v1/prime_field_polynomial_gcd_bezout_laws_candidate.py)
provide terminal witnesses, equivalent-input transport and the implication
that every common divisor divides a Bézout representative. The recursion
separately retains that `G` divides both inputs. The
[uniqueness source](../prime-field-gcd-uniqueness-v1/prime_field_polynomial_gcd_uniqueness_candidate.py)
proves zero-or-monic mutual associates formally equivalent, using actual
quotient trimming, product degrees and a left-unit product; it then applies
the two greatestness clauses to normalized gcds.

## Completion evidence

The [registered plan](working-gcd-closure-rfc-v1.md) fixes 119 working rows and
373 canonical dependencies. The complete source cone has 492 theorem nodes;
packaging its 13 maximal roots requires 493 nodes and 1,578 edges. The
[full source DAG](../prime-field-gcd-notation-v1/complete-source-dag-v1.json)
also records conservative definition relationships, which confer no proof
authority.

All ten actual authoring stages and all 16 final gates passed: novelty against
all 4,092 current Alpha theorem ASTs, complete original HA plus independent
compiled Lean on the same payload, and 14 ordinary empty-context HA roots.
The final [proof bundle](artifacts/working-gcd-closure-prefix-119-proof-bundle-v1.json)
has 493 nodes, 1,578 edges, 47,545 body nodes and 5,193,292 bytes. Its SHA-256 is
`3fe18ad2899cff7db5fbe19df8570ef70b1bfb902171d5212e9b036dda660a46`.
Every final gate used the same source binding
`ea10c4b28b0a0ebaf55616bfa291f93011322764349c6ad8eccbc11ad2582c1d`.

The three requested ordinary certificates contain 56,067 nodes for normalized
gcd/Bézout existence, 24,581 for normalized uniqueness, and 36,635 for Bézout
greatestness. See the [actual final verification records](final-verification-observations-v1.json)
and [completion accounting](completion-accounting-v1.json).

The [focused-test audit](independent-focused-accounting-v1.json) reconciles
938 distinct cases: 320 Bézout-law, 86 recursion/greatestness, 415 uniqueness,
and 117 notation/control cases. The final 117 source/notation cases were also
rerun against the registered artifact; this repeat receives no extra distinct
test credit. The source DAG contains 407 conservative definitions, preserving
all 404 predecessors and adding ND0348–ND0350. Its source-only generation
record is not itself proof authority; the verified mathematical source
identities are linked through the completion record.

The original CPU 170/175 s, wall 180 s, RSS 1,536 MiB, depth-256 and other
kernel/codec limits remain intact. All authoring and final-verification
processes passed on their first runs. Earlier rejected development attempts
remain recorded; a zero-call status-poll syntax typo did not restart or affect
any proof process. No saved observation grants permission to skip verification.

This checkpoint performs no Alpha/Stable promotion or deployment. Full G091
remains open: arbitrary prime-power field construction is not established by
prime-field polynomial gcd, Bézout and uniqueness.
