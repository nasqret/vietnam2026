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

The H0 implementation deliberately has no in-process callback adapter. A
content-addressed executable receives detached canonical JSON in a fresh
process. Its configuration, call preimage, raw response, and host observations
are retained. Returned command lines are reconstructed through the capability-
checked public surface, and any closed state is replayed from the original goal
through the [[trusted-kernel]]. Linux non-root execution supplies the
campaign-grade hard memory/process envelope; macOS RSS sampling is explicitly
diagnostic. Adapter-reported step counts are untrusted accounting, not a host
instruction counter.

The pre-H0 `surface-macro-v0` bootstrap carries one complete structural Peano
line and rejects automation, tacticals, session commands, and multiline text.
It tests portfolio/replay plumbing without a second interpreter; it is not the
structured version-1 protocol and cannot satisfy the H0 macro gate by itself.

The canonical trace records the state, allowed actions, raw proposal, parser
result, compiled commands, intermediate states, external transcript, resources,
and final [[trusted-kernel]] replay. This supports causal ablations and exposes
where a proposed proof actually failed.

Trace loading is replay-aware. It recompiles the raw action, reconstructs the
recorded owner prefix, resolves premises, replays intermediate commands, and
rechecks final certificate metrics and hashes. Exact-field shape and
self-consistent hashes are insufficient evidence by themselves.

## Related

- [[critical-proof-frontier]]
- [[tactic-mode]]
- [[tactical]]
- [[replayable-proof-script]]
- [[peano-hydra]]
- [[peano-hydra-result-evidence]]
- [[peano-hydra-conformance-campaign]]
- [[peano-lab-moc]]
