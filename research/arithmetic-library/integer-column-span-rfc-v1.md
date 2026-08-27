# Integer column-span closure with actual coefficient witnesses

This is the bounded column-span foundation of T13: zero membership, addition,
and negation for arbitrary finite integer generating matrices. It proves
actual signed matrix-vector calculations and constructs the finite coefficient
vectors witnessing the operations. It does not identify an arbitrary
generating family with an independent basis.

The additive implementation is
`peano-lab/py/peano_lab/library/integer_column_span_candidate.py`, with factory
`make_integer_column_span_candidate_theorems`. All 33 new theorem bodies use
only preceding rows and the immutable Alpha-v26 parent of 2,138 checked
theorems. Historical matrix, beta, finite-sum, and definition sources are not
modified. Neither the kernel nor its original checker is changed.

## Exact representation and definitions

An integer is represented by two naturals `(p,n)`, denoting `p-n`. Components
are not required to be canonical. The pairs `(5,2)` and `(10,7)` represent
the same integer. Thus equality must mean `p+m=q+n`, not component equality.

A signed vector is represented by four natural codes `(pb,pc,nb,nc)`. At
coordinate `i`, its positive component is decoded by `Beta(pb,pc,i,p)` and
its negative component by `Beta(nb,nc,i,n)`. The existing beta relation is
total and functional, but encodings need not be unique. Every relation below
quantifies over all actual decoded values at `i<l`.

```
IntegerVectorEqual(X,Y,l):
  at each coordinate with X=(a,b), Y=(c,d), a+d=c+b.

IntegerVectorZero(X,l):
  at each coordinate with X=(a,b), a=b.

IntegerVectorAdd(X,Y,Z,l):
  at each coordinate with X=(a,b), Y=(c,d), Z=(e,f),
  e+(b+d)=(a+c)+f.

IntegerVectorNegate(X,Y,l) := IntegerVectorEqual(swap(X),Y,l).
```

Here `swap` means exchanging the two code/scale pairs. It is notation for
the reordered arguments, not a new term former. Negation permits *any*
integer-equal encoding of the swapped vector.

The generating matrix has `r` rows and `w` columns. Four beta codes encode
its positive and negative components in the unchanged row-major convention:
cell `(i,j)` has index `i*w+j`. A coefficient vector has four codes and `w`
entries. Its product is the frozen `SignedMatrixProduct` specialized to
output width one:

```
RawProduct(A,C,w,r,P) := SignedMatrixProduct(A,C,w,1,r,P).

IntegerMatrixVectorProduct(A,C,w,r,X) :=
  exists P. RawProduct(A,C,w,r,P) /\ IntegerVectorEqual(P,X,r).

IntegerColumnSpan(A,w,r,X) :=
  exists C. IntegerMatrixVectorProduct(A,C,w,r,X).
```

Each displayed `exists P` or `exists C` is literally four natural witnesses,
not a higher-order quantifier. `RawProduct` is notation for the unchanged
full signed-product expansion. It includes four actual finite natural
matrix products and two actual pointwise output-sum codes. No matrix-vector
solver, uncoded sum, supplied basis, or external certificate is assumed.

The quotient-level output equality is important. Membership does not depend
on the positive/negative components chosen for the *output*. A later
canonicalization, or even a noncanonical recoding with a larger common
positive and negative component, does not destroy a valid coefficient witness.

## Main proved statements

All dimensions are arbitrary naturals. None of these statements assumes a
nonempty matrix, a positive column count, square shape, nonzero determinant,
linear independence, or a supplied solution algorithm.

```
integer_column_span_contains_zero:
  forall A w r. IntegerColumnSpan(A,w,r,(0,0,0,0)).

integer_column_span_zero:
  IntegerVectorZero(X,r) -> IntegerColumnSpan(A,w,r,X).

integer_column_span_transport:
  IntegerColumnSpan(A,w,r,X) -> IntegerVectorEqual(X,Y,r) ->
  IntegerColumnSpan(A,w,r,Y).

integer_column_span_add_closed:
  IntegerColumnSpan(A,w,r,X) -> IntegerColumnSpan(A,w,r,Y) ->
  IntegerVectorAdd(X,Y,Z,r) -> IntegerColumnSpan(A,w,r,Z).

integer_column_span_negate_closed:
  IntegerColumnSpan(A,w,r,X) -> IntegerVectorNegate(X,Y,r) ->
  IntegerColumnSpan(A,w,r,Y).
```

