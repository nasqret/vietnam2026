---
title: Proof certificate
tags: [proof-term, kernel, soundness]
---

A **proof certificate** is inert data recording the rule used at each proof step. In Peano Lab it
contains introduction and elimination nodes for intuitionistic [[natural-deduction]], equality
transport and congruence, six PA rule constants, and an induction-schema instance.

Constructing this data does not establish a theorem. A certificate becomes evidence only when the
[[trusted-kernel]] checks it against an explicit context and formula. Tactics are therefore ordinary
untrusted programs that fill holes in a partial certificate.

The [[theorem-ladder]] composes earlier closed certificates by capture-avoiding cut elimination,
then checks the composed certificate again from the empty context.

Named intermediate claims use the same authority boundary: a [[local-reasoning-cut]] is an
engine-only schedule that must be compiled away before this ordinary certificate reaches the
kernel.

## Related

[[peano-lab]] · [[trusted-kernel]] · [[tactic-mode]] · [[curry-howard]] ·
[[local-reasoning-cut]]
