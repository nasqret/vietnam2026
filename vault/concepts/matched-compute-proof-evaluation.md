---
title: Matched-compute proof evaluation
tags: [evaluation, theorem-proving, llm, reproducibility]
---

# Matched-compute proof evaluation

**Matched-compute proof evaluation** compares provers on the same sealed
targets, library view, hardware class, and declared resource envelopes. Hydra
uses 1, 10, 60, and 300 seconds per problem and also reports CPU work, GPU/CPU
energy, memory, cost, proof size, invalid actions, and time-to-proof.

The three final systems are the strongest purely symbolic portfolio $S$, the
strongest non-generative learned system $S+R$, and full generative Hydra $H$.
Training cost is disclosed separately and as an amortized break-even curve.

An LLM advantage requires at two adjacent budgets at least a three-percentage-
point gain over the better baseline, a positive lower paired stratified 95%
interval, a corrected exact paired rejection, complete kernel replay, and no
negative-decision regression. Otherwise the registered conclusion is “no
demonstrated LLM advantage under these budgets.”

This extends [[kernel-judged-evaluation]]: validity is necessary, but fair
resource accounting and a [[sealed-theorem-benchmark]] are necessary for a
comparative performance claim.

## Related

- [[pass-at-k]]
- [[verifier-guided-policy-evaluation-and-search]]
- [[peano-hydra]]
- [[peano-lab-moc]]
