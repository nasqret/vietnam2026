# Three advanced constructive proof campaigns

Immutable **Alpha v21** preserves every one of the **1,776 independently
checked Alpha-v20 theorems** and appends exactly **54 new independently
checked constructive theorems**. Its complete ledger contains **1,830
checked-use entries**, **5,986 checked theorem dependencies**, and **53
dependency-first layers**: **432 unchanged Stable theorems** and **1,398
Alpha-only theorems**, with no body-only, pending, or unchecked entry.

This chapter preserves that exact historical checkpoint. Historical immutable
**Alpha v22** retains all 1,830 v21 rows and independently adds 60 checked
binary-length, Euclidean-gcd-transport, and supplied-digit binary-execution
theorems, for **1,890 checked-use entries**; its distinct proof and genuinely
closed intermediate gaps are documented in
{doc}`Binary and Euclidean transport <transport-layer-campaign>`. Current
immutable **Alpha v23** retains that entire 1,890-theorem ledger and adds
**59 independently checked proofs**: 17 completing G101's logarithmic
Euclidean bound, 24 completing G102's canonical digit extraction and exact
binary execution bound, and 18 proving G025's infinitude of primes three
modulo four. All **1,949 historical v23 entries** have checked-use authority.

| Campaign | New checked theorems | Genuine mathematical progress | Definition-aware proof explorer |
|---|---:|---|---|
| Arbitrary finite matrix products | 23 | Full natural and signed beta-coded matrix multiplication, signed dot products, and true signed two-/three-dimensional determinants | [Matrix-coded products](../_static/constructive-advanced-layer-explorer/matrix-coded-products/explorer/defined/index.html) |
| Euclidean execution and complexity | 15 | Complete beta-coded division history, independent relational gcd, a linear step bound, and genuine two-step halving | [Euclidean complexity](../_static/constructive-advanced-layer-explorer/euclidean-complexity/explorer/defined/index.html) |
| Binary modular exponentiation | 16 | Parity decomposition, doubled/odd powers, canonical modular square-and-multiply transitions, and unique bounded modular powers | [Binary modular exponentiation](../_static/constructive-advanced-layer-explorer/binary-modular-exponentiation/explorer/defined/index.html) |

All values, histories, matrices, signed integers, and certificates are still
natural numbers in the original first-order language `0, S, +, *, =`.
Conservative displayed relations expand hygienically before the unchanged
intuitionistic kernel checks a proof. Neither an executable example nor a
display definition is additional proof authority.

## T13: arbitrary natural and signed matrix multiplication

The earlier v20 campaign established ten finite matrix-cell, dot-product, and
natural-entry signed-determinant components. The v21 campaign adds **23 real
checked theorems**, bringing T13 to **33 independently available components**.
It now proves complete coded multiplication of *arbitrary finite natural
matrices*, including all empty-width and empty-result boundaries:

$$
\forall L,R,w,v,r.\;\exists P.\;
  \operatorname{MatrixProductPrefix}(L,R,w,v,r,P).
$$

This is a conservative presentation of the exact checked root
[`beta_matrix_product_exists` (`MC000B`)](../_static/constructive-advanced-layer-explorer/matrix-coded-products/explorer/defined/tag/MC000B.html).
Each matrix is a beta code and each result entry is a witnessed row/column
dot product. No primitive matrix or list sort has been introduced.

The signed root
[`beta_signed_matrix_product_exists` (`MC000E`)](../_static/constructive-advanced-layer-explorer/matrix-coded-products/explorer/defined/tag/MC000E.html)
extends this to arbitrary finite matrices of signed natural pairs. Its
construction forms the four genuine products `++`, `--`, `+-`, and `-+`,
combining them into the positive and negative result matrices. The family
also proves a functional signed dot product and *genuinely signed*
two-by-two and three-by-three cofactor-expansion determinant pairs; the latter
is
[`signed_matrix_three_full_determinant_exists` (`MC0016`)](../_static/constructive-advanced-layer-explorer/matrix-coded-products/explorer/defined/tag/MC0016.html).

```{admonition} Historical v21 boundary: T13 remains open
:class: important
Arbitrary-dimensional signed matrix multiplication is proved. An
arbitrary-dimensional determinant, matrix rank, integer-lattice bases, and
lattice operations were **not** proved in v21. At that checkpoint the T13
matrix-and-lattice milestone remained **open**, despite its 33 checked
components; its checked multiplication theorem must not be mislabeled as a
proof of the stronger milestone.
```

## G101: actual Euclidean histories, independent gcd, and two-step halving

