# Genuine constructive rank of arbitrary rectangular signed matrices

Status: 55 additive ordinary-kernel candidate bodies are implemented and
checked over the immutable Alpha-v26 statement surface and the 44 new actual
recursive-determinant bodies. This is not an Alpha admission or full closure
receipt. Historical bodies and these exact endpoints still require the
independent release-bundle and Lean gates.

## Exact endpoint

Every signed beta-coded `rows × cols` matrix has exactly one natural
determinantal rank. Its certificate contains all four facts:

1. `rank ≤ rows`;
2. `rank ≤ cols`;
3. actual distinct in-range row and column selectors of length `rank`, an
   actual selected submatrix, and a genuinely evaluated determinant `(p,n)`
   with `p ≠ n`;
4. for **every** order `k > rank`, every actual `k`-minor evaluates to a signed
   pair with equal components.

In particular all `(rank+1)`-minors vanish. Nonzero means the signed
difference is nonzero, not that one of its natural components is nonzero.
The zero-order minor has the actual determinant `(1,0)`, and explicit roots
prove rank zero for zero-row and zero-column matrices without any positive
dimension premise.

This is determinantal rank. No equivalence with a separately formalized
dimension of rational column space, independent lattice basis, echelon form,
Smith/Hermite form, index formula, Cramer rule, or LLL claim is inferred.

## Conservative definition DAG

All displayed relations expand into the unchanged first-order HA signature.
No matrix, vector, rank, search, or determinant primitive is added to the
kernel.

- `UniformBetaPrefixBox(c,T,k,B)` chooses one fixed scale and one positive
  finite code bound **before** quantifying over arbitrary source codes. Every
  length-`k` prefix with values below `B` has an entry-preserving recoding
  `(z,c)` with `z < T`.
- `FiniteMatrixSelector(b,c,k,B)` combines an actually decoded prefix with
  values below `B` and injectivity on its whole finite index domain. Selectors
  are lists of distinct indices, not necessarily sorted lists; all such
  choices are included.
- `SignedSelectedSubmatrix` decodes each flattened child position into row
  and column indices, decodes both selectors, and reads the corresponding
  actual parent entry at `sourceRow*cols+sourceColumn` in both sign streams.
- `SignedSelectedDeterminant` contains that actual submatrix and the existing
  unrestricted recursive determinant history. Supplied unrelated numerical
  values are not accepted as determinants.
- `NonzeroSelectedMinor` adds both valid selectors and `p ≠ n`.
  `NonzeroMatrixMinor` existentially quantifies those actual selectors.
- `AllSignedMinorsZero` universally quantifies all selectors and actual
  determinant values at one order and concludes `p=n`.
- `RectangularMatrixRank` packages the two dimension bounds, a genuine
  nonzero minor, and universal vanishing at every larger order.

## Why the search is finite and complete

Unbounded existential beta-code parameters are not assumed decidable. The
first 19 rows construct the missing uniform recoding bound. A common multiple
selects one fixed beta scale large enough for the requested value bound.
Constructive CRT recodes every existing bounded prefix at that scale. A
second fixed positive common multiple of the finite beta moduli lets us
reduce the new code to a bounded remainder while preserving every entry.

Selector bounds are decided by actual finite-prefix induction and beta
decoding. Injectivity is decided by the previously proved witnessed
collision-or-injection theorem. Constructive pigeonhole proves that every
such selector's length is at most its ambient dimension.

The next 21 rows construct actual selected submatrices, prove cell and
determinant functionality, and prove transport across the complete selector
recoding. Every candidate's determinant is therefore genuinely evaluated
before its nonzeroness is decided.

The final 15 rows instantiate ordinary HA finite search twice, once for each
bounded selector code. The recoding proof establishes that this search finds
every genuine nonzero minor, irrespective of its original unbounded codes.
A further finite dimension induction picks the greatest nonzero order up to
the row count. Every actual minor is already bounded by both dimensions, so
this finite maximum proves universal vanishing at all higher orders.
Uniqueness follows from either strict inequality contradicting the other
certificate's actual nonzero witness.

## Validation and exact inventory

The three factories, in order, are:

1. `make_matrix_rank_finite_coding_candidate_theorems`: 19 rows, 49 declared
   dependencies, 568 tactic commands;
2. `make_matrix_rank_selected_minors_candidate_theorems`: 21 rows, 38
   dependencies, 1,068 commands;
3. `make_matrix_rank_certificate_candidate_theorems`: 15 rows, 38 dependencies,
   709 commands.

Together: 55 rows, 125 direct dependencies, 2,345 tactic commands, and 4,104
actual proof objects/node occurrences. The largest body has 317 nodes and
the greatest actual body depth is 102. The complete individually checked
55-body diagnostic stayed below 245 MiB measured peak RSS. These are only
new-body metrics, not full dependency-closure metrics.

The ordered-name SHA-256 is
`2fd23d962c15888ebacae62d9f8a718f376e0287cfc0a992abbcb42b38e645ad`.
The principal `rectangular_matrix_rank_exists_unique` statement SHA-256 is
`677f945b5341792d5b2281cc8948922456c461c1aeeec880c452199df7d178f1`.
Tests pin every body metric, all eight principal endpoint statements, the
unconditional quantifier boundaries, signed nonzeroness, finite search-box
quantifier order, dependency removal rejection, false-conclusion rejection,
and capture prevention for inherited and newly generated binders.

The original v26 catalog is used only as a pinned source of exact statements,
scripts, and dependencies for bounded candidate authoring. Its hash is not
proof authority; complete closure and independent Lean verification remain
release obligations.

## Signed representation boundary

The present rows prove invariance under recoding with exactly equal positive
and negative entries. They do not yet identify different component pairs
representing the same integer. Determinant signed-quotient invariance
(`ap+bn=bp+an` entrywise implies `p+n'=p'+n`) and the resulting rank invariance
are separate additive obligations. The column-span campaign independently
uses genuine signed-difference equality; it does not supply an unproved rank
or determinant representation-invariance premise here.
