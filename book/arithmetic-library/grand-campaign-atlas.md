# The constructive number-theory research atlas

The completed proofs are not isolated exhibits. They form the beginning of a
single dependency-aware research programme: **120 major mathematical goals**,
**16 reusable constructive tools**, **8 established proof anchors**, and
**152 pieces of mathematical vocabulary** distributed across twelve families.
The current sealed Alpha v23 library supplies **1,949 independently checked
theorems** and **6,285 checked proof dependencies**; the atlas explains how
these existing results support the much larger, still honestly open programme.

```{admonition} A research map is not a proof certificate
:class: important
The atlas separates actual theorem prerequisites, notation dependencies,
historical anchors, verified Alpha/Stable results, and unproved research
objectives. An open goal, a future definition, a conceptual analogy, or a
suggestive arrow never grants proof authority. The unchanged intuitionistic
kernel remains the sole checker of native theorem certificates.
```

<p>
  <a class="btn btn-primary"
     href="../_static/constructive-grand-campaign/index.html">
    Open the complete multiscale research atlas
  </a>
  <a class="btn btn-outline-primary"
     href="../_static/constructive-grand-campaign/index.html?view=family&amp;focus=F05">
    Focus on reciprocity
  </a>
  <a class="btn btn-outline-primary"
     href="../_static/constructive-grand-campaign/index.html?view=definition&amp;focus=Prime">
    Follow the definition of primality
  </a>
</p>

<iframe
  src="../_static/constructive-grand-campaign/index.html"
  title="Interactive multiscale constructive number-theory research atlas"
  width="100%"
  height="1050"
  loading="lazy">
  <p>
    Your browser does not support embedded pages.
    <a href="../_static/constructive-grand-campaign/index.html">
      Open the constructive number-theory atlas directly.
    </a>
  </p>
</iframe>

## Five mathematical scales

The first view condenses the complete programme into five domains. Its
connections are computed from the actual goal/tool/anchor prerequisite graph,
not from a hand-drawn similarity diagram. Select a domain to reveal its
families; select a family to retain its genuine cross-family prerequisites;
then open a goal, its definitions, or the corresponding concrete proof
explorer.

| Domain | Mathematical families | Open the domain |
|---|---|---|
| Foundations, congruences, and combinatorics | divisibility and factorization; congruences and multiplicative orders; binomial and valuation arithmetic | [D01](../_static/constructive-grand-campaign/index.html?view=domain&focus=D01) |
| Primes, reciprocity, and algebraic integers | prime distribution; quadratic and higher reciprocity; Gaussian, Eisenstein, and cyclotomic arithmetic | [D02](../_static/constructive-grand-campaign/index.html?view=domain&focus=D02) |
| Additive theory, quadratic forms, and Diophantine equations | additive combinatorics; sums of squares and quadratic forms; Pell, Pythagorean, and Fermat problems | [D03](../_static/constructive-grand-campaign/index.html?view=domain&focus=D03) |
| Finite fields and certified computation | polynomial and finite-field methods; constructive algorithms and certified cryptography | [D04](../_static/constructive-grand-campaign/index.html?view=domain&focus=D04) |
| Elliptic curves, lattices, and descent | rational elliptic curves, finite Selmer supersets, lattice algorithms, and explicit descent | [D05](../_static/constructive-grand-campaign/index.html?view=domain&focus=D05) |

The twelve development families contain ten major goals each. Existing
quadratic reciprocity, Bertrand, supplementary laws, Lucas, Kummer, sums of
squares, and Pythagorean constructions are entry points into this common
programme rather than disconnected databases.

## From the large map to an actual proof

