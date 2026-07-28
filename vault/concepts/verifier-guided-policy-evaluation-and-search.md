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

The implemented model-v2 layer is bounded verifier-guided beam search. A policy proposes up to a
fixed number of complete tactic lines at each state; the ordinary public surface either rejects an
action without changing its parent or returns a successor. Every edge is reconstructed from the
root in a fresh session, so siblings cannot share mutable proof state. Complete canonical goal
renderings deduplicate successors, and a documented deterministic priority prefers fewer and
smaller obligations before policy rank. Hard depth, beam, model-call, candidate, and unique-state
budgets bound the run. The registered benchmark uses depth 32 because all four sealed reference
routes replay within 23 actions under exactly the model-v2 authority.

Only final kernel-checked trajectories may feed [[kernel-guided-policy-training|expert iteration]].
The first model-v1 measurement remains 0/4 at pass@4, while one fresh shallow goal had one successful
rollout out of eight. Model-v2 search and its persistent REPL are implemented, but **their learned
solve rate and any expert-iteration result remain pending** until the heavy adapter exists.

## Related

[[compact-headless-proof-runner]] · [[genealogy-safe-proof-data-split]] · [[pass-at-k]] ·
[[proof-trace-corpus]] · [[peano-lab-moc|Peano Lab MOC]]