Fifteen checked theorems refine the already proved finite
continued-fraction execution. The exact endpoint
[`euclidean_gcd_execution_linear_bound` (`EC000F`)](../_static/constructive-advanced-layer-explorer/euclidean-complexity/explorer/defined/tag/EC000F.html)
constructs, for every `a,b`, a real beta-coded Euclidean division history, a
separately certified relational gcd `g`, and a witnessed **linear** bound
`steps <= b`. The zero-divisor boundary is proved separately.

The independent arithmetic lemma
[`euclidean_two_step_halving` (`EC0006`)](../_static/constructive-advanced-layer-explorer/euclidean-complexity/explorer/defined/tag/EC0006.html)
proves the exact constructive implication

$$
  a=bq+r,\quad r<b,\quad b=rQ+t,\quad t<r
  \quad\Longrightarrow\quad 2t<b.
$$

At the historical v21 checkpoint the history's terminal state had not yet been
identified with its independently constructed relational gcd, and there was
no object-level `BitLen` theorem or checked logarithmic step bound. Subsequent
Alpha v22 genuinely proves terminal-state identification and total, functional,
unique `BitLen`. Subsequent Alpha v23 additionally derives the exact
`steps <= 2 * BitLen(b) + 1` bound by a genuine unchanged-kernel first-order
proof. Therefore **G101 is completely closed**; the bound is formal proof,
not a host-language complexity observation.

## G102: canonical square-and-multiply prerequisites

The sixteen checked results first construct the exact binary decomposition

$$
  \forall e.\;\exists h,d.\;
    (d=0\lor d=1)\land e=2h+d,
$$

then prove both doubled/odd exponent identities, canonical bounded residues,
and existence/functionality of each guarded square-and-multiply transition.
The modulus guard is exactly `m > 1`; no assertion is made for modulus zero.
The final independently checked theorem is

$$
  \forall a,e,m.\;m>1\;\Longrightarrow\;
    \exists!r.\;r<m\land r\equiv a^e\pmod m,
$$

under its actual first-order relational-power definition. Its permanent root
is
[`binary_modular_exponentiation_result_exists_unique` (`BX0010`)](../_static/constructive-advanced-layer-explorer/binary-modular-exponentiation/explorer/defined/tag/BX0010.html).

A separately resource-capped executable constructs and validates genuine
most-significant-bit square-and-multiply histories, including concrete small
beta-coded witnesses; those executable histories satisfy
`steps <= 3 * BitLen(e) + 2`. This is verified *host computation*, not an
object-level Heyting-arithmetic derivation. At this historical v21 checkpoint
there was no checked complete binary execution trace or object-level `BitLen`.
Subsequent Alpha v22 proves both unique `BitLen` and a complete, power-correct
execution for every **supplied valid digit prefix**. Alpha v23 then constructs
canonical digits for **every arbitrary exponent**, proves their actual
square-and-multiply execution, and formally establishes
`operations <= 3 * BitLen(e) + 2`. Consequently **G102 is completely closed**.

## One hygienic global/local definition DAG

The historical v21 research graph had **132 blueprint vocabulary entries**, **71
blueprint definition dependencies**, **311 actual lexical statement uses**,
**31 separately declared typed notation links**, and **342 total
milestone-to-notation edges**. All notation is sorted into **five
dependency-first layers**.

The corresponding historical shared conservative registry contained **79 independently
expansion-audited definitions** and **123 reviewed definition prerequisite
edges**. Exactly **40 signature-compatible blueprint definitions** are bound
to these objects: **36 exact-name matches** and **four explicitly reviewed
aliases**. The two known incompatible same-name signatures remain visible and
rejected. In particular, parameter order, free variables, alpha-renaming,
substitution hygiene, parsed expansion equality, and acyclicity are checked;
a displayed name cannot smuggle in a new axiom.

The sixteen genuinely new globally shared identities are:

| Identity | Conservative definition | Genuine direct prerequisites |
|---|---|---|
| `ND0012` | `MatrixAffineSlice` | `Beta`, `Lt` |
| `ND0013` | `MatrixProductCell` | `MatrixAffineSlice`, `DotProduct` |
| `ND0014` | `MatrixProductPrefix` | `MatrixProductCell`, `Beta`, `Lt` |
| `ND0015` | `MatrixPointwiseAdd` | `Beta`, `Lt` |
| `ND0016` | `SignedDotProduct` | `DotProduct` |
| `ND0017` | `SignedMatrixProduct` | `MatrixProductPrefix`, `MatrixPointwiseAdd` |
| `ND0018` | `EuclideanDivision` | `Lt` |
| `ND0019` | `EuclideanHalving` | `Lt` |
| `ND0020` | `EuclideanExecution` | `ContinuedFractionTrace`, `IsGCD` |
| `ND0021` | `BinaryModulus` | `Lt` |
| `ND0022` | `BinaryExponentSplit` | none |
| `ND0023` | `CanonicalModularResidue` | `Lt`, `ModEq` |
| `ND0024` | `BinaryDoubledPower` | `Pow` |
| `ND0025` | `BinaryOddPower` | `Pow` |
| `ND0026` | `BinaryModularStep` | `CanonicalModularResidue` |
| `ND0027` | `BinaryModularPower` | `Pow`, `CanonicalModularResidue` |

