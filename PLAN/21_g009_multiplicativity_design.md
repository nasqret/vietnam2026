# G009: finite signed multiplicativity and convolution closure

Date: 2026-08-29. Status: design and source-inventory audit only.

This note adds no theorem, proof certificate, admission, definition identifier,
or completion claim. The proposed bridges below have not been implemented or
proved by this note. Existing theorem names were checked against their source
files; no large proof replay was performed for this design audit. Release work
is tracked separately in [PLAN/20](20_dirichlet_release_and_multiplicative_closure.md).

## Original obligation and proposed exact relation

[PLAN/14, G009](14_constructive_number_theory_grand_campaign.md) requires
`Multiplicative(f) /\ Multiplicative(g) -> Multiplicative(f*g)` on nonempty
coded finite positive-index prefixes or specified HA-provably total function
codes. Its multiplicative-closure clause remains an obligation even though
the condensed historical atlas statement does not repeat it. Associativity,
the delta identity, and the signed-unit inverse criterion do not by themselves
prove multiplicative closure.

There is no reviewed general finite multiplicativity definition in the current
definition registry. In particular, the existing specialized theorem
`totient_coprime_multiplicative` is not a theorem about arbitrary arithmetic
tables.

Proposed public builder, subject to the implementation owner's final choice:

```text
signed_multiplicative_prefix_relation(N, F, *, tag, variables)

MultiplicativePrefix(N,F) :=
  ~(N=0) /\ ArithTable(N,F) /\ ArithAt(F,1,2) /\
  forall a b x y z.
    ~(a=0) -> ~(b=0) -> Le(a*b,N) -> Coprime(a,b) ->
    ArithAt(F,a,x) -> ArithAt(F,b,y) -> ArithAt(F,a*b,z) ->
    SignedMul(x,y,z).
```

The displayed names are conservative first-order notation for existing
graphs, not new kernel operations. The builder must use the established
explicit-context hygiene checks, including compound terms, large numerals,
and unused declared variables that collide with generated binders. No new
definition IDs are assigned here.

Actual expansion dependencies are `ArithTable`, `ArithAt`, `Le`, `Coprime`,
and `SignedMul`. There is no `SignedUnit` subformula: signed positive one is
the exact canonical code **2**, whereas signed negative one has code **1**.
The two-argument finite relation must not silently alias a one-argument
planning expression `Multiplicative(f)`.

The universal lookup form follows the existing `DirichletTable` convention.
Actual table validity supplies genuine lookup witnesses; the property is not
a vacuous assertion about a function with no entries. One could instead prove
an equivalent existential-value presentation, but it must not be silently
substituted for the chosen definition graph.

### Bounds and zero

- `ArithTable(N,F)` has an inclusive certified domain through index `N`.
  Multiplicativity concerns only `0<a`, `0<b`, and `a*b<=N`.
- Separate bounds `a<=N` and `b<=N` do not replace `a*b<=N`. On positive
  inputs they follow from the product bound; they do not imply it.
- Valid packed beta tables have actual values at every requested index, by
  `signed_table_lookup_any`. Values outside the chosen finite prefix exist
  but are **unconstrained by that prefix**. Finite-prefix extensionality must
  not depend on them.
- The proposed strict relation excludes `N=0`, as the original G009 contract
  does. Existing zero-window convolution and inverse theorems remain valid
  and separate. A broader empty-prefix multiplicativity convention, if ever
  needed, must be defined explicitly rather than imposing `F(1)=+1` on an
  empty positive domain.
- At `N=1`, normalization is the only nontrivial data requirement. The values
  at zero of inputs and outputs remain arbitrary. Positive-value uniqueness
  never means equality of table encodings or of their zeroth values.

## Proposed completion endpoints

These are target contracts, not existing theorem names or proved results.

