---
title: Local reasoning cut
tags: [peano-lab, tactics, proof-certificate, cut-elimination]
---

A **local reasoning cut** names an intermediate proposition without adding a theorem rule. In
[[peano-lab]], the exact forms `have h : P` and `suffices h : P` express the same reasoning:
prove `P`, then prove the old target with `h : P` available.

Their difference is scheduling. `have` shows `Γ ⊢ P` first and the old target under `h : P`
second. `suffices` shows the old target under `h : P` first and `Γ ⊢ P` second. Engine-only
`LocalHave` and `LocalSuffices` nodes put their holes in those exact orders, preserving the
goal-to-hole invariant of [[tactic-mode]].

Neither node belongs to the [[trusted-kernel]]. Before QED, an untrusted capture-avoiding compiler
uses [[substitution]] to replace the local hypothesis with its proof and removes the administrative
node. The resulting [[proof-certificate]] may contain separately introduced trusted sharing nodes,
but contains no `LocalHave` or `LocalSuffices`. It is checked from the empty context against the
session owner's original theorem. A bad schedule or compiler can therefore cause rejection, not a
false QED.

This resembles [[checked-theorem-reuse]], but the source of evidence differs: `use` imports an
already closed, rechecked library certificate, whereas `have` and `suffices` create new open goals
inside the current proof. Checked library reuse now uses
[[self-contained-proof-sharing|self-contained Cut]], while local scheduling deliberately retains
capture-avoiding compilation and gives no direct surface access to that trusted constructor.

## Related

[[peano-lab]] · [[tactic-mode]] · [[proof-certificate]] · [[substitution]] ·
[[checked-theorem-reuse]] · [[self-contained-proof-sharing]] · [[natural-deduction]]
