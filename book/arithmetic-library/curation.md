# Curating the next conservative edition

The definition-aware explorer demonstrated that mathematical names can reduce
the statement corpus by more than 95% without changing a single native formula.
The next step is not to add more abbreviations indiscriminately. It is to turn
the useful definitions into a coherent authoring API while retaining the exact
expanded corpus as a regression oracle.

```{admonition} The invariant
:class: important
`Prime`, `Dvd`, `BetaAt`, and every other displayed relation remain untrusted
macros. They expand hygienically to the existing first-order formula AST before
a theorem specification or certificate reaches the kernel. Definition nodes
may appear in the reading graph, never in a proof path.
```

## The first eleven definitions

The P0 facade freezes the relations that are both broadly mathematical and
central to the current dependency graph:

| Layer | Canonical relations |
|---|---|
| order | `Le`, `Lt` |
| divisibility and primes | `Dvd`, `Prime` |
| gcd and division | `Coprime`, `IsGCD`, `DivRem` |
| congruence | `ModEq` |
| finite coding and folds | `BetaAt`, `Product`, `Sum` |

Each relation gets one AST-first builder and one template owner. Duplicate
private string builders are removed only after the replacement expands to the
same parsed formula in every existing theorem and typed intermediate step.

## A definition is not yet a library

For every relation the curation dashboard records seven API families:

1. introduction or construction;
2. elimination and projections;
3. zero, one, successor, and empty-prefix boundaries;
4. characterization, uniqueness, or functionality;
5. transport through equality, congruence, or recoding;
6. constructive decision/search, or an explicit blocker;
7. composition such as transitivity, append, restriction, or Euclidean step.

This exposes gaps that theorem counts hide. `Prime(p)`, for example, becomes a
useful interface only together with prime nonzero, factor characterization,
decision, prime-divisor existence, and Euclid's lemma.

## Two synchronized source editions

Every curated theorem has a readable source and an explicit source:

```text
defined theorem + defined have/suffices propositions
                         │
                         ▼ expand and compare
ordinary theorem + ordinary tactic commands
                         │
                         ▼ construct
                 checked certificate
```

The release gate compares statement ASTs, dependency lists, statuses, expanded
local propositions, authored commands, and deterministic certificate hashes.
It also tests capture, shadowing, wrong arity, unknown names, definition cycles,
and registry drift.

## Dependency tiers

- P0 contains the eleven canonical general-purpose relations above.
- P1 contains reusable parity, finite-fold, residue, factorial, bounded-map,
  and factorization relations, depending only on earlier P0/P1 definitions.
- P2 contains campaign-specific inverse-prefix and division-prefix surfaces
  and remains visibly namespaced.

`BalancedBezout`, `PermutationPrefix`, and `CanonicalPF` are reviewed for new
persistent IDs only after their occurrence and API value is established.
Existing `PD0001`–`PD0040` identifiers are never recycled.

## Immediate route

The verifier prerequisite is closed: Cut-aware source
[`ab966fd1`](https://github.com/nasqret/peano-lab-lean/commit/ab966fd1b8207b99eea0c9dc3d719c6e61ef73c2)
passed pinned Lean 4.31/WMI job
[`218358`](https://github.com/nasqret/peano-lab-lean/tree/8515336ab3b89ca6f0c8ab521d01745a220b5211/artifacts/wmi/218358).
The remaining tranche is deliberately ordered:

1. centralize the P0 AST builders without changing statements;
2. complete the `Even`/`Odd` API and modulo-two bridges;
3. add the round-tripping `Prime` surface and capture tests;
4. generate fixed-residue classifications from generic division and
   congruence theorems;
5. publish the first API matrix and duplicate-builder report before expanding
   P2.

The binding technical policy is
[`curation-policy.md`](https://github.com/nasqret/vietnam2026/blob/agent/quadratic-reciprocity-campaign/research/arithmetic-library/curation-policy.md).
Use the {doc}`definition-aware explorer <defined-proof-explorer>` to inspect
the current 40-definition baseline and {doc}`language and trust
<language-and-trust>` for the kernel boundary.
