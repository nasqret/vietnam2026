---
title: Kernel-judged evaluation
tags: [peano-lab, llm, evaluation, soundness]
---

# Kernel-judged evaluation

In **kernel-judged evaluation**, a tactic policy proposes ordinary surface commands, but a trial
counts as successful only if they close the goals and the independent checker validates the final
[[proof-certificate]] against the original theorem. Empty-looking goals, a policy's confidence, or
a bounded search verdict never count on their own.

The judge should be stricter and simpler than the system being evaluated. In Peano Lab, the same
[[trusted-kernel]] judges a hand-written policy, a random baseline, `auto`, and any future language
model. This makes accuracy comparable without granting learned code logical authority.

Evaluation cases must also be separated from the [[proof-trace-corpus]] by theorem or template
family; otherwise memorized transitions can masquerade as proof search.

## Related

- [[de-bruijn-criterion]]
- [[pass-at-k]]
- [[verifier-guided-policy-evaluation-and-search]]
- [[theorem-ladder]]
- [[peano-lab]]