| Concrete campaign | Family position | Existing proof explorer |
|---|---|---|
| Quadratic reciprocity and supplementary laws | [F05: reciprocity](../_static/constructive-grand-campaign/index.html?view=family&focus=F05) · [G043: proved quadratic reciprocity](../_static/constructive-grand-campaign/index.html?view=goal&focus=G043) | [557-theorem definition-aware QR proof](../_static/pa-proof-explorer/defined/index.html) |
| Bertrand and prime progressions | [F03: prime distribution](../_static/constructive-grand-campaign/index.html?view=family&focus=F03) · [G026: proved 1-mod-4 infinitude](../_static/constructive-grand-campaign/index.html?view=goal&focus=G026) · [G025: proved 3-mod-4 infinitude](../_static/constructive-grand-campaign/index.html?view=goal&focus=G025) | [544-theorem definition-aware Bertrand proof](../_static/bertrand-proof-explorer/defined/index.html) · [18-theorem 3-mod-4 prime proof](../_static/constructive-milestone-closure-explorer/primes-three-mod-four/index.html) |
| Lucas and Kummer | [F04: binomial and valuation arithmetic](../_static/constructive-grand-campaign/index.html?view=family&focus=F04) | [Lucas proof](../_static/constructive-frontier-explorer/lucas/index.html) · [Kummer proof](../_static/constructive-frontier-explorer/kummer/index.html) |
| Two and four squares | [F07: quadratic forms](../_static/constructive-grand-campaign/index.html?view=family&focus=F07) · [G061: prime two-square criterion](../_static/constructive-grand-campaign/index.html?view=goal&focus=G061) | [Two-square proof](../_static/constructive-frontier-explorer/two-squares/index.html) · [Four-square proof](../_static/constructive-frontier-explorer/four-squares/index.html) |
| Pythagorean construction and Fermat descent | [F08: Diophantine equations](../_static/constructive-grand-campaign/index.html?view=family&focus=F08) · [A08: proved forward constructor](../_static/constructive-grand-campaign/index.html?view=goal&focus=A08) | [Pythagorean/Fermat-four proof explorer](../_static/constructive-frontier-explorer/pythagorean-fermat-four/index.html) |
| Complete linear congruences | [F02: congruences and orders](../_static/constructive-grand-campaign/index.html?view=family&focus=F02) · [G012: proved solvability criterion](../_static/constructive-grand-campaign/index.html?view=goal&focus=G012) | [The exact checked Alpha library](../_static/constructive-grand-campaign/index.html?view=goal&focus=G012) |
| Constructive polynomial evaluation | [T12: proved natural Horner evaluation](../_static/constructive-grand-campaign/index.html?view=goal&focus=T12) | [Seven-theorem polynomial Horner explorer](../_static/constructive-next-layer-explorer/polynomial-horner/index.html) |
| Finite matrix components | [T13: open full matrix and lattice milestone](../_static/constructive-grand-campaign/index.html?view=goal&focus=T13) | [Ten historical checked matrix and dot-product components](../_static/constructive-next-layer-explorer/matrix-dot-product/index.html) |
| Arbitrary natural and signed matrix products | [T13: 33 checked components; arbitrary determinant/rank/lattice still open](../_static/constructive-grand-campaign/index.html?view=goal&focus=T13) | [Twenty-three independently checked coded-product theorems](../_static/constructive-advanced-layer-explorer/matrix-coded-products/index.html) |
| Euclidean execution, terminal gcd, and exact logarithmic complexity | [G101: closed; actual terminal gcd and steps ≤ 2 · BitLen(b) + 1](../_static/constructive-grand-campaign/index.html?view=goal&focus=G101) | [17-theorem complete logarithmic Euclidean-GCD proof](../_static/constructive-milestone-closure-explorer/euclidean-logarithmic-bound/index.html) · {doc}`Twenty historical terminal-gcd transport proofs <transport-layer-campaign>` |
| Canonical arbitrary-exponent digits and actual binary modular execution | [G102: closed; operations ≤ 3 · BitLen(e) + 2](../_static/constructive-grand-campaign/index.html?view=goal&focus=G102) | [24-theorem complete canonical-digit/execution proof](../_static/constructive-milestone-closure-explorer/binary-digit-extraction/index.html) · {doc}`Nineteen historical binary-execution proofs <transport-layer-campaign>` |
| Exact object-language binary length | [F11: verified number-theoretic algorithms](../_static/constructive-grand-campaign/index.html?view=family&focus=F11) · [G101: shared total and unique BitLen foundation](../_static/constructive-grand-campaign/index.html?view=goal&focus=G101) | {doc}`Twenty-one total, functional, and unique binary-length proofs <transport-layer-campaign>` |
| Stronger Bertrand prime constructions | [F03: prime distribution](../_static/constructive-grand-campaign/index.html?view=family&focus=F03) · [G023: exact valuation one](../_static/constructive-grand-campaign/index.html?view=goal&focus=G023) · [G024: arbitrary finite prime chains](../_static/constructive-grand-campaign/index.html?view=goal&focus=G024) | [Thirteen-theorem Bertrand prime-chain explorer](../_static/constructive-next-layer-explorer/bertrand-prime-chains/index.html) |
| Finite continued fractions | [F08: Diophantine equations](../_static/constructive-grand-campaign/index.html?view=family&focus=F08) · [G071: proved finite continued fractions](../_static/constructive-grand-campaign/index.html?view=goal&focus=G071) | [Nine-theorem continued-fraction explorer](../_static/constructive-next-layer-explorer/continued-fractions/index.html) |