```text
forall N F G m n x y z.
  MultiplicativePrefix(N,F) -> MultiplicativePrefix(N,G) ->
  ~(m=0) -> ~(n=0) -> Le(m*n,N) -> Coprime(m,n) ->
  DirichletSum(F,G,m,x) -> DirichletSum(F,G,n,y) ->
  DirichletSum(F,G,m*n,z) -> SignedMul(x,y,z).

forall N F G H.
  MultiplicativePrefix(N,F) -> MultiplicativePrefix(N,G) ->
  DirichletTable(N,F,G,H) -> MultiplicativePrefix(N,H).

forall N F G.
  MultiplicativePrefix(N,F) -> MultiplicativePrefix(N,G) ->
  exists H. DirichletTable(N,F,G,H) /\ MultiplicativePrefix(N,H) /\
    (forall K. DirichletTable(N,F,G,K) -> ArithPositiveEqual(H,K,N)).
```

The final existential endpoint must use the existing actual convolution-table
constructor, not assume an output table or a sum value. An explicit
prescribed-zeroth-value constructor would be an additional result and is not
assumed here. Useful accompanying targets are transport across actual
positive-prefix equality and restriction to `0<K<=N`.

## Existing theorem and dependency inventory

All paths below are under `peano-lab/py/peano_lab/library/`. A helper-module
import is not a proof-dependency edge. The proposed implementation must record
only theorem dependencies actually used by its checked proof bodies.

### Canonical signed arithmetic

- `ha_signed_mul_candidate.py`: `signed_mul_total`,
  `signed_mul_functional`.
- `ha_signed_mul_laws_candidate.py`: `signed_mul_commutative`,
  `signed_mul_zero_left`, `signed_mul_zero_right`, `signed_mul_one_left`,
  `signed_mul_one_right`. The one laws use canonical signed code 2.
- `ha_signed_mul_associative_candidate.py`: `signed_mul_associative`.
- `ha_signed_mul_distributive_candidate.py`:
  `signed_mul_left_distributive`.

These graphs already support the four-factor rearrangement needed to compare
`F(a*b)*G(u*v)` with `(F(a)*G(u))*(F(b)*G(v))`. Any new convenience wrapper
must prove the relational statement with actual intermediate products.

### Actual tables and linear sums

- `signed_table_operations_candidate.py`:
  `signed_table_domain_resize(N,M,F)` proves
  `ArithTable(N,F) -> ArithTable(M,F)`;
  `signed_table_lookup_any(N,F,i)` constructs an actual lookup at `i`.
  `signed_table_scalar_exists(l,a,F)` constructs `G` satisfying
  `ArithScale(a,F,G,l)`. The strict operation window is `i<l`, while the
  table certificate includes the harmless endpoint `i=l`.
- `arithmetic_table_extension_candidate.py`:
  `arithmetic_signed_table_extend_at(N,F,l,z)` constructs a new valid table
  preserving all entries `i<l` and installing canonical value `z` at `l`.
  `arithmetic_signed_sum_exists(N,F,l)` constructs `z` with
  `SignedPrefixSum(F,l,z)`. Its direct dependencies are
  `divisor_signed_table_components` and
  `divisor_signed_sum_exists_from_components`.
- `signed_sum_linearity_candidate.py`:
  `signed_prefix_sum_scalar_multiply` has the exact shape
  `forall l a F G b c. ArithScale(a,F,G,l) ->
  SignedPrefixSum(F,l,b) -> SignedPrefixSum(G,l,c) -> SignedMul(a,b,c)`.
  Its direct dependencies are `divisor_signed_sum_empty_value`,
  `signed_mul_zero_right`, `divisor_signed_sum_successor_decompose`,
  `signed_table_scalar_restrict`, `signed_table_scalar_lookup`, `le_refl`,
  and `signed_table_scalar_add_intro`.
  The companion `signed_prefix_sum_scalar_multiply_values_exist` constructs
  both sum values. `signed_prefix_sum_pointwise_add` is also available.

### Fubini and zero support

