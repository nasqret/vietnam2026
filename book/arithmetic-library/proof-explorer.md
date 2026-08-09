# The Alpha QR proof explorer

The proof explorer is the line-by-line reading room for the
quadratic-reciprocity **Alpha slice** of the native arithmetic library. It
combines Stacks-style permanent theorem tags with a
LeanBlueprint-style dependency view, while retaining the exact Peano Lab
statement and authored tactic body for every node in the quadratic-reciprocity
closure.

```{admonition} This is a campaign slice, not either complete edition
:class: important
The 557 generated pages contain **241 Stable prerequisites** and **316 Alpha-only
specifications**. The complete Stable catalog has 432 theorems, so
191 Stable rows lie outside this QR closure. The canonical Alpha catalog has
885 rows; Stable union this slice has only 748 distinct theorem names. K3B and
other Alpha layers are documented separately.
The generated pages retain their historical `public`/`candidate` labels until
the unified Alpha explorer is built: read those only as Stable versus
Alpha-only membership in this slice. They are not canonical evidence labels.
In particular, the campaign corpus still calls `mod_eq_add_cancel_left`
body-checked, while its later HA receipt upgrades the same specification to
`alpha_closed` in the canonical Alpha catalog.
```

```{admonition} Read release membership and evidence separately
:class: note
In particular, `quadratic_reciprocity_combined` has a
kernel-checked modular body and a complete 557-node dependency graph, but its
layered closed certificate is still pending the WMI and admission gates. A
permanent tag, source hash, or green modular-body check is provenance—not an
axiom and not Stable promotion. See {doc}`Alpha and Stable library editions
<library-editions>` for the release lifecycle.
```

The live QR stack now classifies one former candidate-factory output,
`bounded_mod_inverse_unique`, as Stable within this slice because its Stable
and Alpha-source `TheoremSpec` values are exactly equal. This changes the live
status partition
from 240/317 to 241/316 without changing the 557-node, 1,787-edge, 45-layer
topology. The graph receipt is
`26017364ea943c4ed51a4a83f63ff0cd56b0de3686f0e0b458e7548ee84b1253`.
The generated explorer linked below already carries that 241/316 membership
split. Its remaining campaign-local evidence labels should still be read
through the canonical Alpha catalog as explained above.

Use the search and filters to choose a theorem, then follow any highlighted
lemma name in its informal outline or formal tactic lines. Each result has a
stable tag page, direct prerequisites, reverse references, source provenance,
and numbered proof-line anchors. Browser Back and Forward therefore retrace
your mathematical route.

<p>
  <a class="btn btn-primary" href="../_static/pa-proof-explorer/index.html">
    Open the Alpha QR proof explorer
  </a>
  <a class="btn btn-outline-primary" href="../_static/pa-proof-explorer/defined/index.html">
    Open the 40-definition reading edition
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
  title="Alpha quadratic-reciprocity Peano arithmetic proof explorer"
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
- **Trust and provenance** separates Stable membership, modular-body evidence,
  statement and script hashes, and source locations.

The {doc}`theorem atlas <theorem-atlas>` is the complete 432-theorem Stable
snapshot. The frozen QR explorer is exactly a 557-specification slice: 241 of
its rows occur in Stable and 316 are Alpha-only. It omits 191 Stable theorems,
and its 748-name union omits 137 other Alpha rows, so it must not be used as
the count for either complete edition. Exact
QR-factory overlaps are compatible migrations, not implicit promotion by the
explorer. Generated pages grant no entry to the Stable `pa lib` namespace.

When a fully expanded formula obscures the mathematical structure, use the
{doc}`definition-aware edition <defined-proof-explorer>`. It preserves the
same `PA` tags, 557-node proof graph, exact native replay lines, and
the same historical campaign labels while providing a 40-entry conservative-definition
registry; 38 definitions occur in this closure.

For the exact syntax and trust base behind every page, continue with the
{doc}`PA language reference <../peano/language-reference>` and
{doc}`axioms and proof rules <../peano/axioms-and-rules>`.