Each definition-aware proof graph retains its own exact theorem prerequisites
and distinguishes them visually from theorem-to-definition and
definition-to-definition notation arrows. The QR graph contains a forty-entry
conservative registry, of which 38 names occur; Bertrand uses 28 conservative
definitions. Their compact formulas expand back to the original native
first-order statements before any kernel replay.

The larger atlas also derives a vocabulary graph from all **152 campaign
terms**: **108 definition-to-definition edges**, **311 statement-lexical
milestone-to-term occurrences**, and **55 separately typed, explicitly declared
notation references** connect reusable mathematical language across the
programme. Together these form **366 milestone-to-notation edges**.
Historical v22 contained 88 definition-to-definition edges and 41 explicitly
declared references before the new milestone-closure notation was independently
reviewed.
These numbers describe the current machine-readable blueprint. Some
future-facing entries remain planning vocabulary rather than already compiled
kernel definitions; they must not be confused with the individually
expansion-checked registries in an existing proof explorer.

The complete derived artifact is
[`definitions.json`](../_static/constructive-grand-campaign/definitions.json).
It sorts all 152 vocabulary terms into **six dependency-first notation
layers**, records every direct and transitive definition prerequisite, maps
each term to the campaign statements that actually mention it, and separately
audits the **97 genuinely shared conservative registry definitions** and their
**159 reviewed dependency edges**. These include all eleven exact, hygienically
expanded historical Alpha-v20 definition objects under permanent
`ND0001`–`ND0011` identities, sixteen historical Alpha-v21 identities
`ND0012`–`ND0027`, ten historical Alpha-v22 identities `ND0028`–`ND0037`,
and eight new Alpha-v23 identities `ND0038`–`ND0045`;
the atlas and theorem-family explorers use the very same
immutable first-order formula objects. Notation layers and notation edges never
become theorem premises.

Exactly **sixty-one signature-compatible links** connect blueprint vocabulary
to real, expansion-checked reading definitions: fifty-seven share their exact names,
and four use explicitly recorded aliases. In particular,
`Beta(b,c,i,x)` corresponds to `BetaAt(b,c,i,x)`, `Binom(n,k,z)` to
`Choose(n,k,z)`, and `Fact(n,z)` to `Factorial(n,z)`. The map also records the
nontrivial argument permutation relating `Gcd(a,b,g)` to `IsGCD(g,a,b)`:
the reviewed argument positions in the blueprint are `[2,0,1]`.

The eight additional shared identities lead directly to genuine audited
definition pages: [`Horner` (`ND0002`)](../_static/constructive-next-layer-explorer/polynomial-horner/explorer/defined/definition/ND0002.html);
[`MatrixAt` (`ND0003`)](../_static/constructive-next-layer-explorer/matrix-dot-product/explorer/defined/definition/ND0003.html),
[`DotProduct` (`ND0004`)](../_static/constructive-next-layer-explorer/matrix-dot-product/explorer/defined/definition/ND0004.html),
and [`SignedDet2` (`ND0005`)](../_static/constructive-next-layer-explorer/matrix-dot-product/explorer/defined/definition/ND0005.html);
[`BertrandWindow` (`ND0006`)](../_static/constructive-next-layer-explorer/bertrand-prime-chains/explorer/defined/definition/ND0006.html),
[`PowerValuationOne` (`ND0007`)](../_static/constructive-next-layer-explorer/bertrand-prime-chains/explorer/defined/definition/ND0007.html),
and [`BertrandChain` (`ND0008`)](../_static/constructive-next-layer-explorer/bertrand-prime-chains/explorer/defined/definition/ND0008.html);
and [`ContinuedFraction` (`ND0011`)](../_static/constructive-next-layer-explorer/continued-fractions/explorer/defined/definition/ND0011.html).
The canonical `Beta` display identity `ND0001` has the exactly identical
parsed formula as `BetaAt`; its atlas link intentionally retains its original
reviewed `PD0013` identity instead of replacing existing cross-campaign links.

