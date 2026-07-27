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
node. The resulting ordinary [[proof-certificate]] is checked from the empty context against the
session owner's original theorem. A bad schedule or compiler can therefore cause rejection, not a
false QED.

This resembles [[checked-theorem-reuse]], but the source of evidence differs: `use` imports an
already closed, rechecked library certificate, whereas `have` and `suffices` create new open goals
inside the current proof. Neither mechanism gives certificate-tree sharing; repeated uses may copy
the inserted proof during cut elimination.

## Related

[[peano-lab]] · [[tactic-mode]] · [[proof-certificate]] · [[substitution]] ·
[[checked-theorem-reuse]] · [[natural-deduction]]