Separate existence endpoints construct the coded result as well:

```
integer_column_span_add_exists:
  IntegerColumnSpan(A,w,r,X) -> IntegerColumnSpan(A,w,r,Y) ->
  exists Z. IntegerVectorAdd(X,Y,Z,r) /\ IntegerColumnSpan(A,w,r,Z).

integer_column_span_negate_exists:
  IntegerColumnSpan(A,w,r,X) ->
  exists Y. IntegerVectorNegate(X,Y,r) /\ IntegerColumnSpan(A,w,r,Y).
```

The strengthened coefficient constructor exposes the actual witness update,
rather than merely concluding membership:

```
integer_matrix_vector_add_constructive:
  IntegerMatrixVectorProduct(A,C1,w,r,X) ->
  IntegerMatrixVectorProduct(A,C2,w,r,Y) -> IntegerVectorAdd(X,Y,Z,r) ->
  exists C3.
    PointwiseAdd(C1+,C2+,C3+,w) /\
    PointwiseAdd(C1-,C2-,C3-,w) /\
    IntegerMatrixVectorProduct(A,C3,w,r,Z).
```

The same `C3` whose streams are constructed sums is the coefficient vector
used by the product witnessing `Z`. For negation, the actual witness is the
swapped coefficient code. For zero, all four coefficient codes are literally
zero; the theorem permits any output representation of the zero vector.

## Proof construction

The proof begins below the level of matrix abbreviations.

1. For three actual natural dot products, a pointwise distributive equation
   between their decoded multiplicands implies addition of their results.
   The proof extracts the actual product streams and applies the already
   proved arbitrary-length finite-sum additivity theorem.
2. Each old matrix-product cell contains actual affine codes for its row and
   column. The new cell-linearity proof aligns all three row slices with the
   same decoded source entry. For width one, the coefficient column index
   is explicitly normalized from `0+1*i` to `i`. Natural multiplication
   distributivity supplies the required pointwise equation.
3. The one-column product entry theorem proves that the row-major coordinate
   is the actual output row: a column below one is zero, and the old index
   equation then fixes the row. Beta functionality identifies its output
   value. This prevents an unrelated multiplication cell from certifying
   an output vector entry.
4. Natural matrix-vector products therefore distribute over constructed
   coefficient sums. Applying this to all four constituent natural products,
   and checking pointwise addition regrouping, proves actual signed-product
   component additivity.
5. Balanced pair equality is proved transitive by ordinary additive
   cancellation. Vector equality and addition are lifted through actual beta
   entries, so the product result may be replaced by any integer-equal
   output representation.
6. Actual coefficient sums are constructed using the frozen finite pointwise
   addition constructor. A complete signed product of those coefficients is
   constructed with the frozen product-existence theorem. The preceding
   linearity and integer equality lemmas show it represents the given sum.
   Its very same coefficient codes witness column-span membership.

For zero, two actual natural products with the same positive and negative
coefficient stream are reused on both sides of the signed product. Their
constructed sum is therefore a common output stream, representing integer
zero. For negation, the four natural products are reordered exactly by
swapping coefficient components; the output components swap with them.

```
actual beta entries + checked finite-sum additivity
                         |
              natural dot-product linearity
                         |
    actual row/column slices + actual product-entry alignment
                         |
            natural matrix-vector linearity
                         |
      four signed-product constituents + sum regrouping
                         |
      signed product add/neg/zero + integer-pair equality
                         |
       actual constructed coefficient vectors and images
                         |
      column-span zero/add/neg closure and result existence
```

## Conservative definition DAG

Six new public definition builders are provided. Their arguments and tags
are validated. They reject duplicate argument names, formula injection,
and every generated binder prefix used by their nested frozen definitions.
Changing binder tags preserves the native arithmetic AST. Definition edges
below are abbreviation edges; they are not proof-dependency claims.

