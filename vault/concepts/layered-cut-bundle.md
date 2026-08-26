---
title: Layered Cut bundle
tags: [peano-lab, proof-certificate, cut, proof-sharing, quadratic-reciprocity]
---

A **layered Cut bundle** compiles a [[lemma-dependency-dag]] into one ordinary
[[proof-certificate]] accepted by the unchanged [[trusted-kernel]]. Theorems
at each dependency depth are joined by a balanced conjunction. Later theorem
bodies discharge direct dependencies by short projections from earlier layer
packages. One existing contextual `Cut` introduces each package.

For the native quadratic-reciprocity graph, 557 nodes and 1,787 edges occupy
45 layers; root depth is 44 and the widest layer has 63 nodes. Thus the Cut
spine is 45 rather than 557, and a balanced dependency projection has depth at
most six. Every modular theorem body occurs once; repeated uses become
conjunction projections.

This choice is forced by a useful negative result. Recursive closure contains
191,648 theorem occurrences and has a rigorous lower bound of 731,423 proof
nodes before most body constructors are counted, so it cannot fit the
500,000-node policy. See the
[hotspot audit](../../research/arithmetic-library/quadratic-reciprocity-closure-hotspots.md).

The compiler still returns an ordinary proof whose final authority is only
`check((), certificate, QR)`. Its small 20-node fixture measures 274
nodes/depth 16, versus 3,643/depth 20 for the recursively expanded baseline.

Two exact-graph static checks go further. A distinct one-node dummy body at
every real node yields a rejected 13,705-node/depth-56 scaffold with 13,148
fixed glue nodes and balanced formula cost `144,197/68` occurrences/depth. A
distinct-target surrogate gives each node a unique shallow reflexive marker
derived from its local-ID bits. It retains all 557 nodes, 1,787 edges,
dependency orders, projections, and context indices. Each marker body adds one
existing dependency Cut that checks the exact dependency target against its
matching `Hyp(k-1)`. The unchanged kernel therefore type-checks every real
projection ID/direction and dependency order, accepting it at `19,066/74`;
its package formulas measure `19,297/18` occurrences/depth. The first is
deliberately invalid and the second contains no QR formula, so neither is QR
evidence.

The full real-body WMI certificate, resource and mutation receipts, browser
replay, registration, and admission remain pending.

This is preferred over a new [[closed-proof-dag]] checker because compiler
bugs can only make the unchanged kernel reject the final ordinary proof.
Hashes and theorem names remain provenance and builder metadata, never proof
authority.

Full construction, soundness, metrics, and gates:
[layered-cut-bundle.md](../../research/arithmetic-library/layered-cut-bundle.md).

## Related

[[self-contained-proof-sharing]] · [[closed-proof-dag]] ·
[[proof-certificate]] · [[trusted-kernel]] · [[quadratic-reciprocity-moc]]