- `signed_rectangular_slice_candidate.py`:
  `signed_rectangular_slice_exists`,
  `signed_rectangular_slice_sum_exists_unique`,
  `signed_rectangular_slice_sum_successor_decompose`, and
  `signed_rectangular_slice_sum_successor_add` use actual affine indices
  `o+s*i`.
- `signed_rectangular_sums_candidate.py`:
  `signed_rectangular_fubini` proves equality of the actual rectangular sums
  with `(s,t,m,n)` and `(t,s,n,m)` interchanged.
  `signed_rectangular_fubini_exists(F,o,s,t,m,n)` constructs both row and
  column tables and a common sum from `ArithTable(0,F)`. Its direct
  dependencies are `signed_rectangular_row_sums_exists`,
  `arithmetic_signed_sum_exists`, and `signed_rectangular_fubini`.
  `signed_rectangular_row_major_fubini(F,m,n)` specializes this to strides
  `(n,1)` and dimensions `(m,n)`; it depends on
  `signed_rectangular_fubini_exists` and `signed_table_domain_resize`.
- Important missing bridge: `signed_rectangular_row_major_fubini` does
  **not** assert `SignedPrefixSum(F,m*n,z)`. It proves equal row and column
  totals. Flattened-prefix equality still needs a checked block/slice sum
  argument.
- `signed_finite_support_candidate.py`:
  `signed_prefix_sum_zero_tail(F,k,l,a,b)` proves `a=b` from `k<=l`, a
  genuinely zero window `[k,l)`, and the two actual prefix sums.
  `signed_prefix_sum_last_value(F,l,a,z)` proves `z=a` from a zero window
  `[0,l)`, `ArithAt(F,l,a)`, and `SignedPrefixSum(F,S l,z)`.
  Together with actual sum existence these provide a route to a new
  arbitrary-position single-spike lemma. That lemma is not yet present.

### Convolution and coprime divisors

- `dirichlet_convolution_candidate.py`:
  `dirichlet_convolution_sum_exists_unique`,
  `dirichlet_convolution_table_lookup`,
  `dirichlet_convolution_positive_source_extensional`,
  `dirichlet_convolution_table_extensional`, and
  `dirichlet_convolution_table_exists_extensionally_unique`.
  The last theorem depends exactly on `dirichlet_convolution_table_exists`
  and `dirichlet_convolution_table_extensional`; the latter uses
  `dirichlet_convolution_sum_functional`.
  `DirichletSum(F,G,n,z)` explicitly excludes `n=0`, constructs an inclusive
  summand prefix through `n`, and folds `S n` entries. Its masked zeroth
  entry is zero, independently of both input zeroth values.
- `dirichlet_triangular_candidate.py`:
  `dirichlet_convolution_at_one_iff(F,G,a,b,z)` proves
  `ArithAt(F,1,a) -> ArithAt(G,1,b) ->
  (DirichletSum(F,G,1,z) <-> SignedMul(a,b,z))`.
  This and the signed one law establish output normalization.
- `generalized_crt_compatibility_candidate.py`:
  `crt_coprime_divisor_pair(a,b,d,e)` derives `Coprime(d,e)` from
  `Coprime(a,b)`, actual `d|a`, and actual `e|b`; its sole direct dependency
  is `multiple_trans`.
  `crt_is_gcd_coprime_product(a,b,n,ga,gb,P,T)` proves
  `IsGCD(P,T,n)` from `n!=0`, `T=a*b`, `P=ga*gb`, `Coprime(a,b)`,
  `IsGCD(ga,a,n)`, and `IsGCD(gb,b,n)`.
  The existing `canonical_gcd_exists`, `is_gcd_of_dvd`, and `is_gcd_unique`
  are the proposed route to the actual divisor decomposition, not an
  assumed factorization or valuation oracle.

## Missing constructive bridges and proposed module partition

The following five modules are a proposed division of future work, not files
created or proof factories enrolled by this note.