The historical v21 globally shared identities make the preceding advanced
layer navigable:
[`MatrixProductCell` (`ND0013`)](../_static/constructive-advanced-layer-explorer/matrix-coded-products/explorer/defined/definition/ND0013.html),
[`SignedMatrixProduct` (`ND0017`)](../_static/constructive-advanced-layer-explorer/matrix-coded-products/explorer/defined/definition/ND0017.html),
[`EuclideanExecution` (`ND0020`)](../_static/constructive-advanced-layer-explorer/euclidean-complexity/explorer/defined/definition/ND0020.html),
[`CanonicalModularResidue` (`ND0023`)](../_static/constructive-advanced-layer-explorer/binary-modular-exponentiation/explorer/defined/definition/ND0023.html),
and [`BinaryModularStep` (`ND0026`)](../_static/constructive-advanced-layer-explorer/binary-modular-exponentiation/explorer/defined/definition/ND0026.html).
Each is the same reviewed first-order definition object in the large research
atlas and its corresponding local theorem proof graph.

The ten historical v22 identities extend the same actual registry without replacing
any historical object: `PowTwo` (`ND0028`), `BinaryDigit` (`ND0029`), `BitLen`
(`ND0030`), `EuclideanCommonDivisor` (`ND0031`), `EuclideanStateAt`
(`ND0032`), `EuclideanAnchoredExecution` (`ND0033`), `BinaryDigitPrefix`
(`ND0034`), `BinaryExecutionTrace` (`ND0035`), `BinaryModularExecution`
(`ND0036`), and `BinaryExecutionPowerInvariant` (`ND0037`). Each hygienically
expands into the unchanged first-order arithmetic language.

The eight v23 identities connect the completely proved milestones to the
identical global and family-local definition objects:
[`EuclideanBoundedTrace` (`ND0038`)](../_static/constructive-milestone-closure-explorer/euclidean-logarithmic-bound/explorer/defined/definition/ND0038.html),
[`EuclideanLogarithmicExecution` (`ND0039`)](../_static/constructive-milestone-closure-explorer/euclidean-logarithmic-bound/explorer/defined/definition/ND0039.html),
[`BinaryExponentDigitCode` (`ND0040`)](../_static/constructive-milestone-closure-explorer/binary-digit-extraction/explorer/defined/definition/ND0040.html),
[`BinaryCanonicalExponentDigitCode` (`ND0041`)](../_static/constructive-milestone-closure-explorer/binary-digit-extraction/explorer/defined/definition/ND0041.html),
[`BinaryCompleteModularExecution` (`ND0042`)](../_static/constructive-milestone-closure-explorer/binary-digit-extraction/explorer/defined/definition/ND0042.html),
[`BinaryExecutionOperationCount` (`ND0043`)](../_static/constructive-milestone-closure-explorer/binary-digit-extraction/explorer/defined/definition/ND0043.html),
[`PrimeThreeModFourDivisor` (`ND0044`)](../_static/constructive-milestone-closure-explorer/primes-three-mod-four/explorer/defined/definition/ND0044.html),
and [`EuclidThreeNumber` (`ND0045`)](../_static/constructive-milestone-closure-explorer/primes-three-mod-four/explorer/defined/definition/ND0045.html).
These are conservative hygienic abbreviations, never added axioms.

