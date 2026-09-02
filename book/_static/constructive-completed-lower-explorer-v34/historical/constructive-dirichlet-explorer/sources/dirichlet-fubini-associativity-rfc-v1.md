# Constructed divisor grids and signed Dirichlet associativity

This additive mathematical checkpoint proves actual finite signed Dirichlet
associativity. It constructs the complete first/last-factor grid, its real
row and column sum tables, and the four intermediate/output convolution
tables. No divisor-pair permutation, grid, sum oracle, or rearrangement law is
supplied as a premise or encoded into a definition.

The immutable basis contains 3,643 prior statements: 3,222 Alpha v30 entries,
170 and 126 published non-admitted research theorems, and the subsequent 125
local non-admitted continuation theorems. Stable remains 432. The exact
parent catalogue SHA-256 is
`ac7111ec14ff07bf899238ed465de337e6d76e9343384947022360dc7e65d9f7`.
The new convolution core, finite-support and commutativity rows are genuine
cross-track prerequisites, not silently reclassified as Alpha or new rows
of this chapter. No existing source, definition identity, kernel, admission
policy, resource cap, or catalogue is changed.

## Conservative definitions and index conventions

All explanatory names below expand to ordinary HA formulas. `ArithTable`,
`ArithAt`, `SignedMul`, `SignedPrefixSum`, `ArithTableEqual`, `Le`, `Lt`, and
the actual rectangular slice/row-sum graphs are reused exactly. The core
convolution graphs retain their independent divisor-mask definitions.

```text
Triple(u,v,w,z) := ∃r. SignedMul(v,w,r) ∧ SignedMul(u,r,z).

Omitted(n,a,e) := a=0 ∨ (e=0 ∨ ¬((a*e) | n)).

GridEntry(F,G,H,n,a,e,z) :=
  (a≠0 ∧ e≠0 ∧ ∃c u v w.
    n=(a*e)*c ∧ ArithAt(F,a,u) ∧ ArithAt(H,e,v) ∧
    ArithAt(G,c,w) ∧ Triple(u,v,w,z))
  ∨ (Omitted(n,a,e) ∧ z=0).

FlatEntry(F,G,H,n,i,z) :=
  ∃a e. i=(S n)*a+e ∧ Lt(e,S n) ∧ GridEntry(F,G,H,n,a,e,z).

FlatPrefix(F,G,H,n,l,T) :=
  ArithTable(l,T) ∧ ∀i z. Le(i,l) → ArithAt(T,i,z) →
    FlatEntry(F,G,H,n,i,z).

Grid(F,G,H,n,T) :=
  ArithTable((S n)*(S n),T) ∧
  ∀a e z. Le(a,n) → Le(e,n) → ArithAt(T,(S n)*a+e,z) →
    GridEntry(F,G,H,n,a,e,z).

FactorRow(F,G,H,n,a,V) :=
  ArithTable(S n,V) ∧
  ∀e z. Le(e,n) → ArithAt(V,e,z) → GridEntry(F,G,H,n,a,e,z).
```

Thus a retained cell is exactly `F(a) * (H(e) * G(c))`, where the middle
factor `c` is actually witnessed by `n=(a*e)*c`. The two signed operations
are genuine inherited graphs, not arithmetic performed by a definition
oracle. The factor-grid relation contains no convolution equality.

`ArithTable(N,T)` certifies an inclusive bound, while a prefix sum of length
`l` uses exactly `i<l`. The physical square has `(n+1)^2` cells; its separately
certified final endpoint is not a cell or extra summand. Each row sum uses
exactly `S n` entries, including the forced zero at divisor index zero.
The strict remainder bound in `FlatEntry` is essential for unique decoding.

The public interfaces, all with keyword-only `tag` and `variables`, are:

```text
signed_dirichlet_grid_entry_relation(F,G,H,n,a,e,z,*,tag,variables)
signed_dirichlet_grid_table_relation(F,G,H,n,T,*,tag,variables)
signed_dirichlet_flat_entry_relation(F,G,H,n,i,z,*,tag,variables)
signed_dirichlet_flat_prefix_relation(F,G,H,n,l,T,*,tag,variables)
signed_dirichlet_factor_row_relation(F,G,H,n,a,V,*,tag,variables)
```

