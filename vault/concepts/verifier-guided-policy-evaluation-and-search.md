---
title: Verifier-guided policy evaluation and search
tags: [peano-lab, llm, evaluation, search, soundness]
---

# Verifier-guided policy evaluation and search

**Verifier-guided policy evaluation** executes model-proposed tactic lines transactionally and
counts success only after [[kernel-judged-evaluation]] accepts the final certificate against the
original theorem and exact logic mode. Peano Lab's implemented evaluator supports deterministic
independent rollouts, fixed step budgets, pass@k reports, policy and goal-set identities, and a
capability-scoped held-out environment. The target theorem is not importable, and `auto` is not an
unreported escape hatch.

The next planned layer is verifier-guided best-first search. A policy would propose several tactic
lines at each state; the ordinary public surface would either reject each action without changing
the parent or return a successor. Search would hash canonical successor states to deduplicate the
frontier and rank candidates initially by accumulated negative log probability plus a documented
depth penalty. Hard budgets would bound tokens, proposals, unique states, verifier calls, wall
time, and certificate size. Deterministic arithmetic closers may be reported as an explicit
ablation, while the policy handles branching choices such as induction, witnesses, rewrite
direction, and local lemmas.

Only final kernel-checked trajectories may feed [[kernel-guided-policy-training|expert iteration]].
The current repository has the rollout evaluator and the research contract, but **the best-first
driver, trained-model measurements, and expert-iteration results are still pending**.

## Related

[[compact-headless-proof-runner]] · [[genealogy-safe-proof-data-split]] · [[pass-at-k]] ·
[[proof-trace-corpus]] · [[peano-lab-moc|Peano Lab MOC]]
