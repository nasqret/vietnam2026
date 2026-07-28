---
title: Checked theorem reuse
tags: [peano-lab, proof-certificate, cut-elimination, tactics]
---

In [[peano-lab]], `use add_comm` does not grant authority to the text `add_comm`. The library first
replays and independently checks a closed [[proof-certificate]]. The live engine rechecks that exact
formula/certificate pair and embeds it in
[[self-contained-proof-sharing|`Cut(formula, target, certificate, body)`]].

The Cut carries no theorem name or hash. Before QED, the untrusted normalizer removes engine-only
local schedulers and contracts exposed implication and universal redexes, but preserves trusted
Cuts. The [[trusted-kernel]] then checks the imported lemma branch once and the body under its new
hypothesis, all against the session owner's original goal. A bug in name lookup or packaging can
therefore cause rejection, but cannot certify a false theorem.

This is the bridge from the [[theorem-ladder]] to a practical arithmetic toolbox: checked facts can
feed `specialize`, `apply`, `rewrite`, and `simp` without creating a trusted theorem oracle.
The temporary imported and live certificates are guarded by explicit node/depth budgets; exhaustion
is a transactional tactic limit, and QED retains the session on any remaining recursion failure.

## Related

[[proof-certificate]] · [[self-contained-proof-sharing]] · [[substitution]] ·
[[tactic-mode]] · [[de-bruijn-criterion]]
