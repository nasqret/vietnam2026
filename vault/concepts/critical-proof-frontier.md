---
title: Critical proof frontier
tags: [proof-search, neuro-symbolic, tactics, llm]
---

# Critical proof frontier

The **critical proof frontier** is a state where deterministic symbolic closure
has reached its registered fixed point and a sparse semantic choice remains.
Typical choices are an existential witness, a local lemma, an induction motive,
a case split, a premise bundle, or a bounded solver strategy.

[[peano-hydra]] invokes an autoregressive model only at this frontier. Cheap
normalization, rewriting, arithmetic closure, and clause/state ranking stay in
the high-frequency inner loop. After one valid [[macro-proof-action]],
deterministic closure resumes.

A strong teacher may probe DEV frontiers to test whether the interface has
headroom. That result says only that the action space can express useful moves;
it does not measure the student model and cannot support a final LLM-advantage
claim.

## Related

- [[verifier-guided-policy-evaluation-and-search]]
- [[kernel-guided-policy-training]]
- [[tactic-mode]]
- [[peano-lab-moc]]
