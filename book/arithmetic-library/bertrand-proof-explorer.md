# The complete Bertrand proof explorer

This explorer is the line-by-line reading room for the complete transitive
dependency closure of `bertrand_strict`. It uses the same searchable theorem
pages and layered graph controls as the quadratic-reciprocity explorer, but
its input is the exact Alpha-v12 catalog rather than an independently curated
campaign stack.

```{admonition} Complete proof, conservative release status
:class: important
The map contains all **544 theorem nodes**, **1,917 direct dependency edges**,
**28,410 authored tactic lines**, and **45 layers** needed by the final strict
Bertrand theorem. Of those nodes, 203 have checked-use evidence and 341 are
Alpha `body_checked` rows. The focused endpoint suites independently
kernel-check complete empty-context certificates; Alpha v12 still withholds
checked-use from its new rows pending a later promotion review.
```

Permanent explorer tags have the form `BTxxxx`. They are derived from the
immutable Alpha enrollment index in base 35, so additive editions cannot
renumber an existing page. The final endpoint is
<a href="../_static/bertrand-proof-explorer/tag/BT0127.html">
<code>BT0127</code></a>, `bertrand_strict`.

<p>
  <a class="btn btn-primary"
     href="../_static/bertrand-proof-explorer/graph.html?view=prerequisites">
    Open the complete interactive proof map
  </a>
  <a class="btn btn-outline-primary"
     href="../_static/bertrand-proof-explorer/index.html">
    Search all 544 theorem pages
  </a>
  <a class="btn btn-outline-primary"
     href="../_static/bertrand-proof-explorer/tag/BT0127.html">
    Open the final strict theorem
  </a>
</p>

<iframe
  src="../_static/bertrand-proof-explorer/graph.html?view=prerequisites"
  title="Complete interactive Bertrand proof dependency map"
  width="100%"
  height="980"
  loading="lazy">
  <p>
    Your browser does not support embedded pages.
    <a href="../_static/bertrand-proof-explorer/graph.html?view=prerequisites">
      Open the Bertrand proof map directly.
    </a>
  </p>
</iframe>

## Reading the map

Arrows point from prerequisite to dependent. The initial view displays the
complete 544-node prerequisite cone but only the focused route arrows, keeping
the overview legible. Select **All direct arrows** to draw the literal
1,917-edge graph. Other views expose:

- a shortest route from a theorem root;
- a critical route witnessing the full 45-layer depth;
- every route between a selected start and the endpoint;
- a direct neighborhood; or
- the dependent cone of any selected theorem.

Click any node to inspect its statement, evidence status, direct relations,
and source. The theorem-page link opens the exact expanded PA statement and
the complete numbered tactic body. Browser Back and Forward retrace the route.

## What the map does and does not certify

The builder reads the byte-frozen Alpha-v12 catalog and verifies the hash of
every source file represented in the closure. It does not execute tactics,
construct certificates, change enrollment, or grant proof authority. The
graph is a navigable rendering of evidence established elsewhere:

- candidate bodies were checked with their declared dependencies as
  hypotheses;
- focused recursive-closure tests rebuilt and kernel-checked the final BP01
  and BP02 empty-context certificates; and
- Alpha v12 records reviewed provenance while continuing to reject checked
  replay for its `body_checked` suffix.

For the mathematical narrative, see the {doc}`Bertrand campaign
<bertrand-campaign>`. For the release distinction, see {doc}`Alpha and Stable
library editions <library-editions>`.