| Relation | Arguments | Direct abbreviation dependencies |
|---|---|---|
| `IntegerVectorEqual` | `(X4,Y4,l)` | `Beta`, `Lt` |
| `IntegerVectorZero` | `(X4,l)` | `Beta`, `Lt` |
| `IntegerVectorAdd` | `(X4,Y4,Z4,l)` | `Beta`, `Lt` |
| `IntegerVectorNegate` | `(X4,Y4,l)` | `IntegerVectorEqual` |
| `IntegerMatrixVectorProduct` | `(A4,C4,w,r,X4)` | unchanged `SignedMatrixProduct`, `IntegerVectorEqual` |
| `IntegerColumnSpan` | `(A4,w,r,X4)` | `IntegerMatrixVectorProduct` |

The implementation names are the corresponding snake-case builders, each
with keyword `tag`. Every `X4`, `A4`, or `C4` denotes four positional natural
arguments. Stable IDs, the mixed theorem/definition graph, and publication
authority are assigned by release integration, not by this authoring module.

## Inventory and verification boundary

The 33 ordered theorem names are pinned in
`peano-lab/py/tests/test_integer_column_span_candidate.py`. Their ordered-name
SHA-256 is
`49f25c6350493038f10c863b3cf549f0bfa29b2a248f9806bc78daa2985ea715`.
There are 66 declared dependency edges, 2,220 tactic commands, and 3,414
original-kernel body proof nodes. Maximum body size is 302 nodes and maximum
depth is 90. The largest fully expanded statement is 202,908 bytes because
it contains several complete old coded-product expansions. The conservative
definitions above expose its intended mathematical structure; no opaque
shortcut replaces those expansions.

Important exact statement hashes:

| Theorem | SHA-256 |
|---|---|
| `integer_span_signed_product_add_right` | `b791214474e0471436f7e3c93c45ecd338d4d1034646463b1e39aa87f47143d9` |
| `integer_matrix_vector_add_constructive` | `eccbefbe383084f67b9846ac5719cd08f7e008ed1654d36dce91cac03da06aff` |
| `integer_column_span_transport` | `5078153e18a76dc36591d5fc048f0d9c968758cb4c1040ef353255ce551147dd` |
| `integer_column_span_contains_zero` | `1df52e34af59b05182acebe099349fc54eb8b6ca59ac55dccdc096bc8aaf0d01` |
| `integer_column_span_add_closed` | `ae7784648a8b9f249d0b14e83e6a0fd818a48ab39603ba9336736b6c907248d4` |
| `integer_column_span_negate_closed` | `6e851a3b673718d8af101b7f38fe625a3de92e63d11df94cc2f27758532ef002` |
| `integer_column_span_add_exists` | `4c3ef723161578a73747c914a683d2b50ad3a80d087ee222b56a14ef4a1e296a` |

Validation authenticates the exact Alpha-v26 catalogue against SHA-256
`969c261f924060552dda393427b4fbc51515b9d4e69daa17f5e9f1691b5ab534`
and reconstructs the immutable parent theorem formulas and scripts directly.
Avoiding full edition imports reduces authoring memory; it does not alter
the logical judgment. Each new theorem body is independently checked in a
one-row microbatch with its declared dependencies as ordinary hypotheses.

```
PYTHONPATH=peano-lab/py python3 -m pytest -q \
  peano-lab/py/tests/test_integer_column_span_candidate.py
```

Tests cover original-kernel replay, false-conclusion and truncated-body
mutations, dependency removal, exact endpoint ASTs and witness topology,
all six definitions' hygiene, signed equality rather than component
equality, and actual coefficient examples with rectangular, dependent,
zero-row, and zero-column matrices. Finite examples are regressions, not
proof evidence. Result: **250 tests pass** in the complete regression run.

This foundation does **not** prove that arbitrary generators form a basis,
construct an independent basis, establish a determinant/covolume/index
theorem, or implement Hermite, Smith, or LLL normal form. Those are separate
T13 goals. It also does not claim a separately checked theorem transporting
rank or determinant across different signed pair representations. The proved
output quotient invariance is explicitly scoped to these span operations.

Dependency-closed bundle checking and independent Lean verification remain
mandatory release gates. Original-kernel body receipts alone are not Alpha
admission, Lean verification, or deployment, and this family changes no
release or remote publication state.
