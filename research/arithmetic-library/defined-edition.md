# Defined edition: expanded PA relations in the QR corpus

This note is the human-readable companion to
[`pa-proof-definitions.json`](pa-proof-definitions.json). It inventories forty
recurring formula schemas in the exact 557-theorem closure rooted at
`quadratic_reciprocity_combined`. The persistent identifiers `PD0001` through
`PD0040` identify definitions, not theorems. They therefore remain stable when
theorem tags, proof scripts, generated binder names, or page layouts change.

## Frozen baseline

The count baseline is the proof-explorer corpus with:

- 557 unique theorem specifications: 240 public and 317 candidate;
- 1,791 direct dependency edges and 45 dependency layers;
- graph SHA-256
  `2231ca4cde6931fad296513fb0c419e19beb7c37989d31fbf6cf01771597cb46`;
- candidate-source SHA-256
  `457327e29134e08fd8802a18b9e1a9e0e23fa84bb44f2934f1fcba466f6e6cb5`.

The source of theorem statements and scope labels is
`book/_static/pa-proof-explorer/api/corpus.json`. Counts are not estimates.
Every statement was parsed, every formula subtree was visited, and templates
were matched structurally. Bound names were discarded through de Bruijn
comparison, while a definition's displayed arguments were treated as
consistent term metavariables.

“Occurrences” means matching subtrees. “Specs” means distinct theorem
specifications containing a match. The public/candidate occurrence split is
also retained in the JSON registry. Counts overlap by design: for example,
the schema `Le(a,b) := exists h. h + a = b` also matches every strict-order
witness by instantiating `a` with `S x`. Do not sum rows as if they partitioned
the corpus.

## What “defined” means here

Peano Lab's object language still has only natural-number variables, `0`,
`S`, `+`, `*`, equality, falsity, connectives, and first-order quantifiers.
Names such as `Prime`, `BetaAt`, `Product`, and `QRes` are documentation and
authoring notation. They are not constants accepted by the parser or kernel.

The conservative pipeline is:

```text
readable relation call
        ↓  untrusted hygienic authoring helper
fully expanded ordinary PA formula
        ↓  parser (negation/numerals also expand)
de Bruijn formula AST
        ↓
ordinary proof term checked by the unchanged kernel
```

Accordingly, the registry's `alpha_template` field is exact only under its
explicit recursive-expansion contract: replace every referenced `PD` relation
with that relation's template, preserve the displayed association of
connectives, then parse. The listed binder order is outermost to innermost;
together with the syntax tree, it uniquely fixes the de Bruijn representation.
No registry entry grants theorem authority or permits a named predicate to
survive into a certificate.

## Inventory overview

| PD range | Layer | Highest-frequency schemas |
|---|---|---|
| `PD0001`–`PD0012` | order, divisibility, congruence, parity, primes | `Le` 5,873; `Lt` 5,768; `ModEq` 434; `Dvd` 284 |
| `PD0013`–`PD0023` | β coding and finite folds | `BetaAt` 3,341; `Sum` 229; `AllBits` 173; `BitCount` 165 |
| `PD0024`–`PD0029` | finite maps and factorization invariants | `ContainsPrefix` 71; `InjectivePrefix` 49; `AllPrime` and `Sorted` are absent from this QR closure |
| `PD0030`–`PD0040` | modular-unit, inverse-map, and division-prefix campaign surfaces | `UnitResidue` 58; `BalancedInverse` 43; `InverseIndex` 30 |

The most valuable consolidation targets are therefore `Lt`, `BetaAt`,
`ModEq`, `Prime`, and the finite-fold family. `finite_fold_surface.py` already
provides the strongest coherent surface: `BetaAt`, `Product`, `Sum`,
`AllBits`, `BitCount`, `Range`, `Repeat`, and relational `Pow` all expand
there. `quadratic_residue_surface.py` owns the reusable congruence and
quadratic-residue expansions. `finite_permutation_theorems.py` owns the
bounded/injective/surjective/contains family. Other high-frequency relations
still have several private copies.

## Dependency spine

The definitions themselves form a small reusable DAG:

```text
Lt ─────────┬───────────────┬──────────────────────────────┐
            │               │                              │
          DivRem          BetaAt                      UnitResidue
                              │                              │
                 ┌────────────┼───────────┐                  │
                 │            │           │                  │
             Product         Sum     Prefix relations   ScaledInverse
                 │            │                              │
                 ├── Pow ─────┘                         inverse prefixes
                 └── Factorial

ModEq ──────┬── QRes
            ├── BalancedInverse
            └── ScaledInverse / ScaledFixedPoint

Dvd ────────┬── Coprime
            └── IsGCD

Prime + BetaAt + Lt ── AllPrime
Le + BetaAt + Lt ───── Sorted
```

Three useful composites are recorded separately from the forty persistent
definition tags: `PermutationPrefix`, `BalancedBezout`, and `CanonicalPF`.
The first and third have no whole-schema occurrence in this QR closure;
their components do occur. `BalancedBezout` occurs three times in three
public theorem statements.

## Exactness and hygiene risks

The current identifier-only public helpers are reasonably auditable: they
validate arguments and synthesize tag-qualified binder names while rejecting
direct collisions. The remaining risks are concrete:

1. Several private helpers accept raw term strings plus a caller-supplied
   `variables` or `avoid` tuple. If a free identifier is omitted, a generated
   binder can capture it.
2. Tag choice and complete avoidance sets remain caller responsibilities
   across composed fragments.
3. Text interpolation is precedence-sensitive. The finite-fold surface has
   an explicit parenthesization safeguard because `S start + i` and
   `S (start + i)` are different terms.
4. Some modules substitute owned marker identifiers with `str.replace` to
   insert compound terms or numerals. Count guards reduce accidental edits,
   but this is not AST-level hygiene.
5. Duplicated private builders can drift in multiplication orientation,
   connective association, or parentheses while remaining mathematically
   similar.
6. Alpha-equivalent generated formulas can receive different source hashes,
   and tactic scripts may accidentally depend on generated surface names.
7. Closedness checks detect leaked free variables, but they do not detect a
   captured variable or a well-formed formula with the wrong grouping.

The natural implementation direction is one untrusted AST-producing
`arithmetic_surface` layer. It should accept term ASTs, compute free variables
itself, allocate fresh binders hygienically, and serialize a fully expanded PA
formula before the parser/kernel boundary. Migration tests should compare old
and new expansions by alpha/de Bruijn equality, retain legacy statement hashes
until intentionally revised, and include capture, precedence, and mutation
regressions.

## Using the machine registry

Consumers should key links and diagrams by `PD` identifier, display the
friendly name, and resolve `dependencies` to other `PD` records. They should
never interpret a zero occurrence as an unproved or invalid definition: it
only means the complete schema is absent from this frozen QR closure. Likewise,
a high occurrence count measures source repetition, not proof difficulty.

Any future recount must record a new graph SHA, source SHA, theorem totals,
and extraction method. Existing `PD` identifiers must not be recycled; new
relations receive new identifiers.
