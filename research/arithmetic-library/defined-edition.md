# Defined edition: expanded PA relations in the QR corpus

This note is the human-readable companion to
[`pa-proof-definitions.json`](pa-proof-definitions.json). It inventories forty
recurring formula schemas in the exact 557-theorem closure rooted at
`quadratic_reciprocity_combined`. The persistent identifiers `PD0001` through
`PD0040` identify definitions, not theorems. They therefore remain stable when
theorem tags, proof scripts, generated binder names, or page layouts change.
The promotion and consolidation rules for the next authoring release are in
[`curation-policy.md`](curation-policy.md).

## Generated baseline and live classification

The retained pre-migration proof-explorer corpus has:

- 557 unique theorem specifications: 240 public and 317 candidate;
- 1,787 direct dependency edges and 45 dependency layers;
- graph SHA-256
  `98a36450cfe1de29c20be67a1c5f65c8064e9f9eec5368ab769065f910008698`;
- candidate-source SHA-256
  `23fd18aaff26e2c6b428949c35ab3658252c9a4c6fd3b4825a6ccd547f454db1`.

The live QR stack now moves the exact-compatible
`bounded_mod_inverse_unique` overlap from candidate to public. Its partition is
241 public and 316 candidate specifications, and its graph SHA-256 is
`26017364ea943c4ed51a4a83f63ff0cd56b0de3686f0e0b458e7548ee84b1253`.
The 557 nodes, 1,787 edges, 45 layers, and candidate-source hash are unchanged.
The generated definition-aware pages retain the baseline badges and occurrence
receipts until the broader release regeneration; this note does not rewrite
those artifacts.

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
authoring notation. The ordinary formula parser still rejects them. A separate,
opt-in parser accepts the calls only long enough to expand them; they are never
constants in the formula AST or kernel.

The conservative pipeline is:

```text
readable relation call
        ↓  opt-in parser plus hygienic simultaneous substitution
ordinary de Bruijn formula AST
        ↓  exact comparison with the frozen expanded formula
ordinary theorem specification
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

The implemented registry has SHA-256
`924c8bc220f23ce772b72991b8234c3499be7698dc086d90509d39760a1ed0fe`.
The generated 557-theorem reading edition has identity
`9b7c7928ddd3e1930fb5eca6e6b6c4b5ce6978633f6f187525d8813c90f3ddd6`.
These are reproducibility receipts, not trust anchors.

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

## Exactness, hygiene, and remaining risks

The defined edition implements the previously proposed AST boundary in
`defined_syntax.py` and `defined_edition.py`:

1. definition templates are parsed once in an explicit parameter context;
2. compound actual terms are substituted simultaneously under de Bruijn
   binders, with the required shifts, so generated binder names cannot capture
   them;
3. structural compaction prefers the largest matching reviewed schema;
4. every compact theorem statement and every compact `have` or `suffices`
   proposition is expanded again and compared with the original AST;
5. formulas with no selected definition are preserved byte-for-byte; and
6. compilation returns the ordinary `TheoremSpec` type containing only core
   PA formulas.

The older string-producing helpers remain part of the source corpus, so their
capture, precedence, and drift risks have not vanished in the *original*
authoring path. The second edition does not trust or rewrite those helpers: it
starts from their already frozen parsed formulas and proves exact structural
round trips. Adding or changing a definition still requires registry review,
capture and precedence regressions, full-corpus re-expansion, and new content
receipts.

## Using the machine registry

Consumers should key links and diagrams by `PD` identifier, display the
friendly name, and resolve `dependencies` to other `PD` records. They should
never interpret a zero occurrence as an unproved or invalid definition: it
only means the complete schema is absent from this frozen QR closure. Likewise,
a high occurrence count measures source repetition, not proof difficulty.

Any future recount must record a new graph SHA, source SHA, theorem totals,
and extraction method. Existing `PD` identifiers must not be recycled; new
relations receive new identifiers.
