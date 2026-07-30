---
title: Peano Lab — Map of Content
tags: [moc, peano-lab, theorem-proving]
---

> The concepts behind the browser theorem prover and the “Building Peano Lab” book part.

## Architecture

- [[peano-lab]]
- [[arithmetic-library-moc]]
- [[browser-proof-runtime]]
- [[trusted-kernel]]
- [[proof-certificate]]
- [[self-contained-proof-sharing]]
- [[replayable-proof-script]]
- [[multiline-proof-paste]]
- [[de-bruijn-criterion]]
- [[theorem-ladder]]
- [[checked-theorem-reuse]]
- [[local-reasoning-cut]]
- [[commutative-semiring-basis]]
- [[checked-numerical-normalization]]
- [[polynomial-normalization]]
- [[compact-arithmetic-certificate]]
- [[induction-schema]]
- [[substitution]]
- [[natural-deduction]]
- [[intuitionistic-logic]]
- [[heyting-arithmetic]]
- [[tactic-mode]]
- [[tactical]]
- [[simp-termination]]
- [[godel-incompleteness]]

## Learning from traces

- [[proof-trace-corpus]]
- [[kernel-judged-evaluation]]
- [[pass-at-k]]

## Training a tactic policy

- [[compact-headless-proof-runner]]
- [[kernel-guided-policy-training]]
- [[content-addressed-lemma-library]]
- [[wmi-a100-training-runtime]]
- [[genealogy-safe-proof-data-split]]
- [[verifier-guided-policy-evaluation-and-search]]

Model-v3 reading route: follow the notes above from the checked proof-trace corpus through
genealogy and whole-session selection, distinguish the immutable corpus from the content-addressed
lemma library, then follow the guarded WMI runtime to model-free kernel judgment.

## Executable surfaces

- Browser: `/peano-lab/`
- Book: `book/peano/`
- Trace release: `peano-lab/corpus/`
- Data/evaluation protocol: `docs/PEANO_LLM.md`
- Post-training protocol: `docs/PEANO_TRAINING.md`
- Binding design: `docs/PEANO_LAB_DESIGN.md`
- Milestones: `PLAN/09_peano_lab.md`
- Arithmetic-library plan: `PLAN/10_arithmetic_library.md`

## Up

[[00-index]]
