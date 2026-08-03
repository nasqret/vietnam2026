---
title: Peano Hydra
tags: [peano-lab, neuro-symbolic, theorem-proving, research-protocol]
---

# Peano Hydra

**Peano Hydra** is a falsifiable campaign to test whether sparse LLM guidance
improves a strong proof-producing symbolic prover for Peano Lab under matched
resources.

Its many search components are untrusted: native closure, theorem retrieval,
clause ranking, Qwen policies, Codex teacher proposals, Vampire, E, SMT
solvers, translations, and proof reconstruction. Every positive result becomes
a theorem only after the [[trusted-kernel]] checks a self-contained
[[proof-certificate]] against the original goal.

Hydra is a sound theorem prover unless [[decidable-proof-fragment|an exact
restricted fragment]] also has independently justified negative evidence.
Standard full Heyting arithmetic is not described as decidable.

The campaign is organized as H0–H6: freeze semantics, seal a library epoch and
benchmark, construct the strongest symbolic baseline, build checked macro
data, run the model/ablation ladder, execute one matched-compute final, and
release enough evidence for independent reproduction.

H0.1a freezes the [[peano-hydra-semantic-profile]]: closed intuitionistic PA,
PA1--PA6, unrestricted induction, no classical checker, no decision fragment,
and only `proved | unknown`. The functional bootstrap composes fixed symbolic
and recorded-transcript heads through exact quotas and
[[critical-proof-frontier|critical-state]] gates. Every imported trace receives
a fresh profile-bound replay, and every discovered route is freshly traced and
kernel replayed again before publication. Its teacher-oracle pilot reproduces
one known 13-command/180-node proof; because the structural route and
contextual hint were selected from known work, it is plumbing evidence only,
not a model result or completion of the structured [[macro-proof-action]]
protocol.

Exact result field types and hash preimages remain H0.1b; profile v1 labels
that evidence block `required-field-draft`. All surface-macro-v0 rows are
therefore explicitly schema-nonconformant and comparison-ineligible.

## Related

- [[critical-proof-frontier]]
- [[peano-hydra-semantic-profile]]
- [[macro-proof-action]]
- [[library-epoch]]
- [[sealed-theorem-benchmark]]
- [[matched-compute-proof-evaluation]]
- [[kernel-guided-policy-training]]
- [[peano-lab-moc]]
