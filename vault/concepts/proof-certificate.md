---
title: Proof certificate
tags: [proof-term, kernel, soundness]
---

A **proof certificate** is inert data recording the rule used at each proof step. In Peano Lab it
contains introduction and elimination nodes for intuitionistic [[natural-deduction]], equality
transport and congruence, six PA rule constants, an induction-schema instance, and the reviewed
[[self-contained-proof-sharing|self-contained Cut]] constructor.

Constructing this data does not establish a theorem. A certificate becomes evidence only when the
[[trusted-kernel]] checks it against an explicit context and formula. Tactics are therefore ordinary
untrusted programs that fill holes in a partial certificate.

The [[theorem-ladder]] composes earlier closed certificates with nested self-contained Cuts, then
checks the composed certificate again from the empty context. Each Cut embeds its formula, complete
lemma proof, conclusion, and body proof; names and hashes never become kernel evidence.

Named intermediate claims use the same authority boundary: a [[local-reasoning-cut]] is an
engine-only schedule that must be compiled away before this ordinary certificate reaches the
kernel. It is not the trusted sharing constructor.

Certificate size is likewise untrusted metadata. [[compact-arithmetic-certificate|Compact
arithmetic]] may choose a smaller ordinary tree, but only the kernel check supplies authority; a
best-found node count is not a theorem of global minimality.

## Related

[[peano-lab]] · [[trusted-kernel]] · [[tactic-mode]] · [[curry-howard]] ·
[[self-contained-proof-sharing]] · [[local-reasoning-cut]] ·
[[compact-arithmetic-certificate]]
