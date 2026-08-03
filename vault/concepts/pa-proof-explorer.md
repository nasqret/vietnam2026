---
title: Native PA Proof Explorer
tags: [peano-lab, proof-explorer, theorem-dag, quadratic-reciprocity, documentation]
---

The **native PA Proof Explorer** is the line-by-line reading surface for the
exact [[quadratic-reciprocity-moc|quadratic-reciprocity]] dependency closure.
It combines permanent Stacks-style theorem identities with a dependency/status
view and the actual Peano Lab tactic bodies.

The current corpus has 557 canonical `PAxxxx` pages, 1,787 direct edges in 45
layers, and 27,491 numbered tactic commands. The endpoint
`quadratic_reciprocity_combined` has tag `PA00FW`. The page links every
syntax-classified direct lemma occurrence, every explicit PA axiom occurrence,
and every tactic to its corresponding theorem or foundations page. Forward
and reverse neighborhoods expose the seven packaging dependencies that do not
occur literally in a later tactic line.

The graph renderer is deliberately sparse. It opens on the selected theorem's
direct neighborhood, draws only premise-path and selected-node arrows, and
uses compact clickable marks above 160 visible nodes. `edges=all` remains an
explicit full rendering mode; hiding an arrow never changes the 1,787-edge
API or the complete direct-relation lists. The definition-aware edition also
defaults to the selected node's conservative-definition closure rather than
all notation nodes used by the visible theorem set.

The status badge is not theorem authority: 240 pages are public, 316 are
body-checked candidates, and the QR root still awaits its layered
[[layered-cut-bundle]] closure. Likewise, every informal explanation says
whether it is a generated structural guide or curated prose.

Open the source dashboard at
[book/_static/pa-proof-explorer/index.html](../../book/_static/pa-proof-explorer/index.html)
or read the
[Jupyter Book chapter](../../book/arithmetic-library/proof-explorer.md).
The design and release gates live in
[pa-proof-explorer.md](../../research/arithmetic-library/pa-proof-explorer.md).

## Related

[[lemma-dependency-dag]] · [[proof-certificate]] · [[trusted-kernel]] ·
[[layered-cut-bundle]] · [[browser-proof-runtime]]
