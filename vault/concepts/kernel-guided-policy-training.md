---
title: Kernel-guided policy training
tags: [peano-lab, llm, post-training, tactics, soundness]
---

# Kernel-guided policy training

**Kernel-guided policy training** teaches an untrusted language model to propose one complete
Peano Lab tactic line from the canonical current proof state. The model is a search policy, never
a proof authority: its command is executed through the public surface, and a trajectory becomes a
positive proof only after the [[trusted-kernel]] checks the final [[proof-certificate]] against the
original goal.

The repository-owned model-v2 prompt exposes the ordered goals, focus, logic mode, complete-line
grammar, and at most eight deterministically retrieved `name : statement` records. Its authority
digest identifies all 56 permitted theorems by canonical statement, dependencies, source/script
hashes, independently checked certificate hash, node count, and depth. That full identity is
`3ce83721f4517f2d5f2e734da1fbeae086473c4d1b8abb45d875a52769096439`.
The public catalog has 63 ordered entries and root
`d0f9070a2677a03eeca8ce2d1b83bcee04df3c907ef8cec2f797ab5ef99e5db0`.
The prompt shows only the small retrieval projection; manifests retain the complete checked identity. It exposes no hidden
theorem-family label, certificate, or privileged solver. The supervised runtime masks prompt tokens
and trains on the bare tactic followed by EOS.

The implemented pipeline includes checked synthetic trace generation, replay compilation, strict
manifests, a Qwen3 BF16 LoRA training runtime, guarded cluster controls, arbitrary-theorem requests,
and kernel-judged rollout evaluation. The first WMI Qwen3-1.7B smoke scored 0/4 at pass@4 and zero
successful parity rollouts in 16 samples (pass@16 = 0.0), but did produce one checked proof in eight
samples for a fresh direct-witness theorem. That result is consistent with a represented template;
attribution to fine-tuning awaits the pretrained-base baseline, and induction-level planning was
not demonstrated.

The first Helios preparation attempt exposed an environment-design distinction: the pinned
`ML-bundle/25.10` module loads CUDA and points `pip` at a reviewed ARM wheel directory, but does not
make Torch importable. The corrected preflight recreates an isolated environment, installs exact
`torch==2.9.1+cu129` plus an explicit transitive closure, requires binary wheels and `pip check`,
replaces inherited Python paths, disables the user site, and only then performs the real BF16 LoRA
step. Dependency gating kept the failed attempt from starting training or evaluation.

The replacement Helios preparation job passed the full one-step BF16 LoRA save/reload smoke. A
second execution site, [[wmi-a100-training-runtime]], is intentionally treated as a different
environment rather than a drop-in queue. Its accepted prepare/train/evaluate chain completed on an
A100 with exact source, package, adapter, and scheduler provenance.

Once an adapter exists, `scripts/eval_trained_peano_policy.py --theorem ... --proof-output ...`
can attempt any bounded closed PA formula under that adapter's exact attested `model-v1` authority.
It exports ordinary pasteable `.pa` source only after the successful rollout is independently
replayed to another kernel-checked QED. A missing proof exits nonzero and creates no proof file;
the model cannot widen its logic mode, tactic set, or importable theorem list.

Training data enters through the [[compact-headless-proof-runner]] and is separated with a
[[genealogy-safe-proof-data-split]]. Model-v2's deterministic 100,000-row schedule targets a 2:1:1
mixture of foundational, induction/IH, and checked-library retrieval/composition transitions; a
10,000-row gate requires all 25 tactic heads and all 56 allowed imports. The four evaluation goals
are `le_trans`, `le_antisymm`, `le_total`, and `mul_eq_zero`; import sealing additionally excludes
their three public descendants, `mul_ne_zero`, `two_large_factors_impossible`, and `prime_two`.
Every selected row must
also fit the pinned tokenizer without truncation before training starts.

The implemented [[verifier-guided-policy-evaluation-and-search]] asks for several complete lines at
one immutable state, rejects failures transactionally, deduplicates canonical successor states, and
keeps a bounded depth-32 beam. `scripts/peano_policy_repl.py` keeps the adapter resident and exposes
a proof only after a second fresh kernel replay. The guarded WMI and Helios launchers provide the
same interface on an A100 or GH200. No model-v2 quality result exists until the registered heavy run
and kernel-judged evaluation finish.

## Related

[[proof-trace-corpus]] · [[kernel-judged-evaluation]] · [[pass-at-k]] ·
[[peano-lab-moc|Peano Lab MOC]]