1. `coprime_divisor_decomposition_candidate.py`: for positive coprime `m,n`
   and positive `d|m*n`, construct the unique pair `a|m`, `b|n`, `d=a*b`.
   Taking actual gcds with `d` and using the existing coprime-product gcd
   theorem avoids an unnecessary prime-factorization construction. Construct
   positive cofactors `m=a*u`, `n=b*v`; prove their coprimality, the quotient
   identity `(m*n)/d=u*v`, and all required bounds.
2. `signed_block_sum_candidate.py`: prove actual affine-slice concatenation,
   an arbitrary-position single-spike value, and the missing equality between
   a row-major flattened prefix sum and its rectangular row sum.
3. `signed_support_reindex_candidate.py`: use an actual beta-coded map
   between two possibly unequal finite windows. Require value-preserving
   bounded images for nonzero source entries, injectivity on those entries,
   and a witnessed preimage for every nonzero target entry. The definition
   states only this finite relation, never equality of sums. Construct an
   actual incidence table and use single-spike/zero rows and columns plus
   Fubini to prove equality of the sums.
4. `signed_cartesian_product_candidate.py`: construct an actual outer-product
   table and prove that its rectangular/flattened sum is the actual signed
   product of the two input sums, using scalar linearity twice.
5. `dirichlet_multiplicative_candidate.py`: define the exact finite property,
   construct the actual pair-product beta map, prove entry factorization and
   the support-reindex hypotheses, then derive scalar closure, table closure,
   and actual existence with positive-value uniqueness.

For input bounds `m,n`, the source Cartesian window has length
`(S m)*(S n)`, while the target convolution summand window has length
`S(m*n)`. The map `(a,b) -> a*b` is not a permutation of all these indices:
lengths differ and zero/nondivisor indices collide. Only active positive
divisor pairs are bijective. A nonzero-value support argument or a proved
completion by inactive indices is therefore essential. The existing
whole-prefix permutation theorem cannot be applied by relabeling this map.

## Regression and counterexample matrix

These are proposed tests. Small numerical examples were checked directly as
diagnostics; they are not HA evidence or substitutes for actual beta witnesses.

- **Normalization versus units:** `f=-delta` has a convolution inverse
  (itself) but is not multiplicative, already at `1*1`. If a mistaken property
  uses `f(1)=+1 or -1` and checks only coprime inputs greater than one, then
  `f=-delta` and `g=1` satisfy it, but `f*g=-1` fails at `2*3`:
  `h(6)=-1` while `h(2)*h(3)=1`. If the full law includes `1*1`, a unit plus
  that law already rules out negative one; do not claim the same
  counterexample refutes that stronger conjunction.
- **Coprimality is necessary:** `1*1=tau` has `tau(4)=3`, whereas
  `tau(2)*tau(2)=4`. The result is multiplicative, not completely
  multiplicative.
- **Both input properties are necessary:** on `1..6`, take
  `f=[1,0,0,0,0,1]` and `g=delta`. Then `f*g=f`, which fails at `2*3`.
- **Genuine signed data:** take `f=[1,2,-3,5,7,-6]` and `g=1` on `1..6`.
  Both are multiplicative on this prefix. Their convolution is
  `[1,3,-2,8,8,-6]`, so the boundary pair `2*3=6` gives `3*(-2)=-6`.
  The latter values have canonical codes `6,3,11`; natural multiplication of
  encoded values is not `SignedMul`.
- **Product bound:** at `N=3`, two valid tables can agree with
  `f(1)=1,f(2)=2,f(3)=3` but have different values at `6`. Both must satisfy
  the same finite-prefix multiplicativity property. Requiring the law at
  `2*3` solely because `2,3<=N` would incorrectly inspect outside data.
- **Endpoint:** at `N=6`, the pair `2*3=6` is included. A strict product
  bound `a*b<N` would miss a required last-entry case.
- **Empty and singleton prefixes:** the strict proposed predicate rejects
  `N=0`; existing zero-window inverse/convolution results still apply to
  actual tables. At `N=1`, positive values must be signed one, but input and
  output values at zero may all differ.