These accept compound terms and large numerals in an explicit declared
context. Every generated binder is checked against the entire context,
including unused variables. Unknown terms, malformed terms, incomplete or
duplicate contexts, reserved tags, and capture are rejected. This candidate
allocates no display IDs. Its definition DAG runs from the actual scalar
and table graphs through `GridEntry`, then `FlatEntry`/`FlatPrefix` and
`Grid`/`FactorRow`; the actual theorem DAG proves the sum identities later.

## Exact completed endpoints

The full constructive grid/Fubini endpoint is:

```text
∀F G H n. ArithTable(0,F) → ArithTable(0,G) → ArithTable(0,H) →
∃T R C z.
  Grid(F,G,H,n,T) ∧
  RectRows(T,R,0,S n,1,S n,S n) ∧
  RectRows(T,C,0,1,S n,S n,S n) ∧
  SignedPrefixSum(R,S n,z) ∧ SignedPrefixSum(C,S n,z).
```

Here `RectRows(T,R,o,s,t,m,n)` is the existing actual affine row-sum graph:
row `i<m` sums the actual source entries at `(o+s*i)+t*j`, for `j<n`.
Both row tables and both real cumulative histories are constructed. The
case `n=0` yields the one forced-zero physical cell and actual sum tables;
it does not assert convolution at input zero.

Write `CT(N,F,G,H)` for the exact core convolution-table graph and
`Conv(F,G,n,z)` for its actual positive-input sum graph. They contain
actual tables, masks and signed-prefix-sum witnesses. The intermediate
Fubini identity is:

```text
∀N F G H U V n a b.
  CT(N,H,G,U) → CT(N,F,G,V) → n≠0 → Le(n,N) →
  Conv(F,U,n,a) → Conv(H,V,n,b) → a=b.
```

The scalar associativity endpoint is:

```text
∀N F G H A B n u v.
  CT(N,F,G,A) → CT(N,G,H,B) → n≠0 → Le(n,N) →
  Conv(A,H,n,u) → Conv(F,B,n,v) → u=v.
```

The table version takes the four genuine `CT` frames below and concludes
`ArithPositiveEqual(L,R,N)`. The stronger construction endpoint supplies
all four frames itself:

```text
∀N F G H. ArithTable(N,F) → ArithTable(N,G) → ArithTable(N,H) →
∃A B L R.
  CT(N,F,G,A) ∧ CT(N,G,H,B) ∧ CT(N,A,H,L) ∧ CT(N,F,B,R) ∧
  ArithPositiveEqual(L,R,N).
```

`ArithPositiveEqual(L,R,N)` means equality of every pair of actual canonical
lookup values at precisely `0<n≤N`. It does not equate table codes,
noncanonical positive/negative component pairs, or arbitrary entries at
zero. At `N=0` the equality window is empty, but all four actual output
tables are still constructed. No positivity assumption on the signed
function values occurs anywhere.

## Proof route and actual dependencies

1. Constructively decide zero-factor and divisibility guards. Recover the
   real middle factor and construct all three signed lookups and both
   multiplications. Nonzero natural cancellation and canonical signed
   functionality prove cell uniqueness.
2. Use actual division by `S n` to decode every flat index. Ordinary
   induction, singleton construction and real two-beta append construct an
   inclusive flat prefix. Division uniqueness and the inherited proved
   row-major index bound recover every physical grid cell.
3. Extract actual affine row and column tables. A proved signed scalar
   interchange transposes each factor cell; no equation of raw encodings
   is assumed. The previously proved finite signed Fubini theorem constructs
   both outer sum tables and one common value.
4. A retained row with `n=a*q` is the pointwise scalar product of `F(a)` and
   a genuinely constructed padded convolution prefix for `H*G` at `q`.
   Prove `q>0` and `q≤n`; the finite-support zero-tail theorem removes only
   genuine zero padding. Actual signed scalar linearity identifies its sum.
   Zero and nondivisor rows are separately proved to sum to zero.
