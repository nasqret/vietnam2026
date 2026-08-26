---
title: Macro proof action
tags: [peano-lab, tactics, proof-search, llm]
---

# Macro proof action

A **macro proof action** is a typed, canonical proposal for a high-level proof
choice. Hydra version 1 permits `Use`, `Cut`, `Witness`, `Induct`, `Rewrite`,
`Split`, and bounded `Dispatch`.

This is a transport protocol, not a second proof language. Every macro compiles
deterministically to public Peano Lab tactics and/or a bounded untrusted solver
call. Execution is transactional, and no macro introduces a kernel rule.
`Dispatch` may return hints or a reconstructable derivation; a solver status
alone cannot close a goal.

The pre-H0 `surface-macro-v0` bootstrap carries one complete structural Peano
line and rejects automation, tacticals, session commands, and multiline text.
It tests portfolio/replay plumbing without a second interpreter; it is not the
structured version-1 protocol and cannot satisfy the H0 macro gate by itself.

The canonical trace records the state, allowed actions, raw proposal, parser
result, compiled commands, intermediate states, external transcript, resources,
and final [[trusted-kernel]] replay. This supports causal ablations and exposes
where a proposed proof actually failed.

## Related

- [[critical-proof-frontier]]
- [[tactic-mode]]
- [[tactical]]
- [[replayable-proof-script]]
- [[peano-hydra]]
- [[peano-lab-moc]]
