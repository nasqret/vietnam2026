# The constructive number-theory research atlas

The completed proofs are not isolated exhibits. They form the beginning of a
single dependency-aware research programme: **120 major mathematical goals**,
**16 reusable constructive tools**, **8 established proof anchors**, and
**107 pieces of mathematical vocabulary** distributed across twelve families.
The current sealed Alpha v19 library supplies **1,737 independently checked
theorems** and **5,779 checked proof dependencies**; the atlas explains how
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
| Bertrand and prime progressions | [F03: prime distribution](../_static/constructive-grand-campaign/index.html?view=family&focus=F03) · [G026: proved 1-mod-4 infinitude](../_static/constructive-grand-campaign/index.html?view=goal&focus=G026) | [544-theorem definition-aware Bertrand proof](../_static/bertrand-proof-explorer/defined/index.html) |
| Lucas and Kummer | [F04: binomial and valuation arithmetic](../_static/constructive-grand-campaign/index.html?view=family&focus=F04) | [Lucas proof](../_static/constructive-frontier-explorer/lucas/index.html) · [Kummer proof](../_static/constructive-frontier-explorer/kummer/index.html) |
| Two and four squares | [F07: quadratic forms](../_static/constructive-grand-campaign/index.html?view=family&focus=F07) · [G061: prime two-square criterion](../_static/constructive-grand-campaign/index.html?view=goal&focus=G061) | [Two-square proof](../_static/constructive-frontier-explorer/two-squares/index.html) · [Four-square proof](../_static/constructive-frontier-explorer/four-squares/index.html) |
| Pythagorean construction and Fermat descent | [F08: Diophantine equations](../_static/constructive-grand-campaign/index.html?view=family&focus=F08) · [A08: proved forward constructor](../_static/constructive-grand-campaign/index.html?view=goal&focus=A08) | [Pythagorean/Fermat-four proof explorer](../_static/constructive-frontier-explorer/pythagorean-fermat-four/index.html) |
| Complete linear congruences | [F02: congruences and orders](../_static/constructive-grand-campaign/index.html?view=family&focus=F02) · [G012: proved solvability criterion](../_static/constructive-grand-campaign/index.html?view=goal&focus=G012) | [The exact checked Alpha library](../_static/constructive-grand-campaign/index.html?view=goal&focus=G012) |

Each definition-aware proof graph retains its own exact theorem prerequisites
and distinguishes them visually from theorem-to-definition and
definition-to-definition notation arrows. The QR graph contains a forty-entry
conservative registry, of which 38 names occur; Bertrand uses 28 conservative
definitions. Their compact formulas expand back to the original native
first-order statements before any kernel replay.

The larger atlas also derives a vocabulary graph from all **107 campaign
terms**: **32 definition-to-definition edges** and **312 milestone-to-term
occurrences** connect reusable mathematical language across the programme.
These numbers describe the current machine-readable blueprint. Some
future-facing entries remain planning vocabulary rather than already compiled
kernel definitions; they must not be confused with the individually
expansion-checked registries in an existing proof explorer.

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
[infinitely many primes congruent to 3 modulo 4](../_static/constructive-grand-campaign/index.html?view=goal&focus=G025),
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
{doc}`Alpha and Stable library editions <library-editions>`.
