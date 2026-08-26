---
title: Pass at k
tags: [llm, evaluation, theorem-proving]
---

# Pass at k

**Pass@k** asks whether at least one of $k$ independently sampled proof attempts succeeds. In a
theorem prover, “succeeds” must mean [[kernel-judged-evaluation]]: the final certificate checks for
the original theorem, not merely that a policy stopped emitting commands.

The metric exposes a useful tradeoff. Pass@1 measures the first proposal path; larger $k$ measures
whether sampling gives the policy useful diversity. Reports must fix the theorem set, command and
step budgets, sampling temperature or random seed, allowed tactic grammar, and checker version.

A random-policy run is a plumbing baseline, not a claim of useful theorem-proving ability. Its job
is to exercise the entire proposal → tactic → proof state → kernel-judge path before a trained model
is connected.

## Related

- [[proof-trace-corpus]]
- [[kernel-judged-evaluation]]
- [[trusted-kernel]]
