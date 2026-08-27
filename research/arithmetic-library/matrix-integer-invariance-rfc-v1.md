# Determinant and rank invariance under genuine integer representations

Status: 27 additive original-kernel candidate bodies are implemented and
individually checked. They extend, without editing, the earlier 44 recursive
determinant and 55 rank bodies. This is not a full dependency-closure or Alpha
admission receipt; the independent release and Lean gates remain mandatory.

## Exact meaning

A signed integer is represented by a pair of naturals `(a,b)`, with value
`a-b`. Equality is `a+d=c+b`, not component equality. The shared integer-vector
surface from the column-span campaign is used directly on the `rows*cols`
actual row-major entries; no second incompatible equality definition is
introduced.

The determinant endpoint proves, in every natural dimension:

`IntegerMatrixEqual(A,B) ∧ Det(A,p,n) ∧ Det(B,P,N) → p+N=P+n`.

Both `Det` premises are genuine unrestricted recursive evaluation histories.
No supplied cofactor values, recurrence axiom, or smaller-dimension invariance
premise remains in this root. It does **not** claim `p=P` and `n=N`, which
would be false for noncanonical signed representatives.

The rank endpoint proves:

`IntegerMatrixEqual(A,B) ∧ Rank(A,r) ∧ Rank(B,s) → r=s`.

It also transports the full certificate itself: the actual nonzero minor at
rank and vanishing of every higher minor. This closes the representation
boundary explicitly left separate in the earlier determinant/rank RFCs.

## Proof layers

1. Signed-pair multiplication respects both input integer equalities. Actual
   even/odd cofactor terms inherit that equality, with parity checked.
2. Genuine arbitrary finite signed sums respect pointwise integer equality.
   The proof constructs one actual cross-sum beta code and applies checked
   finite-sum additivity twice; it does not assume a sum congruence rule.
3. Genuine cofactor minors share the actual skipped source row and column.
   Uniqueness of skip maps and quotient/remainder coordinates proves that all
   four component entries are compared at the same in-range parent position.
4. Dimension induction compares every genuinely evaluated cofactor stream,
   then the complete parity-correct fold. The empty determinant `(1,0)` is
   handled explicitly.
5. The rectangular layer handles arbitrary distinct, bounded row and column
   selectors, proves true selected-submatrix integer equality, and applies
   determinant invariance. A nonzero minor is transported with the same
   selectors and a newly constructed target evaluation; additive cancellation
   proves `P ≠ N`.
6. Universal higher-minor vanishing and the exact rank certificate transport.
   The previously checked uniqueness of determinantal rank finishes the
   representation-independent rank theorem.

There is no determinant multiplicativity, independent column-basis theorem,
Smith/Hermite normal form, lattice-index formula, geometric covolume theorem,
or LLL assertion in these rows.

## Exact inventory and resource boundary

- `make_matrix_integer_invariance_candidate_theorems`: 16 rows, 40 direct
  dependencies, 1,208 tactic commands.
- `make_matrix_rank_integer_invariance_candidate_theorems`: 11 rows, 28 direct
  dependencies, 721 commands.

Total: 27 rows, 68 direct dependencies, 1,929 commands, and 3,702 actual proof
objects/node occurrences. The largest body has 369 nodes; greatest actual
body depth is 137. The complete individually checked diagnostic peaked below
356 MiB RSS. Every proof still uses the unchanged original kernel; candidate
body metrics exclude all historical dependency bodies.

The ordered-name SHA-256 is
`7f6b47dca5abc0570871683bc2a8ec9ba10114761ae6a148d7450423fc85fae0`.
The determinant root statement SHA-256 is
`a5587046845e712ff96b73c8fc4f54b9ecfeac5cfa224a1d537c6ce20f728dd6`;
the rank root statement SHA-256 is
`d6c74c06c5a55da7ec89d026a4658e49604b6f6b11521d1b453c8bfa16168151`.

Tests pin every body metric, all principal statement hashes, exact integer
cross-sum semantics, the unconditional induction boundary, inherited binder
capture rejection, false-conclusion and missing-dependency mutations, and
rejection of an unsupported component-equality replacement.
