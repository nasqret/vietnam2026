# The definition-aware Bertrand proof explorer

This parallel reading edition presents the complete **544-theorem** proof of
Bertrand's Postulate using **28 conservative, linked mathematical
definitions**. It keeps all **1,917 proof dependencies**, **28,410 authored
tactic lines**, and the exact endpoint <code>BT0127</code>, while making the
campaign's powers, binomial coefficients, primorials, valuations, and prime
intervals readable.

```{admonition} Definitions are presentation, not proof authority
:class: important
Each compact formula expands to exactly the original first-order PA formula.
No definition introduces a kernel rule, axiom, predicate constant, theorem,
or checked-use admission. The frozen Alpha-v12 catalog remains the sole source
for theorem statements, tactic scripts, and historical enrollment provenance.
Independently sealed current Alpha-v19 release evidence establishes checked
use for all 544 actual theorem proofs: 202 Stable and 342 Alpha-only. The
complete proof bundle is separately accepted by the unchanged intuitionistic
kernel and compiled Lean verifier; Alpha-only membership is not Stable.
```

<p>
  <a class="btn btn-primary"
     href="../_static/bertrand-proof-explorer/defined/index.html">
    Open the definition-aware Bertrand explorer
  </a>
  <a class="btn btn-outline-primary"
     href="../_static/bertrand-proof-explorer/defined/graph.html?target=BT0127&amp;view=neighborhood&amp;definitions=selected&amp;edges=focus">
    Draw the mixed proof-and-definition graph
  </a>
  <a class="btn btn-outline-primary"
     href="../_static/bertrand-proof-explorer/defined/tag/BT0127.html">
    Read the strict Bertrand theorem
  </a>
  <a class="btn btn-outline-primary"
     href="../_static/bertrand-proof-explorer/index.html">
    Inspect the exact fully expanded edition
  </a>
  <a class="btn btn-outline-primary"
     href="../_static/constructive-grand-campaign/index.html?view=family&amp;focus=F03">
    Place Bertrand in the prime-distribution campaign
  </a>
</p>

<iframe
  src="../_static/bertrand-proof-explorer/defined/graph.html?target=BT0127&amp;view=neighborhood&amp;definitions=selected&amp;edges=focus"
  title="Definition-aware interactive Bertrand proof dependency map"
  width="100%"
  height="980"
  loading="lazy">
  <p>
    Your browser does not support embedded pages.
    <a href="../_static/bertrand-proof-explorer/defined/graph.html?target=BT0127&amp;view=neighborhood&amp;definitions=selected&amp;edges=focus">
      Open the definition-aware Bertrand proof map directly.
    </a>
  </p>
</iframe>

## Mathematical vocabulary of the proof

The explorer reuses foundational arithmetic notation where appropriate and
introduces campaign-local abbreviations for the structures that actually
drive Bertrand's proof:

| Proof layer | Relevant mathematical definitions |
|---|---|
| order, divisibility, and primality | `Le`, `Lt`, `Dvd`, and `Prime` |
| finite arithmetic constructions | `Pow`, `Factorial`, and encoded finite products |
| binomial coefficients | `Choose` and `CentralBinom` |
| products of primes | `Primorial` and its prime-factor support |
| prime-power accounting | `PowerValuation` and `FactorialValuation` |
| Legendre's formula | `LegendreSum` and the factorial-valuation bridge |
| square-root bounds | `FloorSqrt` and the small-prime cutoff |

Every highlighted call links to a definition page giving its arity, explicit
first-order expansion, conceptual prerequisites, and the theorems that use
it. The original statement and exact proof commands remain available beside
their compact presentation.

## Reading the mixed dependency graph

Solid arrows connect theorem prerequisites; purple arrows connect a theorem to
definitions appearing in its statement or local proof propositions.
Definition-to-definition arrows describe conservative notation structure.
Only theorem arrows participate in proof paths, prerequisite cones, critical
routes, and the 45-layer depth calculation.

The initial view focuses on <code>BT0127</code> and its immediate proof
neighborhood. Switch to **Prerequisites** for the complete proof, enable all
definitions to inspect the visible mathematical vocabulary, or follow any
linked theorem to its exact certificate and source provenance.

For the original frozen graph and release-evidence boundary, see the
{doc}`complete Bertrand proof explorer <bertrand-proof-explorer>`. For the
mathematical campaign, see {doc}`Bertrand's Postulate <bertrand-campaign>`.
For its shared definitions, related prime-progressions results, and open
research successors, see the {doc}`constructive number-theory research atlas
<grand-campaign-atlas>`.
