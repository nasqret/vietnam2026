---
title: Checked numerical normalization
tags: [peano-lab, arithmetic, automation, proof-certificate]
---

Peano Lab's `norm_num` normalizes maximal closed numerical islands inside an equality, optionally
beneath leading universal binders. The untrusted computation chooses a canonical unary numeral; it
must also construct a PA3--PA6 equality proof and have the [[trusted-kernel]] check that certificate.
Computed values are never evidence by themselves.

The traversal is deterministic and left-to-right. Closed calculations can finish a wholly numerical
equality, while congruence lifts a calculation such as `2 * 3 = 6` through an open term like
`n + (2 * 3)`. A changed but still non-reflexive open equality remains a goal. False closed equations,
unresolved metavariables, unsupported goal shapes, and non-closing no-progress requests fail
transactionally. A reflexive equality may close without numerical computation.

This contract differs from [[simp-termination]], which applies an ordered rewrite set, and from
[[polynomial-normalization]], which proves unconditional identities by checked semiring
normalization. `norm_num` never mines hypotheses, proves inequalities or disequalities, solves
nonlinear assumptions, or decides general Peano arithmetic. A future Presburger `omega` needs a
separate certificate-producing design.

Input shape, leading universal binders, computation count, intermediate values, work, generated
numerical-bridge size/depth, complete live-proof size/depth, and wall time all have explicit bounds.
Exhaustion is an honest limit result and leaves [[tactic-mode]] and undo history unchanged.

## Related

[[proof-certificate]] · [[normal-form]] · [[simp-termination]] · [[polynomial-normalization]] ·
[[peano-lab]]
