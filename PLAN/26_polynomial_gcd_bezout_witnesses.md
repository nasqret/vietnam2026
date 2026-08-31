# Polynomial gcd/Bézout: actual witness route after associativity

Continuation of the user's 2026-08-31 instruction: shift/scalar laws,
associativity, then gcd/Bézout. This document is an implementation route,
not a theorem, admission receipt or claim of full G091 completion.

## Representation and current first tranche

A polynomial is a triple `(b,c,L)` with highest-degree-first coefficients.
`Coeff(p,A)` below is the existing `BetaPrefixInto` expansion, and `A ≃ B`
is the existing all-power `PolynomialEquivalent` expansion. Actual products
are the existing `FpPolyProduct`, including their proper-length relation.
These shorthands introduce no duplicate definitions or new kernel symbols.

The new working definition `ND0342 FpPolynomialRightDivides(p,D,A)` is:

```text
Coeff(p,A) ∧ ∃Q P. FpPolyProduct(p,Q,D,P) ∧ PolynomialEquivalent(P,A).
```

Each quantified polynomial stands for three actual natural variables, not
an abstract object or an oracle. In particular the divisor is the right
factor and the quotient is on its left. The canonical quotient/divisor
guards come from the actual product. Different codes and lengths are allowed.

Seven native candidate bodies are implemented in
`research/arithmetic-library/working/prime-field-divisibility-v1/`:
introduction from a real product, divisor/target canonicality, equivalent
target transport, division of the empty polynomial, equivalent divisor
transport, and transitivity via the actual composite quotient `Q₂*Q₁`.
The transitivity row constructs three genuine intermediate products and
uses the exact associativity statement. It does not assume commutativity.

Current evidence: 95 source/model/hygiene cases, 81 combined-map cases and
all seven positive original conditional HA bodies passed. All 61 rejection
cases also passed, completing 163 focused cases. The separate 44-row complete
cone has now passed all thirteen fresh final proof gates; no new Alpha
admission is claimed.

A separate eight-row left-unit/reflexivity source checkpoint is implemented
in `working/prime-field-left-unit-v1`, outside the 44 integration. Its 466
native commands and 35 declared dependencies have 92 source/model checks and
91 combined 52 notation checks passed. All eight original conditional HA
bodies also passed without source changes. All 94 rejection cases passed
in six clean windows, completing 194 focused cases. The separate 52-row
dependency cone has now passed all fourteen fresh final gates, including
the 11,736-node closed reflexivity certificate.
No proof is inferred from the source-only map, which reuses all 399 working
definition identities.

An independent source-only audit found a complete 44-row route with 248
canonical ancestors, 292 mathematical nodes and 835 theorem-dependency edges.
The 43→44 split has now genuinely authored both stages using fresh original
HA checks of every real seed and every complete package body. The actual 44
candidate has 293 nodes, 846 edges, 24,049 body nodes and 11 maximal roots;
its 1,757,906 bytes have SHA-256
`6fb92e887c2ddd604e71574095fdf492814af9651e15f0b36386be3538b1a7e7`.
All thirteen separate fresh final novelty, HA/Lean and ordinary-root gates
passed under a single final source binding. The ordinary transitivity
certificate has 30,634 nodes. No authoring report was substituted for those
acceptance gates. The separate 52-row integration has now passed genuine
authoring from the real 44 and products210 seeds: 306 nodes, 888 edges and
25,043 body nodes. Its unchanged 326 source/inert guards passed both before
authoring and after literal artifact registration. All fourteen fresh final
gates passed under one final binding: current-Alpha novelty, full original
HA and same-byte compiled Lean, and twelve original ordinary-root replays.
The artifact is 1,837,245 bytes with SHA-256
`4051c93175faed973fb3b88d963fdd03f15514e481aab9516d56b7b1e67c44c4`.
This is working-checkpoint acceptance, not Alpha admission or gcd/Bézout.

Only two canonical targets are added beyond the 37-row cone:
`matrix_rank_bounded_prefix_empty` and
`prime_field_polynomial_convolution_empty`. Their exact targets and ordered
premises occur in the existing polynomial202 and polynomial-products210
bundles respectively. Genuine authoring freshly checked those real seeds
and the actual37 artifact. The earlier source/transport analysis itself
grants no proof authority; it is retained in
`prospective-closure-observations-v1.json` beside the candidates.

## Required order and contracts

1. All 700 focused associativity cases and all 163 right-divisibility cases
   passed. Complete-cone integration of both sets is verified. The
   actual 37-row associativity bundle has now passed all eight fresh gates,
   including complete HA, same-byte Lean and the ordinary full associativity
   root. Preserve its independently checked empty-factor cases and formal
   rather than evaluation equality. The separate seven-row divisibility
   extension has its own thirteen-gate 44-row acceptance record.
2. The actual left-unit convolution, length-one encoding and `D | D` are
   now proved in the separate 52-row checkpoint, with actual coefficient
   witnesses including the empty input. All 194 focused cases passed.
   Reuse those witnesses for the gcd base combinations. A right-constant
   lemma or unproved multiplication commutativity is not their proof.
3. Give actual alignment graphs for sums and differences at independent
   lengths, using leading-zero padding, existing coefficient addition and
   subtraction, and formal equivalence. Prove their transport, reassociation
   and cancellation laws; construct alignment/product witnesses before use.
