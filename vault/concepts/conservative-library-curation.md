---
title: Conservative library curation
tags: [peano-arithmetic, definitions, curation, trust]
---

# Conservative library curation

The next Peano Lab edition uses named mathematical relations in theorem
sources and typed intermediate propositions, but expands them immediately to
the existing first-order [[proof-certificate]] language.

## P0 facade

`Le`, `Lt`, `Dvd`, `Prime`, `Coprime`, `IsGCD`, `DivRem`, `ModEq`, `BetaAt`,
`Product`, and `Sum` receive one canonical AST-first builder each.

## Completeness matrix

Every relation records introduction, elimination, boundary,
characterization/functionality, transport, decision/search, and composition
lemmas. This distinguishes a readable definition from a reusable API.

## Paired release

The readable and explicit sources must have identical expanded statement ASTs,
dependencies, statuses, local proposition ASTs, and expanded tactic commands.
Definition nodes appear only as purple notation vertices; proof paths use
theorem edges only. Capture, shadowing, arity, unknown-name, cycle, and drift
tests are mandatory.

P1 contains reusable parity, finite-fold, residue, and factorization surfaces.
P2 remains campaign-specific and namespaced. Existing `PD` identifiers are
never recycled.

The binding policy is
`research/arithmetic-library/curation-policy.md`; the book narrative is
`book/arithmetic-library/curation.md`.

## Related

[[trusted-kernel]] · [[self-contained-proof-sharing]] ·
[[foundational-arithmetic-library]] · [[lemma-dependency-dag]]
