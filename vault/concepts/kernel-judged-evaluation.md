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

Model-v3 adds a model-free publication gate after GPU evaluation. The replay command accepts only
the exact four-goal evaluator-v4 report, capability identity, source commit, Slurm job, seed, and
depth/beam/candidate/model-call/state/token limits. It cross-checks duplicated search payloads and
counters, then runs every attempt labelled `proof` through a fresh `verify_proof` call against the
original formula. Its canonical non-overwriting attestation distinguishes “the search report
claimed success” from “the independent kernel replayed that exact claim.” A report containing zero
proof claims can still be structurally valid, but it establishes no theorem-solving success.

The 2026-08-02 model-v3 launch smoke exposed the converse distinction. Three tactic scripts from
the trained raw report independently kernel-replay, yet the canonical report replay rejected the
experiment because its nested policy identity omitted four required library-prefix fields. The raw
report remains rejected by that unchanged ordinary gate. A separately version-pinned historical
attestation now validates this exact immutable report and independently replayed all 3/3 claims;
the dedicated pretrained attestation validates declared identity/provenance/search accounting and
zero claims, and the paired cross-binding reports `paired_launch_smoke_admitted`. The narrow
four-goal `k=1` trained/pretrained result is therefore admitted as 3/4 versus 0/4.
Mathematical certificate validity does not waive complete evaluation provenance, and this tiny
smoke does not establish bit-for-bit base identity, broad PA, causal, or induction capability.

## Related

- [[de-bruijn-criterion]]
- [[pass-at-k]]
- [[verifier-guided-policy-evaluation-and-search]]
- [[theorem-ladder]]
- [[peano-lab]]