The preceding `ND0001`–`ND0011` identities and all historical proof surfaces
remain unchanged. The large
[definition DAG](../_static/constructive-grand-campaign/definitions.json)
and each family-local proof graph use the same immutable reviewed definition
objects, not merely coincidentally identical display strings.

The historical v22 registry preserved every one of these identities and
extended it to **141 blueprint terms**, **89 reviewed conservative
definitions**, **142 reviewed definition edges**, and **50 compatible
blueprint matches**. Historical v23 further extended the same graph to **152
blueprint terms**, **97 reviewed conservative definitions**, **159 reviewed
definition edges**, and **61 compatible blueprint matches**: 57 exact names
and four preserved explicit aliases.

## Independent original-kernel and Lean evidence

The complete v21 proof artifact contains **208 exact theorem nodes**: **154
actual historical prerequisites** and **all 54 newly admitted results**.
Its one balanced synthetic conjunction combines **27 maximal roots** without
inventing another library theorem. Thus there are **209 independently checked
proof bodies**, **491 proof-dependency edges**, and **10,304 structural
body-proof nodes**.

Every original dependency-curried theorem body is accepted independently by
the unchanged constructive kernel. The separately compiled Lean verifier
also accepts the same complete artifact; both release-level Lean-evidence
flags are earned by actually invoking that verifier during release generation.

```text
Bundle: research/arithmetic-library/artifacts/alpha-v21-advanced-layer-proof-bundle-v1.json
Bytes: 1,005,317
SHA-256: 65ecae7cb6b3e102790efa281451db3da5ab83868afcf9d57e6656f7a3eafda0

Historical v21 channels: artifacts/peano-library/channels-v21.json
Catalog SHA-256: 84bafa545c3c529eb4bcda9d9b501af8577a8e414f5cabf58a4c2a88da5129f1
Enrollment SHA-256: ad2616d7656438ee2084f5ea404df3dad2106a99c6819fd174fd8c3ed6bb4c98
Edition SHA-256: aee42cc37e4a4073eb4892e81e4f26d957b3b4b42675c1ed4e67c90dc89602e6
Evidence SHA-256: 9d217af3e7f77f8beb436f627a44f1a29cda54bb08a4e666899803aa97ccb91b
```

## Historical next layer and the remaining genuine gaps

At the historical v21 checkpoint, eight openly stated milestones had
completely checked direct prerequisites: **T13, G101, G102, G051, G095,
G027, G035, and G107**. Subsequent v22 through v27 made the following progress:

1. **Proved in v22:** formalize total, functional, uniquely witnessed
   first-order `BitLen` and the exact binary digit/power foundations.
2. **Completed in v23:** identify the genuine Euclidean terminal remainder
   with its certified relational gcd and derive the exact
   `2 * BitLen(b) + 1` logarithmic bound, closing G101.
3. **Completed in v23:** construct canonical binary digits for every exponent,
   verify the actual beta-coded square-and-multiply execution, and prove the
   exact `3 * BitLen(e) + 2` bound, closing G102.
4. **Completed in v27:** arbitrary signed determinant recurrences, actual
   rectangular rank, representation invariance, and integer-span/lattice data
   close the exact T13 substrate. Lattice-index and basis/reduction results
   remain distinct stronger targets.
5. **Completed in v27:** actual finite-set Cauchy–Davenport (G051), full
   signed-polynomial simple-root lifting (G095), explicit Chebyshev bounds
   (G027), multinomial carries (G035), and first-stop Cornacchia (G107).

Current Alpha v28 contains 2,764 checked theorems. Its stronger future goals
are not marked complete merely because these exact substrates are available.

Each new layer requires actual first-order theorem statements, hygienic
conservative definitions, adversarial boundary tests, complete
dependency-closed original-kernel proofs, independent Lean verification, and
a new immutable additive Alpha edition. Stable remains a separate promotion
decision throughout.