4. Prove linear-combination and Euclidean backward transport. For an actual
   division identity `A ≃ Q*B + R`, show common-divisor equivalence of `(A,B)`
   and `(B,R)`. From actual `G ≃ U*B + V*R`, construct the witnesses for
   `G ≃ V*A + (U - V*Q)*B`. The minus sign is field subtraction with genuine
   bounded coefficients; all products and aligned sums must be actual.
5. Use the genuine remainder-degree bound for well-founded construction of
   a gcd and Bézout coefficients. Quantify intermediate polynomial codes
   and lengths in the induction predicate. Handle a zero second input and
   `(0,0)` separately; never assign an ordinary nonnegative degree to zero.
6. Normalize a nonzero result by its actual leading-coefficient inverse,
   transport gcd and Bézout witnesses through this scale, and retain zero
   for `(0,0)`. Prove uniqueness only for the normalized represented gcd
   up to formal equivalence, not for raw codes or Bézout coefficients.

### Implemented step 2: actual left-unit route

Source inspection found an existing zero-tail sum invariant, so this step
need not add a general finite-sum induction or assume polynomial
commutativity. For a genuine length-one left input `U` with `At(U,0,1)`,
the diagonal coefficient at index `i` has first term `A_i` and all its
remaining `i` terms zero. The canonical
`polynomial_zero_tail_natural_sum_invariant` compares those actual sums.
The proof uses actual diagonal entries, `beta_sum_exists`,
`beta_sum_succ_decompose`, `beta_sum_zero` and
`prime_field_residue_bounded_value` to derive the left-unit coefficient
lemma, then lifts through actual convolution entries to decoded-prefix
equality and formal equivalence.

Construct `U` with `prime_two_le` and
`prime_field_polynomial_repeat_exists(p,1,1)`. The implemented endpoint is,
in schematic notation:

```text
Prime(p) → Coeff(p,A,L) → ∃ub uc cb cc.
  Coeff(p,U,1) ∧ At(U,0,1) ∧ Conv(p,U,1,A,L,C,L) ∧ Equivalent(C,L,A,L).
```

The proof establishes the actual product length `Length(1,L,L)`, including
its `L=0` branch. The genuine at-length product constructor therefore
produces output length `L`, with an empty output when `L=0`, not a
length-one output. It then applies the already verified
`prime_field_polynomial_right_divides_from_product` to obtain reflexivity.
This route now has the eight separate native candidates described above,
with every original conditional HA body verified and separate complete-cone
HA/Lean/ordinary acceptance passed. All their focused rejection tests passed.
The constructor does not assume a nonempty product.

### Existing entry points for the next aligned-algebra tranche

Read-only source inspection identifies the following reusable interfaces;
this list supplies no additional proof or admission credit:

- `prime_field_polynomial_candidate.py`: genuine fixed-length addition,
  coefficient entry/boundedness, independent recoding transport, and
  fixed-length associativity. These do not yet align independent lengths.
- `prime_field_polynomial_subtraction_candidate.py`: actual coefficient
  subtraction `B_i + R_i = A_i`, with construction, entry, boundedness,
  functionality and recoding transport at one common length.
- `prime_field_polynomial_representation_candidate.py`: actual leading-zero
  padding, its canonicality and formal equivalence, conversion from formal
  equivalence to decoded equality at equal lengths, and common-padding
  transport for addition/subtraction/scaling. The latter requires the same
  old length and the same padding count for every operand; independent
  alignment still needs a separate proof.
- `prime_field_polynomial_equivalence_candidate.py`: the existing
  `prime_field_polynomial_add_equivalent_congruent` and subtraction analogue
  compare actual operations already aligned at lengths `L` and `K`, with
  pairwise equivalent operands. Reuse these output-transport laws after
  constructing alignments; they do not construct an operation on two
  independently sized original operands.

All four files are under `peano-lab/py/peano_lab/library/`. Keep their
existing definitions and identities. The next tranche should first build
real equal-length padded witnesses, then use these coefficient laws and
formal-equivalence transport. Its examples and rejection tests must cover
unequal lengths, leading zeros, empty inputs and unrelated beta encodings.
It belongs in a new checkpoint; none of these future bridges enlarges or
refreezes the fixed 52-row integration.

## Intended final interface — not implemented or registered yet

`RightGcd(p,G,A,B)` will require `G | A`, `G | B`, and every actual common
right divisor to divide `G`. `Bezout(p,G,A,B,U,V)` will witness both actual
products `U*A` and `V*B`, actual leading-zero alignments, an actual sum, and
formal equivalence of that sum to the canonical `G`. Neither relation may
hide gcd existence or an algebraic conclusion in a constructor premise.

The final existence contract is schematically:

```text
∀p A B. Prime(p) → Coeff(p,A) → Coeff(p,B) →
  ∃G U V. RightGcd(p,G,A,B) ∧ Bezout(p,G,A,B,U,V)
           ∧ (ZeroPolynomial(G) ∨ MonicPolynomial(p,G)).
```

All triple quantifiers and new interfaces must be expanded hygienically
over the unchanged HA signature before any body is counted. None of these
future interface names currently denotes an admitted library definition.

## Release and resource boundary

Alpha v33 remains 4,092; Stable remains 432. The unchanged 4,096-entry
transport limit leaves four slots. Larger promotion requires a separately
reviewed capacity design; these working checkpoints do not silently raise it.
Keep original per-job CPU 170/175 seconds, wall 180 seconds, observed RSS
1,536 MiB and live proof depth 256. Run at most one heavyweight proof job.
Complete HA, same-byte compiled Lean, original ordinary-root replays and
current-catalogue novelty remain mandatory before complete-bundle claims.
