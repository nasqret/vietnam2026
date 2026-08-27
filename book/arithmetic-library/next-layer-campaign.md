# Four next-layer constructive proof campaigns

Historical immutable **Alpha v20** preserves all 1,737 independently checked Alpha-v19
theorems and appends exactly **39 new independently checked theorems**. Its
complete ledger has **1,776 checked-use entries**, **5,882 actual theorem
dependencies**, and 53 dependency layers. Stable remains unchanged at 432.

Its immutable child, historical **Alpha v21**, preserves this entire snapshot
and adds 54 further checked results; see
{doc}`Three advanced constructive proof campaigns <advanced-layer-campaign>`.
Historical **Alpha v22** in turn preserves all 1,830 v21 theorems and adds 60
genuinely checked binary-length, Euclidean-gcd, and coded binary-execution
proofs; see {doc}`Binary and Euclidean transport <transport-layer-campaign>`.
Historical **Alpha v23** preserves all 1,890 historical v22 theorems and adds
59 independently checked results that completely prove logarithmic Euclidean
GCD (G101), canonical arbitrary-exponent binary modular execution (G102), and
infinitely many primes congruent to three modulo four (G025).
Statements below about the exact v20 release remain historically precise;
Historical Alpha v27 closes T13's exact determinant/rank/integer-span substrate,
and G011, G095, G035, G027, G051, and G107. Stronger determinant
multiplicativity, lattice-index, independent-basis, and reduction theorems
remain separate open goals.

The four additions are deliberately organized by genuine prerequisites:

| Campaign | New checked theorems | Exact campaign milestone | Proof explorer |
|---|---:|---|---|
| Polynomial Horner evaluation | 7 | T12 is closed for beta-coded natural coefficients | [Definition-aware polynomial map](../_static/constructive-next-layer-explorer/polynomial-horner/explorer/defined/index.html) |
| Finite matrix and dot-product foundations | 10 | T13 remains open; its ten exact components are checked | [Definition-aware matrix-component map](../_static/constructive-next-layer-explorer/matrix-dot-product/explorer/defined/index.html) |
| Bertrand prime windows and chains | 13 | Both G023 and G024 are closed | [Definition-aware Bertrand-chain map](../_static/constructive-next-layer-explorer/bertrand-prime-chains/explorer/defined/index.html) |
| Finite continued fractions | 9 | G071 is closed for every positive rational input | [Definition-aware continued-fraction map](../_static/constructive-next-layer-explorer/continued-fractions/explorer/defined/index.html) |

Every finite list, trace, signed integer, matrix cell, and certificate is
encoded by natural numbers in the original first-order language
`0, S, +, *, =`. The kernel, induction schema, constructive logic, and trusted
axiom boundary are unchanged.

## T12: genuine natural polynomial evaluation

The exact checked milestone is

$$
\forall b,c,x,\ell.\;\exists z.\;
  \operatorname{Horner}(b,c,x,\ell,z).
$$

Here `Beta(b,c,i,a)` decodes coefficient `a` at finite index `i`, while the
conservative relation `Horner(b,c,x,ell,z)` states that a witnessed finite
Horner trace evaluates the first `ell` coefficients at `x` with result `z`.
The seven original-kernel theorems prove trace existence, evaluation existence,
trace functionality, evaluation functionality, unique evaluation, the empty
case, and exact successor decomposition.

The checked root is `beta_horner_eval_exists`, permanent family-local tag
[`PH0002`](../_static/constructive-next-layer-explorer/polynomial-horner/explorer/defined/tag/PH0002.html).
No statement claims arbitrary presented rings, polynomial differentiation, or
a new polynomial sort: those are distinct future layers.

## T13: checked finite components, open full matrix milestone

`MatrixAt(b,c,w,i,j,z)` names a beta-coded matrix entry,
`DotProduct(b,c,d,e,ell,z)` names the witnessed finite dot product of two
encoded natural rows, and `SignedDet2(a,b,c,d,p,n)` names a signed
two-by-two determinant represented as a positive/negative pair.

The ten checked results establish cell existence and uniqueness, dot-product
existence and uniqueness, the empty case, commutativity, and existence and
functionality of the signed two-by-two determinant. The reusable root is
`beta_dot_product_exists_unique`, tag
[`MD0006`](../_static/constructive-next-layer-explorer/matrix-dot-product/explorer/defined/tag/MD0006.html).

