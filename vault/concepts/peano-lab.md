---
title: Peano Lab
tags: [tool, peano-arithmetic, browser, soundness]
---

**Peano Lab** is a small theorem prover for first-order Peano arithmetic. It runs Python inside a
self-hosted Pyodide Web Worker and presents proofs through a terminal-like browser UI.

Its governing separation is simple: tactics may construct a [[proof-certificate]], but only the
[[trusted-kernel]] may claim QED. The checker receives the session owner's original formula rather
than trusting a goal returned by the tactic engine.

The public learning path is the [[theorem-ladder]]. The lab is intuitionistic by default; use of
double-negation elimination is explicit and checked only in the labeled classical mode.

## Related

[[peano-lab-moc|Peano Lab MOC]] · [[natural-deduction]] · [[tactic-mode]] ·
[[checked-numerical-normalization]] · [[substitution]]
