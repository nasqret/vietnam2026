# The native PA proof explorer

The proof explorer is the line-by-line reading room for the native arithmetic
library. It combines Stacks-style permanent theorem tags with a
LeanBlueprint-style dependency view, while retaining the exact Peano Lab
statement and authored tactic body for every node in the quadratic-reciprocity
closure.

```{admonition} Read the status before the proof
:class: important
The explorer distinguishes public closed theorems from dependency-curried
candidate bodies. In particular, `quadratic_reciprocity_combined` has a
kernel-checked modular body and a complete 557-node dependency graph, but its
layered closed certificate is still pending the WMI and admission gates. A
permanent tag, source hash, or green modular-body check is provenance—not an
axiom and not public admission.
```

Use the search and filters to choose a theorem, then follow any highlighted
lemma name in its informal outline or formal tactic lines. Each result has a
stable tag page, direct prerequisites, reverse references, source provenance,
and numbered proof-line anchors. Browser Back and Forward therefore retrace
your mathematical route.

<p>
  <a class="btn btn-primary" href="../_static/pa-proof-explorer/index.html">
    Open the full proof explorer
  </a>
  <a class="btn btn-outline-primary" href="../_static/pa-proof-explorer/foundations.html">
    Read the PA grammar and axioms
  </a>
  <a class="btn btn-outline-primary" href="../_static/pa-proof-explorer/graph.html?target=PA00FW">
    Draw theorem dependency paths
  </a>
  <a class="btn btn-outline-primary" href="../_static/pa-proof-explorer/tag/PA00FW.html">
    Jump to quadratic reciprocity · PA00FW
  </a>
</p>

<iframe
  src="../_static/pa-proof-explorer/index.html"
  title="Native Peano arithmetic proof explorer"
  width="100%"
  height="920"
  loading="lazy">
  <p>
    Your browser does not support embedded pages.
    <a href="../_static/pa-proof-explorer/index.html">Open the proof explorer directly.</a>
  </p>
</iframe>

## Follow a path through the library

The {doc}`interactive dependency graph <dependency-graph>` draws arrows from
prerequisite to dependent and opens with PA00FW as its target. It can isolate
a short premise chain, a critical/deepest chain, every route in a chosen
start-to-target corridor, or the complete prerequisite cone. This keeps the
difference between one readable route and all required premises explicit.

## How to read a theorem page

- **Informal proof** explains the mathematical route and names its reusable
  ingredients. Generated structural outlines are labeled as such; they are
  not presented as reviewed prose.
- **Formal PA proof** numbers every authored tactic command. A theorem token
  links to that theorem's permanent page, and the line number is itself a
  stable target.
- **Dependencies** moves backward to prerequisites or forward to direct
  clients. The {doc}`dependency graph <dependency-graph>` expands that local
  view into selectable paths and transitive cones without forcing all 557
  nodes onto the canvas at once.
- **Trust and provenance** separates public admission, modular-body evidence,
  statement and script hashes, and source locations.

The existing {doc}`theorem atlas <theorem-atlas>` remains the compact,
progressively enhanced view of the public 384-theorem snapshot. The explorer
adds the exact quadratic-reciprocity closure and permanent line-level routes;
it does not silently promote those candidates into `pa lib`.

For the exact syntax and trust base behind every page, continue with the
{doc}`PA language reference <../peano/language-reference>` and
{doc}`axioms and proof rules <../peano/axioms-and-rules>`.