```{admonition} Historical v20/v21 boundary: T13 is not closed
:class: important
At this historical v20 checkpoint, no theorem yet established arbitrary signed
matrix multiplication. Historical Alpha v21 additionally proves that exact
arbitrary signed multiplication theorem, signed dot products, and genuine
signed two-/three-by-three determinants, bringing T13 to 33 checked
components. At those historical checkpoints, determinants in arbitrary
dimension, rank, and lattice data were unproved: the milestone remained
explicitly **open**. Alpha v27 subsequently closes the exact finite
substrate with 182 new proofs; lattice-index, basis, and reduction theorems
are not included in that closure.
```

## G023 and G024: strict constructive Bertrand extensions

`BertrandWindow(n,p)` abbreviates

$$
\operatorname{Prime}(p)\land n<p\land p<2n.
$$

`PowerValuationOne(p,z)` expands to the already checked positive-input
valuation relation with exponent one. Seven new proofs close G023:

$$
\forall n>1.\;\exists p,z.\;
  \operatorname{BertrandWindow}(n,p)
  \land\operatorname{Binom}(2n,n,z)
  \land\operatorname{PowerValuationOne}(p,z).
$$

Its exact root is `central_binom_prime_divisor_multiplicity_one_exists`, tag
[`BP0007`](../_static/constructive-next-layer-explorer/bertrand-prime-chains/explorer/defined/tag/BP0007.html).

Six additional proofs use ordinary induction and beta-prefix extension to
close G024 for every finite requested chain length. `BertrandChain(b,c,n,k)`
records a chain beginning at `n` and containing `k` strict Bertrand-window
prime steps. The exact root is `iterated_bertrand_prime_chain_exists`, tag
[`BP000D`](../_static/constructive-next-layer-explorer/bertrand-prime-chains/explorer/defined/tag/BP000D.html).
Neither theorem relies on an unbounded search oracle or classical choice.

## G071: terminating finite continued fractions

For every positive numerator and denominator, nine original-kernel results
construct a genuine finite quotient list and its beta-coded reverse execution
history. Each transition records exact Euclidean division; the next positive
remainder is strictly smaller, giving constructive bounded termination.

The final theorem `continued_fraction_positive_exists`, tag
[`CF0009`](../_static/constructive-next-layer-explorer/continued-fractions/explorer/defined/tag/CF0009.html),
proves the positive-input expansion directly. Infinite continued fractions,
best-approximation theorems, Pell periods, and analytic convergence remain
separate goals.

## Conservative notation and the shared research graph

At the subsequent immutable v21 checkpoint, the research atlas audited
**132 mathematical definitions**,
**71 definition-to-definition prerequisites**, **five dependency-first
notation layers**, **311 actual lexical theorem-to-notation uses**, and
**31 explicitly declared typed references**. The 342 notation-use arrows are
never confused with genuine proof prerequisites.

The corresponding v21 shared definition registry audited **79 conservative
first-order definitions** with **123 exact reviewed prerequisite edges**.
Exactly **40 signature-compatible blueprint definitions** are aligned with
those immutable, hygienically expanded objects: 36 exact names and four
explicitly reviewed aliases. Parameter order is checked explicitly, including
`Gcd(a,b,g)` versus `IsGCD(g,a,b)`. The three-argument campaign relations
`Sum(s,ell,z)` and `Prod(s,ell,z)` are deliberately not equated with existing
four-argument beta-coded summation and product definitions. Signature
mismatches, duplicate variables, unknown dependencies, and definition cycles
fail closed.

All eleven historical Alpha-v20 display definitions are the exact same `DefinitionSpec`
objects in both the grand-campaign registry and their theorem-family proof
maps. Their permanent identity, genuine direct prerequisite names, and
canonical public proof family are:

