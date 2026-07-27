---
title: Checked theorem reuse
tags: [peano-lab, proof-certificate, cut-elimination, tactics]
---

In [[peano-lab]], `use add_comm` does not grant authority to the text `add_comm`. The library first
replays and independently checks a closed [[proof-certificate]]. The live engine rechecks that exact
formula/certificate pair and introduces it as an ordinary local hypothesis backed by a proof-term
cut.

Before QED, an untrusted capture-avoiding pass contracts the exposed implication and universal
redexes. The resulting closed certificate is checked against the session owner's original goal by
the [[trusted-kernel]]. A bug in name lookup or cut compilation can therefore cause rejection, but
cannot certify a false theorem.

This is the bridge from the [[theorem-ladder]] to a practical arithmetic toolbox: checked facts can
feed `specialize`, `apply`, `rewrite`, and `simp` without creating a trusted theorem oracle.
The temporary imported and live certificates are guarded by explicit node/depth budgets; exhaustion
is a transactional tactic limit, and QED retains the session on any remaining recursion failure.

## Related

[[proof-certificate]] · [[substitution]] · [[tactic-mode]] · [[de-bruijn-criterion]]