- **Representation:** use independently beta-coded tables with the same
  positive canonical values but different codes, zeroth values, and
  compensating positive/negative streams. All conclusions must be invariant
  under positive-value equality, not demand equality of those representations.
- **Proof gates:** independently expand the selected relation and endpoint
  ASTs; exercise capture/arity/compound-term failures, actual original-HA
  bodies, false targets, and every dropped/poisoned declared dependency.
  Check statement novelty against the complete then-current parent inventory.
  A syntactically removed premise is not automatically a semantic
  counterexample when another premise already entails it.

Full dependency-closed HA verification, independent compiled-Lean checking,
ordinary principal certificates, definition-DAG tests, and reader checks must
precede any G009 completion or admission claim. No kernel, resource limit,
historical artifact, or existing source is changed by this design.

## Implementation-status addendum — 2026-08-30

The preceding sections preserve the historical design and source-inventory
audit dated 2026-08-29. Their statements about proposed or missing bridges
describe that audit, not the implementation status recorded below.

### Implemented source and evidence boundary

There are now 90 new theorem rows in nine production mathematical modules:

- `arithmetic_multiplicative_candidate.py`
- `coprime_divisor_decomposition_candidate.py`
- `divisor_pair_index_candidate.py`
- `signed_block_sum_candidate.py`
- `signed_cartesian_product_candidate.py`
- `signed_support_reindex_candidate.py`
- `dirichlet_multiplicative_entry_candidate.py`
- `dirichlet_multiplicative_support_candidate.py`
- `dirichlet_multiplicative_candidate.py`

These files reside in `peano-lab/py/peano_lab/library/`. Their actual
dependency-closed bundle has now passed the complete fresh production gate:
exact-AST novelty, whole-bundle original HA and same-byte compiled Lean,
and all six ordinary empty-context principal certificates. All 277 mandatory
reader tests passed. The independent standalone test path also passed its
own eight fresh proof jobs, 277 inner reader tests and 277 outer reader tests.
The original proof, CPU, wall-time and memory limits were unchanged.

The corrected publisher installed 255 canonical local reader files in
731.530 seconds; worker peak RSS was 1,461,321,728 bytes and render peak
594,690,048 bytes. The definition-namespace and standalone-fixture defects
and their regression evidence are recorded in PLAN/20. The original G009
finite-coded-prefix contract is therefore proved, with the exact scope
below. Remote delivery remains a separate subsequent step. The new 90 rows
have **not** been admitted to Alpha or Stable: Alpha stays 3,796 and Stable
432. The existing v31 algebra and inverse results retain their separate,
prior admission and verification provenance.

### Original G009 obligations mapped to exact roots

A source-only review of all nine new modules, their actual graph contracts,
and the existing v31 roots found no mathematical contract gap against the
**nonempty finite-coded prefix alternative** explicitly allowed by PLAN/14.
The mapping is:

| Original obligation | Exact theorem root(s) | Source and precise guarantee |
|---|---|---|
| Multiplicative convolution closure | `dirichlet_convolution_multiplicative_values`; `dirichlet_convolution_multiplicative_table`; `dirichlet_convolution_multiplicative_exists_unique` | [New closure module](../peano-lab/py/peano_lab/library/dirichlet_multiplicative_candidate.py): the scalar law, preservation of normalized multiplicativity by an actual convolution table, and construction of such a table with uniqueness of represented positive values. |
| Associativity | `dirichlet_convolution_associative_tables_exists` | [Existing associativity module](../peano-lab/py/peano_lab/library/dirichlet_associativity_candidate.py): construct all four intermediate/output tables for both parenthesizations and prove equality on `0<n<=N`. |
| Identity | `dirichlet_delta_unit_exists` | [Existing units module](../peano-lab/py/peano_lab/library/dirichlet_units_candidate.py): construct an actual delta table and prove both convolution unit laws, with any prescribed unrelated zeroth value of the delta table. |
| Exact signed inverse criterion | `dirichlet_inverse_positive_criterion` | [Existing inverse module](../peano-lab/py/peano_lab/library/dirichlet_inverse_candidate.py): for an actual table and `N!=0`, an actual two-sided inverse exists exactly when the value at one is signed `+1` or `-1`. |