5. Functionality of the actual inner output table identifies each row total
   with the corresponding outer convolution summand. The column argument
   similarly identifies `H*(F*G)`. The actual finite Fubini witness yields
   the interchange identity.
6. The independently proved divisor-complement commutativity converts
   interchange to ordinary associativity. Actual core table existence
   constructs the two intermediates and both output tables; the scalar
   result gives positive-domain extensional equality.

Principal dependencies are `division_remainder_exists`,
`division_remainder_unique`, `arithmetic_signed_table_append`,
`signed_rectangular_row_major_fubini`, `signed_prefix_sum_scalar_multiply`,
`dirichlet_convolution_from_padded_prefix`, the actual core prefix/sum/table
constructors and functionality lemmas, and
`dirichlet_convolution_table_commutative`/`dirichlet_convolution_sum_swap`.
Source-helper imports are not additional mathematical premises.

## Inventory and verification boundary

| New source/factory suffix | Rows | Direct edges | Commands | Body occurrences |
| --- | ---: | ---: | ---: | ---: |
| `dirichlet_fubini_candidate` | 29 | 111 | 1,790 | 3,173 |
| `dirichlet_associativity_candidate` | 3 | 6 | 172 | 386 |
| Total | 32 | 117 | 1,962 | 3,559 |

Factories are `make_dirichlet_fubini_candidate_theorems` and
`make_dirichlet_associativity_candidate_theorems`, in that order. There are
3,552 body proof objects (one body shares seven objects), maximum depth 65.
Every body has passed the original HA kernel as an ordinary
dependency-curried certificate. All 32 statements are independently expanded
and compared as ASTs; exact novelty against all 3,643 prior statements and
each other passes. This body-level evidence is not a complete empty-context
bundle, independent Lean receipt, or Alpha/Stable admission. Those remain
separate integration gates requiring actual complete proof replay.

The ordered-name SHA-256 (newline separator, no final newline) is
`79cc448d034309a22b71a3213096c0546f296f0f2a3cf76076d2acc666ef3301`.
The exact combined ordered-spec SHA-256 is
`f00c81c55fe725c7595315fbec8345305bebb3e20f532e6c844c2156fa2fc6cf`.

Recommended principal ordinary replay roots and exact statement hashes:

| Root | Statement SHA-256 |
| --- | --- |
| `dirichlet_convolution_fubini_interchange` | `52ec70863e39714463cce993fd232ffe99a1a5e0c5a97f0daecfe5b41ed8e3bd` |
| `dirichlet_convolution_associative` | `7963b56c370b9ff42ae43dc3e12d13dd36b6bd1dd356b62269a062a6a90d6738` |
| `dirichlet_convolution_associative_tables_exists` | `f0e95e4639f59cc7b592d82384c2cf72b63e594814599db6b7bf24339b35adc1` |

The genuine constructor `dirichlet_grid_fubini_exists` is also pinned in
the tests at statement SHA-256
`84c13a3b8852328db17b1b2a3b7b6bf8939a9b5c62a1dccbabf9fbe2a6892675`;
it is actual checked ancestry of the interchange root, not a supplied grid.

Focused tests also pin every body metric, require all declared dependencies
to be used in topological order, reject every false target and absent body,
and individually remove or poison every declared dependency. Independent
beta diagnostics cover negative values, zero input/grid boundaries,
`N=0`, nondivisor cells, exact quotient bounds, real row/column traces,
strict-remainder decoding, harmless extra certified endpoints, zero padding,
and independently encoded output tables with different values at zero.

Each test CLI uses the unchanged CPU limits 170/175 seconds, 180-second
wall alarm and 1,536 MiB peak-RSS gate. `--pytest-select`, `--case-start` and
`--case-count` select fresh bounded batches; none increases a proof limit.
No numerical diagnostic, expected AST, source hash or cached receipt is
used as proof authority.

This chapter is the finite associativity substrate for G007. It does not,
by itself, claim the separate Möbius inversion endpoint or any new
admission/publication. The independent Möbius-value, unit, cancellation and
inversion proofs must still be composed and genuinely checked.