| Definition | Identity | Direct reviewed prerequisites | Canonical proof family |
|---|---|---|---|
| `Beta(b,c,i,x)` | `ND0001` | none; AST-identical to existing `BetaAt` (`PD0013`) | polynomial Horner |
| `Horner(b,c,x,ell,z)` | `ND0002` | `Beta`, `Lt` | polynomial Horner |
| `MatrixAt(b,c,w,i,j,z)` | `ND0003` | `Beta` | finite matrix components |
| `DotProduct(b,c,d,e,ell,z)` | `ND0004` | `Beta`, `Lt`, four-argument checked `Sum` | finite matrix components |
| `SignedDet2(a,b,c,d,p,n)` | `ND0005` | none | finite matrix components |
| `BertrandWindow(n,p)` | `ND0006` | `Prime`, `Lt` | Bertrand prime chains |
| `PowerValuationOne(p,n)` | `ND0007` | `PowerValuation` | Bertrand prime chains |
| `BertrandChain(b,c,n,k)` | `ND0008` | `Beta`, `Lt`, `BertrandWindow` | Bertrand prime chains |
| `ListCell(s,q,t)` | `ND0009` | none | continued fractions |
| `ContinuedFractionTrace(a,b,s,u,v,ell)` | `ND0010` | `Beta`, `Lt`, `ListCell` | continued fractions |
| `ContinuedFraction(a,b,s)` | `ND0011` | `ContinuedFractionTrace` | continued fractions |

The atlas retains its existing `Beta`→`BetaAt` (`PD0013`) cross-campaign alias;
the additional `ND0001` identity is accepted only because its expanded formula
and ordered parameters are exactly identical. The other eight names that
also occur in the campaign blueprint now link directly to their actual `ND`
definition pages. `ListCell` and `ContinuedFractionTrace` are genuinely checked
internal notation without an invented blueprint match.

Historical Alpha v21 further introduced the sixteen conservatively checked
`ND0012`–`ND0027` matrix-product, Euclidean-execution, and binary-modular
definitions; the original eleven identities and their first-enrollment
provenance remain unchanged. Historical Alpha v22 additionally introduces
`ND0028`–`ND0037`; historical Alpha v23 added `ND0038`–`ND0045`, bringing the
genuine shared registry to **97 conservative definitions**, **159 reviewed
prerequisite edges**, and **61 signature-compatible blueprint matches**
across **152 campaign terms**.

Explore the shared
[complete definition DAG](../_static/constructive-grand-campaign/definitions.json)
or move directly between
<a href="../_static/constructive-grand-campaign/index.html?view=goal&amp;focus=T12">T12</a>,
<a href="../_static/constructive-grand-campaign/index.html?view=goal&amp;focus=T13">T13: closed finite substrate</a>,
<a href="../_static/constructive-grand-campaign/index.html?view=goal&amp;focus=G023">G023</a>,
<a href="../_static/constructive-grand-campaign/index.html?view=goal&amp;focus=G024">G024</a>,
and <a href="../_static/constructive-grand-campaign/index.html?view=goal&amp;focus=G071">G071</a>.

## Independent proof certificate and immutable release

The complete self-contained next-layer certificate contains **589 genuine
theorem proof nodes**, one synthetic balanced conjunction root, **2,045 local
dependency arrows**, and **190,533 structural proof nodes**. The unchanged
intuitionistic checker calls the original kernel independently on all
**590 complete proof bodies**. The existing independently compiled Lean proof
checker also accepts the exact frozen 590-node artifact without translation
assumptions, additional axioms, or changes to the certificate.

```text
Bundle: research/arithmetic-library/artifacts/alpha-v20-next-layer-proof-bundle-v1.json
Bytes: 14,775,673
SHA-256: 1b623064f36e362c1a117daa193b1ee33ee7905ec804ee1ac164b42345b67069

Historical v20 channels: artifacts/peano-library/channels-v20.json
Catalog SHA-256: 8f86225cc560d7b59ff665e58594ac6249c12dbb5cdfe47ae2708a0e497c86ce
Enrollment SHA-256: 947e12db1db93decddd87b833067acf774a37fcb7d89de117010d53baf00065c
Edition SHA-256: ee0f596150d8609ab302303ade44c4413290675398a1d6999a47b3ba046ac38b
```

The historical Alpha-v19 parent, the sealed Alpha-v20, Alpha-v21, and
Alpha-v22 snapshots, and the Stable edition are unchanged. Current channels
are `artifacts/peano-library/channels-v28.json`. Hashes
identify sealed artifacts; only independent checking by the original kernel
grants the new theorem rows their Alpha checked-use authority.
