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

The repository-owned prompt exposes the ordered goals, focus, logic mode, surface name, and a hash
of the exact command-and-theorem capability set. It does not expose a hidden theorem-family label,
certificate, or privileged solver. The supervised runtime masks prompt tokens and trains on the
bare tactic followed by EOS; a delimiter stored in the dataset envelope is validated and removed
before computing loss.

The implemented pipeline currently includes checked synthetic trace generation, replay compilation,
strict manifests, a Qwen3 BF16 LoRA training runtime, Helios job controls, and kernel-judged rollout
evaluation. The first planned smoke model is Qwen3-1.7B-Base, followed only after its gates pass by
controlled four-billion-parameter comparisons. **No real trained-checkpoint result or model solve
rate has been established yet.**

The first Helios preparation attempt exposed an environment-design distinction: the pinned
`ML-bundle/25.10` module loads CUDA and points `pip` at a reviewed ARM wheel directory, but does not
make Torch importable. The corrected preflight recreates an isolated environment, installs exact
`torch==2.9.1+cu129` plus an explicit transitive closure, requires binary wheels and `pip check`,
replaces inherited Python paths, disables the user site, and only then performs the real BF16 LoRA
step. Dependency gating kept the failed attempt from starting training or evaluation.

The replacement Helios preparation job passed the full one-step BF16 LoRA save/reload smoke. A
second execution site, [[wmi-a100-training-runtime]], is intentionally treated as a different
environment rather than a drop-in queue: it must reproduce the gate under its own source, package,
accelerator, and scheduler provenance.

Training data enters through the [[compact-headless-proof-runner]] and is separated with a
[[genealogy-safe-proof-data-split]]. The planned second stage uses
[[verifier-guided-policy-evaluation-and-search]] to collect only newly kernel-checked trajectories
for expert iteration.

## Related

[[proof-trace-corpus]] · [[kernel-judged-evaluation]] · [[pass-at-k]] ·
[[peano-lab-moc|Peano Lab MOC]]