The new bridge definitions contain actual table, entry, divisor-pair and
native-beta-map data, not the conclusions they are used to prove. In
particular, `signed_prefix_sum_row_major_iff` supplies the missing flattened
prefix/rectangular-sum equivalence; `signed_cartesian_product_prefix_sum`
proves the product-of-sums law; and `signed_support_reindex_sum_equal` proves
sum equality using a constructed incidence table. The product map is proved
bijective on nonzero support, not asserted to permute the unequal full
windows. Actual table and sum witnesses are constructed throughout.

### Conservative definition identities now present

The current [G009 definition registry](../scripts/constructive_g009_definitions.py)
preserves all 372 inherited identities and adds exactly these eleven:

| Stable ID | Definition name |
|---|---|
| ND0316 | `MultiplicativePrefix` |
| ND0317 | `DivisorFactorPair` |
| ND0318 | `DivisorPairIndexMap` |
| ND0319 | `SignedCartesianProduct` |
| ND0320 | `SignedSupportReindex` |
| ND0321 | `SignedIncidenceEntry` |
| ND0322 | `SignedIncidenceFlatEntry` |
| ND0323 | `SignedIncidenceFlatPrefix` |
| ND0324 | `SignedSupportIncidence` |
| ND0325 | `DirichletCoprimeProductData` |
| ND0326 | `DirichletDivisorGridWitness` |

The unchanged relevant inherited identities are `DirichletTable` (ND0304),
`KroneckerDeltaTable` (ND0311), `SignedUnit` (ND0313),
`DirichletUnitAtOne` (ND0314), and `DirichletInverse` (ND0315).
ND0316 expands through `ArithTable`, `ArithAt`, `Le`, `Coprime`, and
`SignedMul`; it has no `SignedUnit` definition edge. Definition identities
and expansion arrows are notation evidence, not theorem or admission evidence.

### Required scope of any later completion statement

- The domain is an actual nonempty finite positive prefix `0<n<=N`, with
  `N>0`. No arbitrary second-order function or unproved infinite-function
  coding theorem is asserted.
- Multiplicativity uses `ArithAt(F,1,2)`: canonical code **2** is signed
  **+1**. General invertibility permits signed **+1 or -1**, codes **2 or
  1**. These are different properties.
- The product law requires positive coprime `m,n` and the inclusive bound
  `m*n<=N`. Separate factor bounds do not suffice, and complete
  multiplicativity without coprimality is not claimed.
- Uniqueness and associativity identify represented canonical signed values
  only on `0<n<=N`, never table encodings, their arbitrary zeroth values,
  or outside-prefix values. Those outside values exist but are not
  constrained by this finite-prefix property.
- At `N=0`, strict multiplicativity is false. Existing empty-window
  convolution and inverse results are separate; the general
  `dirichlet_inverse_criterion` has the condition
  `N=0 or DirichletUnitAtOne(F)`. The bare signed-unit iff requires `N!=0`.
- The new existential convolution endpoint constructs an actual table; it
  does not additionally promise an arbitrarily prescribed output zeroth
  value. The separate inverse and delta constructors do have their stated
  prescribed-zero-value arguments.
- `dirichlet_multiplicative_function_invertible` constructs an actual
  two-sided inverse from positive-one normalization. It does **not** prove
  that the inverse is multiplicative. Neither inverse multiplicativity nor
  a convolution-group theorem for multiplicative prefixes is claimed; that
  further corollary is not an obligation of the original PLAN/14 G009 text.

This mapping identifies the original mathematical contract whose fresh
production proof and reader checks are recorded above. Alpha admission and
remote publication remain distinct gates; neither follows automatically
from the proof result or this documentation update.