Two tempting identifications are deliberately rejected: the campaign's
three-argument `Sum(s,ell,z)` and `Prod(s,ell,z)` are not the checked
four-argument `Sum(b,c,l,z)` and `Product(b,c,l,z)` beta-code relations.
Their incompatible signatures remain visible, but confer **no checked
definition evidence**. The synchronizer refuses self-reference, cycles,
duplicate parameters, invalid argument alignments, and stale derived DAG
artifacts before the proof site can be staged.

The first newly implemented campaign layers use honest, dependency-ordered
terms: `BertrandWindow` depends on `Prime` and `Lt`; `BertrandChain` depends
on `Beta`, `Lt`, and `BertrandWindow`; and `PowerValuationOne` depends on the
already reviewed `PowerValuation` relation. The effective polynomial/matrix
substrate introduces `Horner`, `MatrixAt`, `DotProduct`, and `SignedDet2`.
The polynomial milestone is stated at exactly its proved scope: natural
beta-coded Horner evaluation, not arbitrary presented rings or formal
differentiation. Arbitrary natural and signed matrix multiplication is now
proved, but T13 retains its stronger arbitrary determinant/rank/lattice target
and therefore remains open despite **33 independently checked components**.
G101 now has an actual execution, proven terminal-state gcd identification,
total unique object-language `BitLen`, two-step halving, and its completely
proved exact `steps <= 2 * BitLen(b) + 1` logarithmic bound. G102 now
constructs canonical beta-coded digits for **every arbitrary exponent**,
proves complete actual modular execution and its unique correct residue, and
derives `operations <= 3 * BitLen(e) + 2`. G025 independently proves that,
for every supplied natural bound, there is a larger prime congruent to three
modulo four. All three full milestones are closed by actual original-kernel
proofs and independently checked by the compiled Lean verifier.
Their `definition_refs` fields supply separately typed display links without
pretending that expanded proof syntax already contains those surface names.

## A practical research workflow

For a number theorist, a useful path through the database is:

1. Select a domain and compare its already checked, open, and immediately
   available-frontier goals.
2. Open a family to inspect the exact prerequisite cone shared with other
   parts of number theory.
3. Choose a proved anchor and inspect its linked theorem statement, complete
   proof, independently checked evidence, and mathematical definitions.
4. Choose an open successor and inspect which prerequisites are actually
   available and which still require a new constructive argument.
5. Follow a shared definition or cross-family dependency to search for
   transferable lemmas, algorithms, witnesses, and possible generalizations.
6. Formalize the next result in the unchanged object language, check its
   complete dependency certificate, and promote it through Alpha before any
   separate Stable decision.

Interesting honest frontiers include
[Jacobi-symbol reciprocity](../_static/constructive-grand-campaign/index.html?view=goal&focus=G045),
[cubic reciprocity](../_static/constructive-grand-campaign/index.html?view=goal&focus=G047),
[quartic reciprocity](../_static/constructive-grand-campaign/index.html?view=goal&focus=G048),
[two-square representation counts](../_static/constructive-grand-campaign/index.html?view=goal&focus=G063),
[four-square representation formulas](../_static/constructive-grand-campaign/index.html?view=goal&focus=G065),
[the missing inverse in primitive Pythagorean parametrization](../_static/constructive-grand-campaign/index.html?view=goal&focus=G077),
[Fermat exponent-four descent](../_static/constructive-grand-campaign/index.html?view=goal&focus=G078),
[Cornacchia's certified algorithm](../_static/constructive-grand-campaign/index.html?view=goal&focus=G107),
and [finite 2-Selmer bounds](../_static/constructive-grand-campaign/index.html?view=goal&focus=G120).
None is represented as proved merely because its formal target and roadmap
can already be displayed.

The complete machine-readable dataset is
[`campaign.json`](../_static/constructive-grand-campaign/campaign.json), and
the mathematical design is recorded in the repository's
[`Grand Constructive Number-Theory Campaign`](https://github.com/nasqret/vietnam2026/blob/agent/new-theorems-tranche-01/PLAN/14_constructive_number_theory_grand_campaign.md).
For formal release evidence and exact membership, continue with
{doc}`Alpha and Stable library editions <library-editions>` and the
{doc}`three preceding advanced constructive campaigns <advanced-layer-campaign>`
and the {doc}`binary and Euclidean transport layer <transport-layer-campaign>`.
